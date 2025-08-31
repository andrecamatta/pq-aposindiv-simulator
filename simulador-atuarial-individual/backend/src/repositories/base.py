from sqlmodel import Session, select
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from abc import ABC, abstractmethod

T = TypeVar("T")


class BaseRepository(Generic[T], ABC):
    """Repositório base com operações CRUD comuns"""
    
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    def create(self, obj: T) -> T:
        """Criar novo registro"""
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Buscar por ID"""
        return self.session.get(self.model_class, id)
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Listar todos com paginação"""
        statement = select(self.model_class).offset(skip).limit(limit)
        return list(self.session.exec(statement))
    
    def update(self, obj: T) -> T:
        """Atualizar registro existente"""
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj
    
    def delete(self, obj: T) -> bool:
        """Deletar registro"""
        try:
            self.session.delete(obj)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False
    
    def delete_by_id(self, id: int) -> bool:
        """Deletar por ID"""
        obj = self.get_by_id(id)
        if obj:
            return self.delete(obj)
        return False
    
    def count(self) -> int:
        """Contar total de registros"""
        statement = select(self.model_class)
        return len(list(self.session.exec(statement)))
    
    def exists(self, id: int) -> bool:
        """Verificar se registro existe"""
        return self.get_by_id(id) is not None