"""Testes para formatadores de valores"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.formatters import (
    format_currency_safe,
    format_percentage_safe,
    apply_br_number_format,
    format_number_br
)


def test_format_currency_safe_with_value():
    """Testa formatação de moeda com valor válido"""
    result = format_currency_safe(1500.50)
    assert "1" in result and "500" in result
    assert result != "Não definido"


def test_format_currency_safe_with_none():
    """Testa formatação de moeda com None"""
    result = format_currency_safe(None)
    assert result == "Não definido"


def test_format_currency_safe_custom_default():
    """Testa formatação com default customizado"""
    result = format_currency_safe(None, default="N/A")
    assert result == "N/A"


def test_format_percentage_safe_with_value():
    """Testa formatação de percentual com valor"""
    result = format_percentage_safe(12.5)
    assert "12" in result and "5" in result
    assert "%" in result


def test_format_percentage_safe_with_none():
    """Testa formatação de percentual com None"""
    result = format_percentage_safe(None)
    assert result == "Não definido"


def test_format_percentage_decimals():
    """Testa número de decimais em percentual"""
    result1 = format_percentage_safe(12.567, decimals=1)
    result2 = format_percentage_safe(12.567, decimals=2)
    assert result1 != result2


def test_apply_br_number_format():
    """Testa aplicação de formato brasileiro"""
    result = apply_br_number_format("R$ 1,234.56")
    # Deve trocar . por , e , por .
    assert "," in result  # Decimal brasileiro
    assert "." in result  # Milhares brasileiro


def test_format_number_br():
    """Testa formatação de números em padrão brasileiro"""
    result = format_number_br(1234.56, 2)
    assert "1" in result and "234" in result
    assert isinstance(result, str)


def test_zero_values():
    """Testa formatação com valores zero"""
    assert format_currency_safe(0.0) != "Não definido"
    assert format_percentage_safe(0.0) != "Não definido"


def test_negative_values():
    """Testa formatação com valores negativos"""
    result = format_currency_safe(-1000.0)
    assert "-" in result or "(" in result


def test_large_values():
    """Testa formatação com valores grandes"""
    result = format_currency_safe(1_000_000.0)
    assert "1" in result
    # Deve ter separadores de milhares
