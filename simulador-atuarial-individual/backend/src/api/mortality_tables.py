from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Query
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import pandas as pd
import numpy as np
from io import StringIO

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


@router.get("/{table_id}/data")
async def get_mortality_table_data(
    table_id: int,
    format: str = Query("dict", description="Formato: 'dict' ou 'chart'"),
    min_age: int = Query(None, description="Idade mínima"),
    max_age: int = Query(None, description="Idade máxima"),
    session: Session = Depends(get_session)
):
    """Obtém dados da tábua de mortalidade (compatível com gráficos)"""
    table = validate_table_access(table_id, session)
    
    if not table.is_active:
        raise HTTPException(status_code=400, detail="Tábua de mortalidade não está ativa")
    
    table_data = table.get_table_data()
    
    # Aplicar filtros de idade se fornecidos
    if min_age is not None or max_age is not None:
        filtered_data = {}
        for age, qx in table_data.items():
            if min_age is not None and age < min_age:
                continue
            if max_age is not None and age > max_age:
                continue
            filtered_data[age] = qx
        table_data = filtered_data
    
    if format == "chart":
        # Formato para gráficos Chart.js
        return {
            "success": True,
            "table_info": {
                "id": table.id,
                "name": table.name,
                "code": table.code,
                "gender": table.gender
            },
            "data": [
                {"age": int(age), "qx": float(qx)} 
                for age, qx in sorted(table_data.items())
            ],
            "count": len(table_data)
        }
    else:
        # Formato original (dict)
        return {str(k): v for k, v in table_data.items()}


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


# ============================================================================
# NOVOS ENDPOINTS PARA INTERFACE DE GERENCIAMENTO
# ============================================================================

class CSVValidator:
    """Validador para arquivos CSV de tábuas de mortalidade"""
    
    @staticmethod
    def validate_csv_content(content: str) -> Dict[str, Any]:
        """Valida o conteúdo do CSV e retorna dados estruturados"""
        try:
            # Tentar diferentes separadores
            separators = [',', ';', '\t']
            df = None
            used_separator = ','
            
            for sep in separators:
                try:
                    df_test = pd.read_csv(StringIO(content), sep=sep)
                    if len(df_test.columns) > 1:  # Pelo menos 2 colunas
                        df = df_test
                        used_separator = sep
                        break
                except:
                    continue
            
            if df is None:
                return {"valid": False, "error": "Não foi possível interpretar o arquivo CSV"}
            
            # Identificar colunas necessárias
            age_col = None
            qx_col = None
            gender_col = None
            
            # Buscar colunas por nomes comuns
            for col in df.columns:
                col_lower = col.lower().strip()
                if col_lower in ['idade', 'age', 'x']:
                    age_col = col
                elif col_lower in ['qx', 'mortality_rate', 'taxa_mortalidade', 'probabilidade']:
                    qx_col = col
                elif col_lower in ['genero', 'gender', 'sexo', 'sex']:
                    gender_col = col
            
            if age_col is None:
                return {"valid": False, "error": "Coluna de idade não encontrada (esperado: idade, age, x)"}
            
            if qx_col is None:
                return {"valid": False, "error": "Coluna de qx não encontrada (esperado: qx, mortality_rate, taxa_mortalidade)"}
            
            # Validar dados
            df_clean = df.dropna(subset=[age_col, qx_col])
            
            # Validar idades
            try:
                ages = pd.to_numeric(df_clean[age_col], errors='coerce')
                if ages.isna().any():
                    return {"valid": False, "error": "Valores de idade inválidos encontrados"}
                
                if ages.min() < 0 or ages.max() > 130:
                    return {"valid": False, "error": "Idades fora do intervalo válido (0-130)"}
                
            except Exception as e:
                return {"valid": False, "error": f"Erro ao validar idades: {str(e)}"}
            
            # Validar qx
            try:
                qx_values = pd.to_numeric(df_clean[qx_col], errors='coerce')
                if qx_values.isna().any():
                    return {"valid": False, "error": "Valores de qx inválidos encontrados"}
                
                if qx_values.min() < 0 or qx_values.max() > 1:
                    return {"valid": False, "error": "Valores de qx fora do intervalo válido (0-1)"}
                
            except Exception as e:
                return {"valid": False, "error": f"Erro ao validar qx: {str(e)}"}
            
            # Preparar dados para resposta
            table_data = {}
            for _, row in df_clean.iterrows():
                age = int(row[age_col])
                qx = float(row[qx_col])
                table_data[age] = qx
            
            return {
                "valid": True,
                "separator": used_separator,
                "columns": {
                    "age": age_col,
                    "qx": qx_col,
                    "gender": gender_col
                },
                "records_count": len(table_data),
                "age_range": {"min": int(ages.min()), "max": int(ages.max())},
                "qx_range": {"min": float(qx_values.min()), "max": float(qx_values.max())},
                "preview_data": dict(list(table_data.items())[:10]),  # Primeiros 10 registros
                "table_data": table_data
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Erro ao processar CSV: {str(e)}"}


@router.post("/admin/upload-csv")
async def upload_csv_table(
    file: UploadFile = File(...),
    name: str = Query(..., description="Nome da tábua"),
    description: str = Query("", description="Descrição da tábua"),
    country: str = Query("BR", description="País de origem"),
    gender: str = Query(..., description="Gênero (M/F)"),
    session: Session = Depends(get_session)
):
    """Upload e validação de arquivo CSV para nova tábua de mortalidade"""
    
    # Verificar tipo do arquivo
    if not file.content_type or 'csv' not in file.content_type.lower():
        if not file.filename or not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser um CSV")
    
    try:
        # Ler conteúdo do arquivo
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Validar conteúdo
        validation_result = CSVValidator.validate_csv_content(text_content)
        
        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])
        
        # Criar código único para a tábua
        import hashlib
        import time
        code = f"CSV_{hashlib.md5(f'{name}_{time.time()}'.encode()).hexdigest()[:8]}_{gender}"
        
        # Criar entrada no banco
        repo = MortalityTableRepository(session)
        
        # Verificar se já existe
        existing = repo.get_by_code(code)
        if existing:
            raise HTTPException(status_code=400, detail="Tábua com este código já existe")
        
        # Criar nova tábua
        new_table = MortalityTable(
            name=name,
            code=code,
            description=description,
            country=country,
            gender=gender,
            source="csv",
            source_id=file.filename or "uploaded_file.csv",
            is_official=False,  # Tábuas carregadas via CSV não são oficiais por padrão
            regulatory_approved=False,
            is_active=True,
            last_loaded=datetime.utcnow()
        )
        
        # Definir dados da tábua
        new_table.set_table_data(validation_result["table_data"])
        
        # Definir metadados
        metadata = {
            "upload_info": {
                "filename": file.filename,
                "size": len(content),
                "separator": validation_result["separator"],
                "columns_mapped": validation_result["columns"],
                "records_count": validation_result["records_count"],
                "age_range": validation_result["age_range"],
                "qx_range": validation_result["qx_range"]
            },
            "validation_timestamp": datetime.utcnow().isoformat(),
            "upload_timestamp": datetime.utcnow().isoformat()
        }
        new_table.set_metadata(metadata)
        
        # Salvar no banco
        created_table = repo.create(new_table)
        
        logger.info(f"Tábua CSV '{name}' carregada com sucesso: {code}")
        
        return {
            "success": True,
            "message": f"Tábua '{name}' carregada com sucesso",
            "table": _table_to_dict(created_table),
            "validation_info": {
                "records_count": validation_result["records_count"],
                "age_range": validation_result["age_range"],
                "qx_range": validation_result["qx_range"]
            }
        }
        
    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Arquivo deve estar codificado em UTF-8")
    except Exception as e:
        logger.error(f"Erro ao processar upload CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/admin/search-pymort")
async def search_pymort_tables(
    query: str = Query(..., description="Termo de busca"),
    limit: int = Query(20, description="Limite de resultados")
):
    """Busca tábuas no pymort por termo"""
    loader = MortalityTableLoader()
    
    if "pymort" not in loader.get_available_sources():
        raise HTTPException(status_code=400, detail="pymort não está disponível")
    
    try:
        # Base expandida de tábuas SOA conhecidas e funcionais
        # Incluindo tábuas populares de anuidades, seguros de vida e outras
        known_soa_tables = [
            # Tábuas de Anuidades
            {"id": 825, "name": "1983 GAM Female", "description": "1983 Group Annuity Mortality Table – Female", "category": "Annuitant Mortality"},
            {"id": 826, "name": "1983 GAM Male", "description": "1983 Group Annuity Mortality Table – Male", "category": "Annuitant Mortality"},
            {"id": 3262, "name": "2015 VBT Male Smoker", "description": "2015 Valuation Basic Table - Male 100%, Smoker", "category": "Insured Lives Mortality"},
            {"id": 809, "name": "1951 GAM Male", "description": "1951 Group Annuity Mortality (GAM) Table – Male", "category": "Annuitant Mortality"},
            {"id": 810, "name": "1951 GAM Female", "description": "1951 Group Annuity Mortality (GAM) Table – Female", "category": "Annuitant Mortality"},
            
            # Tábuas CSO
            {"id": 1, "name": "1941 CSO Basic ANB", "description": "1941 Commissioners Standard Ordinary Basic Table", "category": "CSO/CET"},
            {"id": 2, "name": "1941 CSO Experience ANB", "description": "1941 Commissioners Standard Ordinary Experience Table", "category": "CSO/CET"},
            {"id": 3, "name": "1941 CSO Standard ANB", "description": "1941 Commissioners Standard Ordinary Table", "category": "CSO/CET"},
            {"id": 17, "name": "1958 CSO ANB", "description": "1958 Commissioners Standard Ordinary Table", "category": "CSO/CET"},
            {"id": 20, "name": "1980 CSO Basic Male ANB", "description": "1980 Commissioners Standard Ordinary Basic Table - Male", "category": "CSO/CET"},
            {"id": 21, "name": "1980 CSO Basic Female ANB", "description": "1980 Commissioners Standard Ordinary Basic Table - Female", "category": "CSO/CET"},
            
            # Tábuas de População
            {"id": 500, "name": "US Life Tables 1959-61", "description": "United States Life Tables 1959-61 – Total Population", "category": "Population Mortality"},
            {"id": 501, "name": "US Life Tables 1959-61 Male", "description": "United States Life Tables 1959-61 – Male", "category": "Population Mortality"},
            {"id": 502, "name": "US Life Tables 1959-61 Female", "description": "United States Life Tables 1959-61 – Female", "category": "Population Mortality"},
            
            # Escalas de Projeção
            {"id": 900, "name": "Projection Scale A", "description": "Mortality Improvement Projection Scale A", "category": "Projection Scale"},
            {"id": 901, "name": "Projection Scale B", "description": "Mortality Improvement Projection Scale B", "category": "Projection Scale"},
            
            # Tábuas de Pensão e Anuidades Modernas
            {"id": 1426, "name": "UP-94 Male", "description": "1994 Unisex Pension Table - Male", "category": "Pension"},
            {"id": 1427, "name": "UP-94 Female", "description": "1994 Unisex Pension Table - Female", "category": "Pension"},
            {"id": 1613, "name": "RP-2000 Combined Healthy", "description": "RP-2000 Combined Healthy Mortality Table", "category": "Pension"},
            {"id": 1614, "name": "RP-2000 Employee", "description": "RP-2000 Employee Mortality Table", "category": "Pension"},
            {"id": 1615, "name": "RP-2000 Healthy Annuitant", "description": "RP-2000 Healthy Annuitant Mortality Table", "category": "Annuitant Mortality"},
            
            # Tábuas VBT 2015
            {"id": 3260, "name": "2015 VBT Male Non-Smoker", "description": "2015 Valuation Basic Table - Male 100%, Non-Smoker", "category": "Insured Lives Mortality"},
            {"id": 3261, "name": "2015 VBT Female Non-Smoker", "description": "2015 Valuation Basic Table - Female 100%, Non-Smoker", "category": "Insured Lives Mortality"},
            {"id": 3263, "name": "2015 VBT Female Smoker", "description": "2015 Valuation Basic Table - Female 100%, Smoker", "category": "Insured Lives Mortality"},
        ]
        
        # Filtrar por query se fornecida
        if query:
            query_lower = query.lower()
            filtered_tables = []
            
            for table in known_soa_tables:
                # Buscar em nome, descrição e categoria
                search_text = f"{table['name']} {table['description']} {table['category']}".lower()
                
                # Busca por termos individuais para melhor flexibilidade
                query_terms = query_lower.split()
                if any(term in search_text for term in query_terms):
                    filtered_tables.append(table)
        else:
            filtered_tables = known_soa_tables
        
        # Ordenar por relevância (tábuas mais modernas primeiro)
        filtered_tables.sort(key=lambda x: x["id"], reverse=True)
        
        return {
            "success": True,
            "query": query,
            "results": filtered_tables[:limit],
            "total_found": len(filtered_tables),
            "note": "Tábuas disponíveis na base SOA conhecida. Para tábuas específicas, use o ID diretamente."
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar no pymort: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@router.get("/{table_id}/statistics")
async def get_table_statistics(
    table_id: int,
    session: Session = Depends(get_session)
):
    """Obtém estatísticas detalhadas de uma tábua"""
    table = validate_table_access(table_id, session)
    
    try:
        table_data = table.get_table_data()
        
        if not table_data:
            raise HTTPException(status_code=400, detail="Tábua não possui dados")
        
        ages = list(table_data.keys())
        qx_values = list(table_data.values())
        
        # Converter para numpy para cálculos
        ages_array = np.array(ages)
        qx_array = np.array(qx_values)
        
        # Calcular estatísticas
        stats = {
            "basic_stats": {
                "records_count": len(table_data),
                "age_range": {"min": int(ages_array.min()), "max": int(ages_array.max())},
                "qx_stats": {
                    "min": float(qx_array.min()),
                    "max": float(qx_array.max()),
                    "mean": float(qx_array.mean()),
                    "median": float(np.median(qx_array)),
                    "std": float(qx_array.std())
                }
            },
            "age_groups": {
                "young": {"ages": "0-20", "avg_qx": float(qx_array[ages_array <= 20].mean()) if any(ages_array <= 20) else 0},
                "adult": {"ages": "21-65", "avg_qx": float(qx_array[(ages_array > 20) & (ages_array <= 65)].mean()) if any((ages_array > 20) & (ages_array <= 65)) else 0},
                "elderly": {"ages": "65+", "avg_qx": float(qx_array[ages_array > 65].mean()) if any(ages_array > 65) else 0}
            },
            "percentiles": {
                "p25": float(np.percentile(qx_array, 25)),
                "p50": float(np.percentile(qx_array, 50)),
                "p75": float(np.percentile(qx_array, 75)),
                "p90": float(np.percentile(qx_array, 90)),
                "p95": float(np.percentile(qx_array, 95))
            }
        }
        
        return {
            "success": True,
            "table_info": {
                "id": table.id,
                "name": table.name,
                "code": table.code,
                "gender": table.gender
            },
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas da tábua {table_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {str(e)}")


@router.get("/admin/compare")
async def compare_tables(
    table_ids: str = Query(..., description="IDs das tábuas separados por vírgula"),
    session: Session = Depends(get_session)
):
    """Compara múltiplas tábuas de mortalidade"""
    try:
        # Parsear IDs
        ids = [int(id.strip()) for id in table_ids.split(',') if id.strip()]
        
        if len(ids) < 2:
            raise HTTPException(status_code=400, detail="Pelo menos 2 tábuas são necessárias para comparação")
        
        if len(ids) > 10:
            raise HTTPException(status_code=400, detail="Máximo de 10 tábuas para comparação")
        
        # Buscar tábuas
        tables = []
        for table_id in ids:
            table = validate_table_access(table_id, session)
            tables.append(table)
        
        # Preparar dados para comparação
        comparison_data = {
            "tables": [],
            "ages_union": set(),
            "comparison_matrix": {}
        }
        
        # Coletar dados de todas as tábuas
        for table in tables:
            table_data = table.get_table_data()
            
            table_info = {
                "id": table.id,
                "name": table.name,
                "code": table.code,
                "gender": table.gender,
                "source": table.source,
                "data": table_data,
                "age_range": {"min": min(table_data.keys()), "max": max(table_data.keys())},
                "records_count": len(table_data)
            }
            
            comparison_data["tables"].append(table_info)
            comparison_data["ages_union"].update(table_data.keys())
        
        # Criar matriz de comparação para idades comuns
        common_ages = sorted(comparison_data["ages_union"])
        comparison_matrix = {}
        
        for age in common_ages:
            age_data = {"age": age, "tables": {}}
            for table_info in comparison_data["tables"]:
                if age in table_info["data"]:
                    age_data["tables"][table_info["code"]] = table_info["data"][age]
                else:
                    age_data["tables"][table_info["code"]] = None
            
            comparison_matrix[age] = age_data
        
        comparison_data["comparison_matrix"] = comparison_matrix
        comparison_data["ages_union"] = common_ages
        
        return {
            "success": True,
            "comparison": comparison_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="IDs inválidos fornecidos")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao comparar tábuas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na comparação: {str(e)}")


@router.post("/admin/{table_id}/toggle-active")
async def toggle_table_active(
    table_id: int,
    session: Session = Depends(get_session)
):
    """Ativa ou desativa uma tábua de mortalidade"""
    table = validate_table_access(table_id, session, allow_system=False)
    
    # Alternar status
    table.is_active = not table.is_active
    table.updated_at = datetime.utcnow()
    
    session.add(table)
    session.commit()
    session.refresh(table)
    
    status = "ativada" if table.is_active else "desativada"
    logger.info(f"Tábua {table.name} foi {status}")
    
    return {
        "success": True,
        "message": f"Tábua '{table.name}' foi {status}",
        "table": _table_to_dict(table)
    }