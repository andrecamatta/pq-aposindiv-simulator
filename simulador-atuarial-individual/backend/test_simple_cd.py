import requests
import json
import time

def test_cd_calculation():
    """Testa um cálculo CD simples"""
    request_data = {
        "age": 30,
        "gender": "M",
        "salary": 8000.0,
        "plan_type": "CD",
        "mortality_table": "BR_EMS_2021",
        "retirement_age": 65,
        "contribution_rate": 8.0,
        "target_benefit": 5000.0,
        "benefit_target_mode": "VALUE",
        "initial_balance": 0.0,
        "accumulation_rate": 5.0,
        "conversion_rate": 5.0,
        "admin_fee_rate": 1.5,
        "cd_conversion_mode": "ACTUARIAL"
    }

    try:
        print("Enviando requisição para cálculo CD...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/calculate",
            json=request_data,
            timeout=30
        )
        
        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cálculo CD bem-sucedido!")
            print(f"Tempo de resposta: {elapsed:.2f}s")

            if 'monthly_income' in result:
                print(f"Renda mensal: R$ {result['monthly_income']:,.2f}")
            if 'final_balance' in result:
                print(f"Saldo final: R$ {result['final_balance']:,.2f}")

            return True
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Timeout na requisição (>30s)")
        return False
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

if __name__ == "__main__":
    print("Testando cálculo CD simples...")
    success = test_cd_calculation()
    if success:
        print("\n🎉 Teste passou! Backend está funcionando.")
    else:
        print("\n💥 Teste falhou! Backend tem problemas.")
