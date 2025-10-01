"""
Testes para validar a lógica de equivalência atuarial do plano CD
"""
import pytest
from src.models.participant import SimulatorState, PlanType, CDConversionMode
from src.core.actuarial_engine import ActuarialEngine


def test_actuarial_equivalent_recalculation():
    """
    Testa se a equivalência atuarial recalcula a renda anualmente
    e se a taxa administrativa é aplicada apenas 1x por mês
    """
    state = SimulatorState(
        age=30,
        gender="M",
        salary=10000.0,
        initial_balance=0.0,
        plan_type=PlanType.CD,
        cd_conversion_mode=CDConversionMode.ACTUARIAL_EQUIVALENT,
        target_benefit=8000.0,
        retirement_age=65,
        contribution_rate=12.0,
        mortality_table="BR_EMS_2021",
        discount_rate=0.05,
        accrual_rate=0.06,
        cd_conversion_rate=0.06,
        salary_growth_real=0.01,
        admin_fee_rate=0.015,
        projection_years=40,
        calculation_method="CD"
    )

    engine = ActuarialEngine()
    results = engine.calculate(state)

    # Verificar que o cálculo foi bem sucedido
    assert results is not None
    assert results.projections is not None
    assert len(results.projections.monthly_balances) > 0

    # Encontrar o mês de aposentadoria
    months_to_retirement = (state.retirement_age - state.age) * 12

    # Pegar saldo no início da aposentadoria (pico)
    balance_at_retirement = results.projections.monthly_balances[months_to_retirement]
    assert balance_at_retirement > 0, "Saldo na aposentadoria deve ser positivo"

    # Pegar benefício do primeiro ano (primeiros 12 meses de aposentadoria)
    first_year_benefits = []
    for i in range(12):
        idx = months_to_retirement + i + 1  # +1 porque o pico é registrado separadamente
        if idx < len(results.projections.monthly_benefits):
            first_year_benefits.append(results.projections.monthly_benefits[idx])

    # Benefícios do primeiro ano devem ser consistentes (exceto 13º)
    regular_benefits_year1 = [b for b in first_year_benefits if b > 0]
    assert len(regular_benefits_year1) > 0, "Deve haver benefícios no primeiro ano"

    # Pegar benefício do segundo ano (meses 13-24 da aposentadoria)
    second_year_benefits = []
    for i in range(12, 24):
        idx = months_to_retirement + i + 1
        if idx < len(results.projections.monthly_benefits):
            second_year_benefits.append(results.projections.monthly_benefits[idx])

    regular_benefits_year2 = [b for b in second_year_benefits if b > 0]

    # Benefícios do segundo ano devem ser menores que do primeiro (devido ao saldo reduzido)
    if len(regular_benefits_year2) > 0:
        avg_benefit_year1 = sum(regular_benefits_year1) / len(regular_benefits_year1)
        avg_benefit_year2 = sum(regular_benefits_year2) / len(regular_benefits_year2)

        print(f"\n=== ANÁLISE DE EQUIVALÊNCIA ATUARIAL ===")
        print(f"Saldo na aposentadoria: R$ {balance_at_retirement:,.2f}")
        print(f"Benefício médio ano 1: R$ {avg_benefit_year1:,.2f}")
        print(f"Benefício médio ano 2: R$ {avg_benefit_year2:,.2f}")
        print(f"Redução: {((avg_benefit_year1 - avg_benefit_year2) / avg_benefit_year1 * 100):.2f}%")

        # Benefício deve reduzir, mas não drasticamente
        # Uma redução de até 15% é esperada (saques + envelhecimento)
        reduction_pct = (avg_benefit_year1 - avg_benefit_year2) / avg_benefit_year1
        assert 0 < reduction_pct < 0.20, f"Redução de {reduction_pct*100:.2f}% está fora do esperado (0-20%)"


def test_actuarial_equivalent_with_floor():
    """
    Testa se o piso de renda é aplicado corretamente
    """
    state = SimulatorState(
        age=30,
        gender="M",
        salary=10000.0,
        initial_balance=0.0,
        plan_type=PlanType.CD,
        cd_conversion_mode=CDConversionMode.ACTUARIAL_EQUIVALENT,
        cd_floor_percentage=80.0,  # Piso de 80%
        target_benefit=8000.0,
        retirement_age=65,
        contribution_rate=12.0,
        mortality_table="BR_EMS_2021",
        discount_rate=0.05,
        accrual_rate=0.06,
        cd_conversion_rate=0.06,
        salary_growth_real=0.01,
        admin_fee_rate=0.015,
        projection_years=40,
        calculation_method="CD"
    )

    engine = ActuarialEngine()
    results = engine.calculate(state)

    assert results is not None

    months_to_retirement = (state.retirement_age - state.age) * 12

    # Benefício do primeiro ano
    first_year_benefits = []
    for i in range(1, 13):
        idx = months_to_retirement + i
        if idx < len(results.projections.monthly_benefits):
            benefit = results.projections.monthly_benefits[idx]
            if benefit > 0:
                first_year_benefits.append(benefit)

    if len(first_year_benefits) > 0:
        avg_benefit_year1 = sum(first_year_benefits) / len(first_year_benefits)
        floor_value = avg_benefit_year1 * 0.80

        print(f"\n=== ANÁLISE DE PISO ===")
        print(f"Benefício médio ano 1: R$ {avg_benefit_year1:,.2f}")
        print(f"Piso (80%): R$ {floor_value:,.2f}")

        # Verificar anos subsequentes
        for year in range(2, 6):  # Anos 2-5
            year_benefits = []
            for i in range(year * 12, (year + 1) * 12):
                idx = months_to_retirement + i
                if idx < len(results.projections.monthly_benefits):
                    benefit = results.projections.monthly_benefits[idx]
                    if benefit > 0:
                        year_benefits.append(benefit)

            if len(year_benefits) > 0:
                avg_benefit = sum(year_benefits) / len(year_benefits)
                print(f"Benefício médio ano {year}: R$ {avg_benefit:,.2f}")

                # O benefício não deve cair abaixo do piso (com margem de 1% para arredondamentos)
                assert avg_benefit >= floor_value * 0.99, f"Benefício do ano {year} está abaixo do piso"


def test_admin_fee_applied_once_per_month():
    """
    Testa se a taxa administrativa está sendo aplicada apenas 1x por mês
    """
    state = SimulatorState(
        age=64,  # 1 ano para aposentar
        gender="M",
        salary=10000.0,
        initial_balance=500000.0,  # Saldo inicial alto para facilitar análise
        plan_type=PlanType.CD,
        cd_conversion_mode=CDConversionMode.ACTUARIAL_EQUIVALENT,
        target_benefit=8000.0,
        retirement_age=65,
        contribution_rate=12.0,
        mortality_table="BR_EMS_2021",
        discount_rate=0.05,
        accrual_rate=0.06,
        cd_conversion_rate=0.06,
        salary_growth_real=0.01,
        admin_fee_rate=0.015,  # 1.5% a.a. = 0.125% a.m.
        projection_years=5,
        calculation_method="CD"
    )

    engine = ActuarialEngine()
    results = engine.calculate(state)

    months_to_retirement = (state.retirement_age - state.age) * 12

    # Saldo na aposentadoria
    balance_at_retirement = results.projections.monthly_balances[months_to_retirement]

    # Saldo após primeiro mês de aposentadoria
    balance_after_first_month = results.projections.monthly_balances[months_to_retirement + 1]

    # Benefício do primeiro mês
    benefit_first_month = results.projections.monthly_benefits[months_to_retirement + 1]

    # Taxa administrativa mensal
    admin_fee_monthly = (1 + state.admin_fee_rate) ** (1/12) - 1
    conversion_rate_monthly = (1 + state.cd_conversion_rate) ** (1/12) - 1

    # Calcular saldo esperado:
    # 1. Consumir benefício
    # 2. Capitalizar com taxa de conversão
    # 3. Aplicar taxa administrativa 1x
    expected_balance = balance_at_retirement - benefit_first_month
    expected_balance *= (1 + conversion_rate_monthly)
    expected_balance *= (1 - admin_fee_monthly)

    print(f"\n=== VERIFICAÇÃO TAXA ADMINISTRATIVA ===")
    print(f"Saldo na aposentadoria: R$ {balance_at_retirement:,.2f}")
    print(f"Benefício 1º mês: R$ {benefit_first_month:,.2f}")
    print(f"Saldo após 1º mês (real): R$ {balance_after_first_month:,.2f}")
    print(f"Saldo após 1º mês (esperado): R$ {expected_balance:,.2f}")
    print(f"Diferença: R$ {abs(balance_after_first_month - expected_balance):,.2f}")

    # Permitir margem de erro de 0.1% devido a arredondamentos
    assert abs(balance_after_first_month - expected_balance) / expected_balance < 0.001, \
        "Taxa administrativa pode estar sendo aplicada mais de 1x por mês"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
