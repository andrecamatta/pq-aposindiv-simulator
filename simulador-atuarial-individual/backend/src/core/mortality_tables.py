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
        "name": "AT-2000 - Tábua Atuarial Americana", 
        "description": "Tábua baseada em experiência de seguros individuais americanos (1971-1976), aprovada pela SUSEP para anuidades",
        "source": "SOA (Society of Actuaries) - Aprovada pela SUSEP",
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


# Mapeamento das funções de carregamento (legacy)
# AT_2000 removida - agora usa dados oficiais do banco via pymort
_TABLE_LOADERS = {
    ("BR_EMS_2021", "M"): _load_br_ems_2021_male,
    ("BR_EMS_2021", "F"): _load_br_ems_2021_female,
}

# Cache para evitar recarregamento
_CACHE = {}


def apply_mortality_aggravation(mortality_table: np.ndarray, aggravation_pct: float) -> np.ndarray:
    """
    Aplica agravamento percentual à tábua de mortalidade seguindo padrão de mercado.
    
    IMPORTANTE: No contexto atuarial brasileiro (SUSEP), agravamento é usado como 
    margem de segurança/prudência. Valores positivos tornam o cálculo mais conservador.
    
    Comportamento implementado (padrão de mercado):
    - Agravamento POSITIVO: Reduz mortalidade → Mais benefícios → Maior RMBA → MENOR superávit (mais conservador)
    - Agravamento NEGATIVO: Aumenta mortalidade → Menos benefícios → Menor RMBA → MAIOR superávit (menos conservador)
    
    Args:
        mortality_table: Array numpy com probabilidades de morte anuais (qx)
        aggravation_pct: Percentual de agravamento (-10 a +20)
    
    Returns:
        Array numpy com probabilidades ajustadas
    """
    if aggravation_pct == 0.0:
        return mortality_table.copy()
    
    # CORREÇÃO: Inverter sinal para seguir padrão de mercado (margem de segurança)
    # Agravamento positivo = mais conservador = menor mortalidade = mais benefícios futuros
    aggravation_factor = 1 - (aggravation_pct / 100)  # Sinal invertido
    adjusted_table = mortality_table * aggravation_factor
    
    # Garantir que qx permaneça no intervalo válido [0, 1]
    adjusted_table = np.clip(adjusted_table, 0.0, 1.0)
    
    return adjusted_table


def get_mortality_table(table_code: str, gender: str, aggravation_pct: float = 0.0) -> np.ndarray:
    """Obtém tábua de mortalidade específica com agravamento opcional"""
    # Cache considerando o agravamento
    cache_key = (table_code, gender, aggravation_pct)
    
    if cache_key in _CACHE:
        return _CACHE[cache_key]
    
    # Primeiro, obter a tábua base (sem agravamento)
    base_cache_key = (table_code, gender)
    base_table = None
    
    if base_cache_key in _CACHE:
        base_table = _CACHE[base_cache_key]
    
    # Carregar tábua base se não estiver em cache
    if base_table is None:
        # Primeiro tentar o sistema antigo (compatibilidade)
        if base_cache_key in _TABLE_LOADERS:
            loader = _TABLE_LOADERS[base_cache_key]
            base_table = loader()
            _CACHE[base_cache_key] = base_table
        else:
            # Tentar o sistema novo (banco de dados)
            base_table = _load_from_database(table_code, gender)
            if base_table is not None:
                _CACHE[base_cache_key] = base_table
            else:
                raise ValueError(f"Tábua {table_code} para gênero {gender} não encontrada")
    
    # Aplicar agravamento à tábua base
    adjusted_table = apply_mortality_aggravation(base_table, aggravation_pct)
    _CACHE[cache_key] = adjusted_table
    return adjusted_table


def _load_from_database(table_code: str, gender: str) -> np.ndarray:
    """Carrega tábua do banco de dados"""
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
                return mortality_rates
    
    except Exception as e:
        print(f"Erro ao carregar tábua do banco: {e}")
    
    return None


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