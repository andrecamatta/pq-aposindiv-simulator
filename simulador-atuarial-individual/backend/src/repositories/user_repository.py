from sqlmodel import Session, select
from typing import Optional, List
from ..models.database import User, UserProfile
from ..models.participant import SimulatorState
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repositório para usuários"""
    
    def __init__(self, session: Session):
        super().__init__(session, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Buscar usuário por email"""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()
    
    def email_exists(self, email: str) -> bool:
        """Verificar se email já existe"""
        return self.get_by_email(email) is not None


class UserProfileRepository(BaseRepository[UserProfile]):
    """Repositório para perfis de usuário"""
    
    def __init__(self, session: Session):
        super().__init__(session, UserProfile)
    
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[UserProfile]:
        """Buscar perfis por usuário"""
        statement = select(UserProfile).where(
            UserProfile.user_id == user_id
        ).offset(skip).limit(limit)
        return list(self.session.exec(statement))
    
    def get_favorites_by_user(self, user_id: int) -> List[UserProfile]:
        """Buscar perfis favoritos do usuário"""
        statement = select(UserProfile).where(
            UserProfile.user_id == user_id,
            UserProfile.is_favorite == True
        )
        return list(self.session.exec(statement))
    
    def create_with_simulator_state(
        self, 
        user_id: int, 
        profile_name: str, 
        state: SimulatorState,
        description: Optional[str] = None
    ) -> UserProfile:
        """Criar perfil com estado do simulador"""
        profile = UserProfile(
            user_id=user_id,
            profile_name=profile_name,
            description=description
        )
        profile.set_simulator_state(state)
        return self.create(profile)
    
    def update_simulator_state(
        self, 
        profile_id: int, 
        state: SimulatorState
    ) -> Optional[UserProfile]:
        """Atualizar estado do simulador em um perfil"""
        profile = self.get_by_id(profile_id)
        if profile:
            profile.set_simulator_state(state)
            return self.update(profile)
        return None
    
    def toggle_favorite(self, profile_id: int) -> Optional[UserProfile]:
        """Alternar status de favorito"""
        profile = self.get_by_id(profile_id)
        if profile:
            profile.is_favorite = not profile.is_favorite
            return self.update(profile)
        return None