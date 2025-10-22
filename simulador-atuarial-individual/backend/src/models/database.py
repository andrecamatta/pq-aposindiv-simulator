from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from .participant import SimulatorState, Gender, CalculationMethod, BenefitTargetMode, PaymentTiming, DecrementType
from .mixins import JSONSerializationMixin


class User(SQLModel, table=True):
    """Tabela de usuários do sistema"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)

    # Google OAuth fields
    google_id: Optional[str] = Field(default=None, unique=True, index=True)
    avatar_url: Optional[str] = None

    # Status
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    # Relacionamentos
    profiles: List["UserProfile"] = Relationship(back_populates="user")


class AllowedEmail(SQLModel, table=True):
    """Whitelist de emails autorizados a acessar o sistema"""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)

    # Metadados
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # Email de quem adicionou
    note: Optional[str] = None  # Observações


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


class ActuarialAssumption(SQLModel, JSONSerializationMixin, table=True):
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
        return self.get_json_field("parameters")
    
    def set_parameters(self, params: Dict[str, Any]):
        """Serializa os parâmetros"""
        self.set_json_field("parameters", params)


class MortalityTable(SQLModel, JSONSerializationMixin, table=True):
    """Tábuas de mortalidade com metadados expandidos"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    code: str = Field(unique=True, description="Código único da tábua (ex: BR_EMS_2021, AT_2000)")
    description: Optional[str] = None
    country: Optional[str] = None
    year: Optional[int] = None
    gender: Optional[str] = None  # "M", "F", ou "UNISEX"
    
    # Metadados da fonte
    source: str = Field(description="Fonte da tábua (pymort, local, csv, excel)")
    source_id: Optional[str] = None  # ID da tábua na fonte original
    version: Optional[str] = None
    is_official: bool = False  # Tábua oficial/regulamentar
    regulatory_approved: bool = False  # Aprovada por órgão regulador
    
    # Dados da tábua serializados como JSON
    table_data: str = Field(description="JSON com os dados da tábua de mortalidade")
    table_metadata: str = Field(default="{}", description="JSON com metadados adicionais")
    
    # Status e controle
    is_active: bool = True  # Tábua ativa para uso
    is_system: bool = False  # Tábuas do sistema não podem ser editadas
    last_loaded: Optional[datetime] = None  # Última vez que foi carregada da fonte
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def get_table_data(self) -> Dict[int, float]:
        """Deserializa os dados da tábua"""
        return self.get_json_field_with_transform("table_data", key_transform=int)
    
    def set_table_data(self, data: Dict[int, float]):
        """Serializa os dados da tábua"""
        self.set_json_field_with_transform("table_data", data, key_transform=str)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Deserializa os metadados"""
        return self.get_json_field("table_metadata")
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """Serializa os metadados"""
        self.set_json_field("table_metadata", metadata)


class DecrementTable(SQLModel, JSONSerializationMixin, table=True):
    """Tábuas de decrementos múltiplos (invalidez, rotatividade, etc.)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Nome descritivo da tábua")
    code: str = Field(unique=True, description="Código único da tábua (ex: UP84_DISABILITY, BR_TURNOVER_2021)")
    decrement_type: DecrementType = Field(description="Tipo de decremento")
    description: Optional[str] = None
    country: Optional[str] = None
    year: Optional[int] = None
    gender: Optional[str] = None  # "M", "F", ou "UNISEX"

    # Metadados específicos do decremento
    base_mortality_table: Optional[str] = None  # Para invalidez: tábua de mortalidade base
    occupation_codes: Optional[str] = None      # JSON com códigos de ocupação aplicáveis
    age_range: str = Field(default="18-110", description="Faixa etária aplicável (ex: '18-65')")

    # Dados da tábua serializados como JSON
    table_data: str = Field(description="JSON com os dados da tábua de decremento")
    table_metadata: str = Field(default="{}", description="JSON com metadados adicionais")

    # Metadados da fonte
    source: str = Field(description="Fonte da tábua (database, csv, excel, manual)")
    source_id: Optional[str] = None  # ID da tábua na fonte original
    version: Optional[str] = None
    is_official: bool = False  # Tábua oficial/regulamentar
    regulatory_approved: bool = False  # Aprovada por órgão regulador

    # Controle
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def get_table_data(self) -> Dict[int, float]:
        """Deserializa os dados da tábua de decremento"""
        return self.get_json_field_with_transform("table_data", key_transform=int)

    def set_table_data(self, data: Dict[int, float]):
        """Serializa os dados da tábua de decremento"""
        self.set_json_field_with_transform("table_data", data, key_transform=str)

    def get_metadata(self) -> Dict[str, Any]:
        """Deserializa os metadados"""
        return self.get_json_field("table_metadata")

    def set_metadata(self, metadata: Dict[str, Any]):
        """Serializa os metadados"""
        self.set_json_field("table_metadata", metadata)

    def get_occupation_codes(self) -> List[str]:
        """Retorna lista de códigos de ocupação aplicáveis"""
        if not self.occupation_codes:
            return []
        try:
            return json.loads(self.occupation_codes)
        except:
            return []

    def set_occupation_codes(self, codes: List[str]):
        """Define códigos de ocupação aplicáveis"""
        self.occupation_codes = json.dumps(codes)


class SimulationResult(SQLModel, JSONSerializationMixin, table=True):
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
        return self.get_json_field("results")
    
    def set_results(self, results_data: Dict[str, Any]):
        """Serializa os resultados"""
        self.set_json_field("results", results_data)