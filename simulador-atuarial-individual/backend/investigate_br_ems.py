#!/usr/bin/env python3
"""
Script para investigar em detalhes o arquivo Excel BR-EMS da SUSEP
e identificar problemas nas tábuas de mortalidade extraídas.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def investigate_br_ems_excel():
    """Investiga detalhadamente o arquivo Excel da SUSEP"""
    
    excel_file = "tabuas-br-ems-2010-2015-2021.xlsx"
    logger.info(f"🔍 Investigando arquivo: {excel_file}")
    
    try:
        # Ler todas as abas do Excel
        excel_data = pd.read_excel(excel_file, sheet_name=None)
        
        logger.info(f"📋 Total de abas encontradas: {len(excel_data.keys())}")
        logger.info(f"📋 Nomes das abas: {list(excel_data.keys())}")
        
        # Analisar cada aba em detalhes
        for sheet_name, df in excel_data.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 ANALISANDO ABA: {sheet_name}")
            logger.info(f"{'='*60}")
            logger.info(f"📊 Dimensões: {df.shape}")
            logger.info(f"📋 Colunas: {list(df.columns)}")
            
            # Mostrar primeiras linhas para entender estrutura
            logger.info(f"\n--- Primeiras 15 linhas ---")
            print(df.head(15).to_string())
            
            # Procurar por indicadores de tipo de tábua
            df_str = df.to_string().upper()
            indicators = {
                'MORTALIDADE': 'MORTALIDADE' in df_str,
                'SOBREVIVENCIA': 'SOBREVIVENCIA' in df_str or 'SOBREVIVÊNCIA' in df_str,
                'QX': 'QX' in df_str,
                'LX': 'LX' in df_str,
                'EX': 'EX' in df_str,
                'MASCULINA': 'MASCULINA' in df_str or 'MASCULINO' in df_str,
                'FEMININA': 'FEMININA' in df_str or 'FEMININO' in df_str,
                '2010': '2010' in df_str,
                '2021': '2021' in df_str,
                'BR-EMS': 'BR-EMS' in df_str or 'BREMS' in df_str
            }
            
            logger.info(f"\n📍 Indicadores encontrados:")
            for indicator, found in indicators.items():
                status = "✅" if found else "❌"
                logger.info(f"  {status} {indicator}")
            
            # Se é a aba BR-EMS 2010, analisar estrutura de dados
            if sheet_name == "BR-EMS 2010":
                analyze_br_ems_2010_detailed(df)
        
        # Comparar com tábuas existentes no sistema
        compare_with_existing_tables()
        
    except Exception as e:
        logger.error(f"❌ Erro ao investigar Excel: {e}")
        raise

def analyze_br_ems_2010_detailed(df):
    """Análise detalhada da aba BR-EMS 2010"""
    
    logger.info(f"\n🔬 ANÁLISE DETALHADA - BR-EMS 2010")
    logger.info(f"{'='*40}")
    
    # Procurar por dados numéricos que parecem idades
    numeric_data = []
    for col_idx in range(df.shape[1]):
        col = df.iloc[:, col_idx]
        numeric_values = pd.to_numeric(col, errors='coerce').dropna()
        
        if len(numeric_values) > 50:  # Pelo menos 50 valores numéricos
            min_val, max_val = numeric_values.min(), numeric_values.max()
            logger.info(f"📊 Coluna {col_idx}: {len(numeric_values)} valores numéricos")
            logger.info(f"    Range: {min_val:.6f} - {max_val:.6f}")
            
            # Verificar se parece sequência de idades
            if 0 <= min_val <= 5 and 100 <= max_val <= 120:
                logger.info(f"    ✅ PARECE SER COLUNA DE IDADES!")
                
                # Procurar colunas adjacentes com qx
                for qx_col_idx in range(col_idx + 1, min(col_idx + 6, df.shape[1])):
                    qx_col = pd.to_numeric(df.iloc[:, qx_col_idx], errors='coerce').dropna()
                    if len(qx_col) > 50:
                        qx_min, qx_max = qx_col.min(), qx_col.max()
                        logger.info(f"📊 Coluna {qx_col_idx} (possível qx): {len(qx_col)} valores")
                        logger.info(f"    Range: {qx_min:.6f} - {qx_max:.6f}")
                        
                        # Verificar se valores parecem qx (0 < qx < 1)
                        if 0.0001 <= qx_min <= 0.1 and 0.1 <= qx_max <= 1.0:
                            logger.info(f"    ✅ PARECE SER COLUNA DE QX!")
                            
                            # Extrair amostra de dados para análise
                            sample_data = []
                            for i in range(min(len(col), len(qx_col))):
                                age_val = pd.to_numeric(col.iloc[i], errors='coerce')
                                qx_val = pd.to_numeric(qx_col.iloc[i], errors='coerce')
                                if pd.notna(age_val) and pd.notna(qx_val):
                                    sample_data.append((int(age_val), float(qx_val)))
                            
                            if len(sample_data) > 10:
                                logger.info(f"\n📋 AMOSTRA DOS DADOS (primeiros 10):")
                                for age, qx in sample_data[:10]:
                                    logger.info(f"    Idade {age}: qx = {qx:.6f}")
                                
                                logger.info(f"\n📋 AMOSTRA DOS DADOS (idades 60-70):")
                                for age, qx in sample_data:
                                    if 60 <= age <= 70:
                                        logger.info(f"    Idade {age}: qx = {qx:.6f}")
            
            elif 0.0001 <= min_val <= 0.01 and 0.1 <= max_val <= 1.0:
                logger.info(f"    ✅ PARECE SER COLUNA DE QX!")

def compare_with_existing_tables():
    """Compara com tábuas existentes para validação"""
    
    logger.info(f"\n🔍 COMPARANDO COM TÁBUAS EXISTENTES")
    logger.info(f"{'='*40}")
    
    # Ler tábuas existentes
    tables = {
        'BR-EMS 2021 Male': 'data/mortality_tables/br_ems_2021_male.csv',
        'BR-EMS 2010 Male (extraído)': 'data/mortality_tables/br_ems_2010_male.csv',
        'AT-2000 Male': 'data/mortality_tables/at_2000_male.csv'
    }
    
    comparison_ages = [30, 40, 50, 60, 65, 70, 75]
    
    logger.info(f"📊 COMPARAÇÃO DE TAXAS qx POR IDADE:")
    logger.info(f"{'Idade':<6} {'BR-EMS 2021':<12} {'BR-EMS 2010':<12} {'AT-2000':<12}")
    logger.info(f"{'-'*50}")
    
    table_data = {}
    for table_name, file_path in tables.items():
        try:
            df = pd.read_csv(file_path)
            table_data[table_name] = dict(zip(df['idade'], df['qx']))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao ler {table_name}: {e}")
            table_data[table_name] = {}
    
    for age in comparison_ages:
        row = f"{age:<6} "
        for table_name in ['BR-EMS 2021 Male', 'BR-EMS 2010 Male (extraído)', 'AT-2000 Male']:
            qx = table_data.get(table_name, {}).get(age, 'N/A')
            if qx != 'N/A':
                row += f"{qx:<12.6f} "
            else:
                row += f"{'N/A':<12} "
        logger.info(row)
    
    # Análise de consistência
    logger.info(f"\n🔍 ANÁLISE DE CONSISTÊNCIA:")
    
    br_2021 = table_data.get('BR-EMS 2021 Male', {})
    br_2010 = table_data.get('BR-EMS 2010 Male (extraído)', {})
    
    if br_2021 and br_2010:
        inconsistencies = 0
        for age in comparison_ages:
            if age in br_2021 and age in br_2010:
                if br_2021[age] > br_2010[age]:
                    inconsistencies += 1
                    logger.warning(f"⚠️ Inconsistência idade {age}: BR-EMS 2021 ({br_2021[age]:.6f}) > BR-EMS 2010 ({br_2010[age]:.6f})")
        
        if inconsistencies > 0:
            logger.error(f"❌ ENCONTRADAS {inconsistencies} INCONSISTÊNCIAS!")
            logger.error(f"   BR-EMS 2021 deveria ter mortalidade MENOR que BR-EMS 2010")
        else:
            logger.info(f"✅ Tábuas consistentes - BR-EMS 2021 tem mortalidade menor que 2010")

if __name__ == "__main__":
    investigate_br_ems_excel()
    logger.info(f"\n🎉 Investigação concluída!")