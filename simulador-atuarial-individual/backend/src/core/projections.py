"""
Módulo para cálculo de projeções temporais atuariais
Consolida lógica comum entre BD e CD
"""

import numpy as np
from typing import Dict, List, TYPE_CHECKING
from ..utils.rates import annual_to_monthly_rate

if TYPE_CHECKING:
    from ..models.database import SimulatorState
    from .actuarial_engine import ActuarialContext


def calculate_salary_projections(
    context: 'ActuarialContext',
    state: 'SimulatorState', 
    total_months: int
) -> List[float]:
    """
    Calcula projeções salariais mensais considerando múltiplos pagamentos anuais
    
    Args:
        context: Contexto atuarial com taxas mensais
        state: Estado do simulador
        total_months: Total de meses para projeção
        
    Returns:
        Lista de salários mensais projetados
    """
    monthly_salaries = []
    months_to_retirement = context.months_to_retirement
    
    for month in range(total_months):
        # Para aposentados: sem salários futuros
        if context.is_already_retired:
            monthly_salary = 0.0
        elif month < months_to_retirement:  # Fase ativa
            # Crescimento anual aplicado no início de cada ano
            year_number = month // 12
            base_monthly_salary = context.monthly_salary * ((1 + state.salary_growth_real) ** year_number)
            
            # Lógica de pagamentos: todos os 12 meses têm pagamento base
            # Meses específicos têm pagamentos extras (13º, 14º, etc.)
            current_month_in_year = month % 12
            
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
    
    return monthly_salaries


def calculate_benefit_projections(
    context: 'ActuarialContext',
    state: 'SimulatorState',
    total_months: int,
    monthly_benefit_amount: float
) -> List[float]:
    """
    Calcula projeções de benefícios mensais considerando múltiplos pagamentos anuais
    
    Args:
        context: Contexto atuarial
        state: Estado do simulador
        total_months: Total de meses para projeção
        monthly_benefit_amount: Valor do benefício mensal base
        
    Returns:
        Lista de benefícios mensais projetados
    """
    monthly_benefits = []
    months_to_retirement = context.months_to_retirement
    
    for month in range(total_months):
        # Para aposentados: benefícios começam imediatamente (mês 0)
        # Para ativos: benefícios começam em months_to_retirement
        benefit_starts = context.is_already_retired or (month >= months_to_retirement)
        
        if benefit_starts:  # Fase aposentado ou aposentadoria futura
            # Lógica de pagamentos: todos os 12 meses têm pagamento base
            # Meses específicos têm pagamentos extras (13º, 14º, etc.)
            current_month_in_year = month % 12
            
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
    
    return monthly_benefits


def calculate_contribution_projections(
    monthly_salaries: List[float],
    state: 'SimulatorState',
    context: 'ActuarialContext'
) -> List[float]:
    """
    Calcula projeções de contribuições mensais
    
    Args:
        monthly_salaries: Lista de salários mensais
        state: Estado do simulador
        context: Contexto atuarial
        
    Returns:
        Lista de contribuições mensais líquidas (após carregamento)
    """
    monthly_contributions = []
    
    for monthly_salary in monthly_salaries:
        # Aposentados não fazem contribuições
        if context.is_already_retired:
            contribution_net = 0.0
        else:
            contribution_gross = monthly_salary * (state.contribution_rate / 100)
            contribution_net = contribution_gross * (1 - context.loading_fee_rate)
        
        monthly_contributions.append(contribution_net)
    
    return monthly_contributions


def calculate_survival_probabilities(
    state: 'SimulatorState',
    mortality_table: np.ndarray,
    total_months: int
) -> List[float]:
    """
    Calcula probabilidades de sobrevivência mensais cumulativas
    
    Args:
        state: Estado do simulador
        mortality_table: Tábua de mortalidade
        total_months: Total de meses para projeção
        
    Returns:
        Lista de probabilidades de sobrevivência cumulativas
    """
    monthly_survival_probs = []
    cumulative_survival = 1.0
    
    for month in range(total_months):
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
    
    return monthly_survival_probs


def calculate_accumulated_reserves(
    state: 'SimulatorState',
    context: 'ActuarialContext',
    monthly_contributions: List[float],
    monthly_benefits: List[float],
    total_months: int
) -> List[float]:
    """
    Calcula evolução das reservas acumuladas considerando custos administrativos
    
    Args:
        state: Estado do simulador
        context: Contexto atuarial
        monthly_contributions: Lista de contribuições mensais
        monthly_benefits: Lista de benefícios mensais
        total_months: Total de meses para projeção
        
    Returns:
        Lista de reservas acumuladas mensais
    """
    monthly_reserves = []
    accumulated = state.initial_balance  # Iniciar com saldo inicial
    months_to_retirement = context.months_to_retirement
    
    for month in range(total_months):
        # Capitalizar saldo existente mensalmente
        accumulated *= (1 + context.discount_rate_monthly)
        
        # Aplicar taxa administrativa mensal sobre o saldo
        accumulated *= (1 - context.admin_fee_monthly)
        
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
    
    return monthly_reserves


def convert_monthly_to_yearly_projections(
    monthly_data: Dict[str, List[float]],
    total_months: int
) -> Dict[str, List[float]]:
    """
    Converte dados mensais para anuais considerando corretamente múltiplos pagamentos
    
    Args:
        monthly_data: Dicionário com dados mensais
        total_months: Total de meses processados
        
    Returns:
        Dicionário com dados anuais agregados
    """
    effective_projection_years = total_months // 12
    
    yearly_salaries = []
    yearly_benefits = []
    yearly_contributions = []
    yearly_survival_probs = []
    yearly_reserves = []
    
    for year_idx in range(effective_projection_years):
        start_month = year_idx * 12
        end_month = min((year_idx + 1) * 12, total_months)
        
        # Somatório anual considerando todos os pagamentos do ano
        # IMPORTANTE: Agora soma corretamente todos os pagamentos mensais
        year_salary = sum(monthly_data["salaries"][start_month:end_month])
        year_benefit = sum(monthly_data["benefits"][start_month:end_month])
        year_contribution = sum(monthly_data["contributions"][start_month:end_month])
        
        # Probabilidade de sobrevivência no final do ano
        year_survival_prob = monthly_data["survival_probs"][min(end_month-1, len(monthly_data["survival_probs"])-1)]
        
        # Reserva no início do ano
        year_reserve = monthly_data["reserves"][min(start_month, len(monthly_data["reserves"])-1)]
        
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
        "reserves": yearly_reserves
    }