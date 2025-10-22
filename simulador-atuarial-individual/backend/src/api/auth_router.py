"""
Router de autenticação com Google OAuth
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from pydantic import BaseModel

from ..database import get_session
from ..services.auth_service import AuthService
from ..models.database import User
from .dependencies.auth import get_current_active_user
from ..core.auth_config import is_auth_properly_configured, validate_auth_config, ENABLE_AUTH


router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    """Resposta com token de acesso"""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Resposta com informações do usuário"""

    id: int
    name: str
    email: str
    avatar_url: str | None
    is_active: bool


@router.get("/login")
async def login():
    """
    Inicia o fluxo de autenticação com Google OAuth.
    Redireciona o usuário para a página de login do Google.
    Se autenticação estiver desabilitada, retorna erro 404.
    """
    if not ENABLE_AUTH:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autenticação está desabilitada (ENABLE_AUTH=false)",
        )

    if not is_auth_properly_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação não está configurada corretamente. Verifique as variáveis de ambiente.",
        )

    oauth_url = AuthService.get_google_oauth_url()
    return RedirectResponse(url=oauth_url)


@router.get("/callback")
async def auth_callback(
    code: str,
    session: Session = Depends(get_session),
):
    """
    Callback do Google OAuth.
    Recebe o código de autorização, troca por access token,
    obtém informações do usuário e gera JWT.
    Se autenticação estiver desabilitada, retorna erro 404.
    """
    if not ENABLE_AUTH:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autenticação está desabilitada (ENABLE_AUTH=false)",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de autorização não fornecido",
        )

    # Trocar código por access token
    token_data = await AuthService.exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao obter token de acesso",
        )

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de acesso não encontrado",
        )

    # Obter informações do usuário do Google
    google_user_info = await AuthService.get_google_user_info(access_token)
    if not google_user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao obter informações do usuário",
        )

    # Criar ou atualizar usuário no banco
    user = AuthService.create_or_update_user(session, google_user_info)

    # Gerar JWT token
    jwt_token = AuthService.generate_jwt_token(user.id, user.email)

    # Redirecionar para o frontend com o token
    # O frontend vai pegar o token da URL e salvar no localStorage
    frontend_url = f"/auth/success?token={jwt_token}"
    return RedirectResponse(url=frontend_url)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """
    Retorna informações do usuário autenticado.
    """
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout do usuário.
    O frontend deve remover o token do localStorage.
    """
    return {"message": "Logout realizado com sucesso"}


@router.get("/health")
async def auth_health():
    """
    Verifica o status da configuração de autenticação.
    """
    config_status = {
        "configured": is_auth_properly_configured(),
        **validate_auth_config(),
    }

    return {
        "status": "ok" if config_status["configured"] else "misconfigured",
        "config": config_status,
    }
