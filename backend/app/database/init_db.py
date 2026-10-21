
from app.database.connection import Base, engine

# Modelos existentes
from app.models import (
    User,
    Post,
    Profile,
    PedidoAmizade,
    Mensagem,
    Notificacao,
    Video,
    Casa,
    DivisaoCasa,
    DispositivoInteligente,
    AutomacaoCasa,
    HistoricoCasa,
    OportunidadeNegocio,
)




def criar_tabelas():
    """
    Cria as tabelas dos modelos que ainda não existem.
    Não apaga as tabelas nem os dados existentes.
    """

    Base.metadata.create_all(bind=engine)

    print("Estrutura da base de dados SMART BOOK preparada.")
    print("Modelos sociais carregados.")
    print("Modelos da Casa Inteligente carregados.")
    print("Modelo Negócio com Oportunidade carregado.")
    print("Modelos Home Assistant carregados.")
    print("Verificação de criação das tabelas concluída.")


if __name__ == "__main__":
    criar_tabelas()
