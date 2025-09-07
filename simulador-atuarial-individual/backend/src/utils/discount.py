"""
Utilitários para cálculos de desconto e timing
"""

from typing import Literal


def calculate_discount_factor(
    discount_rate_monthly: float,
    month: int,
    timing_adjustment: float = 0.0
) -> float:
    """
    Calcula o fator de desconto mensal com ajuste de timing.
    
    Args:
        discount_rate_monthly: Taxa de desconto mensal
        month: Número de meses para desconto
        timing_adjustment: Ajuste temporal em meses (negativo para antecipado, positivo para postecipado)
    
    Returns:
        Fator de desconto calculado
    """
    import math
    
    # Validar parâmetros para evitar valores infinitos
    if discount_rate_monthly <= -1.0:
        # Taxa impossível - retornar valor alto mas finito
        return 1e6
    
    adjusted_month = month + timing_adjustment
    
    # Limitar expoente para evitar overflow
    if abs(adjusted_month) > 500:  # Limite prático para evitar overflow
        if adjusted_month > 0:
            return 1e6 if discount_rate_monthly >= 0 else 1e-6
        else:
            return 1e-6 if discount_rate_monthly >= 0 else 1e6
    
    try:
        result = (1 + discount_rate_monthly) ** adjusted_month
        
        # Verificar se resultado é finito
        if math.isfinite(result) and result > 0:
            return result
        else:
            # Retornar valor seguro baseado no sinal esperado
            return 1e6 if adjusted_month >= 0 else 1e-6
            
    except (OverflowError, ZeroDivisionError):
        # Retornar valor seguro em caso de erro
        return 1e6 if adjusted_month >= 0 else 1e-6


def get_timing_adjustment(payment_timing: Literal["antecipado", "postecipado"]) -> float:
    """
    Retorna o ajuste de timing baseado no tipo de pagamento.
    
    Convenções atuariais padrão:
    - Antecipado: pagamento no início do período (t=0, 1, 2, ...)
    - Postecipado: pagamento no final do período (t=1, 2, 3, ...)
    
    Args:
        payment_timing: Tipo de pagamento ("antecipado" ou "postecipado")
    
    Returns:
        Ajuste em períodos:
        - 0.0 para pagamento antecipado (início do período)
        - 1.0 para pagamento postecipado (final do período)
    """
    return 0.0 if payment_timing == "antecipado" else 1.0