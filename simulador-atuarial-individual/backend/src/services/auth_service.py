"""
Serviço de autenticação com Google OAuth e JWT
"""
from datetime import datetime, timedelta
from typing import Optional
import httpx
from jose import JWTError, jwt
from sqlmodel import Session, select

from ..core.auth_config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    GOOGLE_SCOPES,
)
from ..models.database import User


class AuthService:
    """Serviço para operações de autenticação"""

    @staticmethod
    def generate_jwt_token(user_id: int, email: str) -> str:
        """Gera um token JWT para o usuário"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_jwt_token(token: str) -> Optional[dict]:
        """Verifica e decodifica um token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    def get_google_oauth_url(state: Optional[str] = None) -> str:
        """Gera URL de autenticação do Google OAuth"""
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{GOOGLE_AUTH_URL}?{query_string}"

    @staticmethod
    async def exchange_code_for_token(code: str) -> Optional[dict]:
        """Troca o código de autorização por um access token do Google"""
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(GOOGLE_TOKEN_URL, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return None

    @staticmethod
    async def get_google_user_info(access_token: str) -> Optional[dict]:
        """Obtém informações do usuário do Google"""
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return None

    @staticmethod
    def create_or_update_user(
        session: Session, google_user_info: dict
    ) -> User:
        """Cria ou atualiza um usuário baseado nas informações do Google"""
        google_id = google_user_info.get("id")
        email = google_user_info.get("email")
        name = google_user_info.get("name", email.split("@")[0])
        avatar_url = google_user_info.get("picture")

        # Verificar se usuário já existe por google_id
        statement = select(User).where(User.google_id == google_id)
        user = session.exec(statement).first()

        if user:
            # Atualizar informações do usuário existente
            user.name = name
            user.email = email
            user.avatar_url = avatar_url
            user.last_login_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
        else:
            # Verificar se já existe usuário com esse email (migração)
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()

            if user:
                # Atualizar usuário existente com google_id
                user.google_id = google_id
                user.avatar_url = avatar_url
                user.last_login_at = datetime.utcnow()
                user.updated_at = datetime.utcnow()
            else:
                # Criar novo usuário
                user = User(
                    name=name,
                    email=email,
                    google_id=google_id,
                    avatar_url=avatar_url,
                    is_active=True,
                    last_login_at=datetime.utcnow(),
                )
                session.add(user)

        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
        """Busca usuário por ID"""
        return session.get(User, user_id)

    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """Busca usuário por email"""
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()
