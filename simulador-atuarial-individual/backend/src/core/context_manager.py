"""
Gerenciador de Contextos Atuariais
Responsável por criar e gerenciar contextos de cálculo para diferentes tipos de planos.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..utils.rates import annual_to_monthly_rate
from .constants import (
    MIN_RETIREMENT_YEARS,
    MAX_RETIREMENT_PROJECTION_YEARS,
    MAX_RETIREMENT_AGE_PROJECTION
)
from ..models.participant import DEFAULT_SALARY_MONTHS_PER_YEAR, DEFAULT_BENEFIT_MONTHS_PER_YEAR

if TYPE_CHECKING:
    from ..models.participant import SimulatorState

logger = logging.getLogger(__name__)


@dataclass
class ActuarialContext:
    """Contexto atuarial com taxas mensais e períodos padronizados"""
    # Taxas mensais (convertidas de anuais)
    discount_rate_monthly: float
    salary_growth_real_monthly: float

    # Períodos em meses
    months_to_retirement: int
    total_months_projection: int

    # Status de aposentadoria
    is_already_retired: bool  # True se age >= retirement_age
    months_since_retirement: int  # Meses já aposentado (0 se ainda ativo)

    # Valores mensais efetivos (considerando 13º)
    monthly_salary: float
    monthly_contribution: float
    monthly_benefit: float

    # Custos administrativos (taxas mensais)
    admin_fee_monthly: float     # Taxa administrativa mensal sobre saldo
    loading_fee_rate: float      # Taxa de carregamento sobre contribuições

    # Configurações técnicas
    payment_timing: str  # "antecipado" ou "postecipado"
    salary_months_per_year: int
    benefit_months_per_year: int

    # Fatores calculados
    salary_annual_factor: float  # Fator para converter mensal → anual
    benefit_annual_factor: float  # Fator para converter mensal → anual


class ContextManager:
    """Gerenciador centralizado de contextos atuariais"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_context(self, state: 'SimulatorState') -> ActuarialContext:
        """
        Cria contexto atuarial a partir do estado do simulador.

        Args:
            state: Estado atual do simulador

        Returns:
            Contexto atuarial configurado
        """
        return self._create_standard_context(state)

    def create_bd_context(self, state: 'SimulatorState') -> ActuarialContext:
        """
        Cria contexto específico para planos BD com taxas diferenciadas.

        Args:
            state: Estado atual do simulador

        Returns:
            Contexto atuarial para BD
        """
        context = self._create_standard_context(state)

        # Para BD, usar taxas específicas ou fallback para discount_rate
        accumulation_rate = getattr(state, 'accumulation_rate', None) or state.discount_rate
        conversion_rate = getattr(state, 'conversion_rate', None) or state.discount_rate

        # Substituir taxa de desconto por taxa de acumulação durante fase ativa
        context.discount_rate_monthly = annual_to_monthly_rate(accumulation_rate)

        # Armazenar taxa de conversão para cálculo de valor presente de benefícios
        setattr(context, 'conversion_rate_monthly', annual_to_monthly_rate(conversion_rate))

        self.logger.debug(
            f"Contexto BD: taxa acumulação={accumulation_rate:.4f}, "
            f"taxa conversão={conversion_rate:.4f}"
        )

        return context

    def create_cd_context(self, state: 'SimulatorState') -> ActuarialContext:
        """
        Cria contexto específico para planos CD com taxas diferenciadas.

        Args:
            state: Estado atual do simulador

        Returns:
            Contexto atuarial para CD
        """
        context = self._create_standard_context(state)

        # Para CD, usar taxas específicas ou fallback para taxas BD
        cd_discount_rate = getattr(state, 'cd_discount_rate', None)
        if cd_discount_rate is not None:
            context.discount_rate_monthly = annual_to_monthly_rate(cd_discount_rate)
            self.logger.debug(f"Usando taxa de desconto CD específica: {cd_discount_rate}%")

        return context

    def _create_standard_context(self, state: 'SimulatorState') -> ActuarialContext:
        """
        Implementação padrão de criação de contexto.

        Args:
            state: Estado atual do simulador

        Returns:
            Contexto atuarial padrão
        """
        # Conversão de taxas anuais para mensais
        discount_monthly = annual_to_monthly_rate(state.discount_rate)
        salary_growth_monthly = annual_to_monthly_rate(state.salary_growth_real)

        # Detectar se já está aposentado
        is_already_retired = state.age >= state.retirement_age

        if is_already_retired:
            months_to_retirement = 0
            months_since_retirement = (state.age - state.retirement_age) * 12
            self.logger.info(f"Participante já aposentado há {months_since_retirement} meses")
        else:
            months_to_retirement = (state.retirement_age - state.age) * 12
            months_since_retirement = 0

        # Calcular período total de projeção
        total_months = self._calculate_projection_period(state, is_already_retired)

        # Configurar pagamentos mensais
        monthly_config = self._calculate_monthly_values(state)

        # Configurar custos administrativos
        admin_config = self._calculate_admin_costs(state)

        return ActuarialContext(
            discount_rate_monthly=discount_monthly,
            salary_growth_real_monthly=salary_growth_monthly,
            months_to_retirement=months_to_retirement,
            total_months_projection=total_months,
            is_already_retired=is_already_retired,
            months_since_retirement=months_since_retirement,
            monthly_salary=monthly_config['salary'],
            monthly_contribution=monthly_config['contribution'],
            monthly_benefit=monthly_config['benefit'],
            admin_fee_monthly=admin_config['admin_fee_monthly'],
            loading_fee_rate=admin_config['loading_fee_rate'],
            payment_timing="antecipado",  # Padrão atuarial brasileiro
            salary_months_per_year=monthly_config['salary_months'],
            benefit_months_per_year=monthly_config['benefit_months'],
            salary_annual_factor=monthly_config['salary_months'],
            benefit_annual_factor=monthly_config['benefit_months']
        )

    def _calculate_projection_period(self, state: 'SimulatorState', is_already_retired: bool) -> int:
        """
        Calcula período de projeção apropriado.

        Args:
            state: Estado do simulador
            is_already_retired: Se participante já está aposentado

        Returns:
            Total de meses para projeção
        """
        if is_already_retired:
            # Para aposentados: projetar apenas os anos restantes de expectativa de vida
            max_years_projection = min(MAX_RETIREMENT_PROJECTION_YEARS, MAX_RETIREMENT_AGE_PROJECTION - state.age)
            total_months = max(12, max_years_projection * 12)  # Mínimo 1 ano
            self.logger.debug(f"Aposentado: projetando {max_years_projection} anos")
        else:
            # Para ativos: garantir período adequado para aposentadoria
            projected_retirement_years = state.projection_years - (state.retirement_age - state.age)

            if projected_retirement_years < MIN_RETIREMENT_YEARS:
                total_years = (state.retirement_age - state.age) + MIN_RETIREMENT_YEARS
                total_months = total_years * 12
                self.logger.info(f"Período estendido para {total_years} anos (mín. {MIN_RETIREMENT_YEARS} de aposentadoria)")
            else:
                total_months = state.projection_years * 12

        return total_months

    def _calculate_monthly_values(self, state: 'SimulatorState') -> dict:
        """
        Calcula valores mensais efetivos.

        Args:
            state: Estado do simulador

        Returns:
            Dicionário com valores mensais
        """
        # Número de salários e benefícios por ano
        salary_months = getattr(state, 'salary_months_per_year', DEFAULT_SALARY_MONTHS_PER_YEAR) or DEFAULT_SALARY_MONTHS_PER_YEAR
        benefit_months = getattr(state, 'benefit_months_per_year', DEFAULT_BENEFIT_MONTHS_PER_YEAR) or DEFAULT_BENEFIT_MONTHS_PER_YEAR

        # Valores mensais
        monthly_salary = state.salary
        monthly_contribution = monthly_salary * (state.contribution_rate / 100.0)

        # Benefício mensal depende do modo de configuração
        if hasattr(state, 'target_benefit') and state.target_benefit:
            monthly_benefit = state.target_benefit
        else:
            # Fallback para taxa de reposição ou valor padrão
            replacement_rate = getattr(state, 'target_replacement_rate', 70.0) / 100.0
            monthly_benefit = monthly_salary * replacement_rate

        return {
            'salary': monthly_salary,
            'contribution': monthly_contribution,
            'benefit': monthly_benefit,
            'salary_months': salary_months,
            'benefit_months': benefit_months
        }

    def _calculate_admin_costs(self, state: 'SimulatorState') -> dict:
        """
        Calcula custos administrativos mensais.

        Args:
            state: Estado do simulador

        Returns:
            Dicionário com custos administrativos
        """
        # Taxa administrativa anual → mensal (usando fórmula equivalente)
        admin_rate_annual = state.admin_fee_rate / 100.0
        admin_fee_monthly = admin_rate_annual / 12.0  # Simplificado para demonstração

        loading_fee_rate = getattr(state, 'loading_fee_rate', 0.0) / 100.0

        return {
            'admin_fee_monthly': admin_fee_monthly,
            'loading_fee_rate': loading_fee_rate
        }

    def validate_context(self, context: ActuarialContext) -> bool:
        """
        Valida se o contexto está consistente.

        Args:
            context: Contexto a ser validado

        Returns:
            True se válido, False caso contrário
        """
        try:
            # Validações básicas
            assert context.discount_rate_monthly >= 0, "Taxa de desconto deve ser não-negativa"
            assert context.total_months_projection > 0, "Período de projeção deve ser positivo"
            assert context.monthly_salary > 0, "Salário mensal deve ser positivo"

            return True
        except AssertionError as e:
            self.logger.error(f"Contexto inválido: {e}")
            return False