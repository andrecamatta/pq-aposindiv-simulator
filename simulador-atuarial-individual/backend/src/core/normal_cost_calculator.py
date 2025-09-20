"""
NormalCostCalculator: Especializado em cálculos de Custo Normal para planos BD
Extraído do ActuarialEngine para seguir Single Responsibility Principle
"""
import numpy as np
from typing import Dict, TYPE_CHECKING
from .logging_config import ActuarialLoggerMixin

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .actuarial_engine import ActuarialContext


class NormalCostCalculator(ActuarialLoggerMixin):
    """
    Calculadora especializada para Custo Normal em planos BD
    Responsabilidade única: cálculos de custo normal anual
    """

    def __init__(self):
        super().__init__()

    def calculate_normal_cost(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        projections: Dict,
        survival_probs: np.ndarray
    ) -> float:
        """
        Calcula Custo Normal para planos BD

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções temporais
            survival_probs: Probabilidades de sobrevivência

        Returns:
            Valor do Custo Normal
        """
        if context.is_already_retired:
            self.log_info("Pessoa aposentada: Custo Normal = 0")
            return 0.0

        months_to_retirement = context.months_to_retirement
        monthly_data = projections.get("monthly_data", {})

        method = state.calculation_method.value if hasattr(state.calculation_method, 'value') else state.calculation_method

        if method == "PUC":
            return self._calculate_puc_normal_cost(
                state, context, survival_probs, months_to_retirement
            )
        else:  # EAN
            return self._calculate_ean_normal_cost(
                state, context, monthly_data, survival_probs, months_to_retirement
            )

    def _calculate_puc_normal_cost(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        survival_probs: np.ndarray,
        months_to_retirement: int
    ) -> float:
        """
        Calcula Custo Normal pelo método PUC (Projected Unit Credit)

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            survival_probs: Probabilidades de sobrevivência
            months_to_retirement: Meses até aposentadoria

        Returns:
            Custo Normal PUC
        """
        self.log_info("Calculando Custo Normal PUC")

        # VPA do benefício incremental deste ano
        projected_final_salary = context.monthly_salary * (
            (1 + context.salary_growth_real_monthly) ** months_to_retirement
        )
        annual_benefit_increment = projected_final_salary * (state.accrual_rate / 100)
        monthly_benefit_increment = annual_benefit_increment / max(context.benefit_months_per_year, 1)

        # Taxa efetiva considerando taxa administrativa
        effective_discount_rate = (1 + context.discount_rate_monthly) / (1 + context.admin_fee_monthly) - 1
        effective_discount_rate = max(effective_discount_rate, -0.99)

        # Fator de anuidade vitalícia
        annuity_factor = self._calculate_life_annuity_factor(
            survival_probs,
            effective_discount_rate,
            context.payment_timing,
            start_month=months_to_retirement
        )

        normal_cost = monthly_benefit_increment * annuity_factor

        self.log_info(f"Custo Normal PUC calculado: R$ {normal_cost:,.2f}")
        return normal_cost

    def _calculate_ean_normal_cost(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        monthly_data: Dict,
        survival_probs: np.ndarray,
        months_to_retirement: int
    ) -> float:
        """
        Calcula Custo Normal pelo método EAN (Entry Age Normal)

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            monthly_data: Dados mensais das projeções
            survival_probs: Probabilidades de sobrevivência
            months_to_retirement: Meses até aposentadoria

        Returns:
            Custo Normal EAN
        """
        self.log_info("Calculando Custo Normal EAN")

        monthly_salaries = monthly_data.get("salaries", [])
        monthly_benefits = monthly_data.get("benefits", [])

        # VPA dos benefícios futuros (incluindo fase pós-aposentadoria)
        vpa_benefits = self._calculate_vpa_benefits(
            monthly_benefits, survival_probs, context, months_to_retirement
        )

        # VPA dos salários futuros até a aposentadoria
        apv_future_salaries = self._calculate_vpa_salaries(
            monthly_salaries, survival_probs, context, months_to_retirement
        )

        if apv_future_salaries <= 0:
            return 0.0

        # Recursos já existentes reduzem o passivo a financiar
        resources_available = getattr(state, 'initial_balance', 0.0)

        # Custo normal = (VPA benefícios - recursos) / VPA salários * salário atual
        liability_to_fund = max(0, vpa_benefits - resources_available)
        cost_rate = liability_to_fund / apv_future_salaries if apv_future_salaries > 0 else 0

        # Aplicar aos salários anuais (considerando múltiplos pagamentos)
        annual_salary = context.monthly_salary * context.salary_annual_factor
        normal_cost = cost_rate * annual_salary

        self.log_info(f"Custo Normal EAN calculado: R$ {normal_cost:,.2f}")
        return normal_cost

    def _calculate_life_annuity_factor(
        self,
        survival_probs: np.ndarray,
        discount_rate: float,
        timing: str,
        start_month: int = 0
    ) -> float:
        """
        Calcula fator de anuidade vitalícia

        Args:
            survival_probs: Probabilidades de sobrevivência
            discount_rate: Taxa de desconto
            timing: Timing dos pagamentos
            start_month: Mês de início

        Returns:
            Fator de anuidade vitalícia
        """
        # Importar aqui para evitar dependência circular
        from ..utils import calculate_life_annuity_factor

        return calculate_life_annuity_factor(
            survival_probs, discount_rate, timing, start_month
        )

    def _calculate_vpa_benefits(
        self,
        monthly_benefits,
        survival_probs: np.ndarray,
        context: 'ActuarialContext',
        months_to_retirement: int
    ) -> float:
        """
        Calcula VPA dos benefícios futuros

        Args:
            monthly_benefits: Lista de benefícios mensais
            survival_probs: Probabilidades de sobrevivência
            context: Contexto atuarial
            months_to_retirement: Meses até aposentadoria

        Returns:
            VPA dos benefícios
        """
        # Importar aqui para evitar dependência circular
        from ..utils import calculate_actuarial_present_value

        return calculate_actuarial_present_value(
            monthly_benefits,
            survival_probs,
            context.discount_rate_monthly,
            context.payment_timing,
            start_month=months_to_retirement
        )

    def _calculate_vpa_salaries(
        self,
        monthly_salaries,
        survival_probs: np.ndarray,
        context: 'ActuarialContext',
        months_to_retirement: int
    ) -> float:
        """
        Calcula VPA dos salários futuros

        Args:
            monthly_salaries: Lista de salários mensais
            survival_probs: Probabilidades de sobrevivência
            context: Contexto atuarial
            months_to_retirement: Meses até aposentadoria

        Returns:
            VPA dos salários
        """
        # Importar aqui para evitar dependência circular
        from ..utils import calculate_actuarial_present_value

        return calculate_actuarial_present_value(
            monthly_salaries,
            survival_probs,
            context.discount_rate_monthly,
            context.payment_timing,
            start_month=0,
            end_month=months_to_retirement
        )

    def calculate_cost_allocation_analysis(
        self,
        normal_cost: float,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> Dict:
        """
        Calcula análise de alocação do custo normal

        Args:
            normal_cost: Valor do custo normal
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Dict com análise de alocação
        """
        annual_salary = context.monthly_salary * context.salary_annual_factor
        cost_rate_percentage = (normal_cost / annual_salary * 100) if annual_salary > 0 else 0

        # Comparar com contribuição atual
        current_contribution_rate = state.contribution_rate
        current_annual_contribution = annual_salary * (current_contribution_rate / 100)

        funding_gap = normal_cost - current_annual_contribution
        funding_gap_percentage = (funding_gap / annual_salary * 100) if annual_salary > 0 else 0

        return {
            "normal_cost": normal_cost,
            "cost_rate_percentage": cost_rate_percentage,
            "current_contribution": current_annual_contribution,
            "current_contribution_rate": current_contribution_rate,
            "funding_gap": funding_gap,
            "funding_gap_percentage": funding_gap_percentage,
            "annual_salary": annual_salary
        }

    def estimate_cost_volatility(
        self,
        normal_cost: float,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> Dict:
        """
        Estima volatilidade do custo normal

        Args:
            normal_cost: Valor do custo normal base
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Dict com análise de volatilidade
        """
        # Sensibilidade a mudanças na taxa de desconto (±1%)
        discount_sensitivity = []
        for delta in [-0.01, 0.01]:
            # Simular mudança na taxa de desconto
            adjusted_rate = context.discount_rate_monthly + (delta / 12)
            # Aproximação: custo é inversamente sensível à taxa
            sensitivity_factor = (1 + context.discount_rate_monthly) / (1 + adjusted_rate)
            adjusted_cost = normal_cost * sensitivity_factor
            discount_sensitivity.append({
                "rate_change": delta * 100,
                "cost_change": (adjusted_cost - normal_cost) / normal_cost * 100,
                "adjusted_cost": adjusted_cost
            })

        # Sensibilidade a mudanças na mortalidade (±5%)
        mortality_sensitivity = []
        for delta in [-0.05, 0.05]:
            # Aproximação: custo é diretamente sensível à longevidade
            adjusted_cost = normal_cost * (1 + delta)
            mortality_sensitivity.append({
                "mortality_change": delta * 100,
                "cost_change": delta * 100,
                "adjusted_cost": adjusted_cost
            })

        return {
            "base_cost": normal_cost,
            "discount_sensitivity": discount_sensitivity,
            "mortality_sensitivity": mortality_sensitivity,
            "high_volatility": max(abs(s["cost_change"]) for s in discount_sensitivity) > 20
        }