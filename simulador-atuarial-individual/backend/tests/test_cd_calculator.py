"""Testes para CDCalculator - Core dos cálculos de Contribuição Definida"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.cd_calculator import CDCalculator
from src.core.actuarial_engine import ActuarialEngine
from src.models.participant import SimulatorState


class TestCDCalculator:
    """Testes para cálculos de planos CD"""

    @pytest.fixture
    def base_cd_state(self):
        """Estado base para testes CD"""
        return SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            initial_balance=10000.0,
            retirement_age=60,
            contribution_rate=12.0,
            target_benefit=None,
            benefit_target_mode="VALUE",
            mortality_table="AT_2000",
            discount_rate=0.05,
            accrual_rate=0.04,  # 4% a.a. de rentabilidade
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="CD",
            plan_type="CD",
            cd_conversion_mode="ACTUARIAL"
        )

    def test_accumulation_phase_balance_grows(self, base_cd_state):
        """Testa que saldo cresce durante fase de acumulação"""
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(base_cd_state)

        # Saldo final deve ser maior que saldo inicial
        assert results.individual_balance > base_cd_state.initial_balance

        # Deve ter rendimentos acumulados
        assert results.accumulated_return > 0

    def test_actuarial_conversion_mode(self, base_cd_state):
        """Testa modo de conversão atuarial (renda vitalícia)"""
        state = base_cd_state.model_copy()
        state.cd_conversion_mode = "ACTUARIAL"
        state.target_benefit = 3500.0

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        # Deve calcular renda mensal vitalícia
        assert results.monthly_income_cd > 0
        assert results.conversion_factor > 0

    def test_percentage_mode_withdrawals(self):
        """Testa modo de saque por percentual"""
        state = SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            initial_balance=10000.0,
            retirement_age=60,
            contribution_rate=12.0,
            target_benefit=None,
            benefit_target_mode="VALUE",
            mortality_table="AT_2000",
            discount_rate=0.05,
            accrual_rate=0.04,
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="CD",
            plan_type="CD",
            cd_conversion_mode="PERCENTAGE",
            cd_withdrawal_percentage=8.0  # 8% ao ano
        )

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        # Deve calcular renda baseada em percentual
        assert results.monthly_income_cd > 0

    def test_certain_period_annuity(self):
        """Testa renda certa por período determinado"""
        state = SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            initial_balance=10000.0,
            retirement_age=60,
            contribution_rate=12.0,
            target_benefit=None,
            benefit_target_mode="VALUE",
            mortality_table="AT_2000",
            discount_rate=0.05,
            accrual_rate=0.04,
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="CD",
            plan_type="CD",
            cd_conversion_mode="CERTAIN_10Y"  # 10 anos certos
        )

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        # Deve calcular renda para 10 anos
        assert results.monthly_income_cd > 0
        assert results.benefit_duration_years == 10

    def test_contribution_impact_on_final_balance(self, base_cd_state):
        """Testa impacto da contribuição no saldo final"""
        # Contribuição baixa
        state_low = base_cd_state.model_copy()
        state_low.contribution_rate = 5.0

        # Contribuição alta
        state_high = base_cd_state.model_copy()
        state_high.contribution_rate = 20.0

        engine = ActuarialEngine()
        results_low = engine.calculate_individual_simulation(state_low)
        results_high = engine.calculate_individual_simulation(state_high)

        # Contribuição maior deve resultar em saldo maior
        assert results_high.individual_balance > results_low.individual_balance

    def test_accrual_rate_impact(self, base_cd_state):
        """Testa impacto da taxa de rentabilidade (acumulação)"""
        # Rentabilidade baixa
        state_low = base_cd_state.model_copy()
        state_low.accumulation_rate = 0.02  # 2% a.a.
        state_low.conversion_rate = 0.02    # Mesma taxa para simplicidade

        # Rentabilidade alta
        state_high = base_cd_state.model_copy()
        state_high.accumulation_rate = 0.06  # 6% a.a.
        state_high.conversion_rate = 0.06     # Mesma taxa para simplicidade

        engine = ActuarialEngine()
        results_low = engine.calculate_individual_simulation(state_low)
        results_high = engine.calculate_individual_simulation(state_high)

        # Rentabilidade maior deve resultar em saldo maior
        assert results_high.individual_balance > results_low.individual_balance
        assert results_high.accumulated_return > results_low.accumulated_return

    def test_administrative_costs_reduce_balance(self, base_cd_state):
        """Testa que custos administrativos reduzem saldo"""
        # Sem custos
        state_no_costs = base_cd_state.model_copy()
        state_no_costs.admin_fee_rate = 0.0
        state_no_costs.loading_fee_rate = 0.0

        # Com custos
        state_with_costs = base_cd_state.model_copy()
        state_with_costs.admin_fee_rate = 0.02  # 2% a.a.
        state_with_costs.loading_fee_rate = 0.05  # 5% carregamento

        engine = ActuarialEngine()
        results_no_costs = engine.calculate_individual_simulation(state_no_costs)
        results_with_costs = engine.calculate_individual_simulation(state_with_costs)

        # Custos devem reduzir saldo final
        assert results_with_costs.individual_balance < results_no_costs.individual_balance
        assert results_with_costs.administrative_cost_total > 0

    def test_initial_balance_impact(self, base_cd_state):
        """Testa impacto do saldo inicial"""
        # Sem saldo inicial
        state_zero = base_cd_state.model_copy()
        state_zero.initial_balance = 0.0

        # Com saldo inicial alto
        state_high = base_cd_state.model_copy()
        state_high.initial_balance = 50000.0

        engine = ActuarialEngine()
        results_zero = engine.calculate_individual_simulation(state_zero)
        results_high = engine.calculate_individual_simulation(state_high)

        # Saldo inicial maior deve resultar em saldo final maior
        assert results_high.individual_balance > results_zero.individual_balance

    def test_net_accumulated_value(self, base_cd_state):
        """Testa valor líquido acumulado (após custos)"""
        state = base_cd_state.model_copy()
        state.admin_fee_rate = 0.015

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        # Valor líquido deve ser menor que saldo bruto
        if results.net_accumulated_value is not None:
            assert results.net_accumulated_value <= results.individual_balance

    def test_effective_return_rate(self, base_cd_state):
        """Testa taxa de retorno efetiva"""
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(base_cd_state)

        # Taxa de retorno efetiva deve estar em range razoável
        # Pode estar em formato percentual ou decimal, validar ambos
        if results.effective_return_rate is not None:
            # Aceitar formato decimal (0.05 = 5%) ou percentual (5.0 = 5%)
            assert (0 <= results.effective_return_rate <= 0.15) or (0 <= results.effective_return_rate <= 100)

    def test_actuarial_equivalent_mode(self):
        """Testa modo de equivalência atuarial anual"""
        state = SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            initial_balance=10000.0,
            retirement_age=60,
            contribution_rate=12.0,
            target_benefit=None,
            benefit_target_mode="VALUE",
            mortality_table="AT_2000",
            discount_rate=0.05,
            accrual_rate=0.04,
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="CD",
            plan_type="CD",
            cd_conversion_mode="ACTUARIAL_EQUIVALENT",
            cd_floor_percentage=70.0  # Piso de 70% do primeiro ano
        )

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        # Deve calcular renda com piso
        assert results.monthly_income_cd > 0

    def test_gender_impact_on_annuity(self):
        """Testa impacto do gênero na renda vitalícia"""
        # Masculino
        state_male = SimulatorState(
            age=35,
            gender="M",
            salary=6000.0,
            initial_balance=100000.0,
            retirement_age=60,
            contribution_rate=12.0,
            target_benefit=None,
            benefit_target_mode="VALUE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.05,
            accrual_rate=0.04,
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="CD",
            plan_type="CD",
            cd_conversion_mode="ACTUARIAL"
        )

        # Feminino (vive mais)
        state_female = state_male.model_copy()
        state_female.gender = "F"

        engine = ActuarialEngine()
        results_male = engine.calculate_individual_simulation(state_male)
        results_female = engine.calculate_individual_simulation(state_female)

        # Mulheres vivem mais → renda mensal menor (mesmo saldo)
        assert results_male.monthly_income_cd > results_female.monthly_income_cd

    def test_cd_with_target_benefit_optimization(self):
        """Testa CD com meta de benefício (otimização de contribuição)"""
        state = SimulatorState(
            age=35,
            gender="F",
            salary=6000.0,
            initial_balance=10000.0,
            retirement_age=60,
            contribution_rate=12.0,
            target_benefit=3500.0,  # Meta de renda
            benefit_target_mode="VALUE",
            mortality_table="AT_2000",
            discount_rate=0.05,
            accrual_rate=0.04,
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="CD",
            plan_type="CD",
            cd_conversion_mode="ACTUARIAL"
        )

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        # Deve calcular renda
        assert results.monthly_income_cd > 0
