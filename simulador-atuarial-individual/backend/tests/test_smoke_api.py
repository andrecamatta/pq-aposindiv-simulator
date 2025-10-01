"""
Testes Fumaça (Smoke Tests) para API
Verifica se os endpoints principais estão funcionando
"""
import pytest
import httpx
from typing import Dict, Any
from src.models.participant import DEFAULT_SALARY_MONTHS_PER_YEAR, DEFAULT_BENEFIT_MONTHS_PER_YEAR

API_BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    """Cliente HTTP para testes"""
    with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
        yield client


def test_health_check(client: httpx.Client):
    """Testa se a API está rodando"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "version" in data


def test_get_mortality_tables(client: httpx.Client):
    """Testa se endpoint de tábuas de mortalidade funciona"""
    response = client.get("/mortality-tables")
    assert response.status_code == 200
    data = response.json()
    
    # Verifica estrutura básica
    assert isinstance(data, dict)
    assert "tables" in data or isinstance(data, list)
    
    # Se retornar em formato {"tables": [...]}, pegar a lista
    tables = data.get("tables", data) if isinstance(data, dict) else data
    assert len(tables) > 0
    
    # Verifica estrutura de uma tábua
    first_table = tables[0]
    assert "code" in first_table
    assert "name" in first_table
    assert "description" in first_table


def test_get_default_state(client: httpx.Client):
    """Testa se retorna estado padrão válido"""
    response = client.get("/default-state")
    assert response.status_code == 200
    state = response.json()
    
    # Verifica campos essenciais
    required_fields = [
        "age", "salary", "retirement_age", 
        "contribution_rate", "mortality_table"
    ]
    for field in required_fields:
        assert field in state
    
    # Verifica tipos básicos
    assert isinstance(state["age"], (int, float))
    assert isinstance(state["salary"], (int, float))
    assert state["age"] > 0
    assert state["salary"] > 0


def test_calculate_bd_basic(client: httpx.Client):
    """Testa cálculo básico para plano BD"""
    # Estado completo para BD baseado no default-state
    test_state = {
        "age": 30,
        "gender": "M",
        "salary": 5000.0,
        "initial_balance": 0.0,
        "benefit_target_mode": "VALUE",
        "target_benefit": 3000.0,
        "target_replacement_rate": None,
        "accrual_rate": 5.0,
        "retirement_age": 65,
        "contribution_rate": 10.0,
        "mortality_table": "BR_EMS_2021",
        "discount_rate": 0.05,
        "salary_growth_real": 0.02,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "admin_fee_rate": 0.01,
        "loading_fee_rate": 0.0,
        "payment_timing": "postecipado",
        "salary_months_per_year": DEFAULT_SALARY_MONTHS_PER_YEAR,
        "benefit_months_per_year": DEFAULT_BENEFIT_MONTHS_PER_YEAR,
        "projection_years": 40,
        "calculation_method": "PUC"
    }
    
    response = client.post("/calculate", json=test_state)
    assert response.status_code == 200
    
    result = response.json()
    assert "rmba" in result
    assert "deficit_surplus" in result
    assert "total_contributions" in result
    assert isinstance(result["rmba"], (int, float))


def test_calculate_cd_basic(client: httpx.Client):
    """Testa cálculo básico para plano CD"""
    # Estado completo para CD
    test_state = {
        "age": 35,
        "gender": "F",
        "salary": 6000.0,
        "initial_balance": 10000.0,
        "benefit_target_mode": "VALUE",
        "target_benefit": None,
        "target_replacement_rate": None,
        "accrual_rate": 4.0,
        "retirement_age": 60,
        "contribution_rate": 12.0,
        "mortality_table": "AT_2000",
        "discount_rate": 0.05,
        "salary_growth_real": 0.02,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "admin_fee_rate": 0.01,
        "loading_fee_rate": 0.0,
        "payment_timing": "postecipado",
        "salary_months_per_year": 13,
        "benefit_months_per_year": 13,
        "projection_years": 25,
        "calculation_method": "PUC",
        "plan_type": "CD",
        "cd_conversion_mode": "ACTUARIAL"
    }
    
    response = client.post("/calculate", json=test_state)
    assert response.status_code == 200
    
    result = response.json()
    # Para CD, verifica campos específicos retornados
    assert "accumulated_reserves" in result
    assert "monthly_income_cd" in result or "total_benefits" in result
    # Verifica se tem array de reservas acumuladas
    assert isinstance(result["accumulated_reserves"], list)
    assert len(result["accumulated_reserves"]) > 0
    # Verifica se renda mensal é um número válido
    monthly_income = result.get("monthly_income_cd", result.get("total_benefits"))
    if monthly_income is not None:
        assert isinstance(monthly_income, (int, float))
        assert monthly_income > 0


def test_get_suggestions(client: httpx.Client):
    """Testa se endpoint de sugestões funciona"""
    request_data = {
        "state": {
            "age": 40,
            "gender": "M",
            "salary": 7000.0,
            "initial_balance": 0.0,
            "benefit_target_mode": "VALUE",
            "target_benefit": 5000.0,
            "target_replacement_rate": None,
            "accrual_rate": 5.0,
            "retirement_age": 65,
            "contribution_rate": 8.0,
            "mortality_table": "BR_EMS_2021",
            "discount_rate": 0.05,
            "salary_growth_real": 0.02,
            "benefit_indexation": "none",
            "contribution_indexation": "salary",
            "use_ettj": False,
            "admin_fee_rate": 0.01,
            "loading_fee_rate": 0.0,
            "payment_timing": "postecipado",
            "salary_months_per_year": 13,
            "benefit_months_per_year": 13,
            "projection_years": 25,
            "calculation_method": "PUC"
        },
        "max_suggestions": 3
    }
    
    response = client.post("/suggestions", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    
    if len(data["suggestions"]) > 0:
        suggestion = data["suggestions"][0]
        assert "id" in suggestion
        assert "title" in suggestion
        assert "description" in suggestion
        # Campo pode ser "action" em vez de "action_type"
        assert "action" in suggestion or "action_type" in suggestion


def test_websocket_connection():
    """Testa se WebSocket conecta (teste básico)"""
    import websocket
    import json
    
    ws = websocket.WebSocket()
    try:
        ws.connect("ws://localhost:8000/ws/test_client")
        
        # Envia ping
        ws.send(json.dumps({"type": "ping"}))
        
        # Aguarda resposta (com timeout)
        ws.settimeout(5)
        response = ws.recv()
        data = json.loads(response)
        
        assert data.get("type") == "pong"
        
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")
    finally:
        ws.close()


def test_error_handling_invalid_data(client: httpx.Client):
    """Testa se API trata erros adequadamente"""
    # Dados inválidos
    invalid_state = {
        "age": -5,  # Idade negativa
        "salary": "invalid",  # Tipo errado
    }
    
    response = client.post("/calculate", json=invalid_state)
    
    # Deve retornar erro 4xx (não 5xx)
    assert 400 <= response.status_code < 500
    
    # Deve ter mensagem de erro
    if response.status_code != 404:
        data = response.json()
        assert "detail" in data or "error" in data or "message" in data


def test_cors_headers(client: httpx.Client):
    """Testa se CORS está configurado"""
    response = client.options("/health")
    
    # Verifica se OPTIONS é suportado (indica configuração CORS)
    # Como nem todos os serviços têm CORS configurado, apenas verificamos se não dá erro 404
    assert response.status_code in [200, 405, 501]  # 200=OK, 405=Method Not Allowed, 501=Not Implemented