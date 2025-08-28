import numpy as np
from typing import List, Union


def present_value(cash_flows: List[float], discount_rate: float, periods: List[int] = None) -> float:
    """Calcula o valor presente de uma série de fluxos de caixa"""
    if periods is None:
        periods = list(range(1, len(cash_flows) + 1))
    
    pv = 0.0
    for i, cf in enumerate(cash_flows):
        if i < len(periods):
            pv += cf / ((1 + discount_rate) ** periods[i])
    
    return pv


def annuity_value(payment: float, discount_rate: float, periods: int, due: bool = False) -> float:
    """Calcula o valor presente de uma anuidade"""
    if discount_rate == 0:
        return payment * periods
    
    # Anuidade ordinária (postecipada)
    pv = payment * ((1 - (1 + discount_rate) ** -periods) / discount_rate)
    
    # Anuidade antecipada (due)
    if due:
        pv *= (1 + discount_rate)
    
    return pv


def life_annuity_value(payment: float, discount_rate: float, survival_probs: List[float]) -> float:
    """Calcula o valor presente de uma anuidade de vida"""
    pv = 0.0
    
    for i, prob in enumerate(survival_probs):
        if prob > 0:
            period = i + 1
            pv += payment * prob / ((1 + discount_rate) ** period)
    
    return pv


def compound_interest(principal: float, rate: float, periods: int, frequency: int = 1) -> float:
    """Calcula juros compostos"""
    return principal * ((1 + rate / frequency) ** (frequency * periods))


def effective_rate(nominal_rate: float, frequency: int) -> float:
    """Converte taxa nominal para taxa efetiva"""
    return (1 + nominal_rate / frequency) ** frequency - 1


def duration(cash_flows: List[float], discount_rate: float, periods: List[int] = None) -> float:
    """Calcula a duração (duration) de uma série de fluxos de caixa"""
    if periods is None:
        periods = list(range(1, len(cash_flows) + 1))
    
    present_values = []
    weighted_periods = []
    
    for i, cf in enumerate(cash_flows):
        if i < len(periods) and cf != 0:
            pv = cf / ((1 + discount_rate) ** periods[i])
            present_values.append(pv)
            weighted_periods.append(pv * periods[i])
    
    total_pv = sum(present_values)
    
    if total_pv == 0:
        return 0.0
    
    return sum(weighted_periods) / total_pv


def convexity(cash_flows: List[float], discount_rate: float, periods: List[int] = None) -> float:
    """Calcula a convexidade de uma série de fluxos de caixa"""
    if periods is None:
        periods = list(range(1, len(cash_flows) + 1))
    
    present_values = []
    weighted_convexity = []
    
    for i, cf in enumerate(cash_flows):
        if i < len(periods) and cf != 0:
            pv = cf / ((1 + discount_rate) ** periods[i])
            present_values.append(pv)
            weighted_convexity.append(pv * periods[i] * (periods[i] + 1))
    
    total_pv = sum(present_values)
    
    if total_pv == 0:
        return 0.0
    
    return sum(weighted_convexity) / (total_pv * (1 + discount_rate) ** 2)


def irr(cash_flows: List[float], guess: float = 0.1, max_iterations: int = 100) -> float:
    """Calcula a Taxa Interna de Retorno (TIR) usando método Newton-Raphson"""
    
    def npv(rate: float) -> float:
        return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
    
    def npv_derivative(rate: float) -> float:
        return sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
    
    rate = guess
    
    for _ in range(max_iterations):
        npv_value = npv(rate)
        npv_deriv = npv_derivative(rate)
        
        if abs(npv_value) < 1e-6:
            return rate
        
        if abs(npv_deriv) < 1e-10:
            break
        
        rate = rate - npv_value / npv_deriv
    
    return rate


def mortality_adjusted_pv(cash_flows: List[float], discount_rate: float, 
                         survival_probs: List[float]) -> float:
    """Calcula valor presente ajustado por mortalidade"""
    pv = 0.0
    
    for i, (cf, prob) in enumerate(zip(cash_flows, survival_probs)):
        if cf != 0 and prob > 0:
            period = i + 1
            pv += cf * prob / ((1 + discount_rate) ** period)
    
    return pv