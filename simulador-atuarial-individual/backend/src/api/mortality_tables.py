from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..database import get_session, engine
from ..models.database import MortalityTable
from ..repositories.mortality_repository import MortalityTableRepository
from ..core.mortality_loader import MortalityTableLoader
from ..core.mortality_config import MortalityTableConfig
from ..core.mortality_initializer import MortalityTableInitializer
from ..utils.session_manager import with_background_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mortality-tables", tags=["mortality-tables"])


def _table_to_dict(table: MortalityTable) -> Dict[str, Any]:
    """Converte uma MortalityTable para dicionário de resposta padrão"""
    return {
        "id": table.id,
        "name": table.name,
        "code": table.code,
        "description": table.description,
        "country": table.country,
        "year": table.year,
        "gender": table.gender,
        "source": table.source,
        "source_id": table.source_id,
        "version": table.version,
        "is_official": table.is_official,
        "regulatory_approved": table.regulatory_approved,
        "is_active": table.is_active,
        "is_system": table.is_system,
        "last_loaded": table.last_loaded.isoformat() if table.last_loaded else None,
        "created_at": table.created_at.isoformat(),
        "metadata": table.get_metadata()
    }


class BackgroundTaskHandler:
    """Classe para gerenciar tarefas de background com padrões comuns"""
    
    def __init__(self, session: Session):
        self.session = session
        self.repo = MortalityTableRepository(session)
        self.loader = MortalityTableLoader()
    
    async def reload_table(self, table_id: int) -> bool:
        """Recarrega uma tábua específica"""
        try:
            table = self.repo.get_by_id(table_id)
            if not table:
                return False
            
            new_table = None
            if table.source == "pymort" and table.source_id:
                new_table = self.loader.load_from_pymort(int(table.source_id))
            elif table.source in ["csv", "excel"] and table.source_id:
                if table.source == "csv":
                    new_table = self.loader.load_from_csv(table.source_id)
                else:
                    metadata = table.get_metadata()
                    sheet_name = metadata.get("sheet_name")
                    new_table = self.loader.load_from_excel(table.source_id, sheet_name)
            
            if new_table:
                table.table_data = new_table.table_data
                table.table_metadata = new_table.table_metadata
                table.version = new_table.version
                table.last_loaded = datetime.utcnow()
                table.updated_at = datetime.utcnow()
                
                self.session.add(table)
                self.session.commit()
                logger.info(f"Tábua {table.name} recarregada com sucesso")
                return True
            else:
                logger.error(f"Falha ao recarregar tábua {table.name}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao recarregar tábua {table_id}: {e}")
            return False
    
    async def load_table_from_config(self, config: Dict[str, Any]) -> bool:
        """Carrega uma tábua baseada na configuração"""
        try:
            source = config.get("source")
            table_code = config.get("code")
            
            # Verificar se já existe
            existing = self.repo.get_by_code(table_code)
            if existing:
                logger.info(f"Tábua {table_code} já existe no banco")
                return True
            
            new_table = None
            
            if source == "pymort" and config.get("source_id"):
                new_table = self.loader.load_from_pymort(int(config["source_id"]))
            elif source in ["csv", "excel", "local"] and config.get("file_path"):
                if source in ["csv", "local"]:
                    new_table = self.loader.load_from_csv(config["file_path"])
                else:
                    sheet_name = config.get("sheet_name")
                    new_table = self.loader.load_from_excel(config["file_path"], sheet_name)
            
            if new_table:
                # Aplicar configurações adicionais
                new_table.code = table_code
                if config.get("name"):
                    new_table.name = config["name"]
                if config.get("description"):
                    new_table.description = config["description"]
                if config.get("country"):
                    new_table.country = config["country"]
                if config.get("year"):
                    new_table.year = config["year"]
                if config.get("gender"):
                    new_table.gender = config["gender"]
                if config.get("is_official"):
                    new_table.is_official = config["is_official"]
                if config.get("regulatory_approved"):
                    new_table.regulatory_approved = config["regulatory_approved"]
                
                new_table.is_active = config.get("enabled", True)
                
                self.repo.create(new_table)
                logger.info(f"Tábua {table_code} carregada com sucesso")
                return True
            else:
                logger.error(f"Falha ao carregar tábua {table_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao carregar tábua {config.get('code', 'unknown')}: {e}")
            return False


def validate_table_access(table_id: int, session: Session, allow_system: bool = True) -> MortalityTable:
    """Valida acesso a uma tábua e retorna a instância ou levanta exceção"""
    repo = MortalityTableRepository(session)
    table = repo.get_by_id(table_id)
    
    if not table:
        raise HTTPException(status_code=404, detail="Tábua de mortalidade não encontrada")
    
    if not allow_system and table.is_system:
        raise HTTPException(status_code=400, detail="Tábuas do sistema não podem ser modificadas")
    
    return table


@router.get("/", response_model=List[Dict[str, Any]])
async def list_mortality_tables(
    active_only: bool = True,
    session: Session = Depends(get_session)
):
    """Lista todas as tábuas de mortalidade disponíveis"""
    repo = MortalityTableRepository(session)
    
    if active_only:
        tables = repo.get_active_tables()
    else:
        tables = repo.get_all()
    
    return [_table_to_dict(table) for table in tables]


@router.get("/{table_id}", response_model=Dict[str, Any])
async def get_mortality_table(
    table_id: int,
    include_data: bool = False,
    session: Session = Depends(get_session)
):
    """Obtém detalhes de uma tábua específica"""
    table = validate_table_access(table_id, session)
    
    result = _table_to_dict(table)
    
    if include_data:
        result["table_data"] = table.get_table_data()
    
    return result


@router.get("/{table_id}/data", response_model=Dict[str, float])
async def get_mortality_table_data(
    table_id: int,
    session: Session = Depends(get_session)
):
    """Obtém apenas os dados da tábua de mortalidade"""
    table = validate_table_access(table_id, session)
    
    if not table.is_active:
        raise HTTPException(status_code=400, detail="Tábua de mortalidade não está ativa")
    
    return {str(k): v for k, v in table.get_table_data().items()}


@router.post("/reload/{table_id}")
async def reload_mortality_table(
    table_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Recarrega uma tábua específica da sua fonte original"""
    table = validate_table_access(table_id, session, allow_system=False)
    
    # Agendar recarregamento em background
    background_tasks.add_task(_reload_table_background, table_id)
    
    return {"message": f"Recarregamento da tábua {table.name} iniciado"}


@router.post("/reload-all")
async def reload_all_tables(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Recarrega todas as tábuas configuradas"""
    config = MortalityTableConfig()
    
    # Obter todas as tábuas configuradas
    configured_tables = config.get_all_tables()
    enabled_tables = [t for t in configured_tables if t.get("enabled", True)]
    
    # Agendar recarregamento em background
    background_tasks.add_task(_reload_all_tables_background, enabled_tables)
    
    return {"message": f"Recarregamento de {len(enabled_tables)} tábuas iniciado"}


@router.post("/load-from-config")
async def load_tables_from_config(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Carrega tábuas baseado na configuração atual"""
    config = MortalityTableConfig()
    
    # Carregar configuração padrão se não existir
    if not config.get_all_tables():
        config.load_brazilian_standard_tables()
    
    enabled_tables = [t for t in config.get_all_tables() if t.get("enabled", True)]
    
    # Agendar carregamento em background
    background_tasks.add_task(_load_tables_from_config_background, enabled_tables)
    
    return {"message": f"Carregamento de {len(enabled_tables)} tábuas iniciado"}


@router.get("/config/")
async def get_tables_config():
    """Obtém configuração atual das tábuas"""
    config = MortalityTableConfig()
    
    return {
        "required_tables": config.get_required_tables(),
        "optional_tables": config.get_optional_tables(),
        "sources_config": config.config_data.get("sources_config", {}),
        "version": config.config_data.get("version"),
        "updated_at": config.config_data.get("updated_at")
    }


@router.put("/config/{table_code}/enabled")
async def set_table_enabled(
    table_code: str,
    enabled: bool,
    session: Session = Depends(get_session)
):
    """Habilita/desabilita uma tábua"""
    config = MortalityTableConfig()
    config.set_table_enabled(table_code, enabled)
    
    # Atualizar status no banco de dados se existir
    repo = MortalityTableRepository(session)
    table = repo.get_by_code(table_code)
    if table:
        table.is_active = enabled
        table.updated_at = datetime.utcnow()
        session.add(table)
        session.commit()
    
    return {"message": f"Tábua {table_code} {'habilitada' if enabled else 'desabilitada'}"}


@router.delete("/{table_id}")
async def delete_mortality_table(
    table_id: int,
    session: Session = Depends(get_session)
):
    """Remove uma tábua do banco de dados"""
    table = validate_table_access(table_id, session, allow_system=False)
    
    repo = MortalityTableRepository(session)
    repo.delete(table)
    
    return {"message": f"Tábua {table.name} removida com sucesso"}


@router.get("/sources/available")
async def get_available_sources():
    """Lista fontes de tábuas disponíveis"""
    loader = MortalityTableLoader()
    
    result = {
        "supported_sources": loader.get_available_sources(),
        "pymort_available": "pymort" in loader.get_available_sources()
    }
    
    return result


@router.post("/load/pymort/{table_id}")
async def load_from_pymort(
    table_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Carrega tábua específica do pymort"""
    loader = MortalityTableLoader()
    
    if "pymort" not in loader.get_available_sources():
        raise HTTPException(status_code=400, detail="pymort não está disponível")
    
    # Agendar carregamento em background
    background_tasks.add_task(_load_from_pymort_background, table_id)
    
    return {"message": f"Carregamento da tábua SOA {table_id} iniciado"}




# Funções de background para processamento assíncrono (usando BackgroundTaskHandler)

@with_background_session
async def _reload_table_background(session: Session, table_id: int):
    """Recarrega uma tábua específica em background"""
    handler = BackgroundTaskHandler(session)
    await handler.reload_table(table_id)


@with_background_session
async def _reload_all_tables_background(session: Session, configured_tables: List[Dict[str, Any]]):
    """Recarrega todas as tábuas em background"""
    handler = BackgroundTaskHandler(session)
    
    for table_config in configured_tables:
        try:
            table_code = table_config.get("code")
            existing_table = handler.repo.get_by_code(table_code)
            
            if existing_table:
                await handler.reload_table(existing_table.id)
            else:
                await handler.load_table_from_config(table_config)
                
        except Exception as e:
            logger.error(f"Erro ao processar tábua {table_config.get('code', 'unknown')}: {e}")


@with_background_session
async def _load_tables_from_config_background(session: Session, configured_tables: List[Dict[str, Any]]):
    """Carrega tábuas da configuração em background"""
    handler = BackgroundTaskHandler(session)
    
    for table_config in configured_tables:
        try:
            await handler.load_table_from_config(table_config)
        except Exception as e:
            logger.error(f"Erro ao carregar tábua {table_config.get('code', 'unknown')}: {e}")


@with_background_session
async def _load_from_pymort_background(session: Session, table_id: int):
    """Carrega tábua do pymort em background"""
    try:
        repo = MortalityTableRepository(session)
        loader = MortalityTableLoader()
        
        new_table = loader.load_from_pymort(table_id)
        if new_table:
            repo.create(new_table)
            logger.info(f"Tábua SOA {table_id} carregada com sucesso")
        else:
            logger.error(f"Falha ao carregar tábua SOA {table_id}")
            
    except Exception as e:
        logger.error(f"Erro ao carregar tábua pymort {table_id}: {e}")



@router.get("/initialization/status")
async def get_initialization_status():
    """Retorna status da inicialização de tábuas obrigatórias"""
    initializer = MortalityTableInitializer()
    status = initializer.get_initialization_status()
    return status


@router.post("/initialization/ensure-required")
async def ensure_required_tables(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Força verificação e carregamento das tábuas obrigatórias"""
    def run_initialization():
        initializer = MortalityTableInitializer()
        with Session(engine) as bg_session:
            return initializer.ensure_required_tables(bg_session)
    
    background_tasks.add_task(run_initialization)
    return {"message": "Verificação de tábuas obrigatórias iniciada em background"}