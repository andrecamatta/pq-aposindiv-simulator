"""
Validadores customizados para Pydantic
Automatizam sanitização JSON e outras validações
"""
import math
from typing import Any
from pydantic import field_validator


def sanitize_float_value(value: Any) -> Any:
    """
    Sanitiza um único valor float para ser compatível com JSON
    Converte inf, -inf e nan para None

    Args:
        value: Valor a ser sanitizado

    Returns:
        Valor sanitizado ou None se inválido
    """
    if isinstance(value, float):
        if math.isinf(value) or math.isnan(value):
            return None
        return value
    elif isinstance(value, list):
        return [sanitize_float_value(item) for item in value]
    elif isinstance(value, dict):
        return {key: sanitize_float_value(val) for key, val in value.items()}
    elif isinstance(value, tuple):
        return tuple(sanitize_float_value(item) for item in value)
    return value


# Validador individual - evita dependência circular
@field_validator('*', mode='before')
def universal_float_sanitizer(cls, value: Any) -> Any:
    """
    Aplica sanitização automática a todos os campos
    Converte inf, -inf e nan para None
    """
    return sanitize_float_value(value)