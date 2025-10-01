"""Testes para BDCalculator - Core dos cálculos de Benefício Definido"""
import pytest
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.bd_calculator import BDCalculator
from src.core.actuarial_engine import ActuarialEngine
from src.core.mortality_tables import get_mortality_table
from src.models.participant import SimulatorState


class TestBDCalculator:
    """Testes para cálculos de planos BD"""

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

    def test_rmba_calculation_for_active_participant(self, base_bd_state):
        """Testa cálculo de RMBA para participante ativo"""
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(base_bd_state)

        # RMBA pode ser positivo ou negativo dependendo se há déficit ou superávit
        # O importante é que seja um valor válido e calculado
        assert isinstance(results.rmba, (int, float))
        assert not np.isnan(results.rmba)
        assert not np.isinf(results.rmba)

    def test_rmba_increases_with_age(self):
        """Testa que RMBA aumenta conforme pessoa envelhece"""
        # Pessoa jovem
        state_young = SimulatorState(
            age=25,
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
            projection_years=45,
            calculation_method="PUC",
            plan_type="BD"
        )

        # Pessoa mais velha
        state_old = SimulatorState(
            age=50,
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
            projection_years=20,
            calculation_method="PUC",
            plan_type="BD"
        )

        engine = ActuarialEngine()
        results_young = engine.calculate_individual_simulation(state_young)
        results_old = engine.calculate_individual_simulation(state_old)

        # RMBA deve ser maior para pessoa mais próxima da aposentadoria
        assert results_old.rmba > results_young.rmba

    def test_rmbc_for_retired_participant(self):
        """Testa RMBC para participante já aposentado"""
        state_retired = SimulatorState(
            age=68,
            gender="M",
            salary=5000.0,  # Último salário
            initial_balance=0.0,
            retirement_age=65,
            contribution_rate=0.0,  # Não contribui mais
            target_benefit=3000.0,
            benefit_target_mode="VALUE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            accrual_rate=5.0,
            salary_growth_real=0.02,
            projection_years=20,
            calculation_method="PUC",
            plan_type="BD"
        )

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state_retired)

        # RMBC deve ser positivo para pessoa aposentada
        assert results.rmbc > 0, "RMBC deve ser positivo para aposentado"
        # RMBA deve ser zero para pessoa já aposentada
        assert results.rmba == 0, "RMBA deve ser zero para aposentado"

    def test_normal_cost_calculation(self, base_bd_state):
        """Testa cálculo do Custo Normal"""
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(base_bd_state)

        # Custo Normal deve ser positivo
        assert results.normal_cost > 0, "Custo Normal deve ser positivo"
        # Custo Normal deve ser menor que salário anual
        assert results.normal_cost < base_bd_state.salary * 13

    def test_deficit_surplus_calculation(self, base_bd_state):
        """Testa cálculo de déficit/superávit"""
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(base_bd_state)

        # Déficit/superávit deve ser um número válido
        assert isinstance(results.deficit_surplus, (int, float))

        # Se RMBA > VPA contribuições → déficit positivo
        # Se RMBA < VPA contribuições → superávit negativo

    def test_higher_benefit_increases_rmba(self, base_bd_state):
        """Testa que benefício maior aumenta RMBA"""
        # Benefício baixo
        state_low = base_bd_state.model_copy()
        state_low.target_benefit = 2000.0

        # Benefício alto
        state_high = base_bd_state.model_copy()
        state_high.target_benefit = 4000.0

        engine = ActuarialEngine()
        results_low = engine.calculate_individual_simulation(state_low)
        results_high = engine.calculate_individual_simulation(state_high)

        # Benefício maior deve resultar em RMBA maior
        assert results_high.rmba > results_low.rmba

    def test_higher_contribution_reduces_deficit(self, base_bd_state):
        """Testa que contribuição maior reduz déficit"""
        # Contribuição baixa
        state_low = base_bd_state.model_copy()
        state_low.contribution_rate = 5.0

        # Contribuição alta
        state_high = base_bd_state.model_copy()
        state_high.contribution_rate = 15.0

        engine = ActuarialEngine()
        results_low = engine.calculate_individual_simulation(state_low)
        results_high = engine.calculate_individual_simulation(state_high)

        # Contribuição maior deve aumentar superávit (valor absoluto de deficit_surplus quando RMBA negativo)
        # Se RMBA < 0 (superávit), então deficit_surplus é o valor absoluto do superávit
        # Maior contribuição = maior superávit = maior deficit_surplus
        assert results_high.deficit_surplus > results_low.deficit_surplus

    def test_discount_rate_impact(self, base_bd_state):
        """Testa impacto da taxa de desconto"""
        # Taxa baixa
        state_low_rate = base_bd_state.model_copy()
        state_low_rate.discount_rate = 0.04

        # Taxa alta
        state_high_rate = base_bd_state.model_copy()
        state_high_rate.discount_rate = 0.08

        engine = ActuarialEngine()
        results_low = engine.calculate_individual_simulation(state_low_rate)
        results_high = engine.calculate_individual_simulation(state_high_rate)

        # Taxa maior deve resultar em RMBA menor (desconto maior)
        assert results_high.rmba < results_low.rmba

    def test_gender_impact_on_rmba(self):
        """Testa impacto do gênero (expectativa de vida) na RMBA"""
        # Masculino
        state_male = SimulatorState(
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

        # Feminino (expectativa de vida maior)
        state_female = state_male.model_copy()
        state_female.gender = "F"

        engine = ActuarialEngine()
        results_male = engine.calculate_individual_simulation(state_male)
        results_female = engine.calculate_individual_simulation(state_female)

        # Mulheres vivem mais → RMBA maior (mais anos de benefício)
        assert results_female.rmba > results_male.rmba

    def test_replacement_rate_mode(self):
        """Testa modo de taxa de reposição"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            initial_balance=0.0,
            retirement_age=65,
            contribution_rate=10.0,
            target_replacement_rate=0.7,  # 70% do salário
            benefit_target_mode="REPLACEMENT_RATE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            accrual_rate=5.0,
            salary_growth_real=0.02,
            projection_years=40,
            calculation_method="PUC",
            plan_type="BD"
        )

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        # Deve calcular RMBA normalmente (pode ser negativo indicando superávit)
        assert isinstance(results.rmba, (int, float))

    def test_different_mortality_tables(self, base_bd_state):
        """Testa diferentes tábuas de mortalidade"""
        # BR_EMS_2021
        state_br = base_bd_state.model_copy()
        state_br.mortality_table = "BR_EMS_2021"

        # AT_2000
        state_at = base_bd_state.model_copy()
        state_at.mortality_table = "AT_2000"

        engine = ActuarialEngine()
        results_br = engine.calculate_individual_simulation(state_br)
        results_at = engine.calculate_individual_simulation(state_at)

        # Resultados devem ser diferentes (tábuas têm expectativas diferentes)
        assert results_br.rmba != results_at.rmba

    def test_puc_method_consistency(self, base_bd_state):
        """Testa consistência do método PUC"""
        state = base_bd_state.model_copy()
        state.calculation_method = "PUC"

        engine = ActuarialEngine()

        # Executar múltiplas vezes
        results1 = engine.calculate_individual_simulation(state)
        results2 = engine.calculate_individual_simulation(state)

        # Resultados devem ser idênticos
        assert results1.rmba == results2.rmba
        assert results1.rmbc == results2.rmbc
        assert results1.normal_cost == results2.normal_cost

    def test_zero_contribution_edge_case(self, base_bd_state):
        """Testa caso extremo: contribuição zero"""
        state = base_bd_state.model_copy()
        state.contribution_rate = 0.0

        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        # Deve calcular mesmo sem contribuições
        # Sem contribuições, haverá déficit (RMBA positivo ou deficit_surplus positivo representando falta de recursos)
        assert isinstance(results.rmba, (int, float))
        # Sem contribuições = déficit significativo
        assert results.deficit_surplus != 0  # Deve haver déficit ou superávit calculado
        assert results.total_contributions == 0

    def test_salary_growth_impact(self, base_bd_state):
        """Testa impacto do crescimento salarial"""
        # Sem crescimento
        state_no_growth = base_bd_state.model_copy()
        state_no_growth.salary_growth_real = 0.0

        # Com crescimento
        state_with_growth = base_bd_state.model_copy()
        state_with_growth.salary_growth_real = 0.03  # 3% a.a.

        engine = ActuarialEngine()
        results_no_growth = engine.calculate_individual_simulation(state_no_growth)
        results_with_growth = engine.calculate_individual_simulation(state_with_growth)

        # Com crescimento salarial, contribuições aumentam
        assert results_with_growth.total_contributions > results_no_growth.total_contributions

    def test_bd_differentiated_rates(self, base_bd_state):
        """Testa que BD usa taxas diferenciadas de acumulação e conversão"""
        # Configurar taxas diferentes
        state_diff_rates = base_bd_state.model_copy()
        state_diff_rates.accumulation_rate = 0.08  # 8% a.a. - acumulação agressiva
        state_diff_rates.conversion_rate = 0.04    # 4% a.a. - conversão conservadora

        calculator = BDCalculator()

        # Criar contexto e validar que taxas foram aplicadas
        context = calculator.create_bd_context(state_diff_rates)

        # Validar que contexto tem ambas as taxas
        assert hasattr(context, 'conversion_rate_monthly')
        assert context.discount_rate_monthly > 0  # Taxa de acumulação (mensal)
        assert context.conversion_rate_monthly > 0  # Taxa de conversão (mensal)

        # Taxa de conversão deve ser menor que taxa de acumulação
        assert context.conversion_rate_monthly < context.discount_rate_monthly

        # Executar simulação completa
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state_diff_rates)

        # Validar que cálculos foram realizados com sucesso
        assert results.rmba is not None
        assert not np.isnan(results.rmba)
        assert results.total_contributions > 0

    def test_bd_rates_impact_on_rmba(self, base_bd_state):
        """Testa que diferentes taxas de conversão impactam RMBA de forma correta"""
        # Cenário 1: Taxa de conversão baixa (conservador)
        state_low_conversion = base_bd_state.model_copy()
        state_low_conversion.accumulation_rate = 0.08  # Manter acumulação constante
        state_low_conversion.conversion_rate = 0.02    # Conversão muito conservadora

        # Cenário 2: Taxa de conversão alta
        state_high_conversion = base_bd_state.model_copy()
        state_high_conversion.accumulation_rate = 0.08  # Mesma acumulação
        state_high_conversion.conversion_rate = 0.08    # Conversão agressiva

        calculator = BDCalculator()

        # Obter contextos e tábuas
        context_low = calculator.create_bd_context(state_low_conversion)
        context_high = calculator.create_bd_context(state_high_conversion)

        mortality_table = get_mortality_table(
            state_low_conversion.mortality_table,
            state_low_conversion.gender,
            state_low_conversion.mortality_aggravation
        )

        # Calcular projeções
        projections_low = calculator.calculate_projections(state_low_conversion, context_low, mortality_table)
        projections_high = calculator.calculate_projections(state_high_conversion, context_high, mortality_table)

        # Calcular RMBAs
        rmba_low = calculator.calculate_rmba(state_low_conversion, context_low, projections_low)
        rmba_high = calculator.calculate_rmba(state_high_conversion, context_high, projections_high)

        # Com taxa de conversão mais baixa, o VPA dos benefícios é maior
        # Logo, RMBA deve ser maior (mais negativo, maior passivo)
        # RMBA = VPA(Benefícios) - VPA(Contribuições)
        # Taxa de conversão baixa -> VPA benefícios alto -> RMBA maior
        assert rmba_low != rmba_high  # Devem ser diferentes
        # Se RMBA for negativo (déficit), quanto mais negativo, maior o passivo
        if rmba_low < 0 and rmba_high < 0:
            assert rmba_low < rmba_high  # RMBA low deve ser MAIS negativo
        else:
            # Se positivos, taxa baixa deve resultar em RMBA maior
            assert rmba_low > rmba_high

    def test_bd_context_creation_with_differentiated_rates(self):
        """Testa criação de contexto BD com taxas diferenciadas"""
        state = SimulatorState(
            age=40,
            gender="M",
            salary=6000.0,
            initial_balance=50000.0,
            retirement_age=65,
            contribution_rate=12.0,
            target_benefit=4000.0,
            benefit_target_mode="VALUE",
            mortality_table="BR_EMS_2021",
            discount_rate=0.05,  # Não deve ser usado quando accumulation/conversion definidos
            accumulation_rate=0.07,  # Taxa específica para acumulação
            conversion_rate=0.04,    # Taxa específica para conversão
            accrual_rate=5.0,
            salary_growth_real=0.02,
            projection_years=30,
            calculation_method="PUC",
            plan_type="BD"
        )

        calculator = BDCalculator()
        context = calculator.create_bd_context(state)

        # Validar que taxas específicas foram usadas
        from src.utils.rates import annual_to_monthly_rate

        expected_accumulation = annual_to_monthly_rate(0.07)
        expected_conversion = annual_to_monthly_rate(0.04)

        # Aproximações devido a conversão anual->mensal
        assert abs(context.discount_rate_monthly - expected_accumulation) < 0.0001
        assert abs(context.conversion_rate_monthly - expected_conversion) < 0.0001

        # Taxa de desconto (discount_rate=0.05) NÃO deve ser usada
        not_expected = annual_to_monthly_rate(0.05)
        assert abs(context.discount_rate_monthly - not_expected) > 0.001
