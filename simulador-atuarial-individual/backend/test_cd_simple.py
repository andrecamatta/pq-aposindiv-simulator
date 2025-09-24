#!/usr/bin/env python3
"""
Teste simples para verificar cálculos CD
"""

import sys
import os
sys.path.append('src')

from src.models.participant import SimulatorState, CalculationMethod, PlanType, BenefitTargetMode, Gender, PaymentTiming
from src.core.actuarial_engine import ActuarialEngine
import json

def test_cd_calculation():
    print("🧪 Testando cálculo CD simples...")

    # Verificar se enum CD está disponível
    try:
        print(f"CalculationMethod.CD = {CalculationMethod.CD}")
        print(f"PlanType.CD = {PlanType.CD}")
    except AttributeError as e:
        print(f"❌ Erro no enum: {e}")
        return False

    # Criar estado CD
    try:
        state = SimulatorState(
            age=30,
            gender=Gender.MALE,
            salary=8000.0,
            plan_type=PlanType.CD,

            # Campos obrigatórios
            initial_balance=50000.0,
            benefit_target_mode=BenefitTargetMode.VALUE,
            target_benefit=4000.0,
            accrual_rate=0.06,
            retirement_age=65,
            contribution_rate=8.0,

            # CD específicos
            accumulation_rate=0.06,
            conversion_rate=0.04,

            # Base atuarial
            mortality_table="BR_EMS_2021",
            mortality_aggravation=0.0,
            discount_rate=0.05,
            salary_growth_real=0.01,

            # Config
            payment_timing=PaymentTiming.POSTECIPADO,
            salary_months_per_year=13,
            benefit_months_per_year=13,
            projection_years=40,
            calculation_method=CalculationMethod.CD
        )
        print(f"✅ Estado CD criado")
        print(f"   - plan_type: {state.plan_type}")
        print(f"   - derived_plan_type: {state.derived_plan_type}")
        print(f"   - calculation_method: {state.calculation_method}")

    except Exception as e:
        print(f"❌ Erro criando estado: {e}")
        return False

    # Testar cálculo
    try:
        engine = ActuarialEngine()
        results = engine.calculate_individual_simulation(state)

        print(f"✅ Cálculo CD executado")

        # Verificar campos disponíveis
        result_dict = results.model_dump()
        print("   - Campos disponíveis:")
        for key, value in result_dict.items():
            if value not in [None, 0.0, [], {}] and not key.startswith('sensitivity'):
                print(f"     {key}: {value}")

        # Verificar fase de aposentadoria
        if results.projected_benefits and len(results.projected_benefits) > 420:  # Após 35 anos
            retirement_benefits = results.projected_benefits[420:430]  # Primeiros 10 meses de aposentadoria
            print(f"   - Benefícios nos primeiros meses de aposentadoria: {retirement_benefits[:5]}")
        elif results.projected_benefits:
            print(f"   - Total de meses projetados: {len(results.projected_benefits)}")
            print(f"   - Últimos 5 valores: {results.projected_benefits[-5:]}")

        return True

    except Exception as e:
        print(f"❌ Erro no cálculo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cd_calculation()
    print(f"\n{'✅ SUCESSO' if success else '❌ FALHA'}")
    sys.exit(0 if success else 1)