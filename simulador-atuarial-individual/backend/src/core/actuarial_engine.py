import numpy as np
import math
from typing import Dict, List, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import time
import logging

from .logging_config import ActuarialLoggerMixin
from .constants import (
    MIN_RETIREMENT_YEARS,
    MSG_EXTENDED_PROJECTION,
    MSG_RETIREMENT_PROJECTION,
    MAX_ANNUITY_MONTHS,
    MAX_ANNUITY_YEARS,
    MAX_AGE_LIMIT,
    MAX_RETIREMENT_PROJECTION_YEARS,
    MAX_RETIREMENT_AGE_PROJECTION,
    DEFAULT_PROGRAMMED_WITHDRAWAL_MONTHS
)
from ..models import SimulatorState, SimulatorResults, BenefitTargetMode, PlanType, CDConversionMode
from ..models.participant import DEFAULT_CD_WITHDRAWAL_PERCENTAGE, DEFAULT_BENEFIT_MONTHS_PER_YEAR
from .mortality_tables import get_mortality_table, get_mortality_table_info
from .financial_math import present_value, annuity_value
from ..utils.rates import annual_to_monthly_rate
from ..utils.discount import get_timing_adjustment, calculate_discount_factor
from .calculations.vpa_calculations import (
    calculate_actuarial_present_value,
    calculate_vpa_benefits_contributions,
    calculate_sustainable_benefit,
    get_payment_survival_probability,
    calculate_life_annuity_factor,
    calculate_vpa_contributions_with_admin_fees
)
# Função consolidada agora está em utils via redirecionamento
from ..utils.formatters import format_currency_safe, format_audit_benefit_section
from .builders.results_builder import ResultsBuilder


@dataclass
class ActuarialContext:
    """Contexto atuarial com taxas mensais e períodos padronizados"""
    # Taxas mensais (convertidas de anuais)
    discount_rate_monthly: float
    salary_growth_real_monthly: float
    
    # Períodos em meses
    months_to_retirement: int
    total_months_projection: int
    
    # Status de aposentadoria
    is_already_retired: bool  # True se age >= retirement_age
    months_since_retirement: int  # Meses já aposentado (0 se ainda ativo)
    
    # Valores mensais efetivos (considerando 13º)
    monthly_salary: float
    monthly_contribution: float
    monthly_benefit: float
    
    # Custos administrativos (taxas mensais)
    admin_fee_monthly: float     # Taxa administrativa mensal sobre saldo
    loading_fee_rate: float      # Taxa de carregamento sobre contribuições
    
    # Configurações técnicas
    payment_timing: str  # "antecipado" ou "postecipado"
    salary_months_per_year: int
    benefit_months_per_year: int
    
    # Fatores calculados
    salary_annual_factor: float  # Fator para converter mensal → anual
    benefit_annual_factor: float  # Fator para converter mensal → anual
    
    @classmethod
    def from_state(cls, state: SimulatorState) -> 'ActuarialContext':
        """Cria contexto a partir do estado do simulador"""
        # Conversão de taxas anuais para mensais usando utilitário
        discount_monthly = annual_to_monthly_rate(state.discount_rate)
        salary_growth_monthly = annual_to_monthly_rate(state.salary_growth_real)
        
        # Detectar se já está aposentado
        is_already_retired = state.age >= state.retirement_age
        
        if is_already_retired:
            # Pessoa já aposentada
            months_to_retirement = 0
            months_since_retirement = (state.age - state.retirement_age) * 12
            # Note: logging will be handled by the ActuarialEngine instance
        else:
            # Pessoa ainda ativa
            months_to_retirement = (state.retirement_age - state.age) * 12
            months_since_retirement = 0
        
        # Calcular período total de projeção
        if is_already_retired:
            # Para aposentados: projetar apenas os anos restantes de expectativa de vida
            # Usar no máximo definido em constantes
            max_years_projection = min(MAX_RETIREMENT_PROJECTION_YEARS, MAX_RETIREMENT_AGE_PROJECTION - state.age)
            total_months = max(12, max_years_projection * 12)  # Mínimo 1 ano
            # Note: logging will be handled by the ActuarialEngine instance
        else:
            # Para ativos: garantir período adequado para aposentadoria
            projected_retirement_years = state.projection_years - (state.retirement_age - state.age)
            
            if projected_retirement_years < MIN_RETIREMENT_YEARS:
                # Estender automaticamente para garantir período adequado
                total_years = (state.retirement_age - state.age) + MIN_RETIREMENT_YEARS
                total_months = total_years * 12
                # Note: logging will be handled by the ActuarialEngine instance
            else:
                total_months = state.projection_years * 12
        
        # Configurações técnicas
        payment_timing = state.payment_timing
        salary_months_per_year = state.salary_months_per_year
        benefit_months_per_year = state.benefit_months_per_year
        
        # Calcular fatores anuais considerando timing
        if payment_timing == "antecipado":
            # Antecipado: primeiro pagamento no início do ano, desconto menor
            salary_annual_factor = salary_months_per_year * (1 + discount_monthly) ** 0.5
            benefit_annual_factor = benefit_months_per_year * (1 + discount_monthly) ** 0.5
        else:  # postecipado
            # Postecipado: primeiro pagamento no final do primeiro mês
            salary_annual_factor = salary_months_per_year
            benefit_annual_factor = benefit_months_per_year
        
        # Valores mensais efetivos (ajustados para múltiplos pagamentos anuais)
        # Salário mensal efetivo considera que há salary_months_per_year pagamentos
        monthly_salary = state.salary  # Salário mensal base informado pelo usuário
        monthly_contribution = monthly_salary * (state.contribution_rate / 100)
        
        # Benefício mensal alvo (depende do modo)
        if state.benefit_target_mode == BenefitTargetMode.VALUE:
            monthly_benefit = state.target_benefit or 0  # Benefício mensal desejado
        else:
            # Se for taxa de reposição, será calculado na aposentadoria
            monthly_benefit = 0
        
        # Custos administrativos
        admin_fee_monthly = annual_to_monthly_rate(state.admin_fee_rate)
        loading_fee_rate = state.loading_fee_rate
        
        return cls(
            discount_rate_monthly=discount_monthly,
            salary_growth_real_monthly=salary_growth_monthly,
            months_to_retirement=months_to_retirement,
            total_months_projection=total_months,
            is_already_retired=is_already_retired,
            months_since_retirement=months_since_retirement,
            monthly_salary=monthly_salary,
            monthly_contribution=monthly_contribution,
            monthly_benefit=monthly_benefit,
            admin_fee_monthly=admin_fee_monthly,
            loading_fee_rate=loading_fee_rate,
            payment_timing=payment_timing,
            salary_months_per_year=salary_months_per_year,
            benefit_months_per_year=benefit_months_per_year,
            salary_annual_factor=salary_annual_factor,
            benefit_annual_factor=benefit_annual_factor
        )


# Função sanitize_float_for_json removida - sanitização automática via Pydantic


class ActuarialEngine:
    """
    Motor de cálculos atuariais refatorado para orquestração
    Delega cálculos específicos para classes especializadas
    """

    def __init__(self,
                 bd_calculator=None,
                 cd_calculator=None,
                 rmba_calculator=None,
                 rmbc_calculator=None,
                 normal_cost_calculator=None,
                 projection_engine=None,
):
        """
        Inicializa engine com dependency injection para testabilidade

        Args:
            bd_calculator: Calculadora para planos BD
            cd_calculator: Calculadora para planos CD
            rmba_calculator: Calculadora para RMBA
            rmbc_calculator: Calculadora para RMBC
            normal_cost_calculator: Calculadora para Custo Normal
            projection_engine: Engine de projeções
        """
        from .logging_config import ActuarialLoggerMixin
        from .bd_calculator import BDCalculator
        from .cd_calculator import CDCalculator
        from .rmba_calculator import RMBACalculator
        from .rmbc_calculator import RMBCCalculator
        from .normal_cost_calculator import NormalCostCalculator
        from .projection_engine import ProjectionEngine

        # Cache mantido para compatibilidade
        self.cache = {}

        # Dependency injection com fallback para instâncias padrão
        self.bd_calculator = bd_calculator or BDCalculator()
        self.cd_calculator = cd_calculator or CDCalculator()
        self.rmba_calculator = rmba_calculator or RMBACalculator()
        self.rmbc_calculator = rmbc_calculator or RMBCCalculator()
        self.normal_cost_calculator = normal_cost_calculator or NormalCostCalculator()
        self.projection_engine = projection_engine or ProjectionEngine()

        # Dependency injection para factories e builders
        self.results_builder = ResultsBuilder()

        # Configurar logging
        self.logger = ActuarialLoggerMixin().logger
        
    def _calculate_cd_deficit_surplus(self, state: SimulatorState, monthly_income: float) -> float:
        """
        Calcula déficit/superávit para planos CD comparando:
        - Benefício mensal real resultante da conversão atuarial
        - Benefício mensal desejado pelo participante

        Retorna:
        - Valor positivo = Superávit (renda real > desejada)
        - Valor negativo = Déficit (renda real < desejada)
        """
        target_monthly_benefit = state.target_benefit if state.target_benefit else 0.0

        # Déficit/Superávit = Renda Real - Renda Desejada
        # Se positivo: sistema consegue gerar mais que o desejado (superávit)
        # Se negativo: sistema não consegue gerar o desejado (déficit)
        deficit_surplus = monthly_income - target_monthly_benefit

        return deficit_surplus

    def _calculate_cd_deficit_surplus_percentage(self, state: SimulatorState, monthly_income: float) -> float:
        """
        Calcula percentual do déficit/superávit em relação ao benefício desejado para CD.

        Args:
            state: Estado do simulador
            monthly_income: Renda mensal real do CD

        Returns:
            Percentual do déficit/superávit (positivo = superávit, negativo = déficit)
        """
        target_monthly_benefit = state.target_benefit if state.target_benefit else 0.0

        if target_monthly_benefit <= 0:
            return 0.0

        deficit_surplus = monthly_income - target_monthly_benefit
        percentage = (deficit_surplus / target_monthly_benefit) * 100

        # Sanitizar resultado
        if math.isnan(percentage) or math.isinf(percentage):
            return 0.0

        return percentage

    def _calculate_cd_required_contribution_rate(self, state: SimulatorState, context: ActuarialContext,
                                                projections: Dict, monthly_income: float,
                                                accumulated_balance: float) -> float:
        """
        Calcula taxa de contribuição necessária para atingir o benefício desejado em CD.

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções calculadas
            monthly_income: Renda mensal atual do CD
            accumulated_balance: Saldo acumulado atual

        Returns:
            Taxa de contribuição adicional necessária (%)
        """
        target_monthly_benefit = state.target_benefit if state.target_benefit else 0.0

        if target_monthly_benefit <= monthly_income or target_monthly_benefit <= 0:
            return 0.0  # Não precisa de contribuição adicional

        # Calcular saldo necessário para gerar o benefício desejado
        mortality_table, _ = get_mortality_table(state.mortality_table, state.gender, state.mortality_aggravation)

        # Estimar saldo necessário invertendo o cálculo de renda mensal
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL

        if conversion_mode == CDConversionMode.ACTUARIAL:
            # Calcular fator de anuidade vitalícia para estimar saldo necessário
            annuity_factor = self._calculate_cd_annuity_factor(state, context, mortality_table)
            required_balance = target_monthly_benefit * annuity_factor if annuity_factor > 0 else 0
        elif conversion_mode in [CDConversionMode.CERTAIN_5Y, CDConversionMode.CERTAIN_10Y,
                                CDConversionMode.CERTAIN_15Y, CDConversionMode.CERTAIN_20Y]:
            # Para renda certa, usar cálculo de valor presente
            years_map = {
                CDConversionMode.CERTAIN_5Y: 5,
                CDConversionMode.CERTAIN_10Y: 10,
                CDConversionMode.CERTAIN_15Y: 15,
                CDConversionMode.CERTAIN_20Y: 20
            }
            years = years_map[conversion_mode]
            conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)

            # Calcular valor presente dos pagamentos
            total_payments = years * context.benefit_months_per_year
            if conversion_rate_monthly > 0:
                pv_factor = sum(1 / ((1 + conversion_rate_monthly) ** month) for month in range(int(total_payments)))
                required_balance = target_monthly_benefit * pv_factor
            else:
                required_balance = target_monthly_benefit * total_payments
        else:
            # Para outras modalidades, usar estimativa baseada em 20 anos
            required_balance = target_monthly_benefit * 12 * 20

        # Calcular contribuição adicional necessária
        additional_balance_needed = required_balance - accumulated_balance

        if additional_balance_needed <= 0:
            return 0.0

        # Calcular VPA dos salários futuros para determinar taxa adicional necessária
        total_future_salaries = sum(projections.get("salaries", []))

        if total_future_salaries <= 0:
            return 0.0

        required_additional_rate = (additional_balance_needed / total_future_salaries) * 100

        # Sanitizar e limitar resultado
        if math.isnan(required_additional_rate) or math.isinf(required_additional_rate):
            return 0.0

        return min(required_additional_rate, 50.0)  # Máximo 50%

    def _calculate_cd_annuity_factor(self, state: SimulatorState, context: ActuarialContext,
                                   mortality_table: np.ndarray) -> float:
        """
        Calcula fator de anuidade vitalícia para CD.

        Returns:
            Fator de anuidade (valor presente de R$ 1 mensal vitalício)
        """
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)

        annuity_factor = 0.0
        cumulative_survival = 1.0

        # Calcular até limite máximo de anuidades
        max_months = min(MAX_ANNUITY_MONTHS, (MAX_AGE_LIMIT - state.retirement_age) * 12)

        for month in range(max_months):
            retirement_age_years = state.retirement_age + (month / 12)
            age_index = int(retirement_age_years)

            if age_index < len(mortality_table):
                q_x_annual = mortality_table[age_index]
                if 0 <= q_x_annual <= 1:
                    q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                    p_x_monthly = 1 - q_x_monthly
                    cumulative_survival *= p_x_monthly
                else:
                    cumulative_survival = 0.0
                    break

                # Valor presente da anuidade mensal
                pv_factor = 1 / ((1 + conversion_rate_monthly) ** month) if conversion_rate_monthly > 0 else 1
                annuity_factor += cumulative_survival * pv_factor
            else:
                break

        return annuity_factor
        
    def calculate_individual_simulation(self, state: SimulatorState) -> SimulatorResults:
        """Calcula simulação atuarial individual completa - BD ou CD"""
        start_time = time.time()
        
        # Validar entrada
        self._validate_state(state)
        
        # Delegar para calculadoras especializadas baseado no tipo de plano
        if state.plan_type == PlanType.BD:
            return self._calculate_bd_simulation_with_calculator(state, start_time)
        else:  # PlanType.CD
            return self._calculate_cd_simulation_with_calculator(state, start_time)
    
    def _calculate_bd_simulation_with_calculator(self, state: SimulatorState, start_time: float) -> SimulatorResults:
        """Calcula simulação BD delegando completamente para BDCalculator especializada"""
        # Criar contexto atuarial BD com taxas diferenciadas
        context = self.bd_calculator.create_bd_context(state)

        # Delegar cálculo completo para calculadora BD especializada
        bd_results = self.bd_calculator.calculate_bd_simulation(state, context)

        # Decomposição atuarial
        decomposition = self._calculate_actuarial_decomposition(state, context, bd_results["projections"])

        # Análise de cenários
        scenarios = self._calculate_scenarios(state)

        # Projeções atuariais para gráfico separado
        actuarial_projections = self._calculate_actuarial_projections(state, context, bd_results["projections"])

        computation_time = (time.time() - start_time) * 1000

        # Usar ResultsBuilder para construção padronizada
        return (self.results_builder
                .with_bd_results(bd_results)
                .with_actuarial_projections(actuarial_projections)
                .with_decomposition(decomposition)
                .with_scenarios(scenarios)
                .with_computation_time(computation_time)
                .build_bd_results())

    def _calculate_cd_simulation_with_calculator(self, state: SimulatorState, start_time: float) -> SimulatorResults:
        """Calcula simulação para plano CD (Contribuição Definida)"""
        # Criar contexto atuarial adaptado para CD
        context = self._create_cd_context(state)
        
        
        # Obter tábua de mortalidade com suavização
        mortality_table, _ = get_mortality_table(state.mortality_table, state.gender, state.mortality_aggravation)
        
        # Delegar cálculo CD para calculadora especializada
        cd_results = self.cd_calculator.calculate_cd_simulation(state, context)
        
        # Extrair resultados da calculadora CD
        projections = cd_results["projections"]
        accumulated_balance = cd_results["final_balance"]
        
        # Calcular renda mensal baseada na modalidade de conversão
        monthly_income = self._calculate_cd_monthly_income(state, context, accumulated_balance, mortality_table)
        
        # Métricas específicas CD
        cd_metrics = self._calculate_cd_metrics(state, context, projections, monthly_income)
        
        # Calcular duração precisa dos benefícios
        benefit_duration_years = self._calculate_cd_benefit_duration(state, context, accumulated_balance, monthly_income, mortality_table)
        
        # Análise de modalidades de conversão
        conversion_analysis = self._analyze_cd_conversion_modes(state, context, accumulated_balance, mortality_table)

        # Cenários diferenciados (atuarial vs desejado)
        cd_scenarios = self.cd_calculator.calculate_scenarios(state, context, projections, monthly_income, mortality_table)

        
        computation_time = (time.time() - start_time) * 1000
        
        # Usar ResultsBuilder para construção padronizada
        return (self.results_builder
                .with_cd_results(cd_results)
                .with_cd_specific_data(monthly_income, benefit_duration_years, conversion_analysis, cd_metrics)
                .with_cd_scenarios(cd_scenarios)
                .with_computation_time(computation_time)
                .build_cd_results(state))
    
    def _validate_state(self, state: SimulatorState) -> None:
        """Valida parâmetros de entrada usando validador centralizado"""
        from .validators import StateValidator, ValidationError
        
        try:
            errors = StateValidator.validate_full_state(state)
            if errors:
                raise ValueError("; ".join(errors))
        except ValidationError as e:
            raise ValueError(str(e))
    
    def _calculate_projections(self, state: SimulatorState, context: ActuarialContext, mortality_table: np.ndarray) -> Dict:
        """Calcula projeções temporais em base mensal"""
        total_months = context.total_months_projection
        months_to_retirement = context.months_to_retirement
        projection_months = list(range(total_months))
        
        # Projeção salarial mensal considerando múltiplos pagamentos anuais
        monthly_salaries = []
        for month in projection_months:
            # Para aposentados: sem salários futuros
            if context.is_already_retired:
                monthly_salary = 0.0
            elif month < months_to_retirement:  # Fase ativa: meses 0 até months_to_retirement-1
                # Crescimento anual aplicado no início de cada ano
                year_number = month // 12  # Ano 0, 1, 2, etc.
                base_monthly_salary = context.monthly_salary * ((1 + state.salary_growth_real) ** year_number)
                
                # Lógica de pagamentos: todos os 12 meses têm pagamento base
                # Meses específicos têm pagamentos extras (13º, 14º, etc.)
                current_month_in_year = month % 12  # 0=jan, 1=fev, ..., 11=dez
                
                # Pagamento base mensal
                monthly_salary = base_monthly_salary
                
                # Pagamentos extras: 13º em dezembro (mês 11), 14º em janeiro (mês 0), etc.
                extra_payments = context.salary_months_per_year - 12
                if extra_payments > 0:
                    if current_month_in_year == 11:  # Dezembro - 13º salário
                        if extra_payments >= 1:
                            monthly_salary += base_monthly_salary
                    if current_month_in_year == 0 and month > 0:  # Janeiro (não o primeiro mês) - 14º salário
                        if extra_payments >= 2:
                            monthly_salary += base_monthly_salary
            else:
                # Fase aposentado: sem salários
                monthly_salary = 0.0
            monthly_salaries.append(monthly_salary)
        
        # Benefício de aposentadoria mensal (em termos reais)
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            # Salário base exclui pagamentos extras (13º, 14º)
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            months_to_retirement = context.months_to_retirement
            salary_growth_factor = (1 + context.salary_growth_real_monthly) ** max(months_to_retirement - 1, 0)
            final_salary_base = context.monthly_salary * salary_growth_factor
            monthly_benefit_amount = final_salary_base * (replacement_rate / 100)
        else:  # 'VALUE'
            monthly_benefit_amount = state.target_benefit if state.target_benefit is not None else 0
        
        # Projeção de benefícios mensais considerando múltiplos pagamentos anuais
        monthly_benefits = []
        for month in projection_months:
            # Para aposentados: benefícios começam imediatamente (mês 0)
            # Para ativos: benefícios começam em months_to_retirement
            benefit_starts = context.is_already_retired or (month >= months_to_retirement)
            
            if benefit_starts:  # Fase aposentado ou aposentadoria futura
                # Lógica de pagamentos: todos os 12 meses têm pagamento base
                # Meses específicos têm pagamentos extras (13º, 14º, etc.)
                current_month_in_year = month % 12  # 0=jan, 1=fev, ..., 11=dez
                
                # Pagamento base mensal
                monthly_benefit = monthly_benefit_amount
                
                # Pagamentos extras: 13º em dezembro, 14º em janeiro, etc.
                extra_payments = context.benefit_months_per_year - 12
                if extra_payments > 0:
                    if current_month_in_year == 11:  # Dezembro - 13º benefício
                        if extra_payments >= 1:
                            monthly_benefit += monthly_benefit_amount
                    if current_month_in_year == 0:  # Janeiro - 14º benefício
                        if extra_payments >= 2:
                            monthly_benefit += monthly_benefit_amount
                
                monthly_benefits.append(monthly_benefit)
            else:
                # Fase ativa: sem benefícios
                monthly_benefits.append(0.0)
        
        # Contribuições mensais (brutas e líquidas)
        monthly_contributions_gross = []
        monthly_contributions = []  # Contribuições líquidas após carregamento
        for monthly_salary in monthly_salaries:
            # Aposentados não fazem contribuições
            if context.is_already_retired:
                contribution_gross = 0.0
                contribution_net = 0.0
            else:
                contribution_gross = monthly_salary * (state.contribution_rate / 100)
                contribution_net = contribution_gross * (1 - context.loading_fee_rate)
            
            monthly_contributions_gross.append(contribution_gross)
            monthly_contributions.append(contribution_net)
        
        # Probabilidades de sobrevivência mensais
        monthly_survival_probs = []
        cumulative_survival = 1.0
        
        for month in projection_months:
            current_age_years = state.age + (month / 12)
            age_index = int(current_age_years)
            
            if age_index < len(mortality_table) and age_index >= 0:
                # Conversão de probabilidade anual para mensal: q_mensal = 1 - (1 - q_anual)^(1/12)
                q_x_annual = mortality_table[age_index]
                
                # Validar taxa de mortalidade
                if 0 <= q_x_annual <= 1:
                    q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                    p_x_monthly = 1 - q_x_monthly
                    cumulative_survival *= p_x_monthly
                else:
                    # Taxa inválida, assumir mortalidade zero para este período
                    cumulative_survival *= 1.0
            else:
                # Idade fora da tábua, assumir sobrevivência zero
                cumulative_survival = 0.0
            
            # Garantir que sobrevivência não seja negativa
            cumulative_survival = max(0.0, cumulative_survival)
            monthly_survival_probs.append(cumulative_survival)
        
        # Reservas acumuladas mensais considerando custos administrativos
        monthly_reserves = []
        accumulated = state.initial_balance  # Iniciar com saldo inicial
        
        for month in projection_months:
            # Capitalizar saldo existente mensalmente
            accumulated *= (1 + context.discount_rate_monthly)
            
            # Aplicar taxa administrativa mensal sobre o saldo
            if month < 5:  # Log apenas os primeiros meses
                self.logger.debug(f"Mês {month}: saldo antes taxa adm: {accumulated}")
            
            accumulated *= (1 - context.admin_fee_monthly)
            
            if month < 5:
                self.logger.debug(f"Mês {month}: saldo após taxa adm: {accumulated}, taxa aplicada: {context.admin_fee_monthly}")
            
            # Para aposentados: apenas descontar benefícios (sem contribuições)
            # Para ativos: acumular contribuições até aposentadoria, depois descontar benefícios
            if context.is_already_retired:
                # Aposentados: sempre descontam benefícios
                accumulated -= monthly_benefits[month]
            elif month < months_to_retirement:
                # Ativos na fase de contribuição: acumular contribuições
                accumulated += monthly_contributions[month]
            else:
                # Ativos na fase de aposentadoria: descontar benefícios
                accumulated -= monthly_benefits[month]
            
            # Permitir reservas negativas para análise realística de déficits
            monthly_reserves.append(accumulated)
        
        # Calcular anos efetivos de projeção (pode ter sido estendido)
        effective_projection_years = len(projection_months) // 12
        
        # Converter para anos para compatibilidade com frontend
        # Considera corretamente os pagamentos múltiplos (13º, 14º, etc.) por ano
        yearly_salaries = []
        yearly_benefits = []
        yearly_contributions = []
        yearly_survival_probs = []
        yearly_reserves = []
        
        for year_idx in range(effective_projection_years):
            start_month = year_idx * 12
            end_month = min((year_idx + 1) * 12, len(monthly_salaries))
            
            # Somatório anual considerando todos os pagamentos do ano
            # IMPORTANTE: Agora soma corretamente todos os pagamentos mensais
            year_salary = sum(monthly_salaries[start_month:end_month])
            year_benefit = sum(monthly_benefits[start_month:end_month])
            year_contribution = sum(monthly_contributions[start_month:end_month])
            
            # Probabilidade de sobrevivência no final do ano
            year_survival_prob = monthly_survival_probs[min(end_month-1, len(monthly_survival_probs)-1)]
            
            # Reserva no final do ano
            last_month_index = max(start_month, end_month - 1)
            year_reserve = monthly_reserves[min(last_month_index, len(monthly_reserves) - 1)]
            
            yearly_salaries.append(year_salary)
            yearly_benefits.append(year_benefit)
            yearly_contributions.append(year_contribution)
            yearly_survival_probs.append(year_survival_prob)
            yearly_reserves.append(year_reserve)
        
        # Gerar vetores por idade para gráfico de evolução salarial/benefícios
        projection_ages = []
        projected_salaries_by_age = []
        projected_benefits_by_age = []

        for month in range(0, total_months, 12):  # Every 12 months
            age = state.age + (month // 12)
            projection_ages.append(age)

            # Get corresponding data for this month
            if month < len(monthly_salaries) and month < len(monthly_benefits):
                # Para salários: usar o salário base mensal (sem 13º/14º extras)
                # Para benefícios: usar o benefício base mensal (sem 13º/14º extras)
                if monthly_salaries[month] > 0:
                    # Calcular salário base mensal sem extras
                    year_number = month // 12
                    monthly_salary_base = context.monthly_salary * ((1 + state.salary_growth_real) ** year_number)
                else:
                    monthly_salary_base = 0

                if monthly_benefits[month] > 0:
                    # Benefício base mensal utilizado nas projeções (sem 13º/14º extras)
                    monthly_benefit_base = monthly_benefit_amount
                else:
                    monthly_benefit_base = 0

                projected_salaries_by_age.append(monthly_salary_base)
                projected_benefits_by_age.append(monthly_benefit_base)
            else:
                projected_salaries_by_age.append(0.0)
                projected_benefits_by_age.append(0.0)

        projection_data = {
            "years": list(range(effective_projection_years)),
            "salaries": yearly_salaries,
            "benefits": yearly_benefits,
            "contributions": yearly_contributions,
            "survival_probs": yearly_survival_probs,
            "reserves": yearly_reserves,
            # Vetores por idade para gráfico frontend
            "projection_ages": projection_ages,
            "projected_salaries_by_age": projected_salaries_by_age,
            "projected_benefits_by_age": projected_benefits_by_age,
            # Dados mensais para cálculos precisos
            "monthly_data": {
                "months": projection_months,
                "salaries": monthly_salaries,
                "benefits": monthly_benefits,
                "contributions": monthly_contributions,
                "survival_probs": monthly_survival_probs,
                "reserves": monthly_reserves
            }
        }

        # Log debug information for chart generation
        import logging
        logging.info(f"[PROJECTIONS] Generated projection data: years={len(projection_data['years'])}, salaries={len(projection_data['salaries'])}, contributions={len(projection_data['contributions'])}, reserves={len(projection_data['reserves'])}")

        return projection_data
    
    
    def _validate_economic_sanity(self, state: SimulatorState, vpa_benefits: float, vpa_contributions: float, rmba: float) -> None:
        """
        Valida se os resultados fazem sentido econômico
        
        Args:
            state: Estado do simulador
            vpa_benefits: VPA dos benefícios
            vpa_contributions: VPA das contribuições
            rmba: RMBA calculada
        """
        warnings = []
        
        # Validação 1: Relação VPA Benefícios vs Contribuições
        if vpa_contributions > 0 and vpa_benefits > 0:
            ratio = vpa_contributions / vpa_benefits
            
            if ratio > 3.0:  # Contribuições muito maiores que benefícios
                warnings.append(f"⚠️  VPA Contribuições ({vpa_contributions:.2f}) é {ratio:.1f}x maior que VPA Benefícios ({vpa_benefits:.2f})")
            elif ratio < 0.5:  # Benefícios muito maiores que contribuições
                warnings.append(f"⚠️  VPA Benefícios ({vpa_benefits:.2f}) é {1/ratio:.1f}x maior que VPA Contribuições ({vpa_contributions:.2f})")
        
        # Validação 2: RMBA versus salário e tempo de contribuição
        annual_salary = state.salary * state.salary_months_per_year
        years_to_retirement = (state.retirement_age - state.age)
        total_expected_contributions = annual_salary * (state.contribution_rate / 100) * years_to_retirement
        
        if abs(rmba) > total_expected_contributions * 2:
            warnings.append(f"⚠️  RMBA ({rmba:.2f}) parece desproporcional às contribuições esperadas ({total_expected_contributions:.2f})")
        
        # Validação 3: Superávit suspeito para saldo inicial zero
        if state.initial_balance == 0 and rmba < -50000:  # Superávit > R$ 50.000 com saldo zero
            warnings.append(f"⚠️  Superávit alto ({-rmba:.2f}) com saldo inicial zero pode indicar erro de cálculo")
        
        # Validação 4: Benefício alvo versus capacidade de contribuição
        if hasattr(state, 'target_benefit') and state.target_benefit:
            annual_benefit = state.target_benefit * state.benefit_months_per_year
            annual_contribution = annual_salary * (state.contribution_rate / 100)
            
            if annual_benefit > annual_contribution * 10:  # Benefício > 10x contribuição anual
                warnings.append(f"⚠️  Benefício alvo ({annual_benefit:.2f}/ano) muito alto versus contribuição ({annual_contribution:.2f}/ano)")
        
        # Registrar warnings se houver
        if warnings:
            self.logger.warning("Alertas para validação:")
            for warning in warnings:
                self.logger.warning(warning)
    
    
    
    def _calculate_key_metrics(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> Dict:
        """Calcula métricas-chave usando base atuarial consistente"""
        total_contributions = sum(projections["contributions"])
        total_benefits = sum(projections["benefits"])
        
        monthly_data = projections["monthly_data"]

        # Salário base mensal final sem extras (13º, 14º)
        months_to_retirement = context.months_to_retirement
        salary_growth_factor = (1 + context.salary_growth_real_monthly) ** max(months_to_retirement - 1, 0)
        final_salary_monthly_base = context.monthly_salary * salary_growth_factor if not context.is_already_retired else context.monthly_salary
        
        # Usar salário base para cálculos de taxa de reposição (comparação justa)
        final_salary_monthly = final_salary_monthly_base
        
        # Benefício mensal base (sem extras) para comparação consistente
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            # Se for taxa de reposição, usar a taxa configurada
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            benefit_monthly_base = final_salary_monthly * (replacement_rate / 100)
        else:  # VALUE mode
            # Se for valor fixo, assumir que é o benefício mensal base
            benefit_monthly_base = state.target_benefit if state.target_benefit is not None else 0
        
        # Calcular taxa de reposição real (benefício base / salário base)
        replacement_ratio = (benefit_monthly_base / final_salary_monthly * 100) if final_salary_monthly > 0 else 0
        
        # Taxa de reposição alvo - usar base temporal consistente (salário base mensal)
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            target_replacement_ratio = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
        else:  # VALUE mode - usar benefício base mensal vs. salário base mensal
            target_replacement_ratio = (benefit_monthly_base / final_salary_monthly * 100) if final_salary_monthly > 0 else 0
        
        # TAXA DE REPOSIÇÃO SUSTENTÁVEL
        # Calcular usando o utilitário simplificado
        sustainable_monthly_benefit = 0
        sustainable_replacement_ratio = 0
        
        if final_salary_monthly > 0:
            # Calcular VPA das contribuições futuras considerando taxa administrativa
            _, vpa_contributions = calculate_vpa_benefits_contributions(
                monthly_data["benefits"],
                monthly_data["contributions"],
                monthly_data["survival_probs"],
                context.discount_rate_monthly,
                context.payment_timing,
                context.months_to_retirement,
                context.admin_fee_monthly
            )
            
            # Calcular benefício sustentável usando função utilitária
            sustainable_monthly_benefit = calculate_sustainable_benefit(
                state.initial_balance,
                vpa_contributions,
                monthly_data["survival_probs"],
                context.discount_rate_monthly,
                context.payment_timing,
                context.months_to_retirement,
                context.benefit_months_per_year,
                context.admin_fee_monthly
            )
            
            # Taxa de reposição sustentável
            sustainable_replacement_ratio = (sustainable_monthly_benefit / final_salary_monthly * 100) if final_salary_monthly > 0 else 0
        
        return {
            "total_contributions": total_contributions,
            "total_benefits": total_benefits,
            "replacement_ratio": replacement_ratio,
            "target_replacement_ratio": target_replacement_ratio,
            "sustainable_replacement_ratio": sustainable_replacement_ratio
        }
    
    
    def _calculate_actuarial_decomposition(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> Dict:
        """Calcula decomposição atuarial detalhada"""
        monthly_data = projections["monthly_data"]

        # Usar utilitário para calcular VPAs considerando taxa administrativa
        vpa_benefits, vpa_contributions = calculate_vpa_benefits_contributions(
            monthly_data["benefits"],
            monthly_data["contributions"],
            monthly_data["survival_probs"],
            context.discount_rate_monthly,
            context.payment_timing,
            context.months_to_retirement,
            context.admin_fee_monthly
        )

        
        return {
            "apv_benefits": vpa_benefits,
            "apv_future_contributions": vpa_contributions,
            "service_cost": {"normal": 0, "interest": 0},
            "duration": 15.0,  # Simplificado - pode ser calculado precisamente se necessário
            "convexity": 2.5   # Simplificado - pode ser calculado precisamente se necessário
        }
    
    def _calculate_sufficiency_analysis(self, state: SimulatorState, context: ActuarialContext, projections: Dict, metrics: Dict) -> Dict:
        """Calcula análise de suficiência seguindo a fórmula: Saldo Inicial + (-RMBA) = Superávit"""
        
        # Calcular RMBA usando calculadora especializada
        rmba = self.rmba_calculator.calculate_rmba(state, context, projections)
        
        # Análise de suficiência: Saldo Inicial - RMBA = Superávit
        # Se RMBA for negativo (VPA Contrib > VPA Benefícios), isso indica superávit natural
        deficit_surplus = state.initial_balance - rmba
        
        # Calcular VPA do benefício alvo para cálculo de percentuais
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement
        mortality_table, _ = get_mortality_table(state.mortality_table, state.gender, state.mortality_aggravation)
        
        # Obter o benefício alvo mensal correto baseado no modo
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            # Usar salário final projetado
            active_monthly_salaries = [s for s in monthly_data["salaries"] if s > 0]
            final_monthly_salary = active_monthly_salaries[-1] if active_monthly_salaries else context.monthly_salary
            monthly_target_benefit = final_monthly_salary * (replacement_rate / 100)
        else:  # 'VALUE'
            monthly_target_benefit = (state.target_benefit if state.target_benefit is not None else 0)
        
        # Calcular VPA do benefício desejado como anuidade vitalícia mensal
        target_benefit_apv = 0.0
        cumulative_survival = 1.0
        
        # Primeiramente, calcular sobrevivência até aposentadoria
        for month in range(months_to_retirement):
            current_age_years = state.age + (month / 12)
            age_index = int(current_age_years)
            if age_index < len(mortality_table):
                q_x_annual = mortality_table[age_index]
                q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                p_x_monthly = 1 - q_x_monthly
                cumulative_survival *= p_x_monthly
            else:
                cumulative_survival = 0.0
                break
        
        survival_to_retirement = cumulative_survival
        
        # Calcular anuidade usando mesmo horizonte das reservas para consistência
        max_projection_age = state.age + state.projection_years
        max_months_after_retirement = (max_projection_age - state.retirement_age) * 12
        
        for month_after_retirement in range(max_months_after_retirement):
            total_month = months_to_retirement + month_after_retirement
            current_age_years = state.age + (total_month / 12)
            age_index = int(current_age_years)
            
            if age_index < len(mortality_table):
                # Calcular sobrevivência até este mês específico
                if month_after_retirement == 0:
                    survival_prob = survival_to_retirement
                else:
                    # Probabilidade de sobrevivência mensal adicional
                    q_x_annual = mortality_table[age_index - 1]  # Idade anterior
                    q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                    p_x_monthly = 1 - q_x_monthly
                    cumulative_survival *= p_x_monthly
                    survival_prob = cumulative_survival
                
                # Desconto mensal usando utilitários
                benefit_timing_adjustment = get_timing_adjustment(context.payment_timing)
                discount_factor = calculate_discount_factor(
                    context.discount_rate_monthly,
                    total_month,
                    benefit_timing_adjustment
                )
                present_value = (monthly_target_benefit * survival_prob) / discount_factor
                target_benefit_apv += present_value
            else:
                break
        
        # Percentual do déficit/superávit em relação ao VPA dos benefícios alvos
        deficit_surplus_percentage = (deficit_surplus / target_benefit_apv * 100) if target_benefit_apv > 0 else 0
        
        # Taxa de contribuição necessária para déficit zero
        # Necessário quando: Saldo Inicial < RMBA (passivo líquido)
        if rmba > state.initial_balance:
            required_total_contributions = rmba - state.initial_balance
            
            # Calcular VPA dos salários futuros usando utilitário
            salary_timing_adjustment = get_timing_adjustment(context.payment_timing)
            apv_future_salaries = calculate_actuarial_present_value(
                monthly_data["salaries"],
                monthly_data["survival_probs"],
                context.discount_rate_monthly,
                context.payment_timing,
                start_month=0,
                end_month=months_to_retirement
            )
            
            required_contribution_rate = (required_total_contributions / apv_future_salaries * 100) if apv_future_salaries > 0 else 0
        else:
            required_contribution_rate = 0
        
        # Garantir que a taxa seja realista (máximo 50%)
        required_contribution_rate = min(required_contribution_rate, 50)
        
        return {
            "deficit_surplus": deficit_surplus,
            "deficit_surplus_percentage": deficit_surplus_percentage,
            "required_contribution_rate": required_contribution_rate
        }

    def _calculate_scenarios(self, state: SimulatorState) -> Dict:
        """Calcula análise de cenários"""
        return {
            "best": {"rmba": 0, "benefits": 0},
            "worst": {"rmba": 0, "benefits": 0},
            "confidence": {"rmba": (0, 0), "benefits": (0, 0)}
        }
    
    def _calculate_actuarial_projections(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> Dict:
        """Calcula projeções atuariais ano a ano para gráfico"""
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement
        
        vpa_benefits_yearly = []
        vpa_contributions_yearly = []
        rmba_evolution_yearly = []
        rmbc_evolution_yearly = []  # Novo: para aposentados
        
        # Ajuste de timing usando utilitário
        timing_adjustment = get_timing_adjustment(context.payment_timing)
        
        # Para cada ano da projeção, calcular VPAs restantes
        for year_idx in range(len(projections["years"])):
            year_month = year_idx * 12

            # VPA dos benefícios futuros a partir deste ano
            # CORREÇÃO: Usar função consolidada para consistência com RMBA
            if year_idx == 0:
                # t=0: Usar exatamente a mesma função que calcula RMBA
                vpa_benefits, _ = calculate_vpa_benefits_contributions(
                    monthly_data["benefits"],
                    monthly_data["contributions"],
                    monthly_data["survival_probs"],
                    context.discount_rate_monthly,
                    context.payment_timing,
                    context.months_to_retirement,
                    context.admin_fee_monthly
                )
            else:
                # Para outros anos: calcular VPA das parcelas restantes a partir do ano atual
                benefits_from_year = monthly_data["benefits"][year_month:]
                survival_probs_from_year = monthly_data["survival_probs"][year_month:]

                # Determinar meses até aposentadoria a partir deste ano
                months_to_retirement_from_year = max(0, months_to_retirement - year_month)

                vpa_benefits, _ = calculate_vpa_benefits_contributions(
                    benefits_from_year,
                    [],  # Não precisamos das contribuições aqui
                    survival_probs_from_year,
                    context.discount_rate_monthly,
                    context.payment_timing,
                    months_to_retirement_from_year,
                    context.admin_fee_monthly
                )
            
            # VPA das contribuições futuras a partir deste ano
            # Para aposentados: sempre 0 (não há contribuições futuras)
            # Para ativos: usar cálculo normal
            if context.is_already_retired or year_month >= months_to_retirement:
                vpa_contributions = 0.0
            else:
                # Extrair contribuições a partir deste ano
                contributions_from_year = monthly_data["contributions"][year_month:months_to_retirement]
                survival_probs_from_year = monthly_data["survival_probs"][year_month:]
                
                # Usar função com taxa administrativa (mesmo cálculo do RMBA)
                vpa_contributions = calculate_vpa_contributions_with_admin_fees(
                    contributions_from_year,
                    survival_probs_from_year,
                    context.discount_rate_monthly,
                    context.admin_fee_monthly,
                    context.payment_timing,
                    len(contributions_from_year)  # meses restantes até aposentadoria
                )
            
            # Calcular reservas matemáticas
            if context.is_already_retired:
                # Para aposentados: RMBC = VPA benefícios, RMBA = 0
                rmbc_year = vpa_benefits
                rmba_year = 0.0
            else:
                # Para ativos: RMBA = VPA benefícios - VPA contribuições, RMBC = 0
                rmba_year = vpa_benefits - vpa_contributions
                rmbc_year = 0.0
            

            vpa_benefits_yearly.append(vpa_benefits)
            vpa_contributions_yearly.append(vpa_contributions)
            rmba_evolution_yearly.append(rmba_year)
            rmbc_evolution_yearly.append(rmbc_year)
        
        return {
            "vpa_benefits": vpa_benefits_yearly,
            "vpa_contributions": vpa_contributions_yearly,
            "rmba_evolution": rmba_evolution_yearly,
            "rmbc_evolution": rmbc_evolution_yearly
        }

    # ============================================================
    # MÉTODOS ESPECÍFICOS PARA CD (CONTRIBUIÇÃO DEFINIDA)
    # ============================================================
    
    def _create_cd_context(self, state: SimulatorState) -> ActuarialContext:
        """Cria contexto atuarial adaptado para CD usando taxas específicas"""
        # Usar taxas específicas do CD ou fallback para taxas BD
        accumulation_rate = state.accumulation_rate or state.discount_rate
        conversion_rate = state.conversion_rate or state.discount_rate


        # Criar contexto base
        context = ActuarialContext.from_state(state)

        # Substituir taxa de desconto por taxa de acumulação durante fase ativa
        context.discount_rate_monthly = annual_to_monthly_rate(accumulation_rate)

        # Armazenar taxa de conversão para uso posterior (usar setattr para adicionar dinamicamente)
        setattr(context, 'conversion_rate_monthly', annual_to_monthly_rate(conversion_rate))

        return context
    
    
    def _calculate_cd_monthly_income_simple(self, state: SimulatorState, context: ActuarialContext, balance: float, mortality_table: np.ndarray) -> float:
        """Cálculo simplificado da renda mensal CD para uso interno"""
        if balance <= 0:
            return 0.0

        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL

        # Inicializar monthly_rate com valor padrão para evitar UnboundLocalError
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        monthly_rate = conversion_rate_monthly
        
        if conversion_mode == CDConversionMode.ACTUARIAL:
            # Anuidade vitalícia usando tábua de mortalidade
            return self._calculate_actuarial_annuity(balance, state, context, mortality_table)

        elif conversion_mode == CDConversionMode.ACTUARIAL_EQUIVALENT:
            # Equivalência atuarial - similar ao atuarial mas recalculado anualmente
            return self._calculate_actuarial_annuity(balance, state, context, mortality_table)
        
        elif conversion_mode in [CDConversionMode.CERTAIN_5Y, CDConversionMode.CERTAIN_10Y, 
                                CDConversionMode.CERTAIN_15Y, CDConversionMode.CERTAIN_20Y]:
            # Renda certa por N anos
            years_map = {
                CDConversionMode.CERTAIN_5Y: 5,
                CDConversionMode.CERTAIN_10Y: 10,
                CDConversionMode.CERTAIN_15Y: 15,
                CDConversionMode.CERTAIN_20Y: 20
            }
            years = years_map[conversion_mode]
            months = years * 12
            # monthly_rate já foi inicializado no início do método
            
            # Considerar pagamentos extras (13º, 14º salário) no cálculo
            benefit_months_per_year = context.benefit_months_per_year  # Normalmente 13
            total_payments = years * benefit_months_per_year  # Ex: 20 anos × 13 pagamentos = 260 pagamentos
            
            # Fórmula de anuidade temporária ajustada para total de pagamentos reais
            if monthly_rate > 0:
                # Calcular o valor presente dos pagamentos considerando que nem todos são mensais
                # Usar uma abordagem mês a mês para considerar pagamentos extras em dezembro/janeiro
                pv_total = 0.0
                payment_count = 0
                
                for year in range(years):
                    for month in range(12):
                        months_from_start = year * 12 + month
                        pv_factor = 1 / ((1 + monthly_rate) ** months_from_start)
                        
                        # Pagamento normal mensal
                        pv_total += pv_factor
                        payment_count += 1
                        
                        # Pagamentos extras
                        extra_payments = benefit_months_per_year - 12
                        if extra_payments > 0:
                            if month == 11:  # Dezembro - 13º salário
                                if extra_payments >= 1:
                                    pv_total += pv_factor  # 13º salário
                                    payment_count += 1
                            if month == 0 and year > 0:  # Janeiro - 14º salário (se aplicável)
                                if extra_payments >= 2:
                                    pv_total += pv_factor  # 14º salário  
                                    payment_count += 1
                
                return balance / pv_total if pv_total > 0 else 0
            else:
                return balance / total_payments
        
        elif conversion_mode == CDConversionMode.PERCENTAGE:
            # Percentual do saldo por ano
            percentage = state.cd_withdrawal_percentage or DEFAULT_CD_WITHDRAWAL_PERCENTAGE
            return (balance * (percentage / 100)) / (state.benefit_months_per_year or DEFAULT_BENEFIT_MONTHS_PER_YEAR)  # Converter para mensal
        
        else:  # PROGRAMMED - simplificado
            # Saque programado padrão
            return balance / DEFAULT_PROGRAMMED_WITHDRAWAL_MONTHS
    
    def _calculate_actuarial_annuity(self, balance: float, state: SimulatorState, context: ActuarialContext, mortality_table: np.ndarray) -> float:
        """Calcula anuidade vitalícia atuarial"""
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        monthly_rate = conversion_rate_monthly
        
        # Calcular fator de anuidade vitalícia
        annuity_factor = 0.0
        cumulative_survival = 1.0
        
        # Calcular até limite máximo de anuidades
        max_months = min(MAX_ANNUITY_MONTHS, (MAX_AGE_LIMIT - state.retirement_age) * 12)
        
        for month in range(max_months):
            retirement_age_years = state.retirement_age + (month / 12)
            age_index = int(retirement_age_years)
            
            if age_index < len(mortality_table):
                q_x_annual = mortality_table[age_index]
                q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                p_x_monthly = 1 - q_x_monthly
                cumulative_survival *= p_x_monthly
                
                # Valor presente da anuidade mensal
                pv_factor = 1 / ((1 + monthly_rate) ** month) if monthly_rate > 0 else 1
                annuity_factor += cumulative_survival * pv_factor
            else:
                break
        
        return balance / annuity_factor if annuity_factor > 0 else 0
    
    def _calculate_cd_monthly_income(self, state: SimulatorState, context: ActuarialContext, balance: float, mortality_table: np.ndarray) -> float:
        """Calcula renda mensal CD baseada na modalidade de conversão"""
        return self._calculate_cd_monthly_income_simple(state, context, balance, mortality_table)
    
    def _calculate_cd_metrics(self, state: SimulatorState, context: ActuarialContext, projections: Dict, monthly_income: float) -> Dict:
        """Calcula métricas específicas para CD"""
        total_contributions = sum(projections["contributions"])
        total_benefits = sum(projections["benefits"])
        
        # Salário base final sem pagamentos extras (13º)
        months_to_retirement = context.months_to_retirement if hasattr(context, "months_to_retirement") else max(0, (state.retirement_age - state.age) * 12)
        if getattr(context, "is_already_retired", False):
            final_monthly_salary_base = context.monthly_salary
        else:
            salary_growth_factor = (1 + context.salary_growth_real_monthly) ** max(months_to_retirement - 1, 0)
            final_monthly_salary_base = context.monthly_salary * salary_growth_factor
        
        # Taxa de reposição baseada na renda CD calculada
        replacement_ratio = (monthly_income / final_monthly_salary_base * 100) if final_monthly_salary_base > 0 else 0

        # Sanitizar replacement_ratio para evitar valores inválidos
        if math.isnan(replacement_ratio) or math.isinf(replacement_ratio):
            replacement_ratio = 0.0

        # Taxa de reposição alvo (baseada no input do usuário)
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            target_replacement_ratio = state.target_replacement_rate or 70.0
        else:
            target_replacement_ratio = replacement_ratio  # Se não especificado, usar o calculado

        # Sanitizar target_replacement_ratio
        if math.isnan(target_replacement_ratio) or math.isinf(target_replacement_ratio):
            target_replacement_ratio = 70.0

        # Taxa de reposição sustentável (para CD, é a própria taxa calculada)
        sustainable_replacement_ratio = replacement_ratio

        # Sanitizar sustainable_replacement_ratio
        if math.isnan(sustainable_replacement_ratio) or math.isinf(sustainable_replacement_ratio):
            sustainable_replacement_ratio = replacement_ratio
        
        return {
            "total_contributions": total_contributions,
            "total_benefits": total_benefits,
            "replacement_ratio": replacement_ratio,
            "target_replacement_ratio": target_replacement_ratio,
            "sustainable_replacement_ratio": sustainable_replacement_ratio
        }
    
    def _analyze_cd_conversion_modes(self, state: SimulatorState, context: ActuarialContext, balance: float, mortality_table: np.ndarray) -> Dict:
        """Analisa diferentes modalidades de conversão para comparação"""
        modes_analysis = {}
        
        # Analisar cada modalidade
        for conversion_mode_option in CDConversionMode:
            temp_state = state.model_copy()
            temp_state.cd_conversion_mode = conversion_mode_option

            monthly_income = self._calculate_cd_monthly_income_simple(temp_state, context, balance, mortality_table)
            modes_analysis[conversion_mode_option] = {
                "monthly_income": monthly_income,
                "annual_income": monthly_income * 12,
                "description": self._get_conversion_mode_description(conversion_mode_option)
            }
        
        return modes_analysis
    
    def _get_conversion_mode_description(self, mode: CDConversionMode) -> str:
        """Retorna descrição da modalidade de conversão"""
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
    
    def _calculate_cd_benefit_duration(self, state: SimulatorState, context: ActuarialContext, balance: float, monthly_income: float, mortality_table: np.ndarray) -> float:
        """
        Calcula duração precisa dos benefícios CD usando simulação mês a mês
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial  
            balance: Saldo acumulado na aposentadoria
            monthly_income: Renda mensal CD calculada
            mortality_table: Tábua de mortalidade
            
        Returns:
            Duração dos benefícios em anos (pode ser vitalícia se > 50 anos)
        """
        if balance <= 0 or monthly_income <= 0:
            return 0.0
            
        # Configurações
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        
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

        # Para equivalência atuarial, considerar como vitalícia
        if conversion_mode == CDConversionMode.ACTUARIAL_EQUIVALENT:
            return float(MAX_ANNUITY_YEARS)

        # Para modalidades vitalícias ou dinâmicas, simular mês a mês
        remaining_balance = balance
        months_count = 0
        max_months = MAX_ANNUITY_MONTHS
        
        # Probabilidade de sobrevivência acumulada
        cumulative_survival = 1.0
        
        while months_count < max_months and remaining_balance > 0 and cumulative_survival > 0.01:
            # Calcular idade atual
            current_age_years = state.retirement_age + (months_count / 12)
            age_index = int(current_age_years)
            
            # Verificar mortalidade se modalidade for atuarial ou equivalência atuarial
            if conversion_mode in [CDConversionMode.ACTUARIAL, CDConversionMode.ACTUARIAL_EQUIVALENT]:
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
            
            # Calcular pagamento mensal (incluindo extras - 13º, 14º)
            current_month_in_year = months_count % 12
            monthly_payment = monthly_income
            
            extra_payments = context.benefit_months_per_year - 12
            if extra_payments > 0:
                if current_month_in_year == 11:  # Dezembro - 13º
                    if extra_payments >= 1:
                        monthly_payment += monthly_income
                if current_month_in_year == 0 and months_count > 0:  # Janeiro - 14º
                    if extra_payments >= 2:
                        monthly_payment += monthly_income
            
            # Descontar pagamento do saldo
            remaining_balance -= monthly_payment
            
            # Capitalizar saldo restante
            remaining_balance *= (1 + conversion_rate_monthly)
            
            months_count += 1
            
            # Para modalidade percentage, recalcular renda baseada no saldo atual
            if conversion_mode == CDConversionMode.PERCENTAGE:
                percentage = state.cd_withdrawal_percentage or DEFAULT_CD_WITHDRAWAL_PERCENTAGE
                monthly_income = (remaining_balance * (percentage / 100)) / 12
                if monthly_income < 1.0:  # Critério de parada quando renda fica muito baixa
                    break
        
        # Se chegou ao limite de 50 anos ou sobrevivência muito baixa, considerar vitalício
        if months_count >= max_months or (conversion_mode in [CDConversionMode.ACTUARIAL, CDConversionMode.ACTUARIAL_EQUIVALENT] and cumulative_survival <= 0.01):
            return 50.0  # Máximo de 50 anos para benefícios vitalícios (JSON-safe)
        
        return months_count / 12.0  # Converter para anos
