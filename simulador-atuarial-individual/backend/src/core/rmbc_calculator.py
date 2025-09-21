"""
RMBCCalculator: Especializado em cálculos de Reserva Matemática de Benefícios Concedidos
Extraído do ActuarialEngine para seguir Single Responsibility Principle
"""
from typing import Dict, TYPE_CHECKING
from .logging_config import ActuarialLoggerMixin
from .constants import MSG_PERSON_ACTIVE

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .actuarial_engine import ActuarialContext


class RMBCCalculator(ActuarialLoggerMixin):
    """
    Calculadora especializada para RMBC (Reserva Matemática de Benefícios Concedidos)
    Responsabilidade única: cálculos de reservas para pessoas já aposentadas
    """

    def __init__(self):
        super().__init__()

    def calculate_rmbc(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        projections: Dict
    ) -> float:
        """
        Calcula RMBC - Reserva Matemática de Benefícios Concedidos

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções temporais

        Returns:
            Valor do RMBC
        """
        # Para pessoas ativas, RMBC = 0 (ainda não há benefícios concedidos)
        if not context.is_already_retired:
            self.log_rmbc_debug(f"{MSG_PERSON_ACTIVE}: RMBC = 0")
            return 0.0

        # Para aposentados: RMBC = VPA dos benefícios restantes
        monthly_data = projections["monthly_data"]

        rmbc = self._calculate_vpa_remaining_benefits(
            monthly_data["benefits"],
            monthly_data["survival_probs"],
            context.discount_rate_monthly,
            context.payment_timing,
            context.admin_fee_monthly
        )

        self.log_rmbc_debug(f"Pessoa aposentada: RMBC = {rmbc:.2f}")

        # Log de auditoria detalhada
        self._log_rmbc_audit(state, context, rmbc)

        return rmbc

    def _calculate_vpa_remaining_benefits(
        self,
        monthly_benefits,
        monthly_survival_probs,
        discount_rate_monthly,
        timing,
        admin_fee_monthly
    ) -> float:
        """
        Calcula VPA dos benefícios restantes para aposentado

        Args:
            monthly_benefits: Lista de benefícios mensais
            monthly_survival_probs: Probabilidades de sobrevivência
            discount_rate_monthly: Taxa de desconto mensal
            timing: Timing dos pagamentos
            admin_fee_monthly: Taxa administrativa mensal

        Returns:
            VPA dos benefícios restantes
        """
        # Importar aqui para evitar dependência circular
        from .calculations.vpa_calculations import calculate_actuarial_present_value

        # Para aposentados, começar do mês 0 (já estão recebendo)
        return calculate_actuarial_present_value(
            monthly_benefits,
            monthly_survival_probs,
            discount_rate_monthly,
            timing,
            start_month=0
        )

    def _log_rmbc_audit(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        rmbc: float
    ):
        """
        Log detalhado de auditoria do RMBC

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            rmbc: Valor do RMBC calculado
        """
        years_since_retirement = context.months_since_retirement / 12

        self.log_auditoria("=== DETALHAMENTO DO RMBC ===")
        self.log_auditoria("Parâmetros do aposentado:")
        self.log_auditoria(f"  - Idade atual: {state.age} anos")
        self.log_auditoria(f"  - Idade aposentadoria: {state.retirement_age} anos")
        self.log_auditoria(f"  - Anos desde aposentadoria: {years_since_retirement:.1f}")
        self.log_auditoria(f"  - Benefício mensal: R$ {context.monthly_benefit:,.2f}")
        self.log_auditoria(f"  - Taxa desconto: {state.discount_rate*100:.1f}% a.a.")
        self.log_auditoria(f"  - Taxa administrativa: {state.admin_fee_rate*100:.1f}% a.a.")

        self.log_auditoria("Resultado:")
        self.log_auditoria(f"  - RMBC (VPA benefícios restantes): R$ {rmbc:,.2f}")
        self.log_auditoria("============================")

    def calculate_benefit_projection_for_retiree(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext'
    ) -> Dict:
        """
        Calcula projeção de benefícios para pessoa já aposentada

        Args:
            state: Estado do simulador
            context: Contexto atuarial

        Returns:
            Dict com projeção de benefícios
        """
        # Para aposentados, benefício é constante (sem crescimento)
        monthly_benefit = context.monthly_benefit
        total_months = context.total_months_projection

        # Criar projeção constante de benefícios
        monthly_benefits = []
        for month in range(total_months):
            # Considerar múltiplos pagamentos por ano (13º salário)
            month_in_year = month % 12
            if month_in_year < context.benefit_months_per_year:
                monthly_benefits.append(monthly_benefit)
            else:
                monthly_benefits.append(0.0)

        return {
            "monthly_benefits": monthly_benefits,
            "constant_benefit": monthly_benefit,
            "total_projection_months": total_months
        }

    def calculate_coverage_ratio(
        self,
        rmbc: float,
        available_assets: float
    ) -> Dict:
        """
        Calcula índice de cobertura das reservas

        Args:
            rmbc: Valor do RMBC
            available_assets: Ativos disponíveis

        Returns:
            Dict com análise de cobertura
        """
        coverage_ratio = (available_assets / rmbc * 100) if rmbc > 0 else 100.0

        coverage_status = "ADEQUADA"
        if coverage_ratio < 80:
            coverage_status = "INSUFICIENTE"
        elif coverage_ratio < 100:
            coverage_status = "LIMITADA"

        return {
            "coverage_ratio": coverage_ratio,
            "coverage_status": coverage_status,
            "rmbc": rmbc,
            "available_assets": available_assets,
            "shortfall": max(0, rmbc - available_assets)
        }

    def estimate_benefit_duration(
        self,
        rmbc: float,
        monthly_benefit: float
    ) -> Dict:
        """
        Estima duração dos benefícios com base no RMBC

        Args:
            rmbc: Valor do RMBC
            monthly_benefit: Benefício mensal

        Returns:
            Dict com estimativa de duração
        """
        if monthly_benefit <= 0:
            return {
                "estimated_months": 0,
                "estimated_years": 0,
                "status": "INVALIDO"
            }

        # Estimativa simples (sem considerar juros ou mortalidade)
        estimated_months = rmbc / monthly_benefit if monthly_benefit > 0 else 0
        estimated_years = estimated_months / 12

        status = "NORMAL"
        if estimated_years < 10:
            status = "CURTA_DURACAO"
        elif estimated_years > 30:
            status = "LONGA_DURACAO"

        return {
            "estimated_months": estimated_months,
            "estimated_years": estimated_years,
            "status": status
        }