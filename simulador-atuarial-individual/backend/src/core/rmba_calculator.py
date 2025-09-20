"""
RMBACalculator: Especializado em cálculos de Reserva Matemática de Benefícios a Conceder
Extraído do ActuarialEngine para seguir Single Responsibility Principle
"""
from typing import Dict, TYPE_CHECKING
from .logging_config import ActuarialLoggerMixin
from .constants import MSG_PERSON_RETIRED, MSG_PERSON_ACTIVE

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .actuarial_engine import ActuarialContext


class RMBACalculator(ActuarialLoggerMixin):
    """
    Calculadora especializada para RMBA (Reserva Matemática de Benefícios a Conceder)
    Responsabilidade única: cálculos de reservas para benefícios futuros
    """

    def __init__(self):
        super().__init__()

    def calculate_rmba(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        projections: Dict
    ) -> float:
        """
        Calcula RMBA - Reserva Matemática de Benefícios a Conceder

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções temporais

        Returns:
            Valor do RMBA
        """
        # Para pessoas já aposentadas, RMBA = 0 (não há benefícios futuros a conceder)
        if context.is_already_retired:
            self.log_rmba_debug(f"{MSG_PERSON_RETIRED}: RMBA = 0")
            return 0.0

        # Para pessoas ativas: RMBA = VPA(Benefícios) - VPA(Contribuições)
        monthly_data = projections["monthly_data"]

        # Usar utilitário para calcular VPAs de benefícios e contribuições
        vpa_benefits, vpa_contributions = self._calculate_vpa_benefits_contributions(
            monthly_data["benefits"],
            monthly_data["contributions"],
            monthly_data["survival_probs"],
            context.discount_rate_monthly,
            context.payment_timing,
            context.months_to_retirement,
            context.admin_fee_monthly
        )

        self.log_rmba_debug(
            f"{MSG_PERSON_ACTIVE}: VPA Benefícios = {vpa_benefits:.2f}, VPA Contrib = {vpa_contributions:.2f}"
        )

        rmba = vpa_benefits - vpa_contributions

        # Log de auditoria detalhada
        self._log_rmba_audit(state, context, vpa_benefits, vpa_contributions, rmba)

        return rmba

    def _calculate_vpa_benefits_contributions(
        self,
        monthly_benefits,
        monthly_contributions,
        monthly_survival_probs,
        discount_rate_monthly,
        timing,
        months_to_retirement,
        admin_fee_monthly
    ):
        """
        Calcula VPAs de benefícios e contribuições
        Delegação para utilitário especializado
        """
        # Importar aqui para evitar dependência circular
        from ..utils import calculate_vpa_benefits_contributions

        return calculate_vpa_benefits_contributions(
            monthly_benefits,
            monthly_contributions,
            monthly_survival_probs,
            discount_rate_monthly,
            timing,
            months_to_retirement,
            admin_fee_monthly
        )

    def _log_rmba_audit(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        vpa_benefits: float,
        vpa_contributions: float,
        rmba: float
    ):
        """
        Log detalhado de auditoria do RMBA

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            vpa_benefits: VPA dos benefícios
            vpa_contributions: VPA das contribuições
            rmba: Valor do RMBA calculado
        """
        contribution_years = (state.retirement_age - state.age)
        monthly_contribution = context.monthly_salary * (state.contribution_rate / 100)

        self.log_auditoria("=== DETALHAMENTO DOS VPAS ===")
        self.log_auditoria("Parâmetros base:")
        self.log_auditoria(f"  - Idade: {state.age} → {state.retirement_age} anos ({contribution_years} anos contribuição)")
        self.log_auditoria(f"  - Salário mensal: R$ {context.monthly_salary:,.2f} ({state.salary_months_per_year}x/ano)")
        self.log_auditoria(f"  - Contribuição: {state.contribution_rate}% = R$ {monthly_contribution:,.2f}/mês")
        self.log_auditoria(f"  - Benefício alvo: R$ {state.target_benefit or 0:,.2f}/mês ({state.benefit_months_per_year}x/ano)")
        self.log_auditoria(f"  - Taxa desconto: {state.discount_rate*100:.1f}% a.a. = {context.discount_rate_monthly*100:.4f}%/mês")
        self.log_auditoria(f"  - Crescimento salarial: {state.salary_growth_real*100:.1f}% a.a.")
        self.log_auditoria(f"  - Taxa administrativa: {state.admin_fee_rate*100:.1f}% a.a. = {context.admin_fee_monthly*100:.4f}%/mês")
        self.log_auditoria(f"  - Timing pagamentos: {context.payment_timing}")
        self.log_auditoria(f"  - Meses até aposentadoria: {context.months_to_retirement}")

        self.log_auditoria("Contribuições:")
        net_contribution = monthly_contribution * (1 - context.loading_fee_rate)
        self.log_auditoria(f"  - Contribuição inicial líquida: R$ {net_contribution:,.2f}/mês")
        self.log_auditoria(f"  - Total meses de contribuição: {context.months_to_retirement}")

        self.log_auditoria("Benefícios:")
        if state.benefit_target_mode.value == "VALUE":
            self.log_auditoria(f" - Benefício: Valor fixo de R$ {state.target_benefit or 0:,.2f}/mês")
        else:
            self.log_auditoria(" - Benefício: Baseado em taxa de reposição")
            replacement_rate = state.target_replacement_rate or "Não definido"
            self.log_auditoria(f" - Taxa de reposição: {replacement_rate}")

        self.log_auditoria("Resultado final:")
        self.log_auditoria(f"  - VPA Contribuições: R$ {vpa_contributions:,.2f}")
        self.log_auditoria(f"  - VPA Benefícios: R$ {vpa_benefits:,.2f}")
        self.log_auditoria(f"  - RMBA: R$ {rmba:,.2f}")

        deficit_surplus = -rmba  # Convenção: superávit é negativo
        self.log_auditoria(f"  - {'Déficit' if deficit_surplus < 0 else 'Superávit'}: R$ {abs(deficit_surplus):,.2f}")
        self.log_auditoria("================================")

        # Sanidade econômica
        if abs(deficit_surplus) > 50000 and state.initial_balance == 0:
            self.log_sanidade(
                f"⚠️  {'Déficit' if deficit_surplus < 0 else 'Superávit'} alto "
                f"({deficit_surplus:.2f}) com saldo inicial zero pode indicar erro de cálculo"
            )

    def calculate_deficit_surplus_analysis(
        self,
        rmba: float,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> Dict:
        """
        Calcula análise de déficit/superávit baseada no RMBA

        Args:
            rmba: Valor do RMBA
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Dict com análise de déficit/superávit
        """
        # Recursos disponíveis vs passivos
        available_resources = state.initial_balance
        required_reserves = rmba

        deficit_surplus = available_resources - required_reserves
        deficit_surplus_percentage = (
            (deficit_surplus / abs(required_reserves) * 100)
            if required_reserves != 0 else 0.0
        )

        # Taxa de contribuição necessária para equilibrar
        required_contribution_rate = 0.0
        if rmba > state.initial_balance:
            required_total_contributions = rmba - state.initial_balance

            # VPA dos salários futuros para calcular contribuição necessária
            apv_future_salaries = self._calculate_apv_future_salaries(state, context)

            required_contribution_rate = (
                (required_total_contributions / apv_future_salaries * 100)
                if apv_future_salaries > 0 else 0
            )
            required_contribution_rate = min(required_contribution_rate, 50)  # Máximo 50%

        return {
            "deficit_surplus": deficit_surplus,
            "deficit_surplus_percentage": deficit_surplus_percentage,
            "required_contribution_rate": required_contribution_rate,
            "available_resources": available_resources,
            "required_reserves": required_reserves
        }

    def _calculate_apv_future_salaries(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> float:
        """
        Calcula VPA dos salários futuros até aposentadoria

        Args:
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            VPA dos salários futuros
        """
        # Importar aqui para evitar dependência circular
        from ..utils import calculate_actuarial_present_value

        # Simular salários mensais até aposentadoria
        monthly_salaries = []
        current_salary = context.monthly_salary

        for month in range(context.months_to_retirement):
            # Aplicar crescimento salarial
            salary_growth_factor = (1 + context.salary_growth_real_monthly) ** month
            projected_salary = current_salary * salary_growth_factor
            monthly_salaries.append(projected_salary)

        # Probabilidades de sobrevivência simplificadas (assumir 100% para VPA salários)
        survival_probs = [1.0] * len(monthly_salaries)

        return calculate_actuarial_present_value(
            monthly_salaries,
            survival_probs,
            context.discount_rate_monthly,
            context.payment_timing,
            start_month=0,
            end_month=context.months_to_retirement
        )