"""
Cálculos de Valor Presente Atuarial (VPA) especializados
Consolida e centraliza todas as funções VPA do projeto.
Substitui utils/vpa.py e core/vpa_calculator.py
"""

import math
import logging
from typing import List, Tuple, TYPE_CHECKING
from .basic_math import calculate_discount_factor
from scipy.optimize import fsolve, root_scalar

logger = logging.getLogger(__name__)

# Import apenas para type hints, evita circular imports
if TYPE_CHECKING:
    from ...models.participant import SimulatorState
    from ..actuarial_engine import ActuarialEngine


def calculate_actuarial_present_value(
    cash_flows: List[float],
    survival_probs: List[float],
    discount_rate: float,
    timing: str = "postecipado",
    start_month: int = 0,
    end_month: int = None
) -> float:
    """
    Calcula Valor Presente Atuarial de um fluxo de caixa considerando mortalidade
    
    Args:
        cash_flows: Fluxos de caixa por período
        survival_probs: Probabilidades de sobrevivência cumulativas
        discount_rate: Taxa de desconto por período
        timing: "antecipado" ou "postecipado"
        start_month: Mês de início do cálculo
        end_month: Mês de fim do cálculo (None = até o final)
    
    Returns:
        VPA total
    """
    if end_month is None:
        end_month = min(len(cash_flows), len(survival_probs))
    
    vpa_total = 0.0
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    
    for month in range(start_month, min(end_month, len(cash_flows), len(survival_probs))):
        cash_flow = cash_flows[month]
        survival_prob = survival_probs[month]
        
        if cash_flow != 0 and survival_prob > 0:  # Otimização
            discount_factor = calculate_discount_factor(discount_rate, month, timing_adjustment)
            vpa_total += cash_flow * survival_prob * discount_factor
    
    return vpa_total


def calculate_vpa_benefits_contributions(
    monthly_benefits: List[float],
    monthly_contributions: List[float],
    monthly_survival_probs: List[float],
    discount_rate_monthly: float,
    timing: str,
    months_to_retirement: int,
    admin_fee_monthly: float = 0.0
) -> tuple:
    """
    Calcula VPA de benefícios e contribuições considerando custos administrativos

    Args:
        monthly_benefits: Lista de benefícios mensais
        monthly_contributions: Lista de contribuições mensais
        monthly_survival_probs: Probabilidades de sobrevivência
        discount_rate_monthly: Taxa de desconto mensal (taxa atuarial única)
        timing: Timing dos pagamentos
        months_to_retirement: Meses até aposentadoria
        admin_fee_monthly: Taxa administrativa mensal

    Returns:
        Tupla (VPA benefícios, VPA contribuições líquido)
    """
    # VPA dos benefícios (sempre começam na aposentadoria)
    vpa_benefits = calculate_actuarial_present_value(
        monthly_benefits,
        monthly_survival_probs,
        discount_rate_monthly,
        timing,
        start_month=months_to_retirement
    )

    # VPA das contribuições (sem dedução da taxa administrativa)
    # A taxa admin deve incidir sobre o SALDO, não sobre as contribuições
    # Para o cálculo do VPA, usamos uma taxa de desconto efetiva que já considera a taxa admin

    if admin_fee_monthly > 0:
        # Taxa efetiva = taxa de desconto ajustada pela taxa administrativa
        # Isso simula o efeito da taxa admin incidindo sobre o saldo acumulado
        effective_discount_rate = (1 + discount_rate_monthly) / (1 - admin_fee_monthly) - 1

        # Calcular VPA com a taxa efetiva
        vpa_contributions_net = calculate_actuarial_present_value(
            monthly_contributions,
            monthly_survival_probs,
            effective_discount_rate,
            timing,
            start_month=0,
            end_month=months_to_retirement
        )
    else:
        # Sem taxa administrativa
        vpa_contributions_net = calculate_actuarial_present_value(
            monthly_contributions,
            monthly_survival_probs,
            discount_rate_monthly,
            timing,
            start_month=0,
            end_month=months_to_retirement
        )

    return vpa_benefits, vpa_contributions_net


def calculate_sustainable_benefit(
    initial_balance: float,
    vpa_contributions: float,
    monthly_survival_probs: List[float],
    discount_rate_monthly: float,
    timing: str,
    months_to_retirement: int,
    benefit_months_per_year: int = 12,
    admin_fee_monthly: float = 0.0
) -> float:
    """
    Calcula benefício sustentável que equilibra recursos com VPA de benefícios
    
    Args:
        initial_balance: Saldo inicial disponível
        vpa_contributions: VPA das contribuições futuras
        monthly_survival_probs: Probabilidades de sobrevivência
        discount_rate_monthly: Taxa de desconto mensal
        timing: Timing dos pagamentos
        months_to_retirement: Meses até aposentadoria
        benefit_months_per_year: Número de pagamentos anuais de benefício
        admin_fee_monthly: Taxa administrativa mensal
    
    Returns:
        Benefício mensal sustentável
    """
    # Recursos totais disponíveis
    total_resources = initial_balance + vpa_contributions
    
    if total_resources <= 0:
        return 0.0
    
    # Calcular fator de anuidade vitalícia a partir da aposentadoria
    annuity_factor = 0.0
    max_months = len(monthly_survival_probs)
    
    for month in range(months_to_retirement, max_months):
        if month < len(monthly_survival_probs):
            survival_prob = monthly_survival_probs[month]
            
            if survival_prob > 0:
                discount_factor = calculate_discount_factor(discount_rate_monthly, month, timing)
                
                # Taxa administrativa não deve ser aplicada como desconto direto
                # Deve ser incorporada na taxa de desconto efetiva
                net_discount_factor = discount_factor
                
                # Considerar múltiplos pagamentos por ano
                months_in_year = month % 12
                payment_multiplier = 1.0
                
                # Pagamentos extras (13º, 14º, etc.)
                extra_payments = benefit_months_per_year - 12
                if extra_payments > 0:
                    if months_in_year == 11:  # Dezembro
                        if extra_payments >= 1:
                            payment_multiplier += 1.0
                    if months_in_year == 0:  # Janeiro
                        if extra_payments >= 2:
                            payment_multiplier += 1.0
                
                annuity_factor += survival_prob * net_discount_factor * payment_multiplier
    
    # Calcular benefício sustentável
    if annuity_factor > 0:
        return total_resources / annuity_factor
    else:
        return 0.0


def calculate_life_annuity_immediate(
    survival_probs: List[float],
    discount_rate: float,
    start_period: int = 0
) -> float:
    """
    Calcula fator de anuidade vitalícia imediata (postecipada)
    
    Args:
        survival_probs: Probabilidades de sobrevivência cumulativas
        discount_rate: Taxa de desconto por período
        start_period: Período de início
    
    Returns:
        Fator de anuidade vitalícia
    """
    annuity_factor = 0.0
    
    for period in range(start_period, len(survival_probs)):
        survival_prob = survival_probs[period]
        if survival_prob > 0:
            discount_factor = (1 + discount_rate) ** -(period + 1)  # Postecipado
            annuity_factor += survival_prob * discount_factor
    
    return annuity_factor


def calculate_life_annuity_due(
    survival_probs: List[float],
    discount_rate: float,
    start_period: int = 0
) -> float:
    """
    Calcula fator de anuidade vitalícia antecipada
    
    Args:
        survival_probs: Probabilidades de sobrevivência cumulativas
        discount_rate: Taxa de desconto por período
        start_period: Período de início
    
    Returns:
        Fator de anuidade vitalícia antecipada
    """
    annuity_factor = 0.0
    
    for period in range(start_period, len(survival_probs)):
        survival_prob = survival_probs[period]
        if survival_prob > 0:
            discount_factor = (1 + discount_rate) ** -period  # Antecipado
            annuity_factor += survival_prob * discount_factor
    
    return annuity_factor


def calculate_deferred_annuity(
    survival_probs: List[float],
    discount_rate: float,
    deferral_periods: int,
    annuity_periods: int = None
) -> float:
    """
    Calcula valor presente de anuidade diferida
    
    Args:
        survival_probs: Probabilidades de sobrevivência
        discount_rate: Taxa de desconto
        deferral_periods: Períodos de diferimento
        annuity_periods: Períodos de anuidade (None = vitalícia)
    
    Returns:
        Valor presente da anuidade diferida
    """
    if annuity_periods is None:
        end_period = len(survival_probs)
    else:
        end_period = min(deferral_periods + annuity_periods, len(survival_probs))
    
    annuity_factor = 0.0
    
    for period in range(deferral_periods, end_period):
        if period < len(survival_probs):
            survival_prob = survival_probs[period]
            if survival_prob > 0:
                discount_factor = (1 + discount_rate) ** -(period + 1)
                annuity_factor += survival_prob * discount_factor

    return annuity_factor


# ============================================================================
# FUNÇÕES CONSOLIDADAS DE VALIDAÇÃO E UTILIDADES VPA
# ============================================================================

def get_payment_survival_probability(
    survival_probs: List[float],
    month: int,
    payment_timing: str
) -> float:
    """Obtém probabilidade de sobrevivência coerente com o instante do pagamento."""
    if not survival_probs:
        return 0.0

    if payment_timing == "antecipado":
        if month <= 0:
            return 1.0
        index = min(month - 1, len(survival_probs) - 1)
    else:
        index = min(month, len(survival_probs) - 1)

    return max(0.0, survival_probs[index])


def validate_actuarial_inputs(
    cash_flows: List[float],
    survival_probs: List[float],
    discount_rate_monthly: float,
    start_month: int = 0,
    end_month: int = None
) -> None:
    """
    Valida entradas para cálculos atuariais.

    Raises:
        ValueError: Se algum parâmetro for inválido
    """
    if not cash_flows:
        raise ValueError("Lista de fluxos de caixa não pode estar vazia")

    if not survival_probs:
        raise ValueError("Lista de probabilidades de sobrevivência não pode estar vazia")

    if len(cash_flows) != len(survival_probs):
        # Só alertar se cash_flows for maior que survival_probs (problema real)
        # É normal cash_flows ser menor (ex: contribuições só no período ativo)
        if len(cash_flows) > len(survival_probs):
            logger.warning(f"[VPA_DEBUG] PROBLEMA: cash_flows ({len(cash_flows)}) > survival_probs ({len(survival_probs)})")
        else:
            # Normal: cash_flows menores que survival_probs (contribuições vs. período total)
            logger.debug(f"[VPA_DEBUG] Normal: cash_flows={len(cash_flows)}, survival_probs={len(survival_probs)}")

    if discount_rate_monthly < 0:
        raise ValueError(f"Taxa de desconto não pode ser negativa: {discount_rate_monthly}")

    if discount_rate_monthly > 1:
        raise ValueError(f"Taxa de desconto mensal suspeita (>100%): {discount_rate_monthly}")

    if start_month < 0:
        raise ValueError(f"Mês inicial não pode ser negativo: {start_month}")

    if end_month is not None and end_month <= start_month:
        raise ValueError(f"Mês final ({end_month}) deve ser maior que inicial ({start_month})")

    # Validar probabilidades de sobrevivência
    for i, prob in enumerate(survival_probs):
        if prob < 0 or prob > 1:
            raise ValueError(f"Probabilidade de sobrevivência inválida no índice {i}: {prob}")


def calculate_life_annuity_factor(
    survival_probs: List[float],
    discount_rate_monthly: float,
    payment_timing: str,
    start_month: int = 0,
    end_month: int = None
) -> float:
    """
    Calcula o fator de anuidade vitalícia (äx).

    Representa o valor presente de uma anuidade de R$ 1,00 mensal vitalícia.

    Args:
        survival_probs: Lista de probabilidades de sobrevivência (tPx)
        discount_rate_monthly: Taxa de juros técnica mensal
        payment_timing: Tipo de anuidade ("antecipado" ou "postecipado")
        start_month: Mês inicial para início da anuidade
        end_month: Mês final (None para vitalícia)

    Returns:
        Fator de anuidade vitalícia (äx para antecipado, ax para postecipado)
    """
    unit_cash_flows = [1.0] * len(survival_probs)
    return calculate_actuarial_present_value(
        unit_cash_flows,
        survival_probs,
        discount_rate_monthly,
        payment_timing,
        start_month,
        end_month
    )


def calculate_vpa_contributions_with_admin_fees(
    monthly_contributions: List[float],
    survival_probs: List[float],
    discount_rate_monthly: float,
    admin_fee_monthly: float,
    payment_timing: str,
    months_to_retirement: int
) -> float:
    """
    Calcula VPA de contribuições considerando taxas administrativas aplicadas corretamente.

    Args:
        monthly_contributions: Lista de contribuições mensais brutas
        survival_probs: Lista de probabilidades de sobrevivência
        discount_rate_monthly: Taxa de desconto mensal
        admin_fee_monthly: Taxa administrativa mensal (aplicada aos fluxos individuais)
        payment_timing: Timing dos pagamentos
        months_to_retirement: Meses até aposentadoria

    Returns:
        VPA das contribuições líquidas (após taxas administrativas)
    """
    # Validar inputs básicos
    try:
        validate_actuarial_inputs(monthly_contributions, survival_probs, discount_rate_monthly)
    except ValueError as e:
        logger.error(f"[VPA_ADMIN_FEES] Erro de validação: {e}")
        return 0.0

    vpa = 0.0

    # Calcular VPA apenas para o período ativo (antes da aposentadoria)
    end_month = min(months_to_retirement, len(monthly_contributions), len(survival_probs))

    for month in range(end_month):
        contribution = monthly_contributions[month]
        survival_prob = survival_probs[month]

        if contribution > 0 and survival_prob > 0:
            # NÃO aplicar taxa admin diretamente na contribuição
            # A taxa admin incide sobre SALDO, não sobre fluxos
            net_contribution = contribution

            # Calcular fator de desconto considerando timing
            # Se há taxa admin, ajustar a taxa de desconto efetiva
            if admin_fee_monthly > 0:
                # Taxa efetiva considerando admin fee sobre saldo
                effective_discount_rate = (1 + discount_rate_monthly) / (1 - admin_fee_monthly) - 1
            else:
                effective_discount_rate = discount_rate_monthly

            timing_adjustment = 0.0 if payment_timing == "antecipado" else 1.0
            discount_factor = calculate_discount_factor(effective_discount_rate, month, timing_adjustment)

            # Verificar se valores são finitos
            if math.isfinite(net_contribution) and math.isfinite(discount_factor):
                contribution_vpa = net_contribution * survival_prob * discount_factor

                # Verificar se o resultado é finito
                if not math.isfinite(contribution_vpa):
                    continue

                vpa += contribution_vpa

    # Validar resultado final
    if not math.isfinite(vpa):
        raise ValueError("VPA resultante não é finito")

    return vpa


# ============================================================================
# FUNÇÕES ESPECÍFICAS PARA OTIMIZAÇÃO (DEPENDEM DO ENGINE)
# ============================================================================

def calculate_parameter_to_zero_deficit(
    state: "SimulatorState",
    engine: "ActuarialEngine",
    parameter_name: str,
    bounds: tuple = None,
    initial_guess: float = None
) -> float:
    """
    Função genérica que usa fsolve para calcular qualquer parâmetro que zere o déficit/superávit.

    Args:
        state: Estado atual do simulador
        engine: Engine atuarial para cálculos
        parameter_name: Nome do parâmetro a ser otimizado
            - "target_benefit": Benefício mensal
            - "contribution_rate": Taxa de contribuição (%)
            - "retirement_age": Idade de aposentadoria
            - "salary": Salário atual
        bounds: Tupla com (min, max) valores permitidos
        initial_guess: Chute inicial (se None, será calculado automaticamente)

    Returns:
        Valor do parâmetro que zera o déficit/superávit
    """
    import copy

    logger.info(f"[FSOLVE] Calculando {parameter_name} que zera déficit/superávit")

    def objective_function(parameter_value: float) -> float:
        """
        Função objetivo: retorna déficit/superávit para um dado valor do parâmetro.
        Quando retorna 0, temos o valor ótimo do parâmetro.
        """
        # Criar cópia do estado com novo valor do parâmetro
        test_state = copy.deepcopy(state)

        # Aplicar o novo valor do parâmetro
        if parameter_name == "target_benefit":
            test_state.target_benefit = float(parameter_value)
        elif parameter_name == "contribution_rate":
            # Trabalhamos sempre em pontos percentuais para manter consistência
            test_state.contribution_rate = float(parameter_value)
        elif parameter_name == "retirement_age":
            test_state.retirement_age = int(parameter_value)
        elif parameter_name == "salary":
            test_state.salary = float(parameter_value)
        else:
            raise ValueError(f"Parâmetro desconhecido: {parameter_name}")

        try:
            # Calcular resultado com novo parâmetro
            results = engine.calculate_individual_simulation(test_state)
            deficit = results.deficit_surplus

            logger.debug(f"[FSOLVE] {parameter_name}={parameter_value} → déficit={deficit:.2f}")
            return deficit

        except Exception as e:
            logger.error(f"[FSOLVE] Erro no cálculo com {parameter_name}={parameter_value}: {e}")
            return float('inf')

    # Configurar bounds e chute inicial baseado no parâmetro
    if bounds is None:
        if parameter_name == "target_benefit":
            bounds = (100.0, state.salary * 3.0)
        elif parameter_name == "contribution_rate":
            bounds = (1.0, 30.0)  # 1% a 30%
        elif parameter_name == "retirement_age":
            min_age = max(50, state.age + 1)
            bounds = (min_age, 100)
        elif parameter_name == "salary":
            bounds = (state.salary * 0.5, state.salary * 3.0)

    if initial_guess is None:
        initial_guess = (bounds[0] + bounds[1]) / 2

    try:
        # Testar se os bounds têm sinais opostos
        f_min = objective_function(bounds[0])
        f_max = objective_function(bounds[1])

        logger.debug(f"[FSOLVE] Testando bounds: f({bounds[0]}) = {f_min:.2f}, f({bounds[1]}) = {f_max:.2f}")

        evaluation_points = [(bounds[0], f_min), (bounds[1], f_max)]
        previous_value = bounds[0]
        previous_result = f_min
        bracket = None

        if math.isfinite(f_min) and math.isfinite(f_max) and f_min * f_max <= 0:
            bracket = (bounds[0], bounds[1])
        else:
            # Escanear o intervalo em busca de mudança de sinal
            samples = 12
            step = (bounds[1] - bounds[0]) / samples if samples > 0 else 0

            for i in range(1, samples):
                test_value = bounds[0] + step * i
                result_value = objective_function(test_value)
                evaluation_points.append((test_value, result_value))

                if (
                    math.isfinite(previous_result)
                    and math.isfinite(result_value)
                    and previous_result * result_value <= 0
                ):
                    bracket = (previous_value, test_value)
                    break

                previous_value = test_value
                previous_result = result_value

        if bracket:
            result = root_scalar(
                objective_function,
                bracket=bracket,
                method='brentq',
                xtol=1e-3
            )

            if result.converged:
                optimal_value = result.root
                logger.info(f"[FSOLVE] ✅ Convergência: {parameter_name}={optimal_value:.3f}")
                return optimal_value
            logger.warning(f"[FSOLVE] ⚠️ Não convergiu no bracket {bracket}, usando melhor aproximação disponível")

        # Sem bracket válido: selecionar o valor com menor déficit absoluto
        finite_points = [p for p in evaluation_points if math.isfinite(p[1])]
        if finite_points:
            best_value, best_deficit = min(finite_points, key=lambda x: abs(x[1]))
            logger.info(
                f"[FSOLVE] ⚠️ Sem raiz clara; escolhendo {parameter_name}={best_value:.3f} (déficit={best_deficit:.2f})"
            )
            return best_value

        logger.warning(f"[FSOLVE] ⚠️ Não foi possível avaliar ponto estável para {parameter_name}, usando chute inicial")
        return initial_guess

    except Exception as e:
        logger.error(f"[FSOLVE] Erro na otimização: {e}")
        return initial_guess


def calculate_optimal_contribution_rate(state: "SimulatorState", engine: "ActuarialEngine") -> float:
    """Calcula taxa de contribuição que zera o déficit/superávit"""
    return calculate_parameter_to_zero_deficit(
        state, engine, "contribution_rate",
        bounds=(1.0, 30.0),
        initial_guess=state.contribution_rate
    )


def calculate_optimal_retirement_age(state: "SimulatorState", engine: "ActuarialEngine") -> float:
    """Calcula idade de aposentadoria que zera o déficit/superávit"""
    min_age = max(50, state.age + 1)  # No mínimo 1 ano a mais que idade atual
    return calculate_parameter_to_zero_deficit(
        state, engine, "retirement_age",
        bounds=(min_age, 100),
        initial_guess=state.retirement_age
    )


def calculate_optimal_cd_contribution_rate(
    state: "SimulatorState",
    engine: "ActuarialEngine",
    target_monthly_income: float
) -> float:
    """
    Calcula taxa de contribuição CD que atinge renda mensal alvo usando root seeking.

    Similar a calculate_optimal_contribution_rate mas para CD com renda vitalícia.
    Usa root_scalar com brentq para encontrar taxa que resulta em monthly_income = target.

    Args:
        state: Estado do simulador
        engine: Engine atuarial
        target_monthly_income: Renda mensal desejada na aposentadoria

    Returns:
        Taxa de contribuição (%) que atinge a renda alvo
    """
    import logging
    import math
    from scipy.optimize import root_scalar

    logger = logging.getLogger(__name__)

    def objective_function(contribution_rate: float) -> float:
        """Função objetivo: diferença entre renda resultante e renda alvo"""
        test_state = state.model_copy()
        test_state.contribution_rate = float(contribution_rate)

        try:
            results = engine.calculate_individual_simulation(test_state)
            monthly_income = getattr(results, 'monthly_income', 0)
            gap = monthly_income - target_monthly_income

            logger.debug(f"[FSOLVE_CD] taxa={contribution_rate:.2f}% → renda={monthly_income:.2f} (alvo={target_monthly_income:.2f}, gap={gap:.2f})")
            return gap

        except Exception as e:
            logger.error(f"[FSOLVE_CD] Erro com taxa={contribution_rate}: {e}")
            return float('inf')

    # Bounds: 1% a 30%
    bounds = (1.0, 30.0)
    initial_guess = state.contribution_rate or 10.0

    try:
        # Testar bounds
        f_min = objective_function(bounds[0])
        f_max = objective_function(bounds[1])

        logger.debug(f"[FSOLVE_CD] Bounds: f({bounds[0]})={f_min:.2f}, f({bounds[1]})={f_max:.2f}")

        evaluation_points = [(bounds[0], f_min), (bounds[1], f_max)]
        previous_value = bounds[0]
        previous_result = f_min
        bracket = None

        if math.isfinite(f_min) and math.isfinite(f_max) and f_min * f_max <= 0:
            bracket = (bounds[0], bounds[1])
        else:
            # Escanear intervalo em busca de mudança de sinal
            samples = 12
            step = (bounds[1] - bounds[0]) / samples

            for i in range(1, samples):
                test_value = bounds[0] + step * i
                result_value = objective_function(test_value)
                evaluation_points.append((test_value, result_value))

                if (math.isfinite(previous_result) and
                    math.isfinite(result_value) and
                    previous_result * result_value <= 0):
                    bracket = (previous_value, test_value)
                    break

                previous_value = test_value
                previous_result = result_value

        if bracket:
            result = root_scalar(
                objective_function,
                bracket=bracket,
                method='brentq',
                xtol=1e-3
            )

            if result.converged:
                optimal_rate = result.root
                logger.info(f"[FSOLVE_CD] ✅ Convergência: taxa={optimal_rate:.2f}%")
                return optimal_rate
            logger.warning(f"[FSOLVE_CD] ⚠️ Não convergiu no bracket {bracket}")

        # Sem bracket: escolher menor gap absoluto
        finite_points = [p for p in evaluation_points if math.isfinite(p[1])]
        if finite_points:
            best_rate, best_gap = min(finite_points, key=lambda x: abs(x[1]))
            logger.info(f"[FSOLVE_CD] ⚠️ Sem raiz clara; taxa={best_rate:.2f}% (gap={best_gap:.2f})")
            return best_rate

        logger.warning(f"[FSOLVE_CD] ⚠️ Usando chute inicial {initial_guess}%")
        return initial_guess

    except Exception as e:
        logger.error(f"[FSOLVE_CD] Erro na otimização: {e}")
        return initial_guess


def calculate_sustainable_benefit_with_engine(
    state: "SimulatorState",
    engine: "ActuarialEngine"
) -> float:
    """
    Calcula benefício sustentável usando root finding com ActuarialEngine.

    Esta função encontra o valor de benefício que zera o déficit/superávit
    usando métodos de root finding otimizados (fsolve + fallbacks) e o engine atuarial completo.

    Args:
        state: Estado atual do simulador
        engine: Engine atuarial para cálculos

    Returns:
        Benefício mensal que zera o déficit/superávit
    """
    import copy

    def objective_function(benefit_value: float) -> float:
        """
        Função objetivo: retorna déficit/superávit para um dado benefício.
        Quando retorna 0, temos o benefício sustentável.
        """
        # Criar cópia do estado com novo benefício
        test_state = copy.deepcopy(state)
        test_state.target_benefit = float(benefit_value)
        test_state.benefit_target_mode = BenefitTargetMode.VALUE

        # Calcular usando engine atuarial existente
        try:
            benefit_scalar = float(benefit_value) if hasattr(benefit_value, '__iter__') and hasattr(benefit_value, 'shape') else benefit_value
            logger.debug(f"[VPA_DEBUG] Calculando para benefício: {benefit_scalar:.2f}")
            results = engine.calculate_individual_simulation(test_state)
            result = results.deficit_surplus

            # Verificar se resultado é finito
            if not math.isfinite(result):
                logger.error(f"[SUSTENTÁVEL] Engine retornou valor não finito: {result} para benefício {benefit_scalar:.2f}")
                salary_monthly = state.salary if hasattr(state, 'salary') else 8000.0
                if benefit_value > salary_monthly:
                    return 1e6  # Superávit muito alto
                else:
                    return -1e6  # Déficit muito alto

            logger.debug(f"[SUSTENTÁVEL] Benefício: R$ {benefit_scalar:.2f} → Déficit: R$ {result:.2f}")
            return result

        except Exception as e:
            # Converter benefit_value para scalar se for array numpy
            try:
                if hasattr(benefit_value, '__iter__') and hasattr(benefit_value, 'shape'):
                    benefit_scalar = float(benefit_value.item() if benefit_value.size == 1 else benefit_value[0])
                else:
                    benefit_scalar = float(benefit_value)
            except:
                benefit_scalar = 0.0

            logger.error(f"[SUSTENTÁVEL] Erro no cálculo para benefício {benefit_scalar:.2f}: {e}")

            # Usar lógica consistente baseada no benefício testado
            try:
                salary_monthly = state.salary if hasattr(state, 'salary') else 8000.0
                benefit_check = float(benefit_value.item() if hasattr(benefit_value, 'item') else benefit_value)
                if benefit_check > salary_monthly:
                    return 1e6  # Assumir superávit alto em caso de erro
                else:
                    return -1e6  # Assumir déficit alto em caso de erro
            except:
                return -1e6  # Fallback para déficit

    # Determinar bounds inteligentes baseados no salário e benefício desejado
    salary_monthly = state.salary if hasattr(state, 'salary') else 8000.0
    benefit_hint = state.target_benefit if state.target_benefit else salary_monthly
    logger.info(f"[VPA_DEBUG] Salário mensal: R$ {salary_monthly:.2f}, Benefício desejado: R$ {benefit_hint:.2f}")

    # Usar calculate_parameter_to_zero_deficit para consistência
    return calculate_parameter_to_zero_deficit(
        state, engine, "target_benefit",
        bounds=(100.0, salary_monthly * 3),  # Entre R$ 100 e 3x salário
        initial_guess=benefit_hint
    )
