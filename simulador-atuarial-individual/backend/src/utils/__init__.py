"""
Utilitários reutilizáveis para cálculos atuariais
"""

from .discount import calculate_discount_factor, get_timing_adjustment
from .rates import annual_to_monthly_rate, monthly_to_annual_rate

__all__ = [
    'calculate_discount_factor',
    'get_timing_adjustment',
    'annual_to_monthly_rate',
    'monthly_to_annual_rate'
]
