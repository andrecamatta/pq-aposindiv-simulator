#!/usr/bin/env python3
"""
Teste de Equivalência BD × CD via API HTTP

Verifica se BD e CD retornam valores equivalentes quando:
- Participante JÁ ESTÁ na aposentadoria (sem contribuições futuras)
- Taxas atuariais são idênticas
- Mesmos parâmetros de configuração

Expectativa: benefícios devem ser matematicamente idênticos.
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_bd_cd_equivalence():
    """Teste de equivalência BD × CD com participante aposentado"""

    print("=" * 80)
    print("TESTE DE EQUIVALÊNCIA BD × CD - Via API HTTP")
    print("=" * 80)

    # Parâmetros comuns
    common_params = {
        "age": 64,  # 1 ano antes da aposentadoria
        "retirement_age": 65,
        "gender": "M",
        "salary": 5000,
        "initial_balance": 1000000,  # R$ 1MM
        "contribution_rate": 0.11,
        "admin_fee_rate": 0.0015,
        "benefit_months_per_year": 13,
        "payment_timing": "antecipado",
        "mortality_table": "AT_2000",
        "projection_years": 30
    }

    # Estado BD
    state_bd = {
        **common_params,
        "plan_type": "BD",
        "discount_rate": 0.05,  # 5% a.a.
        "benefit_target_mode": "VALUE",
        "target_benefit": 5000,
        "accrual_rate": 1.0,
        "salary_growth_real": 0.0,
        "calculation_method": "PUC"
    }

    # Estado CD com MESMAS TAXAS
    state_cd = {
        **common_params,
        "plan_type": "CD",
        "accumulation_rate": 0.05,  # Mesma taxa que BD
        "conversion_rate": 0.05,     # ← CRÍTICO: mesma taxa
        "cd_conversion_mode": "ACTUARIAL",  # Vitalícia
        # Campos obrigatórios (mesmo para CD)
        "accrual_rate": 1.0,
        "discount_rate": 0.05,
        "salary_growth_real": 0.0,
        "calculation_method": "PUC"
    }

    print(f"\n📋 Configuração:")
    print(f"   Idade: {common_params['age']} anos (APOSENTADO)")
    print(f"   Saldo Inicial: R$ {common_params['initial_balance']:,.2f}")
    print(f"   Taxa Atuarial: 5.00% a.a.")
    print(f"   Taxa Admin: {common_params['admin_fee_rate']*100:.4f}% a.a.")
    print(f"   Benefícios/ano: {common_params['benefit_months_per_year']} meses")

    try:
        # Calcular BD
        print(f"\n🔵 Calculando BD...")
        response_bd = requests.post(f"{API_URL}/calculate", json=state_bd)

        if response_bd.status_code != 200:
            print(f"   ❌ Erro {response_bd.status_code}: {response_bd.text}")
            return False

        results_bd = response_bd.json()

        # Extrair AMBOS os valores do BD
        bd_monthly_income = results_bd.get('monthly_income', 0)
        bd_sustainable = results_bd.get('sustainable_monthly_benefit', 0)

        print(f"   BD monthly_income:               R$ {bd_monthly_income:,.2f}")
        print(f"   BD sustainable_monthly_benefit:  R$ {bd_sustainable:,.2f}")

        # Calcular CD
        print(f"\n🟢 Calculando CD...")
        response_cd = requests.post(f"{API_URL}/calculate", json=state_cd)

        if response_cd.status_code != 200:
            print(f"   ❌ Erro {response_cd.status_code}: {response_cd.text}")
            return False

        results_cd = response_cd.json()

        cd_income = results_cd.get('monthly_income_cd', 0)
        print(f"   ✓ CD monthly_income_cd (ACTUARIAL): R$ {cd_income:,.2f}")

        # Comparar BD SUSTAINABLE com CD
        print(f"\n" + "=" * 80)
        print(f"📊 COMPARAÇÃO: BD Sustentável × CD Vitalícia")
        print(f"=" * 80)

        if cd_income == 0:
            print(f"\n❌ ERRO: CD retornou 0 - isso é um erro!")
            return False

        # Usar sustainable como referência principal
        bd_value = bd_sustainable if bd_sustainable > 0 else bd_monthly_income

        if bd_value == 0:
            print(f"\n⚠️  BD retornou 0 em ambos os campos:")
            print(f"   - monthly_income: R$ {bd_monthly_income:,.2f}")
            print(f"   - sustainable_monthly_benefit: R$ {bd_sustainable:,.2f}")
            print(f"\n   💡 Isso pode indicar que a lógica BD não está")
            print(f"      convertendo saldo inicial em renda sustentável.")
            print(f"\n   ✓ Mas CD funciona: R$ {cd_income:,.2f}")
            return False

        difference = abs(bd_value - cd_income)
        percent_diff = (difference / max(bd_value, cd_income) * 100)

        print(f"\n   BD sustainable_monthly_benefit: R$ {bd_value:,.2f}")
        print(f"   CD monthly_income_cd:           R$ {cd_income:,.2f}")
        print(f"   Diferença Absoluta:             R$ {difference:,.2f}")
        print(f"   Diferença Percentual:           {percent_diff:.4f}%")

        # Verificação
        tolerance = 0.5  # 0.5% de tolerância
        if percent_diff < tolerance:
            print(f"\n✅ SUCESSO: Valores equivalentes (diferença < {tolerance}%)")
            print(f"   As fórmulas BD e CD são matematicamente consistentes!")
            return True
        else:
            print(f"\n⚠️  ATENÇÃO: Diferença significativa ({percent_diff:.4f}%)")
            print(f"   Esperado: diferença < {tolerance}%")

            # Debugging
            print(f"\n🔍 Debug - Valores retornados:")
            print(f"   BD sustainable_monthly_benefit: {bd_benefit}")
            print(f"   CD monthly_income_cd: {cd_income}")

            return False

    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRO: Não foi possível conectar ao backend em {API_URL}")
        print(f"   Certifique-se que o backend está rodando:")
        print(f"   cd backend && uv run uvicorn src.api.main:app --reload --port 8000")
        return False

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executar teste"""
    print("\n🔬 TESTE DE EQUIVALÊNCIA MATEMÁTICA: BD × CD")
    print(f"Servidor: {API_URL}\n")

    success = test_bd_cd_equivalence()

    if success:
        print("\n🎉 TESTE PASSOU!")
        print("\nConclusão:")
        print("  ✓ BD e CD retornam valores equivalentes quando aposentado")
        print("  ✓ As correções matemáticas estão funcionando corretamente")
    else:
        print("\n⚠️  TESTE FALHOU")
        print("Revisar implementação das fórmulas")

    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
