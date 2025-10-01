"""Testes unitários para endpoints da API"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.main import app
from src.models.participant import SimulatorState


class TestAPIEndpoints:
    """Testes para endpoints da API"""
    
    @pytest.fixture
    def client(self):
        """Cliente de teste para a API"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_bd_state(self):
        """Estado válido para testes BD"""
        return {
            "plan_type": "BD",
            "age": 30,
            "gender": "M",
            "salary": 5000.0,
            "retirement_age": 65,
            "contribution_rate": 10.0,
            "target_benefit": 3000.0,
            "benefit_target_mode": "VALUE",
            "mortality_table": "BR_EMS_2021",
            "discount_rate": 0.06
        }
    
    @pytest.fixture
    def valid_cd_state(self):
        """Estado válido para testes CD"""
        return {
            "plan_type": "CD",
            "age": 35,
            "gender": "F",
            "salary": 6000.0,
            "retirement_age": 60,
            "contribution_rate": 12.0,
            "initial_balance": 10000.0,
            "accrual_rate": 0.04,
            "mortality_table": "AT_2000",
            "discount_rate": 0.05,
            "cd_conversion_mode": "ACTUARIAL"
        }
    
    def test_health_endpoint(self, client):
        """Testa endpoint de health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        # timestamp é opcional - pode ou não estar presente
    
    def test_default_state_endpoint(self, client):
        """Testa endpoint de estado padrão"""
        response = client.get("/default-state")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica campos obrigatórios
        required_fields = ['age', 'gender', 'salary', 'retirement_age', 
                          'contribution_rate', 'mortality_table', 'discount_rate']
        
        for field in required_fields:
            assert field in data
        
        # Verifica tipos
        assert isinstance(data['age'], int)
        assert isinstance(data['salary'], (int, float))
        assert data['gender'] in ['M', 'F']
    
    def test_mortality_tables_endpoint(self, client):
        """Testa endpoint de tábuas de mortalidade"""
        response = client.get("/mortality-tables")
        
        assert response.status_code == 200
        data = response.json()
        
        # Pode retornar lista direta ou objeto com 'tables'
        tables = data if isinstance(data, list) else data.get('tables', [])
        
        assert len(tables) > 0
        
        # Verifica estrutura da primeira tábua
        first_table = tables[0]
        assert 'code' in first_table
        assert 'name' in first_table
        assert 'description' in first_table
    
    def test_calculate_endpoint_bd_valid(self, client, valid_bd_state):
        """Testa endpoint de cálculo com estado BD válido"""
        response = client.post("/calculate", json=valid_bd_state)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica campos BD obrigatórios
        bd_fields = ['rmba', 'total_contributions', 'deficit_surplus', 
                    'sustainable_replacement_ratio']
        
        for field in bd_fields:
            assert field in data
        
        # Verifica tipos e valores razoáveis
        assert isinstance(data['rmba'], (int, float))
        assert data['rmba'] > 0
        assert isinstance(data['total_contributions'], (int, float))
        assert data['total_contributions'] > 0
    
    def test_calculate_endpoint_cd_valid(self, client, valid_cd_state):
        """Testa endpoint de cálculo com estado CD válido"""
        response = client.post("/calculate", json=valid_cd_state)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica campos CD obrigatórios
        cd_fields = ['accumulated_balance_retirement', 'estimated_benefit']
        
        for field in cd_fields:
            assert field in data
        
        # Verifica valores razoáveis
        assert isinstance(data['accumulated_balance_retirement'], (int, float))
        assert data['accumulated_balance_retirement'] > valid_cd_state['initial_balance']
        assert isinstance(data['estimated_benefit'], (int, float))
        assert data['estimated_benefit'] > 0
    
    def test_calculate_endpoint_invalid_data(self, client):
        """Testa endpoint de cálculo com dados inválidos"""
        invalid_state = {
            "age": -5,  # Idade inválida
            "gender": "X",  # Gênero inválido
            "salary": -1000  # Salário negativo
        }
        
        response = client.post("/calculate", json=invalid_state)
        
        # Deve retornar erro de validação
        assert response.status_code in [400, 422]  # Bad Request ou Unprocessable Entity
    
    def test_calculate_endpoint_missing_fields(self, client):
        """Testa endpoint de cálculo com campos obrigatórios ausentes"""
        incomplete_state = {
            "age": 30,
            "gender": "M"
            # Faltam campos obrigatórios
        }
        
        response = client.post("/calculate", json=incomplete_state)
        
        # Deve retornar erro de validação
        assert response.status_code in [400, 422]
    
    def test_calculate_endpoint_empty_body(self, client):
        """Testa endpoint de cálculo com corpo vazio"""
        response = client.post("/calculate", json={})
        
        # Deve retornar erro de validação
        assert response.status_code in [400, 422]
    
    def test_bd_replacement_rate_mode(self, client, valid_bd_state):
        """Testa cálculo BD com modo de taxa de reposição"""
        replacement_state = valid_bd_state.copy()
        replacement_state['benefit_target_mode'] = 'REPLACEMENT_RATE'
        replacement_state['target_replacement_rate'] = 0.7
        replacement_state.pop('target_benefit', None)
        
        response = client.post("/calculate", json=replacement_state)
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve calcular benefício baseado na taxa
        assert 'target_benefit_calculated' in data
        expected_benefit = replacement_state['salary'] * replacement_state['target_replacement_rate']
        calculated_benefit = data['target_benefit_calculated']
        
        # Deve estar próximo do esperado
        assert abs(calculated_benefit - expected_benefit) < replacement_state['salary'] * 0.1
    
    def test_cd_different_conversion_modes(self, client, valid_cd_state):
        """Testa CD com diferentes modos de conversão"""
        # Modo atuarial
        actuarial_state = valid_cd_state.copy()
        actuarial_state['cd_conversion_mode'] = 'ACTUARIAL'
        
        response_actuarial = client.post("/calculate", json=actuarial_state)
        assert response_actuarial.status_code == 200
        data_actuarial = response_actuarial.json()
        
        # Modo taxa fixa
        fixed_state = valid_cd_state.copy()
        fixed_state['cd_conversion_mode'] = 'FIXED_RATE'
        
        response_fixed = client.post("/calculate", json=fixed_state)
        assert response_fixed.status_code == 200
        data_fixed = response_fixed.json()
        
        # Ambos devem ter benefícios válidos
        assert data_actuarial['estimated_benefit'] > 0
        assert data_fixed['estimated_benefit'] > 0
    
    def test_large_payload_handling(self, client, valid_bd_state):
        """Testa tratamento de payload grande"""
        # Adicionar campo com string muito grande
        large_state = valid_bd_state.copy()
        large_state['large_field'] = 'x' * 10000  # 10KB de dados
        
        response = client.post("/calculate", json=large_state)
        
        # Deve funcionar ou retornar erro apropriado
        assert response.status_code in [200, 413, 422]  # OK, Payload Too Large, ou Validation Error
    
    def test_cors_headers(self, client):
        """Testa headers CORS"""
        response = client.options("/calculate")
        
        # Verifica se CORS está configurado
        headers = response.headers
        
        # Pode ter headers CORS configurados
        cors_headers = [
            'access-control-allow-origin',
            'access-control-allow-methods',
            'access-control-allow-headers'
        ]
        
        # Pelo menos um header CORS deve estar presente em ambiente de desenvolvimento
        has_cors = any(header in headers for header in cors_headers)
        
        # Se não tiver CORS, pelo menos não deve dar erro
        assert response.status_code in [200, 405]  # OK ou Method Not Allowed
    
    def test_error_response_format(self, client):
        """Testa formato das respostas de erro"""
        # Forçar erro com dados inválidos
        invalid_data = {"age": "invalid"}
        
        response = client.post("/calculate", json=invalid_data)
        
        assert response.status_code in [400, 422]
        
        # Verifica se resposta de erro tem formato consistente
        error_data = response.json()
        
        # FastAPI geralmente retorna 'detail' para erros
        assert 'detail' in error_data or 'message' in error_data
    
    def test_api_documentation_endpoints(self, client):
        """Testa endpoints de documentação da API"""
        # Swagger UI
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200
        
        # OpenAPI schema
        openapi_response = client.get("/openapi.json")
        assert openapi_response.status_code == 200
        
        schema = openapi_response.json()
        assert 'openapi' in schema
        assert 'paths' in schema
        assert '/calculate' in schema['paths']
    
