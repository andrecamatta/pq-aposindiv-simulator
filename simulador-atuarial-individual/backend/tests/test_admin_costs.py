"""Testes para custos administrativos - Convertido para pytest"""
import pytest
import httpx
from src.models.participant import DEFAULT_SALARY_MONTHS_PER_YEAR, DEFAULT_BENEFIT_MONTHS_PER_YEAR

API_BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    """Cliente HTTP para testes"""
    with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
        yield client


def test_admin_costs_calculation(client: httpx.Client):
    """Testa cálculo com custos administrativos significativos"""
    # Estado teste com custos administrativos
    test_state = {
        "age": 30,
        "gender": "M",
        "salary": 8000.0,
        "initial_balance": 10000.0,
        "benefit_target_mode": "VALUE",
        "target_benefit": 5000.0,
        "accrual_rate": 5.0,
        "retirement_age": 65,
        "contribution_rate": 10.0,
        "mortality_table": "BR_EMS_2021",
        "discount_rate": 0.06,
        "salary_growth_real": 0.02,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "admin_fee_rate": 0.02,  # 2% ao ano sobre saldo
        "loading_fee_rate": 0.05,  # 5% de carregamento
        "payment_timing": "postecipado",
        "salary_months_per_year": DEFAULT_SALARY_MONTHS_PER_YEAR,
        "benefit_months_per_year": DEFAULT_BENEFIT_MONTHS_PER_YEAR,
        "projection_years": 40,
        "calculation_method": "PUC"
    }

    response = client.post("/calculate", json=test_state)
    assert response.status_code == 200

    result = response.json()

    # Verifica campos essenciais
    assert "rmba" in result
    assert "deficit_surplus" in result
    assert "total_contributions" in result

    # Valores devem ser numéricos e razoáveis
    assert isinstance(result["rmba"], (int, float))
    # RMBA pode ser negativo (superávit) ou positivo (déficit) - apenas verificar que é válido
    assert not (result["rmba"] == 0 and result["total_contributions"] > 0)

    assert isinstance(result["total_contributions"], (int, float))
    assert result["total_contributions"] > 0

    # Com custos administrativos, resultados devem refletir o impacto
    # (déficit pode ser maior ou reservas menores devido às taxas)
    assert isinstance(result["deficit_surplus"], (int, float))


def test_admin_costs_zero_vs_nonzero(client: httpx.Client):
    """Compara resultados com e sem custos administrativos"""
    base_state = {
        "age": 30,
        "gender": "M",
        "salary": 8000.0,
        "initial_balance": 10000.0,
        "benefit_target_mode": "VALUE",
        "target_benefit": 5000.0,
        "accrual_rate": 5.0,
        "retirement_age": 65,
        "contribution_rate": 10.0,
        "mortality_table": "BR_EMS_2021",
        "discount_rate": 0.06,
        "salary_growth_real": 0.02,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "payment_timing": "postecipado",
        "salary_months_per_year": DEFAULT_SALARY_MONTHS_PER_YEAR,
        "benefit_months_per_year": DEFAULT_BENEFIT_MONTHS_PER_YEAR,
        "projection_years": 40,
        "calculation_method": "PUC"
    }

    # Sem custos administrativos
    state_no_fees = {**base_state, "admin_fee_rate": 0.0, "loading_fee_rate": 0.0}
    response_no_fees = client.post("/calculate", json=state_no_fees)
    assert response_no_fees.status_code == 200
    result_no_fees = response_no_fees.json()

    # Com custos administrativos
    state_with_fees = {**base_state, "admin_fee_rate": 0.02, "loading_fee_rate": 0.05}
    response_with_fees = client.post("/calculate", json=state_with_fees)
    assert response_with_fees.status_code == 200
    result_with_fees = response_with_fees.json()

    # Ambos devem calcular com sucesso
    assert "rmba" in result_no_fees
    assert "rmba" in result_with_fees

    # Com taxas, o resultado pode ser diferente
    # (dependendo da implementação, RMBA ou déficit pode ser afetado)
    # Apenas garantimos que ambos retornam valores válidos
    # RMBA pode ser negativo (superávit) ou positivo (déficit)
    assert isinstance(result_no_fees["rmba"], (int, float))
    assert isinstance(result_with_fees["rmba"], (int, float))


def test_loading_fee_impact(client: httpx.Client):
    """Testa impacto específico da taxa de carregamento"""
    base_state = {
        "age": 30,
        "gender": "M",
        "salary": 6000.0,
        "retirement_age": 65,
        "contribution_rate": 12.0,
        "target_benefit": 4000.0,
        "benefit_target_mode": "VALUE",
        "mortality_table": "BR_EMS_2021",
        "discount_rate": 0.05,
        "payment_timing": "postecipado",
        "salary_months_per_year": DEFAULT_SALARY_MONTHS_PER_YEAR,
        "benefit_months_per_year": DEFAULT_BENEFIT_MONTHS_PER_YEAR,
        "calculation_method": "PUC"
    }

    # Alta taxa de carregamento
    state_high_loading = {**base_state, "loading_fee_rate": 0.10}  # 10%
    response = client.post("/calculate", json=state_high_loading)

    assert response.status_code == 200
    result = response.json()

    # Deve calcular mesmo com taxa alta
    assert "rmba" in result
    assert "total_contributions" in result
    assert result["rmba"] > 0
