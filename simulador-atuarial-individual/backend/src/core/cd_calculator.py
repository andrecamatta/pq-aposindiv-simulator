"""
Calculadora especializada para planos CD (Contribuição Definida)
Extrai lógica específica CD do ActuarialEngine
"""

import numpy as np
from typing import Dict, TYPE_CHECKING
from .projections import (
    calculate_salary_projections,
    calculate_contribution_projections,
    calculate_survival_probabilities,
    convert_monthly_to_yearly_projections
)
from ..utils.rates import annual_to_monthly_rate

if TYPE_CHECKING:
    from ..models.database import SimulatorState, CDConversionMode
    from .actuarial_engine import ActuarialContext


class CDCalculator:
    """Calculadora especializada para planos de Contribuição Definida"""
    
    def __init__(self):
        self.cache = {}
    
    def create_cd_context(self, state: 'SimulatorState') -> 'ActuarialContext':
        """
        Cria contexto atuarial adaptado para CD usando taxas específicas
        
        Args:
            state: Estado do simulador
            
        Returns:
            Contexto atuarial para CD
        """
        from .actuarial_engine import ActuarialContext
        
        # Usar taxas específicas do CD ou fallback para taxas BD
        accumulation_rate = state.accumulation_rate or state.discount_rate
        conversion_rate = state.conversion_rate or state.discount_rate
        
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
        total_months = context.total_months_projection
        months_to_retirement = context.months_to_retirement
        
        # 1. Projeções salariais (mesmo cálculo que BD)
        monthly_salaries = calculate_salary_projections(context, state, total_months)
        
        # 2. Contribuições mensais
        monthly_contributions = calculate_contribution_projections(monthly_salaries, state, context)
        
        # 3. Probabilidades de sobrevivência
        monthly_survival_probs = calculate_survival_probabilities(state, mortality_table, total_months)
        
        # 4. Calcular renda mensal estimada primeiro
        temp_final_balance = self._estimate_final_balance(state, context, monthly_contributions, months_to_retirement)
        monthly_income = self.calculate_monthly_income(state, context, temp_final_balance, mortality_table)
        
        # 5. EVOLUÇÃO DO SALDO CD - CORE LOGIC
        monthly_balances, monthly_benefits = self._calculate_balance_evolution(
            state, context, monthly_contributions, monthly_income, total_months, months_to_retirement
        )
        
        # Saldo final na aposentadoria
        final_balance = monthly_balances[months_to_retirement] if months_to_retirement < len(monthly_balances) else temp_final_balance
        
        # 6. Converter para dados anuais
        monthly_data = {
            "months": list(range(total_months)),
            "salaries": monthly_salaries,
            "benefits": monthly_benefits,
            "contributions": monthly_contributions,
            "survival_probs": monthly_survival_probs,
            "balances": monthly_balances
        }
        
        yearly_data = convert_monthly_to_yearly_projections(monthly_data, total_months)
        yearly_data["monthly_data"] = monthly_data
        yearly_data["final_balance"] = final_balance
        
        return yearly_data
    
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
        
        from ..models.database import CDConversionMode
        
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        
        if conversion_mode == CDConversionMode.ACTUARIAL:
            return self._calculate_actuarial_annuity(balance, state, context, mortality_table)
        
        elif conversion_mode in [CDConversionMode.CERTAIN_5Y, CDConversionMode.CERTAIN_10Y, 
                                CDConversionMode.CERTAIN_15Y, CDConversionMode.CERTAIN_20Y]:
            return self._calculate_certain_annuity(balance, state, context, conversion_mode)
        
        elif conversion_mode == CDConversionMode.PERCENTAGE:
            percentage = state.cd_withdrawal_percentage or 5.0
            return (balance * (percentage / 100)) / 12
        
        else:  # PROGRAMMED - simplificado
            return balance / (20 * 12)  # 20 anos default
    
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
        
        # Salário final para cálculo de taxa de reposição
        active_salaries = [s for s in projections["monthly_data"]["salaries"] if s > 0]
        final_monthly_salary_base = active_salaries[-1] if active_salaries else state.salary
        
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
        
        from ..models.database import CDConversionMode
        
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
        
        print(f"[CD_DEFICIT_DEBUG] Renda real: R$ {monthly_income:.2f}")
        print(f"[CD_DEFICIT_DEBUG] Renda desejada: R$ {target_monthly_benefit:.2f}")  
        print(f"[CD_DEFICIT_DEBUG] Déficit/Superávit: R$ {deficit_surplus:.2f}")
        
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
        from ..models.database import CDConversionMode
        
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
        months_to_retirement: int
    ) -> tuple:
        """Calcula evolução do saldo e benefícios mensais"""
        monthly_balances = []
        monthly_benefits = []
        accumulated_balance = state.initial_balance
        
        # Determinar período de benefícios
        from ..models.database import CDConversionMode
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        benefit_period_months = self._get_benefit_period_months(conversion_mode)
        
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
                
                # No primeiro mês, registrar pico ANTES do primeiro saque
                if months_since_retirement == 0:
                    monthly_balances.append(max(0, accumulated_balance))
                
                # Verificar se ainda está no período de benefícios
                if benefit_period_months is not None and months_since_retirement >= benefit_period_months:
                    # Período acabou, apenas capitalizar
                    accumulated_balance *= (1 + getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly))
                    monthly_benefits.append(0.0)
                else:
                    # Ainda no período de benefícios
                    current_month_in_year = month % 12
                    monthly_benefit_payment = monthly_income
                    
                    # Aplicar pagamentos extras (13º, 14º, etc.)
                    extra_payments = context.benefit_months_per_year - 12
                    if extra_payments > 0:
                        if current_month_in_year == 11:  # Dezembro
                            if extra_payments >= 1:
                                monthly_benefit_payment += monthly_income
                        if current_month_in_year == 0:  # Janeiro
                            if extra_payments >= 2:
                                monthly_benefit_payment += monthly_income
                    
                    # Consumir saldo
                    accumulated_balance -= monthly_benefit_payment
                    
                    # Capitalizar saldo restante
                    conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
                    accumulated_balance *= (1 + conversion_rate_monthly)
                    
                    monthly_benefits.append(monthly_benefit_payment)
                
                # Para meses após o primeiro mês da aposentadoria
                if months_since_retirement > 0:
                    monthly_balances.append(max(0, accumulated_balance))
        
        return monthly_balances, monthly_benefits
    
    def _calculate_actuarial_annuity(
        self, 
        balance: float, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        mortality_table: np.ndarray
    ) -> float:
        """Calcula anuidade vitalícia atuarial"""
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        
        annuity_factor = 0.0
        cumulative_survival = 1.0
        max_months = min(50 * 12, (110 - state.retirement_age) * 12)
        
        for month in range(max_months):
            retirement_age_years = state.retirement_age + (month / 12)
            age_index = int(retirement_age_years)
            
            if age_index < len(mortality_table):
                q_x_annual = mortality_table[age_index]
                q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                p_x_monthly = 1 - q_x_monthly
                cumulative_survival *= p_x_monthly
                
                pv_factor = 1 / ((1 + conversion_rate_monthly) ** month) if conversion_rate_monthly > 0 else 1
                annuity_factor += cumulative_survival * pv_factor
            else:
                break
        
        return balance / annuity_factor if annuity_factor > 0 else 0
    
    def _calculate_certain_annuity(
        self, 
        balance: float, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        conversion_mode: 'CDConversionMode'
    ) -> float:
        """Calcula renda certa por N anos"""
        from ..models.database import CDConversionMode
        
        years_map = {
            CDConversionMode.CERTAIN_5Y: 5,
            CDConversionMode.CERTAIN_10Y: 10,
            CDConversionMode.CERTAIN_15Y: 15,
            CDConversionMode.CERTAIN_20Y: 20
        }
        
        years = years_map[conversion_mode]
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        benefit_months_per_year = context.benefit_months_per_year
        
        # Calcular valor presente dos pagamentos considerando pagamentos extras
        pv_total = 0.0
        
        for year in range(years):
            for month in range(12):
                months_from_start = year * 12 + month
                pv_factor = 1 / ((1 + conversion_rate_monthly) ** months_from_start)
                
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
    
    def _simulate_benefit_duration(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext', 
        balance: float,
        monthly_income: float,
        mortality_table: np.ndarray
    ) -> float:
        """Simula duração dos benefícios mês a mês"""
        from ..models.database import CDConversionMode
        
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        
        remaining_balance = balance
        months_count = 0
        max_months = 50 * 12
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
            monthly_payment = monthly_income
            
            extra_payments = context.benefit_months_per_year - 12
            if extra_payments > 0:
                if current_month_in_year == 11:  # Dezembro
                    if extra_payments >= 1:
                        monthly_payment += monthly_income
                if current_month_in_year == 0 and months_count > 0:  # Janeiro
                    if extra_payments >= 2:
                        monthly_payment += monthly_income
            
            # Descontar pagamento e capitalizar
            remaining_balance -= monthly_payment
            remaining_balance *= (1 + conversion_rate_monthly)
            
            months_count += 1
            
            # Para modalidade percentage, recalcular renda
            if conversion_mode == CDConversionMode.PERCENTAGE:
                percentage = state.cd_withdrawal_percentage or 5.0
                monthly_income = (remaining_balance * (percentage / 100)) / 12
                if monthly_income < 1.0:
                    break
        
        if months_count >= max_months or (conversion_mode == CDConversionMode.ACTUARIAL and cumulative_survival <= 0.01):
            return 50.0  # Máximo de 50 anos
        
        return months_count / 12.0
    
    def _get_benefit_period_months(self, conversion_mode: 'CDConversionMode') -> int:
        """Retorna período de benefícios em meses ou None se vitalício"""
        from ..models.database import CDConversionMode
        
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
        from ..models.database import CDConversionMode
        
        descriptions = {
            CDConversionMode.ACTUARIAL: "Renda vitalícia baseada em tábua de mortalidade",
            CDConversionMode.CERTAIN_5Y: "Renda garantida por 5 anos",
            CDConversionMode.CERTAIN_10Y: "Renda garantida por 10 anos",
            CDConversionMode.CERTAIN_15Y: "Renda garantida por 15 anos",
            CDConversionMode.CERTAIN_20Y: "Renda garantida por 20 anos",
            CDConversionMode.PERCENTAGE: "Percentual anual do saldo",
            CDConversionMode.PROGRAMMED: "Saque programado customizável"
        }
        return descriptions.get(mode, "Modalidade não definida")