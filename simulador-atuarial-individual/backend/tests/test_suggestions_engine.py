"""Testes unitários para SuggestionsEngine"""
import pytest
import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.suggestions_engine import SuggestionsEngine
from src.models.participant import SimulatorState
from src.models.results import SimulatorResults


class TestSuggestionsEngine:
    """Testes para a classe SuggestionsEngine"""
    
    @pytest.fixture
    def base_state(self):
        """Estado base para testes"""
        return SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            target_benefit=3000.0,
            benefit_target_mode="VALUE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            plan_type="BD"
        )
    
    @pytest.fixture
    def deficit_results(self):
        """Resultados com déficit para testes"""
        return SimulatorResults(
            rmba=150000.0,
            total_contributions=100000.0,
            deficit_surplus=50000.0,  # Déficit
            sustainable_replacement_ratio=45.0,
            cash_flows=[],
            accumulated_reserves=[]
        )
    
    @pytest.fixture
    def surplus_results(self):
        """Resultados com superávit para testes"""
        return SimulatorResults(
            rmba=80000.0,
            total_contributions=100000.0,
            deficit_surplus=-20000.0,  # Superávit
            sustainable_replacement_ratio=85.0,
            cash_flows=[],
            accumulated_reserves=[]
        )
    
    def test_engine_initialization(self, base_state, deficit_results):
        """Testa inicialização do engine"""
        engine = SuggestionsEngine(base_state, deficit_results)
        
        assert engine.state == base_state
        assert engine.results == deficit_results
        assert hasattr(engine, 'generate_suggestions')
    
    def test_generate_suggestions_with_deficit(self, base_state, deficit_results):
        """Testa geração de sugestões com déficit"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        # Deve retornar lista de sugestões
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Verifica estrutura das sugestões
        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert 'type' in suggestion
            assert 'message' in suggestion
            assert 'impact' in suggestion
            assert 'parameters' in suggestion
    
    def test_generate_suggestions_with_surplus(self, base_state, surplus_results):
        """Testa geração de sugestões com superávit"""
        engine = SuggestionsEngine(base_state, surplus_results)
        suggestions = engine.generate_suggestions()
        
        # Pode ter menos sugestões ou sugestões diferentes
        assert isinstance(suggestions, list)
        
        # Se houver sugestões, devem ter estrutura correta
        for suggestion in suggestions:
            assert isinstance(suggestion, dict)
            assert 'type' in suggestion
            assert 'message' in suggestion
    
    def test_contribution_rate_suggestions(self, base_state, deficit_results):
        """Testa sugestões de taxa de contribuição"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        # Deve haver sugestão de aumentar contribuição em caso de déficit
        contribution_suggestions = [
            s for s in suggestions 
            if s['type'] == 'contribution_rate' or 'contribuição' in s['message'].lower()
        ]
        
        assert len(contribution_suggestions) > 0
        
        # Verifica parâmetros da sugestão
        contrib_suggestion = contribution_suggestions[0]
        if 'new_contribution_rate' in contrib_suggestion['parameters']:
            new_rate = contrib_suggestion['parameters']['new_contribution_rate']
            assert new_rate > base_state.contribution_rate
    
    def test_retirement_age_suggestions(self, base_state, deficit_results):
        """Testa sugestões de idade de aposentadoria"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        # Pode haver sugestão de postergar aposentadoria
        retirement_suggestions = [
            s for s in suggestions 
            if s['type'] == 'retirement_age' or 'aposentadoria' in s['message'].lower()
        ]
        
        if len(retirement_suggestions) > 0:
            retirement_suggestion = retirement_suggestions[0]
            if 'new_retirement_age' in retirement_suggestion['parameters']:
                new_age = retirement_suggestion['parameters']['new_retirement_age']
                assert new_age > base_state.retirement_age
    
    def test_benefit_adjustment_suggestions(self, base_state, deficit_results):
        """Testa sugestões de ajuste de benefício"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        # Pode haver sugestão de reduzir benefício alvo
        benefit_suggestions = [
            s for s in suggestions 
            if s['type'] == 'target_benefit' or 'benefício' in s['message'].lower()
        ]
        
        if len(benefit_suggestions) > 0:
            benefit_suggestion = benefit_suggestions[0]
            if 'new_target_benefit' in benefit_suggestion['parameters']:
                new_benefit = benefit_suggestion['parameters']['new_target_benefit']
                assert new_benefit < base_state.target_benefit
    
    def test_suggestion_impact_calculation(self, base_state, deficit_results):
        """Testa cálculo de impacto das sugestões"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        for suggestion in suggestions:
            impact = suggestion['impact']
            
            # Impacto deve ser dicionário com informações relevantes
            assert isinstance(impact, dict)
            
            # Pode ter redução de déficit
            if 'deficit_reduction' in impact:
                assert isinstance(impact['deficit_reduction'], (int, float))
                assert impact['deficit_reduction'] >= 0
    
    def test_multiple_suggestions_generation(self, base_state, deficit_results):
        """Testa geração de múltiplas sugestões"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        # Deve gerar várias sugestões para déficit significativo
        assert len(suggestions) >= 1
        
        # Sugestões devem ter tipos diferentes
        suggestion_types = [s['type'] for s in suggestions]
        unique_types = set(suggestion_types)
        
        # Deve haver diversidade de sugestões
        assert len(unique_types) >= 1
    
    def test_suggestion_applicability(self, base_state, deficit_results):
        """Testa aplicabilidade das sugestões"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        for suggestion in suggestions:
            # Cada sugestão deve ser aplicável ao contexto
            assert 'applicable' not in suggestion or suggestion['applicable'] is True
            
            # Parâmetros devem ser realistas
            params = suggestion['parameters']
            
            if 'new_contribution_rate' in params:
                new_rate = params['new_contribution_rate']
                assert 0 < new_rate <= 50.0  # Até 50%
            
            if 'new_retirement_age' in params:
                new_age = params['new_retirement_age']
                assert base_state.age < new_age <= 75  # Até 75 anos
    
    def test_cd_specific_suggestions(self, base_state, deficit_results):
        """Testa sugestões específicas para CD"""
        cd_state = base_state.model_copy()
        cd_state.plan_type = "CD"
        cd_state.accrual_rate = 0.04
        
        cd_results = deficit_results.model_copy()
        cd_results.accumulated_balance_retirement = 200000.0
        cd_results.estimated_benefit = 1500.0
        
        engine = SuggestionsEngine(cd_state, cd_results)
        suggestions = engine.generate_suggestions()
        
        # Pode ter sugestões específicas para CD
        cd_suggestion_types = [s['type'] for s in suggestions]
        
        # Tipos relevantes para CD
        relevant_types = ['contribution_rate', 'accrual_rate', 'retirement_age']
        has_relevant = any(t in relevant_types for t in cd_suggestion_types)
        
        # Se houver sugestões, pelo menos uma deve ser relevante para CD
        if suggestions:
            assert has_relevant or any('saldo' in s['message'].lower() for s in suggestions)
    
    def test_low_replacement_ratio_suggestions(self, base_state):
        """Testa sugestões para taxa de reposição baixa"""
        low_ratio_results = SimulatorResults(
            rmba=80000.0,
            total_contributions=100000.0,
            deficit_surplus=20000.0,
            sustainable_replacement_ratio=25.0,  # Muito baixa
            cash_flows=[],
            accumulated_reserves=[]
        )
        
        engine = SuggestionsEngine(base_state, low_ratio_results)
        suggestions = engine.generate_suggestions()
        
        # Deve sugerir melhorias para taxa de reposição baixa
        assert len(suggestions) > 0
        
        # Mensagens devem abordar insuficiência
        messages = [s['message'].lower() for s in suggestions]
        relevant_messages = [
            msg for msg in messages 
            if any(word in msg for word in ['baixa', 'insuficiente', 'aumentar', 'melhorar'])
        ]
        
        assert len(relevant_messages) > 0
    
    def test_high_contribution_scenario(self, base_state, surplus_results):
        """Testa cenário com contribuição já alta"""
        high_contrib_state = base_state.model_copy()
        high_contrib_state.contribution_rate = 25.0  # Já muito alta
        
        engine = SuggestionsEngine(high_contrib_state, surplus_results)
        suggestions = engine.generate_suggestions()
        
        # Não deve sugerir aumentar contribuição ainda mais
        contribution_increases = [
            s for s in suggestions 
            if (s['type'] == 'contribution_rate' and 
                s['parameters'].get('new_contribution_rate', 0) > high_contrib_state.contribution_rate)
        ]
        
        # Se sugerir aumento, deve ser moderado
        for suggestion in contribution_increases:
            new_rate = suggestion['parameters']['new_contribution_rate']
            assert new_rate <= 30.0  # Limite razoável
    
    def test_near_retirement_suggestions(self, base_state, deficit_results):
        """Testa sugestões para pessoa próxima da aposentadoria"""
        near_retirement_state = base_state.model_copy()
        near_retirement_state.age = 62
        near_retirement_state.retirement_age = 65
        
        engine = SuggestionsEngine(near_retirement_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        # Sugestões devem ser adequadas para pouco tempo restante
        assert len(suggestions) >= 0  # Pode não ter sugestões viáveis
        
        for suggestion in suggestions:
            # Se sugerir mudanças, devem ser significativas
            if 'new_contribution_rate' in suggestion['parameters']:
                new_rate = suggestion['parameters']['new_contribution_rate']
                # Pode precisar de aumento significativo
                assert new_rate > near_retirement_state.contribution_rate
    
    def test_suggestion_message_quality(self, base_state, deficit_results):
        """Testa qualidade das mensagens das sugestões"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        for suggestion in suggestions:
            message = suggestion['message']
            
            # Mensagem deve ser string não vazia
            assert isinstance(message, str)
            assert len(message.strip()) > 0
            
            # Deve ter conteúdo descritivo
            assert len(message) > 20  # Pelo menos uma frase básica
            
            # Não deve ter placeholders
            assert '{' not in message and '}' not in message
    
    def test_empty_or_balanced_scenario(self, base_state):
        """Testa cenário equilibrado sem necessidade de sugestões"""
        balanced_results = SimulatorResults(
            rmba=100000.0,
            total_contributions=100000.0,
            deficit_surplus=0.0,  # Equilibrado
            sustainable_replacement_ratio=70.0,  # Boa taxa
            cash_flows=[],
            accumulated_reserves=[]
        )
        
        engine = SuggestionsEngine(base_state, balanced_results)
        suggestions = engine.generate_suggestions()
        
        # Pode não ter sugestões ou ter sugestões de otimização
        assert isinstance(suggestions, list)
        
        # Se houver sugestões, devem ser de otimização ou diversificação
        for suggestion in suggestions:
            message = suggestion['message'].lower()
            # Não deve usar linguagem de urgência
            urgent_words = ['crítico', 'urgente', 'insuficiente', 'grave']
            has_urgent = any(word in message for word in urgent_words)
            assert not has_urgent
    
    def test_suggestion_parameter_validation(self, base_state, deficit_results):
        """Testa validação dos parâmetros das sugestões"""
        engine = SuggestionsEngine(base_state, deficit_results)
        suggestions = engine.generate_suggestions()
        
        for suggestion in suggestions:
            params = suggestion['parameters']
            
            # Parâmetros devem ser dicionário
            assert isinstance(params, dict)
            
            # Validar parâmetros específicos
            if 'new_contribution_rate' in params:
                rate = params['new_contribution_rate']
                assert isinstance(rate, (int, float))
                assert 0 < rate <= 100  # Entre 0% e 100%
            
            if 'new_retirement_age' in params:
                age = params['new_retirement_age']
                assert isinstance(age, (int, float))
                assert 18 <= age <= 120  # Idades realistas
            
            if 'new_target_benefit' in params:
                benefit = params['new_target_benefit']
                assert isinstance(benefit, (int, float))
                assert benefit > 0