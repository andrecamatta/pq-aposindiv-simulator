#!/usr/bin/env python3
"""
Teste da infraestrutura de múltiplos decrementos com invalidez
"""

import sys
import os
sys.path.append('src')

# Direct imports to avoid import chain issues
from src.models.participant import SimulatorState, DecrementType, DisabilityEntryMode, CalculationMethod
from src.models.database import DecrementTable
from src.core.decrement_tables import DecrementTableManager
from src.core.mortality_tables import get_mortality_table
from src.core.projections import calculate_survival_probabilities_multi_decrement
from src.database import engine
from sqlmodel import Session, select
import numpy as np
import json

def test_decrement_table_loading():
    """Testa o carregamento das tábuas de decremento"""
    print("🧪 Testando carregamento de tábuas de decremento...")

    # Instanciar manager
    manager = DecrementTableManager()

    # Testar carregamento de tábua de invalidez
    disability_table = manager.get_decrement_table("UP84_DISABILITY", DecrementType.DISABILITY, "UNISEX")

    if disability_table is not None:
        print(f"✅ Tábua UP84_DISABILITY carregada: {len(disability_table)} idades")
        print(f"   - Taxa aos 30 anos: {disability_table[30]:.4f} ({disability_table[30]*100:.3f}%)")
        print(f"   - Taxa aos 50 anos: {disability_table[50]:.4f} ({disability_table[50]*100:.3f}%)")
        print(f"   - Taxa aos 60 anos: {disability_table[60]:.4f} ({disability_table[60]*100:.3f}%)")
    else:
        print("❌ Falha ao carregar tábua UP84_DISABILITY")
        return False

    # Testar carregamento de tábua de mortalidade
    mortality_table = get_mortality_table("BR_EMS_2021", "M")

    if mortality_table is not None:
        print(f"✅ Tábua BR_EMS_2021 carregada: {len(mortality_table)} idades")
    else:
        print("❌ Falha ao carregar tábua BR_EMS_2021")
        return False

    return True

def test_multiple_decrements_calculation():
    """Testa o cálculo de múltiplos decrementos"""
    print("\n🧪 Testando cálculo de múltiplos decrementos...")

    # Carregar tábuas
    mortality_table = get_mortality_table("BR_EMS_2021", "M")
    manager = DecrementTableManager()
    disability_table = manager.get_decrement_table("UP84_DISABILITY", DecrementType.DISABILITY, "UNISEX")

    if mortality_table is None or disability_table is None:
        print("❌ Falha ao carregar tábuas necessárias")
        return False

    # Aplicar múltiplos decrementos
    decrement_tables = {
        DecrementType.MORTALITY: mortality_table,
        DecrementType.DISABILITY: disability_table
    }

    try:
        result = manager.apply_multiple_decrements(decrement_tables, initial_age=30, total_months=420)  # 35 anos

        # Verificar resultados
        print(f"✅ Cálculo de múltiplos decrementos concluído")
        print(f"   - Sobrevivência total (ativo) em 10 anos: {result.survival_total[120]:.4f} ({result.survival_total[120]*100:.2f}%)")
        print(f"   - Sobrevivência apenas mortalidade em 10 anos: {result.survival_mortality_only[120]:.4f} ({result.survival_mortality_only[120]*100:.2f}%)")
        print(f"   - Probabilidade entrada invalidez mês 120: {result.probability_disability[120]:.6f} ({result.probability_disability[120]*100:.4f}%)")

        # Verificar que sobrevivência total <= sobrevivência só mortalidade
        if result.survival_total[120] <= result.survival_mortality_only[120]:
            print("✅ Lógica de decrementos está correta (sobrevivência total ≤ só mortalidade)")
        else:
            print("❌ Erro na lógica de decrementos")
            return False

        return True

    except Exception as e:
        print(f"❌ Erro no cálculo de múltiplos decrementos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simulator_state_integration():
    """Testa integração com SimulatorState"""
    print("\n🧪 Testando integração com SimulatorState...")

    try:
        # Criar estado com invalidez habilitada
        state = SimulatorState(
            age=30,
            gender="M",
            salary=8000.0,
            contribution_rate=8.0,
            retirement_age=65,
            target_replacement_ratio=0.7,
            # Campos obrigatórios
            initial_balance=0.0,
            accrual_rate=0.02,
            mortality_table="BR_EMS_2021",
            discount_rate=0.05,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method=CalculationMethod.PUC,
            # Campos de invalidez
            disability_enabled=True,
            disability_entry_mode=DisabilityEntryMode.IMMEDIATE,
            disability_table="UP84_DISABILITY",
            disability_mortality_table="BR_EMS_2021"
        )

        print(f"✅ SimulatorState criado com invalidez habilitada")
        print(f"   - Invalidez habilitada: {state.disability_enabled}")
        print(f"   - Modo de entrada: {state.disability_entry_mode}")
        print(f"   - Tábua de invalidez: {state.disability_table}")

        # Testar função de projeção integrada
        mortality_table = get_mortality_table("BR_EMS_2021", state.gender)
        manager = DecrementTableManager()
        disability_table = manager.get_decrement_table(state.disability_table, DecrementType.DISABILITY, state.gender)

        if mortality_table is None or disability_table is None:
            print("❌ Falha ao carregar tábuas do estado")
            return False

        # Usar função de projeção integrada
        result = calculate_survival_probabilities_multi_decrement(
            state=state,
            mortality_table=mortality_table,
            disability_table=disability_table,
            total_months=420
        )

        print(f"✅ Projeção com múltiplos decrementos concluída")
        print(f"   - Sobrevivência total aos 65 anos: {result['survival_total'][-1]:.4f} ({result['survival_total'][-1]*100:.2f}%)")
        print(f"   - Sobrevivência só mortalidade aos 65 anos: {result['survival_mortality_only'][-1]:.4f} ({result['survival_mortality_only'][-1]*100:.2f}%)")

        return True

    except Exception as e:
        print(f"❌ Erro na integração com SimulatorState: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Testa compatibilidade com código legado"""
    print("\n🧪 Testando compatibilidade com código legado...")

    try:
        from src.core.projections import calculate_survival_probabilities

        # Estado sem invalidez (legado)
        state_legacy = SimulatorState(
            age=30,
            gender="M",
            salary=8000.0,
            contribution_rate=8.0,
            retirement_age=65,
            target_replacement_ratio=0.7,
            # Campos obrigatórios
            initial_balance=0.0,
            accrual_rate=0.02,
            mortality_table="BR_EMS_2021",
            discount_rate=0.05,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method=CalculationMethod.PUC
            # disability_enabled=False por padrão
        )

        mortality_table = get_mortality_table("BR_EMS_2021", state_legacy.gender)

        if mortality_table is None:
            print("❌ Falha ao carregar tábua de mortalidade")
            return False

        # Usar função legada
        legacy_result = calculate_survival_probabilities(state_legacy, mortality_table, 420)

        print(f"✅ Função legada funciona corretamente")
        print(f"   - Sobrevivência aos 65 anos (legado): {legacy_result[-1]:.4f} ({legacy_result[-1]*100:.2f}%)")

        # Estado com invalidez
        state_disability = SimulatorState(
            age=30,
            gender="M",
            salary=8000.0,
            contribution_rate=8.0,
            retirement_age=65,
            target_replacement_ratio=0.7,
            # Campos obrigatórios
            initial_balance=0.0,
            accrual_rate=0.02,
            mortality_table="BR_EMS_2021",
            discount_rate=0.05,
            salary_growth_real=0.01,
            projection_years=40,
            calculation_method=CalculationMethod.PUC,
            # Invalidez
            disability_enabled=True,
            disability_table="UP84_DISABILITY"
        )

        # Usar mesma função (deve detectar automaticamente múltiplos decrementos)
        disability_result = calculate_survival_probabilities(state_disability, mortality_table, 420)

        print(f"✅ Função com múltiplos decrementos funciona automaticamente")
        print(f"   - Sobrevivência aos 65 anos (com invalidez): {disability_result[-1]:.4f} ({disability_result[-1]*100:.2f}%)")

        # Verificar que invalidez reduz sobrevivência
        if disability_result[-1] <= legacy_result[-1]:
            print("✅ Lógica correta: invalidez reduz sobrevivência total")
        else:
            print("❌ Erro: invalidez não está afetando sobrevivência corretamente")
            return False

        return True

    except Exception as e:
        print(f"❌ Erro na compatibilidade: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes da infraestrutura de múltiplos decrementos...")

    tests = [
        ("Carregamento de tábuas", test_decrement_table_loading),
        ("Cálculo de múltiplos decrementos", test_multiple_decrements_calculation),
        ("Integração com SimulatorState", test_simulator_state_integration),
        ("Compatibilidade com código legado", test_backward_compatibility)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print('='*60)

        try:
            if test_func():
                print(f"✅ {test_name}: PASSOU")
                passed += 1
            else:
                print(f"❌ {test_name}: FALHOU")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"📊 RESULTADOS DOS TESTES")
    print('='*60)
    print(f"✅ Testes passaram: {passed}")
    print(f"❌ Testes falharam: {failed}")
    print(f"📈 Taxa de sucesso: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print("\n🎉 Todos os testes passaram! Infraestrutura de múltiplos decrementos está funcionando!")
        return True
    else:
        print(f"\n⚠️  {failed} teste(s) falharam. Verificar implementação.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)