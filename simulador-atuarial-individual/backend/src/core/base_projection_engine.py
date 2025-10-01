"""
BaseProjectionEngine: Lógica comum de projeções entre BD e CD
Preserva diferenças atuariais fundamentais enquanto elimina duplicação
"""
import numpy as np
from typing import List, Dict, TYPE_CHECKING
from abc import ABC, abstractmethod

from .constants import (
    MIN_RETIREMENT_YEARS,
    MSG_EXTENDED_PROJECTION,
    MSG_RETIREMENT_PROJECTION,
    MAX_RETIREMENT_PROJECTION_YEARS,
    MAX_RETIREMENT_AGE_PROJECTION
)
from .logging_config import ActuarialLoggerMixin
from .projections import (
    calculate_salary_projections,
    calculate_survival_probabilities
)

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .actuarial_engine import ActuarialContext


class BaseProjectionEngine(ActuarialLoggerMixin, ABC):
    """
    Engine base para projeções atuariais
    Contém lógica comum entre BD e CD, preservando especializações
    """

    def __init__(self):
        super().__init__()

    def calculate_common_projections(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        mortality_table: np.ndarray
    ) -> Dict:
        """
        Calcula projeções comuns entre BD e CD

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            mortality_table: Tábua de mortalidade

        Returns:
            Dict com projeções comuns
        """
        self.log_info(f"Iniciando projeções comuns para {state.plan_type}")

        # 1. Projeções de salários (comum para BD e CD)
        monthly_salaries = calculate_salary_projections(
            context, state, context.total_months_projection
        )

        # 2. Probabilidades de sobrevivência (comum para BD e CD)
        survival_probabilities = calculate_survival_probabilities(
            state, mortality_table, context.total_months_projection
        )

        # 3. Timeline temporal (comum)
        timeline = self._calculate_timeline(state, context)

        return {
            "monthly_salaries": monthly_salaries,
            "survival_probabilities": survival_probabilities,
            "timeline": timeline,
            "context": context
        }

    def _calculate_timeline(self, state: 'SimulatorState', context: 'ActuarialContext') -> Dict:
        """
        Calcula cronograma temporal comum

        Args:
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Dict com informações temporais
        """
        return {
            "total_months": context.total_months_projection,
            "months_to_retirement": context.months_to_retirement,
            "is_already_retired": context.is_already_retired,
            "months_since_retirement": context.months_since_retirement,
            "retirement_age": state.retirement_age,
            "current_age": state.age
        }

    def validate_projection_period(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> 'ActuarialContext':
        """
        Valida e ajusta período de projeção se necessário

        Args:
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Contexto atuarial ajustado
        """
        if context.is_already_retired:
            # Para aposentados: projetar anos restantes de expectativa
            max_years_projection = min(MAX_RETIREMENT_PROJECTION_YEARS, MAX_RETIREMENT_AGE_PROJECTION - state.age)
            total_months = max(12, max_years_projection * 12)
            self.log_info(MSG_RETIREMENT_PROJECTION.format(total_months/12))

        else:
            # Para ativos: garantir período adequado para aposentadoria
            projected_retirement_years = state.projection_years - (state.retirement_age - state.age)

            if projected_retirement_years < MIN_RETIREMENT_YEARS:
                total_years = (state.retirement_age - state.age) + MIN_RETIREMENT_YEARS
                total_months = total_years * 12
                self.log_info(MSG_EXTENDED_PROJECTION.format(total_years))
            else:
                total_months = state.projection_years * 12

        # Atualizar contexto com período validado
        context.total_months_projection = total_months
        return context

    @abstractmethod
    def calculate_specialized_projections(
        self,
        common_projections: Dict,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> Dict:
        """
        Método abstrato para cálculos especializados
        Implementado por BDProjectionEngine e CDProjectionEngine

        Args:
            common_projections: Projeções comuns já calculadas
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Dict com projeções especializadas
        """
        pass


class BDProjectionEngine(BaseProjectionEngine):
    """
    Engine especializado para projeções BD
    Foca em VPA, desconto atuarial e reservas matemáticas
    """

    def calculate_specialized_projections(
        self,
        common_projections: Dict,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> Dict:
        """
        Cálculos especializados para BD

        Args:
            common_projections: Projeções comuns
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Dict com projeções BD especializadas
        """
        self.log_info("Calculando projeções especializadas BD")

        # Importar aqui para evitar dependência circular
        from .projections import calculate_benefit_projections, calculate_contribution_projections

        monthly_salaries = common_projections["monthly_salaries"]

        # Benefícios BD: baseados em meta ou taxa de reposição
        target_benefit = state.target_benefit if state.target_benefit else 0.0
        monthly_benefits = calculate_benefit_projections(
            context, state, context.total_months_projection, target_benefit
        )

        # Contribuições BD: com taxa de carregamento aplicada
        monthly_contributions = calculate_contribution_projections(
            monthly_salaries, state, context
        )

        return {
            **common_projections,
            "monthly_benefits": monthly_benefits,
            "monthly_contributions": monthly_contributions,
            "calculation_type": "BD_ACTUARIAL"
        }


class CDProjectionEngine(BaseProjectionEngine):
    """
    Engine especializado para projeções CD
    Foca em capitalização e conversão em renda
    """

    def calculate_specialized_projections(
        self,
        common_projections: Dict,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> Dict:
        """
        Cálculos especializados para CD

        Args:
            common_projections: Projeções comuns
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Dict com projeções CD especializadas
        """
        self.log_info("Calculando projeções especializadas CD")

        # Importar aqui para evitar dependência circular
        from .projections import calculate_contribution_projections

        monthly_salaries = common_projections["monthly_salaries"]

        # Contribuições CD: com taxa de carregamento aplicada
        monthly_contributions = calculate_contribution_projections(
            monthly_salaries, state, context
        )

        # CD não tem benefícios pré-definidos (são calculados na conversão)
        monthly_benefits = [0.0] * context.total_months_projection

        return {
            **common_projections,
            "monthly_benefits": monthly_benefits,
            "monthly_contributions": monthly_contributions,
            "calculation_type": "CD_ACCUMULATION"
        }


def create_projection_engine(plan_type: str) -> BaseProjectionEngine:
    """
    Factory para criar engine de projeção apropriado

    Args:
        plan_type: Tipo de plano ("BD" ou "CD")

    Returns:
        Engine de projeção especializado
    """
    if plan_type == "BD":
        return BDProjectionEngine()
    elif plan_type == "CD":
        return CDProjectionEngine()
    else:
        raise ValueError(f"Tipo de plano não suportado: {plan_type}")