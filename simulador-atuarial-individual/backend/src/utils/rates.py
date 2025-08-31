"""
Utilitários para conversão de taxas
"""


def annual_to_monthly_rate(annual_rate: float) -> float:
    """
    Converte taxa anual para taxa mensal equivalente.
    
    Fórmula: taxa_mensal = (1 + taxa_anual)^(1/12) - 1
    
    Args:
        annual_rate: Taxa anual (ex: 0.06 para 6% ao ano)
    
    Returns:
        Taxa mensal equivalente
    """
    return (1 + annual_rate) ** (1/12) - 1


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