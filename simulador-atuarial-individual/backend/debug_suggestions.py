#!/usr/bin/env python3
"""
Script de Debug para Sugestões Inteligentes
Testa o cenário padrão do frontend e debuga o root finding
"""

import sys
import logging
import json
from pathlib import Path

# Adicionar o backend ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.participant import SimulatorState, BenefitTargetMode, Gender, CalculationMethod, PlanType
from core.actuarial_engine import ActuarialEngine
from core.suggestions_engine import SuggestionsEngine
from models.suggestions import SuggestionsRequest
from utils.vpa import calculate_sustainable_benefit_with_engine

# Configurar logging para debug
logging.basicConfig(
    level=logging.INFO,  # Mudei para INFO para menos spam
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_default_state():
    """Cria estado padrão exato do frontend"""
    return SimulatorState(
        age=30,
        gender=Gender.MALE,
        salary=8000.0,
        initial_balance=0.0,
        benefit_target_mode=BenefitTargetMode.VALUE,
        target_benefit=5000.0,
        target_replacement_rate=None,
        accrual_rate=5.0,
        retirement_age=65,
        contribution_rate=8.0,
        mortality_table="BR_EMS_2021",
        discount_rate=0.05,
        salary_growth_real=0.02,
        benefit_indexation="none",
        contribution_indexation="salary",
        use_ettj=False,
        admin_fee_rate=0.01,
        loading_fee_rate=0.0,
        payment_timing="postecipado",
        salary_months_per_year=13,
        benefit_months_per_year=13,
        projection_years=40,
        calculation_method=CalculationMethod.PUC,
        plan_type=PlanType.BD
    )

def test_baseline_scenario():
    """Teste 1: Estabelecer linha base do problema"""
    print("="*60)
    print("TESTE 1: LINHA BASE DO CENÁRIO PADRÃO")
    print("="*60)
    
    # Criar estado padrão
    state = create_default_state()
    print(f"Estado padrão criado:")
    print(f"  - Idade: {state.age} anos")
    print(f"  - Salário: R$ {state.salary:,.2f}/mês")
    print(f"  - Benefício alvo: R$ {state.target_benefit:,.2f}/mês") 
    print(f"  - Contribuição: {state.contribution_rate:.1f}%")
    print(f"  - Aposentadoria: {state.retirement_age} anos")
    
    # Executar simulação
    engine = ActuarialEngine()
    results = engine.calculate_individual_simulation(state)
    
    print(f"RESULTADO DA SIMULAÇÃO:")
    print(f"  - Déficit/Superávit: R$ {results.deficit_surplus:,.2f}")
    print(f"  - Taxa Reposição: {results.replacement_ratio:.2f}%")
    
    if results.deficit_surplus > 0:
        print(f"  - STATUS: SUPERÁVIT de R$ {results.deficit_surplus:,.2f}")
    else:
        print(f"  - STATUS: DÉFICIT de R$ {abs(results.deficit_surplus):,.2f}")
        
    return state, results

def test_objective_function_manually(state, engine):
    """Teste 2: Testar função objetivo manualmente"""
    print("="*60)
    print("TESTE 2: FUNÇÃO OBJETIVO MANUAL")
    print("="*60)
    
    test_benefits = [4000, 4500, 5000, 5500, 6000, 6500, 7000, 8000, 9000, 10000]
    
    print("Testando função objetivo com diferentes benefícios:")
    for benefit in test_benefits:
        test_state = state.model_copy()
        test_state.target_benefit = float(benefit)
        test_state.benefit_target_mode = BenefitTargetMode.VALUE
        
        try:
            test_results = engine.calculate_individual_simulation(test_state)
            deficit = test_results.deficit_surplus
            print(f"  - R$ {benefit:,.0f}/mês → Déficit: R$ {deficit:,.2f}")
            
            if abs(deficit) < 100:  # Próximo de zero
                print(f"    *** POSSÍVEL BENEFÍCIO SUSTENTÁVEL: R$ {benefit:,.0f} ***")
                
        except Exception as e:
            print(f"  - R$ {benefit:,.0f}/mês → ERRO: {e}")

def test_current_suggestions(state):
    """Teste 3: Testar sugestões atuais"""
    print("="*60)
    print("TESTE 3: SUGESTÕES ATUAIS")
    print("="*60)
    
    suggestions_engine = SuggestionsEngine()
    request = SuggestionsRequest(state=state, max_suggestions=5)
    
    response = suggestions_engine.generate_suggestions(request)
    
    print(f"Sugestões geradas: {len(response.suggestions)}")
    for i, suggestion in enumerate(response.suggestions):
        print(f"  {i+1}. {suggestion.title}")
        print(f"     Ação: {suggestion.action}")
        print(f"     Valor: {suggestion.action_value}")
        print(f"     Descrição: {suggestion.description}")
        print(f"     Confiança: {suggestion.confidence:.2f}")
        
        # Se for sugestão de benefício sustentável, testar
        if suggestion.action in ['apply_sustainable_benefit', 'update_target_benefit']:
            print(f"     >>> TESTANDO EFICÁCIA DA SUGESTÃO:")
            test_state = state.model_copy()
            test_state.target_benefit = suggestion.action_value
            test_state.benefit_target_mode = BenefitTargetMode.VALUE
            
            engine = ActuarialEngine()
            test_results = engine.calculate_individual_simulation(test_state)
            residual_deficit = test_results.deficit_surplus
            
            print(f"     >>> Déficit residual: R$ {residual_deficit:,.2f}")
            if abs(residual_deficit) <= 50:
                print(f"     >>> ✅ SUGESTÃO EFICAZ (déficit residual < R$ 50)")
            else:
                print(f"     >>> ❌ SUGESTÃO INEFICAZ (déficit residual > R$ 50)")

def test_root_finding_debug(state):
    """Teste 4: Debug do root finding"""
    print("="*60)
    print("TESTE 4: DEBUG DO ROOT FINDING")
    print("="*60)
    
    engine = ActuarialEngine()
    
    print("Testando calculate_sustainable_benefit_with_engine...")
    
    try:
        sustainable_benefit = calculate_sustainable_benefit_with_engine(state, engine)
        print(f"Benefício sustentável calculado: R$ {sustainable_benefit:,.2f}")
        
        # Validar resultado
        test_state = state.model_copy()
        test_state.target_benefit = sustainable_benefit
        test_state.benefit_target_mode = BenefitTargetMode.VALUE
        
        validation_results = engine.calculate_individual_simulation(test_state)
        validation_deficit = validation_results.deficit_surplus
        
        print(f"Validação - Déficit residual: R$ {validation_deficit:,.2f}")
        
        if abs(validation_deficit) <= 50:
            print(f"✅ ROOT FINDING FUNCIONOU - Déficit residual: R$ {validation_deficit:,.2f}")
        else:
            print(f"❌ ROOT FINDING FALHOU - Déficit residual: R$ {validation_deficit:,.2f}")
        
        return sustainable_benefit
        
    except Exception as e:
        print(f"❌ ERRO NO ROOT FINDING: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Função principal do debug"""
    print("INICIANDO DEBUG DAS SUGESTÕES INTELIGENTES")
    print("=" * 80)
    
    try:
        # Teste 1: Linha base
        state, baseline_results = test_baseline_scenario()
        
        # Teste 2: Função objetivo manual  
        engine = ActuarialEngine()
        test_objective_function_manually(state, engine)
        
        # Teste 3: Sugestões atuais
        test_current_suggestions(state)
        
        # Teste 4: Root finding debug
        sustainable_benefit = test_root_finding_debug(state)
        
        # Resumo final
        print("="*80)
        print("RESUMO FINAL")
        print("="*80)
        print(f"Déficit/Superávit original: R$ {baseline_results.deficit_surplus:,.2f}")
        if sustainable_benefit:
            print(f"Benefício sustentável calculado: R$ {sustainable_benefit:,.2f}")
        print("Debug concluído.")
        
    except Exception as e:
        print(f"ERRO GERAL NO DEBUG: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()