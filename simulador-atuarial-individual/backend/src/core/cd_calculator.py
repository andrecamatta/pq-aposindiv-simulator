"""
Calculadora especializada para planos CD (Contribuição Definida)
Extrai lógica específica CD do ActuarialEngine
"""

import numpy as np
from typing import Dict, List, TYPE_CHECKING
from .abstract_calculator import AbstractCalculator
from .projection_builder import ProjectionBuilder
from ..utils.rates import annual_to_monthly_rate
from .constants import (
    MAX_ANNUITY_MONTHS,
    MAX_AGE_LIMIT,
    DEFAULT_PROGRAMMED_WITHDRAWAL_MONTHS,
    MIN_EFFECTIVE_RATE,
    ACHIEVABILITY_THRESHOLD
)

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from ..models.participant import CDConversionMode
    from .actuarial_engine import ActuarialContext


class CDCalculator(AbstractCalculator):
    """Calculadora especializada para planos de Contribuição Definida"""

    def __init__(self):
        super().__init__()
    
    def create_cd_context(self, state: 'SimulatorState') -> 'ActuarialContext':
        """
        Cria contexto atuarial adaptado para CD usando taxas específicas

        Args:
            state: Estado do simulador

        Returns:
            Contexto atuarial para CD
        """
        from .actuarial_engine import ActuarialContext

        # Validações comuns (herdadas de AbstractCalculator)
        self._validate_state(state)

        # Usar taxas específicas do CD ou fallback para taxas BD
        accumulation_rate = state.accumulation_rate or state.discount_rate
        conversion_rate = state.conversion_rate or state.discount_rate

        # Validar taxas (método centralizado)
        self._validate_rates(accumulation_rate, conversion_rate)

        # Criar contexto base
        context = ActuarialContext.from_state(state)

        # Substituir taxa de desconto por taxa de acumulação durante fase ativa
        context.discount_rate_monthly = annual_to_monthly_rate(accumulation_rate)

        # Armazenar taxa de conversão para uso posterior
        setattr(context, 'conversion_rate_monthly', annual_to_monthly_rate(conversion_rate))

        return context
    
    def calculate_projections(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        mortality_table: np.ndarray
    ) -> Dict:
        """
        Calcula projeções específicas para CD - foco na evolução do saldo

        Args:
            state: Estado do simulador
            context: Contexto atuarial CD
            mortality_table: Tábua de mortalidade

        Returns:
            Dicionário com projeções CD
        """
        # Usar ProjectionBuilder com lógica completa CD migrada
        projections = ProjectionBuilder.build_cd_projections_with_final_balance(state, context, mortality_table, self)

        return projections
    
    def calculate_monthly_income(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        balance: float, 
        mortality_table: np.ndarray
    ) -> float:
        """
        Calcula renda mensal CD baseada na modalidade de conversão
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            balance: Saldo acumulado
            mortality_table: Tábua de mortalidade
            
        Returns:
            Renda mensal CD
        """
        if balance <= 0:
            return 0.0
        
        from ..models.participant import CDConversionMode
        
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        
        if conversion_mode == CDConversionMode.ACTUARIAL:
            return self._calculate_actuarial_annuity(balance, state, context, mortality_table)

        elif conversion_mode == CDConversionMode.ACTUARIAL_EQUIVALENT:
            return self._calculate_actuarial_equivalent_annuity(balance, state, context, mortality_table, 0)

        elif conversion_mode in [CDConversionMode.CERTAIN_5Y, CDConversionMode.CERTAIN_10Y,
                                CDConversionMode.CERTAIN_15Y, CDConversionMode.CERTAIN_20Y]:
            return self._calculate_certain_annuity(balance, state, context, conversion_mode)

        elif conversion_mode == CDConversionMode.PERCENTAGE:
            percentage = state.cd_withdrawal_percentage or 5.0
            return self._calculate_percentage_withdrawal(balance, context, percentage)

        else:  # PROGRAMMED - simplificado
            return balance / DEFAULT_PROGRAMMED_WITHDRAWAL_MONTHS
    
    def calculate_metrics(self, state: 'SimulatorState', projections: Dict, monthly_income: float) -> Dict:
        """
        Calcula métricas específicas para CD
        
        Args:
            state: Estado do simulador
            projections: Projeções calculadas
            monthly_income: Renda mensal CD
            
        Returns:
            Dicionário com métricas CD
        """
        total_contributions = sum(projections["contributions"])
        total_benefits = sum(projections["benefits"])
        
        # Salário base final sem pagamentos extras (13º, 14º)
        months_to_retirement = max(0, (state.retirement_age - state.age) * 12)
        salary_growth_monthly = annual_to_monthly_rate(state.salary_growth_real)
        salary_growth_factor = (1 + salary_growth_monthly) ** max(months_to_retirement - 1, 0)
        final_monthly_salary_base = state.salary * salary_growth_factor
        
        # Taxa de reposição baseada na renda CD calculada
        replacement_ratio = (monthly_income / final_monthly_salary_base * 100) if final_monthly_salary_base > 0 else 0
        
        # Taxa de reposição alvo - compatível com string ou enum
        if str(state.benefit_target_mode) == "REPLACEMENT_RATE":
            target_replacement_ratio = state.target_replacement_rate or 70.0
        else:
            target_replacement_ratio = replacement_ratio
        
        # Para CD, a taxa sustentável é a própria taxa calculada
        sustainable_replacement_ratio = replacement_ratio
        
        return {
            "total_contributions": total_contributions,
            "total_benefits": total_benefits,
            "replacement_ratio": replacement_ratio,
            "target_replacement_ratio": target_replacement_ratio,
            "sustainable_replacement_ratio": sustainable_replacement_ratio
        }
    
    def calculate_benefit_duration(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        balance: float, 
        monthly_income: float, 
        mortality_table: np.ndarray
    ) -> float:
        """
        Calcula duração precisa dos benefícios CD usando simulação mês a mês
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial  
            balance: Saldo acumulado na aposentadoria
            monthly_income: Renda mensal CD calculada
            mortality_table: Tábua de mortalidade
            
        Returns:
            Duração dos benefícios em anos
        """
        if balance <= 0 or monthly_income <= 0:
            return 0.0
        
        from ..models.participant import CDConversionMode
        
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        
        # Para modalidades com período determinado, retornar diretamente
        if conversion_mode in [CDConversionMode.CERTAIN_5Y, CDConversionMode.CERTAIN_10Y, 
                              CDConversionMode.CERTAIN_15Y, CDConversionMode.CERTAIN_20Y]:
            years_map = {
                CDConversionMode.CERTAIN_5Y: 5,
                CDConversionMode.CERTAIN_10Y: 10,
                CDConversionMode.CERTAIN_15Y: 15,
                CDConversionMode.CERTAIN_20Y: 20
            }
            return float(years_map[conversion_mode])
        
        # Para modalidades vitalícias ou dinâmicas, simular mês a mês
        return self._simulate_benefit_duration(state, context, balance, monthly_income, mortality_table)
    
    def calculate_deficit_surplus(self, state: 'SimulatorState', monthly_income: float) -> float:
        """
        Calcula déficit/superávit para planos CD
        
        Args:
            state: Estado do simulador
            monthly_income: Renda mensal calculada
            
        Returns:
            Déficit (negativo) ou Superávit (positivo)
        """
        target_monthly_benefit = state.target_benefit if state.target_benefit else 0.0
        deficit_surplus = monthly_income - target_monthly_benefit
        
        return deficit_surplus
    
    def analyze_conversion_modes(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        balance: float, 
        mortality_table: np.ndarray
    ) -> Dict:
        """
        Analisa diferentes modalidades de conversão para comparação
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            balance: Saldo acumulado
            mortality_table: Tábua de mortalidade
            
        Returns:
            Análise de modalidades
        """
        from ..models.participant import CDConversionMode
        
        modes_analysis = {}
        
        for mode in CDConversionMode:
            temp_state = state.model_copy()
            temp_state.cd_conversion_mode = mode
            
            monthly_income = self.calculate_monthly_income(temp_state, context, balance, mortality_table)
            modes_analysis[mode] = {
                "monthly_income": monthly_income,
                "annual_income": monthly_income * 12,
                "description": self._get_conversion_mode_description(mode)
            }
        
        return modes_analysis
    
    def _estimate_final_balance(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        monthly_contributions: list, 
        months_to_retirement: int
    ) -> float:
        """Estimativa inicial do saldo final para cálculo da renda"""
        accumulated = state.initial_balance
        
        for month in range(months_to_retirement):
            accumulated *= (1 + context.discount_rate_monthly)
            accumulated *= (1 - context.admin_fee_monthly)
            if month < len(monthly_contributions):
                accumulated += monthly_contributions[month]
        
        return accumulated
    
    def _calculate_balance_evolution(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        monthly_contributions: list,
        monthly_income: float,
        total_months: int,
        months_to_retirement: int,
        mortality_table: np.ndarray = None
    ) -> tuple:
        """Calcula evolução do saldo e benefícios mensais"""
        monthly_balances = []
        monthly_benefits = []
        accumulated_balance = state.initial_balance

        # Determinar período de benefícios
        from ..models.participant import CDConversionMode
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        benefit_period_months = self._get_benefit_period_months(conversion_mode)

        # Armazena rendas recalculadas conforme modalidade exige
        annual_monthly_incomes = {}

        # Para modalidades dinâmicas, não usar valor fixo inicial
        if conversion_mode in [CDConversionMode.PERCENTAGE, CDConversionMode.ACTUARIAL_EQUIVALENT]:
            current_year_income = 0  # Será recalculado no primeiro mês
        else:
            current_year_income = monthly_income  # Modalidades com valor fixo

        for month in range(total_months):
            # Durante acumulação: capitalizar com taxa de acumulação
            if month < months_to_retirement:
                accumulated_balance *= (1 + context.discount_rate_monthly)
                accumulated_balance *= (1 - context.admin_fee_monthly)
                accumulated_balance += monthly_contributions[month]
                monthly_balances.append(max(0, accumulated_balance))
                monthly_benefits.append(0.0)
            else:
                # Durante aposentadoria
                months_since_retirement = month - months_to_retirement
                years_since_retirement = months_since_retirement // 12
                month_in_retirement_year = months_since_retirement % 12

                # No primeiro mês, registrar pico ANTES do primeiro saque
                if months_since_retirement == 0:
                    accumulated_balance *= (1 - context.admin_fee_monthly)
                    monthly_balances.append(max(0, accumulated_balance))

                # Para equivalência atuarial, recalcular renda a cada ano
                if conversion_mode == CDConversionMode.ACTUARIAL_EQUIVALENT and mortality_table is not None:
                    # Recalcular renda no início de cada novo ano de aposentadoria
                    if month_in_retirement_year == 0 and years_since_retirement not in annual_monthly_incomes:
                        current_year_income = self._calculate_actuarial_equivalent_annuity(
                            accumulated_balance, state, context, mortality_table, years_since_retirement
                        )
                        annual_monthly_incomes[years_since_retirement] = current_year_income
                    elif years_since_retirement in annual_monthly_incomes:
                        current_year_income = annual_monthly_incomes[years_since_retirement]
                elif conversion_mode == CDConversionMode.PERCENTAGE:
                    # Recalcular renda no início de cada ano baseado no saldo atual
                    if month_in_retirement_year == 0:
                        percentage = state.cd_withdrawal_percentage or 5.0
                        current_year_income = self._calculate_percentage_withdrawal(
                            accumulated_balance,
                            context,
                            percentage
                        )
                        annual_monthly_incomes[years_since_retirement] = current_year_income
                    elif years_since_retirement in annual_monthly_incomes:
                        current_year_income = annual_monthly_incomes[years_since_retirement]

                # Verificar se ainda está no período de benefícios
                if benefit_period_months is not None and months_since_retirement >= benefit_period_months:
                    # Período acabou, apenas capitalizar
                    accumulated_balance *= (1 + getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly))
                    accumulated_balance *= (1 - context.admin_fee_monthly)
                    monthly_benefits.append(0.0)
                else:
                    # Ainda no período de benefícios
                    current_month_in_year = month % 12

                    # Usar renda do ano corrente (recalculada para equivalência atuarial)
                    monthly_benefit_payment = current_year_income

                    # Aplicar pagamentos extras (13º, 14º, etc.)
                    extra_payments = context.benefit_months_per_year - 12
                    if extra_payments > 0:
                        if current_month_in_year == 11:  # Dezembro
                            if extra_payments >= 1:
                                monthly_benefit_payment += current_year_income
                        if current_month_in_year == 0:  # Janeiro
                            if extra_payments >= 2:
                                monthly_benefit_payment += current_year_income

                    # Consumir saldo
                    accumulated_balance -= monthly_benefit_payment

                    # Capitalizar saldo restante
                    conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
                    accumulated_balance *= (1 + conversion_rate_monthly)
                    accumulated_balance *= (1 - context.admin_fee_monthly)

                    monthly_benefits.append(monthly_benefit_payment)

                # Para meses após o primeiro mês da aposentadoria
                if months_since_retirement > 0:
                    monthly_balances.append(max(0, accumulated_balance))
        
        return monthly_balances, monthly_benefits
    
    def _convert_mortality_to_survival(
        self,
        mortality_table: np.ndarray,
        start_age: float,
        max_months: int
    ) -> List[float]:
        """
        Converte tábua de mortalidade (qx anual) em probabilidades de sobrevivência cumulativas mensais.

        Args:
            mortality_table: Tábua de mortalidade (qx anual por idade)
            start_age: Idade inicial
            max_months: Número de meses a projetar

        Returns:
            Lista de probabilidades de sobrevivência cumulativas mensais
        """
        survival_probs = []
        cumulative_survival = 1.0

        for month in range(max_months):
            age_years = start_age + (month / 12)
            age_index = int(age_years)

            if age_index < len(mortality_table):
                q_x_annual = mortality_table[age_index]
                q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                p_x_monthly = 1 - q_x_monthly
                cumulative_survival *= p_x_monthly
                survival_probs.append(cumulative_survival)
            else:
                # Além da tábua, assumir sobrevivência zero
                survival_probs.append(0.0)
                cumulative_survival = 0.0

        return survival_probs

    def _calculate_annuity_factor_from_age(
        self,
        current_age: float,
        context: 'ActuarialContext',
        mortality_table: np.ndarray,
        conversion_rate_monthly: float = None
    ) -> float:
        """
        DEPRECATED: Use _calculate_annuity_factor_unified para nova implementação.

        Mantido temporariamente para compatibilidade.
        """
        return self._calculate_annuity_factor_unified(
            current_age, context, mortality_table, conversion_rate_monthly
        )

    def _calculate_annuity_factor_unified(
        self,
        current_age: float,
        context: 'ActuarialContext',
        mortality_table: np.ndarray,
        conversion_rate_monthly: float = None
    ) -> float:
        """
        Calcula fator de anuidade vitalícia usando função centralizada.

        Args:
            current_age: Idade atual para início da anuidade
            context: Contexto atuarial
            mortality_table: Tábua de mortalidade
            conversion_rate_monthly: Taxa de conversão (opcional)

        Returns:
            Fator de anuidade vitalícia
        """
        from .calculations.vpa_calculations import calculate_actuarial_present_value

        if conversion_rate_monthly is None:
            conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)

        # Taxa efetiva considerando admin fee sobre saldo
        effective_rate = (1 + conversion_rate_monthly) / (1 + context.admin_fee_monthly) - 1
        effective_rate = max(effective_rate, MIN_EFFECTIVE_RATE)

        # Converter tábua de mortalidade em probabilidades de sobrevivência
        max_months = min(MAX_ANNUITY_MONTHS, int((MAX_AGE_LIMIT - current_age) * 12))
        survival_probs = self._convert_mortality_to_survival(mortality_table, current_age, max_months)

        # Criar fluxos unitários (R$ 1,00 por mês)
        unit_cash_flows = [1.0] * len(survival_probs)

        # Calcular VPA usando função centralizada
        annuity_factor = calculate_actuarial_present_value(
            unit_cash_flows,
            survival_probs,
            effective_rate,
            timing="antecipado",  # CD geralmente usa antecipado
            start_month=0
        )

        # Ajustar para múltiplos pagamentos anuais
        benefit_months_per_year = getattr(context, 'benefit_months_per_year', 12) or 12
        if benefit_months_per_year > 12:
            annuity_factor *= (benefit_months_per_year / 12.0)

        return annuity_factor

    def _calculate_actuarial_annuity(
        self,
        balance: float,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        mortality_table: np.ndarray
    ) -> float:
        """Calcula anuidade vitalícia atuarial usando função centralizada"""
        annuity_factor = self._calculate_annuity_factor_unified(
            state.retirement_age,
            context,
            mortality_table
        )
        return balance / annuity_factor if annuity_factor > 0 else 0

    def _calculate_actuarial_equivalent_annuity(
        self,
        balance: float,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        mortality_table: np.ndarray,
        years_since_retirement: int
    ) -> float:
        """
        Calcula equivalência atuarial anual - recalcula a renda com base no saldo remanescente

        Args:
            balance: Saldo atual disponível
            state: Estado do simulador
            context: Contexto atuarial
            mortality_table: Tábua de mortalidade
            years_since_retirement: Anos transcorridos desde a aposentadoria

        Returns:
            Renda mensal recalculada para este ano
        """
        if balance <= 0:
            return 0.0

        # Idade atual (considerando anos de aposentadoria transcorridos)
        current_age = state.retirement_age + years_since_retirement

        # Usar método unificado para cálculo de anuidade
        annuity_factor = self._calculate_annuity_factor_unified(
            current_age,
            context,
            mortality_table
        )

        return balance / annuity_factor if annuity_factor > 0 else 0
    
    def _calculate_certain_annuity(
        self, 
        balance: float, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        conversion_mode: 'CDConversionMode'
    ) -> float:
        """Calcula renda certa por N anos"""
        from ..models.participant import CDConversionMode
        
        years_map = {
            CDConversionMode.CERTAIN_5Y: 5,
            CDConversionMode.CERTAIN_10Y: 10,
            CDConversionMode.CERTAIN_15Y: 15,
            CDConversionMode.CERTAIN_20Y: 20
        }
        
        years = years_map[conversion_mode]
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        benefit_months_per_year = context.benefit_months_per_year
        # Taxa efetiva considerando admin fee sobre saldo
        effective_rate = (1 + conversion_rate_monthly) / (1 + context.admin_fee_monthly) - 1
        effective_rate = max(effective_rate, MIN_EFFECTIVE_RATE)

        # Calcular valor presente dos pagamentos considerando pagamentos extras
        pv_total = 0.0

        for year in range(years):
            for month in range(12):
                months_from_start = year * 12 + month
                pv_factor = 1 / ((1 + effective_rate) ** months_from_start) if effective_rate > -1 else 1
                
                # Pagamento normal mensal
                pv_total += pv_factor
                
                # Pagamentos extras
                extra_payments = benefit_months_per_year - 12
                if extra_payments > 0:
                    if month == 11:  # Dezembro - 13º salário
                        if extra_payments >= 1:
                            pv_total += pv_factor
                    if month == 0 and year > 0:  # Janeiro - 14º salário
                        if extra_payments >= 2:
                            pv_total += pv_factor

        return balance / pv_total if pv_total > 0 else 0

    def _calculate_percentage_withdrawal(
        self,
        balance: float,
        context: 'ActuarialContext',
        percentage: float
    ) -> float:
        """Calcula retirada mensal proporcional ao saldo remanescente."""
        if balance <= 0 or percentage <= 0:
            return 0.0

        benefit_months_per_year = getattr(context, 'benefit_months_per_year', 12) or 12
        annual_withdrawal = balance * (percentage / 100.0)
        monthly_withdrawal = annual_withdrawal / max(benefit_months_per_year, 1)
        return monthly_withdrawal

    def _simulate_benefit_duration(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext', 
        balance: float,
        monthly_income: float,
        mortality_table: np.ndarray
    ) -> float:
        """Simula duração dos benefícios mês a mês"""
        from ..models.participant import CDConversionMode
        
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        
        remaining_balance = balance
        months_count = 0
        max_months = MAX_ANNUITY_MONTHS
        cumulative_survival = 1.0
        
        while months_count < max_months and remaining_balance > 0 and cumulative_survival > 0.01:
            # Calcular idade atual
            current_age_years = state.retirement_age + (months_count / 12)
            age_index = int(current_age_years)
            
            # Verificar mortalidade se modalidade for atuarial
            if conversion_mode == CDConversionMode.ACTUARIAL:
                if age_index < len(mortality_table):
                    q_x_annual = mortality_table[age_index]
                    if 0 <= q_x_annual <= 1:
                        q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                        p_x_monthly = 1 - q_x_monthly
                        cumulative_survival *= p_x_monthly
                    else:
                        cumulative_survival = 0.0
                else:
                    cumulative_survival = 0.0
            
            # Calcular pagamento mensal (incluindo extras)
            current_month_in_year = months_count % 12
            base_monthly_income = monthly_income

            if conversion_mode == CDConversionMode.PERCENTAGE:
                percentage = state.cd_withdrawal_percentage or 5.0
                base_monthly_income = self._calculate_percentage_withdrawal(
                    max(remaining_balance, 0.0),
                    context,
                    percentage
                )

            monthly_payment = base_monthly_income

            extra_payments = context.benefit_months_per_year - 12
            if extra_payments > 0:
                if current_month_in_year == 11:  # Dezembro
                    if extra_payments >= 1:
                        monthly_payment += base_monthly_income
                if current_month_in_year == 0 and months_count > 0:  # Janeiro
                    if extra_payments >= 2:
                        monthly_payment += base_monthly_income

            # Descontar pagamento e capitalizar
            remaining_balance -= monthly_payment
            remaining_balance *= (1 + conversion_rate_monthly)
            
            months_count += 1
            
            # Para modalidade percentage, recalcular renda
            if conversion_mode == CDConversionMode.PERCENTAGE:
                percentage = state.cd_withdrawal_percentage or 5.0
                monthly_income = (remaining_balance * (percentage / 100)) / (state.benefit_months_per_year or 13)
                if monthly_income < 1.0:
                    break
        
        if months_count >= max_months or (conversion_mode == CDConversionMode.ACTUARIAL and cumulative_survival <= 0.01):
            return 50.0  # Máximo de 50 anos
        
        return months_count / 12.0
    
    def _get_benefit_period_months(self, conversion_mode: 'CDConversionMode') -> int:
        """Retorna período de benefícios em meses ou None se vitalício"""
        from ..models.participant import CDConversionMode
        
        if conversion_mode in [CDConversionMode.CERTAIN_5Y, CDConversionMode.CERTAIN_10Y, 
                               CDConversionMode.CERTAIN_15Y, CDConversionMode.CERTAIN_20Y]:
            years_map = {
                CDConversionMode.CERTAIN_5Y: 5,
                CDConversionMode.CERTAIN_10Y: 10,
                CDConversionMode.CERTAIN_15Y: 15,
                CDConversionMode.CERTAIN_20Y: 20
            }
            return years_map[conversion_mode] * 12
        
        return None  # Vitalício
    
    def _get_conversion_mode_description(self, mode: 'CDConversionMode') -> str:
        """Retorna descrição da modalidade de conversão"""
        from ..models.participant import CDConversionMode

        descriptions = {
            CDConversionMode.ACTUARIAL: "Renda vitalícia baseada em tábua de mortalidade",
            CDConversionMode.ACTUARIAL_EQUIVALENT: "Equivalência atuarial - renda recalculada anualmente",
            CDConversionMode.CERTAIN_5Y: "Renda garantida por 5 anos",
            CDConversionMode.CERTAIN_10Y: "Renda garantida por 10 anos",
            CDConversionMode.CERTAIN_15Y: "Renda garantida por 15 anos",
            CDConversionMode.CERTAIN_20Y: "Renda garantida por 20 anos",
            CDConversionMode.PERCENTAGE: "Percentual anual do saldo",
            CDConversionMode.PROGRAMMED: "Saque programado customizável"
        }
        return descriptions.get(mode, "Modalidade não definida")

    # REMOVED: _generate_age_projections - código duplicado
    # ProjectionBuilder.build_cd_projections() já centraliza essa lógica

    def calculate_scenarios(self, state: 'SimulatorState', context: 'ActuarialContext',
                           current_projections: Dict, current_monthly_income: float,
                           mortality_table: Dict) -> Dict:
        """
        Calcula cenários diferenciados: atuarial vs desejado

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            current_projections: Projeções atuais
            current_monthly_income: Renda mensal atual
            mortality_table: Tábua de mortalidade

        Returns:
            Dict com cenários diferenciados
        """
        print(f"[CD_SCENARIOS] Iniciando cálculo de cenários")
        print(f"[CD_SCENARIOS] benefit_target_mode: {state.benefit_target_mode}")
        print(f"[CD_SCENARIOS] target_benefit: {state.target_benefit}")
        print(f"[CD_SCENARIOS] current_monthly_income: {current_monthly_income}")
        print(f"[CD_SCENARIOS] current_projections keys: {list(current_projections.keys())}")
        print(f"[CD_SCENARIOS] state.benefit_months_per_year: {state.benefit_months_per_year}")

        scenarios = {}

        # Cenário Atuarial (atual)
        scenarios["actuarial"] = {
            "description": "Cenário baseado nas contribuições atuais",
            "contribution_rate": state.contribution_rate,
            "final_balance": current_projections["final_balance"],
            "monthly_income": current_monthly_income,
            "annual_income": current_monthly_income * 12,
            "replacement_ratio": (current_monthly_income / (state.salary * (state.salary_months_per_year or 13) / 12) * 100) if state.salary > 0 else 0,
            "projections": current_projections
        }

        # Cenário Desejado (com benefício alvo, mas mesmo saldo de acumulação)
        print(f"[CD_SCENARIOS] Verificando condição VALUE: {state.get_enum_value('benefit_target_mode') == 'VALUE'} and {state.target_benefit is not None}")
        if state.get_enum_value('benefit_target_mode') == "VALUE" and state.target_benefit:
            benefit_months_per_year = state.benefit_months_per_year or 13  # Fallback para 13 se None
            target_monthly_benefit = state.target_benefit  # target_benefit já é mensal

            # Verificar se o objetivo já foi atingido
            # Se current_monthly_income >= target, não criar cenário separado (linhas devem convergir)
            goal_achieved = current_monthly_income >= target_monthly_benefit * 0.99  # 1% de tolerância

            print(f"[CD_SCENARIOS] current_monthly_income: {current_monthly_income}")
            print(f"[CD_SCENARIOS] target_monthly_benefit: {target_monthly_benefit}")
            print(f"[CD_SCENARIOS] goal_achieved: {goal_achieved}")

            if goal_achieved:
                # Objetivo já atingido - cenário desejado é idêntico ao atuarial
                # Apenas criar referência para manter compatibilidade com frontend
                scenarios["desired"] = {
                    "description": f"Objetivo de R$ {state.target_benefit:,.2f}/mês já atingido",
                    "contribution_rate": state.contribution_rate,
                    "final_balance": current_projections["final_balance"],
                    "monthly_income": current_monthly_income,  # Usar o atuarial (já >= alvo)
                    "annual_income": current_monthly_income * 12,
                    "replacement_ratio": scenarios["actuarial"]["replacement_ratio"],
                    "projections": current_projections,  # Mesmas projeções do atuarial
                    "target_monthly_benefit": target_monthly_benefit,
                    "achievable": True,
                    "goal_achieved": True  # Flag para indicar que objetivo foi atingido
                }
                print(f"[CD_SCENARIOS] Cenário desejado unificado com atuarial (objetivo atingido)")
            else:
                # Objetivo ainda não atingido - criar cenário separado para comparação
                # Usar MESMO saldo final do cenário atuarial (fase de acumulação idêntica)
                final_balance = current_projections["final_balance"]

                # Calcular evolução do saldo durante aposentadoria com benefício desejado
                desired_projections = self._calculate_desired_scenario_projections(
                    state, context, current_projections, target_monthly_benefit, mortality_table
                )

                scenarios["desired"] = {
                    "description": f"Cenário para atingir benefício de R$ {state.target_benefit:,.2f}/mês",
                    "contribution_rate": state.contribution_rate,  # Mesma taxa da acumulação
                    "final_balance": final_balance,  # Mesmo saldo final
                    "monthly_income": target_monthly_benefit,  # Benefício desejado
                    "annual_income": target_monthly_benefit * 12,
                    "replacement_ratio": (target_monthly_benefit / (state.salary * (state.salary_months_per_year or 13) / 12) * 100) if state.salary > 0 else 0,
                    "projections": desired_projections,
                    "target_monthly_benefit": target_monthly_benefit,
                    "achievable": True,  # Sempre será o valor desejado
                    "goal_achieved": False
                }
                print(f"[CD_SCENARIOS] Cenário desejado separado criado (objetivo não atingido)")

        elif state.get_enum_value('benefit_target_mode') == "REPLACEMENT_RATE" and state.target_replacement_rate:
            target_monthly_benefit = (state.salary * (state.salary_months_per_year or 13) / 12) * (state.target_replacement_rate / 100)

            # Similar logic for replacement rate
            required_contribution_rate = self._calculate_required_contribution_rate(
                state, context, target_monthly_benefit, mortality_table
            )

            if required_contribution_rate and required_contribution_rate > 0:
                temp_state = state.model_copy()
                temp_state.contribution_rate = min(required_contribution_rate, 50.0)

                desired_projections = self.calculate_projections(temp_state, context, mortality_table)
                desired_monthly_income = self.calculate_monthly_income(
                    temp_state, context, desired_projections["final_balance"], mortality_table
                )

                scenarios["desired"] = {
                    "description": f"Cenário para taxa de reposição de {state.target_replacement_rate}%",
                    "contribution_rate": required_contribution_rate,
                    "final_balance": desired_projections["final_balance"],
                    "monthly_income": desired_monthly_income,
                    "annual_income": desired_monthly_income * 12,
                    "replacement_ratio": (desired_monthly_income / (state.salary * (state.salary_months_per_year or 13) / 12) * 100) if state.salary > 0 else 0,
                    "projections": desired_projections,
                    "target_monthly_benefit": target_monthly_benefit,
                    "achievable": desired_monthly_income >= target_monthly_benefit * ACHIEVABILITY_THRESHOLD
                }

        # Comparação entre cenários
        if "desired" in scenarios:
            actuarial = scenarios["actuarial"]
            desired = scenarios["desired"]

            scenarios["comparison"] = {
                "contribution_rate_gap": desired["contribution_rate"] - actuarial["contribution_rate"],
                "income_gap": desired["monthly_income"] - actuarial["monthly_income"],
                "balance_gap": desired["final_balance"] - actuarial["final_balance"],
                "replacement_ratio_gap": desired["replacement_ratio"] - actuarial["replacement_ratio"],
                "additional_contribution_needed": (
                    desired["contribution_rate"] - actuarial["contribution_rate"]
                ) * state.salary / 100,
                "feasible": desired["contribution_rate"] <= 30.0  # Limite razoável
            }

        print(f"[CD_SCENARIOS] Resultado final: actuarial={scenarios.get('actuarial') is not None}, desired={scenarios.get('desired') is not None}")
        if scenarios.get('actuarial'):
            print(f"[CD_SCENARIOS] Actuarial monthly_income: {scenarios['actuarial']['monthly_income']}")
        if scenarios.get('desired'):
            print(f"[CD_SCENARIOS] Desired monthly_income: {scenarios['desired']['monthly_income']}")

        # Converter numpy types para tipos nativos do Python para serialização JSON
        return self._convert_numpy_types(scenarios)

    def _calculate_required_contribution_rate(self, state: 'SimulatorState', context: 'ActuarialContext',
                                            target_monthly_income: float, mortality_table: Dict) -> float:
        """
        Calcula a taxa de contribuição necessária para atingir uma renda alvo

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            target_monthly_income: Renda mensal desejada
            mortality_table: Tábua de mortalidade

        Returns:
            Taxa de contribuição necessária (%)
        """
        # Busca binária para encontrar taxa necessária
        min_rate = 0.1
        max_rate = 50.0
        tolerance = 0.01
        max_iterations = 20

        for _ in range(max_iterations):
            test_rate = (min_rate + max_rate) / 2

            # Criar estado temporário
            temp_state = state.model_copy()
            temp_state.contribution_rate = test_rate

            # Calcular projeções
            projections = self.calculate_projections(temp_state, context, mortality_table)
            resulting_income = self.calculate_monthly_income(
                temp_state, context, projections["final_balance"], mortality_table
            )

            # Verificar se atingiu o alvo
            if abs(resulting_income - target_monthly_income) <= tolerance:
                return test_rate
            elif resulting_income < target_monthly_income:
                min_rate = test_rate
            else:
                max_rate = test_rate

        return (min_rate + max_rate) / 2

    def calculate_cd_simulation(self, state: 'SimulatorState', context: 'ActuarialContext') -> Dict:
        """
        Orquestrador principal para simulações CD completas.

        Args:
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Resultados completos da simulação CD
        """
        from .mortality_tables import get_mortality_table

        # Obter tábua de mortalidade
        mortality_table, _ = get_mortality_table(state.mortality_table, state.gender, state.mortality_aggravation)

        # Calcular projeções temporais
        projections = self.calculate_projections(state, context, mortality_table)

        # Calcular renda mensal baseada no saldo acumulado
        monthly_income = self.calculate_monthly_income(state, context, projections["final_balance"], mortality_table)

        # Calcular métricas-chave
        metrics = self.calculate_metrics(state, projections, monthly_income)

        # Calcular duração dos benefícios
        benefit_duration = self.calculate_benefit_duration(state, context, projections["final_balance"], monthly_income, mortality_table)

        # Calcular déficit/superávit
        deficit_surplus = self.calculate_deficit_surplus(state, monthly_income)

        # Calcular cenários diferenciados
        scenarios = self.calculate_scenarios(state, context, projections, monthly_income, mortality_table)

        return {
            "projections": projections,
            "final_balance": projections["final_balance"],
            "monthly_income": monthly_income,
            "metrics": metrics,
            "benefit_duration": benefit_duration,
            "deficit_surplus": deficit_surplus,
            "scenarios": scenarios
        }

    def calculate(self, state: 'SimulatorState', context: 'ActuarialContext') -> Dict:
        """
        Implementação do método abstrato para cálculos CD.

        Args:
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Resultados dos cálculos CD
        """
        return self.calculate_cd_simulation(state, context)

    def _convert_numpy_types(self, data):
        """
        Converte qualquer tipo não-serializável para tipos nativos do Python
        usando uma abordagem simples e robusta via JSON
        """
        import json
        try:
            return json.loads(json.dumps(data, default=str))
        except Exception:
            # Fallback para conversão manual se JSON falhar
            return self._manual_convert(data)

    def _calculate_desired_scenario_projections(self, state: 'SimulatorState', context: 'ActuarialContext',
                                              current_projections: Dict, target_monthly_benefit: float,
                                              mortality_table: Dict) -> Dict:
        """
        Calcula projeções para o cenário desejado mantendo a mesma fase de acumulação,
        mas com benefício diferente na fase de aposentadoria.

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            current_projections: Projeções atuais (cenário atuarial)
            target_monthly_benefit: Benefício mensal desejado
            mortality_table: Tábua de mortalidade

        Returns:
            Dict com projeções do cenário desejado
        """
        # Copiar dados base mantendo fase de acumulação idêntica
        desired_projections = {
            "years": current_projections["years"].copy(),
            "projection_ages": current_projections["projection_ages"].copy(),
            "reserves": [],
            "contributions": current_projections["contributions"].copy(),
            "benefits": [],
            "final_balance": current_projections["final_balance"],
            "salaries": current_projections["salaries"].copy(),
            "survival_probs": current_projections["survival_probs"].copy(),
            "projected_salaries_by_age": current_projections["projected_salaries_by_age"].copy(),
            "projected_benefits_by_age": current_projections["projected_benefits_by_age"].copy(),
            "monthly_data": current_projections["monthly_data"].copy()
        }

        # Recalcular evolução do saldo usando MESMA lógica do cenário atuarial
        # mas com o benefício desejado em vez do atuarial
        total_months = len(current_projections["monthly_data"]["reserves"])
        months_to_retirement = context.months_to_retirement
        monthly_contributions = current_projections["monthly_data"]["contributions"]

        # Usar a MESMA função que o cenário atuarial usa (ProjectionBuilder)
        from .projection_builder import ProjectionBuilder
        monthly_balances, monthly_benefits = ProjectionBuilder._calculate_cd_balance_evolution_with_benefits(
            state,
            context,
            monthly_contributions,
            target_monthly_benefit,  # Usar benefício desejado em vez do atuarial
            total_months,
            months_to_retirement,
            mortality_table
        )

        # Atualizar dados mensais
        desired_projections["monthly_data"]["reserves"] = monthly_balances
        desired_projections["monthly_data"]["benefits"] = monthly_benefits

        # Converter para dados anuais
        from .projections import convert_monthly_to_yearly_projections
        yearly_data = convert_monthly_to_yearly_projections(
            desired_projections["monthly_data"],
            total_months
        )

        # Atualizar com dados anuais
        desired_projections["reserves"] = yearly_data["reserves"]
        desired_projections["benefits"] = yearly_data["benefits"]

        return desired_projections

    def _manual_convert(self, data):
        """Conversão manual como fallback"""
        if isinstance(data, dict):
            return {k: self._manual_convert(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._manual_convert(item) for item in data]
        elif hasattr(data, 'dtype') or 'numpy' in str(type(data)):
            return str(data)
        else:
            return data
