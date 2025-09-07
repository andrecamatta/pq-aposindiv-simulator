"""
Funções matemáticas básicas para cálculos atuariais
Extraído de actuarial_math.py para melhor organização
"""

import numpy as np
from typing import List, Optional


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
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    adjusted_periods = periods + timing_adjustment
    return (1 + rate) ** (-adjusted_periods)


def calculate_annuity_factor(
    rate: float,
    periods: int,
    timing: str = "postecipado",
    survival_probs: Optional[List[float]] = None
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
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    annuity_factor = 0.0
    
    for period in range(periods):
        adjusted_period = period + timing_adjustment
        discount_factor = (1 + rate) ** (-adjusted_period)
        
        survival_prob = survival_probs[period] if survival_probs and period < len(survival_probs) else 1.0
        annuity_factor += survival_prob * discount_factor
    
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
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    annuity_factor = 0.0
    
    for period in range(start_period, len(survival_probs)):
        adjusted_period = period + timing_adjustment
        discount_factor = (1 + rate) ** (-adjusted_period)
        annuity_factor += survival_probs[period] * discount_factor
    
    return annuity_factor


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
        return float(mortality_probs[-1]) if len(mortality_probs) > 0 else 1.0
    
    # Interpolação linear
    lower_index = int(age_index)
    upper_index = lower_index + 1
    
    if upper_index >= len(mortality_probs):
        return float(mortality_probs[lower_index])
    
    weight = age_index - lower_index
    interpolated = float(mortality_probs[lower_index]) * (1 - weight) + float(mortality_probs[upper_index]) * weight
    
    return interpolated


def compound_growth(
    initial_value: float,
    growth_rate: float,
    periods: int,
    compounding_frequency: str = "monthly"
) -> List[float]:
    """
    Calcula crescimento composto ao longo do tempo
    
    Args:
        initial_value: Valor inicial
        growth_rate: Taxa de crescimento por período
        periods: Número de períodos
        compounding_frequency: "monthly" ou "annual"
    
    Returns:
        Lista de valores projetados
    """
    values = []
    
    for period in range(periods):
        if compounding_frequency == "monthly":
            growth_factor = (1 + growth_rate) ** period
        elif compounding_frequency == "annual":
            # Para crescimento anual aplicado mensalmente
            years_elapsed = period / 12
            growth_factor = (1 + growth_rate) ** years_elapsed
        else:
            growth_factor = (1 + growth_rate) ** period
        
        projected_value = initial_value * growth_factor
        values.append(projected_value)
    
    return values


def present_value_stream(
    cash_flows: List[float],
    discount_rate: float,
    timing: str = "postecipado"
) -> float:
    """
    Calcula valor presente de um fluxo de caixa
    
    Args:
        cash_flows: Lista de fluxos por período
        discount_rate: Taxa de desconto por período
        timing: "antecipado" ou "postecipado"
    
    Returns:
        Valor presente total
    """
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    pv_total = 0.0
    
    for period, cash_flow in enumerate(cash_flows):
        if cash_flow != 0:  # Otimização: pular fluxos zero
            adjusted_period = period + timing_adjustment
            pv_factor = (1 + discount_rate) ** (-adjusted_period)
            pv_total += cash_flow * pv_factor
    
    return pv_total


def annuity_due_factor(rate: float, periods: int) -> float:
    """
    Calcula fator de anuidade antecipada (pagamentos no início)
    
    Args:
        rate: Taxa por período
        periods: Número de períodos
    
    Returns:
        Fator de anuidade antecipada
    """
    if rate == 0:
        return periods
    
    return (1 - (1 + rate) ** (-periods)) / rate * (1 + rate)


def annuity_immediate_factor(rate: float, periods: int) -> float:
    """
    Calcula fator de anuidade postecipada (pagamentos no final)
    
    Args:
        rate: Taxa por período
        periods: Número de períodos
    
    Returns:
        Fator de anuidade postecipada
    """
    if rate == 0:
        return periods
    
    return (1 - (1 + rate) ** (-periods)) / rate