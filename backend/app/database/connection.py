import os

from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Localização da pasta principal do projeto
ROOT_DIR = Path(__file__).resolve().parents[3]

# Carregar as configurações do ficheiro .env
load_dotenv(ROOT_DIR / ".env")


# Configurações da base de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "smart_book")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError(
        "A variável DB_PASSWORD não foi encontrada. "
        "Confirma o ficheiro .env na raiz do projeto."
    )


# Construir a ligação de forma segura, incluindo caracteres especiais
from sqlalchemy.engine import URL

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)


# Criar o motor de ligação
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


# Criar sessões para consultar e guardar dados
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Classe base para os modelos da base de dados
class Base(DeclarativeBase):
    pass


# Dependência para utilizar sessões nas rotas da API
def obter_sessao():
    sessao = SessionLocal()

    try:
        yield sessao
    finally:
        sessao.close()

        # Compatibilidade com rotas que utilizam get_db

get_db = obter_sessao
