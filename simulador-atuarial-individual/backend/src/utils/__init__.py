"""
Utilitários reutilizáveis para cálculos atuariais
"""

from .discount import calculate_discount_factor, get_timing_adjustment
from .rates import annual_to_monthly_rate, monthly_to_annual_rate
# Redirecionamento para módulo consolidado
from ..core.calculations.vpa_calculations import (
    calculate_actuarial_present_value,
    calculate_life_annuity_factor,
    calculate_vpa_benefits_contributions,
    calculate_sustainable_benefit,
    get_payment_survival_probability,
    calculate_vpa_contributions_with_admin_fees,
    calculate_optimal_contribution_rate,
    calculate_optimal_retirement_age
)

__all__ = [
    'calculate_discount_factor',
    'get_timing_adjustment',
    'annual_to_monthly_rate',
    'monthly_to_annual_rate',
    'calculate_actuarial_present_value',
    'calculate_life_annuity_factor',
    'calculate_vpa_benefits_contributions',
    'calculate_sustainable_benefit',
    'get_payment_survival_probability',
    'calculate_vpa_contributions_with_admin_fees',
    'calculate_optimal_contribution_rate',
    'calculate_optimal_retirement_age'
]
