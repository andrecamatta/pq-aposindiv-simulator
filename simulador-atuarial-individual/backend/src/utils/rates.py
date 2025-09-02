"""
Utilitários para conversão de taxas
"""
import logging
import math

logger = logging.getLogger(__name__)


def annual_to_monthly_rate(annual_rate: float) -> float:
    """
    Converte taxa anual para taxa mensal equivalente.
    
    Fórmula: taxa_mensal = (1 + taxa_anual)^(1/12) - 1
    
    Args:
        annual_rate: Taxa anual (ex: 0.06 para 6% ao ano)
    
    Returns:
        Taxa mensal equivalente
    """
    logger.debug(f"[TAXA_DEBUG] Convertendo taxa anual {annual_rate} para mensal")
    
    if annual_rate == 0:
        logger.info(f"[TAXA_DEBUG] Taxa anual é zero, retornando taxa mensal zero")
        return 0.0
    
    if annual_rate < -1:
        logger.warning(f"[TAXA_DEBUG] Taxa anual negativa muito baixa: {annual_rate}")
        
    monthly_rate = (1 + annual_rate) ** (1/12) - 1
    
    # Verificar se o resultado é válido
    if math.isnan(monthly_rate) or math.isinf(monthly_rate):
        logger.error(f"[TAXA_DEBUG] Taxa mensal inválida calculada: {monthly_rate} (input: {annual_rate})")
        return 0.0
    
    logger.debug(f"[TAXA_DEBUG] Taxa anual {annual_rate} -> taxa mensal {monthly_rate}")
    return monthly_rate


def monthly_to_annual_rate(monthly_rate: float) -> float:
    """
    Converte taxa mensal para taxa anual equivalente.
    
    Fórmula: taxa_anual = (1 + taxa_mensal)^12 - 1
    
    Args:
        monthly_rate: Taxa mensal (ex: 0.005 para 0.5% ao mês)
    
    Returns:
        Taxa anual equivalente
    """
    return (1 + monthly_rate) ** 12 - 1