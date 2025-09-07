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
    calculate_sustainable_benefit
)

from .projection_math import (
    project_salary_growth,
    calculate_contribution_stream,
    calculate_benefit_stream,
    calculate_survival_probabilities_detailed,
    calculate_net_present_value
)

from .advanced_actuarial import (
    solve_target_benefit,
    calculate_life_expectancy,
    calculate_normal_cost_puc,
    calculate_normal_cost_ean
)

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
    
    # Projeções
    'project_salary_growth',
    'calculate_contribution_stream',
    'calculate_benefit_stream',
    'calculate_survival_probabilities_detailed',
    'calculate_net_present_value',
    
    # Atuarial avançado
    'solve_target_benefit',
    'calculate_life_expectancy',
    'calculate_normal_cost_puc',
    'calculate_normal_cost_ean'
]