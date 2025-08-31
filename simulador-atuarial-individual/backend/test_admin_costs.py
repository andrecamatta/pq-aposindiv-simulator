import json
import requests

# Estado teste com custos administrativos
test_state = {
    "age": 30,
    "gender": "M",
    "salary": 8000.0,
    "initial_balance": 10000.0,
    "benefit_target_mode": "VALUE",
    "target_benefit": 5000.0,
    "accrual_rate": 5.0,
    "retirement_age": 65,
    "contribution_rate": 10.0,
    "mortality_table": "BR_EMS_2021",
    "discount_rate": 0.06,
    "salary_growth_real": 0.02,
    "benefit_indexation": "none",
    "contribution_indexation": "salary",
    "use_ettj": False,
    "admin_fee_rate": 0.02,  # 2% ao ano sobre saldo
    "loading_fee_rate": 0.05,  # 5% de carregamento
    "payment_timing": "postecipado",
    "salary_months_per_year": 13,
    "benefit_months_per_year": 13,
    "projection_years": 40,
    "calculation_method": "PUC"
}

try:
    response = requests.post("http://localhost:8001/calculate", json=test_state)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cálculo realizado com sucesso!")
        print(f"RMBA: R$ {result['rmba']:,.2f}")
        print(f"Déficit/Superávit: R$ {result['deficit_surplus']:,.2f}")
        print(f"Total de contribuições: R$ {result['total_contributions']:,.2f}")
        print(f"Taxa de reposição sustentável: {result['sustainable_replacement_ratio']:.1f}%")
        print(f"Reserva final: R$ {result['accumulated_reserves'][-1]:,.2f}")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Erro na requisição: {e}")
