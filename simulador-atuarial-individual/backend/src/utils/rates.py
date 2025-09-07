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
    
    # Validações para evitar valores infinitos ou inválidos
    if annual_rate <= -1.0:
        logger.error(f"[TAXA_DEBUG] Taxa anual impossível: {annual_rate} (<= -100%), usando 0%")
        return 0.0
    
    if annual_rate < -0.99:
        logger.warning(f"[TAXA_DEBUG] Taxa anual negativa muito baixa: {annual_rate}, limitando a -99%")
        annual_rate = -0.99
    
    # Limitar taxa anual extrema para evitar overflow
    if abs(annual_rate) > 100:  # Mais de 10000% ao ano
        logger.warning(f"[TAXA_DEBUG] Taxa anual extrema: {annual_rate}, limitando")
        annual_rate = 100 if annual_rate > 0 else -0.99
    
    try:
        base = 1 + annual_rate
        if base <= 0:
            logger.error(f"[TAXA_DEBUG] Base inválida: {base}, usando taxa zero")
            return 0.0
        
        monthly_rate = base ** (1/12) - 1
        
        # Verificar se o resultado é válido
        if math.isnan(monthly_rate) or math.isinf(monthly_rate):
            logger.error(f"[TAXA_DEBUG] Taxa mensal inválida calculada: {monthly_rate} (input: {annual_rate})")
            return 0.0
        
        logger.debug(f"[TAXA_DEBUG] Taxa anual {annual_rate} -> taxa mensal {monthly_rate}")
        return monthly_rate
        
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        logger.error(f"[TAXA_DEBUG] Erro no cálculo da taxa: {e} (input: {annual_rate})")
        return 0.0


def monthly_to_annual_rate(monthly_rate: float) -> float:
    """
    Converte taxa mensal para taxa anual equivalente.
    
    Fórmula: taxa_anual = (1 + taxa_mensal)^12 - 1
    
    Args:
        monthly_rate: Taxa mensal (ex: 0.005 para 0.5% ao mês)
    
    Returns:
        Taxa anual equivalente
    """
    # Validações para evitar valores infinitos
    if monthly_rate <= -1.0:
        logger.error(f"[TAXA_DEBUG] Taxa mensal impossível: {monthly_rate} (<= -100%), usando 0%")
        return 0.0
    
    if monthly_rate < -0.99:
        logger.warning(f"[TAXA_DEBUG] Taxa mensal negativa muito baixa: {monthly_rate}, limitando a -99%")
        monthly_rate = -0.99
    
    # Limitar taxa mensal extrema para evitar overflow
    if abs(monthly_rate) > 10:  # Mais de 1000% ao mês
        logger.warning(f"[TAXA_DEBUG] Taxa mensal extrema: {monthly_rate}, limitando")
        monthly_rate = 10 if monthly_rate > 0 else -0.99
    
    try:
        base = 1 + monthly_rate
        if base <= 0:
            logger.error(f"[TAXA_DEBUG] Base inválida para taxa mensal: {base}, usando 0%")
            return 0.0
        
        annual_rate = base ** 12 - 1
        
        # Verificar se o resultado é válido
        if math.isnan(annual_rate) or math.isinf(annual_rate):
            logger.error(f"[TAXA_DEBUG] Taxa anual inválida calculada: {annual_rate} (input: {monthly_rate})")
            return 0.0
        
        return annual_rate
        
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        logger.error(f"[TAXA_DEBUG] Erro no cálculo da taxa anual: {e} (input: {monthly_rate})")
        return 0.0