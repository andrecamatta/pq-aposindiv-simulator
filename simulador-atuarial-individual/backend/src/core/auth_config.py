"""
Configurações de autenticação com Google OAuth e JWT
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ========== Authentication Control ==========
ENABLE_AUTH: bool = os.getenv("ENABLE_AUTH", "true").lower() == "true"

# ========== Email Whitelist Configuration ==========
# Lista de emails autorizados (separados por vírgula)
# Exemplo: "user1@example.com,user2@example.com,admin@example.com"
# Se vazio ou "*", permite todos os emails
ALLOWED_EMAILS_RAW: str = os.getenv("ALLOWED_EMAILS", "*")
ALLOWED_EMAILS: set[str] = (
    set(email.strip().lower() for email in ALLOWED_EMAILS_RAW.split(",") if email.strip())
    if ALLOWED_EMAILS_RAW != "*"
    else set()
)

def is_email_allowed(email: str) -> bool:
    """Verifica se um email está na whitelist"""
    # Se ALLOWED_EMAILS está vazio (configurado como "*"), permite todos
    if not ALLOWED_EMAILS:
        return True
    # Verifica se o email está na whitelist (case-insensitive)
    return email.strip().lower() in ALLOWED_EMAILS

# ========== Mock User Configuration (Development) ==========
MOCK_USER_ID: int = 999
MOCK_USER_NAME: str = os.getenv("MOCK_USER_NAME", "Dev User")
MOCK_USER_EMAIL: str = os.getenv("MOCK_USER_EMAIL", "dev@localhost")
MOCK_USER_AVATAR: str = "https://ui-avatars.com/api/?name=Dev+User&background=3b82f6&color=fff"

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
        "enabled": ENABLE_AUTH,
        "secret_key_configured": SECRET_KEY != "dev-secret-key-CHANGE-IN-PRODUCTION",
        "google_client_id_configured": GOOGLE_CLIENT_ID is not None,
        "google_client_secret_configured": GOOGLE_CLIENT_SECRET is not None,
        "google_redirect_uri_configured": GOOGLE_REDIRECT_URI is not None,
    }


def is_auth_properly_configured() -> bool:
    """Verifica se a autenticação está completamente configurada"""
    if not ENABLE_AUTH:
        return True  # Auth desabilitado = sempre "configurado"

    config = validate_auth_config()
    # Remove 'enabled' da verificação
    config_without_enabled = {k: v for k, v in config.items() if k != "enabled"}
    return all(config_without_enabled.values())
