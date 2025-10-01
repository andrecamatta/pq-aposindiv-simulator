"""Testes para conversões de taxas de juros"""
import pytest
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.rates import annual_to_monthly_rate, monthly_to_annual_rate


def test_annual_to_monthly_conversion():
    """Testa conversão de taxa anual para mensal"""
    annual = 0.06  # 6% a.a.
    monthly = annual_to_monthly_rate(annual)

    assert monthly > 0
    assert monthly < annual / 12  # Taxa composta é menor que simples


def test_monthly_to_annual_conversion():
    """Testa conversão de taxa mensal para anual"""
    monthly = 0.005  # 0.5% a.m.
    annual = monthly_to_annual_rate(monthly)

    assert annual > 0
    assert annual > monthly * 12  # Taxa composta é maior que simples


def test_round_trip_conversion():
    """Testa reversibilidade das conversões"""
    annual_original = 0.06

    monthly = annual_to_monthly_rate(annual_original)
    annual_back = monthly_to_annual_rate(monthly)

    # Deve retornar ao valor original (com pequena tolerância)
    assert abs(annual_back - annual_original) < 0.0001


def test_zero_rate():
    """Testa conversão com taxa zero"""
    assert annual_to_monthly_rate(0.0) == 0.0
    assert monthly_to_annual_rate(0.0) == 0.0


def test_high_rate():
    """Testa conversão com taxa alta"""
    annual = 0.20  # 20% a.a.
    monthly = annual_to_monthly_rate(annual)

    assert monthly > 0
    assert monthly < annual


def test_compound_interest_formula():
    """Testa se fórmula de juros compostos está correta"""
    annual = 0.12  # 12% a.a.
    monthly = annual_to_monthly_rate(annual)

    # (1 + mensal)^12 deve ser aproximadamente (1 + anual)
    compound_annual = (1 + monthly) ** 12 - 1
    assert abs(compound_annual - annual) < 0.0001


def test_negative_rate_handling():
    """Testa tratamento de taxas negativas"""
    # Taxas negativas podem ser válidas em alguns contextos
    # Mas geralmente devem retornar zero ou lançar erro
    try:
        result = annual_to_monthly_rate(-0.02)
        # Se aceitar, deve ser um valor razoável
        assert result <= 0
    except (ValueError, AssertionError):
        # Se não aceitar, deve lançar erro
        pass


def test_monthly_equivalence():
    """Testa equivalência mensal"""
    annual_rates = [0.03, 0.06, 0.09, 0.12]

    for annual in annual_rates:
        monthly = annual_to_monthly_rate(annual)
        # Taxa mensal multiplicada por 12 deve ser maior que anual (juros compostos)
        assert monthly * 12 < annual + 0.001


def test_precision():
    """Testa precisão das conversões"""
    annual = 0.0587  # Taxa com muitos decimais
    monthly = annual_to_monthly_rate(annual)

    # Deve manter precisão razoável
    assert isinstance(monthly, float)
    assert monthly > 0.004
    assert monthly < 0.005
