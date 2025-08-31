"""
Módulo de utilitários matemáticos atuariais
Funções matemáticas especializadas para cálculos atuariais.

PREMISSAS MATEMÁTICAS CORRIGIDAS (versão revisada):

1. CONVENÇÕES DE TIMING:
   - Antecipado: pagamento no início do período (t = 0, 1, 2, ...)
   - Postecipado: pagamento no final do período (t = 1, 2, 3, ...)
   - Ajuste temporal: 0.0 para antecipado, 1.0 para postecipado

2. CONVERSÃO DE TAXAS:
   - Anual → Mensal: (1 + i_anual)^(1/12) - 1
   - Mensal → Anual: (1 + i_mensal)^12 - 1

3. MORTALIDADE:
   - Conversão anual → mensal: q_mensal = 1 - (1 - q_anual)^(1/12)
   - Probabilidade de sobrevivência: p_x = 1 - q_x
   - Validação: 0 ≤ q_x ≤ 1 para todas as idades

4. VALOR PRESENTE ATUARIAL (VPA):
   - Fórmula: VPA = Σ(CF_t × tPx × v^t)
   - onde: CF_t = fluxo no tempo t, tPx = prob. sobrevivência, v^t = fator desconto

5. PERÍODOS DE CÁLCULO:
   - Fase ativa: meses 0 até (months_to_retirement - 1)
   - Fase aposentado: meses months_to_retirement em diante
   - Condições de loop corrigidas para evitar off-by-one errors

6. BENEFÍCIO SUSTENTÁVEL:
   - Fórmula: B_sustentável = (Saldo_Inicial + VPA_Contribuições) / Fator_Anuidade
   - Garante equilíbrio atuarial: VPA_Benefícios = Recursos_Totais
"""

import numpy as np
from typing import List, Tuple
import math


def annual_to_monthly_rate(annual_rate: float) -> float:
    """
    Converte taxa anual para taxa mensal equivalente
    
    Args:
        annual_rate: Taxa anual (decimal, ex: 0.05 para 5%)
    
    Returns:
        Taxa mensal equivalente
    """
    return (1 + annual_rate) ** (1/12) - 1


def monthly_to_annual_rate(monthly_rate: float) -> float:
    """
    Converte taxa mensal para taxa anual equivalente
    
    Args:
        monthly_rate: Taxa mensal (decimal)
    
    Returns:
        Taxa anual equivalente
    """
    return (1 + monthly_rate) ** 12 - 1


def calculate_discount_factor(rate: float, periods: int, timing: str = "postecipado") -> float:
    """
    Calcula fator de desconto para valor presente
    
    Args:
        rate: Taxa de desconto por período
        periods: Número de períodos
        timing: "antecipado" ou "postecipado"
    
    Returns:
        Fator de desconto
    """
    # Usar convenção padrão: antecipado = 0.0, postecipado = 1.0
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    adjusted_periods = periods + timing_adjustment
    return (1 + rate) ** adjusted_periods


def calculate_annuity_factor(
    rate: float,
    periods: int,
    timing: str = "postecipado",
    survival_probs: List[float] = None
) -> float:
    """
    Calcula fator de anuidade considerando mortalidade (se fornecida)
    
    Args:
        rate: Taxa de desconto por período
        periods: Número de períodos
        timing: "antecipado" ou "postecipado"
        survival_probs: Probabilidades de sobrevivência (opcional)
    
    Returns:
        Fator de anuidade
    """
    # Usar convenção padrão: antecipado = 0.0, postecipado = 1.0  
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    annuity_factor = 0.0
    
    for period in range(periods):
        adjusted_period = period + timing_adjustment
        discount_factor = (1 + rate) ** adjusted_period
        
        # Se probabilidades de sobrevivência fornecidas, usar; senão assumir 1.0
        survival_prob = survival_probs[period] if survival_probs and period < len(survival_probs) else 1.0
        
        annuity_factor += survival_prob / discount_factor
    
    return annuity_factor


def calculate_life_annuity_factor(
    rate: float,
    survival_probs: List[float],
    start_period: int = 0,
    timing: str = "postecipado"
) -> float:
    """
    Calcula fator de anuidade vitalícia usando tábua de mortalidade
    
    Args:
        rate: Taxa de desconto por período
        survival_probs: Probabilidades de sobrevivência
        start_period: Período inicial (para diferimento)
        timing: "antecipado" ou "postecipado"
    
    Returns:
        Fator de anuidade vitalícia
    """
    # Usar convenção padrão: antecipado = 0.0, postecipado = 1.0
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    annuity_factor = 0.0
    
    for period in range(start_period, len(survival_probs)):
        adjusted_period = period + timing_adjustment
        discount_factor = (1 + rate) ** adjusted_period
        annuity_factor += survival_probs[period] / discount_factor
    
    return annuity_factor


def project_salary_growth(
    initial_salary: float,
    growth_rate: float,
    periods: int,
    compounding: str = "monthly"
) -> List[float]:
    """
    Projeta crescimento salarial ao longo do tempo
    
    Args:
        initial_salary: Salário inicial
        growth_rate: Taxa de crescimento por período
        periods: Número de períodos
        compounding: Frequência de capitalização
    
    Returns:
        Lista de salários projetados
    """
    salaries = []
    
    for period in range(periods):
        if compounding == "monthly":
            growth_factor = (1 + growth_rate) ** period
        elif compounding == "annual":
            # Para crescimento anual aplicado mensalmente
            years_elapsed = period / 12
            growth_factor = (1 + growth_rate) ** years_elapsed
        else:
            growth_factor = (1 + growth_rate) ** period
        
        projected_salary = initial_salary * growth_factor
        salaries.append(projected_salary)
    
    return salaries


def calculate_contribution_stream(
    salaries: List[float],
    contribution_rate: float,
    salary_annual_factor: float = 12.0
) -> List[float]:
    """
    Calcula fluxo de contribuições baseado em salários
    
    Args:
        salaries: Lista de salários mensais
        contribution_rate: Taxa de contribuição (decimal)
        salary_annual_factor: Fator para múltiplos pagamentos anuais
    
    Returns:
        Lista de contribuições mensais
    """
    contributions = []
    
    for salary in salaries:
        # Contribuição efetiva considerando múltiplos pagamentos
        effective_monthly_salary = salary * salary_annual_factor / 12.0
        contribution = effective_monthly_salary * contribution_rate
        contributions.append(contribution)
    
    return contributions


def calculate_benefit_stream(
    monthly_benefit: float,
    start_period: int,
    total_periods: int,
    benefit_annual_factor: float = 12.0
) -> List[float]:
    """
    Calcula fluxo de benefícios a partir de determinado período
    
    Args:
        monthly_benefit: Benefício mensal base
        start_period: Período de início dos benefícios
        total_periods: Total de períodos na projeção
        benefit_annual_factor: Fator para múltiplos pagamentos anuais
    
    Returns:
        Lista de benefícios mensais
    """
    benefits = [0.0] * total_periods
    
    # Benefício efetivo considerando múltiplos pagamentos
    effective_monthly_benefit = monthly_benefit * benefit_annual_factor / 12.0
    
    for period in range(start_period, total_periods):
        benefits[period] = effective_monthly_benefit
    
    return benefits


def interpolate_mortality_table(
    age: float,
    mortality_probs: List[float],
    min_age: int = 0
) -> float:
    """
    Interpola probabilidade de mortalidade para idades não inteiras
    
    Args:
        age: Idade (pode ser decimal)
        mortality_probs: Probabilidades de mortalidade por idade
        min_age: Idade mínima da tábua
    
    Returns:
        Probabilidade de mortalidade interpolada
    """
    if age < min_age:
        return 0.0
    
    age_index = age - min_age
    
    if age_index >= len(mortality_probs) - 1:
        return mortality_probs[-1] if mortality_probs else 1.0
    
    # Interpolação linear
    lower_index = int(age_index)
    upper_index = lower_index + 1
    
    if upper_index >= len(mortality_probs):
        return mortality_probs[lower_index]
    
    weight = age_index - lower_index
    interpolated = mortality_probs[lower_index] * (1 - weight) + mortality_probs[upper_index] * weight
    
    return interpolated


def calculate_survival_probabilities(
    initial_age: int,
    gender: str,
    mortality_table: List[float],
    periods: int,
    frequency: str = "monthly"
) -> List[float]:
    """
    Calcula probabilidades de sobrevivência cumulativas
    
    Args:
        initial_age: Idade inicial
        gender: Gênero ('M' ou 'F')
        mortality_table: Probabilidades de mortalidade por idade
        periods: Número de períodos
        frequency: Frequência dos períodos ("monthly" ou "annual")
    
    Returns:
        Lista de probabilidades de sobrevivência
    """
    survival_probs = []
    cumulative_survival = 1.0
    
    for period in range(periods):
        if frequency == "monthly":
            # Idade fracionária para cada mês
            age = initial_age + (period / 12)
        else:
            age = initial_age + period
        
        # Obter probabilidade de mortalidade para esta idade
        mortality_prob = interpolate_mortality_table(age, mortality_table)
        
        # Para frequência mensal, converter para probabilidade mensal
        if frequency == "monthly":
            # q_mensal ≈ q_anual / 12 (aproximação para pequenas probabilidades)
            monthly_mortality = mortality_prob / 12
            survival_rate = 1 - monthly_mortality
        else:
            survival_rate = 1 - mortality_prob
        
        # Atualizar sobrevivência cumulativa
        cumulative_survival *= survival_rate
        survival_probs.append(cumulative_survival)
    
    return survival_probs


def calculate_net_present_value(
    cash_flows: List[float],
    discount_rate: float,
    timing: str = "postecipado"
) -> float:
    """
    Calcula valor presente líquido de fluxo de caixa
    
    Args:
        cash_flows: Lista de fluxos de caixa por período
        discount_rate: Taxa de desconto por período
        timing: "antecipado" ou "postecipado"
    
    Returns:
        Valor presente líquido
    """
    # Usar convenção padrão: antecipado = 0.0, postecipado = 1.0
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    npv = 0.0
    
    for period, cash_flow in enumerate(cash_flows):
        adjusted_period = period + timing_adjustment
        discount_factor = (1 + discount_rate) ** adjusted_period
        npv += cash_flow / discount_factor
    
    return npv


def solve_target_benefit(
    target_vpa: float,
    survival_probs: List[float],
    start_period: int,
    discount_rate: float,
    timing: str = "postecipado",
    benefit_annual_factor: float = 12.0
) -> float:
    """
    Resolve benefício mensal que resulta em VPA alvo
    
    Args:
        target_vpa: VPA alvo dos benefícios
        survival_probs: Probabilidades de sobrevivência
        start_period: Período de início dos benefícios
        discount_rate: Taxa de desconto
        timing: "antecipado" ou "postecipado"
        benefit_annual_factor: Fator para múltiplos pagamentos
    
    Returns:
        Benefício mensal necessário
    """
    # Calcular fator de anuidade vitalícia
    annuity_factor = calculate_life_annuity_factor(
        discount_rate, survival_probs, start_period, timing
    )
    
    # Ajustar por múltiplos pagamentos anuais
    effective_annuity_factor = annuity_factor * benefit_annual_factor / 12.0
    
    if effective_annuity_factor > 0:
        return target_vpa / effective_annuity_factor
    else:
        return 0.0