#!/usr/bin/env python3
"""
Script para corrigir diretamente as tábuas AT-83 no banco SQLite
"""

import sqlite3
import json
import sys
from datetime import datetime

def fix_at83_tables():
    """Corrige as tábuas AT-83 carregando dados corretos do pymort"""
    db_path = "data/simulador.db"
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return
    
    # Importar pymort
    try:
        import pymort
        print("✅ pymort disponível")
    except ImportError:
        print("❌ pymort não disponível")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Corrigindo tábuas AT-83...\n")
    
    # Remover tábuas AT-83 existentes
    cursor.execute("DELETE FROM mortalitytable WHERE code LIKE '%AT_83%'")
    removed = cursor.rowcount
    print(f"🗑️ Removidas {removed} tábuas AT-83 incorretas")
    
    # Carregar dados corretos do pymort
    tables_data = {
        "AT_83_M": {"id": 826, "gender": "M", "name": "AT-83 - Annuity Table 1983 Masculina"},
        "AT_83_F": {"id": 825, "gender": "F", "name": "AT-83 - Annuity Table 1983 Feminina"}
    }
    
    success_count = 0
    
    for code, config in tables_data.items():
        try:
            print(f"\n📥 Carregando {code} (ID {config['id']})...")
            
            # Carregar do pymort
            xml = pymort.MortXML.from_id(config['id'])
            if not xml or not hasattr(xml, 'Tables') or len(xml.Tables) == 0:
                print(f"❌ Erro: tábua {config['id']} não encontrada no pymort")
                continue
            
            table_df = xml.Tables[0].Values
            if table_df is None or len(table_df) == 0:
                print(f"❌ Erro: tábua {config['id']} sem dados")
                continue
            
            # Converter dados
            table_data = {}
            for idx, row in table_df.iterrows():
                try:
                    age = int(idx[0]) if isinstance(idx, tuple) else int(idx)
                    qx = float(row['vals'])
                    if 0 < qx <= 1:  # Validar
                        table_data[age] = qx
                except (ValueError, KeyError, TypeError):
                    continue
            
            if len(table_data) == 0:
                print(f"❌ Erro: nenhum dado válido na tábua {config['id']}")
                continue
            
            # Inserir no banco
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO mortalitytable (
                    code, name, description, source, source_id, gender,
                    is_official, regulatory_approved, is_active, is_system, 
                    table_data, table_metadata, created_at, last_loaded
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code,
                config['name'],
                f"Tábua histórica AT-83 (Annuity Table 1983) - {config['gender']}",
                "pymort",
                str(config['id']),
                config['gender'],
                1,  # is_official
                0,  # regulatory_approved  
                1,  # is_active
                1,  # is_system
                json.dumps(table_data),
                json.dumps({"corrected": True, "original_issue": "identical_tables"}),
                now,  # created_at
                now   # last_loaded
            ))
            
            success_count += 1
            print(f"✅ {code} carregada com sucesso ({len(table_data)} idades)")
            
        except Exception as e:
            print(f"❌ Erro ao carregar {code}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Correção concluída! {success_count}/2 tábuas carregadas")
    return success_count == 2

def verify_fix():
    """Verifica se a correção funcionou"""
    import os
    
    db_path = "data/simulador.db"
    if not os.path.exists(db_path):
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verificando correção...")
    
    # Buscar tábuas AT-83
    cursor.execute("""
        SELECT code, name, gender, source_id
        FROM mortalitytable 
        WHERE code LIKE '%AT_83%' AND is_active = 1
        ORDER BY code
    """)
    
    tables = cursor.fetchall()
    
    if len(tables) != 2:
        print(f"❌ Esperado 2 tábuas, encontrado {len(tables)}")
        conn.close()
        return False
    
    print("📋 Tábuas encontradas:")
    for code, name, gender, source_id in tables:
        print(f"   - {code}: {name} (ID: {source_id})")
    
    # Obter dados e comparar
    cursor.execute("SELECT table_data FROM mortalitytable WHERE code = 'AT_83_M'")
    male_data_raw = cursor.fetchone()[0]
    cursor.execute("SELECT table_data FROM mortalitytable WHERE code = 'AT_83_F'")
    female_data_raw = cursor.fetchone()[0]
    
    male_data = json.loads(male_data_raw)
    female_data = json.loads(female_data_raw)
    
    # Comparar algumas idades
    test_ages = ['30', '50', '70']  # JSON armazena como strings
    print(f"\n📊 Comparação de taxas:")
    print(f"{'Idade':>5} {'Masculina':>12} {'Feminina':>12} {'Diferença':>12}")
    print("-" * 45)
    
    different_count = 0
    for age in test_ages:
        if age in male_data and age in female_data:
            male_qx = float(male_data[age])
            female_qx = float(female_data[age])
            diff = male_qx - female_qx
            
            print(f"{age:>5} {male_qx:>12.6f} {female_qx:>12.6f} {diff:>12.6f}")
            
            if abs(diff) > 1e-10:
                different_count += 1
    
    conn.close()
    
    if different_count > 0:
        print(f"\n✅ SUCESSO! {different_count} diferenças encontradas")
        print("   As tábuas AT-83 agora estão diferenciadas por gênero")
        return True
    else:
        print(f"\n❌ PROBLEMA: Tábuas ainda idênticas")
        return False

if __name__ == "__main__":
    import os
    
    print("🔧 Correção Direta das Tábuas AT-83")
    print("=" * 50)
    
    if fix_at83_tables():
        verify_fix()
    
    print("\n✅ Processo concluído!")