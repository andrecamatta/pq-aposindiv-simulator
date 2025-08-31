from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
import os
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
    create_db_and_tables()
    
    # Aqui podemos adicionar dados iniciais se necessário
    with Session(engine) as session:
        # Verificar se já existem dados para evitar duplicação
        from .models.database import MortalityTable
        
        # Exemplo: verificar se já existem tábuas de mortalidade
        existing_tables = session.query(MortalityTable).first()
        if not existing_tables:
            # Aqui seria chamada a função para popular tábuas iniciais
            pass
        
        session.commit()


# Função para resetar o banco (útil para desenvolvimento)
def reset_database():
    """CUIDADO: Remove todas as tabelas e recria"""
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()