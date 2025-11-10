from sqlmodel import create_engine, Session, SQLModel
from typing import Generator
from dotenv import load_dotenv
import os

# Carrega variáveis do arquivo .env
load_dotenv()

# Pega a URL do banco do .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Variável de ambiente DATABASE_URL não definida no .env")

# Cria engine do banco de dados
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

def create_db_and_tables():
    """Cria todas as tabelas no banco de dados"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency para obter sessão do banco de dados"""
    with Session(engine) as session:
        yield session