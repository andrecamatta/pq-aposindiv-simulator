from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import numpy as np
from typing import Dict, Any, List
import uuid

from ..models import SimulatorState, SimulatorResults
from ..models.suggestions import SuggestionsRequest, SuggestionsResponse
from ..core.actuarial_engine import ActuarialEngine
from ..core.suggestions_engine import SuggestionsEngine
from ..core.mortality_tables import get_mortality_table_info, get_mortality_table
from ..core.actuarial_math import calculate_life_expectancy
from ..utils.error_handling import handle_api_errors
from ..utils.state_updater import state_action_handler
from ..utils.response_formatter import response_formatter
from .mortality_tables import router as mortality_tables_router
from .reports_router import router as reports_router

# Função para serializar tipos NumPy
def numpy_serializer(obj):
    """Serializa tipos NumPy para tipos nativos Python"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'dtype') and 'numpy' in str(type(obj)):
        return str(obj)
    raise TypeError(f"Objeto do tipo {type(obj)} não é serializável JSON")

# Classe customizada para JSONResponse que trata NumPy
class NumpyJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=numpy_serializer
        ).encode("utf-8")

app = FastAPI(
    title="PrevLab API",
    description="API para plataforma de simulação atuarial PrevLab",
    version="1.0.0",
    default_response_class=NumpyJSONResponse
)

# Inicializar aplicação
@app.on_event("startup")
async def startup_event():
    import logging
    from ..database import engine, create_db_and_tables
    from ..models.database import MortalityTable, DecrementTable  # Import all models
    from sqlmodel import Session, select

    logger = logging.getLogger(__name__)

    logger.info("Iniciando aplicação...")

    # Criar todas as tabelas (incluindo novas como DecrementTable)
    create_db_and_tables()
    logger.info("✅ Tabelas do banco de dados criadas/verificadas")
    
    # Verificar tábuas de mortalidade disponíveis no banco
    try:
        with Session(engine) as session:
            statement = select(MortalityTable).where(MortalityTable.is_active == True)
            tables = session.exec(statement).all()
            
            # Agrupar por família
            table_families = set()
            for table in tables:
                family_code = table.code
                if family_code.endswith('_M') or family_code.endswith('_F'):
                    family_code = family_code[:-2]
                table_families.add(family_code)
            
            logger.info(f"✅ {len(tables)} tábuas de mortalidade disponíveis no banco")
            logger.info(f"   Famílias: {', '.join(sorted(table_families))}")
            
            # Verificar tábuas essenciais
            essential_tables = ['BR_EMS_2021', 'AT_2000']
            missing = [t for t in essential_tables if t not in table_families]
            if missing:
                logger.warning(f"⚠️  Tábuas essenciais faltando: {', '.join(missing)}")
            else:
                logger.info("✅ Todas as tábuas essenciais estão disponíveis")
    
    except Exception as e:
        logger.error(f"Erro ao verificar tábuas de mortalidade: {e}")
    
    logger.info("Aplicação iniciada com sucesso")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(mortality_tables_router)
app.include_router(reports_router)

# Engines globais
actuarial_engine = ActuarialEngine()
suggestions_engine = SuggestionsEngine()

# Gerenciamento de conexões WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except:
                self.disconnect(client_id)

manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": "PrevLab API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/mortality-tables")
async def get_mortality_tables():
    """Retorna informações sobre todas as tábuas de mortalidade disponíveis (agrupadas por família)"""
    tables = get_mortality_table_info()
    return {"tables": tables}


@app.post("/calculate", response_model=SimulatorResults)
@handle_api_errors(default_message="Erro no cálculo atuarial")
async def calculate_simulation(state: SimulatorState):
    """Calcula simulação atuarial (endpoint REST)"""
    result = actuarial_engine.calculate_individual_simulation(state)
    return result


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Endpoint WebSocket para simulação reativa"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receber mensagem do cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "calculate":
                # Processar cálculo em background
                asyncio.create_task(
                    handle_calculation(client_id, message["state"])
                )
            
            elif message["type"] == "ping":
                await manager.send_message(client_id, {
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        await manager.send_message(client_id, {
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(client_id)


async def handle_calculation(client_id: str, state_data: dict):
    """Processa cálculo atuarial em background"""
    try:
        # Validar e criar estado
        state = SimulatorState(**state_data)
        
        # Enviar indicador de processamento
        await manager.send_message(client_id, {
            "type": "calculation_started",
            "calculation_id": state.calculation_id or str(uuid.uuid4())
        })
        
        # Calcular resultados principais
        results = actuarial_engine.calculate_individual_simulation(state)
        
        # Enviar resultados principais
        await manager.send_message(client_id, {
            "type": "results_update",
            "data": results.dict()
        })
        
        
        # Enviar confirmação de conclusão
        await manager.send_message(client_id, {
            "type": "calculation_completed",
            "computation_time_ms": results.computation_time_ms
        })
        
    except Exception as e:
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Erro no cálculo: {str(e)}"
        })


@app.get("/default-state")
async def get_default_state():
    """Retorna estado padrão para inicialização do simulador"""
    return {
        "age": 30,
        "gender": "M",
        "salary": 8000.0,
        "initial_balance": 0.0,
        "benefit_target_mode": "VALUE",
        "target_benefit": 5000.0,
        "target_replacement_rate": None,
        "accrual_rate": 5.0,
        "retirement_age": 65,
        "contribution_rate": 8.0,
        "mortality_table": "BR_EMS_2021",
        "discount_rate": 0.05,
        "salary_growth_real": 0.01,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "admin_fee_rate": 0.015,
        "loading_fee_rate": 0.0,
        "payment_timing": "postecipado",
        "salary_months_per_year": 13,
        "benefit_months_per_year": 13,
        "projection_years": 40,
        "calculation_method": "PUC"
    }


# ENDPOINTS DE SUGESTÕES INTELIGENTES

@app.post("/suggestions", response_model=SuggestionsResponse)
@handle_api_errors(default_message="Erro ao gerar sugestões")
async def get_smart_suggestions(request: SuggestionsRequest):
    """Gera sugestões inteligentes contextuais"""
    suggestions_response = suggestions_engine.generate_suggestions(request)
    return suggestions_response


@app.post("/apply-suggestion")
@handle_api_errors(default_message="Erro ao aplicar sugestão")
async def apply_suggestion(request: dict):
    """Aplica uma sugestão ao estado do simulador"""
    # Extrair dados da requisição
    current_state = SimulatorState(**request["state"])
    action = request["action"]
    action_value = request["action_value"]
    
    # Aplicar mudança usando o handler centralizado
    updated_state = state_action_handler.apply_action(current_state, action, action_value)
    
    # Calcular nova simulação
    new_results = actuarial_engine.calculate_individual_simulation(updated_state)
    
    return response_formatter.format_success_response(
        data={
            "updated_state": response_formatter.sanitize_for_json(updated_state),
            "new_results": response_formatter.sanitize_for_json(new_results)
        },
        message="Sugestão aplicada com sucesso"
    )


@app.get("/life-expectancy")
@handle_api_errors(default_message="Erro ao calcular expectativa de vida")
async def get_life_expectancy(
    age: int,
    gender: str,
    mortality_table: str,
    aggravation: float = 0.0
):
    """
    Calcula a expectativa de vida condicionada à idade atual
    
    Args:
        age: Idade atual
        gender: Gênero ('M' ou 'F')
        mortality_table: Código da tábua de mortalidade
        aggravation: Suavização percentual (-10% a +20%, default 0%)
    
    Returns:
        Dict com expectativa de vida em anos e idade esperada de morte
    """
    # Converter suavização de percentual para fator
    aggravation_factor = 1.0 + (aggravation / 100.0)

    # Obter dados da tábua de mortalidade (já aplicando a suavização)
    table_data = get_mortality_table(mortality_table, gender, aggravation)
    
    # Calcular expectativa de vida (suavização já aplicada na tábua)
    life_expectancy = calculate_life_expectancy(
        age=age,
        gender=gender,
        mortality_table=table_data,
        aggravation_factor=1.0  # Sem suavização adicional, já aplicada na tábua
    )
    
    # Calcular idade esperada de morte
    expected_death_age = age + life_expectancy
    
    return response_formatter.format_success_response(
        data={
            "life_expectancy": round(life_expectancy, 2),
            "expected_death_age": round(expected_death_age, 1),
            "current_age": age,
            "parameters": {
                "gender": gender,
                "mortality_table": mortality_table,
                "smoothing_percent": aggravation,
                "aggravation_percent": aggravation  # Mantido por compatibilidade
            }
        },
        message="Expectativa de vida calculada com sucesso"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main_simple:app", host="0.0.0.0", port=8000, reload=True)
