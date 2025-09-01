from functools import wraps
from fastapi import HTTPException
import logging
from typing import Callable, Any


logger = logging.getLogger(__name__)


def handle_api_errors(
    default_status_code: int = 400,
    default_message: str = "Erro interno do servidor"
):
    """
    Decorator para padronizar tratamento de erros em endpoints da API
    
    Args:
        default_status_code: Código HTTP padrão para erros não tratados
        default_message: Mensagem padrão para erros não tratados
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTPException para manter comportamento original
                raise
            except ValueError as e:
                # Erros de validação/entrada
                logger.warning(f"Erro de validação em {func.__name__}: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except FileNotFoundError as e:
                # Recursos não encontrados
                logger.warning(f"Recurso não encontrado em {func.__name__}: {str(e)}")
                raise HTTPException(status_code=404, detail="Recurso não encontrado")
            except PermissionError as e:
                # Erros de permissão
                logger.warning(f"Erro de permissão em {func.__name__}: {str(e)}")
                raise HTTPException(status_code=403, detail="Acesso negado")
            except Exception as e:
                # Erros genéricos
                logger.error(f"Erro não tratado em {func.__name__}: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=default_status_code, 
                    detail=f"{default_message}: {str(e)}"
                )
        
        return wrapper
    return decorator


def handle_background_errors(task_name: str = "background task"):
    """
    Decorator para tratamento de erros em tarefas de background
    
    Args:
        task_name: Nome da tarefa para logs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Erro em {task_name} ({func.__name__}): {str(e)}", exc_info=True)
                # Para tarefas background, não re-raise para não quebrar a aplicação
                return None
        
        return wrapper
    return decorator


class APIError(HTTPException):
    """Classe base para erros customizados da API"""
    
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


class ValidationError(APIError):
    """Erro de validação de dados"""
    
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=400)


class NotFoundError(APIError):
    """Erro de recurso não encontrado"""
    
    def __init__(self, detail: str = "Recurso não encontrado"):
        super().__init__(detail=detail, status_code=404)


class PermissionError(APIError):
    """Erro de permissão"""
    
    def __init__(self, detail: str = "Acesso negado"):
        super().__init__(detail=detail, status_code=403)


class BusinessLogicError(APIError):
    """Erro de regra de negócio"""
    
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=422)