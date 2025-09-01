#!/usr/bin/env python3
"""
Script para extrair tábuas BR-EMS 2010 do arquivo Excel da SUSEP
e convertê-las para formato CSV padrão do sistema.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_br_ems_2010():
    """Extrai tábuas BR-EMS 2010 do arquivo Excel da SUSEP"""
    
    excel_file = "tabuas-br-ems-2010-2015-2021.xlsx"
    output_dir = Path("data/mortality_tables")
    output_dir.mkdir(exist_ok=True)
    
    logger.info(f"📊 Analisando arquivo: {excel_file}")
    
    try:
        # Ler apenas a aba BR-EMS 2010
        br_ems_2010 = pd.read_excel(excel_file, sheet_name="BR-EMS 2010")
        
        logger.info(f"🔍 Analisando aba BR-EMS 2010")
        logger.info(f"  - Dimensões: {br_ems_2010.shape}")
        logger.info(f"  - Colunas: {list(br_ems_2010.columns)}")
        
        # Exibir dados para análise
        print("\n--- Estrutura completa da aba BR-EMS 2010 ---")
        print(br_ems_2010.head(20))
        print("\n--- Últimas linhas ---")
        print(br_ems_2010.tail(10))
        
        # Analisar estrutura específica da BR-EMS 2010
        extract_br_ems_2010_specific(br_ems_2010, output_dir)
    
    except Exception as e:
        logger.error(f"❌ Erro ao processar Excel: {e}")
        raise

def detect_mortality_table_structure(df):
    """Detecta se o DataFrame contém estrutura de tábua de mortalidade"""
    
    # Verificar se há colunas com idade/qx
    columns_str = ' '.join(df.columns.astype(str)).upper()
    age_indicators = ['IDADE', 'AGE', 'X']
    qx_indicators = ['QX', 'MORTALITY', 'MORT', 'TAXA']
    
    has_age = any(indicator in columns_str for indicator in age_indicators)
    has_qx = any(indicator in columns_str for indicator in qx_indicators)
    
    # Verificar se há dados numéricos que parecem idades (0-120)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    potential_ages = False
    
    for col in numeric_cols:
        values = df[col].dropna()
        if len(values) > 10:  # Pelo menos 10 valores
            min_val, max_val = values.min(), values.max()
            if 0 <= min_val <= 10 and 50 <= max_val <= 120:
                potential_ages = True
                break
    
    return has_age or has_qx or potential_ages

def extract_mortality_data(df, sheet_name, output_dir):
    """Extrai dados de mortalidade do DataFrame"""
    
    logger.info(f"🔄 Extraindo dados de mortalidade da aba: {sheet_name}")
    
    # Tentar diferentes estratégias para extrair dados
    
    # Estratégia 1: Procurar colunas com nomes padrão
    age_col = None
    qx_cols = {}
    
    for col in df.columns:
        col_str = str(col).upper()
        if any(indicator in col_str for indicator in ['IDADE', 'AGE', 'X']):
            if age_col is None:  # Primeira coluna de idade encontrada
                age_col = col
        
        if any(indicator in col_str for indicator in ['QX', 'MORT', 'TAXA']):
            # Tentar determinar gênero pela coluna
            if any(gender in col_str for gender in ['MASC', 'MALE', 'M']):
                qx_cols['M'] = col
            elif any(gender in col_str for gender in ['FEM', 'FEMALE', 'F']):
                qx_cols['F'] = col
            else:
                qx_cols['UNISEX'] = col
    
    logger.info(f"  - Coluna de idade: {age_col}")
    logger.info(f"  - Colunas qx: {qx_cols}")
    
    if age_col and qx_cols:
        # Extrair dados
        for gender, qx_col in qx_cols.items():
            try:
                extract_single_table(df, age_col, qx_col, gender, sheet_name, output_dir)
            except Exception as e:
                logger.error(f"❌ Erro ao extrair tábua {gender}: {e}")
    
    # Estratégia 2: Se não encontrou colunas padrão, tentar análise posicional
    elif df.shape[1] >= 2:
        logger.info("  📍 Tentando análise posicional...")
        try_positional_extraction(df, sheet_name, output_dir)

def extract_single_table(df, age_col, qx_col, gender, sheet_name, output_dir):
    """Extrai uma tábua individual"""
    
    # Limpar dados
    clean_df = df[[age_col, qx_col]].dropna()
    
    # Filtrar idades válidas
    clean_df = clean_df[
        (clean_df[age_col] >= 0) & 
        (clean_df[age_col] <= 120) &
        (clean_df[qx_col] >= 0) &
        (clean_df[qx_col] <= 1)
    ]
    
    if len(clean_df) < 10:
        logger.warning(f"  ⚠️ Poucos dados válidos para {gender}: {len(clean_df)} registros")
        return
    
    # Renomear colunas para padrão
    clean_df = clean_df.rename(columns={age_col: 'idade', qx_col: 'qx'})
    
    # Ordenar por idade
    clean_df = clean_df.sort_values('idade')
    
    # Gerar nome do arquivo
    gender_suffix = 'male' if gender == 'M' else 'female' if gender == 'F' else 'unisex'
    filename = f"br_ems_2010_{gender_suffix}.csv"
    filepath = output_dir / filename
    
    # Salvar CSV
    clean_df.to_csv(filepath, index=False)
    
    logger.info(f"  ✅ Tábua salva: {filepath}")
    logger.info(f"     - Registros: {len(clean_df)}")
    logger.info(f"     - Idades: {clean_df['idade'].min()}-{clean_df['idade'].max()}")
    logger.info(f"     - qx médio: {clean_df['qx'].mean():.6f}")

def try_positional_extraction(df, sheet_name, output_dir):
    """Tentativa de extração posicional quando não há colunas claras"""
    
    logger.info("  🔄 Análise posicional dos dados...")
    
    # Procurar por sequências que parecem idades
    for col_idx in range(min(3, df.shape[1])):  # Primeiras 3 colunas
        col = df.iloc[:, col_idx]
        
        if col.dtype in ['int64', 'float64']:
            # Verificar se parece sequência de idades
            non_null_values = col.dropna()
            if len(non_null_values) > 20:
                min_val, max_val = non_null_values.min(), non_null_values.max()
                
                if 0 <= min_val <= 5 and 70 <= max_val <= 120:
                    logger.info(f"    📊 Coluna {col_idx} parece ser idades: {min_val}-{max_val}")
                    
                    # Procurar colunas de qx adjacentes
                    for qx_col_idx in range(col_idx + 1, min(col_idx + 4, df.shape[1])):
                        qx_col = df.iloc[:, qx_col_idx]
                        
                        if qx_col.dtype in ['float64']:
                            non_null_qx = qx_col.dropna()
                            if len(non_null_qx) > 20:
                                qx_min, qx_max = non_null_qx.min(), non_null_qx.max()
                                
                                if 0.0001 <= qx_min <= 0.01 and 0.1 <= qx_max <= 1.0:
                                    logger.info(f"    📊 Coluna {qx_col_idx} parece ser qx: {qx_min:.6f}-{qx_max:.6f}")
                                    
                                    # Extrair dados
                                    data = pd.DataFrame({
                                        'idade': col,
                                        'qx': qx_col
                                    }).dropna()
                                    
                                    # Determinar gênero pelo nome da aba ou posição
                                    gender = 'male' if 'MASC' in sheet_name.upper() or qx_col_idx == col_idx + 1 else 'female'
                                    
                                    filename = f"br_ems_2010_{gender}.csv"
                                    filepath = output_dir / filename
                                    
                                    data.to_csv(filepath, index=False)
                                    logger.info(f"    ✅ Tábua extraída: {filepath} ({len(data)} registros)")

def extract_br_ems_2010_specific(df, output_dir):
    """Extrai dados específicos da aba BR-EMS 2010"""
    
    logger.info(f"🔄 Extraindo dados da BR-EMS 2010...")
    
    # A aba BR-EMS 2010 tem estrutura específica com dados em colunas adjacentes
    # Procurar por dados que começam com idades (0, 1, 2, ...)
    
    # Encontrar linha onde começam os dados (procurar por idade 0)
    start_row = None
    age_col = None
    
    for idx, row in df.iterrows():
        for col_idx, value in enumerate(row):
            if pd.notna(value) and str(value).strip() == "0":
                # Verificar se parece início de sequência de idades
                next_values = []
                for i in range(1, 5):  # Verificar próximas 4 linhas
                    if idx + i < len(df):
                        next_val = df.iloc[idx + i, col_idx]
                        if pd.notna(next_val):
                            next_values.append(str(next_val).strip())
                
                # Se encontrou sequência 0, 1, 2, 3...
                if next_values[:3] == ["1", "2", "3"]:
                    start_row = idx
                    age_col = col_idx
                    logger.info(f"  ✓ Dados encontrados iniciando na linha {start_row}, coluna {age_col}")
                    break
        
        if start_row is not None:
            break
    
    if start_row is None:
        logger.error("  ❌ Não foi possível localizar início dos dados")
        return
    
    # Extrair dados a partir da linha encontrada
    # A estrutura da BR-EMS 2010 tem: Idade | qx Masculina | qx Feminina
    male_data = []
    female_data = []
    
    for row_idx in range(start_row, len(df)):
        row = df.iloc[row_idx]
        
        # Idade na primeira coluna encontrada
        age = row.iloc[age_col]
        if pd.isna(age):
            break
            
        try:
            age = int(float(age))
            if age < 0 or age > 120:
                break
        except (ValueError, TypeError):
            break
        
        # qx masculino (próxima coluna com dados válidos)
        male_qx = None
        female_qx = None
        
        for col_offset in range(1, 6):  # Procurar nas próximas 5 colunas
            if age_col + col_offset < len(row):
                val = row.iloc[age_col + col_offset]
                if pd.notna(val):
                    try:
                        qx_val = float(val)
                        if 0 <= qx_val <= 1:
                            if male_qx is None:
                                male_qx = qx_val
                            elif female_qx is None:
                                female_qx = qx_val
                                break
                    except (ValueError, TypeError):
                        continue
        
        # Adicionar aos dados se válido
        if male_qx is not None:
            male_data.append({"idade": age, "qx": male_qx})
        if female_qx is not None:
            female_data.append({"idade": age, "qx": female_qx})
    
    # Salvar arquivos CSV
    if male_data:
        male_df = pd.DataFrame(male_data)
        male_file = output_dir / "br_ems_2010_male.csv"
        male_df.to_csv(male_file, index=False)
        logger.info(f"  ✅ Tábua masculina salva: {male_file} ({len(male_data)} registros)")
        logger.info(f"     - Idades: {male_df['idade'].min()}-{male_df['idade'].max()}")
        logger.info(f"     - qx médio: {male_df['qx'].mean():.6f}")
    
    if female_data:
        female_df = pd.DataFrame(female_data)
        female_file = output_dir / "br_ems_2010_female.csv"
        female_df.to_csv(female_file, index=False)
        logger.info(f"  ✅ Tábua feminina salva: {female_file} ({len(female_data)} registros)")
        logger.info(f"     - Idades: {female_df['idade'].min()}-{female_df['idade'].max()}")
        logger.info(f"     - qx médio: {female_df['qx'].mean():.6f}")
    
    if not male_data and not female_data:
        logger.error("  ❌ Nenhum dado válido foi extraído")

if __name__ == "__main__":
    extract_br_ems_2010()
    print("\n🎉 Extração concluída!")