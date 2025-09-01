import numpy as np
import pandas as pd
import os
from typing import Dict, Any
from pathlib import Path

# Caminho para os dados das tábuas
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "mortality_tables"

MORTALITY_TABLES = {
    "BR_EMS_2021": {
        "name": "BR-EMS 2021 - Experiência Brasileira",
        "description": "Tábua oficial SUSEP baseada em 94M registros (2004-2018)",
        "source": "SUSEP - Superintendência de Seguros Privados",
        "is_official": True,
        "regulatory_approved": True
    },
    "AT_2000": {
        "name": "AT-2000 - Anuidades Brasileiras", 
        "description": "Tábua para anuidades aprovada pela SUSEP",
        "source": "SUSEP",
        "is_official": True,
        "regulatory_approved": True
    }
}


def _load_csv_table(filename: str) -> np.ndarray:
    """Carrega tábua de mortalidade de arquivo CSV"""
    file_path = DATA_DIR / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de tábua não encontrado: {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Criar array com índices por idade (0 a idade_max)
    max_age = df['idade'].max()
    mortality_rates = np.zeros(max_age + 1)
    
    # Preencher as taxas de mortalidade
    for _, row in df.iterrows():
        age = int(row['idade'])
        mortality_rates[age] = float(row['qx'])
    
    return mortality_rates


def _load_br_ems_2021_male() -> np.ndarray:
    """Carrega tábua BR-EMS 2021 masculina oficial"""
    return _load_csv_table("br_ems_2021_male.csv")


def _load_br_ems_2021_female() -> np.ndarray:
    """Carrega tábua BR-EMS 2021 feminina oficial"""
    return _load_csv_table("br_ems_2021_female.csv")


def _load_at_2000_male() -> np.ndarray:
    """Carrega tábua AT-2000 masculina oficial"""
    return _load_csv_table("at_2000_male.csv")


def _load_at_2000_female() -> np.ndarray:
    """Carrega tábua AT-2000 feminina oficial"""
    return _load_csv_table("at_2000_female.csv")


# Mapeamento das funções de carregamento
_TABLE_LOADERS = {
    ("BR_EMS_2021", "M"): _load_br_ems_2021_male,
    ("BR_EMS_2021", "F"): _load_br_ems_2021_female,
    ("AT_2000", "M"): _load_at_2000_male,
    ("AT_2000", "F"): _load_at_2000_female,
}

# Cache para evitar recarregamento
_CACHE = {}


def get_mortality_table(table_code: str, gender: str) -> np.ndarray:
    """Obtém tábua de mortalidade específica"""
    cache_key = (table_code, gender)
    
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    
    # Primeiro tentar o sistema antigo (compatibilidade)
    if cache_key in _TABLE_LOADERS:
        loader = _TABLE_LOADERS[cache_key]
        table_data = loader()
        _CACHE[cache_key] = table_data
        return table_data
    
    # Tentar o sistema novo (banco de dados)
    try:
        from ..database import engine
        from ..models.database import MortalityTable
        from sqlmodel import Session, select
        
        with Session(engine) as session:
            # Procurar tábua específica por gênero primeiro
            specific_code = f"{table_code}_{gender}"
            statement = select(MortalityTable).where(
                MortalityTable.code == specific_code,
                MortalityTable.is_active == True
            )
            table = session.exec(statement).first()
            
            if table:
                table_data_dict = table.get_table_data()
                # Converter para numpy array no formato esperado
                max_age = max(table_data_dict.keys())
                mortality_rates = np.zeros(max_age + 1)
                for age, rate in table_data_dict.items():
                    mortality_rates[age] = rate
                
                _CACHE[cache_key] = mortality_rates
                return mortality_rates
            
            # Se não encontrar específica, procurar genérica com o gênero correto
            statement = select(MortalityTable).where(
                MortalityTable.code.like(f"{table_code}%"),
                MortalityTable.gender == gender,
                MortalityTable.is_active == True
            )
            table = session.exec(statement).first()
            
            if table:
                table_data_dict = table.get_table_data()
                max_age = max(table_data_dict.keys())
                mortality_rates = np.zeros(max_age + 1)
                for age, rate in table_data_dict.items():
                    mortality_rates[age] = rate
                
                _CACHE[cache_key] = mortality_rates
                return mortality_rates
    
    except Exception as e:
        print(f"Erro ao carregar tábua do banco: {e}")
    
    raise ValueError(f"Tábua {table_code} para gênero {gender} não encontrada")


def get_mortality_table_info() -> list[Dict[str, Any]]:
    """Retorna informações sobre todas as tábuas disponíveis (genéricas, sem especificar gênero)"""
    tables_info = []
    
    # Adicionar tábuas do sistema antigo
    for code, table in MORTALITY_TABLES.items():
        tables_info.append({
            "code": code,
            "name": table["name"],
            "description": table["description"],
            "source": table["source"],
            "is_official": table["is_official"],
            "regulatory_approved": table["regulatory_approved"]
        })
    
    # Adicionar tábuas do banco de dados (agrupadas por família)
    try:
        from ..database import engine
        from ..models.database import MortalityTable
        from sqlmodel import Session, select
        
        with Session(engine) as session:
            statement = select(MortalityTable).where(MortalityTable.is_active == True)
            db_tables = session.exec(statement).all()
            
            # Agrupar tábuas por família (removendo sufixo _M/_F)
            table_families = {}
            for table in db_tables:
                # Extrair código da família (remover _M, _F)
                family_code = table.code
                if family_code.endswith('_M') or family_code.endswith('_F'):
                    family_code = family_code[:-2]
                
                if family_code not in table_families:
                    # Usar dados da primeira tábua da família para metadados
                    table_families[family_code] = {
                        "code": family_code,
                        "name": table.name.replace(" Masculina", "").replace(" Feminina", ""),
                        "description": table.description or "",
                        "source": table.source,
                        "is_official": table.is_official,
                        "regulatory_approved": table.regulatory_approved
                    }
            
            # Adicionar apenas se não existir no sistema antigo
            for family_code, family_info in table_families.items():
                if not any(t["code"] == family_code for t in tables_info):
                    tables_info.append(family_info)
    
    except Exception as e:
        print(f"Erro ao carregar tábuas do banco: {e}")
    
    return tables_info


def validate_mortality_table(table_code: str) -> bool:
    """Valida se a tábua existe"""
    return table_code in MORTALITY_TABLES