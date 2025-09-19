#!/usr/bin/env python3
"""
Script simples para investigar a tábua AT-83
"""

import sys
import os
import sqlite3
import numpy as np

def investigate_at83_from_db():
    """Investiga diretamente no banco SQLite"""
    db_path = "data/simulador.db"
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return
    
    print("🔍 Investigando tábuas AT-83 no banco de dados...\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar tábuas AT-83
    cursor.execute("""
        SELECT code, name, gender, source, source_id, is_active
        FROM mortalitytable 
        WHERE code LIKE '%AT%83%' OR code LIKE '%AT_83%'
        ORDER BY code
    """)
    
    tables = cursor.fetchall()
    
    if not tables:
        print("❌ Nenhuma tábua AT-83 encontrada no banco!")
        conn.close()
        return
    
    print(f"📋 Encontradas {len(tables)} tábuas AT-83:")
    for table in tables:
        code, name, gender, source, source_id, is_active = table
        print(f"   - {code}: {name}")
        print(f"     Gênero: {gender}")
        print(f"     Fonte: {source}")
        print(f"     Source ID: {source_id}")
        print(f"     Ativa: {is_active}")
        print()
    
    # Buscar dados das tábuas masculina e feminina
    at83_m_data = get_table_data(cursor, "AT_83_M")
    at83_f_data = get_table_data(cursor, "AT_83_F")
    
    if at83_m_data and at83_f_data:
        print("✅ Encontrados dados para ambas as versões (M e F)")
        compare_table_data(at83_m_data, at83_f_data)
    else:
        print("⚠️  Não foi possível encontrar dados para ambas as versões")
        if at83_m_data:
            print("   Encontrados dados para versão masculina")
        if at83_f_data:
            print("   Encontrados dados para versão feminina")
    
    conn.close()

def get_table_data(cursor, table_code):
    """Obtém dados de uma tábua específica"""
    cursor.execute("""
        SELECT table_data 
        FROM mortalitytable 
        WHERE code = ? AND is_active = 1
    """, (table_code,))
    
    result = cursor.fetchone()
    if result and result[0]:
        import json
        try:
            # Os dados estão armazenados como JSON
            data = json.loads(result[0])
            # Converter chaves string para int
            return {int(k): float(v) for k, v in data.items()}
        except:
            return None
    return None

def compare_table_data(male_data, female_data):
    """Compara dados das tábuas masculina e feminina"""
    print("\n📊 Comparando tábuas AT-83 masculina vs feminina:\n")
    
    print(f"Tábua Masculina:")
    print(f"   - Total de idades: {len(male_data)}")
    print(f"   - Faixa etária: {min(male_data.keys())} - {max(male_data.keys())}")
    
    print(f"\nTábua Feminina:")
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
        print("   A tábua AT-83 deveria ter diferenças entre masculina e feminina.")
    else:
        print("✅ As tábuas mostram diferenças esperadas entre gêneros.")

def check_pymort_at83():
    """Verifica informações sobre AT-83 no pymort"""
    print("\n🌐 Verificando informações da AT-83 no pymort:\n")
    
    try:
        import pymort
        print("✅ pymort disponível")
        
        # Tentar carregar a tábua 825 (AT-83 atual)
        try:
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
                        
                    # Verificar se há dados por gênero
                    if hasattr(table, 'Values') and table.Values is not None:
                        df = table.Values
                        print(f"   - Total de registros: {len(df)}")
                        
                        # Verificar se há coluna de gênero ou se são dados unissex
                        print(f"   - Colunas: {list(df.columns)}")
                        
                        # Mostrar algumas linhas
                        print(f"   - Primeiras idades:")
                        for i, (idx, row) in enumerate(df.head(5).iterrows()):
                            age = idx[0] if isinstance(idx, tuple) else idx
                            qx = row['vals'] if 'vals' in row else row[0]
                            print(f"     Idade {age}: qx = {qx:.6f}")
                        
        except Exception as e:
            print(f"   ❌ Erro ao carregar tábua 825: {e}")
        
        # Buscar outras possíveis AT-83
        print(f"\n🔍 Buscando outras tábuas relacionadas à AT-83...")
        
        # Alguns IDs que podem ter AT-83 separadas por gênero
        potential_ids = [825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835]
        found_tables = []
        
        for table_id in potential_ids:
            try:
                xml = pymort.MortXML.from_id(table_id)
                if xml:
                    name = getattr(xml, 'ContentClassification', f'Table {table_id}')
                    if name and ('AT' in str(name).upper() and '83' in str(name)):
                        found_tables.append((table_id, name))
                        print(f"   - ID {table_id}: {name}")
            except:
                continue
        
        if found_tables:
            print(f"\n✅ Encontradas {len(found_tables)} tábuas AT-83 relacionadas")
        else:
            print(f"\n⚠️  Apenas a tábua 825 encontrada - pode ser unissex")
                
    except ImportError:
        print("❌ pymort não disponível")
    except Exception as e:
        print(f"❌ Erro ao consultar pymort: {e}")

if __name__ == "__main__":
    print("🔍 Investigação da Tábua AT-83")
    print("=" * 50)
    
    investigate_at83_from_db()
    check_pymort_at83()
    
    print("\n✅ Investigação concluída!")