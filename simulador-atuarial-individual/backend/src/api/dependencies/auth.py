"""
Dependencies de autenticação para FastAPI
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from ...database import get_session
from ...services.auth_service import AuthService
from ...models.database import User


# Security scheme para Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """
    Dependency para obter o usuário atual a partir do token JWT.

    Raises:
        HTTPException: Se o token for inválido ou o usuário não existir.
    """
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
