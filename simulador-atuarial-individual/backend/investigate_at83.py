#!/usr/bin/env python3
"""
Script para investigar a tábua AT-83 e verificar diferenças entre gêneros
"""

import sys
import os
sys.path.append('src')

import numpy as np
from sqlmodel import Session, select
from database import engine
from models.database import MortalityTable
from core.mortality_tables import get_mortality_table

def investigate_at83_tables():
    """Investiga as tábuas AT-83 no banco de dados"""
    print("🔍 Investigando tábuas AT-83 no banco de dados...\n")
    
    with Session(engine) as session:
        # Buscar todas as tábuas relacionadas à AT-83
        stmt = select(MortalityTable).where(
            MortalityTable.code.like("%AT%83%"),
            MortalityTable.is_active == True
        )
        tables = session.exec(stmt).all()
        
        if not tables:
            print("❌ Nenhuma tábua AT-83 encontrada no banco!")
            return
            
        print(f"📋 Encontradas {len(tables)} tábuas AT-83:")
        for table in tables:
            print(f"   - {table.code}: {table.name}")
            print(f"     Gênero: {table.gender}")
            print(f"     Fonte: {table.source}")
            if hasattr(table, 'source_id'):
                print(f"     Source ID: {table.source_id}")
            print()
        
        # Verificar se existem versões masculina e feminina
        at83_m = None
        at83_f = None
        
        for table in tables:
            if table.gender == 'M' or table.code.endswith('_M'):
                at83_m = table
            elif table.gender == 'F' or table.code.endswith('_F'):
                at83_f = table
        
        if at83_m and at83_f:
            print("✅ Encontradas versões masculina e feminina da AT-83")
            compare_at83_tables(at83_m, at83_f)
        else:
            print("⚠️  Não foram encontradas versões separadas por gênero da AT-83")
            if at83_m:
                print("   Encontrada apenas versão masculina")
            if at83_f:
                print("   Encontrada apenas versão feminina")

def compare_at83_tables(male_table, female_table):
    """Compara as tábuas AT-83 masculina e feminina"""
    print("\n📊 Comparando tábuas AT-83 masculina vs feminina:\n")
    
    # Obter dados das tábuas
    male_data = male_table.get_table_data()
    female_data = female_table.get_table_data()
    
    print(f"Tábua Masculina ({male_table.code}):")
    print(f"   - Total de idades: {len(male_data)}")
    print(f"   - Faixa etária: {min(male_data.keys())} - {max(male_data.keys())}")
    
    print(f"\nTábua Feminina ({female_table.code}):")
    print(f"   - Total de idades: {len(female_data)}")
    print(f"   - Faixa etária: {min(female_data.keys())} - {max(female_data.keys())}")
    
    # Comparar algumas idades específicas
    test_ages = [30, 40, 50, 60, 70, 80]
    print(f"\n📈 Comparação de taxas de mortalidade (qx):")
    print(f"{'Idade':>5} {'Masculina':>12} {'Feminina':>12} {'Diferença':>12} {'% Diff':>8}")
    print("-" * 55)
    
    identical_count = 0
    different_count = 0
    
    for age in test_ages:
        if age in male_data and age in female_data:
            male_qx = male_data[age]
            female_qx = female_data[age]
            diff = male_qx - female_qx
            pct_diff = (diff / female_qx * 100) if female_qx > 0 else 0
            
            print(f"{age:>5} {male_qx:>12.6f} {female_qx:>12.6f} {diff:>12.6f} {pct_diff:>7.2f}%")
            
            if abs(diff) < 1e-10:  # Praticamente idênticos
                identical_count += 1
            else:
                different_count += 1
    
    print(f"\n📊 Resumo da comparação:")
    print(f"   - Idades idênticas: {identical_count}")
    print(f"   - Idades diferentes: {different_count}")
    
    if identical_count > different_count:
        print("⚠️  As tábuas parecem ser muito similares ou idênticas!")
        print("   Isso pode indicar um problema na configuração/carregamento.")
    else:
        print("✅ As tábuas mostram diferenças esperadas entre gêneros.")

def check_mortality_table_access():
    """Verifica se conseguimos acessar as tábuas via API"""
    print("\n🔧 Testando acesso via API de mortalidade:\n")
    
    try:
        # Tentar obter tábuas via API
        male_table = get_mortality_table("AT_83", "M")
        female_table = get_mortality_table("AT_83", "F")
        
        print("✅ Conseguimos carregar ambas as tábuas via API")
        
        # Comparar algumas idades
        test_ages = [30, 50, 70]
        print(f"\n📈 Comparação via API:")
        print(f"{'Idade':>5} {'Masculina':>12} {'Feminina':>12} {'Diferença':>12}")
        print("-" * 45)
        
        for age in test_ages:
            if age < len(male_table) and age < len(female_table):
                male_qx = male_table[age]
                female_qx = female_table[age]
                diff = male_qx - female_qx
                
                print(f"{age:>5} {male_qx:>12.6f} {female_qx:>12.6f} {diff:>12.6f}")
                
    except Exception as e:
        print(f"❌ Erro ao acessar tábuas via API: {e}")

def check_pymort_info():
    """Verifica informações sobre AT-83 no pymort"""
    print("\n🌐 Verificando informações da AT-83 no pymort:\n")
    
    try:
        import pymort
        print("✅ pymort disponível")
        
        # Tentar carregar a tábua 825 (AT-83 atual)
        xml = pymort.MortXML.from_id(825)
        if xml:
            print(f"📋 Tábua 825 encontrada:")
            print(f"   - Nome: {getattr(xml, 'ContentClassification', 'N/A')}")
            print(f"   - Tabelas disponíveis: {len(xml.Tables) if hasattr(xml, 'Tables') else 0}")
            
            if hasattr(xml, 'Tables') and len(xml.Tables) > 0:
                table = xml.Tables[0]
                if hasattr(table, 'MetaData') and table.MetaData:
                    metadata = table.MetaData
                    print(f"   - Nação: {getattr(metadata, 'Nation', 'N/A')}")
                    print(f"   - Descrição: {getattr(metadata, 'TableDescription', 'N/A')}")
        
        # Buscar outras possíveis AT-83
        print(f"\n🔍 Buscando outras tábuas AT-83 no pymort...")
        
        # IDs conhecidos relacionados à AT-83
        potential_ids = [825, 826, 827, 828, 829]  # Alguns IDs próximos
        
        for table_id in potential_ids:
            try:
                xml = pymort.MortXML.from_id(table_id)
                if xml:
                    name = getattr(xml, 'ContentClassification', f'Table {table_id}')
                    if 'AT' in name and '83' in name:
                        print(f"   - ID {table_id}: {name}")
            except:
                continue
                
    except ImportError:
        print("❌ pymort não disponível")
    except Exception as e:
        print(f"❌ Erro ao consultar pymort: {e}")

if __name__ == "__main__":
    print("🔍 Investigação da Tábua AT-83")
    print("=" * 50)
    
    investigate_at83_tables()
    check_mortality_table_access()
    check_pymort_info()
    
    print("\n✅ Investigação concluída!")