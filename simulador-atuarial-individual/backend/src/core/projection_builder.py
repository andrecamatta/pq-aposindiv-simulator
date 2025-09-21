"""
ProjectionBuilder - Classe para centralizar lógica de montagem de projeções
Elimina duplicação entre BD/CD e consolida cálculos temporais
"""

import numpy as np
from typing import Dict, TYPE_CHECKING
from .projections import (
    calculate_salary_projections,
    calculate_benefit_projections,
    calculate_contribution_projections,
    calculate_survival_probabilities,
    calculate_accumulated_reserves,
    convert_monthly_to_yearly_projections
)

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .actuarial_engine import ActuarialContext


class ProjectionBuilder:
    """
    Centralizador de montagem de projeções mensais/anuais
    Aplica DRY e encapsula lógica comum entre BD/CD
    """

    @classmethod
    def build_bd_projections(
        cls,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        mortality_table: np.ndarray
    ) -> Dict:
        """
        Constrói projeções completas para planos BD usando funções modulares

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            mortality_table: Tábua de mortalidade

        Returns:
            Dicionário com projeções mensais e anuais organizadas
        """
        total_months = context.total_months_projection

        # 1. Projeções salariais mensais (função reutilizável)
        monthly_salaries = calculate_salary_projections(context, state, total_months)

        # 2. Determinar benefício mensal alvo
        monthly_benefit_amount = cls._calculate_target_benefit_amount(state, context, monthly_salaries)

        # 3. Projeções de benefícios mensais (função reutilizável)
        monthly_benefits = calculate_benefit_projections(context, state, total_months, monthly_benefit_amount)

        # 4. Projeções de contribuições mensais (função reutilizável)
        monthly_contributions = calculate_contribution_projections(monthly_salaries, state, context)

        # 5. Probabilidades de sobrevivência (função reutilizável)
        monthly_survival_probs = calculate_survival_probabilities(state, mortality_table, total_months)

        # 6. Evolução das reservas (função reutilizável)
        monthly_reserves = calculate_accumulated_reserves(
            state, context, monthly_contributions, monthly_benefits, total_months
        )

        # 7. Organizar dados mensais
        monthly_data = {
            "months": list(range(total_months)),
            "salaries": monthly_salaries,
            "benefits": monthly_benefits,
            "contributions": monthly_contributions,
            "survival_probs": monthly_survival_probs,
            "reserves": monthly_reserves
        }

        # 8. Converter para dados anuais (função reutilizável)
        yearly_data = convert_monthly_to_yearly_projections(monthly_data, total_months)
        yearly_data["monthly_data"] = monthly_data

        # 9. Gerar vetores por idade para frontend
        age_projections = cls._generate_age_projections(
            state, context, monthly_salaries, monthly_benefits, total_months
        )
        yearly_data.update(age_projections)

        return yearly_data

    @classmethod
    def build_cd_projections(
        cls,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        mortality_table: np.ndarray
    ) -> Dict:
        """
        Constrói projeções completas para planos CD focando na evolução do saldo
        Reutiliza máximo de funções existentes

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            mortality_table: Tábua de mortalidade

        Returns:
            Dicionário com projeções CD organizadas
        """
        total_months = context.total_months_projection
        months_to_retirement = context.months_to_retirement

        # 1. Projeções salariais (reutiliza função BD)
        monthly_salaries = calculate_salary_projections(context, state, total_months)

        # 2. Contribuições mensais (reutiliza função BD)
        monthly_contributions = calculate_contribution_projections(monthly_salaries, state, context)

        # 3. Probabilidades de sobrevivência (reutiliza função BD)
        monthly_survival_probs = calculate_survival_probabilities(state, mortality_table, total_months)

        # 4. Evolução do saldo CD (específico)
        monthly_balances = cls._calculate_cd_balance_evolution(
            monthly_contributions, context, months_to_retirement
        )

        # 5. Projeções de renda na aposentadoria (específico CD)
        # Inicializar com zeros, será calculado no CDCalculator
        monthly_benefits = [0.0] * total_months

        # 6. Organizar dados mensais
        monthly_data = {
            "months": list(range(total_months)),
            "salaries": monthly_salaries,
            "benefits": monthly_benefits,
            "contributions": monthly_contributions,
            "survival_probs": monthly_survival_probs,
            "reserves": monthly_balances  # Use "reserves" key for compatibility with conversion function
        }

        # 7. Converter para dados anuais
        yearly_data = convert_monthly_to_yearly_projections(monthly_data, total_months)
        yearly_data["monthly_data"] = monthly_data
        yearly_data["final_balance"] = monthly_balances[months_to_retirement - 1] if months_to_retirement > 0 else 0.0

        # 8. Age projections will be generated later in CDCalculator after benefits are calculated
        # This ensures benefits are properly included in age-based charts

        return yearly_data

    @classmethod
    def _calculate_target_benefit_amount(
        cls,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        monthly_salaries: list
    ) -> float:
        """Calcula valor do benefício mensal alvo baseado no modo configurado"""
        from ..models.participant import BenefitTargetMode

        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            months_to_retirement = context.months_to_retirement
            salary_growth_factor = (1 + context.salary_growth_real_monthly) ** max(months_to_retirement - 1, 0)
            final_salary_base = context.monthly_salary * salary_growth_factor
            return final_salary_base * (replacement_rate / 100)
        else:  # VALUE
            return state.target_benefit if state.target_benefit is not None else 0

    @classmethod
    def _calculate_cd_balance_evolution(
        cls,
        monthly_contributions: list,
        context: 'ActuarialContext',
        months_to_retirement: int
    ) -> list:
        """
        Calcula evolução do saldo CD durante fase ativa
        Aplica taxa de acumulação mensal sobre saldo + contribuições
        """
        monthly_balances = []
        current_balance = getattr(context, 'initial_balance', 0.0)

        for month, contribution in enumerate(monthly_contributions):
            if month < months_to_retirement:
                # Fase ativa: saldo cresce com rendimento + contribuições
                current_balance = current_balance * (1 + context.discount_rate_monthly) + contribution

                # Descontar taxa administrativa do saldo
                current_balance *= (1 - context.admin_fee_monthly)
            else:
                # Fase inativa: sem novas contribuições, só rendimento
                current_balance = current_balance * (1 + context.discount_rate_monthly)
                current_balance *= (1 - context.admin_fee_monthly)

            monthly_balances.append(max(current_balance, 0.0))

        return monthly_balances

    @classmethod
    def _generate_age_projections(
        cls,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        monthly_salaries: list,
        monthly_benefits: list,
        total_months: int
    ) -> Dict:
        """
        Gera vetores de projeção por idade para o frontend
        Reutilizável entre BD/CD
        """
        projection_ages = []
        projected_salaries_by_age = []
        projected_benefits_by_age = []

        # Gerar lista de idades (apenas anos completos)
        for month in range(0, total_months, 12):  # A cada 12 meses
            age = state.age + (month // 12)
            projection_ages.append(age)

            # Para benefícios e salários, usar valor do primeiro mês do ano
            if month < len(monthly_salaries):
                monthly_salary = monthly_salaries[month]
                monthly_benefit = monthly_benefits[month]

                # Converter para valores anuais considerando múltiplos pagamentos
                annual_salary = monthly_salary * context.salary_months_per_year if monthly_salary > 0 else 0
                annual_benefit = monthly_benefit * context.benefit_months_per_year if monthly_benefit > 0 else 0

                projected_salaries_by_age.append(annual_salary)
                projected_benefits_by_age.append(annual_benefit)
            else:
                projected_salaries_by_age.append(0.0)
                projected_benefits_by_age.append(0.0)

        return {
            "projection_ages": projection_ages,
            "projected_salaries_by_age": projected_salaries_by_age,
            "projected_benefits_by_age": projected_benefits_by_age
        }