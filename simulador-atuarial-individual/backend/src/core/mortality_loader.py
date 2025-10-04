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

    def list_pymort_tables(self, offset: int = 0, limit: int = 50, search: str = None, category: str = None) -> Dict[str, Any]:
        """Lista tábuas disponíveis no pymort com paginação

        Nota: pymort não fornece lista de tábuas diretamente, então usamos
        uma lista curada de tábuas SOA conhecidas e populares
        """
        if not PYMORT_AVAILABLE:
            logger.error("pymort não está disponível")
            return {"tables": [], "total": 0}

        try:
            # Lista curada expandida de tábuas SOA conhecidas e testadas
            # Baseada em categorias principais: CSO, VBT, GAM, RP, UP, e outras
            all_tables = [
                # CSO - Commissioners Standard Ordinary (1941-2001)
                {'id': 1, 'name': '1941 CSO Basic ANB', 'description': '1941 Commissioners Standard Ordinary Basic Table'},
                {'id': 2, 'name': '1941 CSO Experience ANB', 'description': '1941 Commissioners Standard Ordinary Experience Table'},
                {'id': 3, 'name': '1941 CSO Standard ANB', 'description': '1941 Commissioners Standard Ordinary Table'},
                {'id': 17, 'name': '1958 CSO ANB', 'description': '1958 Commissioners Standard Ordinary Table'},
                {'id': 20, 'name': '1980 CSO Basic Male ANB', 'description': '1980 Commissioners Standard Ordinary Basic Table - Male'},
                {'id': 21, 'name': '1980 CSO Basic Female ANB', 'description': '1980 Commissioners Standard Ordinary Basic Table - Female'},
                {'id': 22, 'name': '1980 CSO Male ANB', 'description': '1980 Commissioners Standard Ordinary - Male'},
                {'id': 23, 'name': '1980 CSO Female ANB', 'description': '1980 Commissioners Standard Ordinary - Female'},
                {'id': 42, 'name': '2001 CSO Male Smoker ANB', 'description': '2001 Commissioners Standard Ordinary - Male Smoker'},
                {'id': 43, 'name': '2001 CSO Male Non-Smoker ANB', 'description': '2001 Commissioners Standard Ordinary - Male Non-Smoker'},
                {'id': 50, 'name': '2001 CSO Female Smoker ANB', 'description': '2001 Commissioners Standard Ordinary - Female Smoker'},
                {'id': 51, 'name': '2001 CSO Female Non-Smoker ANB', 'description': '2001 Commissioners Standard Ordinary - Female Non-Smoker'},

                # VBT - Valuation Basic Table (2008, 2015)
                {'id': 3252, 'name': '2015 VBT Male Non-Smoker', 'description': '2015 Valuation Basic Table - Male 100%, Non-Smoker'},
                {'id': 3262, 'name': '2015 VBT Male Smoker', 'description': '2015 Valuation Basic Table - Male 100%, Smoker'},
                {'id': 3272, 'name': '2015 VBT Female Non-Smoker', 'description': '2015 Valuation Basic Table - Female 100%, Non-Smoker'},
                {'id': 3282, 'name': '2015 VBT Female Smoker', 'description': '2015 Valuation Basic Table - Female 100%, Smoker'},

                # GAM - Group Annuity Mortality
                {'id': 809, 'name': '1951 GAM Male', 'description': '1951 Group Annuity Mortality (GAM) Table – Male'},
                {'id': 810, 'name': '1951 GAM Female', 'description': '1951 Group Annuity Mortality (GAM) Table – Female'},
                {'id': 825, 'name': '1983 GAM Female', 'description': '1983 Group Annuity Mortality Table – Female'},
                {'id': 826, 'name': '1983 GAM Male', 'description': '1983 Group Annuity Mortality Table – Male'},
                {'id': 827, 'name': '1983 GAM Unisex', 'description': '1983 Group Annuity Mortality Table – Unisex'},

                # UP - Uninsured Pensioner
                {'id': 1619, 'name': 'UP-1984 Male', 'description': '1984 Uninsured Pensioner Mortality Table - Male'},
                {'id': 1620, 'name': 'UP-1984 Female', 'description': '1984 Uninsured Pensioner Mortality Table - Female'},

                # RP - Retirement Plan (2014)
                {'id': 1478, 'name': 'RP-2014 Employee Male', 'description': 'RP-2014 Mortality Tables - Employee Male'},
                {'id': 1479, 'name': 'RP-2014 Employee Female', 'description': 'RP-2014 Mortality Tables - Employee Female'},
                {'id': 1487, 'name': 'RP-2014 Healthy Annuitant Male', 'description': 'RP-2014 Mortality Tables - Healthy Annuitant Male'},
                {'id': 1488, 'name': 'RP-2014 Healthy Annuitant Female', 'description': 'RP-2014 Mortality Tables - Healthy Annuitant Female'},
                {'id': 1502, 'name': 'RP-2014 Disabled Retiree Male', 'description': 'RP-2014 Mortality Tables - Disabled Retiree Male'},
                {'id': 1503, 'name': 'RP-2014 Disabled Retiree Female', 'description': 'RP-2014 Mortality Tables - Disabled Retiree Female'},
            ]

            # Processar lista para formato estruturado
            tables_info = []
            for table in all_tables:
                table_id = table['id']
                table_name = table['name']
                table_desc = table['description']

                # Categorizar baseado no nome
                category_name = self._categorize_table(table_name, table_desc)

                # Detectar gênero
                gender = self._detect_gender(table_name, table_desc)

                # Extrair ano se possível
                year = self._extract_year(table_name)

                tables_info.append({
                    'id': table_id,
                    'name': table_name,
                    'description': table_desc,
                    'category': category_name,
                    'gender': gender,
                    'year': year
                })

            # Filtrar por busca se fornecido
            if search:
                search_lower = search.lower()
                tables_info = [
                    t for t in tables_info
                    if search_lower in t['name'].lower()
                    or search_lower in t['description'].lower()
                    or search_lower in t['category'].lower()
                ]

            # Filtrar por categoria se fornecido
            if category and category != 'all':
                tables_info = [t for t in tables_info if t['category'] == category]

            # Ordenar por ID (mais recente primeiro)
            tables_info.sort(key=lambda x: x['id'], reverse=True)

            total = len(tables_info)
            paginated = tables_info[offset:offset+limit]

            return {
                'tables': paginated,
                'total': total,
                'offset': offset,
                'limit': limit,
                'has_more': offset + limit < total
            }

        except Exception as e:
            logger.error(f"Erro ao listar tábuas pymort: {e}")
            return {"tables": [], "total": 0, "error": str(e)}

    def _categorize_table(self, name: str, desc: str) -> str:
        """Categoriza tábua baseado no nome e descrição"""
        combined = f"{name} {desc}".lower()

        if 'cso' in combined:
            return 'CSO'
        elif 'vbt' in combined or 'valuation basic' in combined:
            return 'VBT'
        elif 'gam' in combined or 'group annuity' in combined:
            return 'Anuidades (GAM)'
        elif 'rp-' in combined or 'retirement plan' in combined:
            return 'Previdência (RP)'
        elif 'up-' in combined or 'uninsured pension' in combined:
            return 'Previdência (UP)'
        elif 'annuit' in combined:
            return 'Anuidades'
        elif 'pension' in combined or 'retirement' in combined:
            return 'Previdência'
        elif 'insured' in combined or 'insurance' in combined:
            return 'Seguros'
        elif 'population' in combined:
            return 'População'
        elif 'health' in combined or 'disability' in combined:
            return 'Saúde'
        else:
            return 'Outras'

    def _detect_gender(self, name: str, desc: str) -> str:
        """Detecta gênero baseado no nome e descrição"""
        combined = f"{name} {desc}".lower()

        if 'male' in combined and 'female' not in combined:
            return 'M'
        elif 'female' in combined:
            return 'F'
        elif 'unisex' in combined:
            return 'UNISEX'
        else:
            return 'N/A'

    def _extract_year(self, name: str) -> Optional[int]:
        """Extrai ano do nome da tábua"""
        import re
        # Procurar por anos de 4 dígitos (1900-2099)
        match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
        return int(match.group(1)) if match else None
    
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
            content_class = getattr(xml, 'ContentClassification', None)
            # Extrair TableName do ContentClassification se disponível
            if content_class and hasattr(content_class, 'TableName'):
                table_name = content_class.TableName
            else:
                table_name = f"SOA Table {table_id}"

            # Extrair TableDescription se disponível
            if content_class and hasattr(content_class, 'TableDescription'):
                description = content_class.TableDescription
            else:
                description = ""

            # Detectar gênero baseado no nome da tábua
            gender = None
            table_name_lower = table_name.lower()
            description_lower = description.lower() if description else ""
            combined_text = f"{table_name_lower} {description_lower}"

            if 'male' in combined_text and 'female' not in combined_text:
                gender = 'M'
            elif 'female' in combined_text or 'feminina' in combined_text:
                gender = 'F'
            elif 'unisex' in combined_text or 'unissex' in combined_text:
                gender = 'UNISEX'

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

                # Gerar código com sufixo de gênero quando aplicável
                code = f"SOA_{table_id}"
                if gender in ['M', 'F']:
                    code = f"{code}_{gender}"

                # Criar objeto MortalityTable
                mortality_table = MortalityTable(
                    name=table_name,
                    code=code,
                    description=description,
                    gender=gender,
                    source="pymort",
                    source_id=str(table_id),
                    is_official=True,
                    regulatory_approved=True,
                    is_active=True,
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