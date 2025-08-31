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
    adjusted_month = month + timing_adjustment
    return (1 + discount_rate_monthly) ** adjusted_month


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