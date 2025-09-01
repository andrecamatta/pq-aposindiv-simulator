import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
from pathlib import Path
import json
import hashlib

try:
    import pymort
    PYMORT_AVAILABLE = True
except ImportError:
    PYMORT_AVAILABLE = False

# pyliferisk removido - não é mais necessário
PYLIFERISK_AVAILABLE = False

from ..models.database import MortalityTable

logger = logging.getLogger(__name__)


class MortalityTableLoader:
    """Serviço para carregar tábuas de mortalidade de diferentes fontes"""
    
    def __init__(self):
        self.supported_sources = []
        if PYMORT_AVAILABLE:
            self.supported_sources.append("pymort")
        self.supported_sources.extend(["local", "csv", "excel"])
    
    def get_available_sources(self) -> List[str]:
        """Retorna lista de fontes disponíveis"""
        return self.supported_sources.copy()
    
    def load_from_pymort(self, table_id: int) -> Optional[MortalityTable]:
        """Carrega tábua do pymort (SOA)"""
        if not PYMORT_AVAILABLE:
            logger.error("pymort não está disponível")
            return None
        
        try:
            logger.info(f"✅ Carregando tábua {table_id} do pymort...")
            xml = pymort.MortXML.from_id(table_id)
            
            if not xml:
                logger.error(f"Tábua {table_id} não encontrada no pymort")
                return None
            
            # Extrair informações da tábua dos metadados
            table_name = getattr(xml, 'ContentClassification', f"SOA Table {table_id}")
            description = ""
            
            # Processar dados da tábua
            if hasattr(xml, 'Tables') and len(xml.Tables) > 0:
                # Usar primeira tábua disponível
                table_df = xml.Tables[0].Values
                
                if table_df is None or len(table_df) == 0:
                    logger.error(f"Tábua {table_id} não contém dados válidos")
                    return None
                
                # Converter para formato dict {idade: qx}
                table_data = {}
                for idx, row in table_df.iterrows():
                    try:
                        # O índice é uma tupla (Age, Duration) - queremos Age
                        if isinstance(idx, tuple):
                            age = int(idx[0])  # Primeiro elemento é a idade
                        else:
                            age = int(idx)
                            
                        qx = float(row['vals'])
                        if qx > 0 and qx <= 1:  # Validar taxa (0 < qx <= 1)
                            # Para múltiplas durações, usar a primeira ou fazer média
                            if age not in table_data:
                                table_data[age] = qx
                            # Se já existe, usar valor menor (mais conservador)
                            elif qx < table_data[age]:
                                table_data[age] = qx
                    except (ValueError, KeyError, TypeError) as e:
                        logger.warning(f"Erro ao processar linha da tábua {table_id}: {e}")
                        continue
                
                if len(table_data) == 0:
                    logger.error(f"Nenhum dado válido encontrado na tábua {table_id}")
                    return None
                
                # Validar dados da tábua
                is_valid, errors = self.validate_table_data(table_data)
                if not is_valid:
                    logger.error(f"Dados da tábua {table_id} são inválidos: {'; '.join(errors)}")
                    return None
                
                # Usar metadados da primeira tábua se disponível
                table_metadata = {}
                if hasattr(xml.Tables[0], 'MetaData') and xml.Tables[0].MetaData:
                    metadata = xml.Tables[0].MetaData
                    table_metadata = {
                        "scaling_factor": getattr(metadata, 'ScalingFactor', 0.0),
                        "data_type": getattr(metadata, 'DataType', ''),
                        "nation": getattr(metadata, 'Nation', ''),
                        "table_description": getattr(metadata, 'TableDescription', ''),
                    }
                    # Se description estiver vazio, usar TableDescription
                    if not description and table_metadata["table_description"]:
                        description = table_metadata["table_description"]

                # Criar objeto MortalityTable
                mortality_table = MortalityTable(
                    name=table_name,
                    code=f"SOA_{table_id}",
                    description=description,
                    source="pymort",
                    source_id=str(table_id),
                    is_official=True,
                    regulatory_approved=True,
                    last_loaded=datetime.utcnow()
                )
                
                mortality_table.set_table_data(table_data)
                
                mortality_table.set_metadata({
                    "pymort_table_id": table_id,
                    "content_classification": str(getattr(xml, 'ContentClassification', '')),
                    "table_metadata": table_metadata,
                    "source_url": f"https://mort.soa.org/ViewTable.aspx?&TableIdentity={table_id}",
                    "data_format": "pymort_xml",
                    "load_timestamp": datetime.utcnow().isoformat(),
                    "record_count": len(table_data)
                })
                
                logger.info(f"Tábua {table_id} carregada com sucesso ({len(table_data)} registros)")
                return mortality_table
            else:
                logger.error(f"Tábua {table_id} não contém tabelas de dados")
                return None
                
        except ConnectionError as e:
            logger.error(f"Erro de conexão ao carregar tábua {table_id}: {e}")
            return None
        except ImportError as e:
            logger.error(f"Erro de importação ao carregar tábua {table_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar tábua {table_id}: {e}", exc_info=True)
            return None
    
# Função load_from_pyliferisk removida - pyliferisk não é mais necessário
    
    def load_from_csv(self, file_path: str, **kwargs) -> Optional[MortalityTable]:
        """Carrega tábua de arquivo CSV"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Arquivo não encontrado: {file_path}")
                return None
            
            df = pd.read_csv(path, **kwargs)
            
            # Validar colunas necessárias
            required_cols = {'idade', 'qx'} if 'idade' in df.columns else {'age', 'qx'}
            if not required_cols.issubset(df.columns):
                logger.error(f"Arquivo CSV deve conter colunas {required_cols}")
                return None
            
            age_col = 'idade' if 'idade' in df.columns else 'age'
            
            # Converter para dict {idade: qx}
            table_data = {}
            for _, row in df.iterrows():
                age = int(row[age_col])
                qx = float(row['qx'])
                table_data[age] = qx
            
            # Criar código hash do arquivo para controle de versão
            file_hash = self._generate_file_hash(path)
            
            mortality_table = MortalityTable(
                name=path.stem,
                code=f"CSV_{path.stem}",
                description=f"Tábua carregada de {path.name}",
                source="csv",
                source_id=str(path),
                version=file_hash[:8],
                last_loaded=datetime.utcnow()
            )
            
            mortality_table.set_table_data(table_data)
            mortality_table.set_metadata({
                "file_path": str(path),
                "file_hash": file_hash,
                "file_size": path.stat().st_size,
                "load_timestamp": datetime.utcnow().isoformat()
            })
            
            return mortality_table
            
        except Exception as e:
            logger.error(f"Erro ao carregar CSV {file_path}: {e}")
            return None
    
    def load_from_excel(self, file_path: str, sheet_name: str = None, **kwargs) -> Optional[MortalityTable]:
        """Carrega tábua de arquivo Excel"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Arquivo não encontrado: {file_path}")
                return None
            
            df = pd.read_excel(path, sheet_name=sheet_name, **kwargs)
            
            # Validar colunas necessárias
            required_cols = {'idade', 'qx'} if 'idade' in df.columns else {'age', 'qx'}
            if not required_cols.issubset(df.columns):
                logger.error(f"Arquivo Excel deve conter colunas {required_cols}")
                return None
            
            age_col = 'idade' if 'idade' in df.columns else 'age'
            
            # Converter para dict {idade: qx}
            table_data = {}
            for _, row in df.iterrows():
                age = int(row[age_col])
                qx = float(row['qx'])
                table_data[age] = qx
            
            file_hash = self._generate_file_hash(path)
            sheet_suffix = f"_{sheet_name}" if sheet_name else ""
            
            mortality_table = MortalityTable(
                name=f"{path.stem}{sheet_suffix}",
                code=f"EXCEL_{path.stem}{sheet_suffix}",
                description=f"Tábua carregada de {path.name}" + (f" aba {sheet_name}" if sheet_name else ""),
                source="excel",
                source_id=f"{path}#{sheet_name}" if sheet_name else str(path),
                version=file_hash[:8],
                last_loaded=datetime.utcnow()
            )
            
            mortality_table.set_table_data(table_data)
            mortality_table.set_metadata({
                "file_path": str(path),
                "sheet_name": sheet_name,
                "file_hash": file_hash,
                "file_size": path.stat().st_size,
                "load_timestamp": datetime.utcnow().isoformat()
            })
            
            return mortality_table
            
        except Exception as e:
            logger.error(f"Erro ao carregar Excel {file_path}: {e}")
            return None
    
    def validate_table_data(self, table_data: Dict[int, float]) -> Tuple[bool, List[str]]:
        """Valida dados da tábua de mortalidade"""
        errors = []
        
        if not table_data:
            errors.append("Dados da tábua não podem estar vazios")
            return False, errors
        
        # Verificar se todas as idades são válidas
        for age in table_data.keys():
            if not isinstance(age, int) or age < 0 or age > 150:
                errors.append(f"Idade inválida: {age}")
        
        # Verificar se todas as taxas são válidas
        for age, qx in table_data.items():
            if not isinstance(qx, (int, float)) or qx < 0 or qx > 1:
                errors.append(f"Taxa de mortalidade inválida para idade {age}: {qx}")
        
        return len(errors) == 0, errors
    
# Função get_pyliferisk_tables removida - pyliferisk não é mais necessário
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """Gera hash SHA-256 de um arquivo para controle de versão"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()