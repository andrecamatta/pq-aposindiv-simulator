from contextlib import asynccontextmanager
from sqlmodel import Session
from ..database import engine
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_background_session():
    """
    Context manager for database sessions in background tasks
    
    Usage:
        async with get_background_session() as session:
            # Use session here
            repo = SomeRepository(session)
            # Session is automatically closed when exiting context
    """
    session = None
    try:
        session = Session(engine)
        logger.debug("Criada sessão do banco para tarefa background")
        yield session
    except Exception as e:
        if session:
            session.rollback()
            logger.error(f"Erro na sessão background, rollback executado: {e}")
        raise
    finally:
        if session:
            session.close()
            logger.debug("Sessão do banco fechada para tarefa background")


class BackgroundSessionMixin:
    """
    Mixin que fornece session management para classes que executam background tasks
    """
    
    async def with_session(self, func, *args, **kwargs):
        """
        Execute a function with a managed database session
        
        Args:
            func: Function to execute that takes session as first parameter
            *args: Additional arguments to pass to func
            **kwargs: Additional keyword arguments to pass to func
        """
        async with get_background_session() as session:
            return await func(session, *args, **kwargs)
    
    async def run_with_session(self, operations):
        """
        Execute multiple operations within a single session
        
        Args:
            operations: List of callables or async callables that take session as first parameter
        """
        async with get_background_session() as session:
            results = []
            for operation in operations:
                if callable(operation):
                    if hasattr(operation, '__await__'):
                        result = await operation(session)
                    else:
                        result = operation(session)
                    results.append(result)
            return results


def with_background_session(func):
    """
    Decorator that automatically injects a database session as the first argument
    
    Usage:
        @with_background_session
        async def my_background_task(session, other_args):
            # session is automatically provided
            repo = SomeRepository(session)
            # ...
    """
    async def wrapper(*args, **kwargs):
        async with get_background_session() as session:
            return await func(session, *args, **kwargs)
    return wrapper