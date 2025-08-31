from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
import asyncio
import json
from typing import Dict, Any, List
import uuid

from ..models import SimulatorState, SimulatorResults
from ..models.database import User, UserProfile, MortalityTable, ActuarialAssumption
from ..core.actuarial_engine import ActuarialEngine
from ..core.mortality_tables import get_mortality_table_info
from ..database import get_session, init_database
from ..repositories.user_repository import UserRepository, UserProfileRepository
from ..repositories.mortality_repository import MortalityTableRepository
from ..repositories.assumption_repository import ActuarialAssumptionRepository

app = FastAPI(
    title="Simulador Atuarial Individual",
    description="API para simulação atuarial interativa individual",
    version="1.0.0"
)

# Inicializar banco de dados na inicialização da aplicação
@app.on_event("startup")
async def startup_event():
    init_database()

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
async def get_mortality_tables(session: Session = Depends(get_session)):
    """Retorna informações sobre todas as tábuas de mortalidade disponíveis"""
    repo = MortalityTableRepository(session)
    tables = repo.get_table_info()
    
    # Se não houver tábuas no banco, retornar as do sistema legado
    if not tables:
        return get_mortality_table_info()
    
    return {"tables": tables}


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
        "salary_growth_real": 0.02,
        "benefit_indexation": "none",
        "contribution_indexation": "salary",
        "use_ettj": False,
        "admin_fee_rate": 0.01,
        "loading_fee_rate": 0.0,
        "payment_timing": "postecipado",
        "salary_months_per_year": 13,
        "benefit_months_per_year": 13,
        "projection_years": 40,
        "calculation_method": "PUC"
    }


# Endpoints para gerenciamento de usuários e perfis
@app.post("/users", response_model=dict)
async def create_user(
    user_data: dict, 
    session: Session = Depends(get_session)
):
    """Criar novo usuário"""
    repo = UserRepository(session)
    
    # Verificar se email já existe
    if repo.email_exists(user_data["email"]):
        raise HTTPException(status_code=400, detail="Email já está em uso")
    
    user = User(
        name=user_data["name"],
        email=user_data["email"]
    )
    
    created_user = repo.create(user)
    return {
        "id": created_user.id,
        "name": created_user.name,
        "email": created_user.email,
        "created_at": created_user.created_at
    }


@app.get("/users/{user_id}/profiles")
async def get_user_profiles(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Listar perfis de um usuário"""
    repo = UserProfileRepository(session)
    profiles = repo.get_by_user(user_id)
    
    return {
        "profiles": [
            {
                "id": profile.id,
                "profile_name": profile.profile_name,
                "description": profile.description,
                "is_favorite": profile.is_favorite,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at
            }
            for profile in profiles
        ]
    }


@app.post("/users/{user_id}/profiles")
async def create_user_profile(
    user_id: int,
    profile_data: dict,
    session: Session = Depends(get_session)
):
    """Criar novo perfil para usuário"""
    repo = UserProfileRepository(session)
    
    # Validar dados do simulador
    try:
        simulator_state = SimulatorState(**profile_data["simulator_state"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Estado do simulador inválido: {str(e)}")
    
    profile = repo.create_with_simulator_state(
        user_id=user_id,
        profile_name=profile_data["profile_name"],
        state=simulator_state,
        description=profile_data.get("description")
    )
    
    return {
        "id": profile.id,
        "profile_name": profile.profile_name,
        "description": profile.description,
        "created_at": profile.created_at
    }


@app.get("/users/{user_id}/profiles/{profile_id}")
async def get_user_profile(
    user_id: int,
    profile_id: int,
    session: Session = Depends(get_session)
):
    """Obter perfil específico do usuário"""
    repo = UserProfileRepository(session)
    profile = repo.get_by_id(profile_id)
    
    if not profile or profile.user_id != user_id:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    
    return {
        "id": profile.id,
        "profile_name": profile.profile_name,
        "description": profile.description,
        "is_favorite": profile.is_favorite,
        "simulator_state": profile.get_simulator_state().model_dump(),
        "created_at": profile.created_at,
        "updated_at": profile.updated_at
    }


@app.put("/users/{user_id}/profiles/{profile_id}")
async def update_user_profile(
    user_id: int,
    profile_id: int,
    profile_data: dict,
    session: Session = Depends(get_session)
):
    """Atualizar perfil do usuário"""
    repo = UserProfileRepository(session)
    profile = repo.get_by_id(profile_id)
    
    if not profile or profile.user_id != user_id:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    
    # Atualizar campos básicos
    if "profile_name" in profile_data:
        profile.profile_name = profile_data["profile_name"]
    if "description" in profile_data:
        profile.description = profile_data["description"]
    
    # Atualizar estado do simulador se fornecido
    if "simulator_state" in profile_data:
        try:
            simulator_state = SimulatorState(**profile_data["simulator_state"])
            profile.set_simulator_state(simulator_state)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Estado do simulador inválido: {str(e)}")
    
    updated_profile = repo.update(profile)
    
    return {
        "id": updated_profile.id,
        "profile_name": updated_profile.profile_name,
        "description": updated_profile.description,
        "updated_at": updated_profile.updated_at
    }


@app.delete("/users/{user_id}/profiles/{profile_id}")
async def delete_user_profile(
    user_id: int,
    profile_id: int,
    session: Session = Depends(get_session)
):
    """Deletar perfil do usuário"""
    repo = UserProfileRepository(session)
    profile = repo.get_by_id(profile_id)
    
    if not profile or profile.user_id != user_id:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    
    success = repo.delete(profile)
    if success:
        return {"message": "Perfil deletado com sucesso"}
    else:
        raise HTTPException(status_code=500, detail="Erro ao deletar perfil")


@app.post("/users/{user_id}/profiles/{profile_id}/toggle-favorite")
async def toggle_profile_favorite(
    user_id: int,
    profile_id: int,
    session: Session = Depends(get_session)
):
    """Alternar status de favorito do perfil"""
    repo = UserProfileRepository(session)
    profile = repo.get_by_id(profile_id)
    
    if not profile or profile.user_id != user_id:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    
    updated_profile = repo.toggle_favorite(profile_id)
    
    return {
        "id": updated_profile.id,
        "is_favorite": updated_profile.is_favorite
    }


# Endpoints para premissas atuariais
@app.get("/actuarial-assumptions")
async def get_actuarial_assumptions(
    category: str = None,
    session: Session = Depends(get_session)
):
    """Listar premissas atuariais"""
    repo = ActuarialAssumptionRepository(session)
    
    if category:
        assumptions = repo.get_by_category(category)
    else:
        assumptions = repo.get_all()
    
    return {
        "assumptions": [
            {
                "id": assumption.id,
                "name": assumption.name,
                "description": assumption.description,
                "category": assumption.category,
                "parameters": assumption.get_parameters(),
                "is_default": assumption.is_default,
                "is_system": assumption.is_system
            }
            for assumption in assumptions
        ]
    }


@app.get("/actuarial-assumptions/categories")
async def get_assumption_categories(session: Session = Depends(get_session)):
    """Listar categorias de premissas atuariais"""
    repo = ActuarialAssumptionRepository(session)
    categories = repo.get_categories()
    return {"categories": categories}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)