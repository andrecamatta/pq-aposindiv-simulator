"""
Módulo de cálculos matemáticos atuariais centralizados
Consolida todas as funções de cálculo em um local organizado
"""

from .basic_math import (
    calculate_discount_factor,
    calculate_annuity_factor,
    calculate_life_annuity_factor,
    interpolate_mortality_table
)

from .vpa_calculations import (
    calculate_actuarial_present_value,
    calculate_vpa_benefits_contributions,
    calculate_sustainable_benefit,
    calculate_life_annuity_immediate,
    calculate_life_annuity_due,
    calculate_deferred_annuity,
    get_payment_survival_probability,
    validate_actuarial_inputs,
    calculate_life_annuity_factor,
    calculate_vpa_contributions_with_admin_fees,
    calculate_parameter_to_zero_deficit,
    calculate_optimal_contribution_rate,
    calculate_optimal_retirement_age,
    calculate_sustainable_benefit_with_engine
)

# Módulos projection_math e advanced_actuarial não existem ainda
# TODO: Implementar quando necessário

__all__ = [
    # Matemática básica
    'calculate_discount_factor',
    'calculate_annuity_factor',
    'calculate_life_annuity_factor',
    'interpolate_mortality_table',

    # Cálculos VPA
    'calculate_actuarial_present_value',
    'calculate_vpa_benefits_contributions',
    'calculate_sustainable_benefit',
    'calculate_life_annuity_immediate',
    'calculate_life_annuity_due',
    'calculate_deferred_annuity',
    'get_payment_survival_probability',
    'validate_actuarial_inputs',
    'calculate_life_annuity_factor',
    'calculate_vpa_contributions_with_admin_fees',
    'calculate_parameter_to_zero_deficit',
    'calculate_optimal_contribution_rate',
    'calculate_optimal_retirement_age',
    'calculate_sustainable_benefit_with_engine'
]