"""
Testes Fumaça para Cálculos Atuariais
Verifica se os cálculos principais produzem resultados consistentes
"""
import pytest
import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.actuarial_engine import ActuarialEngine
from src.core.vpa_calculator import VPACalculator
from src.utils.rates import annual_to_monthly_rate, monthly_to_annual_rate
from src.models.participant import SimulatorState


def test_bd_calculation_consistency():
    """Testa se cálculo BD produz valores consistentes"""
    state = SimulatorState(
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
    
    engine = ActuarialEngine(state)
    results = engine.calculate()
    
    # Verifica se valores fazem sentido
    assert results.rmba > 0, "RMBA deve ser positivo"
    assert results.total_contributions > 0, "Total de contribuições deve ser positivo"
    assert abs(results.deficit_surplus) < 1e6, "Déficit/Superávit deve estar em range razoável"
    
    # Verifica se arrays têm tamanhos corretos
    months = (state.retirement_age - state.age) * 12
    assert len(results.cash_flows) > 0, "Deve ter fluxos de caixa"
    assert len(results.accumulated_reserves) > 0, "Deve ter reservas acumuladas"
    
    # Verifica consistência básica
    assert results.sustainable_replacement_ratio >= 0, "Taxa de reposição deve ser >= 0"
    assert results.sustainable_replacement_ratio <= 200, "Taxa de reposição deve ser <= 200%"


def test_cd_calculation_consistency():
    """Testa se cálculo CD produz valores consistentes"""
    state = SimulatorState(
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
    
    engine = ActuarialEngine(state)
    results = engine.calculate()
    
    # Verifica valores CD específicos
    assert results.accumulated_balance_retirement > state.initial_balance, \
        "Saldo na aposentadoria deve ser maior que saldo inicial"
    assert results.estimated_benefit > 0, "Benefício estimado deve ser positivo"
    
    # Verifica se cálculo atuarial faz sentido
    if state.cd_conversion_mode == "ACTUARIAL":
        # Benefício atuarial não pode ser absurdamente alto
        benefit_ratio = results.estimated_benefit / state.salary
        assert benefit_ratio < 5.0, "Benefício não deve ser mais que 5x o salário"
    
    # Verifica arrays de acumulação
    assert len(results.contribution_phase_balances) > 0, "Deve ter saldos na fase contributiva"
    assert results.contribution_phase_balances[-1] == results.accumulated_balance_retirement, \
        "Último saldo deve ser igual ao saldo na aposentadoria"


def test_rate_conversions():
    """Testa conversões de taxas"""
    # Taxa anual de 6%
    annual_rate = 0.06
    monthly_rate = annual_to_monthly_rate(annual_rate)
    
    # Taxa mensal deve ser menor que anual/12 (juros compostos)
    assert monthly_rate < annual_rate / 12
    assert monthly_rate > 0
    
    # Conversão reversa deve ser próxima ao original
    back_to_annual = monthly_to_annual_rate(monthly_rate)
    assert abs(back_to_annual - annual_rate) < 0.0001
    
    # Testa casos especiais
    assert annual_to_monthly_rate(0) == 0
    assert monthly_to_annual_rate(0) == 0
    
    # Taxa negativa (deflação)
    negative_annual = -0.02
    negative_monthly = annual_to_monthly_rate(negative_annual)
    assert negative_monthly < 0
    assert negative_monthly > negative_annual / 12


def test_vpa_calculator_equilibrium():
    """Testa se VPA Calculator encontra ponto de equilíbrio"""
    state = SimulatorState(
        age=40,
        gender="M",
        salary=8000.0,
        retirement_age=65,
        contribution_rate=10.0,
        target_benefit=5000.0,
        mortality_table="BR_EMS_2021",
        discount_rate=0.06,
        plan_type="BD"
    )
    
    calculator = VPACalculator(state)
    
    # Testa busca de contribuição de equilíbrio
    equilibrium_rate = calculator.find_equilibrium_contribution_rate(
        target_benefit=state.target_benefit
    )
    
    assert equilibrium_rate > 0, "Taxa de equilíbrio deve ser positiva"
    assert equilibrium_rate < 100, "Taxa de equilíbrio deve ser < 100%"
    
    # Verifica se realmente equilibra
    state_test = state.model_copy()
    state_test.contribution_rate = equilibrium_rate
    engine = ActuarialEngine(state_test)
    results = engine.calculate()
    
    # Déficit deve ser próximo de zero
    assert abs(results.deficit_surplus) < state.salary, \
        "Com taxa de equilíbrio, déficit deve ser próximo de zero"


def test_mortality_table_impact():
    """Testa se diferentes tábuas de mortalidade produzem resultados diferentes"""
    base_state = SimulatorState(
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
    
    # Calcula com primeira tábua
    engine1 = ActuarialEngine(base_state)
    results1 = engine1.calculate()
    
    # Calcula com outra tábua
    state2 = base_state.model_copy()
    state2.mortality_table = "AT_2000"
    engine2 = ActuarialEngine(state2)
    results2 = engine2.calculate()
    
    # RMBAs devem ser diferentes
    assert results1.rmba != results2.rmba, \
        "Diferentes tábuas devem produzir RMBAs diferentes"
    
    # Ambos devem ser valores razoáveis
    assert results1.rmba > 0 and results2.rmba > 0
    assert results1.rmba < 10_000_000 and results2.rmba < 10_000_000


def test_edge_cases():
    """Testa casos extremos"""
    # Pessoa muito jovem
    young_state = SimulatorState(
        age=18,
        gender="M",
        salary=2000.0,
        retirement_age=65,
        contribution_rate=5.0,
        target_benefit=1000.0,
        mortality_table="BR_EMS_2021",
        discount_rate=0.06
    )
    
    engine = ActuarialEngine(young_state)
    results = engine.calculate()
    assert results.rmba > 0
    assert len(results.cash_flows) > 500  # Muitos meses até aposentadoria
    
    # Pessoa próxima da aposentadoria
    old_state = SimulatorState(
        age=64,
        gender="F",
        salary=10000.0,
        retirement_age=65,
        contribution_rate=20.0,
        target_benefit=8000.0,
        mortality_table="AT_2000",
        discount_rate=0.04
    )
    
    engine = ActuarialEngine(old_state)
    results = engine.calculate()
    assert results.rmba > 0
    assert len(results.cash_flows) >= 12  # Pelo menos 1 ano
    
    # Salário muito alto
    high_salary_state = SimulatorState(
        age=45,
        gender="M",
        salary=100000.0,
        retirement_age=60,
        contribution_rate=15.0,
        target_benefit=50000.0,
        mortality_table="BR_EMS_2021",
        discount_rate=0.05
    )
    
    engine = ActuarialEngine(high_salary_state)
    results = engine.calculate()
    assert results.rmba > 0
    assert results.total_contributions > 1_000_000  # Contribuições altas


def test_calculation_determinism():
    """Testa se cálculos são determinísticos (mesmo input = mesmo output)"""
    state = SimulatorState(
        age=40,
        gender="M",
        salary=7500.0,
        retirement_age=65,
        contribution_rate=11.0,
        target_benefit=4500.0,
        mortality_table="BR_EMS_2021",
        discount_rate=0.055
    )
    
    # Calcula duas vezes
    engine1 = ActuarialEngine(state)
    results1 = engine1.calculate()
    
    engine2 = ActuarialEngine(state)
    results2 = engine2.calculate()
    
    # Resultados devem ser idênticos
    assert results1.rmba == results2.rmba
    assert results1.deficit_surplus == results2.deficit_surplus
    assert results1.total_contributions == results2.total_contributions
    assert len(results1.cash_flows) == len(results2.cash_flows)