from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
from ..models.database import ActuarialAssumption
from .base import BaseRepository


class ActuarialAssumptionRepository(BaseRepository[ActuarialAssumption]):
    """Repositório para premissas atuariais"""
    
    def __init__(self, session: Session):
        super().__init__(session, ActuarialAssumption)
    
    def get_by_category(self, category: str) -> List[ActuarialAssumption]:
        """Buscar premissas por categoria"""
        statement = select(ActuarialAssumption).where(
            ActuarialAssumption.category == category
        )
        return list(self.session.exec(statement))
    
    def get_default_by_category(self, category: str) -> Optional[ActuarialAssumption]:
        """Buscar premissa padrão de uma categoria"""
        statement = select(ActuarialAssumption).where(
            ActuarialAssumption.category == category,
            ActuarialAssumption.is_default == True
        )
        return self.session.exec(statement).first()
    
    def get_system_assumptions(self) -> List[ActuarialAssumption]:
        """Buscar premissas do sistema"""
        statement = select(ActuarialAssumption).where(
            ActuarialAssumption.is_system == True
        )
        return list(self.session.exec(statement))
    
    def create_with_parameters(
        self,
        name: str,
        category: str,
        parameters: Dict[str, Any],
        description: Optional[str] = None,
        is_default: bool = False,
        is_system: bool = False
    ) -> ActuarialAssumption:
        """Criar premissa com parâmetros"""
        assumption = ActuarialAssumption(
            name=name,
            category=category,
            description=description,
            is_default=is_default,
            is_system=is_system
        )
        assumption.set_parameters(parameters)
        return self.create(assumption)
    
    def update_parameters(
        self, 
        assumption_id: int, 
        parameters: Dict[str, Any]
    ) -> Optional[ActuarialAssumption]:
        """Atualizar parâmetros de uma premissa"""
        assumption = self.get_by_id(assumption_id)
        if assumption and not assumption.is_system:  # Não permite editar premissas do sistema
            assumption.set_parameters(parameters)
            return self.update(assumption)
        return None
    
    def set_default(self, assumption_id: int, category: str) -> Optional[ActuarialAssumption]:
        """Definir premissa como padrão (remove default das outras da mesma categoria)"""
        # Remove default das outras da mesma categoria
        statement = select(ActuarialAssumption).where(
            ActuarialAssumption.category == category,
            ActuarialAssumption.is_default == True
        )
        current_defaults = list(self.session.exec(statement))
        
        for default in current_defaults:
            default.is_default = False
            self.session.add(default)
        
        # Define nova padrão
        assumption = self.get_by_id(assumption_id)
        if assumption:
            assumption.is_default = True
            self.session.commit()
            return assumption
        
        return None
    
    def get_categories(self) -> List[str]:
        """Listar categorias disponíveis"""
        statement = select(ActuarialAssumption.category).distinct()
        return list(self.session.exec(statement))
    
    def get_assumptions_by_categories(self) -> Dict[str, List[ActuarialAssumption]]:
        """Agrupar premissas por categoria"""
        assumptions = self.get_all()
        grouped = {}
        
        for assumption in assumptions:
            if assumption.category not in grouped:
                grouped[assumption.category] = []
            grouped[assumption.category].append(assumption)
        
        return grouped