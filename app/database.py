from sqlmodel import create_engine, Session, SQLModel
from typing import Generator

# Configuração do banco de dados SQLite
DATABASE_URL = "sqlite:///./database.db"

# Criar engine do banco de dados
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Cria todas as tabelas no banco de dados"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency para obter sessão do banco de dados"""
    with Session(engine) as session:
        yield session