from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
import os
import logging
from typing import Generator

# Configuração do banco de dados
DATABASE_DIR = Path(__file__).parent.parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_DIR}/simulador.db"

# Engine do SQLite com configurações otimizadas
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Definir como True para debug
    connect_args={
        "check_same_thread": False,  # Permite uso em múltiplas threads
        "timeout": 30,  # Timeout de 30 segundos
    }
)


def create_db_and_tables():
    """Cria o banco de dados e todas as tabelas"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency para obter sessão do banco de dados"""
    with Session(engine) as session:
        yield session


def init_database():
    """Inicializa o banco de dados com dados padrão"""
    logger = logging.getLogger(__name__)
    
    create_db_and_tables()
    logger.info("Banco de dados inicializado")
    
    # Inicializar tábuas de mortalidade obrigatórias
    try:
        from .core.mortality_initializer import MortalityTableInitializer
        
        initializer = MortalityTableInitializer()
        
        with Session(engine) as session:
            report = initializer.ensure_required_tables(session)
            
            if report["failed_to_load"] > 0:
                logger.warning(
                    f"Algumas tábuas obrigatórias falharam ao carregar: "
                    f"{', '.join(report['failed_tables'])}"
                )
            else:
                logger.info("Todas as tábuas obrigatórias estão disponíveis")
                
    except Exception as e:
        logger.error(f"Erro na inicialização de tábuas obrigatórias: {str(e)}", exc_info=True)
        # Não bloquear a inicialização da aplicação por falhas nas tábuas


# Função para resetar o banco (útil para desenvolvimento)
def reset_database():
    """CUIDADO: Remove todas as tabelas e recria"""
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()