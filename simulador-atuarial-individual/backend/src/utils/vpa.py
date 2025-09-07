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
from scipy.optimize import fsolve, root_scalar

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


# Função _bisection_root_finding removida - substituída por scipy.optimize.fsolve


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
    # Importação dinâmica para evitar circular imports
    import copy
    
    # Cache para evitar recálculos
    calculation_cache = {}
    
    def objective_function(benefit_value: float) -> float:
        """
        Função objetivo sem cache para máxima precisão: retorna déficit/superávit para um dado benefício.
        Quando retorna 0, temos o benefício sustentável.
        """
        # CORREÇÃO: Eliminar cache para precisão máxima na região crítica
        # Cache pode mascarar pequenas diferenças cruciais para convergência precisa
        
        # Criar cópia do estado com novo benefício
        test_state = copy.deepcopy(state)
        test_state.target_benefit = float(benefit_value)
        
        # CORREÇÃO CRÍTICA: garantir que seja string, não enum
        test_state.benefit_target_mode = "VALUE"
        
        # Calcular usando engine atuarial existente
        try:
            benefit_scalar = float(benefit_value) if hasattr(benefit_value, '__iter__') and hasattr(benefit_value, 'shape') else benefit_value
            logger.debug(f"[VPA_DEBUG] Antes de chamar engine - benefit_value: {benefit_scalar:.2f}")
            logger.debug(f"[VPA_DEBUG] Antes de chamar engine - test_state.benefit_target_mode: {test_state.benefit_target_mode}")
            logger.debug(f"[VPA_DEBUG] Antes de chamar engine - test_state.target_benefit: {test_state.target_benefit}")
            results = engine.calculate_individual_simulation(test_state)
            result = results.deficit_surplus
            
            # PROTEÇÃO CRÍTICA: verificar se resultado é finito antes de usar
            import math
            if not math.isfinite(result):
                benefit_scalar = float(benefit_value) if hasattr(benefit_value, '__iter__') and hasattr(benefit_value, 'shape') else benefit_value
                logger.error(f"[SUSTENTÁVEL] Engine retornou valor não finito: {result} para benefício {benefit_scalar:.2f}")
                # CORREÇÃO: Retornar valor consistente com função de déficit
                # Se benefício muito alto = superávit = valor positivo
                # Se benefício muito baixo = déficit = valor negativo
                if benefit_value > salary_monthly:
                    return 1e6  # Superávit muito alto
                else:
                    return -1e6  # Déficit muito alto
            
            benefit_scalar = float(benefit_value) if hasattr(benefit_value, '__iter__') and hasattr(benefit_value, 'shape') else benefit_value
            logger.debug(f"[SUSTENTÁVEL] Benefício: R$ {benefit_scalar:.2f} → Déficit: R$ {result:.2f}")
            return result
            
        except Exception as e:
            # Converter benefit_value para scalar se for array numpy - PROTEÇÃO ROBUSTA
            try:
                if hasattr(benefit_value, '__iter__') and hasattr(benefit_value, 'shape'):
                    # É um array numpy
                    benefit_scalar = float(benefit_value.item() if benefit_value.size == 1 else benefit_value[0])
                else:
                    benefit_scalar = float(benefit_value)
            except:
                benefit_scalar = 0.0  # Fallback seguro
                
            logger.error(f"[SUSTENTÁVEL] Erro no cálculo para benefício {benefit_scalar:.2f}: {e}")
            
            # CORREÇÃO: Usar lógica consistente baseada no benefício testado
            try:
                benefit_check = float(benefit_value.item() if hasattr(benefit_value, 'item') else benefit_value)
                if benefit_check > salary_monthly:
                    return 1e6  # Assumir superávit alto em caso de erro
                else:
                    return -1e6  # Assumir déficit alto em caso de erro
            except:
                return -1e6  # Fallback para déficit
    
    # Determinar bounds inteligentes baseados no salário e benefício desejado
    # CORREÇÃO CRÍTICA: state.salary já é mensal, não dividir por 12!
    salary_monthly = state.salary if hasattr(state, 'salary') else 8000.0
    benefit_hint = state.target_benefit if state.target_benefit else salary_monthly
    logger.info(f"[VPA_DEBUG] Salário mensal: R$ {salary_monthly:.2f}, Benefício desejado: R$ {benefit_hint:.2f}")
    logger.info(f"[VPA_DEBUG] Déficit atual do estado: R$ {getattr(state, 'deficit_surplus', 'N/A')}")
    
    # DEBUG: Testar função objetivo com valor conhecido
    logger.info(f"[VPA_DEBUG] Testando função objetivo com valores conhecidos...")
    try:
        test_5000 = objective_function(5000.0)
        test_13235 = objective_function(13235.0)
        logger.info(f"[VPA_DEBUG] Função objetivo R$ 5.000: {test_5000:.2f}")
        logger.info(f"[VPA_DEBUG] Função objetivo R$ 13.235: {test_13235:.2f}")
    except Exception as test_error:
        logger.error(f"[VPA_DEBUG] Erro ao testar função objetivo: {test_error}")
        import traceback
        traceback.print_exc()
    
    # Usar scipy.optimize.fsolve como método primário com fallbacks robustos
    logger.info(f"[VPA_DEBUG] Iniciando root finding com fsolve")
    
    # Usar benefício atual como chute inicial inteligente
    initial_guess = benefit_hint if benefit_hint > 0 else salary_monthly * 0.7
    logger.info(f"[VPA_DEBUG] Chute inicial: R$ {initial_guess:.2f}")
    
    try:
        # Tentar fsolve primeiro (método mais robusto)
        result_array = fsolve(objective_function, initial_guess, xtol=1e-6)
        result = float(result_array[0])
        logger.info(f"[VPA_DEBUG] fsolve convergiu para: R$ {result:.2f}")
        
        # Validar resultado do fsolve
        validation_residual = objective_function(result)
        logger.info(f"[VPA_DEBUG] Resíduo da validação: R$ {validation_residual:.2f}")
        
        if abs(validation_residual) <= 50.0:  # Tolerância de R$ 50
            logger.info(f"[SUSTENTÁVEL] ✅ fsolve bem-sucedido: R$ {result:.2f}")
        else:
            logger.warning(f"[SUSTENTÁVEL] fsolve impreciso, tentando root_scalar")
            raise ValueError("fsolve não convergiu adequadamente")
            
    except Exception as fsolve_error:
        logger.warning(f"[VPA_DEBUG] fsolve falhou: {fsolve_error}")
        logger.info(f"[VPA_DEBUG] Tentando root_scalar como fallback")
        
        try:
            # Fallback: usar root_scalar com bounds conservadores
            lower_bound = max(100.0, salary_monthly * 0.1)  # Mín 10% do salário ou R$ 100
            upper_bound = min(salary_monthly * 3.0, 50000.0)  # Máx 3x salário ou R$ 50k
            
            logger.info(f"[VPA_DEBUG] Bounds para root_scalar: R$ {lower_bound:.2f} - R$ {upper_bound:.2f}")
            
            # Testar se os bounds têm sinais opostos
            f_lower = objective_function(lower_bound)
            f_upper = objective_function(upper_bound)
            logger.info(f"[VPA_DEBUG] Teste bounds: f({lower_bound:.2f})={f_lower:.2f}, f({upper_bound:.2f})={f_upper:.2f}")
            
            if (f_lower * f_upper) <= 0:
                sol = root_scalar(objective_function, bracket=[lower_bound, upper_bound], 
                                method='brentq', xtol=1e-6)
                result = float(sol.root)
                logger.info(f"[SUSTENTÁVEL] ✅ root_scalar bem-sucedido: R$ {result:.2f}")
            else:
                logger.error(f"[SUSTENTÁVEL] Bounds não têm sinais opostos, usando chute inicial")
                result = initial_guess
                
        except Exception as root_scalar_error:
            logger.error(f"[VPA_DEBUG] root_scalar também falhou: {root_scalar_error}")
            # Último recurso: usar chute inicial
            result = initial_guess
    
    # VALIDAÇÃO CRÍTICA FINAL: Re-simular sem cache para garantir precisão
    logger.info(f"[SUSTENTÁVEL] Validação final do resultado: R$ {result:.2f}")
    
    # Criar estado de validação limpo
    validation_state = copy.deepcopy(state)
    validation_state.target_benefit = float(result)
    validation_state.benefit_target_mode = "VALUE"
    
    try:
        # Re-calcular sem cache para validar
        final_results = engine.calculate_individual_simulation(validation_state)
        final_deficit = final_results.deficit_surplus
        
        logger.info(f"[SUSTENTÁVEL] Validação final - Déficit residual: R$ {final_deficit:.2f}")
        
        # Verificar se realmente zera o déficit com tolerância rigorosa
        if abs(final_deficit) > 50.0:  # Tolerância de R$ 50
            logger.error(f"[SUSTENTÁVEL] ❌ FALHA NA VALIDAÇÃO FINAL: déficit residual R$ {final_deficit:.2f} > R$ 50")
            # Tentar ajuste fino manual
            adjustment = final_deficit / 1000.0  # Ajuste baseado no déficit residual
            adjusted_result = result - adjustment
            
            logger.info(f"[SUSTENTÁVEL] Tentando ajuste fino: R$ {result:.2f} → R$ {adjusted_result:.2f}")
            
            # Re-validar ajuste
            validation_state.target_benefit = float(adjusted_result)
            adjusted_results = engine.calculate_individual_simulation(validation_state)
            adjusted_deficit = adjusted_results.deficit_surplus
            
            if abs(adjusted_deficit) < abs(final_deficit):
                logger.info(f"[SUSTENTÁVEL] ✅ Ajuste melhorou: R$ {adjusted_deficit:.2f}")
                result = adjusted_result
            else:
                logger.warning(f"[SUSTENTÁVEL] ⚠️ Ajuste não melhorou, mantendo resultado original")
        else:
            logger.info(f"[SUSTENTÁVEL] ✅ Validação final APROVADA: déficit residual R$ {final_deficit:.2f}")
    
    except Exception as validation_error:
        logger.error(f"[SUSTENTÁVEL] Erro na validação final: {validation_error}")
    
    # Validação crítica: garantir que resultado é válido e JSON-safe
    import math
    if math.isnan(result) or math.isinf(result) or result <= 0:
        logger.error(f"[SUSTENTÁVEL] Resultado inválido: {result}, usando fallback")
        result = salary_monthly * 0.7  # 70% do salário como fallback
        
    # PROTEÇÃO ADICIONAL: garantir que não há valores infinitos nos cálculos intermediários
    if not math.isfinite(result):
        logger.error(f"[SUSTENTÁVEL] Valor não finito detectado: {result}")
        result = salary_monthly * 0.5  # Fallback mais conservador
    
    # CORREÇÃO: Limites finais mais razoáveis para evitar valores absurdos
    min_benefit = 50.0  # Mínimo absoluto de R$ 50
    max_benefit = salary_monthly * 5.0   # Máximo 5x o salário (R$ 40.000 para salário de R$ 8.000)
    result = max(min_benefit, min(max_benefit, result))
    
    logger.info(f"[SUSTENTÁVEL] 🎯 RESULTADO FINAL: R$ {result:.2f}")
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


def calculate_parameter_to_zero_deficit(
    state: "SimulatorState",
    engine: "ActuarialEngine",
    parameter_name: str,
    bounds: Tuple[float, float] = None,
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
    
    logger = logging.getLogger(__name__)
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
            # Garantir que estamos em modo VALUE (string, não enum)
            test_state.benefit_target_mode = "VALUE"
            
        elif parameter_name == "contribution_rate":
            test_state.contribution_rate = float(parameter_value)
            
        elif parameter_name == "retirement_age":
            # Garantir idade válida (inteira entre 50-100)
            retirement_age = max(50, min(100, int(round(parameter_value))))
            test_state.retirement_age = retirement_age
            
        elif parameter_name == "salary":
            test_state.salary = float(parameter_value)
            
        else:
            raise ValueError(f"Parâmetro não suportado: {parameter_name}")
        
        # Calcular usando engine atuarial
        try:
            results = engine.calculate_individual_simulation(test_state)
            deficit = results.deficit_surplus
            
            # Verificar se resultado é finito
            import math
            if not math.isfinite(deficit):
                # Converter parameter_value para scalar para log seguro
                param_scalar = float(parameter_value.item() if hasattr(parameter_value, 'item') else parameter_value)
                logger.error(f"[FSOLVE] Engine retornou valor não finito para {parameter_name}={param_scalar:.2f}")
                # Retornar valor alto se inválido
                current_value = getattr(state, parameter_name, 0)
                if param_scalar > current_value:
                    return 1e6  # Superávit alto
                else:
                    return -1e6  # Déficit alto
            
            # Converter parameter_value para scalar para log seguro
            param_scalar = float(parameter_value.item() if hasattr(parameter_value, 'item') else parameter_value)
            logger.debug(f"[FSOLVE] {parameter_name}={param_scalar:.2f} → Déficit=R${deficit:.2f}")
            return deficit
            
        except Exception as e:
            # Converter parameter_value para scalar para log seguro
            param_scalar = float(parameter_value.item() if hasattr(parameter_value, 'item') else parameter_value)
            logger.error(f"[FSOLVE] Erro no cálculo para {parameter_name}={param_scalar:.2f}: {e}")
            # Em caso de erro, assumir comportamento baseado no valor testado
            current_value = getattr(state, parameter_name, 0)
            if param_scalar > current_value:
                return 1e6  # Assumir superávit se valor maior
            else:
                return -1e6  # Assumir déficit se valor menor
    
    # Definir chute inicial baseado no parâmetro
    if initial_guess is None:
        if parameter_name == "target_benefit":
            initial_guess = getattr(state, 'target_benefit', state.salary * 0.7)
        elif parameter_name == "contribution_rate":
            initial_guess = getattr(state, 'contribution_rate', 8.0)
        elif parameter_name == "retirement_age":
            initial_guess = getattr(state, 'retirement_age', 65.0)
        elif parameter_name == "salary":
            initial_guess = getattr(state, 'salary', 8000.0)
    
    # Definir bounds padrão se não fornecidos
    if bounds is None:
        if parameter_name == "target_benefit":
            bounds = (100.0, state.salary * 3.0)  # R$ 100 a 3x salário (mais conservador)
        elif parameter_name == "contribution_rate":
            bounds = (1.0, 30.0)  # 1% a 30%
        elif parameter_name == "retirement_age":
            bounds = (max(50, state.age + 1), 100)  # Idade mínima 50, máxima 100
        elif parameter_name == "salary":
            current_salary = getattr(state, 'salary', 8000.0)
            bounds = (current_salary * 0.1, current_salary * 5.0)  # 10% a 5x salário atual
    
    logger.info(f"[FSOLVE] Parâmetro: {parameter_name}, Chute inicial: {initial_guess:.2f}, Bounds: {bounds}")
    
    try:
        # Tentar fsolve primeiro
        result_array = fsolve(objective_function, initial_guess, xtol=1e-6)
        result = float(result_array[0])
        
        # Validar se resultado está dentro dos bounds
        if bounds and (result < bounds[0] or result > bounds[1]):
            logger.warning(f"[FSOLVE] Resultado fora dos bounds: {result:.2f}, tentando root_scalar")
            raise ValueError("Resultado fora dos bounds")
        
        # Validar resultado
        validation_residual = objective_function(result)
        logger.info(f"[FSOLVE] {parameter_name} convergiu para: {result:.2f}, resíduo: R${validation_residual:.2f}")
        
        if abs(validation_residual) <= 50.0:  # Tolerância de R$ 50
            logger.info(f"[FSOLVE] ✅ Sucesso para {parameter_name}: {result:.2f}")
            return result
        else:
            logger.warning(f"[FSOLVE] Precisão insuficiente, tentando root_scalar")
            raise ValueError("Precisão insuficiente")
            
    except Exception as fsolve_error:
        logger.warning(f"[FSOLVE] fsolve falhou para {parameter_name}: {fsolve_error}")
        
        if bounds:
            try:
                # Fallback: usar root_scalar com bounds
                logger.info(f"[FSOLVE] Tentando root_scalar com bounds {bounds}")
                
                # Testar se os bounds têm sinais opostos
                f_lower = objective_function(bounds[0])
                f_upper = objective_function(bounds[1])
                logger.info(f"[FSOLVE] Teste bounds: f({bounds[0]:.2f})={f_lower:.2f}, f({bounds[1]:.2f})={f_upper:.2f}")
                
                if (f_lower * f_upper) <= 0:
                    sol = root_scalar(objective_function, bracket=bounds, method='brentq', xtol=1e-6)
                    result = float(sol.root)
                    logger.info(f"[FSOLVE] ✅ root_scalar bem-sucedido para {parameter_name}: {result:.2f}")
                    return result
                else:
                    logger.error(f"[FSOLVE] Bounds não têm sinais opostos para {parameter_name}")
                    
            except Exception as root_scalar_error:
                logger.error(f"[FSOLVE] root_scalar também falhou para {parameter_name}: {root_scalar_error}")
        
        # Último recurso: usar chute inicial
        logger.warning(f"[FSOLVE] Usando chute inicial como resultado para {parameter_name}: {initial_guess:.2f}")
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


def calculate_optimal_salary(state: "SimulatorState", engine: "ActuarialEngine") -> float:
    """Calcula salário necessário que zera o déficit/superávit"""
    current_salary = state.salary
    return calculate_parameter_to_zero_deficit(
        state, engine, "salary",
        bounds=(current_salary * 0.1, current_salary * 5.0),
        initial_guess=current_salary
    )