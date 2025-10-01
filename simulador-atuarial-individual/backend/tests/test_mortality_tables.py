"""Testes para carregamento e uso de tábuas de mortalidade"""
import pytest
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.mortality_tables import (
    get_mortality_table,
    get_mortality_table_info,
    validate_mortality_table,
    apply_mortality_aggravation
)
from src.models.participant import Gender


def test_get_available_tables():
    """Testa listagem de tábuas disponíveis"""
    tables = get_mortality_table_info()

    assert isinstance(tables, list)
    assert len(tables) > 0

    # Deve conter tábuas conhecidas
    table_codes = [t["code"] for t in tables]
    assert "BR_EMS_2021" in table_codes or "AT_2000" in table_codes


def test_load_br_ems_2021():
    """Testa carregamento da tábua BR-EMS 2021"""
    table = get_mortality_table("BR_EMS_2021", "M")

    assert table is not None
    assert isinstance(table, np.ndarray)
    assert len(table) > 0

    # Probabilidades devem estar entre 0 e 1
    assert np.all(table >= 0)
    assert np.all(table <= 1)


def test_load_at_2000():
    """Testa carregamento da tábua AT-2000"""
    table = get_mortality_table("AT_2000", "F")

    assert table is not None
    assert isinstance(table, np.ndarray)
    assert len(table) > 0


def test_gender_impact_on_mortality():
    """Testa que gênero afeta probabilidades de mortalidade"""
    table_male = get_mortality_table("BR_EMS_2021", "M")
    table_female = get_mortality_table("BR_EMS_2021", "F")

    # Tábuas devem ser diferentes (mulheres vivem mais)
    assert not np.array_equal(table_male, table_female)

    # Em idades jovens/médias, mortalidade feminina deve ser menor
    # (varia por tábua, mas geralmente é verdade)


def test_mortality_increases_with_age():
    """Testa que mortalidade aumenta com a idade"""
    table = get_mortality_table("BR_EMS_2021", "M")

    # Tomar uma faixa de idades (ex: 30 a 80)
    if len(table) > 80:
        ages_sample = table[30:80]

        # Tendência deve ser crescente (pode ter pequenas flutuações)
        # Verificar se média da segunda metade > média da primeira metade
        first_half = ages_sample[:25]
        second_half = ages_sample[25:]

        assert np.mean(second_half) > np.mean(first_half)


def test_survival_probability_decreases():
    """Testa que probabilidade de sobrevivência diminui com idade"""
    table = get_mortality_table("BR_EMS_2021", "M")

    # Probabilidade de sobrevivência = 1 - qx
    survival_30 = 1 - table[30] if len(table) > 30 else 0.99
    survival_60 = 1 - table[60] if len(table) > 60 else 0.95

    # Deve sobreviver menos aos 60 do que aos 30
    assert survival_60 < survival_30


def test_mortality_aggravation():
    """Testa aplicação de agravamento/suavização"""
    table_base = get_mortality_table("BR_EMS_2021", "M")

    # Agravamento negativo (aumenta mortalidade)
    table_aggravated = apply_mortality_aggravation(table_base, aggravation_pct=-10.0)
    assert np.mean(table_aggravated) > np.mean(table_base), "Agravamento negativo deve aumentar mortalidade"

    # Agravamento positivo (reduz mortalidade/suaviza)
    table_smoothed = apply_mortality_aggravation(table_base, aggravation_pct=10.0)
    assert np.mean(table_smoothed) < np.mean(table_base), "Agravamento positivo deve reduzir mortalidade"


def test_invalid_table_name():
    """Testa erro com nome de tábua inválido"""
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        get_mortality_table("INVALID_TABLE_XYZ", "M")


def test_table_length_reasonable():
    """Testa que tábuas têm tamanho razoável"""
    table = get_mortality_table("BR_EMS_2021", "M")

    # Deve cobrir idades de 0 a pelo menos 100
    assert len(table) >= 100


def test_mortality_at_extreme_ages():
    """Testa mortalidade em idades extremas"""
    table = get_mortality_table("BR_EMS_2021", "M")

    if len(table) > 100:
        # Mortalidade aos 100+ anos deve ser muito alta
        assert table[100] > 0.1  # >10%

        # Mortalidade aos 0-10 anos deve ser baixa (tábuas modernas)
        if table[10] < 1.0:  # Se não é 100% (dado ausente)
            assert table[10] < 0.05  # <5%


def test_different_tables_different_results():
    """Testa que tábuas diferentes produzem resultados diferentes"""
    tables_to_test = ["BR_EMS_2021", "AT_2000"]
    results = []

    for table_name in tables_to_test:
        try:
            table = get_mortality_table(table_name, "M")
            if table is not None:
                # Pegar mortalidade aos 50 anos como referência
                mort_50 = table[50] if len(table) > 50 else None
                results.append((table_name, mort_50))
        except:
            pass

    # Se conseguimos carregar 2 tábuas, devem ser diferentes
    if len(results) >= 2:
        assert results[0][1] != results[1][1]


def test_cache_consistency():
    """Testa que chamadas múltiplas retornam mesmos valores"""
    table1 = get_mortality_table("BR_EMS_2021", "M")
    table2 = get_mortality_table("BR_EMS_2021", "M")

    # Deve retornar a mesma referência ou valores iguais
    assert np.array_equal(table1, table2)
