"""Testes unitários para ActuarialEngine"""
import pytest
import sys
from pathlib import Path
from decimal import Decimal

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.actuarial_engine import ActuarialEngine
from src.models.participant import SimulatorState
from src.models.results import SimulatorResults


class TestActuarialEngine:
    """Testes para a classe ActuarialEngine"""
    
    @pytest.fixture
    def base_bd_state(self):
        """Estado base para testes BD"""
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
    def base_cd_state(self):
        """Estado base para testes CD"""
        return SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            retirement_age=60,
            contribution_rate=12.0,
            initial_balance=10000.0,
            mortality_table="AT_2000",
            discount_rate=0.05,
            accrual_rate=0.04,
            plan_type="CD",
            cd_conversion_mode="ACTUARIAL"
        )
    
    def test_engine_initialization_bd(self, base_bd_state):
        """Testa inicialização do engine para BD"""
        engine = ActuarialEngine(base_bd_state)
        
        assert engine.state == base_bd_state
        assert engine.state.plan_type == "BD"
        assert hasattr(engine, 'calculate')
    
    def test_engine_initialization_cd(self, base_cd_state):
        """Testa inicialização do engine para CD"""
        engine = ActuarialEngine(base_cd_state)
        
        assert engine.state == base_cd_state
        assert engine.state.plan_type == "CD"
        assert hasattr(engine, 'calculate')
    
    def test_bd_calculation_basic(self, base_bd_state):
        """Testa cálculo básico BD"""
        engine = ActuarialEngine(base_bd_state)
        results = engine.calculate()
        
        # Verifica tipo do resultado
        assert isinstance(results, SimulatorResults)
        
        # Verifica campos obrigatórios BD
        assert hasattr(results, 'rmba')
        assert hasattr(results, 'total_contributions')
        assert hasattr(results, 'deficit_surplus')
        assert hasattr(results, 'sustainable_replacement_ratio')
        
        # Verifica valores razoáveis
        assert results.rmba > 0
        assert results.total_contributions > 0
        assert isinstance(results.deficit_surplus, (int, float))
    
    def test_cd_calculation_basic(self, base_cd_state):
        """Testa cálculo básico CD"""
        engine = ActuarialEngine(base_cd_state)
        results = engine.calculate()
        
        # Verifica tipo do resultado
        assert isinstance(results, SimulatorResults)
        
        # Verifica campos obrigatórios CD
        assert hasattr(results, 'accumulated_balance_retirement')
        assert hasattr(results, 'estimated_benefit')
        assert hasattr(results, 'contribution_phase_balances')
        
        # Verifica valores razoáveis
        assert results.accumulated_balance_retirement > base_cd_state.initial_balance
        assert results.estimated_benefit > 0
        assert len(results.contribution_phase_balances) > 0
    
    def test_bd_projections_structure(self, base_bd_state):
        """Testa estrutura das projeções BD"""
        engine = ActuarialEngine(base_bd_state)
        results = engine.calculate()
        
        # Verifica arrays de projeção
        assert hasattr(results, 'cash_flows')
        assert hasattr(results, 'accumulated_reserves')
        
        assert len(results.cash_flows) > 0
        assert len(results.accumulated_reserves) > 0
        
        # Verifica consistência de tamanhos
        months_to_retirement = (base_bd_state.retirement_age - base_bd_state.age) * 12
        assert len(results.cash_flows) >= months_to_retirement
    
    def test_cd_conversion_modes(self, base_cd_state):
        """Testa diferentes modos de conversão CD"""
        # Teste modo atuarial
        base_cd_state.cd_conversion_mode = "ACTUARIAL"
        engine_actuarial = ActuarialEngine(base_cd_state)
        results_actuarial = engine_actuarial.calculate()
        
        # Teste modo taxa fixa
        base_cd_state.cd_conversion_mode = "FIXED_RATE"
        engine_fixed = ActuarialEngine(base_cd_state)
        results_fixed = engine_fixed.calculate()
        
        # Ambos devem ter benefícios válidos
        assert results_actuarial.estimated_benefit > 0
        assert results_fixed.estimated_benefit > 0
        
        # Benefícios podem ser diferentes entre modos
        # (não necessariamente, mas é provável)
    
    def test_rate_impact_bd(self, base_bd_state):
        """Testa impacto de diferentes taxas no BD"""
        # Calcula com taxa padrão
        engine1 = ActuarialEngine(base_bd_state)
        results1 = engine1.calculate()
        
        # Calcula com taxa mais alta
        state_high_rate = base_bd_state.model_copy()
        state_high_rate.discount_rate = 0.08
        engine2 = ActuarialEngine(state_high_rate)
        results2 = engine2.calculate()
        
        # RMBA deve ser diferente com taxas diferentes
        assert results1.rmba != results2.rmba
        
        # Taxa mais alta normalmente resulta em RMBA menor
        assert results2.rmba < results1.rmba
    
    def test_contribution_rate_impact_bd(self, base_bd_state):
        """Testa impacto da taxa de contribuição no BD"""
        # Taxa baixa
        state_low = base_bd_state.model_copy()
        state_low.contribution_rate = 5.0
        engine_low = ActuarialEngine(state_low)
        results_low = engine_low.calculate()
        
        # Taxa alta
        state_high = base_bd_state.model_copy()
        state_high.contribution_rate = 20.0
        engine_high = ActuarialEngine(state_high)
        results_high = engine_high.calculate()
        
        # Taxa maior deve reduzir déficit (ou aumentar superávit)
        assert results_high.deficit_surplus < results_low.deficit_surplus
        assert results_high.total_contributions > results_low.total_contributions
    
    def test_age_impact_calculation(self, base_bd_state):
        """Testa impacto da idade no cálculo"""
        # Pessoa jovem
        state_young = base_bd_state.model_copy()
        state_young.age = 25
        engine_young = ActuarialEngine(state_young)
        results_young = engine_young.calculate()
        
        # Pessoa mais velha
        state_old = base_bd_state.model_copy()
        state_old.age = 50
        engine_old = ActuarialEngine(state_old)
        results_old = engine_old.calculate()
        
        # Pessoa jovem tem mais tempo para contribuir
        assert len(results_young.cash_flows) > len(results_old.cash_flows)
        assert results_young.total_contributions > results_old.total_contributions
    
    def test_gender_impact_calculation(self, base_bd_state):
        """Testa impacto do gênero no cálculo"""
        # Masculino
        state_male = base_bd_state.model_copy()
        state_male.gender = "M"
        engine_male = ActuarialEngine(state_male)
        results_male = engine_male.calculate()
        
        # Feminino
        state_female = base_bd_state.model_copy()
        state_female.gender = "F"
        engine_female = ActuarialEngine(state_female)
        results_female = engine_female.calculate()
        
        # RMBAs devem ser diferentes devido à expectativa de vida
        assert results_male.rmba != results_female.rmba
    
    def test_replacement_rate_mode_bd(self, base_bd_state):
        """Testa modo de taxa de reposição BD"""
        state = base_bd_state.model_copy()
        state.benefit_target_mode = "REPLACEMENT_RATE"
        state.target_replacement_rate = 0.7  # 70%
        state.target_benefit = None
        
        engine = ActuarialEngine(state)
        results = engine.calculate()
        
        # Deve calcular normalmente
        assert results.rmba > 0
        assert results.total_contributions > 0
        
        # Benefício alvo deve ser calculado com base na taxa
        expected_benefit = state.salary * state.target_replacement_rate
        # Verifica se está na faixa esperada (pode ter ajustes)
        assert abs(results.target_benefit_calculated - expected_benefit) < state.salary * 0.1
    
    def test_edge_case_same_age_retirement(self, base_bd_state):
        """Testa caso extremo: idade igual à aposentadoria"""
        state = base_bd_state.model_copy()
        state.age = 65
        state.retirement_age = 65
        
        engine = ActuarialEngine(state)
        results = engine.calculate()
        
        # Deve funcionar mesmo sem período contributivo
        assert isinstance(results, SimulatorResults)
        assert results.rmba >= 0
    
    def test_high_salary_calculation(self, base_bd_state):
        """Testa cálculo com salário muito alto"""
        state = base_bd_state.model_copy()
        state.salary = 100000.0  # R$ 100k
        state.target_benefit = 70000.0  # R$ 70k
        
        engine = ActuarialEngine(state)
        results = engine.calculate()
        
        # Deve lidar com valores altos sem erro
        assert results.rmba > 0
        assert results.total_contributions > 1_000_000  # Esperado para salário alto
    
    def test_low_contribution_rate(self, base_bd_state):
        """Testa taxa de contribuição muito baixa"""
        state = base_bd_state.model_copy()
        state.contribution_rate = 1.0  # 1%
        
        engine = ActuarialEngine(state)
        results = engine.calculate()
        
        # Deve ter déficit significativo
        assert results.deficit_surplus > 0  # Déficit positivo
        assert results.deficit_surplus > state.target_benefit * 10  # Déficit substancial
    
    def test_different_mortality_tables(self, base_bd_state):
        """Testa cálculo com diferentes tábuas de mortalidade"""
        # BR_EMS_2021
        state1 = base_bd_state.model_copy()
        state1.mortality_table = "BR_EMS_2021"
        engine1 = ActuarialEngine(state1)
        results1 = engine1.calculate()
        
        # AT_2000
        state2 = base_bd_state.model_copy()
        state2.mortality_table = "AT_2000"
        engine2 = ActuarialEngine(state2)
        results2 = engine2.calculate()
        
        # Resultados devem ser diferentes
        assert results1.rmba != results2.rmba
        assert abs(results1.rmba - results2.rmba) > 1000  # Diferença significativa
    
    def test_calculation_consistency_multiple_runs(self, base_bd_state):
        """Testa consistência em múltiplas execuções"""
        results = []
        
        for _ in range(5):
            engine = ActuarialEngine(base_bd_state)
            result = engine.calculate()
            results.append(result)
        
        # Todos os resultados devem ser idênticos
        first_result = results[0]
        for result in results[1:]:
            assert result.rmba == first_result.rmba
            assert result.deficit_surplus == first_result.deficit_surplus
            assert result.total_contributions == first_result.total_contributions
    
    def test_zero_contribution_edge_case(self, base_bd_state):
        """Testa caso extremo: contribuição zero"""
        state = base_bd_state.model_copy()
        state.contribution_rate = 0.0
        
        engine = ActuarialEngine(state)
        results = engine.calculate()
        
        # Deve funcionar e mostrar déficit total
        assert results.total_contributions == 0
        assert results.deficit_surplus > 0  # Todo o benefício é déficit
        assert results.deficit_surplus >= results.rmba * 0.9  # Aproximadamente igual à RMBA
    
    def test_benefit_greater_than_salary_bd(self, base_bd_state):
        """Testa benefício maior que salário BD"""
        state = base_bd_state.model_copy()
        state.target_benefit = state.salary * 1.5  # 150% do salário
        
        engine = ActuarialEngine(state)
        results = engine.calculate()
        
        # Deve calcular normalmente
        assert results.rmba > 0
        # Déficit deve ser significativo
        assert results.deficit_surplus > state.salary * 10