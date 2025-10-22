"""
Dependencies de autenticação para FastAPI
"""
from typing import Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from ...database import get_session
from ...services.auth_service import AuthService
from ...models.database import User
from ...core.auth_config import (
    ENABLE_AUTH,
    MOCK_USER_ID,
    MOCK_USER_NAME,
    MOCK_USER_EMAIL,
    MOCK_USER_AVATAR,
)


# Security scheme para Bearer token (opcional quando auth desabilitado)
security = HTTPBearer(auto_error=False)


def create_mock_user() -> User:
    """
    Cria um usuário mock para desenvolvimento quando autenticação está desabilitada.
    """
    return User(
        id=MOCK_USER_ID,
        name=MOCK_USER_NAME,
        email=MOCK_USER_EMAIL,
        google_id="mock-google-id",
        avatar_url=MOCK_USER_AVATAR,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=None,
        last_login_at=datetime.utcnow(),
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """
    Dependency para obter o usuário atual a partir do token JWT.
    Se ENABLE_AUTH=false, retorna mock user automaticamente.

    Raises:
        HTTPException: Se o token for inválido ou o usuário não existir (quando auth habilitado).
    """
    # Se autenticação estiver desabilitada, retornar mock user
    if not ENABLE_AUTH:
        return create_mock_user()

    # Autenticação habilitada - validar token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extrair token
    token = credentials.credentials

    # Verificar token JWT
    payload = AuthService.verify_jwt_token(token)
    if payload is None:
        raise credentials_exception

    # Extrair user_id do payload
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    # Buscar usuário no banco
    user = AuthService.get_user_by_id(session, user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency para obter o usuário atual e verificar se está ativo.

    Raises:
        HTTPException: Se o usuário estiver inativo.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )
    return current_user
