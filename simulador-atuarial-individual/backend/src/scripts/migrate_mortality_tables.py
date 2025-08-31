#!/usr/bin/env python3
"""
Script para migrar tábuas de mortalidade para o banco de dados
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.database import get_session, init_database, engine
from src.repositories.mortality_repository import MortalityTableRepository
from sqlmodel import Session


def load_mortality_table_from_file(file_path: Path) -> dict:
    """Carregar tábua de mortalidade de arquivo CSV"""
    try:
        # Assumindo que as tábuas estão em CSV com colunas: age, qx_male, qx_female
        df = pd.read_csv(file_path)
        
        # Verificar se tem colunas separadas por gênero ou unisex
        if 'qx_male' in df.columns and 'qx_female' in df.columns:
            male_data = {int(row['age']): float(row['qx_male']) for _, row in df.iterrows()}
            female_data = {int(row['age']): float(row['qx_female']) for _, row in df.iterrows()}
            return {
                'has_gender_separation': True,
                'male': male_data,
                'female': female_data
            }
        elif 'qx' in df.columns:
            unisex_data = {int(row['age']): float(row['qx']) for _, row in df.iterrows()}
            return {
                'has_gender_separation': False,
                'unisex': unisex_data
            }
        else:
            raise ValueError(f"Formato de arquivo não reconhecido: {file_path}")
    
    except Exception as e:
        print(f"Erro ao carregar {file_path}: {e}")
        return None


def get_default_mortality_tables():
    """Retornar tábuas de mortalidade padrão do sistema"""
    # Estas são as tábuas que já existem no sistema atual
    return [
        {
            "name": "BR_EMS_2021",
            "description": "Tábua de Mortalidade Brasileira EMS 2021",
            "country": "Brasil",
            "year": 2021,
            "gender": "UNISEX",
            "is_system": True,
            # Dados simplificados - na prática viriam de arquivo ou sistema existente
            "table_data": {i: 0.001 * (1.1 ** (max(0, i - 20) / 10)) for i in range(0, 121)}
        },
        {
            "name": "AT_2000",
            "description": "Tábua AT-2000 - Tábua Atuarial",
            "country": "Brasil",
            "year": 2000,
            "gender": "UNISEX",
            "is_system": True,
            "table_data": {i: 0.001 * (1.08 ** (max(0, i - 20) / 10)) for i in range(0, 121)}
        },
        {
            "name": "IBGE_2018_M",
            "description": "Tábua IBGE 2018 - Masculina",
            "country": "Brasil",
            "year": 2018,
            "gender": "M",
            "is_system": True,
            "table_data": {i: 0.001 * (1.12 ** (max(0, i - 20) / 10)) for i in range(0, 121)}
        },
        {
            "name": "IBGE_2018_F",
            "description": "Tábua IBGE 2018 - Feminina",
            "country": "Brasil",
            "year": 2018,
            "gender": "F",
            "is_system": True,
            "table_data": {i: 0.0008 * (1.1 ** (max(0, i - 20) / 10)) for i in range(0, 121)}
        }
    ]


def migrate_mortality_tables():
    """Migrar tábuas de mortalidade para o banco de dados"""
    print("Iniciando migração das tábuas de mortalidade...")
    
    # Inicializar banco de dados
    init_database()
    
    with Session(engine) as session:
        repo = MortalityTableRepository(session)
        
        # Verificar se já existem tábuas no banco
        existing_count = repo.count()
        if existing_count > 0:
            print(f"Já existem {existing_count} tábuas no banco. Pulando migração.")
            return
        
        # Tentar carregar tábuas de arquivos primeiro
        mortality_tables_dir = project_root / "data" / "mortality_tables"
        tables_migrated = 0
        
        if mortality_tables_dir.exists():
            print(f"Buscando tábuas em: {mortality_tables_dir}")
            
            for csv_file in mortality_tables_dir.glob("*.csv"):
                print(f"Carregando tábua: {csv_file.name}")
                
                table_data = load_mortality_table_from_file(csv_file)
                if table_data:
                    file_stem = csv_file.stem
                    
                    if table_data['has_gender_separation']:
                        # Criar duas tábuas separadas por gênero
                        male_table = repo.create_with_data(
                            name=f"{file_stem}_M",
                            table_data=table_data['male'],
                            description=f"Tábua {file_stem} - Masculina",
                            gender="M",
                            is_system=True
                        )
                        female_table = repo.create_with_data(
                            name=f"{file_stem}_F",
                            table_data=table_data['female'],
                            description=f"Tábua {file_stem} - Feminina",
                            gender="F",
                            is_system=True
                        )
                        tables_migrated += 2
                        print(f"  Criadas tábuas: {male_table.name} e {female_table.name}")
                    else:
                        # Criar tábua unisex
                        unisex_table = repo.create_with_data(
                            name=file_stem,
                            table_data=table_data['unisex'],
                            description=f"Tábua {file_stem}",
                            gender="UNISEX",
                            is_system=True
                        )
                        tables_migrated += 1
                        print(f"  Criada tábua: {unisex_table.name}")
        
        # Se não encontrou arquivos, usar tábuas padrão
        if tables_migrated == 0:
            print("Não foram encontrados arquivos CSV. Criando tábuas padrão...")
            
            default_tables = get_default_mortality_tables()
            
            for table_config in default_tables:
                table = repo.create_with_data(
                    name=table_config["name"],
                    table_data=table_config["table_data"],
                    description=table_config["description"],
                    country=table_config.get("country"),
                    year=table_config.get("year"),
                    gender=table_config.get("gender"),
                    is_system=table_config.get("is_system", False)
                )
                tables_migrated += 1
                print(f"  Criada tábua padrão: {table.name}")
        
        print(f"Migração concluída! {tables_migrated} tábuas foram criadas.")


def create_sample_assumptions():
    """Criar algumas premissas atuariais de exemplo"""
    from src.repositories.assumption_repository import ActuarialAssumptionRepository
    
    print("Criando premissas atuariais de exemplo...")
    
    with Session(engine) as session:
        repo = ActuarialAssumptionRepository(session)
        
        # Verificar se já existem premissas
        existing_count = repo.count()
        if existing_count > 0:
            print(f"Já existem {existing_count} premissas no banco. Pulando criação.")
            return
        
        # Premissas de taxa de desconto
        discount_rates = [
            {"name": "Conservadora", "rate": 0.04, "description": "Taxa conservadora de 4% a.a."},
            {"name": "Moderada", "rate": 0.06, "description": "Taxa moderada de 6% a.a.", "is_default": True},
            {"name": "Agressiva", "rate": 0.08, "description": "Taxa agressiva de 8% a.a."}
        ]
        
        for dr in discount_rates:
            repo.create_with_parameters(
                name=dr["name"],
                category="discount_rate",
                parameters={"annual_rate": dr["rate"]},
                description=dr["description"],
                is_default=dr.get("is_default", False),
                is_system=True
            )
        
        # Premissas de crescimento salarial
        salary_growth_rates = [
            {"name": "Baixo", "rate": 0.01, "description": "Crescimento salarial baixo de 1% a.a."},
            {"name": "Médio", "rate": 0.025, "description": "Crescimento salarial médio de 2,5% a.a.", "is_default": True},
            {"name": "Alto", "rate": 0.04, "description": "Crescimento salarial alto de 4% a.a."}
        ]
        
        for sgr in salary_growth_rates:
            repo.create_with_parameters(
                name=sgr["name"],
                category="salary_growth",
                parameters={"annual_rate": sgr["rate"]},
                description=sgr["description"],
                is_default=sgr.get("is_default", False),
                is_system=True
            )
        
        print("Premissas criadas com sucesso!")


if __name__ == "__main__":
    try:
        migrate_mortality_tables()
        create_sample_assumptions()
        print("\n✅ Migração completa!")
        
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
        sys.exit(1)