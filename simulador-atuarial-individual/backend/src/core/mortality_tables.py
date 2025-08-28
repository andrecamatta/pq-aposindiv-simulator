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
    
    if cache_key not in _TABLE_LOADERS:
        raise ValueError(f"Tábua {table_code} para gênero {gender} não encontrada")
    
    loader = _TABLE_LOADERS[cache_key]
    table_data = loader()
    
    _CACHE[cache_key] = table_data
    return table_data


def get_mortality_table_info() -> list[Dict[str, Any]]:
    """Retorna informações sobre todas as tábuas disponíveis"""
    return [
        {
            "code": code,
            "name": table["name"],
            "description": table["description"],
            "source": table["source"],
            "is_official": table["is_official"],
            "regulatory_approved": table["regulatory_approved"]
        }
        for code, table in MORTALITY_TABLES.items()
    ]


def validate_mortality_table(table_code: str) -> bool:
    """Valida se a tábua existe"""
    return table_code in MORTALITY_TABLES