"""
Validadores customizados para Pydantic
Automatizam sanitização JSON e outras validações
"""
import math
from typing import Any, Type, Union
from enum import Enum
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


def get_enum_value(value: Union[str, Enum], enum_class: Type[Enum] = None) -> str:
    """
    Extrai o valor string de um enum de forma robusta.
    Funciona tanto com instâncias de enum quanto com strings.

    Args:
        value: Valor a ser processado (enum ou string)
        enum_class: Classe do enum (opcional, para validação)

    Returns:
        String representando o valor do enum

    Example:
        >>> get_enum_value(BenefitTargetMode.VALUE)
        'VALUE'
        >>> get_enum_value("VALUE")
        'VALUE'
    """
    if isinstance(value, Enum):
        return value.value
    elif isinstance(value, str):
        return value
    else:
        return str(value)


def ensure_enum_instance(value: Union[str, Enum], enum_class: Type[Enum]) -> Enum:
    """
    Garante que o valor retornado seja uma instância de enum.
    Converte strings para enum quando possível.

    Args:
        value: Valor a ser processado
        enum_class: Classe do enum de destino

    Returns:
        Instância do enum

    Raises:
        ValueError: Se o valor não for válido para o enum
    """
    if isinstance(value, enum_class):
        return value
    elif isinstance(value, str):
        try:
            return enum_class(value)
        except ValueError:
            raise ValueError(f"'{value}' is not a valid {enum_class.__name__}")
    else:
        raise ValueError(f"Cannot convert {type(value)} to {enum_class.__name__}")


def create_enum_validator(enum_class: Type[Enum]):
    """
    Cria um validador Pydantic para um enum específico.

    Args:
        enum_class: Classe do enum

    Returns:
        Função validadora que pode ser usada com @field_validator
    """
    def validator(cls, value: Any) -> Enum:
        """Valida e converte valores para o enum especificado"""
        if value is None:
            return value
        return ensure_enum_instance(value, enum_class)

    validator.__name__ = f"validate_{enum_class.__name__.lower()}"
    return validator


class EnumMixin:
    """
    Mixin para modelos Pydantic que trabalham com enums.
    Fornece métodos utilitários para lidar com enums de forma robusta.
    """

    def get_enum_value(self, field_name: str) -> str:
        """
        Obtém o valor string de um campo enum de forma robusta.

        Args:
            field_name: Nome do campo

        Returns:
            Valor string do enum
        """
        value = getattr(self, field_name)
        return get_enum_value(value)

    def ensure_enum(self, field_name: str, enum_class: Type[Enum]) -> Enum:
        """
        Garante que um campo seja uma instância de enum.

        Args:
            field_name: Nome do campo
            enum_class: Classe do enum esperada

        Returns:
            Instância do enum
        """
        value = getattr(self, field_name)
        return ensure_enum_instance(value, enum_class)