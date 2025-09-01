from sqlmodel import Session, select
from typing import Optional, List, Dict
from ..models.database import MortalityTable
from .base import BaseRepository


class MortalityTableRepository(BaseRepository[MortalityTable]):
    """Repositório para tábuas de mortalidade"""
    
    def __init__(self, session: Session):
        super().__init__(session, MortalityTable)
    
    def get_by_name(self, name: str) -> Optional[MortalityTable]:
        """Buscar tábua por nome"""
        statement = select(MortalityTable).where(MortalityTable.name == name)
        return self.session.exec(statement).first()
    
    def get_system_tables(self) -> List[MortalityTable]:
        """Buscar tábuas do sistema"""
        statement = select(MortalityTable).where(MortalityTable.is_system == True)
        return list(self.session.exec(statement))
    
    def get_active_tables(self) -> List[MortalityTable]:
        """Buscar tábuas ativas"""
        statement = select(MortalityTable).where(MortalityTable.is_active == True)
        return list(self.session.exec(statement))
    
    def get_by_code(self, code: str) -> Optional[MortalityTable]:
        """Buscar tábua por código"""
        statement = select(MortalityTable).where(MortalityTable.code == code)
        return self.session.exec(statement).first()
    
    def get_by_country(self, country: str) -> List[MortalityTable]:
        """Buscar tábuas por país"""
        statement = select(MortalityTable).where(MortalityTable.country == country)
        return list(self.session.exec(statement))
    
    def get_by_gender(self, gender: str) -> List[MortalityTable]:
        """Buscar tábuas por gênero"""
        statement = select(MortalityTable).where(MortalityTable.gender == gender)
        return list(self.session.exec(statement))
    
    def create_with_data(
        self,
        name: str,
        table_data: Dict[int, float],
        description: Optional[str] = None,
        country: Optional[str] = None,
        year: Optional[int] = None,
        gender: Optional[str] = None,
        is_system: bool = False
    ) -> MortalityTable:
        """Criar tábua com dados"""
        table = MortalityTable(
            name=name,
            description=description,
            country=country,
            year=year,
            gender=gender,
            is_system=is_system
        )
        table.set_table_data(table_data)
        return self.create(table)
    
    def get_table_info(self) -> List[Dict]:
        """Retornar informações resumidas das tábuas"""
        tables = self.get_all()
        return [
            {
                "id": table.id,
                "name": table.name,
                "description": table.description,
                "country": table.country,
                "year": table.year,
                "gender": table.gender,
                "is_system": table.is_system
            }
            for table in tables
        ]
    
    def name_exists(self, name: str) -> bool:
        """Verificar se nome da tábua já existe"""
        return self.get_by_name(name) is not None