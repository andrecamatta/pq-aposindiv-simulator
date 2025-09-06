import numpy as np
import math
from typing import Dict, List, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
import time

from ..models import SimulatorState, SimulatorResults, BenefitTargetMode, PlanType, CDConversionMode
from .mortality_tables import get_mortality_table, MORTALITY_TABLES
from .financial_math import present_value, annuity_value
from ..utils import (
    annual_to_monthly_rate,
    get_timing_adjustment,
    calculate_discount_factor,
    calculate_actuarial_present_value,
    calculate_vpa_benefits_contributions,
    calculate_sustainable_benefit
)
from ..utils.vpa import calculate_vpa_contributions_with_admin_fees


@dataclass
class ActuarialContext:
    """Contexto atuarial com taxas mensais e períodos padronizados"""
    # Taxas mensais (convertidas de anuais)
    discount_rate_monthly: float
    salary_growth_real_monthly: float
    
    # Períodos em meses
    months_to_retirement: int
    total_months_projection: int
    
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
        
        # Períodos em meses - garantir horizonte adequado para aposentadoria
        months_to_retirement = (state.retirement_age - state.age) * 12
        
        # Estender período se necessário para cobrir aposentadoria adequadamente
        min_retirement_years = 25  # Mínimo 25 anos de aposentadoria
        projected_retirement_years = state.projection_years - (state.retirement_age - state.age)
        
        if projected_retirement_years < min_retirement_years:
            # Estender automaticamente para garantir período adequado
            total_years = (state.retirement_age - state.age) + min_retirement_years
            total_months = total_years * 12
            print(f"[INFO] Período estendido para {total_years} anos para análise adequada da aposentadoria")
        else:
            total_months = state.projection_years * 12
        
        # Configurações técnicas
        payment_timing = state.payment_timing.value
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


def sanitize_float_for_json(value: Any) -> Any:
    """
    Sanitiza valores float para serem compatíveis com JSON
    Converte inf, -inf e nan para valores seguros
    """
    if isinstance(value, (int, float)):
        if math.isinf(value):
            if value > 0:
                return 1e6  # 1 milhão para +inf
            else:
                return -1e6  # -1 milhão para -inf
        elif math.isnan(value):
            return 0.0  # Zero para NaN
        return value
    elif isinstance(value, list):
        return [sanitize_float_for_json(item) for item in value]
    elif isinstance(value, dict):
        return {key: sanitize_float_for_json(val) for key, val in value.items()}
    return value


class ActuarialEngine:
    """Motor de cálculos atuariais para simulação individual"""
    
    def __init__(self):
        self.cache = {}
        
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
        
        print(f"[CD_DEFICIT_DEBUG] Renda real: R$ {monthly_income:.2f}")
        print(f"[CD_DEFICIT_DEBUG] Renda desejada: R$ {target_monthly_benefit:.2f}")  
        print(f"[CD_DEFICIT_DEBUG] Déficit/Superávit: R$ {deficit_surplus:.2f}")
        
        return deficit_surplus
        
    def calculate_individual_simulation(self, state: SimulatorState) -> SimulatorResults:
        """Calcula simulação atuarial individual completa - BD ou CD"""
        start_time = time.time()
        
        # Validar entrada
        self._validate_state(state)
        
        # Delegar para método específico baseado no tipo de plano
        if state.plan_type == PlanType.BD:
            return self._calculate_bd_simulation(state, start_time)
        else:  # PlanType.CD
            return self._calculate_cd_simulation(state, start_time)
    
    def _calculate_bd_simulation(self, state: SimulatorState, start_time: float) -> SimulatorResults:
        """Calcula simulação para plano BD (Benefício Definido) - comportamento atual"""
        # Criar contexto atuarial com taxas mensais
        context = ActuarialContext.from_state(state)
        
        print(f"[ENGINE_DEBUG] Taxa administrativa anual: {state.admin_fee_rate}")
        print(f"[ENGINE_DEBUG] Taxa administrativa mensal: {context.admin_fee_monthly}")
        
        # Obter tábua de mortalidade com agravamento
        mortality_table = get_mortality_table(state.mortality_table, state.gender.value, state.mortality_aggravation)
        
        # Calcular projeções temporais
        projections = self._calculate_projections(state, context, mortality_table)
        
        # Calcular reservas matemáticas
        rmba = self._calculate_rmba(state, context, projections)
        rmbc = self._calculate_rmbc(state, projections)
        normal_cost = self._calculate_normal_cost(state, context, projections)
        
        # Calcular métricas-chave
        metrics = self._calculate_key_metrics(state, context, projections)
        
        # Análise de sensibilidade
        sensitivity = self._calculate_sensitivity(state)
        
        # Decomposição atuarial
        decomposition = self._calculate_actuarial_decomposition(state, context, projections)
        
        # Análise de suficiência
        sufficiency = self._calculate_sufficiency_analysis(state, context, projections, metrics)
        
        # Análise de cenários
        scenarios = self._calculate_scenarios(state)
        
        # Projeções atuariais para gráfico separado
        actuarial_projections = self._calculate_actuarial_projections(state, context, projections)
        
        computation_time = (time.time() - start_time) * 1000
        
        return SimulatorResults(
            # Reservas Matemáticas (sanitizadas)
            rmba=sanitize_float_for_json(rmba),
            rmbc=sanitize_float_for_json(rmbc),
            normal_cost=sanitize_float_for_json(normal_cost),
            
            # Análise de Suficiência (sanitizada)
            deficit_surplus=sanitize_float_for_json(sufficiency["deficit_surplus"]),
            deficit_surplus_percentage=sanitize_float_for_json(sufficiency["deficit_surplus_percentage"]),
            required_contribution_rate=sanitize_float_for_json(sufficiency["required_contribution_rate"]),
            
            # Projeções
            projection_years=projections["years"],
            projected_salaries=projections["salaries"],
            projected_benefits=projections["benefits"],
            projected_contributions=projections["contributions"],
            survival_probabilities=projections["survival_probs"],
            accumulated_reserves=projections["reserves"],
            
            # Projeções atuariais para gráfico separado
            projected_vpa_benefits=actuarial_projections["vpa_benefits"],
            projected_vpa_contributions=actuarial_projections["vpa_contributions"],
            projected_rmba_evolution=actuarial_projections["rmba_evolution"],
            
            # Métricas (sanitizadas)
            total_contributions=sanitize_float_for_json(metrics["total_contributions"]),
            total_benefits=sanitize_float_for_json(metrics["total_benefits"]),
            replacement_ratio=sanitize_float_for_json(metrics["replacement_ratio"]),
            target_replacement_ratio=sanitize_float_for_json(metrics["target_replacement_ratio"]),
            sustainable_replacement_ratio=sanitize_float_for_json(metrics["sustainable_replacement_ratio"]),
            funding_ratio=None,
            
            # Sensibilidade
            sensitivity_discount_rate=sensitivity["discount_rate"],
            sensitivity_mortality=sensitivity["mortality"],
            sensitivity_retirement_age=sensitivity["retirement_age"],
            sensitivity_salary_growth=sensitivity["salary_growth"],
            sensitivity_inflation=sensitivity["inflation"],
            
            # Decomposição
            actuarial_present_value_benefits=decomposition["apv_benefits"],
            actuarial_present_value_salary=decomposition["apv_future_contributions"],
            service_cost_breakdown=decomposition["service_cost"],
            liability_duration=decomposition["duration"],
            convexity=decomposition["convexity"],
            
            # Cenários
            best_case_scenario=scenarios["best"],
            worst_case_scenario=scenarios["worst"],
            confidence_intervals=scenarios["confidence"],
            
            # Metadados
            calculation_timestamp=datetime.now(),
            computation_time_ms=computation_time,
            actuarial_method_details={"method": state.calculation_method.value},
            assumptions_validation={"valid": True}
        )

    def _calculate_cd_simulation(self, state: SimulatorState, start_time: float) -> SimulatorResults:
        """Calcula simulação para plano CD (Contribuição Definida)"""
        # Criar contexto atuarial adaptado para CD
        context = self._create_cd_context(state)
        
        print(f"[CD_ENGINE_DEBUG] Taxa acumulação: {state.accumulation_rate}")
        print(f"[CD_ENGINE_DEBUG] Taxa conversão: {state.conversion_rate}")
        
        # Obter tábua de mortalidade com agravamento
        mortality_table = get_mortality_table(state.mortality_table, state.gender.value, state.mortality_aggravation)
        
        # Calcular projeções CD - foco na evolução do saldo
        projections = self._calculate_cd_projections(state, context, mortality_table)
        
        # Calcular saldo final acumulado na aposentadoria
        accumulated_balance = projections["final_balance"]
        
        # Calcular renda mensal baseada na modalidade de conversão
        monthly_income = self._calculate_cd_monthly_income(state, context, accumulated_balance, mortality_table)
        
        # Métricas específicas CD
        cd_metrics = self._calculate_cd_metrics(state, projections, monthly_income)
        
        # Calcular duração precisa dos benefícios
        benefit_duration_years = self._calculate_cd_benefit_duration(state, context, accumulated_balance, monthly_income, mortality_table)
        
        # Análise de modalidades de conversão
        conversion_analysis = self._analyze_cd_conversion_modes(state, context, accumulated_balance, mortality_table)
        
        # Sensibilidade específica para CD
        cd_sensitivity = self._calculate_cd_sensitivity(state)
        
        computation_time = (time.time() - start_time) * 1000
        
        # Calcular métricas específicas CD
        total_contributions_value = sum(projections["contributions"])
        administrative_costs = total_contributions_value * state.loading_fee_rate + accumulated_balance * state.admin_fee_rate
        net_balance = accumulated_balance - administrative_costs
        accumulated_return_value = accumulated_balance - state.initial_balance - total_contributions_value
        effective_return = (accumulated_return_value / total_contributions_value * 100) if total_contributions_value > 0 else 0.0
        conversion_factor_value = monthly_income / accumulated_balance if accumulated_balance > 0 else 0.0
        
        # Sanitizar valores que podem conter inf/nan
        benefit_duration_years = sanitize_float_for_json(benefit_duration_years)
        
        return SimulatorResults(
            # Reservas Matemáticas (zeradas para CD)
            rmba=0.0,
            rmbc=0.0,  
            normal_cost=0.0,
            
            # Campos específicos CD
            individual_balance=accumulated_balance,
            net_accumulated_value=net_balance,
            accumulated_return=accumulated_return_value,
            effective_return_rate=effective_return,
            monthly_income_cd=monthly_income,
            conversion_factor=conversion_factor_value,
            administrative_cost_total=administrative_costs,
            benefit_duration_years=benefit_duration_years,
            
            # Análise de Suficiência para CD
            deficit_surplus=self._calculate_cd_deficit_surplus(state, monthly_income),
            deficit_surplus_percentage=0.0,  # Por enquanto não calculado para CD
            required_contribution_rate=0.0,  # Por enquanto não calculado para CD
            
            # Projeções CD
            projection_years=projections["years"],
            projected_salaries=projections["salaries"],
            projected_benefits=projections["benefits"],  # Renda projetada na aposentadoria
            projected_contributions=projections["contributions"],
            survival_probabilities=projections["survival_probs"],
            accumulated_reserves=projections["balances"],  # Evolução do saldo
            
            # Projeções específicas CD
            projected_vpa_benefits=[],  # Não aplicável
            projected_vpa_contributions=[],  # Não aplicável
            projected_rmba_evolution=projections["balances"],  # Usar evolução do saldo
            
            # Métricas CD
            total_contributions=cd_metrics["total_contributions"],
            total_benefits=cd_metrics["total_benefits"],
            replacement_ratio=cd_metrics["replacement_ratio"],
            target_replacement_ratio=cd_metrics["target_replacement_ratio"],
            sustainable_replacement_ratio=cd_metrics["sustainable_replacement_ratio"],
            funding_ratio=None,  # Não aplicável
            
            # Sensibilidade CD
            sensitivity_discount_rate=cd_sensitivity["accumulation_rate"],
            sensitivity_mortality=cd_sensitivity["mortality"],
            sensitivity_retirement_age=cd_sensitivity["retirement_age"],
            sensitivity_salary_growth=cd_sensitivity["salary_growth"],
            sensitivity_inflation={},
            
            # Decomposição (simplificada para CD)
            actuarial_present_value_benefits=monthly_income * 12 * 15,  # Estimativa
            actuarial_present_value_salary=cd_metrics["total_contributions"],
            service_cost_breakdown={"accumulated_balance": accumulated_balance},
            liability_duration=0.0,
            convexity=0.0,
            
            # Cenários (simplificados)
            best_case_scenario={"balance": accumulated_balance * 1.2},
            worst_case_scenario={"balance": accumulated_balance * 0.8},
            confidence_intervals={"balance": (accumulated_balance * 0.9, accumulated_balance * 1.1)},
            
            # Metadados
            calculation_timestamp=datetime.now(),
            computation_time_ms=computation_time,
            actuarial_method_details={"method": "CD", "conversion_mode": state.cd_conversion_mode.value if state.cd_conversion_mode else "ACTUARIAL"},
            assumptions_validation={"valid": True}
        )
    
    def _validate_state(self, state: SimulatorState) -> None:
        """Valida parâmetros de entrada"""
        if state.age < 18 or state.age > 70:
            raise ValueError("Idade deve estar entre 18 e 70 anos")
        
        if state.retirement_age <= state.age:
            raise ValueError("Idade de aposentadoria deve ser maior que idade atual")
        
        if state.salary <= 0:
            raise ValueError("Salário deve ser positivo")
    
    def _calculate_projections(self, state: SimulatorState, context: ActuarialContext, mortality_table: np.ndarray) -> Dict:
        """Calcula projeções temporais em base mensal"""
        total_months = context.total_months_projection
        months_to_retirement = context.months_to_retirement
        projection_months = list(range(total_months))
        
        # Projeção salarial mensal considerando múltiplos pagamentos anuais
        monthly_salaries = []
        for month in projection_months:
            if month < months_to_retirement:  # Fase ativa: meses 0 até months_to_retirement-1
                # Crescimento mensal composto do salário base
                base_monthly_salary = context.monthly_salary * ((1 + context.salary_growth_real_monthly) ** month)
                
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
            # Usar valor padrão de 70% se target_replacement_rate for None
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            active_salaries = [s for s in monthly_salaries if s > 0]
            final_salary = active_salaries[-1] if active_salaries else context.monthly_salary
            monthly_benefit_amount = final_salary * (replacement_rate / 100)
        else:  # 'VALUE'
            monthly_benefit_amount = state.target_benefit if state.target_benefit is not None else 0
        
        # Projeção de benefícios mensais considerando múltiplos pagamentos anuais
        monthly_benefits = []
        for month in projection_months:
            if month >= months_to_retirement:  # Fase aposentado: meses months_to_retirement em diante
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
                print(f"[ENGINE_DEBUG] Mês {month}: saldo antes taxa adm: {accumulated}")
            
            accumulated *= (1 - context.admin_fee_monthly)
            
            if month < 5:
                print(f"[ENGINE_DEBUG] Mês {month}: saldo após taxa adm: {accumulated}, taxa aplicada: {context.admin_fee_monthly}")
            
            if month < months_to_retirement:  # Fase ativa: acumular contribuições
                # Adicionar contribuição líquida (já com carregamento descontado)
                accumulated += monthly_contributions[month]
            else:
                # Fase aposentado: descontar benefícios
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
            year_reserve = monthly_reserves[min(start_month, len(monthly_reserves)-1)]
            
            yearly_salaries.append(year_salary)
            yearly_benefits.append(year_benefit)
            yearly_contributions.append(year_contribution)
            yearly_survival_probs.append(year_survival_prob)
            yearly_reserves.append(year_reserve)
        
        return {
            "years": list(range(effective_projection_years)),
            "salaries": yearly_salaries,
            "benefits": yearly_benefits,
            "contributions": yearly_contributions,
            "survival_probs": yearly_survival_probs,
            "reserves": yearly_reserves,
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
    
    def _calculate_rmba(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> float:
        """Calcula Reserva Matemática de Benefícios a Conceder (RMBA)"""
        monthly_data = projections["monthly_data"]
        
        # Usar utilitário para calcular VPAs de benefícios e contribuições
        # IMPORTANTE: Agora considera o impacto da taxa administrativa no VPA das contribuições
        vpa_benefits, vpa_contributions = calculate_vpa_benefits_contributions(
            monthly_data["benefits"],
            monthly_data["contributions"],
            monthly_data["survival_probs"],
            context.discount_rate_monthly,
            context.payment_timing,
            context.months_to_retirement,
            context.admin_fee_monthly  # Passa a taxa administrativa
        )
        
        # RMBA = VPA(Benefícios) - VPA(Contribuições)
        return vpa_benefits - vpa_contributions
    
    def _calculate_rmbc(self, state: SimulatorState, projections: Dict) -> float:
        """Calcula Reserva Matemática de Benefícios Concedidos"""
        # Para participante ativo, RMBC = 0
        # Seria calculada após aposentadoria
        return 0.0
    
    def _calculate_normal_cost(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> float:
        """Calcula Custo Normal anual usando base mensal"""
        months_to_retirement = context.months_to_retirement
        
        if state.calculation_method == "PUC":
            # Projected Unit Credit - acumulação mensal do benefício
            monthly_benefit_accrual = (context.monthly_salary * (state.accrual_rate / 100)) / 12
            # Descontar para valor presente usando taxa mensal
            pv_factor = 1 / ((1 + context.discount_rate_monthly) ** months_to_retirement)
            # Retornar custo anual (12 meses)
            return monthly_benefit_accrual * pv_factor * 12
        else:  # EAN
            # Entry Age Normal - distribuir custo total pelos meses de contribuição
            total_cost = self._calculate_rmba(state, context, projections)
            monthly_cost = total_cost / months_to_retirement if months_to_retirement > 0 else 0
            # Retornar custo anual
            return monthly_cost * 12
    
    def _calculate_key_metrics(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> Dict:
        """Calcula métricas-chave usando base atuarial consistente"""
        total_contributions = sum(projections["contributions"])
        total_benefits = sum(projections["benefits"])
        
        # Salário final projetado mensal - calcular salário base sem extras (13º, 14º)
        monthly_data = projections["monthly_data"]
        
        # Calcular salário base mensal final sem extras para base consistente
        months_to_retirement = len([s for s in monthly_data["salaries"] if s > 0])
        if months_to_retirement > 0:
            # Salário base mensal no final da carreira (sem 13º/14º)
            final_salary_monthly_base = context.monthly_salary * ((1 + context.salary_growth_real_monthly) ** (months_to_retirement - 1))
        else:
            final_salary_monthly_base = context.monthly_salary
        
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
    
    def _calculate_sensitivity(self, state: SimulatorState) -> Dict:
        """Calcula análise de sensibilidade"""
        # Criar contexto base e obter tábua de mortalidade
        base_context = ActuarialContext.from_state(state)
        base_mortality_table = get_mortality_table(state.mortality_table, state.gender.value, state.mortality_aggravation)
        base_projections = self._calculate_projections(state, base_context, base_mortality_table)
        base_rmba = self._calculate_rmba(state, base_context, base_projections)
        
        sensitivity = {
            "discount_rate": {},
            "mortality": {},
            "retirement_age": {},
            "salary_growth": {},
            "inflation": {}
        }
        
        # Sensibilidade taxa de desconto
        for rate in [0.04, 0.05, 0.06, 0.07, 0.08]:
            modified_state = state.copy()
            modified_state.discount_rate = rate
            modified_context = ActuarialContext.from_state(modified_state)
            projections = self._calculate_projections(modified_state, modified_context, base_mortality_table)
            rmba = self._calculate_rmba(modified_state, modified_context, projections)
            sensitivity["discount_rate"][rate] = rmba
        
        # Sensibilidade idade aposentadoria
        for age in [60, 62, 65, 67, 70]:
            if age > state.age:
                modified_state = state.copy()
                modified_state.retirement_age = age
                modified_context = ActuarialContext.from_state(modified_state)
                projections = self._calculate_projections(modified_state, modified_context, base_mortality_table)
                rmba = self._calculate_rmba(modified_state, modified_context, projections)
                sensitivity["retirement_age"][age] = rmba
        
        # Sensibilidade crescimento salarial
        for growth in [0.01, 0.02, 0.03, 0.04]:
            modified_state = state.copy()
            modified_state.salary_growth_real = growth
            modified_context = ActuarialContext.from_state(modified_state)
            projections = self._calculate_projections(modified_state, modified_context, base_mortality_table)
            rmba = self._calculate_rmba(modified_state, modified_context, projections)
            sensitivity["salary_growth"][growth] = rmba
        
        # Sensibilidade inflação (removida - não aplicável em cálculos reais)
        # Mantendo estrutura para compatibilidade com interface
        sensitivity["inflation"] = {}
        
        # Sensibilidade mortalidade
        from .mortality_tables import MORTALITY_TABLES
        for table_name in MORTALITY_TABLES.keys():
            try:
                mortality_table = get_mortality_table(table_name, state.gender.value)
                projections = self._calculate_projections(state, base_context, mortality_table)
                rmba = self._calculate_rmba(state, base_context, projections)
                sensitivity["mortality"][table_name] = rmba
            except Exception as e:
                # Se a tábua não estiver disponível, usar valor base
                sensitivity["mortality"][table_name] = base_rmba
        
        return sensitivity
    
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
        
        # Calcular RMBA usando a função dedicada para consistência
        rmba = self._calculate_rmba(state, context, projections)
        
        # Análise de suficiência: Saldo Inicial - RMBA = Superávit
        # Se RMBA for negativo (VPA Contrib > VPA Benefícios), isso indica superávit natural
        deficit_surplus = state.initial_balance - rmba
        
        # Calcular VPA do benefício alvo para cálculo de percentuais
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement
        mortality_table = get_mortality_table(state.mortality_table, state.gender.value, state.mortality_aggravation)
        
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
        
        # Ajuste de timing usando utilitário
        timing_adjustment = get_timing_adjustment(context.payment_timing)
        
        # Para cada ano da projeção, calcular VPAs restantes
        for year_idx in range(len(projections["years"])):
            year_month = year_idx * 12
            
            # VPA dos benefícios futuros a partir deste ano
            vpa_benefits = 0.0
            for month in range(year_month, len(monthly_data["benefits"])):
                if month >= months_to_retirement:
                    benefit = monthly_data["benefits"][month]
                    survival_prob = monthly_data["survival_probs"][month]
                    discount_months = month - year_month
                    if discount_months >= 0:
                        discount_factor = calculate_discount_factor(
                            context.discount_rate_monthly,
                            discount_months,
                            timing_adjustment
                        )
                        vpa_benefits += (benefit * survival_prob) / discount_factor
            
            # VPA das contribuições futuras a partir deste ano
            # CORREÇÃO: Usar mesma metodologia da função _calculate_rmba para consistência
            # Aplicar taxa administrativa usando utilitário dedicado
            if year_month < months_to_retirement:
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
            else:
                # Após aposentadoria, não há mais contribuições
                vpa_contributions = 0.0
            
            # RMBA neste ponto = VPA benefícios - VPA contribuições
            rmba_year = vpa_benefits - vpa_contributions
            
            vpa_benefits_yearly.append(vpa_benefits)
            vpa_contributions_yearly.append(vpa_contributions)
            rmba_evolution_yearly.append(rmba_year)
        
        return {
            "vpa_benefits": vpa_benefits_yearly,
            "vpa_contributions": vpa_contributions_yearly,
            "rmba_evolution": rmba_evolution_yearly
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
        
        # Armazenar taxa de conversão para uso posterior
        context.conversion_rate_monthly = annual_to_monthly_rate(conversion_rate)
        
        return context
    
    def _calculate_cd_projections(self, state: SimulatorState, context: ActuarialContext, mortality_table: np.ndarray) -> Dict:
        """Calcula projeções específicas para CD - foco na evolução do saldo"""
        total_months = context.total_months_projection
        months_to_retirement = context.months_to_retirement
        projection_months = list(range(total_months))
        
        # Projeções salariais (mesmo cálculo que BD)
        monthly_salaries = []
        for month in projection_months:
            if month < months_to_retirement:
                base_monthly_salary = context.monthly_salary * ((1 + context.salary_growth_real_monthly) ** month)
                current_month_in_year = month % 12
                monthly_salary = base_monthly_salary
                
                # Pagamentos extras (13º, 14º, etc.)
                extra_payments = context.salary_months_per_year - 12
                if extra_payments > 0:
                    if current_month_in_year == 11:  # Dezembro
                        if extra_payments >= 1:
                            monthly_salary += base_monthly_salary
                    if current_month_in_year == 0 and month > 0:  # Janeiro
                        if extra_payments >= 2:
                            monthly_salary += base_monthly_salary
            else:
                monthly_salary = 0.0
            monthly_salaries.append(monthly_salary)
        
        # Contribuições mensais
        monthly_contributions = []
        for monthly_salary in monthly_salaries:
            contribution_gross = monthly_salary * (state.contribution_rate / 100)
            contribution_net = contribution_gross * (1 - context.loading_fee_rate)
            monthly_contributions.append(contribution_net)
        
        # Probabilidades de sobrevivência (mesmo cálculo que BD)
        monthly_survival_probs = []
        cumulative_survival = 1.0
        for month in projection_months:
            current_age_years = state.age + (month / 12)
            age_index = int(current_age_years)
            
            if age_index < len(mortality_table) and age_index >= 0:
                q_x_annual = mortality_table[age_index]
                if 0 <= q_x_annual <= 1:
                    q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                    p_x_monthly = 1 - q_x_monthly
                    cumulative_survival *= p_x_monthly
                else:
                    cumulative_survival *= 1.0
            else:
                cumulative_survival = 0.0
            
            cumulative_survival = max(0.0, cumulative_survival)
            monthly_survival_probs.append(cumulative_survival)
        
        # Calcular renda mensal base primeiro (estimativa inicial)
        # Usaremos o saldo final estimado para calcular a renda mensal
        temp_final_balance = state.initial_balance
        for month in range(months_to_retirement):
            temp_final_balance *= (1 + context.discount_rate_monthly)
            temp_final_balance *= (1 - context.admin_fee_monthly)
            monthly_contribution = monthly_contributions[month] if month < len(monthly_contributions) else 0
            temp_final_balance += monthly_contribution
        
        monthly_income = self._calculate_cd_monthly_income_simple(state, context, temp_final_balance, mortality_table)
        
        # EVOLUÇÃO DO SALDO CD - CORE LOGIC
        monthly_balances = []
        accumulated_balance = state.initial_balance
        
        # Determinar período de benefícios baseado na modalidade de conversão
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        benefit_period_months = None
        
        if conversion_mode in [CDConversionMode.CERTAIN_5Y, CDConversionMode.CERTAIN_10Y, 
                               CDConversionMode.CERTAIN_15Y, CDConversionMode.CERTAIN_20Y]:
            # Renda certa por N anos
            years_map = {
                CDConversionMode.CERTAIN_5Y: 5,
                CDConversionMode.CERTAIN_10Y: 10,
                CDConversionMode.CERTAIN_15Y: 15,
                CDConversionMode.CERTAIN_20Y: 20
            }
            benefit_period_months = years_map[conversion_mode] * 12
        # Para ACTUARIAL (vitalícia) e outros modos, benefit_period_months fica None (sem limite)
        
        for month in projection_months:
            # Durante acumulação: capitalizar com taxa de acumulação
            if month < months_to_retirement:
                # Capitalizar saldo com taxa de acumulação mensal
                accumulated_balance *= (1 + context.discount_rate_monthly)
                
                # Aplicar taxa administrativa mensal
                accumulated_balance *= (1 - context.admin_fee_monthly)
                
                # Adicionar contribuição líquida
                accumulated_balance += monthly_contributions[month]
                
                monthly_balances.append(max(0, accumulated_balance))
            else:
                # Durante aposentadoria: verificar se ainda está no período de benefícios
                months_since_retirement = month - months_to_retirement
                
                # No primeiro mês da aposentadoria, registrar pico ANTES do primeiro saque
                if months_since_retirement == 0:
                    monthly_balances.append(max(0, accumulated_balance))  # Pico real aos 65 anos
                
                # Se há limite de tempo e já passou, não consumir mais saldo
                if benefit_period_months is not None and months_since_retirement >= benefit_period_months:
                    # Período de benefícios acabou, apenas capitalizar saldo restante
                    accumulated_balance *= (1 + context.conversion_rate_monthly)
                else:
                    # Ainda no período de benefícios: saldo é consumido pelos benefícios
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
                    
                    # Consumir o saldo com o pagamento do benefício
                    accumulated_balance -= monthly_benefit_payment
                    
                    # Continuar capitalização do saldo restante com taxa de conversão
                    accumulated_balance *= (1 + context.conversion_rate_monthly)
                
                # Para meses após o primeiro mês da aposentadoria
                if months_since_retirement > 0:
                    monthly_balances.append(max(0, accumulated_balance))
        
        # Saldo final na aposentadoria (no momento exato da aposentadoria)
        final_balance = monthly_balances[months_to_retirement] if months_to_retirement < len(monthly_balances) else accumulated_balance
        
        # Recalcular array de benefícios mensais para os gráficos
        monthly_benefits = []
        for month in projection_months:
            if month >= months_to_retirement:
                # Verificar se ainda está no período de benefícios
                months_since_retirement = month - months_to_retirement
                
                # Se há limite de tempo e já passou, benefício = 0
                if benefit_period_months is not None and months_since_retirement >= benefit_period_months:
                    monthly_benefits.append(0.0)
                else:
                    # Ainda no período de benefícios
                    current_month_in_year = month % 12
                    monthly_benefit = monthly_income
                    
                    extra_payments = context.benefit_months_per_year - 12
                    if extra_payments > 0:
                        if current_month_in_year == 11:  # Dezembro
                            if extra_payments >= 1:
                                monthly_benefit += monthly_income
                        if current_month_in_year == 0:  # Janeiro
                            if extra_payments >= 2:
                                monthly_benefit += monthly_income
                    
                    monthly_benefits.append(monthly_benefit)
            else:
                monthly_benefits.append(0.0)
        
        # Converter para anos
        effective_projection_years = len(projection_months) // 12
        yearly_salaries = []
        yearly_benefits = []
        yearly_contributions = []
        yearly_survival_probs = []
        yearly_balances = []
        
        for year_idx in range(effective_projection_years):
            start_month = year_idx * 12
            end_month = min((year_idx + 1) * 12, len(monthly_salaries))
            
            year_salary = sum(monthly_salaries[start_month:end_month])
            year_benefit = sum(monthly_benefits[start_month:end_month])
            year_contribution = sum(monthly_contributions[start_month:end_month])
            year_survival_prob = monthly_survival_probs[min(end_month-1, len(monthly_survival_probs)-1)]
            year_balance = monthly_balances[min(start_month, len(monthly_balances)-1)]
            
            yearly_salaries.append(year_salary)
            yearly_benefits.append(year_benefit)
            yearly_contributions.append(year_contribution)
            yearly_survival_probs.append(year_survival_prob)
            yearly_balances.append(year_balance)
        
        return {
            "years": list(range(effective_projection_years)),
            "salaries": yearly_salaries,
            "benefits": yearly_benefits,
            "contributions": yearly_contributions,
            "survival_probs": yearly_survival_probs,
            "balances": yearly_balances,  # Evolução do saldo ao invés de reserves
            "final_balance": final_balance,
            "monthly_data": {
                "months": projection_months,
                "salaries": monthly_salaries,
                "benefits": monthly_benefits,
                "contributions": monthly_contributions,
                "survival_probs": monthly_survival_probs,
                "balances": monthly_balances
            }
        }
    
    def _calculate_cd_monthly_income_simple(self, state: SimulatorState, context: ActuarialContext, balance: float, mortality_table: np.ndarray) -> float:
        """Cálculo simplificado da renda mensal CD para uso interno"""
        if balance <= 0:
            return 0.0
        
        conversion_mode = state.cd_conversion_mode or CDConversionMode.ACTUARIAL
        
        if conversion_mode == CDConversionMode.ACTUARIAL:
            # Anuidade vitalícia usando tábua de mortalidade
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
            monthly_rate = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
            
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
            percentage = state.cd_withdrawal_percentage or 5.0  # 5% default
            return (balance * (percentage / 100)) / 12  # Converter para mensal
        
        else:  # PROGRAMMED - simplificado
            # Saque programado por 20 anos (default)
            return balance / (20 * 12)
    
    def _calculate_actuarial_annuity(self, balance: float, state: SimulatorState, context: ActuarialContext, mortality_table: np.ndarray) -> float:
        """Calcula anuidade vitalícia atuarial"""
        monthly_rate = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
        
        # Calcular fator de anuidade vitalícia
        annuity_factor = 0.0
        cumulative_survival = 1.0
        
        # Calcular até 50 anos após aposentadoria (idade limite)
        max_months = min(50 * 12, (110 - state.retirement_age) * 12)
        
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
    
    def _calculate_cd_metrics(self, state: SimulatorState, projections: Dict, monthly_income: float) -> Dict:
        """Calcula métricas específicas para CD"""
        total_contributions = sum(projections["contributions"])
        total_benefits = sum(projections["benefits"])
        
        # Salário final para cálculo de taxa de reposição
        active_salaries = [s for s in projections["monthly_data"]["salaries"] if s > 0]
        final_monthly_salary_base = active_salaries[-1] if active_salaries else state.salary
        
        # Taxa de reposição baseada na renda CD calculada
        replacement_ratio = (monthly_income / final_monthly_salary_base * 100) if final_monthly_salary_base > 0 else 0
        
        # Taxa de reposição alvo (baseada no input do usuário)
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            target_replacement_ratio = state.target_replacement_rate or 70.0
        else:
            target_replacement_ratio = replacement_ratio  # Se não especificado, usar o calculado
        
        # Taxa de reposição sustentável (para CD, é a própria taxa calculada)
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
        for mode in CDConversionMode:
            temp_state = state.model_copy()
            temp_state.cd_conversion_mode = mode
            
            monthly_income = self._calculate_cd_monthly_income_simple(temp_state, context, balance, mortality_table)
            modes_analysis[mode.value] = {
                "monthly_income": monthly_income,
                "annual_income": monthly_income * 12,
                "description": self._get_conversion_mode_description(mode)
            }
        
        return modes_analysis
    
    def _get_conversion_mode_description(self, mode: CDConversionMode) -> str:
        """Retorna descrição da modalidade de conversão"""
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
        
        # Para modalidades vitalícias ou dinâmicas, simular mês a mês
        remaining_balance = balance
        months_count = 0
        max_months = 50 * 12  # Limite máximo de 50 anos
        
        # Probabilidade de sobrevivência acumulada
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
                percentage = state.cd_withdrawal_percentage or 5.0
                monthly_income = (remaining_balance * (percentage / 100)) / 12
                if monthly_income < 1.0:  # Critério de parada quando renda fica muito baixa
                    break
        
        # Se chegou ao limite de 50 anos ou sobrevivência muito baixa, considerar vitalício
        if months_count >= max_months or (conversion_mode == CDConversionMode.ACTUARIAL and cumulative_survival <= 0.01):
            return 50.0  # Máximo de 50 anos para benefícios vitalícios (JSON-safe)
        
        return months_count / 12.0  # Converter para anos

    def _calculate_cd_sensitivity(self, state: SimulatorState) -> Dict:
        """Calcula análise de sensibilidade específica para CD"""
        # Simplificado - pode ser expandido conforme necessário
        return {
            "accumulation_rate": {},  # Sensibilidade à taxa de acumulação
            "conversion_rate": {},    # Sensibilidade à taxa de conversão
            "mortality": {},
            "retirement_age": {},
            "salary_growth": {}
        }