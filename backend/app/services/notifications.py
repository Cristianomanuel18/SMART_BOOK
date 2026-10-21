from sqlalchemy.orm import Session

from app.models import Notificacao


def criar_notificacao(
    db: Session,
    *,
    utilizador_id: int,
    tipo: str,
    titulo: str,
    mensagem: str,
    autor_id: int | None = None,
    referencia_id: int | None = None,
) -> Notificacao:
    """
    Cria uma notificação para um utilizador.

    A função não executa commit: a transação é controlada
    pela operação que originou a notificação.
    """

    if utilizador_id == autor_id:
        raise ValueError(
            "Não é permitido notificar um utilizador sobre a própria ação."
        )

    notificacao = Notificacao(
        utilizador_id=utilizador_id,
        autor_id=autor_id,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        referencia_id=referencia_id,
        lida=False,
    )

    db.add(notificacao)

    return notificacao


def notificar_pedido_amizade(
    db: Session,
    *,
    remetente_id: int,
    destinatario_id: int,
    pedido_id: int,
    nome_remetente: str,
) -> Notificacao:
    return criar_notificacao(
        db,
        utilizador_id=destinatario_id,
        autor_id=remetente_id,
        tipo="pedido_amizade",
        titulo="Novo pedido de amizade",
        mensagem=f"{nome_remetente} enviou-te um pedido de amizade.",
        referencia_id=pedido_id,
    )


def notificar_amizade_aceite(
    db: Session,
    *,
    remetente_id: int,
    destinatario_id: int,
    nome_utilizador: str,
    pedido_id: int,
) -> Notificacao:
    return criar_notificacao(
        db,
        utilizador_id=remetente_id,
        autor_id=destinatario_id,
        tipo="amizade_aceite",
        titulo="Pedido de amizade aceite",
        mensagem=f"{nome_utilizador} aceitou o teu pedido de amizade.",
        referencia_id=pedido_id,
    )


def notificar_mensagem(
    db: Session,
    *,
    remetente_id: int,
    destinatario_id: int,
    mensagem_id: int,
    nome_remetente: str,
) -> Notificacao:
    return criar_notificacao(
        db,
        utilizador_id=destinatario_id,
        autor_id=remetente_id,
        tipo="mensagem",
        titulo="Nova mensagem",
        mensagem=f"{nome_remetente} enviou-te uma mensagem.",
        referencia_id=mensagem_id,
    )


def notificar_nova_publicacao(
    db: Session,
    *,
    autor_id: int,
    destinatario_id: int,
    publicacao_id: int,
    nome_autor: str,
) -> Notificacao:
    return criar_notificacao(
        db,
        utilizador_id=destinatario_id,
        autor_id=autor_id,
        tipo="publicacao",
        titulo="Nova publicação",
        mensagem=f"{nome_autor} publicou uma nova atualização.",
        referencia_id=publicacao_id,
    )