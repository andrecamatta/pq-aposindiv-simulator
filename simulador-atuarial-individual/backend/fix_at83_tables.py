#!/usr/bin/env python3
"""
Script para corrigir as tábuas AT-83 com os IDs corretos por gênero
"""

import sys
import os
sys.path.append('src')

from sqlmodel import Session, select
from database import engine
from models.database import MortalityTable
from core.mortality_initializer import MortalityTableInitializer

def remove_incorrect_at83_tables():
    """Remove as tábuas AT-83 incorretas do banco"""
    print("🗑️ Removendo tábuas AT-83 incorretas...\n")
    
    with Session(engine) as session:
        # Buscar tábuas AT-83 existentes
        stmt = select(MortalityTable).where(
            MortalityTable.code.like("%AT_83%")
        )
        tables = session.exec(stmt).all()
        
        removed_count = 0
        for table in tables:
            print(f"   Removendo: {table.code} - {table.name}")
            session.delete(table)
            removed_count += 1
        
        session.commit()
        print(f"✅ Removidas {removed_count} tábuas AT-83 incorretas\n")

def reload_at83_tables():
    """Recarrega as tábuas AT-83 com os IDs corretos"""
    print("🔄 Recarregando tábuas AT-83 com IDs corretos...\n")
    
    initializer = MortalityTableInitializer()
    
    # Buscar apenas a configuração da AT-83
    at83_config = None
    for config in initializer.REQUIRED_TABLES:
        if config["code"] == "AT_83":
            at83_config = config
            break
    
    if not at83_config:
        print("❌ Configuração AT-83 não encontrada!")
        return
    
    print("📋 Configuração encontrada:")
    print(f"   - Código: {at83_config['code']}")
    print(f"   - ID Masculino: {at83_config.get('source_id_male', 'N/A')}")
    print(f"   - ID Feminino: {at83_config.get('source_id_female', 'N/A')}")
    print()
    
    # Carregar as tábuas com a nova configuração
    with Session(engine) as session:
        success = initializer._load_table_family(session, at83_config)
        if success:
            print("✅ Tábuas AT-83 recarregadas com sucesso!")
        else:
            print("❌ Erro ao recarregar tábuas AT-83")

def verify_at83_fix():
    """Verifica se a correção funcionou"""
    print("\n🔍 Verificando correção das tábuas AT-83...\n")
    
    with Session(engine) as session:
        # Buscar as novas tábuas
        stmt = select(MortalityTable).where(
            MortalityTable.code.like("%AT_83%"),
            MortalityTable.is_active == True
        )
        tables = session.exec(stmt).all()
        
        at83_m = None
        at83_f = None
        
        for table in tables:
            print(f"   - {table.code}: {table.name}")
            print(f"     Source ID: {table.source_id}")
            print(f"     Gênero: {table.gender}")
            print()
            
            if table.gender == 'M':
                at83_m = table
            elif table.gender == 'F':
                at83_f = table
        
        if at83_m and at83_f:
            # Verificar se agora são diferentes
            male_data = at83_m.get_table_data()
            female_data = at83_f.get_table_data()
            
            # Testar algumas idades
            test_ages = [30, 50, 70]
            print("📊 Verificando diferenças entre tábuas:")
            print(f"{'Idade':>5} {'Masculina':>12} {'Feminina':>12} {'Diferença':>12}")
            print("-" * 45)
            
            different_count = 0
            for age in test_ages:
                if age in male_data and age in female_data:
                    male_qx = male_data[age]
                    female_qx = female_data[age]
                    diff = male_qx - female_qx
                    
                    print(f"{age:>5} {male_qx:>12.6f} {female_qx:>12.6f} {diff:>12.6f}")
                    
                    if abs(diff) > 1e-10:
                        different_count += 1
            
            if different_count > 0:
                print(f"\n✅ SUCESSO! Encontradas {different_count} diferenças entre gêneros")
                print("   As tábuas AT-83 agora têm diferenciação correta por gênero")
            else:
                print(f"\n❌ PROBLEMA: Tábuas ainda são idênticas")
        else:
            print("❌ Não foram encontradas ambas as versões (M e F)")

if __name__ == "__main__":
    print("🔧 Correção das Tábuas AT-83")
    print("=" * 50)
    
    remove_incorrect_at83_tables()
    reload_at83_tables()
    verify_at83_fix()
    
    print("\n✅ Processo de correção concluído!")