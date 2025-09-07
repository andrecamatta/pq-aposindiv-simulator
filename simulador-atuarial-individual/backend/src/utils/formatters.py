"""
Formatadores seguros para valores que podem ser None
"""
from typing import Optional


def format_currency_safe(value: Optional[float], default: str = "Não definido") -> str:
    """
    Formatar valor monetário com proteção contra None
    
    Args:
        value: Valor a ser formatado (pode ser None)
        default: Texto padrão quando valor é None
        
    Returns:
        String formatada como moeda brasileira ou valor padrão
    """
    if value is not None:
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return default


def format_percentage_safe(value: Optional[float], decimals: int = 1, default: str = "Não definido") -> str:
    """
    Formatar porcentagem com proteção contra None
    
    Args:
        value: Valor a ser formatado (pode ser None)
        decimals: Número de casas decimais
        default: Texto padrão quando valor é None
        
    Returns:
        String formatada como porcentagem ou valor padrão
    """
    if value is not None:
        return f"{value:.{decimals}f}%".replace('.', ',')
    return default


def format_benefit_display(state) -> str:
    """
    Formatar display de benefício baseado no modo
    
    Args:
        state: Estado do simulador
        
    Returns:
        String formatada apropriada para o modo de benefício
    """
    benefit_mode = str(state.benefit_target_mode)
    
    if benefit_mode == "VALUE":
        return format_currency_safe(state.target_benefit, "Valor não definido")
    else:  # REPLACEMENT_RATE
        return f"Taxa de Reposição ({format_percentage_safe(state.target_replacement_rate, 1, 'não definida')})"


def format_audit_benefit_section(state) -> tuple[str, list[str]]:
    """
    Formatar seção completa de benefícios para auditoria
    
    Args:
        state: Estado do simulador
        
    Returns:
        Tupla com (título, lista de linhas formatadas)
    """
    lines = []
    benefit_mode = str(state.benefit_target_mode)
    
    if benefit_mode == "VALUE" and state.target_benefit is not None:
        annual_benefit = state.target_benefit * state.benefit_months_per_year
        lines.extend([
            f"  - Benefício mensal: {format_currency_safe(state.target_benefit)}",
            f"  - Benefício anual: {format_currency_safe(annual_benefit)}"
        ])
    else:
        lines.extend([
            f"  - Benefício: Baseado em taxa de reposição",
            f"  - Taxa de reposição: {format_percentage_safe(state.target_replacement_rate)}"
        ])
    
    return "Benefícios:", lines


def format_number_safe(value: Optional[float], decimals: int = 2, default: str = "Não definido") -> str:
    """
    Formatar número com proteção contra None
    
    Args:
        value: Valor a ser formatado (pode ser None)
        decimals: Número de casas decimais
        default: Texto padrão quando valor é None
        
    Returns:
        String formatada como número ou valor padrão
    """
    if value is not None:
        return f"{value:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return default