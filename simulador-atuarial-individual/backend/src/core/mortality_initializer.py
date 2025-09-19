import logging
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select

from ..models.database import MortalityTable
from ..database import engine
from .mortality_loader import MortalityTableLoader

logger = logging.getLogger(__name__)


class MortalityTableInitializer:
    """Serviço para garantir que tábuas obrigatórias estejam disponíveis na inicialização"""
    
    # Lista fixa de tábuas obrigatórias baseada no Excel "Hipóteses Atuariais por Plano - 2024.xlsx"
    REQUIRED_TABLES = [
        {
            "code": "BR_EMS_2021",
            "name": "BR-EMS 2021 - Experiência Brasileira",
            "description": "Tábua oficial SUSEP baseada em 94M registros (2004-2018)",
            "source": "local",
            "priority": 1,
            "is_official": True,
            "regulatory_approved": True
        },
        {
            "code": "2012_IAM_BASIC",
            "name": "2012 IAM Basic - Individual Annuity Mortality",
            "description": "2012 Individual Annuity Mortality Basic Table (SOA)",
            "source": "pymort",
            "source_id_male": "2581",
            "source_id_female": "2582", 
            "priority": 1,
            "is_official": True,
            "regulatory_approved": False
        },
        {
            "code": "AT_83",
            "name": "AT-83 - Annuity Table 1983",
            "description": "Tábua histórica AT-83 (Annuity Table 1983)",
            "source": "pymort",
            "source_id_male": "826",
            "source_id_female": "825", 
            "priority": 1,
            "is_official": True,
            "regulatory_approved": False
        },
        {
            "code": "GAM_71",
            "name": "GAM-71 - Group Annuity Mortality 1971",
            "description": "Tábua Group Annuity Mortality 1971",
            "source": "pymort",
            "source_id": "809",
            "priority": 2,
            "is_official": True,
            "regulatory_approved": False
        },
        {
            "code": "UP_84",
            "name": "UP-84 - Unisex Pension 1984",
            "description": "Tábua Unisex Pension 1984",
            "source": "pymort", 
            "source_id": "900",
            "priority": 2,
            "is_official": True,
            "regulatory_approved": False
        },
        {
            "code": "MI_85",
            "name": "MI-85 - Mortalidade de Inválidos 1985",
            "description": "Tábua brasileira para mortalidade de inválidos MI-85",
            "source": "local",
            "priority": 2,
            "is_official": True,
            "regulatory_approved": True
        }
# Comentando tábuas que requerem carregamento da internet até implementação completa
        # {
        #     "code": "SOA_2012_IAM",
        #     "name": "SOA 2012 Individual Annuity Mortality", 
        #     "description": "Tábua SOA para anuidades individuais",
        #     "source": "pymort",
        #     "source_id": "2012",
        #     "priority": 2,
        #     "is_official": True,
        #     "regulatory_approved": False
        # }
    ]
    
    def __init__(self):
        self.loader = MortalityTableLoader()
    
    def ensure_required_tables(self, session: Optional[Session] = None) -> Dict[str, Any]:
        """
        Garante que todas as tábuas obrigatórias estejam disponíveis no banco.
        Retorna relatório do processo de inicialização.
        """
        if session is None:
            with Session(engine) as session:
                return self._ensure_tables_with_session(session)
        else:
            return self._ensure_tables_with_session(session)
    
    def _ensure_tables_with_session(self, session: Session) -> Dict[str, Any]:
        """Executa verificação e carregamento com sessão fornecida"""
        report = {
            "total_required": len(self.REQUIRED_TABLES),
            "already_available": 0,
            "successfully_loaded": 0,
            "failed_to_load": 0,
            "errors": [],
            "loaded_tables": [],
            "failed_tables": []
        }
        
        logger.info(f"Verificando {len(self.REQUIRED_TABLES)} tábuas obrigatórias...")
        
        for table_config in self.REQUIRED_TABLES:
            code = table_config["code"]
            logger.debug(f"Verificando tábua: {code}")
            
            # Verificar se a família de tábuas existe (considerando _M e _F)
            if self._is_table_family_available(session, code):
                report["already_available"] += 1
                logger.debug(f"Tábua {code} já disponível")
                continue
            
            # Tentar carregar a tábua
            try:
                source = table_config.get("source", "local")
                source_id = table_config.get("source_id")
                
                # Log detalhado para debug
                logger.debug(f"Carregando {code} de fonte '{source}'" + 
                           (f" (ID: {source_id})" if source_id else ""))
                
                success = self._load_table_family(session, table_config)
                if success:
                    report["successfully_loaded"] += 1
                    report["loaded_tables"].append(code)
                    logger.info(f"Tábua {code} carregada com sucesso")
                else:
                    report["failed_to_load"] += 1
                    report["failed_tables"].append(code)
                    error_msg = f"Falha ao carregar {code} de {source}"
                    if source_id:
                        error_msg += f" (ID: {source_id})"
                    report["errors"].append(error_msg)
                    logger.warning(error_msg)
                    
            except Exception as e:
                report["failed_to_load"] += 1
                report["failed_tables"].append(code)
                error_msg = f"Erro ao carregar {code}: {str(e)}"
                report["errors"].append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        # Log do relatório final
        logger.info(
            f"Inicialização de tábuas concluída: "
            f"{report['already_available']} já disponíveis, "
            f"{report['successfully_loaded']} carregadas, "
            f"{report['failed_to_load']} falharam"
        )
        
        return report
    
    def _is_table_family_available(self, session: Session, family_code: str) -> bool:
        """Verifica se pelo menos uma variante da família de tábuas existe"""
        # Procurar por códigos com sufixos _M/_F ou código exato
        patterns = [family_code, f"{family_code}_M", f"{family_code}_F"]
        
        for pattern in patterns:
            stmt = select(MortalityTable).where(
                MortalityTable.code == pattern,
                MortalityTable.is_active == True
            )
            existing = session.exec(stmt).first()
            if existing:
                return True
        
        return False
    
    def _load_table_family(self, session: Session, table_config: Dict[str, Any]) -> bool:
        """Carrega uma família de tábuas (masculina e feminina)"""
        code = table_config["code"]
        source = table_config.get("source", "local")
        
        success_count = 0
        
        # Tentar carregar versões masculina e feminina
        for gender in ["M", "F"]:
            gender_code = f"{code}_{gender}"
            
            try:
                table = None
                
                if source == "local":
                    # Para tábuas locais, verificar se já estão no sistema antigo
                    table = self._create_local_table(table_config, gender)
                    
                elif source == "pymort":
                    # Usar IDs específicos por gênero se disponível
                    if gender == "M" and "source_id_male" in table_config:
                        source_id = table_config["source_id_male"]
                    elif gender == "F" and "source_id_female" in table_config:
                        source_id = table_config["source_id_female"]
                    else:
                        # Fallback para source_id genérico (backward compatibility)
                        source_id = table_config.get("source_id")
                    
                    if source_id:
                        table = self.loader.load_from_pymort(int(source_id))
                        if table:
                            # Para tábuas pymort, usar o código personalizado em vez de SOA_ID
                            table.code = gender_code
                            table.name = f"{table_config['name']} {'Masculina' if gender == 'M' else 'Feminina'}"
                            
# pyliferisk removido - não é mais necessário
                
                if table:
                    # Atualizar metadados da tábua
                    table.name = f"{table_config['name']} {'Masculina' if gender == 'M' else 'Feminina'}"
                    table.description = table_config.get("description", "")
                    table.source = source
                    table.is_official = table_config.get("is_official", False)
                    table.regulatory_approved = table_config.get("regulatory_approved", False)
                    table.is_active = True
                    table.gender = gender
                    
                    # Salvar no banco
                    session.add(table)
                    session.commit()
                    success_count += 1
                    logger.debug(f"Tábua {gender_code} salva com sucesso")
                    
                else:
                    logger.warning(f"Não foi possível carregar {gender_code} de {source}")
                    
            except Exception as e:
                logger.error(f"Erro ao carregar {gender_code}: {str(e)}", exc_info=True)
        
        # Considera sucesso se pelo menos uma variante foi carregada
        return success_count > 0
    
    def _create_local_table(self, table_config: Dict[str, Any], gender: str) -> Optional[MortalityTable]:
        """Cria tábua local usando dados já disponíveis no sistema"""
        code = table_config["code"]
        
        # Para tábuas locais como BR_EMS_2021 e AT_2000, elas já são carregadas
        # pelo sistema antigo via CSV. Aqui criamos apenas a entrada no banco
        # para compatibilidade com o novo sistema
        
        try:
            from .mortality_tables import get_mortality_table
            
            # Tentar carregar do sistema antigo
            table_data = get_mortality_table(code, gender)
            
            if table_data is not None and len(table_data) > 0:
                # Converter array numpy para formato do banco
                table_dict = {}
                for age, rate in enumerate(table_data):
                    if rate > 0:  # Só incluir idades com taxas válidas
                        table_dict[age] = float(rate)
                
                # Criar entrada no banco
                table = MortalityTable(
                    code=f"{code}_{gender}",
                    name=f"{table_config['name']} {'Masculina' if gender == 'M' else 'Feminina'}",
                    description=table_config.get("description", ""),
                    source="local",
                    gender=gender,
                    is_official=table_config.get("is_official", False),
                    regulatory_approved=table_config.get("regulatory_approved", False),
                    is_active=True
                )
                
                # Definir dados da tábua
                table.set_table_data(table_dict)
                
                return table
            
        except Exception as e:
            logger.error(f"Erro ao criar tábua local {code}_{gender}: {str(e)}")
        
        return None
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """Retorna status atual das tábuas obrigatórias"""
        with Session(engine) as session:
            status = {
                "required_tables": [],
                "total_required": len(self.REQUIRED_TABLES),
                "available_count": 0,
                "missing_count": 0
            }
            
            for table_config in self.REQUIRED_TABLES:
                code = table_config["code"]
                is_available = self._is_table_family_available(session, code)
                
                table_status = {
                    "code": code,
                    "name": table_config["name"],
                    "priority": table_config.get("priority", 999),
                    "available": is_available,
                    "source": table_config.get("source", "unknown")
                }
                
                status["required_tables"].append(table_status)
                
                if is_available:
                    status["available_count"] += 1
                else:
                    status["missing_count"] += 1
            
            return status