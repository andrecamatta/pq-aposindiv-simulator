"""Testes unitários para SuggestionsEngine - Atualizado para nova interface"""
import pytest
import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.suggestions_engine import SuggestionsEngine
from src.core.actuarial_engine import ActuarialEngine
from src.models.participant import SimulatorState
from src.models.suggestions import SuggestionsRequest, SuggestionsResponse, Suggestion


class TestSuggestionsEngine:
    """Testes para a classe SuggestionsEngine"""

    @pytest.fixture
    def base_bd_state(self):
        """Estado base para testes BD"""
        return SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            retirement_age=65,
            contribution_rate=10.0,
            target_benefit=3000.0,
            benefit_target_mode="VALUE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            accrual_rate=5.0,
            salary_growth_real=0.02,
            projection_years=40,
            calculation_method="PUC",
            plan_type="BD"
        )

    @pytest.fixture
    def deficit_bd_state(self):
        """Estado BD com déficit para gerar sugestões"""
        return SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            retirement_age=65,
            contribution_rate=5.0,  # Baixa contribuição = déficit
            target_benefit=4000.0,  # Alto benefício
            benefit_target_mode="VALUE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            accrual_rate=5.0,
            salary_growth_real=0.02,
            projection_years=40,
            calculation_method="PUC",
            plan_type="BD"
        )

    @pytest.fixture
    def base_cd_state(self):
        """Estado base para testes CD com renda vitalícia"""
        return SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            retirement_age=60,
            contribution_rate=12.0,
            initial_balance=10000.0,
            target_benefit=3500.0,
            benefit_target_mode="VALUE",
            mortality_table="AT_2000",
            discount_rate=0.05,
            accrual_rate=0.04,
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="CD",
            plan_type="CD",
            cd_conversion_mode="ACTUARIAL"  # Renda vitalícia
        )

    @pytest.fixture
    def suggestions_engine(self):
        """Engine de sugestões"""
        actuarial_engine = ActuarialEngine()
        return SuggestionsEngine(actuarial_engine)

    def test_engine_initialization(self, suggestions_engine):
        """Testa inicialização do engine"""
        assert suggestions_engine is not None
        assert hasattr(suggestions_engine, 'generate_suggestions')
        assert suggestions_engine.actuarial_engine is not None

    def test_generate_suggestions_bd_with_deficit(self, suggestions_engine, deficit_bd_state):
        """Testa geração de sugestões para BD com déficit"""
        request = SuggestionsRequest(
            state=deficit_bd_state,
            max_suggestions=5
        )

        response = suggestions_engine.generate_suggestions(request)

        # Verifica tipo do resultado
        assert isinstance(response, SuggestionsResponse)
        assert isinstance(response.suggestions, list)
        assert isinstance(response.context, dict)
        assert response.computation_time_ms > 0

        # Deve ter sugestões para cenário com déficit
        assert len(response.suggestions) > 0

        # Verifica estrutura das sugestões
        for suggestion in response.suggestions:
            assert isinstance(suggestion, Suggestion)
            assert suggestion.id
            assert suggestion.title
            assert suggestion.description
            assert suggestion.action
            assert suggestion.action_label
            assert suggestion.priority in [1, 2, 3]
            assert 0 <= suggestion.confidence <= 1

    def test_generate_suggestions_bd_balanced(self, suggestions_engine, base_bd_state):
        """Testa geração de sugestões para BD equilibrado"""
        request = SuggestionsRequest(
            state=base_bd_state,
            max_suggestions=3
        )

        response = suggestions_engine.generate_suggestions(request)

        # Deve retornar mesmo para cenário equilibrado
        assert isinstance(response, SuggestionsResponse)
        assert isinstance(response.suggestions, list)

        # Pode ter ou não sugestões, mas deve ter contexto
        assert "is_bd" in response.context
        assert response.context["is_bd"] is True

    def test_generate_suggestions_cd_actuarial(self, suggestions_engine, base_cd_state):
        """Testa geração de sugestões para CD com renda vitalícia"""
        request = SuggestionsRequest(
            state=base_cd_state,
            max_suggestions=5
        )

        response = suggestions_engine.generate_suggestions(request)

        # Verifica estrutura
        assert isinstance(response, SuggestionsResponse)
        assert isinstance(response.suggestions, list)

        # CD com renda vitalícia deve ser suportado
        assert "is_cd" in response.context
        assert response.context.get("is_supported", True) is True

        # Pode ter sugestões específicas para CD
        if response.suggestions:
            for suggestion in response.suggestions:
                assert isinstance(suggestion, Suggestion)

    def test_unsupported_plan_configuration(self, suggestions_engine):
        """Testa configuração de plano não suportada"""
        # CD com modo PERCENTAGE (não vitalício)
        cd_saldo_state = SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            retirement_age=60,
            contribution_rate=12.0,
            initial_balance=10000.0,
            accrual_rate=0.04,
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="CD",
            mortality_table="AT_2000",
            discount_rate=0.05,
            plan_type="CD",
            cd_conversion_mode="PERCENTAGE"  # Não suportado para sugestões
        )

        request = SuggestionsRequest(
            state=cd_saldo_state,
            max_suggestions=3
        )

        response = suggestions_engine.generate_suggestions(request)

        # Não deve gerar sugestões
        assert len(response.suggestions) == 0
        assert response.context.get("is_supported") is False
        assert "unsupported_reason" in response.context

    def test_suggestion_types_bd_deficit(self, suggestions_engine, deficit_bd_state):
        """Testa tipos de sugestões geradas para BD com déficit"""
        request = SuggestionsRequest(
            state=deficit_bd_state,
            max_suggestions=10
        )

        response = suggestions_engine.generate_suggestions(request)

        # Coleta tipos de sugestões
        suggestion_types = {s.type for s in response.suggestions}

        # Deve ter pelo menos algumas sugestões
        assert len(suggestion_types) >= 1

    def test_suggestion_action_values(self, suggestions_engine, deficit_bd_state):
        """Testa valores de ação das sugestões"""
        request = SuggestionsRequest(
            state=deficit_bd_state,
            max_suggestions=5
        )

        response = suggestions_engine.generate_suggestions(request)

        for suggestion in response.suggestions:
            # Se tem action_value, deve ser numérico
            if suggestion.action_value is not None:
                assert isinstance(suggestion.action_value, (int, float))
                assert suggestion.action_value > 0

            # Se tem action_values (múltiplos), deve ser dicionário
            if suggestion.action_values is not None:
                assert isinstance(suggestion.action_values, dict)
                for key, value in suggestion.action_values.items():
                    assert isinstance(value, (int, float))

    def test_suggestion_priorities(self, suggestions_engine, deficit_bd_state):
        """Testa priorização das sugestões"""
        request = SuggestionsRequest(
            state=deficit_bd_state,
            max_suggestions=5
        )

        response = suggestions_engine.generate_suggestions(request)

        if len(response.suggestions) > 1:
            # Primeira sugestão deve ter prioridade alta (1 ou 2)
            assert response.suggestions[0].priority in [1, 2]

            # Todas as prioridades devem ser válidas
            for suggestion in response.suggestions:
                assert suggestion.priority in [1, 2, 3]

    def test_suggestion_confidence(self, suggestions_engine, base_bd_state):
        """Testa confiança das sugestões"""
        request = SuggestionsRequest(
            state=base_bd_state,
            max_suggestions=5
        )

        response = suggestions_engine.generate_suggestions(request)

        for suggestion in response.suggestions:
            # Confiança deve estar entre 0 e 1
            assert 0 <= suggestion.confidence <= 1
            # Sugestões devem ter confiança razoável (> 0.3)
            assert suggestion.confidence > 0.3

    def test_context_information(self, suggestions_engine, deficit_bd_state):
        """Testa informações de contexto retornadas"""
        request = SuggestionsRequest(
            state=deficit_bd_state,
            max_suggestions=3
        )

        response = suggestions_engine.generate_suggestions(request)

        # Contexto deve conter informações essenciais
        assert "is_bd" in response.context or "is_cd" in response.context
        assert "plan_type" in response.context
        assert "benefit_target_mode" in response.context

    def test_max_suggestions_limit(self, suggestions_engine, deficit_bd_state):
        """Testa limite de número de sugestões"""
        request = SuggestionsRequest(
            state=deficit_bd_state,
            max_suggestions=2
        )

        response = suggestions_engine.generate_suggestions(request)

        # Não deve retornar mais que o limite
        assert len(response.suggestions) <= 2

    def test_replacement_rate_mode_bd(self, suggestions_engine):
        """Testa sugestões para modo taxa de reposição"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            retirement_age=65,
            contribution_rate=8.0,
            target_replacement_rate=0.8,  # 80%
            benefit_target_mode="REPLACEMENT_RATE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            accrual_rate=5.0,
            salary_growth_real=0.02,
            projection_years=40,
            calculation_method="PUC",
            plan_type="BD"
        )

        request = SuggestionsRequest(
            state=state,
            max_suggestions=5
        )

        response = suggestions_engine.generate_suggestions(request)

        # Deve funcionar para modo taxa de reposição
        assert isinstance(response, SuggestionsResponse)
        mode = str(response.context["benefit_target_mode"])
        # Deve conter REPLACEMENT_RATE na representação
        assert "REPLACEMENT_RATE" in mode

    def test_computation_time_reasonable(self, suggestions_engine, base_bd_state):
        """Testa se tempo de computação é razoável"""
        request = SuggestionsRequest(
            state=base_bd_state,
            max_suggestions=3
        )

        response = suggestions_engine.generate_suggestions(request)

        # Tempo deve ser positivo e razoável (< 5 segundos)
        assert response.computation_time_ms > 0
        assert response.computation_time_ms < 5000

    def test_suggestion_uniqueness(self, suggestions_engine, deficit_bd_state):
        """Testa se sugestões têm IDs únicos"""
        request = SuggestionsRequest(
            state=deficit_bd_state,
            max_suggestions=5
        )

        response = suggestions_engine.generate_suggestions(request)

        if len(response.suggestions) > 1:
            suggestion_ids = [s.id for s in response.suggestions]
            unique_ids = set(suggestion_ids)

            # Todos os IDs devem ser únicos
            assert len(suggestion_ids) == len(unique_ids)

    def test_consistency_multiple_calls(self, suggestions_engine, base_bd_state):
        """Testa consistência em múltiplas chamadas"""
        request = SuggestionsRequest(
            state=base_bd_state,
            max_suggestions=3
        )

        response1 = suggestions_engine.generate_suggestions(request)
        response2 = suggestions_engine.generate_suggestions(request)

        # Número de sugestões deve ser consistente
        assert len(response1.suggestions) == len(response2.suggestions)

        # Tipos de sugestões devem ser os mesmos
        types1 = [s.type for s in response1.suggestions]
        types2 = [s.type for s in response2.suggestions]
        assert types1 == types2
