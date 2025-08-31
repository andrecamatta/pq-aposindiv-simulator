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

from typing import List, Tuple
from .discount import calculate_discount_factor, get_timing_adjustment
import math


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
        raise ValueError(f"Comprimentos inconsistentes: cash_flows={len(cash_flows)}, survival_probs={len(survival_probs)}")
    
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


def calculate_sustainable_benefit(
    initial_balance: float,
    vpa_contributions: float,
    survival_probs: List[float],
    discount_rate_monthly: float,
    payment_timing: str,
    months_to_retirement: int,
    benefit_months_per_year: int = 12
) -> float:
    """
    Calcula benefício mensal sustentável usando equilíbrio atuarial.
    
    Fórmula: Benefício_Sustentável = Recursos_Totais / Fator_Anuidade_Vitalícia
    onde Recursos_Totais = Saldo_Inicial + VPA_Contribuições_Futuras
    
    Args:
        initial_balance: Saldo inicial acumulado
        vpa_contributions: VPA das contribuições futuras
        survival_probs: Lista de probabilidades de sobrevivência
        discount_rate_monthly: Taxa de juros técnica mensal
        payment_timing: Tipo de anuidade ("antecipado" ou "postecipado")
        months_to_retirement: Período diferido até aposentadoria
        benefit_months_per_year: Pagamentos de benefício por ano (12, 13, 14, etc.)
    
    Returns:
        Benefício mensal sustentável (base, sem pagamentos extras)
    """
    # Recursos totais disponíveis para equilíbrio atuarial
    total_resources = initial_balance + vpa_contributions
    
    # Calcular fator de anuidade vitalícia mensal desde aposentadoria
    annuity_factor = calculate_life_annuity_factor(
        survival_probs,
        discount_rate_monthly,
        payment_timing,
        start_month=months_to_retirement
    )
    
    # Ajustar fator pela frequência de pagamentos anuais
    # Se há 13 pagamentos por ano, cada R$ 1,00 mensal = R$ 13,00/12 = R$ 1,083 efetivo
    annual_payment_factor = benefit_months_per_year / 12.0
    effective_annuity_factor = annuity_factor * annual_payment_factor
    
    # Calcular benefício sustentável
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
    if admin_fee_monthly <= 0:
        # Se não há taxa administrativa, usar cálculo padrão
        return calculate_actuarial_present_value(
            monthly_contributions,
            survival_probs,
            discount_rate_monthly,
            payment_timing,
            start_month=0,
            end_month=months_to_retirement
        )
    
    timing_adjustment = get_timing_adjustment(payment_timing)
    vpa_adjusted = 0.0
    
    for month in range(min(months_to_retirement, len(monthly_contributions))):
        if month < len(survival_probs):
            contribution = monthly_contributions[month]
            survival_prob = survival_probs[month]
            
            if contribution > 0 and survival_prob > 0:
                # Calcular quantos meses essa contribuição ficará sujeita à taxa administrativa
                months_under_admin_fee = months_to_retirement - month
                
                # Fator de erosão: (1 - admin_fee_monthly)^months_under_admin_fee
                # Representa o valor remanescente após aplicação da taxa administrativa
                erosion_factor = (1 - admin_fee_monthly) ** months_under_admin_fee
                
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
    
    return vpa_adjusted