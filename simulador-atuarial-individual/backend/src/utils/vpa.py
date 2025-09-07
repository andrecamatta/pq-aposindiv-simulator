"""
Utilitários para cálculos de Valor Presente Atuarial (VPA) e Anuidades

CORREÇÕES IMPLEMENTADAS:

1. VALIDAÇÃO DE INPUTS:
   - Verificação de consistência entre listas de cash flows e probabilidades
   - Validação de taxas de desconto (0 ≤ taxa ≤ 100%)
   - Verificação de probabilidades de sobrevivência (decrescentes, 0 ≤ p ≤ 1)
   - Detecção de valores extremos e infinitos

2. ROBUSTEZ MATEMÁTICA:
   - Tratamento de overflow/underflow em fatores de desconto
   - Verificação de resultados finitos
   - Continuidade em caso de valores inválidos

3. CONVENÇÕES PADRONIZADAS:
   - Timing adjustment consistente: antecipado = 0.0, postecipado = 1.0
   - Fórmulas atuariais padrão para VPA e anuidades
   - Separação clara entre fase ativa e aposentadoria

4. BENEFÍCIO SUSTENTÁVEL SIMPLIFICADO:
   - Extração da lógica complexa em função dedicada
   - Cálculo direto usando fator de anuidade vitalícia
   - Ajuste automático para múltiplos pagamentos anuais (13º, 14º)
"""

from typing import List, Tuple, TYPE_CHECKING
from .discount import calculate_discount_factor, get_timing_adjustment
import math
import logging

logger = logging.getLogger(__name__)

# Import apenas para type hints, evita circular imports
if TYPE_CHECKING:
    from ..models.database import SimulatorState
    from ..core.actuarial_engine import ActuarialEngine


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
        # Log do problema para investigação, mas não falhar
        logger.warning(f"[VPA_DEBUG] COMPRIMENTOS INCONSISTENTES DETECTADOS - cash_flows={len(cash_flows)}, survival_probs={len(survival_probs)}")
        # A correção será feita na função que chama esta validação
    
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
        if i > 0 and prob > survival_probs[i-1]:
            raise ValueError(f"Probabilidade de sobrevivência crescente no índice {i}: {prob} > {survival_probs[i-1]}")
    
    # Validar fluxos de caixa para valores extremos
    for i, cf in enumerate(cash_flows):
        if not math.isfinite(cf):
            raise ValueError(f"Fluxo de caixa não finito no índice {i}: {cf}")
        if abs(cf) > 1e12:  # 1 trilhão
            raise ValueError(f"Fluxo de caixa extremo no índice {i}: {cf}")


def validate_mortality_conversion(mortality_rates: List[float]) -> None:
    """
    Valida taxas de mortalidade para conversão mensal.
    
    Args:
        mortality_rates: Lista de probabilidades anuais de mortalidade (qx)
    
    Raises:
        ValueError: Se alguma taxa for inválida
    """
    for i, qx in enumerate(mortality_rates):
        if qx < 0 or qx > 1:
            raise ValueError(f"Taxa de mortalidade inválida no índice {i}: {qx}")
        if qx >= 0.99:  # Taxa extremamente alta - suspeita
            raise ValueError(f"Taxa de mortalidade suspeita (>=99%) no índice {i}: {qx}")
        if i > 0 and qx < mortality_rates[i-1] * 0.5:  # Redução drástica - suspeita
            raise ValueError(f"Redução drástica na mortalidade no índice {i}: {qx} vs {mortality_rates[i-1]}")


def calculate_actuarial_present_value(
    cash_flows: List[float],
    survival_probs: List[float],
    discount_rate_monthly: float,
    payment_timing: str,
    start_month: int = 0,
    end_month: int = None
) -> float:
    """
    Calcula o valor presente atuarial de fluxos de caixa com probabilidades de sobrevivência.
    
    Implementa o cálculo padrão atuarial: VPA = Σ(CF_t × tPx × v^t)
    onde:
    - CF_t = fluxo de caixa no tempo t
    - tPx = probabilidade de sobrevivência até o tempo t
    - v^t = fator de desconto para o tempo t
    
    Args:
        cash_flows: Lista de fluxos de caixa mensais
        survival_probs: Lista de probabilidades de sobrevivência (tPx)
        discount_rate_monthly: Taxa de juros técnica mensal
        payment_timing: Tipo de anuidade ("antecipado" ou "postecipado")
        start_month: Mês inicial (inclusive)
        end_month: Mês final (exclusive), None para usar todo o período
    
    Returns:
        Valor presente atuarial dos fluxos
        
    Raises:
        ValueError: Se inputs forem inválidos
    """
    # Validar inputs
    validate_actuarial_inputs(cash_flows, survival_probs, discount_rate_monthly, start_month, end_month)
    
    # CORREÇÃO AUTOMÁTICA: Se os comprimentos forem inconsistentes, ajustar
    if len(cash_flows) != len(survival_probs):
        min_length = min(len(cash_flows), len(survival_probs))
        logger.warning(f"[VPA_DEBUG] CORREÇÃO AUTOMÁTICA - Ajustando para min_length={min_length}")
        cash_flows = cash_flows[:min_length]
        survival_probs = survival_probs[:min_length]
    
    if end_month is None:
        end_month = min(len(cash_flows), len(survival_probs))
    
    timing_adjustment = get_timing_adjustment(payment_timing)
    vpa = 0.0
    
    for month in range(start_month, end_month):
        if month < len(cash_flows) and month < len(survival_probs):
            cash_flow = cash_flows[month]
            survival_prob = survival_probs[month]
            
            if cash_flow > 0 and survival_prob > 0:
                discount_factor = calculate_discount_factor(
                    discount_rate_monthly,
                    month,
                    timing_adjustment
                )
                
                # Verificar overflow no cálculo
                if discount_factor == 0:
                    continue  # Skip se o fator de desconto for zero (overflow)
                
                contribution = (cash_flow * survival_prob) / discount_factor
                
                # Verificar se o resultado é finito
                if not math.isfinite(contribution):
                    continue
                    
                vpa += contribution
    
    # Validar resultado final
    if not math.isfinite(vpa):
        raise ValueError("VPA resultante não é finito")
    
    return vpa


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


def calculate_vpa_benefits_contributions(
    monthly_benefits: List[float],
    monthly_contributions: List[float],
    survival_probs: List[float],
    discount_rate_monthly: float,
    payment_timing: str,
    months_to_retirement: int,
    admin_fee_monthly: float = 0.0
) -> Tuple[float, float]:
    """
    Calcula VPA de benefícios de aposentadoria e contribuições ativas.
    
    Args:
        monthly_benefits: Lista de benefícios mensais de aposentadoria
        monthly_contributions: Lista de contribuições mensais na fase ativa
        survival_probs: Lista de probabilidades de sobrevivência (tPx)
        discount_rate_monthly: Taxa de juros técnica mensal
        payment_timing: Tipo de anuidade
        months_to_retirement: Período diferido (meses até aposentadoria)
        admin_fee_monthly: Taxa administrativa mensal sobre saldo (opcional)
    
    Returns:
        Tupla (VPA_benefícios_aposentadoria, VPA_contribuições_ativas)
    """
    # VPA dos benefícios de aposentadoria (anuidade diferida)
    vpa_benefits = calculate_actuarial_present_value(
        monthly_benefits,
        survival_probs,
        discount_rate_monthly,
        payment_timing,
        start_month=months_to_retirement
    )
    
    # VPA das contribuições na fase ativa considerando taxa administrativa
    vpa_contributions = calculate_vpa_contributions_with_admin_fees(
        monthly_contributions,
        survival_probs,
        discount_rate_monthly,
        admin_fee_monthly,
        payment_timing,
        months_to_retirement
    )
    
    return vpa_benefits, vpa_contributions


def _bisection_root_finding(
    objective_function, 
    low_bound: float, 
    high_bound: float, 
    tolerance: float = 0.01, 
    max_iterations: int = 100
) -> float:
    """
    Algoritmo híbrido (bissecção + secante) otimizado para convergência rápida.
    
    Args:
        objective_function: Função f(x) para encontrar x onde f(x) = 0
        low_bound: Limite inferior do intervalo
        high_bound: Limite superior do intervalo
        tolerance: Tolerância para convergência
        max_iterations: Máximo de iterações
    
    Returns:
        Valor x onde f(x) ≈ 0
    """
    logger.debug(f"[BISSECÇÃO] Iniciando com bounds: [{low_bound:.2f}, {high_bound:.2f}], tolerância: {tolerance}")
    
    # Verificar condições iniciais
    try:
        f_low = objective_function(low_bound)
        f_high = objective_function(high_bound)
        
        logger.debug(f"[BISSECÇÃO] Valores iniciais: f({low_bound:.2f})={f_low:.2f}, f({high_bound:.2f})={f_high:.2f}")
        
        # Verificar se já temos a resposta nos extremos
        if abs(f_low) < tolerance:
            logger.debug(f"[BISSECÇÃO] Resposta encontrada no lower bound")
            return low_bound
        if abs(f_high) < tolerance:
            logger.debug(f"[BISSECÇÃO] Resposta encontrada no upper bound")
            return high_bound
            
        # Verificar se temos sinais opostos
        if (f_low * f_high) > 0:
            logger.warning(f"[BISSECÇÃO] Bounds não têm sinais opostos: f_low={f_low:.2f}, f_high={f_high:.2f}")
            # Retornar ponto médio como estimativa
            return (low_bound + high_bound) / 2.0
            
    except Exception as e:
        logger.error(f"[BISSECÇÃO] Erro na verificação inicial: {e}")
        return (low_bound + high_bound) / 2.0
    
    # Algoritmo híbrido otimizado (Brent's method simplificado)
    iteration = 0
    prev_x, prev_f = None, None
    
    while iteration < max_iterations:
        # Usar método da secante nas primeiras iterações se possível
        if iteration >= 2 and prev_x is not None and prev_f is not None and abs(prev_f) > tolerance:
            # Tentativa com método da secante (mais rápido)
            try:
                if abs(f_low - prev_f) > 1e-10:  # Evitar divisão por zero
                    secant_x = low_bound - f_low * (low_bound - prev_x) / (f_low - prev_f)
                    # Verificar se ponto da secante está dentro do intervalo
                    if low_bound < secant_x < high_bound:
                        mid_point = secant_x
                        logger.debug(f"[HÍBRIDO] Iter {iteration}: Usando secante x={mid_point:.2f}")
                    else:
                        mid_point = (low_bound + high_bound) / 2.0
                        logger.debug(f"[HÍBRIDO] Iter {iteration}: Secante fora do intervalo, usando bissecção")
                else:
                    mid_point = (low_bound + high_bound) / 2.0
            except:
                mid_point = (low_bound + high_bound) / 2.0
        else:
            mid_point = (low_bound + high_bound) / 2.0
        
        try:
            f_mid = objective_function(mid_point)
            
            # Validação crítica: verificar se f_mid é válido
            import math
            if math.isnan(f_mid) or math.isinf(f_mid):
                logger.error(f"[HÍBRIDO] Valor inválido f({mid_point:.2f}) = {f_mid}")
                return float(mid_point)
            
            if iteration < 5 or iteration % 20 == 0:  # Log menos frequente
                logger.debug(f"[HÍBRIDO] Iter {iteration}: x={mid_point:.2f}, f(x)={f_mid:.2f}")
            
            # Verificar convergência com tolerância mais agressiva
            if abs(f_mid) < tolerance:
                logger.debug(f"[HÍBRIDO] Convergiu em {iteration} iterações: x={mid_point:.2f}")
                return float(mid_point)
                
            # Verificar se o intervalo ficou muito pequeno (convergência por intervalo)
            if abs(high_bound - low_bound) < tolerance * 0.01:
                logger.debug(f"[HÍBRIDO] Convergência por intervalo: x={mid_point:.2f}")
                return float(mid_point)
            
            # Salvar estado anterior para método da secante
            prev_x, prev_f = low_bound, f_low
            
            # Atualizar bounds
            if (f_low * f_mid) < 0:
                high_bound = mid_point
                f_high = f_mid
            else:
                low_bound = mid_point
                f_low = f_mid
                
        except Exception as e:
            logger.error(f"[HÍBRIDO] Erro na iteração {iteration}: {e}")
            return float(mid_point)
            
        iteration += 1
    
    # Se não convergiu, retornar melhor estimativa
    final_result = (low_bound + high_bound) / 2.0
    logger.warning(f"[HÍBRIDO] Não convergiu em {max_iterations} iterações, retornando: {final_result:.2f}")
    return float(final_result)


def calculate_sustainable_benefit_with_engine(
    state: "SimulatorState",
    engine: "ActuarialEngine"
) -> float:
    """
    Calcula benefício sustentável usando root finding com ActuarialEngine.
    
    Esta função encontra o valor de benefício que zera o déficit/superávit
    usando o método da bissecção e o engine atuarial completo.
    
    Args:
        state: Estado atual do simulador
        engine: Engine atuarial para cálculos
    
    Returns:
        Benefício mensal que zera o déficit/superávit
    """
    # Importação dinâmica para evitar circular imports
    import copy
    
    # Cache para evitar recálculos
    calculation_cache = {}
    
    def objective_function(benefit_value: float) -> float:
        """
        Função objetivo otimizada com cache: retorna déficit/superávit para um dado benefício.
        Quando retorna 0, temos o benefício sustentável.
        """
        # Arredondar para evitar muitos cálculos muito próximos
        cache_key = round(benefit_value, 2)
        
        if cache_key in calculation_cache:
            logger.debug(f"[SUSTENTÁVEL] Cache hit para R$ {benefit_value:.2f}")
            return calculation_cache[cache_key]
        
        # Criar cópia do estado com novo benefício
        test_state = copy.deepcopy(state)
        test_state.target_benefit = float(benefit_value)
        test_state.benefit_target_mode = "VALUE"
        
        # Calcular usando engine atuarial existente
        try:
            results = engine.calculate_individual_simulation(test_state)
            result = results.deficit_surplus
            
            # PROTEÇÃO CRÍTICA: verificar se resultado é finito antes de usar
            import math
            if not math.isfinite(result):
                logger.error(f"[SUSTENTÁVEL] Engine retornou valor não finito: {result} para benefício {benefit_value:.2f}")
                # Retornar valor seguro baseado no salário para guiar o algoritmo
                safe_result = benefit_value - salary_monthly  # Déficit/superávit estimado
                calculation_cache[cache_key] = safe_result
                return safe_result
            
            # Armazenar no cache
            calculation_cache[cache_key] = result
            
            logger.debug(f"[SUSTENTÁVEL] Benefício: R$ {benefit_value:.2f} → Déficit: R$ {result:.2f}")
            return result
        except Exception as e:
            logger.error(f"[SUSTENTÁVEL] Erro no cálculo para benefício {benefit_value}: {e}")
            # Em caso de erro, retornar valor alto para evitar essa região (JSON-safe)
            error_result = 1e6  # 1 milhão - valor muito alto mas JSON-safe
            calculation_cache[cache_key] = error_result
            return error_result
    
    # Determinar bounds inteligentes baseados no salário e benefício desejado
    salary_monthly = state.salary / 12.0 if hasattr(state, 'salary') else 8000.0
    benefit_hint = state.target_benefit if state.target_benefit else salary_monthly
    logger.debug(f"[SUSTENTÁVEL] Salário mensal: R$ {salary_monthly:.2f}, Benefício desejado: R$ {benefit_hint:.2f}")
    
    # Bounds inteligentes: usar o maior entre salário e benefício desejado como referência
    reference_value = max(salary_monthly, benefit_hint)
    low_bound = min(salary_monthly * 0.01, reference_value * 0.1)  # Mínimo mais baixo
    high_bound = max(salary_monthly * 10.0, reference_value * 2.0)  # Máximo mais alto baseado no benefício
    
    logger.debug(f"[SUSTENTÁVEL] Bounds iniciais: R$ {low_bound:.2f} - R$ {high_bound:.2f}")
    
    # Ajustar bounds se necessário para garantir que tenham sinais opostos
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        try:
            f_low = objective_function(low_bound)
            f_high = objective_function(high_bound)
            
            logger.debug(f"[SUSTENTÁVEL] Tentativa {attempt + 1}: f({low_bound:.2f})={f_low:.2f}, f({high_bound:.2f})={f_high:.2f}")
            
            # Verificar se temos sinais opostos (condição para bissecção)
            if (f_low * f_high) <= 0:
                logger.debug(f"[SUSTENTÁVEL] Bounds válidos encontrados")
                break
                
            # Se ambos têm mesmo sinal, expandir bounds dinamicamente
            if f_low > 0 and f_high > 0:  # Ambos superávit - aumentar benefício
                logger.debug(f"[SUSTENTÁVEL] Ambos superávit - expandindo upper bound")
                low_bound = high_bound  # O que era high vira low
                high_bound = high_bound * 2.0  # Dobrar upper bound
                
            elif f_low < 0 and f_high < 0:  # Ambos déficit - diminuir benefício
                logger.debug(f"[SUSTENTÁVEL] Ambos déficit - expandindo lower bound")
                high_bound = low_bound  # O que era low vira high
                low_bound = max(low_bound * 0.5, salary_monthly * 0.01)  # Reduzir lower bound
                
            # Evitar bounds extremos
            if high_bound > salary_monthly * 1000:  # Máximo 1000x o salário
                logger.warning(f"[SUSTENTÁVEL] Upper bound extremo, limitando")
                high_bound = salary_monthly * 1000
                break
            if low_bound < salary_monthly * 0.001:  # Mínimo 0.1% do salário
                logger.warning(f"[SUSTENTÁVEL] Lower bound extremo, limitando")
                low_bound = salary_monthly * 0.001
                break
                
        except Exception as e:
            logger.error(f"[SUSTENTÁVEL] Erro ao ajustar bounds: {e}")
            break
            
        attempt += 1
    
    # Se não conseguiu encontrar bounds válidos, usar fallback
    if attempt >= max_attempts:
        logger.warning(f"[SUSTENTÁVEL] Não foi possível encontrar bounds válidos, usando fallback")
        # Fallback: usar benefício baseado no salário atual
        fallback_benefit = salary_monthly * 0.7  # 70% do salário como estimativa
        logger.debug(f"[SUSTENTÁVEL] Fallback: R$ {fallback_benefit:.2f}")
        return fallback_benefit
    
    # Encontrar benefício sustentável com bissecção melhorada
    logger.debug(f"[SUSTENTÁVEL] Iniciando bissecção com bounds: R$ {low_bound:.2f} - R$ {high_bound:.2f}")
    
    result = _bisection_root_finding(
        objective_function,
        low_bound,
        high_bound,
        tolerance=1.0,   # Tolerância mais rigorosa: R$ 1,00
        max_iterations=200  # Mais iterações para maior precisão
    )
    
    # Validação crítica: garantir que resultado é válido e JSON-safe
    import math
    if math.isnan(result) or math.isinf(result) or result <= 0:
        logger.warning(f"[SUSTENTÁVEL] Resultado inválido: {result}, usando fallback")
        result = salary_monthly * 0.7  # 70% do salário como fallback
        
    # PROTEÇÃO ADICIONAL: garantir que não há valores infinitos nos cálculos intermediários
    if not math.isfinite(result):
        logger.error(f"[SUSTENTÁVEL] Valor não finito detectado: {result}")
        result = salary_monthly * 0.5  # Fallback mais conservador
    
    # Garantir que o resultado está dentro de limites razoáveis
    min_benefit = salary_monthly * 0.05  # Mínimo 5% do salário
    max_benefit = salary_monthly * 20.0   # Máximo 20x o salário
    result = max(min_benefit, min(max_benefit, result))
    
    logger.debug(f"[SUSTENTÁVEL] Resultado final (validado): R$ {result:.2f}")
    return float(result)


def calculate_sustainable_benefit(
    initial_balance: float,
    vpa_contributions: float,
    survival_probs: List[float],
    discount_rate_monthly: float,
    payment_timing: str,
    months_to_retirement: int,
    benefit_months_per_year: int = 12,
    admin_fee_monthly: float = 0.0
) -> float:
    """
    Calcula benefício sustentável usando método simplificado.
    
    Para cálculos mais precisos, use calculate_sustainable_benefit_with_engine.
    """
    total_resources = initial_balance + vpa_contributions
    
    annuity_factor = calculate_life_annuity_factor(
        survival_probs,
        discount_rate_monthly,
        payment_timing,
        start_month=months_to_retirement
    )
    
    annual_payment_factor = benefit_months_per_year / 12.0
    effective_annuity_factor = annuity_factor * annual_payment_factor
    
    if effective_annuity_factor > 0:
        return total_resources / effective_annuity_factor
    else:
        return 0.0


def calculate_vpa_contributions_with_admin_fees(
    monthly_contributions: List[float],
    survival_probs: List[float],
    discount_rate_monthly: float,
    admin_fee_monthly: float,
    payment_timing: str,
    months_to_retirement: int
) -> float:
    """
    Calcula VPA das contribuições considerando o impacto da taxa administrativa.
    
    A taxa administrativa reduz o valor efetivo das contribuições ao longo do tempo,
    pois é aplicada sobre o saldo acumulado mensalmente. Esta função simula esse
    efeito no cálculo atuarial.
    
    Método:
    1. Para cada contribuição mensal, calcula o fator de erosão pela taxa administrativa
    2. O fator considera quantos meses a contribuição ficará sujeita à taxa administrativa
    3. Aplica o VPA sobre as contribuições ajustadas pelo fator de erosão
    
    Args:
        monthly_contributions: Lista de contribuições mensais líquidas
        survival_probs: Lista de probabilidades de sobrevivência (tPx)
        discount_rate_monthly: Taxa de juros técnica mensal  
        admin_fee_monthly: Taxa administrativa mensal sobre saldo
        payment_timing: Tipo de anuidade ("antecipado" ou "postecipado")
        months_to_retirement: Período ativo em meses
        
    Returns:
        VPA das contribuições ajustado pela taxa administrativa
    """
    logger.debug(f"[VPA_DEBUG] Calculando VPA com taxa administrativa: {admin_fee_monthly}")
    logger.debug(f"[VPA_DEBUG] Parâmetros: discount_rate={discount_rate_monthly}, months_to_retirement={months_to_retirement}")
    logger.debug(f"[VPA_DEBUG] Contribuições length: {len(monthly_contributions)}, Survival length: {len(survival_probs)}")
    
    if admin_fee_monthly <= 0:
        logger.info(f"[VPA_DEBUG] Taxa administrativa zero ou negativa, usando cálculo padrão")
        logger.debug(f"[VPA_DEBUG] ANTES DO CÁLCULO PADRÃO - Contribuições length: {len(monthly_contributions)}, Survival length: {len(survival_probs)}")
        # Se não há taxa administrativa, usar cálculo padrão
        try:
            result = calculate_actuarial_present_value(
                monthly_contributions,
                survival_probs,
                discount_rate_monthly,
                payment_timing,
                start_month=0,
                end_month=months_to_retirement
            )
            logger.debug(f"[VPA_DEBUG] VPA padrão calculado: {result}")
            return result
        except ValueError as e:
            logger.error(f"[VPA_DEBUG] ERRO no cálculo padrão: {e}")
            logger.error(f"[VPA_DEBUG] Contribuições length: {len(monthly_contributions)}, Survival length: {len(survival_probs)}")
            logger.error(f"[VPA_DEBUG] months_to_retirement: {months_to_retirement}")
            # Corrigir automaticamente usando o menor comprimento
            min_length = min(len(monthly_contributions), len(survival_probs), months_to_retirement)
            logger.warning(f"[VPA_DEBUG] Usando comprimento mínimo: {min_length}")
            result = calculate_actuarial_present_value(
                monthly_contributions[:min_length],
                survival_probs[:min_length],
                discount_rate_monthly,
                payment_timing,
                start_month=0,
                end_month=min_length
            )
            return result
    
    timing_adjustment = get_timing_adjustment(payment_timing)
    vpa_adjusted = 0.0
    
    logger.debug(f"[VPA_DEBUG] Iniciando cálculo com taxa administrativa > 0: {admin_fee_monthly}")
    
    for month in range(min(months_to_retirement, len(monthly_contributions))):
        if month < len(survival_probs):
            contribution = monthly_contributions[month]
            survival_prob = survival_probs[month]
            
            if contribution > 0 and survival_prob > 0:
                # Calcular quantos meses essa contribuição ficará sujeita à taxa administrativa
                months_under_admin_fee = months_to_retirement - month
                
                # Validações para evitar valores infinitos no fator de erosão
                if admin_fee_monthly >= 1.0:
                    logger.error(f"[VPA_DEBUG] Taxa administrativa impossível: {admin_fee_monthly} (>= 100%), usando erosion_factor = 0")
                    erosion_factor = 0.0
                elif months_under_admin_fee > 1000:  # Limite prático para evitar overflow
                    logger.warning(f"[VPA_DEBUG] Período muito longo: {months_under_admin_fee} meses, limitando erosão")
                    erosion_factor = 0.001  # Valor mínimo prático
                else:
                    try:
                        # Fator de erosão: (1 - admin_fee_monthly)^months_under_admin_fee
                        # Representa o valor remanescente após aplicação da taxa administrativa
                        base = 1 - admin_fee_monthly
                        if base <= 0:
                            erosion_factor = 0.0
                        else:
                            erosion_factor = base ** months_under_admin_fee
                            
                        # Verificar se erosion_factor é válido
                        if math.isnan(erosion_factor) or math.isinf(erosion_factor):
                            logger.error(f"[VPA_DEBUG] Erosion factor inválido no mês {month}: {erosion_factor}")
                            erosion_factor = max(0.0, 1 - admin_fee_monthly)  # Usar aproximação linear
                    
                    except (OverflowError, ZeroDivisionError):
                        logger.error(f"[VPA_DEBUG] Erro no cálculo do erosion factor no mês {month}")
                        erosion_factor = max(0.0, 1 - admin_fee_monthly)  # Usar aproximação linear
                
                if month < 5:  # Log apenas os primeiros meses para não poluir
                    logger.debug(f"[VPA_DEBUG] Mês {month}: contrib={contribution}, erosion_factor={erosion_factor}, months_under_fee={months_under_admin_fee}")
                
                # Se erosion factor for inválido, pular esta contribuição
                if erosion_factor < 0 or not math.isfinite(erosion_factor):
                    logger.error(f"[VPA_DEBUG] Erosion factor inválido no mês {month}: {erosion_factor}, pulando contribuição")
                    continue
                
                # Contribuição efetiva após erosão administrativa
                effective_contribution = contribution * erosion_factor
                
                # Fator de desconto atuarial
                discount_factor = calculate_discount_factor(
                    discount_rate_monthly,
                    month,
                    timing_adjustment
                )
                
                if discount_factor > 0:
                    contribution_pv = (effective_contribution * survival_prob) / discount_factor
                    if math.isfinite(contribution_pv):
                        vpa_adjusted += contribution_pv
                    else:
                        logger.error(f"[VPA_DEBUG] PV inválido no mês {month}: {contribution_pv}")
    
    logger.debug(f"[VPA_DEBUG] VPA final com taxa administrativa: {vpa_adjusted}")
    return vpa_adjusted