#!/usr/bin/env python3
"""
Debug Simples para testar manualmente se há problema no root finding
"""

import sys
import json
from pathlib import Path

def test_default_state_calculation():
    """Testa o cálculo padrão via API"""
    print("="*60)
    print("TESTE: ESTADO PADRÃO VIA API")  
    print("="*60)
    
    # Estado padrão igual ao main.py
    default_state = {
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
        "salary_growth_real": 0.02,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "admin_fee_rate": 0.01,
        "loading_fee_rate": 0.0,
        "payment_timing": "postecipado",
        "salary_months_per_year": 13,
        "benefit_months_per_year": 13,
        "projection_years": 40,
        "calculation_method": "PUC"
    }
    
    print("Estado padrão:")
    print(f"  - Idade: {default_state['age']} anos")
    print(f"  - Salário: R$ {default_state['salary']:,.2f}/mês")
    print(f"  - Benefício: R$ {default_state['target_benefit']:,.2f}/mês")
    print(f"  - Contribuição: {default_state['contribution_rate']:.1f}%")
    
    return default_state

def test_manual_benefits(default_state):
    """Testa manualmente diferentes valores de benefício"""
    print("="*60)
    print("TESTE: BENEFÍCIOS MANUAIS")
    print("="*60)
    
    # Teste de diferentes benefícios
    test_benefits = [3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
    
    print("Testando benefícios diferentes:")
    results = {}
    
    for benefit in test_benefits:
        test_state = default_state.copy()
        test_state['target_benefit'] = benefit
        
        # Simular manualmente o cálculo (seria melhor via API mas vou usar lógica aproximada)
        # Contribuição total: 35 anos * 13 meses * 8% * R$ 8000 = R$ 2.912.000  
        # Com 5% a.a. de rendimento real: FV ≈ R$ 7.500.000
        # Benefício sustentável aproximado: R$ 7.500.000 / (20 anos * 13 meses) ≈ R$ 28.800/mês
        
        total_contrib = 35 * 13 * 0.08 * 8000  # R$ 2.912.000
        
        # Estimativa muito simples de déficit/superávit
        # Se benefício for maior que ~R$ 11.000, provavelmente déficit
        # Se menor, provavelmente superávit
        
        estimated_sustainable = 11000  # Estimativa grosseira
        estimated_deficit = (benefit - estimated_sustainable) * 20 * 13  # 20 anos de diferença
        
        results[benefit] = estimated_deficit
        
        print(f"  - R$ {benefit:,.0f}/mês → Déficit estimado: R$ {estimated_deficit:,.0f}")
        
        if abs(estimated_deficit) < 50000:  # Próximo de sustentável
            print(f"    *** PRÓXIMO AO SUSTENTÁVEL ***")
    
    # Encontrar o mais próximo de zero
    best_benefit = min(results.keys(), key=lambda x: abs(results[x]))
    print(f"\nMelhor estimativa: R$ {best_benefit:,.0f}/mês com déficit de R$ {results[best_benefit]:,.0f}")
    
    return best_benefit

def main():
    """Função principal"""
    print("DEBUG SIMPLES - TESTE MANUAL DE BENEFÍCIO SUSTENTÁVEL")
    print("=" * 80)
    
    # Teste 1: Estado padrão
    default_state = test_default_state_calculation()
    
    # Teste 2: Benefícios manuais
    best_manual = test_manual_benefits(default_state)
    
    print("="*80)
    print("CONCLUSÕES:")
    print("="*80)
    print(f"1. Estado padrão tem benefício de R$ {default_state['target_benefit']:,.0f}/mês")
    print(f"2. Benefício sustentável estimado manualmente: R$ {best_manual:,.0f}/mês")
    print(f"3. Se sugestão atual é R$ 5.300, isso sugere:")
    
    if best_manual > 5300:
        print(f"   - Sugestão está BAIXA (deveria ser ~R$ {best_manual:,.0f})")
    elif best_manual < 5300:
        print(f"   - Sugestão está ALTA (deveria ser ~R$ {best_manual:,.0f})")
    else:
        print(f"   - Sugestão parece razoável")
    
    print("\nIMPORTANTE: Estes são cálculos aproximados.")
    print("Para debug real, precisa executar o engine atuarial completo.")

if __name__ == "__main__":
    main()