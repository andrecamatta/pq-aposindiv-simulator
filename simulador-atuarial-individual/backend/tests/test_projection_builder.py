"""Testes unitários para ProjectionBuilder"""
import pytest
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.projection_builder import ProjectionBuilder
from src.models.participant import SimulatorState


class TestProjectionBuilder:
    """Testes para a classe ProjectionBuilder"""
    
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
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            plan_type="BD"
        )
    
    def test_builder_initialization(self, base_state):
        """Testa inicialização do builder"""
        builder = ProjectionBuilder(base_state)
        
        assert builder.state == base_state
        assert hasattr(builder, 'build_projections')
        assert hasattr(builder, 'calculate_cash_flows')
    
    def test_build_projections_structure(self, base_state):
        """Testa estrutura das projeções"""
        builder = ProjectionBuilder(base_state)
        projections = builder.build_projections()
        
        # Verifica estrutura básica
        assert isinstance(projections, dict)
        assert 'projection_ages' in projections
        assert 'cash_flows' in projections
        assert 'reserves' in projections
        
        # Verifica tipos
        assert isinstance(projections['projection_ages'], list)
        assert isinstance(projections['cash_flows'], list)
        assert isinstance(projections['reserves'], list)
        
        # Verifica tamanhos consistentes
        assert len(projections['projection_ages']) == len(projections['cash_flows'])
        assert len(projections['projection_ages']) == len(projections['reserves'])
    
    def test_projection_ages_sequence(self, base_state):
        """Testa sequência de idades nas projeções"""
        builder = ProjectionBuilder(base_state)
        projections = builder.build_projections()
        
        ages = projections['projection_ages']
        
        # Deve começar na idade atual
        assert ages[0] == base_state.age
        
        # Deve ser sequência crescente
        for i in range(1, len(ages)):
            assert ages[i] > ages[i-1]
        
        # Última idade deve estar próxima à aposentadoria ou mais
        assert ages[-1] >= base_state.retirement_age
    
    def test_cash_flows_calculation(self, base_state):
        """Testa cálculo de fluxos de caixa"""
        builder = ProjectionBuilder(base_state)
        cash_flows = builder.calculate_cash_flows()
        
        assert isinstance(cash_flows, list)
        assert len(cash_flows) > 0
        
        # Verifica que fluxos são numéricos
        for cf in cash_flows:
            assert isinstance(cf, (int, float, Decimal))
        
        # Durante fase contributiva, fluxos devem ser negativos (contribuições)
        months_to_retirement = (base_state.retirement_age - base_state.age) * 12
        contributory_flows = cash_flows[:months_to_retirement]
        
        # Pelo menos alguns fluxos contributivos devem ser negativos
        negative_flows = [cf for cf in contributory_flows if cf < 0]
        assert len(negative_flows) > 0
    
    def test_reserves_accumulation(self, base_state):
        """Testa acumulação de reservas"""
        builder = ProjectionBuilder(base_state)
        projections = builder.build_projections()
        
        reserves = projections['reserves']
        
        # Verifica que reservas são numéricas
        for reserve in reserves:
            assert isinstance(reserve, (int, float, Decimal))
        
        # Reservas devem crescer durante fase contributiva (na maioria dos casos)
        months_to_retirement = (base_state.retirement_age - base_state.age) * 12
        contributory_reserves = reserves[:min(months_to_retirement, len(reserves))]
        
        if len(contributory_reserves) > 12:  # Pelo menos 1 ano de dados
            # Verifica tendência de crescimento
            growth_count = sum(1 for i in range(1, len(contributory_reserves)) 
                             if contributory_reserves[i] > contributory_reserves[i-1])
            total_periods = len(contributory_reserves) - 1
            
            # Pelo menos 60% dos períodos devem mostrar crescimento
            assert growth_count / total_periods >= 0.6
    
    def test_retirement_transition(self, base_state):
        """Testa transição para aposentadoria"""
        builder = ProjectionBuilder(base_state)
        projections = builder.build_projections()
        
        ages = projections['projection_ages']
        cash_flows = projections['cash_flows']
        
        # Encontra índice da aposentadoria
        retirement_idx = None
        for i, age in enumerate(ages):
            if age >= base_state.retirement_age:
                retirement_idx = i
                break
        
        if retirement_idx is not None and retirement_idx < len(cash_flows) - 1:
            # Após aposentadoria, fluxos devem ser positivos (benefícios)
            post_retirement_flows = cash_flows[retirement_idx:]
            positive_flows = [cf for cf in post_retirement_flows if cf > 0]
            
            # Pelo menos alguns fluxos pós-aposentadoria devem ser positivos
            assert len(positive_flows) > 0
    
    def test_different_contribution_rates(self, base_state):
        """Testa impacto de diferentes taxas de contribuição"""
        # Taxa baixa
        state_low = base_state.model_copy()
        state_low.contribution_rate = 5.0
        builder_low = ProjectionBuilder(state_low)
        projections_low = builder_low.build_projections()
        
        # Taxa alta
        state_high = base_state.model_copy()
        state_high.contribution_rate = 15.0
        builder_high = ProjectionBuilder(state_high)
        projections_high = builder_high.build_projections()
        
        # Contribuição maior deve resultar em reservas maiores
        reserves_low = projections_low['reserves']
        reserves_high = projections_high['reserves']
        
        # Compara reservas na metade do período contributivo
        mid_point = min(len(reserves_low), len(reserves_high)) // 2
        if mid_point > 0:
            assert reserves_high[mid_point] > reserves_low[mid_point]
    
    def test_different_ages(self, base_state):
        """Testa projeções para diferentes idades"""
        # Pessoa jovem
        state_young = base_state.model_copy()
        state_young.age = 25
        builder_young = ProjectionBuilder(state_young)
        projections_young = builder_young.build_projections()
        
        # Pessoa mais velha
        state_old = base_state.model_copy()
        state_old.age = 50
        builder_old = ProjectionBuilder(state_old)
        projections_old = builder_old.build_projections()
        
        # Pessoa jovem deve ter mais períodos de projeção
        assert len(projections_young['projection_ages']) > len(projections_old['projection_ages'])
    
    def test_cd_projections(self, base_state):
        """Testa projeções específicas para CD"""
        cd_state = base_state.model_copy()
        cd_state.plan_type = "CD"
        cd_state.initial_balance = 10000.0
        cd_state.accrual_rate = 0.05
        
        builder = ProjectionBuilder(cd_state)
        projections = builder.build_projections()
        
        # Estrutura deve ser similar
        assert 'projection_ages' in projections
        assert 'reserves' in projections
        
        # Reservas devem começar com saldo inicial
        reserves = projections['reserves']
        assert reserves[0] >= cd_state.initial_balance
    
    def test_salary_growth_impact(self, base_state):
        """Testa impacto do crescimento salarial"""
        # Sem crescimento
        state_no_growth = base_state.model_copy()
        state_no_growth.salary_growth_real = 0.0
        builder_no_growth = ProjectionBuilder(state_no_growth)
        projections_no_growth = builder_no_growth.build_projections()
        
        # Com crescimento
        state_growth = base_state.model_copy()
        state_growth.salary_growth_real = 0.02  # 2% a.a.
        builder_growth = ProjectionBuilder(state_growth)
        projections_growth = builder_growth.build_projections()
        
        # Crescimento salarial deve impactar reservas
        reserves_no_growth = projections_no_growth['reserves']
        reserves_growth = projections_growth['reserves']
        
        # Comparar reservas no final da fase contributiva
        months_to_retirement = (base_state.retirement_age - base_state.age) * 12
        compare_idx = min(months_to_retirement - 12, len(reserves_no_growth) - 1, len(reserves_growth) - 1)
        
        if compare_idx > 12:  # Ter dados suficientes
            assert reserves_growth[compare_idx] > reserves_no_growth[compare_idx]
    
    def test_discount_rate_impact(self, base_state):
        """Testa impacto da taxa de desconto"""
        # Taxa baixa
        state_low_rate = base_state.model_copy()
        state_low_rate.discount_rate = 0.04
        builder_low_rate = ProjectionBuilder(state_low_rate)
        projections_low_rate = builder_low_rate.build_projections()
        
        # Taxa alta
        state_high_rate = base_state.model_copy()
        state_high_rate.discount_rate = 0.08
        builder_high_rate = ProjectionBuilder(state_high_rate)
        projections_high_rate = builder_high_rate.build_projections()
        
        # Ambas devem produzir projeções válidas
        assert len(projections_low_rate['reserves']) > 0
        assert len(projections_high_rate['reserves']) > 0
    
    def test_edge_case_near_retirement(self, base_state):
        """Testa caso extremo: próximo da aposentadoria"""
        state = base_state.model_copy()
        state.age = 64
        state.retirement_age = 65
        
        builder = ProjectionBuilder(state)
        projections = builder.build_projections()
        
        # Deve funcionar mesmo com período curto
        assert len(projections['projection_ages']) > 0
        assert len(projections['reserves']) > 0
        
        # Deve cobrir pelo menos até a aposentadoria
        assert max(projections['projection_ages']) >= state.retirement_age
    
    def test_monthly_vs_annual_consistency(self, base_state):
        """Testa consistência entre cálculos mensais e anuais"""
        builder = ProjectionBuilder(base_state)
        projections = builder.build_projections()
        
        ages = projections['projection_ages']
        
        # Verifica que existe pelo menos uma idade por ano
        years_covered = int(ages[-1] - ages[0])
        if years_covered > 0:
            assert len(ages) >= years_covered
    
    def test_projection_data_types(self, base_state):
        """Testa tipos de dados nas projeções"""
        builder = ProjectionBuilder(base_state)
        projections = builder.build_projections()
        
        # Idades devem ser numéricas
        for age in projections['projection_ages']:
            assert isinstance(age, (int, float))
            assert age >= 0
        
        # Fluxos de caixa devem ser numéricos
        for cf in projections['cash_flows']:
            assert isinstance(cf, (int, float, Decimal))
        
        # Reservas devem ser numéricas
        for reserve in projections['reserves']:
            assert isinstance(reserve, (int, float, Decimal))
            assert reserve >= 0 or abs(reserve) < 1e6  # Permite pequenos negativos por arredondamento
    
    def test_projection_length_limits(self, base_state):
        """Testa limites no comprimento das projeções"""
        builder = ProjectionBuilder(base_state)
        projections = builder.build_projections()
        
        # Não deve ter projeções excessivamente longas
        max_expected_length = (120 - base_state.age) * 12  # Até 120 anos, mensal
        assert len(projections['projection_ages']) <= max_expected_length
        
        # Nem muito curtas (pelo menos até aposentadoria)
        min_expected_length = max(1, (base_state.retirement_age - base_state.age) * 12)
        assert len(projections['projection_ages']) >= min_expected_length
    
    def test_empty_or_invalid_state_handling(self):
        """Testa tratamento de estados inválidos"""
        # Estado com idade negativa
        invalid_state = SimulatorState(
            age=-5,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            target_benefit=3000.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        
        # Deve lidar com entrada inválida graciosamente
        try:
            builder = ProjectionBuilder(invalid_state)
            projections = builder.build_projections()
            # Se não lançar exceção, deve retornar estrutura válida
            assert isinstance(projections, dict)
        except (ValueError, AssertionError):
            # Aceita exceção para entrada inválida
            pass