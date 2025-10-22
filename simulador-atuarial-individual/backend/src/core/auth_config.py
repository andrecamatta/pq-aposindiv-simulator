"""
Configurações de autenticação com Google OAuth e JWT
"""
import os
from typing import Optional

# ========== JWT Configuration ==========
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-CHANGE-IN-PRODUCTION")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias

# ========== Google OAuth Configuration ==========
GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI")

# URLs do Google OAuth
GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes necessários
GOOGLE_SCOPES: list[str] = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def validate_auth_config() -> dict[str, bool]:
    """Valida se todas as configurações necessárias estão definidas"""
    return {
        "secret_key_configured": SECRET_KEY != "dev-secret-key-CHANGE-IN-PRODUCTION",
        "google_client_id_configured": GOOGLE_CLIENT_ID is not None,
        "google_client_secret_configured": GOOGLE_CLIENT_SECRET is not None,
        "google_redirect_uri_configured": GOOGLE_REDIRECT_URI is not None,
    }


def is_auth_properly_configured() -> bool:
    """Verifica se a autenticação está completamente configurada"""
    config = validate_auth_config()
    return all(config.values())
