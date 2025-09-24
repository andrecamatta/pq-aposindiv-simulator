#!/usr/bin/env python3

import requests
import json

# Teste rápido da API CD
def test_cd_api():
    url = "http://localhost:8000/calculate"

    # Estado CD básico baseado no default-state
    cd_state = {
        "plan_type": "CD",
        "calculation_method": "CD",
        "age": 30,
        "gender": "M",
        "salary": 8000.0,
        "initial_balance": 0.0,
        "benefit_target_mode": "VALUE",
        "target_benefit": 5000.0,
        "target_replacement_rate": None,
        "accrual_rate": 5.0,
        "retirement_age": 65,
        "contribution_rate": 8.0,
        "mortality_table": "BR_EMS_2021",
        "discount_rate": 0.05,
        "salary_growth_real": 0.01,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "admin_fee_rate": 0.015,
        "loading_fee_rate": 0.0,
        "payment_timing": "postecipado",
        "salary_months_per_year": 13,
        "benefit_months_per_year": 13,
        "projection_years": 40,
        "conversion_rate": 0.045,
        "mortality_aggravation": 0,
        "cd_conversion_mode": "ACTUARIAL"
    }

    try:
        print("Enviando request CD...")
        response = requests.post(url, json=cd_state)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Sucesso!")
            print(f"Monthly income CD: {result.get('monthly_income_cd', 'N/A')}")
            print(f"Has actuarial scenario: {bool(result.get('actuarial_scenario'))}")
            print(f"Has desired scenario: {bool(result.get('desired_scenario'))}")

            # Verificar se os cenários têm dados
            if result.get('actuarial_scenario'):
                act_scenario = result['actuarial_scenario']
                print(f"Actuarial monthly income: {act_scenario.get('monthly_income', 'N/A')}")
                print(f"Actuarial has projections: {bool(act_scenario.get('projections'))}")

                # Verificar saldos aos 65 anos
                if act_scenario.get('projections') and act_scenario['projections'].get('reserves'):
                    reserves = act_scenario['projections']['reserves']
                    ages = act_scenario['projections'].get('projection_ages', [])
                    retirement_idx = None
                    for i, age in enumerate(ages):
                        if age >= 65:
                            retirement_idx = i
                            break
                    if retirement_idx is not None and retirement_idx < len(reserves):
                        print(f"Actuarial saldo aos 65 anos (idx {retirement_idx}): R$ {reserves[retirement_idx]:,.2f}")

            if result.get('desired_scenario'):
                des_scenario = result['desired_scenario']
                print(f"Desired monthly income: {des_scenario.get('monthly_income', 'N/A')}")
                print(f"Desired has projections: {bool(des_scenario.get('projections'))}")

                # Verificar saldos aos 65 anos
                if des_scenario.get('projections') and des_scenario['projections'].get('reserves'):
                    reserves = des_scenario['projections']['reserves']
                    ages = des_scenario['projections'].get('projection_ages', [])
                    retirement_idx = None
                    for i, age in enumerate(ages):
                        if age >= 65:
                            retirement_idx = i
                            break
                    if retirement_idx is not None and retirement_idx < len(reserves):
                        print(f"Desired saldo aos 65 anos (idx {retirement_idx}): R$ {reserves[retirement_idx]:,.2f}")
        else:
            print("❌ Erro!")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_cd_api()