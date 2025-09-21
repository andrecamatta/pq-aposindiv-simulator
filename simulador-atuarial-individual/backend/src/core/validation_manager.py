"""
Gerenciador de Validações Atuariais
Centraliza todas as validações de entrada e saída dos cálculos atuariais.
"""

import logging
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .context_manager import ActuarialContext

logger = logging.getLogger(__name__)


class ValidationManager:
    """Gerenciador centralizado de validações atuariais"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_input_state(self, state: 'SimulatorState') -> None:
        """
        Valida parâmetros de entrada do estado do simulador.

        Args:
            state: Estado do simulador a ser validado

        Raises:
            ValueError: Se algum parâmetro for inválido
        """
        self._validate_personal_data(state)
        self._validate_financial_data(state)
        self._validate_actuarial_data(state)

    def validate_context(self, context: 'ActuarialContext') -> None:
        """
        Valida contexto atuarial.

        Args:
            context: Contexto a ser validado

        Raises:
            ValueError: Se o contexto for inválido
        """
        if not context:
            raise ValueError("Contexto atuarial não pode ser None")

        if context.discount_rate_monthly < 0:
            raise ValueError(f"Taxa de desconto mensal inválida: {context.discount_rate_monthly}")

        if context.months_to_retirement < 0:
            raise ValueError(f"Meses até aposentadoria inválido: {context.months_to_retirement}")

        if context.total_months_projection <= 0:
            raise ValueError(f"Período de projeção inválido: {context.total_months_projection}")

    def validate_economic_sanity(self, state: 'SimulatorState', vpa_benefits: float,
                               vpa_contributions: float, rmba: float) -> None:
        """
        Valida consistência econômica dos resultados atuariais.

        Args:
            state: Estado do simulador
            vpa_benefits: Valor Presente Atuarial dos benefícios
            vpa_contributions: Valor Presente Atuarial das contribuições
            rmba: Reserva Matemática de Benefícios Ativos

        Raises:
            ValueError: Se há inconsistências detectadas
        """
        issues = []

        # Verificar valores NaN ou infinitos
        values_to_check = {
            'VPA Benefícios': vpa_benefits,
            'VPA Contribuições': vpa_contributions,
            'RMBA': rmba
        }

        for name, value in values_to_check.items():
            if math.isnan(value) or math.isinf(value):
                issues.append(f"{name} é inválido: {value}")

        # Verificar ordens de magnitude
        annual_salary = state.salary * 12
        if vpa_benefits > annual_salary * 100:  # Mais de 100 anos de salário
            issues.append(f"VPA Benefícios suspeito: R$ {vpa_benefits:,.2f} (>100x salário anual)")

        if vpa_contributions < 0:
            issues.append(f"VPA Contribuições negativo: R$ {vpa_contributions:,.2f}")

        # Verificar consistência BD vs CD
        if hasattr(state, 'plan_type') and str(state.plan_type) == 'BD':
            # Para BD, RMBA deve ser significativa
            if abs(rmba) < annual_salary * 0.1:  # Menos de 10% do salário anual
                self.logger.warning(f"RMBA muito baixa para BD: R$ {rmba:,.2f}")

        if issues:
            error_msg = "Inconsistências econômicas detectadas:\n" + "\n".join(f"- {issue}" for issue in issues)
            raise ValueError(error_msg)

        self.logger.debug("Validação de sanidade econômica aprovada")

    def _validate_personal_data(self, state: 'SimulatorState') -> None:
        """Valida dados pessoais"""
        if state.age < 18 or state.age > 100:
            raise ValueError(f"Idade inválida: {state.age}")

        if state.retirement_age <= state.age:
            raise ValueError(f"Idade de aposentadoria ({state.retirement_age}) deve ser maior que idade atual ({state.age})")

        if state.retirement_age > 100:
            raise ValueError(f"Idade de aposentadoria muito alta: {state.retirement_age}")

        # Validar gênero se fornecido
        if hasattr(state, 'gender') and state.gender:
            if state.gender not in ['M', 'F', 'MASCULINO', 'FEMININO']:
                raise ValueError(f"Gênero inválido: {state.gender}")

    def _validate_financial_data(self, state: 'SimulatorState') -> None:
        """Valida dados financeiros"""
        if state.salary <= 0:
            raise ValueError(f"Salário deve ser positivo: {state.salary}")

        if state.salary > 1_000_000:  # R$ 1 milhão por mês
            self.logger.warning(f"Salário muito alto: R$ {state.salary:,.2f}")

        if hasattr(state, 'contribution_rate') and state.contribution_rate:
            if state.contribution_rate < 0 or state.contribution_rate > 50:
                raise ValueError(f"Taxa de contribuição inválida: {state.contribution_rate}%")

        # Validar benefício se fornecido
        if hasattr(state, 'target_benefit') and state.target_benefit:
            if state.target_benefit < 0:
                raise ValueError(f"Benefício alvo inválido: {state.target_benefit}")

            # Taxa de reposição implícita
            replacement_ratio = (state.target_benefit / state.salary) * 100
            if replacement_ratio > 150:  # Mais de 150% do salário
                self.logger.warning(f"Taxa de reposição muito alta: {replacement_ratio:.1f}%")

    def _validate_actuarial_data(self, state: 'SimulatorState') -> None:
        """Valida parâmetros atuariais"""
        if state.discount_rate < 0 or state.discount_rate > 30:
            raise ValueError(f"Taxa de desconto inválida: {state.discount_rate}%")

        if hasattr(state, 'salary_growth_real') and state.salary_growth_real:
            if state.salary_growth_real < -10 or state.salary_growth_real > 20:
                raise ValueError(f"Crescimento salarial real inválido: {state.salary_growth_real}%")

        if hasattr(state, 'admin_fee_rate') and state.admin_fee_rate:
            if state.admin_fee_rate < 0 or state.admin_fee_rate > 10:
                raise ValueError(f"Taxa administrativa inválida: {state.admin_fee_rate}%")

        # Validar períodos de projeção
        if hasattr(state, 'projection_years') and state.projection_years:
            max_projection = 100 - state.age
            if state.projection_years > max_projection:
                raise ValueError(f"Período de projeção muito longo: {state.projection_years} anos (máx: {max_projection})")

    def validate_calculation_inputs(self, **kwargs) -> None:
        """
        Valida inputs específicos de cálculos.

        Args:
            **kwargs: Parâmetros a serem validados

        Raises:
            ValueError: Se algum parâmetro for inválido
        """
        for name, value in kwargs.items():
            if value is None:
                raise ValueError(f"Parâmetro '{name}' não pode ser None")

            if isinstance(value, (int, float)):
                if math.isnan(value) or math.isinf(value):
                    raise ValueError(f"Parâmetro '{name}' é inválido: {value}")

    def validate_calculation_outputs(self, results: dict) -> None:
        """
        Valida outputs de cálculos atuariais.

        Args:
            results: Dicionário com resultados

        Raises:
            ValueError: Se algum resultado for inconsistente
        """
        required_fields = ['vpa_benefits', 'vpa_contributions', 'deficit_surplus']

        for field in required_fields:
            if field not in results:
                raise ValueError(f"Campo obrigatório ausente: {field}")

            value = results[field]
            if isinstance(value, (int, float)) and (math.isnan(value) or math.isinf(value)):
                raise ValueError(f"Resultado inválido para {field}: {value}")

        self.logger.debug("Validação de outputs aprovada")