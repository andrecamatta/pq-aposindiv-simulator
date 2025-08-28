from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
from typing import Dict, Any
import uuid

from ..models import SimulatorState, SimulatorResults
from ..core.actuarial_engine import ActuarialEngine
from ..core.mortality_tables import get_mortality_table_info

app = FastAPI(
    title="Simulador Atuarial Individual",
    description="API para simulação atuarial interativa individual",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Engine atuarial global
actuarial_engine = ActuarialEngine()

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
    return {"message": "Simulador Atuarial Individual API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/mortality-tables")
async def get_mortality_tables():
    """Retorna informações sobre todas as tábuas de mortalidade disponíveis"""
    return get_mortality_table_info()


@app.post("/calculate", response_model=SimulatorResults)
async def calculate_simulation(state: SimulatorState):
    """Calcula simulação atuarial (endpoint REST)"""
    try:
        result = actuarial_engine.calculate_individual_simulation(state)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        
        # Calcular e enviar análise de sensibilidade (paralelo)
        # Note: A sensibilidade já é calculada no engine principal
        await manager.send_message(client_id, {
            "type": "sensitivity_update",
            "data": {
                "discount_rate": results.sensitivity_discount_rate,
                "mortality": results.sensitivity_mortality,
                "retirement_age": results.sensitivity_retirement_age,
                "salary_growth": results.sensitivity_salary_growth,
                "inflation": results.sensitivity_inflation
            }
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
        "age": 45,
        "gender": "M",
        "salary": 8000.0,
        "initial_balance": 50000.0,
        "benefit_target_mode": "VALUE",
        "target_benefit": 5000.0,
        "target_replacement_rate": None,
        "accrual_rate": 2.0,
        "retirement_age": 65,
        "contribution_rate": 8.0,
        "mortality_table": "BR_EMS_2021",
        "discount_rate": 0.06,
        "salary_growth_real": 0.02,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "projection_years": 40,
        "calculation_method": "PUC"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)