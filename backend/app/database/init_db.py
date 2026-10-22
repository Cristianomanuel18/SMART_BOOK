
from sqlalchemy import inspect

from app.database.connection import Base, engine

# Importar todos os modelos para os registar no SQLAlchemy.
import app.models  # noqa: F401


def criar_tabelas():
    """
    Cria as tabelas dos modelos registados que ainda não existem.
    Não apaga tabelas nem dados existentes.
    """
    print("A preparar a estrutura da base de dados SMART BOOK...")

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tabelas = sorted(inspector.get_table_names())

    print("\nTabelas encontradas na base de dados:")
    for tabela in tabelas:
        print(f"  - {tabela}")

    print(f"\nTotal de tabelas encontradas: {len(tabelas)}")
    print("Verificação da estrutura concluída.")


if __name__ == "__main__":
    criar_tabelas()
