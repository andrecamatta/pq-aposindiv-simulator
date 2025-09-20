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

# Importar conversores de taxa da versão mais robusta
from ..utils.rates import annual_to_monthly_rate, monthly_to_annual_rate


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
        mortality_probs: Probabilidades de mortalidade por idade (lista ou numpy array)
        min_age: Idade mínima da tábua
    
    Returns:
        Probabilidade de mortalidade interpolada
    """
    if age < min_age:
        return 0.0
    
    age_index = age - min_age
    
    if age_index >= len(mortality_probs) - 1:
        return float(mortality_probs[-1]) if len(mortality_probs) > 0 else 1.0
    
    # Interpolação linear
    lower_index = int(age_index)
    upper_index = lower_index + 1
    
    if upper_index >= len(mortality_probs):
        return float(mortality_probs[lower_index])
    
    weight = age_index - lower_index
    interpolated = float(mortality_probs[lower_index]) * (1 - weight) + float(mortality_probs[upper_index]) * weight
    
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


def calculate_life_expectancy(
    age: int,
    gender: str,
    mortality_table: List[float],
    aggravation_factor: float = 1.0,
    max_age: int = 120
) -> float:
    """
    Calcula a expectativa de vida condicionada à idade atual
    
    Fórmula: E(x) = Σ(i=1 to ∞) [i * p(x,i)]
    onde p(x,i) é a probabilidade de sobreviver i anos a partir da idade x
    
    Args:
        age: Idade atual
        gender: Gênero ('M' ou 'F')
        mortality_table: Lista de probabilidades de mortalidade por idade
        aggravation_factor: Fator de suavização da tábua (1.0 = sem ajuste)
        max_age: Idade máxima para cálculo (default 120)
    
    Returns:
        Expectativa de vida em anos (float)
    """
    if age >= len(mortality_table) or age >= max_age:
        return 0.0
    
    life_expectancy = 0.0
    survival_prob = 1.0  # Probabilidade cumulativa de sobrevivência
    
    for years_ahead in range(1, max_age - age + 1):
        current_age = age + years_ahead - 1
        
        # Verificar se ainda temos dados da tábua
        if current_age >= len(mortality_table):
            break
        
        # Obter probabilidade de mortalidade com interpolação se necessário
        mortality_prob = interpolate_mortality_table(current_age, mortality_table)
        
        # Validar probabilidade de mortalidade
        if mortality_prob is None or not (0 <= mortality_prob <= 1):
            break
        
        # Aplicar fator de suavização (valores <1 reduzem mortalidade, >1 intensificam)
        adjusted_mortality = min(mortality_prob * aggravation_factor, 1.0)
        
        # Calcular probabilidade de sobreviver mais um ano
        annual_survival = 1.0 - adjusted_mortality
        survival_prob *= annual_survival
        
        # Validar probabilidade de sobrevivência
        if not (0 <= survival_prob <= 1) or survival_prob < 1e-10:
            break
        
        # Adicionar à expectativa de vida
        life_expectancy += survival_prob
        
        # Proteger contra valores inválidos
        if life_expectancy > 200 or not isinstance(life_expectancy, (int, float)):
            break
    
    # Garantir que o resultado é válido
    return max(0.0, min(life_expectancy, 200.0))
