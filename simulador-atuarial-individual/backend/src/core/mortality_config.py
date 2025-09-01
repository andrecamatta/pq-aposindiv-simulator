import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

from ..models.database import MortalityTable

logger = logging.getLogger(__name__)


class MortalityTableConfig:
    """Gerenciador de configuração de tábuas de mortalidade"""
    
    def __init__(self, config_file: str = "mortality_tables_config.json"):
        self.config_file = Path(config_file)
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo JSON"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar configuração: {e}")
        
        # Configuração padrão
        return {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat(),
            "required_tables": [],
            "optional_tables": [],
            "sources_config": {
                "pymort": {
                    "enabled": True,
                    "cache_duration_hours": 24
                },
# pyliferisk removido - não é mais necessário
                "local": {
                    "enabled": True,
                    "data_directory": "data/mortality_tables"
                }
            }
        }
    
    def save_config(self):
        """Salva configuração no arquivo JSON"""
        try:
            self.config_data["updated_at"] = datetime.utcnow().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    def get_required_tables(self) -> List[Dict[str, Any]]:
        """Retorna lista de tábuas obrigatórias"""
        return self.config_data.get("required_tables", [])
    
    def get_optional_tables(self) -> List[Dict[str, Any]]:
        """Retorna lista de tábuas opcionais"""
        return self.config_data.get("optional_tables", [])
    
    def get_all_tables(self) -> List[Dict[str, Any]]:
        """Retorna todas as tábuas configuradas"""
        return self.get_required_tables() + self.get_optional_tables()
    
    def add_required_table(self, table_config: Dict[str, Any]):
        """Adiciona tábua obrigatória"""
        if "required_tables" not in self.config_data:
            self.config_data["required_tables"] = []
        
        # Verificar se já existe
        existing = next(
            (t for t in self.config_data["required_tables"] 
             if t.get("code") == table_config.get("code")), 
            None
        )
        
        if existing:
            # Atualizar existente
            existing.update(table_config)
        else:
            # Adicionar nova
            self.config_data["required_tables"].append(table_config)
        
        self.save_config()
    
    def add_optional_table(self, table_config: Dict[str, Any]):
        """Adiciona tábua opcional"""
        if "optional_tables" not in self.config_data:
            self.config_data["optional_tables"] = []
        
        # Verificar se já existe
        existing = next(
            (t for t in self.config_data["optional_tables"] 
             if t.get("code") == table_config.get("code")), 
            None
        )
        
        if existing:
            # Atualizar existente
            existing.update(table_config)
        else:
            # Adicionar nova
            self.config_data["optional_tables"].append(table_config)
        
        self.save_config()
    
    def remove_table(self, table_code: str) -> bool:
        """Remove tábua da configuração"""
        removed = False
        
        # Remover das obrigatórias
        if "required_tables" in self.config_data:
            original_len = len(self.config_data["required_tables"])
            self.config_data["required_tables"] = [
                t for t in self.config_data["required_tables"] 
                if t.get("code") != table_code
            ]
            if len(self.config_data["required_tables"]) < original_len:
                removed = True
        
        # Remover das opcionais
        if "optional_tables" in self.config_data:
            original_len = len(self.config_data["optional_tables"])
            self.config_data["optional_tables"] = [
                t for t in self.config_data["optional_tables"] 
                if t.get("code") != table_code
            ]
            if len(self.config_data["optional_tables"]) < original_len:
                removed = True
        
        if removed:
            self.save_config()
        
        return removed
    
    def is_table_enabled(self, table_code: str) -> bool:
        """Verifica se tábua está habilitada"""
        for table in self.get_all_tables():
            if table.get("code") == table_code:
                return table.get("enabled", True)
        return False
    
    def set_table_enabled(self, table_code: str, enabled: bool):
        """Habilita/desabilita tábua"""
        for table_list in [self.config_data.get("required_tables", []), 
                          self.config_data.get("optional_tables", [])]:
            for table in table_list:
                if table.get("code") == table_code:
                    table["enabled"] = enabled
                    self.save_config()
                    return
    
    def get_source_config(self, source: str) -> Dict[str, Any]:
        """Retorna configuração de uma fonte específica"""
        return self.config_data.get("sources_config", {}).get(source, {})
    
    def update_source_config(self, source: str, config: Dict[str, Any]):
        """Atualiza configuração de uma fonte"""
        if "sources_config" not in self.config_data:
            self.config_data["sources_config"] = {}
        
        if source not in self.config_data["sources_config"]:
            self.config_data["sources_config"][source] = {}
        
        self.config_data["sources_config"][source].update(config)
        self.save_config()
    
    def generate_default_config_from_excel(self, excel_path: str) -> List[Dict[str, Any]]:
        """Gera configuração padrão baseada em análise do Excel"""
        try:
            import pandas as pd
            
            # Ler todas as abas do Excel
            sheets = pd.read_excel(excel_path, sheet_name=None)
            extracted_tables = []
            
            # Procurar por menções de tábuas em todas as abas
            table_patterns = [
                "BR-EMS", "BR_EMS", "AT-2000", "AT_2000", "AT-49", "AT_49",
                "SOA", "SUSEP", "tábua", "tabua", "mortality", "mortalidade"
            ]
            
            for sheet_name, df in sheets.items():
                # Converter DataFrame para string para busca
                df_str = df.to_string().upper()
                
                for pattern in table_patterns:
                    if pattern.upper() in df_str:
                        # Extrair informações da tábua mencionada
                        table_info = {
                            "code": f"EXCEL_{pattern.upper()}_{sheet_name}",
                            "name": f"{pattern} (extraída de {sheet_name})",
                            "source": "excel",
                            "sheet_name": sheet_name,
                            "pattern_found": pattern,
                            "enabled": True,
                            "extracted_from": excel_path,
                            "extraction_date": datetime.utcnow().isoformat()
                        }
                        extracted_tables.append(table_info)
            
            return extracted_tables
            
        except Exception as e:
            logger.error(f"Erro ao analisar Excel {excel_path}: {e}")
            return []
    
    def load_brazilian_standard_tables(self):
        """Carrega configuração padrão de tábuas brasileiras"""
        brazilian_tables = [
            {
                "code": "BR_EMS_2021_M",
                "name": "BR-EMS 2021 Masculina",
                "source": "local",
                "gender": "M",
                "country": "BR",
                "year": 2021,
                "is_official": True,
                "regulatory_approved": True,
                "enabled": True,
                "file_path": "data/mortality_tables/br_ems_2021_male.csv"
            },
            {
                "code": "BR_EMS_2021_F",
                "name": "BR-EMS 2021 Feminina",
                "source": "local",
                "gender": "F",
                "country": "BR",
                "year": 2021,
                "is_official": True,
                "regulatory_approved": True,
                "enabled": True,
                "file_path": "data/mortality_tables/br_ems_2021_female.csv"
            },
            {
                "code": "AT_2000_M",
                "name": "AT-2000 Masculina",
                "source": "local",
                "gender": "M",
                "country": "BR",
                "year": 2000,
                "is_official": True,
                "regulatory_approved": True,
                "enabled": True,
                "file_path": "data/mortality_tables/at_2000_male.csv"
            },
            {
                "code": "AT_2000_F",
                "name": "AT-2000 Feminina",
                "source": "local",
                "gender": "F",
                "country": "BR",
                "year": 2000,
                "is_official": True,
                "regulatory_approved": True,
                "enabled": True,
                "file_path": "data/mortality_tables/at_2000_female.csv"
            }
        ]
        
        # Adicionar como tábuas obrigatórias
        for table in brazilian_tables:
            self.add_required_table(table)
    
    def get_table_config(self, table_code: str) -> Optional[Dict[str, Any]]:
        """Retorna configuração de uma tábua específica"""
        for table in self.get_all_tables():
            if table.get("code") == table_code:
                return table
        return None