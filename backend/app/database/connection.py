
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Localização da pasta principal do projeto
ROOT_DIR = Path(__file__).resolve().parents[3]

# Carregar o .env local sem substituir variáveis já definidas
# pelo ambiente de execução (por exemplo, o Render).
load_dotenv(ROOT_DIR / ".env")

# Preferir a URL completa fornecida pelo Render.
DATABASE_URL_ENV = os.getenv("DATABASE_URL")

if DATABASE_URL_ENV:
    # O Render pode fornecer URLs com o esquema postgres://.
    # O SQLAlchemy moderno utiliza postgresql:// ou postgresql+psycopg://.
    DATABASE_URL_ENV = DATABASE_URL_ENV.strip()

    if DATABASE_URL_ENV.startswith("postgres://"):
        DATABASE_URL_ENV = DATABASE_URL_ENV.replace(
            "postgres://",
            "postgresql://",
            1,
        )

    url = make_url(DATABASE_URL_ENV)

    # Forçar o driver psycopg 3, instalado no projeto.
    url = url.set(drivername="postgresql+psycopg")

    # Utilizar SSL nas ligações PostgreSQL em produção.
    # O Render suporta SSL; na ligação local, não o forçamos.
    if os.getenv("RENDER"):
        parametros = dict(url.query)
        parametros.setdefault("sslmode", "require")
        url = url.set(query=parametros)

    DATABASE_URL = url

else:
    # Compatibilidade com a configuração local existente.
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "smart_book")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not DB_PASSWORD:
        raise RuntimeError(
            "Não foi encontrada DATABASE_URL nem DB_PASSWORD. "
            "Verifica as variáveis de ambiente ou o ficheiro .env."
        )

    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    )

# Criar o motor de ligação à base de dados.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Criar sessões para consultar e guardar dados.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Classe base para os modelos.
class Base(DeclarativeBase):
    pass


# Dependência para utilizar sessões nas rotas da API.
def obter_sessao():
    sessao = SessionLocal()

    try:
        yield sessao
    finally:
        sessao.close()


# Compatibilidade com rotas que utilizam get_db.
get_db = obter_sessao
