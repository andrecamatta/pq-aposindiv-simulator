#!/usr/bin/env python3
"""
Teste de equivalência entre CD Renda Vitalícia e BD Benefício Sustentável

Valida que, para um mesmo saldo na aposentadoria, ambos os métodos
retornam o mesmo benefício mensal.
"""

import sys
import numpy as np
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from src.models.participant import (
    SimulatorState, CDConversionMode, PlanType,
    Gender, CalculationMethod
)
from src.core.cd_calculator import CDCalculator
from src.core.bd_calculator import BDCalculator
from src.core.mortality_tables import get_mortality_table
from src.core.context_manager import ContextManager


def test_cd_bd_equivalence():
    """
    Testa equivalência entre CD e BD para mesmo saldo na aposentadoria
    """
    print("=" * 80)
    print("TESTE DE EQUIVALÊNCIA: CD RENDA VITALÍCIA vs BD BENEFÍCIO SUSTENTÁVEL")
    print("=" * 80)

    # Configuração de teste: pessoa já aposentada com saldo
    test_state = SimulatorState(
        age=40.0,
        retirement_age=65.0,
        salary=8000.0,
        initial_balance=0.0,
        contribution_rate=0.0,
        discount_rate=0.05,  # 5% em decimal
        projection_years=30.0,
        mortality_table="BR-EMS",
        gender=Gender.MALE,
        benefit_months_per_year=13,
        salary_months_per_year=12,
        admin_fee_rate=0.0015,  # 0.15% em decimal
        accrual_rate=1.0,
        salary_growth_real=0.0,
        calculation_method=CalculationMethod.PUC,
    )

    # Simular pessoa já aposentada com saldo
    test_balance_at_retirement = 500_000.0

    print(f"\n📊 Parâmetros do Teste:")
    print(f"  • Idade atual: {test_state.age} anos")
    print(f"  • Idade de aposentadoria: {test_state.retirement_age} anos")
    print(f"  • Saldo na aposentadoria (teste): R$ {test_balance_at_retirement:,.2f}")
    print(f"  • Taxa de desconto: {test_state.discount_rate}% a.a.")
    print(f"  • Taxa administrativa: {test_state.admin_fee_rate}% a.a.")
    print(f"  • Benefícios por ano: {test_state.benefit_months_per_year}")
    print(f"  • Tábua: Sintética (Gompertz-Makeham)")

    # Criar tábua de mortalidade sintética para teste
    # Probabilidades crescentes de mortalidade por idade
    mortality_table = np.array([
        0.0001 * (1.08 ** (age - 18)) if age < 110 else 1.0
        for age in range(111)
    ])
    # Limitar valores entre 0 e 1
    mortality_table = np.clip(mortality_table, 0.0, 1.0)

    # ========================================================================
    # TESTE 1: CD Renda Vitalícia
    # ========================================================================
    print("\n" + "─" * 80)
    print("1️⃣  TESTE CD - RENDA VITALÍCIA (ACTUARIAL)")
    print("─" * 80)

    cd_state = test_state.model_copy()
    cd_state.plan_type = PlanType.CD
    cd_state.cd_conversion_mode = CDConversionMode.ACTUARIAL

    cd_calculator = CDCalculator()
    cd_context = cd_calculator.create_cd_context(cd_state)

    # Debug: verificar parâmetros do contexto
    print(f"  CD Context:")
    print(f"    • discount_rate_monthly: {cd_context.discount_rate_monthly:.6f}")
    print(f"    • admin_fee_monthly: {cd_context.admin_fee_monthly:.6f}")
    print(f"    • benefit_months_per_year: {cd_context.benefit_months_per_year}")
    print(f"    • payment_timing: {cd_context.payment_timing}")

    cd_monthly_income = cd_calculator.calculate_monthly_income(
        cd_state,
        cd_context,
        test_balance_at_retirement,
        mortality_table
    )

    print(f"\n✓ Benefício mensal CD: R$ {cd_monthly_income:,.2f}")

    # ========================================================================
    # TESTE 2: BD Benefício Sustentável
    # ========================================================================
    print("\n" + "─" * 80)
    print("2️⃣  TESTE BD - BENEFÍCIO SUSTENTÁVEL")
    print("─" * 80)

    # Usar calculate_sustainable_benefit diretamente
    from src.core.calculations.vpa_calculations import calculate_sustainable_benefit
    from src.core.projection_builder import ProjectionBuilder

    bd_state = test_state.model_copy()
    bd_state.plan_type = PlanType.BD

    bd_calculator = BDCalculator()
    bd_context = bd_calculator.create_bd_context(bd_state)

    # Debug: verificar parâmetros do contexto
    print(f"  BD Context:")
    print(f"    • discount_rate_monthly: {bd_context.discount_rate_monthly:.6f}")
    print(f"    • admin_fee_monthly: {bd_context.admin_fee_monthly:.6f}")
    print(f"    • benefit_months_per_year: {bd_context.benefit_months_per_year}")
    print(f"    • payment_timing: {bd_context.payment_timing}")

    # Usar mesma função do CD para gerar survival_probs desde aposentadoria
    # Isso garante equivalência matemática
    from src.core.constants import MAX_ANNUITY_MONTHS, MAX_AGE_LIMIT

    # Calcular survival probs desde idade de aposentadoria (como CD faz)
    max_months_from_retirement = min(MAX_ANNUITY_MONTHS, int((MAX_AGE_LIMIT - test_state.retirement_age) * 12))

    survival_probs_from_retirement = []
    cumulative_survival = 1.0
    for month in range(max_months_from_retirement):
        age_years = test_state.retirement_age + (month / 12)
        age_index = int(age_years)

        if age_index < len(mortality_table):
            q_x_annual = mortality_table[age_index]
            q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
            p_x_monthly = 1 - q_x_monthly
            cumulative_survival *= p_x_monthly
            survival_probs_from_retirement.append(cumulative_survival)
        else:
            survival_probs_from_retirement.append(0.0)
            cumulative_survival = 0.0

    print(f"  • Survival probs length (from retirement): {len(survival_probs_from_retirement)}")
    print(f"  • First 3 survival probs: {survival_probs_from_retirement[:3]}")

    # Calcular benefício sustentável (pessoa já aposentada, sem contribuições futuras)
    bd_monthly_income = calculate_sustainable_benefit(
        initial_balance=test_balance_at_retirement,
        vpa_contributions=0.0,  # Já aposentada, sem contribuições futuras
        monthly_survival_probs=survival_probs_from_retirement,
        discount_rate_monthly=bd_context.discount_rate_monthly,
        timing=bd_context.payment_timing,
        months_to_retirement=0,  # Já na aposentadoria
        benefit_months_per_year=bd_context.benefit_months_per_year,
        admin_fee_monthly=bd_context.admin_fee_monthly
    )

    print(f"\n✓ Benefício mensal BD: R$ {bd_monthly_income:,.2f}")

    # ========================================================================
    # COMPARAÇÃO
    # ========================================================================
    print("\n" + "=" * 80)
    print("📈 RESULTADO DA COMPARAÇÃO")
    print("=" * 80)

    print(f"\nCD Renda Vitalícia:      R$ {cd_monthly_income:,.2f}")
    print(f"BD Benefício Sustentável: R$ {bd_monthly_income:,.2f}")

    diff = cd_monthly_income - bd_monthly_income
    diff_pct = (diff / cd_monthly_income * 100) if cd_monthly_income > 0 else 0

    print(f"\nDiferença absoluta:       R$ {abs(diff):,.2f}")
    print(f"Diferença percentual:     {abs(diff_pct):.4f}%")

    # Tolerância de 0.01% para erros numéricos
    TOLERANCE_PCT = 0.01

    if abs(diff_pct) <= TOLERANCE_PCT:
        print(f"\n✅ SUCESSO: Diferença dentro da tolerância ({TOLERANCE_PCT}%)")
        print("   Os cálculos estão matematicamente equivalentes!")
        return True
    else:
        print(f"\n❌ FALHA: Diferença acima da tolerância ({TOLERANCE_PCT}%)")
        print("   Há inconsistência entre os métodos de cálculo!")
        return False


if __name__ == "__main__":
    success = test_cd_bd_equivalence()
    sys.exit(0 if success else 1)
