from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from .participant import SimulatorState, Gender, CalculationMethod, BenefitTargetMode, PaymentTiming


class User(SQLModel, table=True):
    """Tabela de usuários do sistema"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Relacionamentos
    profiles: List["UserProfile"] = Relationship(back_populates="user")


class UserProfile(SQLModel, table=True):
    """Perfis/cenários salvos pelos usuários"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    profile_name: str
    description: Optional[str] = None
    
    # Dados do simulador serializados como JSON
    simulator_state: str = Field(description="JSON serializado do SimulatorState")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_favorite: bool = False
    
    # Relacionamentos
    user: Optional[User] = Relationship(back_populates="profiles")
    
    def get_simulator_state(self) -> SimulatorState:
        """Deserializa o estado do simulador"""
        data = json.loads(self.simulator_state)
        return SimulatorState(**data)
    
    def set_simulator_state(self, state: SimulatorState):
        """Serializa o estado do simulador"""
        self.simulator_state = state.model_dump_json()


class ActuarialAssumption(SQLModel, table=True):
    """Premissas atuariais pré-definidas e personalizadas"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    category: str = Field(description="Categoria da premissa: discount_rate, mortality, salary_growth, etc.")
    
    # Parâmetros serializados como JSON
    parameters: str = Field(description="JSON com os parâmetros da premissa")
    
    is_default: bool = False
    is_system: bool = False  # Premissas do sistema não podem ser editadas
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def get_parameters(self) -> Dict[str, Any]:
        """Deserializa os parâmetros"""
        return json.loads(self.parameters)
    
    def set_parameters(self, params: Dict[str, Any]):
        """Serializa os parâmetros"""
        self.parameters = json.dumps(params)


class MortalityTable(SQLModel, table=True):
    """Tábuas de mortalidade"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: Optional[str] = None
    country: Optional[str] = None
    year: Optional[int] = None
    gender: Optional[str] = None  # "M", "F", ou "UNISEX"
    
    # Dados da tábua serializados como JSON
    table_data: str = Field(description="JSON com os dados da tábua de mortalidade")
    
    is_system: bool = False  # Tábuas do sistema não podem ser editadas
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def get_table_data(self) -> Dict[int, float]:
        """Deserializa os dados da tábua"""
        return {int(k): v for k, v in json.loads(self.table_data).items()}
    
    def set_table_data(self, data: Dict[int, float]):
        """Serializa os dados da tábua"""
        self.table_data = json.dumps({str(k): v for k, v in data.items()})


class SimulationResult(SQLModel, table=True):
    """Resultados de simulações para cache e histórico"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Hash do estado do simulador para cache
    state_hash: str = Field(index=True)
    
    # Resultados serializados como JSON
    results: str = Field(description="JSON com os resultados da simulação")
    
    computation_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # Para limpeza automática do cache
    
    def get_results(self) -> Dict[str, Any]:
        """Deserializa os resultados"""
        return json.loads(self.results)
    
    def set_results(self, results_data: Dict[str, Any]):
        """Serializa os resultados"""
        self.results = json.dumps(results_data)