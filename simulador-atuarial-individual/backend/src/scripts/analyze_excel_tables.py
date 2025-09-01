#!/usr/bin/env python3
"""
Script para analisar arquivo Excel e extrair tábuas de mortalidade mencionadas.
Gera configuração automática baseada nas hipóteses atuariais encontradas.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Remover import que causa problemas - implementar funcionalidade diretamente


def analyze_excel_file(excel_path: str) -> dict:
    """Analisa arquivo Excel buscando por tábuas de mortalidade mencionadas"""
    
    print(f"Analisando arquivo: {excel_path}")
    
    try:
        # Ler todas as abas
        sheets = pd.read_excel(excel_path, sheet_name=None)
        
        results = {
            "file_path": excel_path,
            "analysis_date": datetime.utcnow().isoformat(),
            "sheets_analyzed": list(sheets.keys()),
            "tables_found": [],
            "references_found": []
        }
        
        # Padrões de busca para tábuas brasileiras conhecidas
        mortality_patterns = {
            "BR-EMS": ["BR-EMS", "BR_EMS", "BREMS", "EMS"],
            "AT-2000": ["AT-2000", "AT_2000", "AT2000"],
            "AT-49": ["AT-49", "AT_49", "AT49"],
            "AT-83": ["AT-83", "AT_83", "AT83"],
            "CSO": ["CSO", "COMMISSIONER", "COMISSIONERS"],
            "GAM": ["GAM", "GROUP ANNUITY MORTALITY"],
            "SUSEP": ["SUSEP", "SUPERINTENDENCIA"]
        }
        
        # Analisar cada planilha
        for sheet_name, df in sheets.items():
            print(f"\nAnalisando planilha: {sheet_name}")
            
            # Converter para string para análise textual
            sheet_content = df.to_string().upper()
            
            # Procurar padrões de tábuas
            for table_family, patterns in mortality_patterns.items():
                for pattern in patterns:
                    if pattern in sheet_content:
                        table_info = {
                            "table_family": table_family,
                            "pattern_found": pattern,
                            "sheet_name": sheet_name,
                            "suggested_code": f"{table_family.replace('-', '_')}_AUTO",
                            "priority": "high" if table_family in ["BR-EMS", "AT-2000"] else "medium"
                        }
                        
                        # Verificar se não é duplicata
                        if not any(t["table_family"] == table_family and t["sheet_name"] == sheet_name 
                                  for t in results["tables_found"]):
                            results["tables_found"].append(table_info)
                            print(f"  ✓ Encontrada: {table_family} (padrão: {pattern})")
            
            # Procurar referências gerais à mortalidade
            mortality_refs = ["MORTALIDADE", "MORTALITY", "TÁBUA", "TABUA", "TABLE"]
            for ref in mortality_refs:
                if ref in sheet_content:
                    ref_info = {
                        "reference": ref,
                        "sheet_name": sheet_name,
                        "context": "mortality_reference"
                    }
                    results["references_found"].append(ref_info)
        
        print(f"\nResumo da análise:")
        print(f"- {len(results['sheets_analyzed'])} planilhas analisadas")
        print(f"- {len(results['tables_found'])} tábuas específicas encontradas")
        print(f"- {len(results['references_found'])} referências gerais à mortalidade")
        
        return results
        
    except Exception as e:
        print(f"Erro ao analisar arquivo: {e}")
        return {"error": str(e)}


def generate_config_from_analysis(analysis_results: dict) -> dict:
    """Gera configuração de tábuas baseada na análise"""
    
    if "error" in analysis_results:
        return analysis_results
    
    config_tables = []
    
    # Configurações padrão para tábuas brasileiras conhecidas
    brazilian_standard_tables = {
        "BR-EMS": {
            "genders": ["M", "F"],
            "years": [2021, 2010],
            "source": "local",
            "official": True,
            "regulatory": True
        },
        "AT-2000": {
            "genders": ["M", "F"], 
            "years": [2000],
            "source": "local",
            "official": True,
            "regulatory": True
        }
    }
    
    # Gerar configurações para tábuas encontradas
    for table_info in analysis_results["tables_found"]:
        table_family = table_info["table_family"]
        
        if table_family in brazilian_standard_tables:
            standard_config = brazilian_standard_tables[table_family]
            
            for gender in standard_config["genders"]:
                for year in standard_config["years"]:
                    table_config = {
                        "code": f"{table_family.replace('-', '_')}_{year}_{gender}",
                        "name": f"{table_family} {year} {'Masculina' if gender == 'M' else 'Feminina'}",
                        "description": f"Tábua {table_family} ano {year} - {'Masculina' if gender == 'M' else 'Feminina'} (extraída de análise Excel)",
                        "source": standard_config["source"],
                        "country": "BR",
                        "year": year,
                        "gender": gender,
                        "is_official": standard_config["official"],
                        "regulatory_approved": standard_config["regulatory"],
                        "enabled": True,
                        "priority": table_info["priority"],
                        "extracted_from": analysis_results["file_path"],
                        "extraction_context": {
                            "sheet_name": table_info["sheet_name"],
                            "pattern_found": table_info["pattern_found"],
                            "analysis_date": analysis_results["analysis_date"]
                        }
                    }
                    
                    # Definir caminho do arquivo se for fonte local
                    if standard_config["source"] == "local":
                        filename = f"{table_family.lower().replace('-', '_')}_{year}_{gender.lower()}.csv"
                        table_config["file_path"] = f"data/mortality_tables/{filename}"
                    
                    config_tables.append(table_config)
    
    return {
        "analysis_summary": analysis_results,
        "generated_config": {
            "required_tables": [t for t in config_tables if t["priority"] == "high"],
            "optional_tables": [t for t in config_tables if t["priority"] != "high"],
            "generation_date": datetime.utcnow().isoformat(),
            "source_analysis": analysis_results["file_path"]
        }
    }


def save_config_file(config_data: dict, output_path: str = None):
    """Salva configuração gerada em arquivo JSON"""
    
    if output_path is None:
        output_path = "mortality_tables_config_generated.json"
    
    output_file = Path(output_path)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nConfiguração salva em: {output_file.absolute()}")
        return str(output_file.absolute())
        
    except Exception as e:
        print(f"Erro ao salvar configuração: {e}")
        return None


def main():
    """Função principal do script"""
    
    # Caminho do arquivo Excel (relativo ao diretório do projeto)
    project_root = Path(__file__).parent.parent.parent.parent.parent
    excel_file = project_root / "Hipóteses Atuariais por Plano - 2024.xlsx"
    
    if not excel_file.exists():
        print(f"Arquivo Excel não encontrado: {excel_file}")
        sys.exit(1)
    
    print("=== ANÁLISE DE TÁBUAS DE MORTALIDADE ===")
    print(f"Projeto: {project_root.name}")
    print(f"Arquivo: {excel_file.name}")
    
    # Analisar arquivo
    analysis = analyze_excel_file(str(excel_file))
    
    if "error" in analysis:
        print(f"Erro na análise: {analysis['error']}")
        sys.exit(1)
    
    # Gerar configuração
    print("\n=== GERANDO CONFIGURAÇÃO ===")
    config = generate_config_from_analysis(analysis)
    
    # Salvar configuração
    config_file = save_config_file(config)
    
    if config_file:
        print("\n=== RESUMO ===")
        gen_config = config["generated_config"]
        print(f"Tábuas obrigatórias: {len(gen_config['required_tables'])}")
        print(f"Tábuas opcionais: {len(gen_config['optional_tables'])}")
        print(f"Total de tábuas: {len(gen_config['required_tables']) + len(gen_config['optional_tables'])}")
        
        print("\nTábuas obrigatórias identificadas:")
        for table in gen_config["required_tables"]:
            print(f"  - {table['code']}: {table['name']}")
        
        print(f"\nPróximos passos:")
        print(f"1. Revisar configuração gerada em: {config_file}")
        print(f"2. Executar carregamento das tábuas via API")
        print(f"3. Verificar se arquivos CSV existem em data/mortality_tables/")


if __name__ == "__main__":
    main()