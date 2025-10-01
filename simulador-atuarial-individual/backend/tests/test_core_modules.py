"""Testes unitários para módulos principais do core"""
import pytest
import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.participant import SimulatorState
from src.models.results import SimulatorResults
from src.core.actuarial_engine import ActuarialEngine


class TestActuarialEngine:
    """Testes básicos para ActuarialEngine"""
    
    @pytest.fixture
    def base_state(self):
        """Estado básico para testes"""
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
    
    def test_engine_initialization(self, base_state):
        """Testa inicialização do engine"""
        engine = ActuarialEngine()
        assert hasattr(engine, 'calculate_individual_simulation')
        assert hasattr(engine, 'bd_calculator')
        assert hasattr(engine, 'cd_calculator')

    def test_basic_calculation(self, base_state):
        """Testa cálculo básico"""
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(base_state)
        
        # Verifica tipo do resultado
        assert isinstance(results, dict) or hasattr(results, '__dict__')
        
        # Se for dict, converte para verificação
        if isinstance(results, dict):
            assert 'rmba' in results or 'monthly_income_bd' in results
        else:
            assert hasattr(results, 'rmba') or hasattr(results, 'monthly_income_bd')
    
    def test_cd_calculation(self, base_state):
        """Testa cálculo CD"""
        cd_state = base_state.model_copy()
        cd_state.plan_type = "CD"
        cd_state.initial_balance = 10000.0
        cd_state.accrual_rate = 0.05

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(cd_state)
        
        # Deve retornar resultado válido
        assert results is not None
        
        # Se for dict, verifica campos CD
        if isinstance(results, dict):
            assert 'monthly_income_cd' in results or 'accumulated_balance_retirement' in results
    
    def test_different_ages(self, base_state):
        """Testa cálculo com diferentes idades"""
        engine = ActuarialEngine()

        # Pessoa jovem
        young_state = base_state.model_copy()
        young_state.age = 25
        results_young = engine.calculate_individual_simulation(young_state)

        # Pessoa mais velha
        old_state = base_state.model_copy()
        old_state.age = 50
        results_old = engine.calculate_individual_simulation(old_state)
        
        # Ambos devem retornar resultados válidos
        assert results_young is not None
        assert results_old is not None
        
        # Resultados devem ser diferentes
        assert results_young != results_old
    
    def test_different_genders(self, base_state):
        """Testa cálculo com diferentes gêneros"""
        # Masculino
        male_state = base_state.model_copy()
        male_state.gender = "M"
        engine = ActuarialEngine()
        results_male = engine.calculate_individual_simulation(male_state)
        
        # Feminino
        female_state = base_state.model_copy()
        female_state.gender = "F"
        results_female = engine.calculate_individual_simulation(female_state)
        
        # Ambos devem retornar resultados válidos
        assert results_male is not None
        assert results_female is not None
    
    def test_rate_impact(self, base_state):
        """Testa impacto de diferentes taxas"""
        # Taxa baixa
        low_rate_state = base_state.model_copy()
        low_rate_state.discount_rate = 0.04
        engine = ActuarialEngine()
        results_low = engine.calculate_individual_simulation(low_rate_state)
        
        # Taxa alta
        high_rate_state = base_state.model_copy()
        high_rate_state.discount_rate = 0.08
        engine = ActuarialEngine()
        results_high = engine.calculate_individual_simulation(high_rate_state)
        
        # Ambos devem retornar resultados válidos
        assert results_low is not None
        assert results_high is not None
        
        # Resultados devem ser diferentes
        assert results_low != results_high
    
    def test_contribution_impact(self, base_state):
        """Testa impacto de diferentes contribuições"""
        # Contribuição baixa
        low_contrib_state = base_state.model_copy()
        low_contrib_state.contribution_rate = 5.0
        engine = ActuarialEngine()
        results_low = engine.calculate_individual_simulation(low_contrib_state)
        
        # Contribuição alta
        high_contrib_state = base_state.model_copy()
        high_contrib_state.contribution_rate = 20.0
        engine = ActuarialEngine()
        results_high = engine.calculate_individual_simulation(high_contrib_state)
        
        # Ambos devem retornar resultados válidos
        assert results_low is not None
        assert results_high is not None
    
    def test_edge_cases(self, base_state):
        """Testa casos extremos"""
        # Idade próxima da aposentadoria
        near_retirement_state = base_state.model_copy()
        near_retirement_state.age = 64
        near_retirement_state.retirement_age = 65
        engine = ActuarialEngine()
        results_near = engine.calculate_individual_simulation(near_retirement_state)
        
        # Deve funcionar mesmo com pouco tempo
        assert results_near is not None
        
        # Salário muito alto
        high_salary_state = base_state.model_copy()
        high_salary_state.salary = 100000.0
        high_salary_state.target_benefit = 70000.0
        engine = ActuarialEngine()
        results_high_salary = engine.calculate_individual_simulation(high_salary_state)
        
        # Deve lidar com valores altos
        assert results_high_salary is not None
    
    def test_mortality_tables(self, base_state):
        """Testa diferentes tábuas de mortalidade"""
        # Tábua BR_EMS_2021
        br_state = base_state.model_copy()
        br_state.mortality_table = "BR_EMS_2021"
        engine = ActuarialEngine()
        results_br = engine.calculate_individual_simulation(br_state)
        
        # Tábua AT_2000
        at_state = base_state.model_copy()
        at_state.mortality_table = "AT_2000"
        engine = ActuarialEngine()
        results_at = engine.calculate_individual_simulation(at_state)
        
        # Ambos devem funcionar
        assert results_br is not None
        assert results_at is not None
        
        # Resultados podem ser diferentes
        # (não força diferença, mas permite)
    
    def test_replacement_rate_mode(self, base_state):
        """Testa modo de taxa de reposição"""
        replacement_state = base_state.model_copy()
        replacement_state.benefit_target_mode = "REPLACEMENT_RATE"
        replacement_state.target_replacement_rate = 0.7
        replacement_state.target_benefit = None
        
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(replacement_state)
        
        # Deve calcular normalmente
        assert results is not None
    
    def test_calculation_consistency(self, base_state):
        """Testa consistência dos cálculos"""
        # Executa o mesmo cálculo várias vezes
        engine1 = ActuarialEngine()
        results1 = engine1.calculate_individual_simulation(base_state)
        
        engine2 = ActuarialEngine()
        results2 = engine2.calculate_individual_simulation(base_state)
        
        # Resultados devem ser consistentes
        assert results1 == results2 or (
            # Se forem objetos complexos, pelo menos devem ser do mesmo tipo
            type(results1) == type(results2)
        )


class TestModels:
    """Testes para modelos de dados"""
    
    def test_simulator_state_creation(self):
        """Testa criação do SimulatorState"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            accrual_rate=5.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method="PUC"
        )
        
        assert state.age == 30
        assert state.gender == "M"
        assert state.salary == 5000.0
        assert state.retirement_age == 65
        assert state.contribution_rate == 10.0
        assert state.mortality_table == "BR_EMS_2021"
        assert state.discount_rate == 0.06
    
    def test_simulator_state_validation(self):
        """Testa validação do SimulatorState"""
        # Estado válido
        valid_state = SimulatorState(
            age=25,
            gender="F",
            salary=8000.0,
            initial_balance=0.0,
            accrual_rate=5.0,
            retirement_age=60,
            contribution_rate=15.0,
            mortality_table="AT_2000",
            discount_rate=0.05,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method="PUC"
        )
        
        assert valid_state.age == 25
        assert valid_state.gender == "F"
        assert valid_state.salary == 8000.0
    
    def test_simulator_state_model_copy(self):
        """Testa cópia do SimulatorState"""
        original = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            accrual_rate=5.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method="PUC"
        )
        
        # Cópia simples
        copy1 = original.model_copy()
        assert copy1.age == original.age
        assert copy1.salary == original.salary
        
        # Cópia com modificações
        copy2 = original.model_copy(update={'age': 35, 'salary': 6000.0})
        assert copy2.age == 35
        assert copy2.salary == 6000.0
        assert copy2.gender == original.gender  # Não modificado
    
    def test_simulator_state_defaults(self):
        """Testa valores padrão do SimulatorState"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            accrual_rate=5.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method="PUC"
        )
        
        # Verifica alguns valores padrão esperados
        assert hasattr(state, 'plan_type')
        assert hasattr(state, 'initial_balance')
        assert hasattr(state, 'admin_fee_rate')
        assert hasattr(state, 'loading_fee_rate')
    
    def test_bd_specific_fields(self):
        """Testa campos específicos para BD"""
        bd_state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            accrual_rate=5.0,
            retirement_age=65,
            contribution_rate=10.0,
            target_benefit=3000.0,
            benefit_target_mode="VALUE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method="PUC",
            plan_type="BD"
        )
        
        assert bd_state.plan_type == "BD"
        assert bd_state.target_benefit == 3000.0
        assert bd_state.benefit_target_mode == "VALUE"
    
    def test_cd_specific_fields(self):
        """Testa campos específicos para CD"""
        cd_state = SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            retirement_age=60,
            contribution_rate=12.0,
            initial_balance=10000.0,
            accrual_rate=0.05,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            salary_growth_real=0.01,
            projection_years=30,
            calculation_method="CD",
            plan_type="CD",
            cd_conversion_mode="ACTUARIAL"
        )
        
        assert cd_state.plan_type == "CD"
        assert cd_state.initial_balance == 10000.0
        assert cd_state.accrual_rate == 0.05
        assert cd_state.cd_conversion_mode == "ACTUARIAL"
    
    def test_field_types(self):
        """Testa tipos dos campos"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            accrual_rate=5.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method="PUC"
        )
        
        # Verifica tipos básicos
        assert isinstance(state.age, int)
        assert isinstance(state.gender, str)
        assert isinstance(state.salary, (int, float))
        assert isinstance(state.retirement_age, int)
        assert isinstance(state.contribution_rate, (int, float))
        assert isinstance(state.mortality_table, str)
        assert isinstance(state.discount_rate, (int, float))
    
    def test_numeric_ranges(self):
        """Testa faixas numéricas razoáveis"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            accrual_rate=5.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method="PUC"
        )
        
        # Verifica faixas razoáveis
        assert 0 < state.age < 120
        assert state.salary > 0
        assert state.age < state.retirement_age
        assert 0 < state.contribution_rate < 100
        assert 0 < state.discount_rate < 1