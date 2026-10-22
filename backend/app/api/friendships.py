from datetime import UTC, datetime
from typing import Literal

from app.database.connection import get_db
from app.models import PedidoAmizade, User
from app.security.auth import obter_token, validar_token_acesso
from app.services.notifications import (
    notificar_amizade_aceite,
    notificar_pedido_amizade,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/amizades",
    tags=["Amizades"],
)


# ============================================================
# ESQUEMAS
# ============================================================

class RespostaPedidoAmizade(BaseModel):
    estado: Literal["aceite", "recusado"]


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def obter_utilizador_atual(
    token: str = Depends(obter_token),
    db: Session = Depends(get_db),
) -> User:
    """
    Valida o token de acesso e devolve o utilizador autenticado.
    """

    dados_token = validar_token_acesso(token)

    if not dados_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    identificador = (
        dados_token.get("sub")
        or dados_token.get("utilizador_id")
        or dados_token.get("id")
    )

    if identificador is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token não contém um identificador válido.",
        )

    try:
        utilizador_id = int(identificador)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de utilizador inválido.",
        )

    utilizador = (
        db.query(User)
        .filter(
            User.id == utilizador_id,
            User.ativo.is_(True),
        )
        .first()
    )

    if not utilizador:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizador não encontrado ou conta desativada.",
        )

    return utilizador


# ============================================================
# FORMATAÇÃO DAS RESPOSTAS
# ============================================================

def formatar_utilizador(utilizador: User) -> dict:
    """
    Formata os dados públicos de um utilizador.
    Não devolve a palavra-passe nem o seu hash.
    """

    perfil = getattr(utilizador, "perfil", None)

    return {
        "id": utilizador.id,
        "nome_completo": utilizador.nome_completo,
        "username": utilizador.username,
        "foto_url": getattr(perfil, "foto_url", None),
    }


def formatar_pedido(
    pedido: PedidoAmizade,
    db: Session,
) -> dict:
    """
    Formata um pedido de amizade e inclui os dados públicos
    do remetente e do destinatário.
    """

    remetente = (
        db.query(User)
        .filter(User.id == pedido.remetente_id)
        .first()
    )

    destinatario = (
        db.query(User)
        .filter(User.id == pedido.destinatario_id)
        .first()
    )

    return {
        "id": pedido.id,
        "remetente_id": pedido.remetente_id,
        "destinatario_id": pedido.destinatario_id,
        "estado": pedido.estado,
        "data_criacao": pedido.data_criacao,
        "data_resposta": pedido.data_resposta,
        "remetente": (
            formatar_utilizador(remetente)
            if remetente
            else None
        ),
        "destinatario": (
            formatar_utilizador(destinatario)
            if destinatario
            else None
        ),
    }


# ============================================================
# PESQUISAR PEDIDOS ENTRE DOIS UTILIZADORES
# ============================================================

def procurar_pedido_entre(
    db: Session,
    utilizador_a_id: int,
    utilizador_b_id: int,
):
    """
    Procura um pedido de amizade entre dois utilizadores,
    independentemente de quem o enviou.
    """

    return (
        db.query(PedidoAmizade)
        .filter(
            or_(
                and_(
                    PedidoAmizade.remetente_id == utilizador_a_id,
                    PedidoAmizade.destinatario_id == utilizador_b_id,
                ),
                and_(
                    PedidoAmizade.remetente_id == utilizador_b_id,
                    PedidoAmizade.destinatario_id == utilizador_a_id,
                ),
            )
        )
        .first()
    )


# ============================================================
# VERIFICAR AMIZADE
# ============================================================

def sao_amigos(
    db: Session,
    utilizador_a_id: int,
    utilizador_b_id: int,
) -> bool:
    """
    Verifica se existe um pedido aceite entre os utilizadores.
    """

    pedido = (
        db.query(PedidoAmizade)
        .filter(
            PedidoAmizade.estado == "aceite",
            or_(
                and_(
                    PedidoAmizade.remetente_id == utilizador_a_id,
                    PedidoAmizade.destinatario_id == utilizador_b_id,
                ),
                and_(
                    PedidoAmizade.remetente_id == utilizador_b_id,
                    PedidoAmizade.destinatario_id == utilizador_a_id,
                ),
            ),
        )
        .first()
    )

    return pedido is not None


# ============================================================
# PESQUISAR UTILIZADORES
# ============================================================

@router.get("/utilizadores")
def pesquisar_utilizadores(
    busca: str = Query(default="", max_length=100),
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Pesquisa utilizadores pelo nome completo ou username.

    Indica também se já são amigos ou se existe um pedido
    de amizade pendente.
    """

    consulta = db.query(User).filter(
        User.ativo.is_(True),
        User.id != atual.id,
    )

    termo = busca.strip()

    if termo:
        termo_like = f"%{termo}%"

        consulta = consulta.filter(
            or_(
                User.nome_completo.ilike(termo_like),
                User.username.ilike(termo_like),
            )
        )

    utilizadores = (
        consulta
        .order_by(User.nome_completo.asc())
        .limit(50)
        .all()
    )

    resultados = []

    for utilizador in utilizadores:
        pedido = procurar_pedido_entre(
            db,
            atual.id,
            utilizador.id,
        )

        if not pedido:
            estado_amizade = "disponivel"

        elif pedido.estado == "aceite":
            estado_amizade = "amigos"

        elif pedido.estado == "pendente":
            if pedido.remetente_id == atual.id:
                estado_amizade = "pedido_enviado"
            else:
                estado_amizade = "pedido_recebido"

        else:
            estado_amizade = "disponivel"

        resultado = formatar_utilizador(utilizador)
        resultado["estado_amizade"] = estado_amizade

        resultados.append(resultado)

    return {
        "total": len(resultados),
        "utilizadores": resultados,
    }


# ============================================================
# PEDIDOS DE AMIZADE RECEBIDOS
# ============================================================

@router.get("/pedidos/recebidos")
def listar_pedidos_recebidos(
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Lista os pedidos pendentes enviados por outros utilizadores
    à conta autenticada.
    """

    pedidos = (
        db.query(PedidoAmizade)
        .filter(
            PedidoAmizade.destinatario_id == atual.id,
            PedidoAmizade.estado == "pendente",
        )
        .order_by(PedidoAmizade.data_criacao.desc())
        .all()
    )

    return {
        "total": len(pedidos),
        "pedidos": [
            formatar_pedido(pedido, db)
            for pedido in pedidos
        ],
    }


# ============================================================
# PEDIDOS DE AMIZADE ENVIADOS
# ============================================================

@router.get("/pedidos/enviados")
def listar_pedidos_enviados(
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Lista os pedidos pendentes enviados pela conta autenticada.
    """

    pedidos = (
        db.query(PedidoAmizade)
        .filter(
            PedidoAmizade.remetente_id == atual.id,
            PedidoAmizade.estado == "pendente",
        )
        .order_by(PedidoAmizade.data_criacao.desc())
        .all()
    )

    return {
        "total": len(pedidos),
        "pedidos": [
            formatar_pedido(pedido, db)
            for pedido in pedidos
        ],
    }


# ============================================================
# RESPONDER A UM PEDIDO DE AMIZADE
# ============================================================

@router.patch("/pedidos/{pedido_id}")
def responder_pedido_amizade(
    pedido_id: int,
    dados: RespostaPedidoAmizade,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Aceita ou recusa um pedido de amizade recebido.

    Apenas o destinatário do pedido pode responder.
    """

    pedido = (
        db.query(PedidoAmizade)
        .filter(PedidoAmizade.id == pedido_id)
        .with_for_update()
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido de amizade não encontrado.",
        )

    if pedido.destinatario_id != atual.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não tens autorização para responder a este pedido.",
        )

    if pedido.estado != "pendente":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este pedido já foi respondido.",
        )

    try:
        pedido.estado = dados.estado
        pedido.data_resposta = datetime.now(UTC)

        if dados.estado == "aceite":
            remetente = (
                db.query(User)
                .filter(
                    User.id == pedido.remetente_id,
                    User.ativo.is_(True),
                )
                .first()
            )

            if remetente:
                notificar_amizade_aceite(
                    db,
                    remetente_id=remetente.id,
                    destinatario_id=atual.id,
                    nome_utilizador=atual.nome_completo,
                    pedido_id=pedido.id,
                )

        db.commit()
        db.refresh(pedido)

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": (
            "Pedido de amizade aceite."
            if dados.estado == "aceite"
            else "Pedido de amizade recusado."
        ),
        "pedido": formatar_pedido(pedido, db),
    }


# ============================================================
# LISTAR AMIGOS
# ============================================================

@router.get("")
def listar_amigos(
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Devolve a lista de amigos da conta autenticada.
    """

    pedidos = (
        db.query(PedidoAmizade)
        .filter(
            PedidoAmizade.estado == "aceite",
            or_(
                PedidoAmizade.remetente_id == atual.id,
                PedidoAmizade.destinatario_id == atual.id,
            ),
        )
        .order_by(PedidoAmizade.data_resposta.desc())
        .all()
    )

    amigos = []
    ids_adicionados = set()

    for pedido in pedidos:
        if pedido.remetente_id == atual.id:
            amigo_id = pedido.destinatario_id
        else:
            amigo_id = pedido.remetente_id

        if amigo_id in ids_adicionados:
            continue

        amigo = (
            db.query(User)
            .filter(
                User.id == amigo_id,
                User.ativo.is_(True),
            )
            .first()
        )

        if amigo:
            amigos.append(formatar_utilizador(amigo))
            ids_adicionados.add(amigo_id)

    return {
        "total": len(amigos),
        "amigos": amigos,
    }


# ============================================================
# ENVIAR PEDIDO DE AMIZADE
# ============================================================

@router.post(
    "/pedidos/{utilizador_id}",
    status_code=status.HTTP_201_CREATED,
)
def enviar_pedido_amizade(
    utilizador_id: int,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Envia um pedido de amizade para outro utilizador.

    Cria também uma notificação para o destinatário.
    """

    if utilizador_id == atual.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não podes enviar um pedido de amizade a ti próprio.",
        )

    destinatario = (
        db.query(User)
        .filter(
            User.id == utilizador_id,
            User.ativo.is_(True),
        )
        .first()
    )

    if not destinatario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado ou conta desativada.",
        )

    pedido_existente = procurar_pedido_entre(
        db,
        atual.id,
        destinatario.id,
    )

    if pedido_existente:
        if pedido_existente.estado == "aceite":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já são amigos.",
            )

        if pedido_existente.estado == "pendente":
            if pedido_existente.remetente_id == atual.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já enviaste um pedido a este utilizador.",
                )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este utilizador já te enviou um pedido de amizade. Responde ao pedido recebido.",
            )

        # Permite um novo pedido quando o pedido anterior
        # foi recusado.
        db.delete(pedido_existente)
        db.flush()

    pedido = PedidoAmizade(
        remetente_id=atual.id,
        destinatario_id=destinatario.id,
        estado="pendente",
    )

    try:
        db.add(pedido)
        db.flush()

        notificar_pedido_amizade(
            db,
            remetente_id=atual.id,
            destinatario_id=destinatario.id,
            pedido_id=pedido.id,
            nome_remetente=atual.nome_completo,
        )

        db.commit()
        db.refresh(pedido)

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Pedido de amizade enviado com sucesso.",
        "pedido": formatar_pedido(pedido, db),
    }


# ============================================================
# REMOVER AMIZADE
# ============================================================

@router.delete("/{utilizador_id}")
def remover_amizade(
    utilizador_id: int,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Remove uma amizade existente entre a conta autenticada
    e outro utilizador.
    """

    if utilizador_id == atual.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não podes remover uma amizade contigo próprio.",
        )

    pedido = (
        db.query(PedidoAmizade)
        .filter(
            PedidoAmizade.estado == "aceite",
            or_(
                and_(
                    PedidoAmizade.remetente_id == atual.id,
                    PedidoAmizade.destinatario_id == utilizador_id,
                ),
                and_(
                    PedidoAmizade.remetente_id == utilizador_id,
                    PedidoAmizade.destinatario_id == atual.id,
                ),
            ),
        )
        .first()
    )

    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Não existe uma amizade entre estes utilizadores.",
        )

    try:
        db.delete(pedido)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Amizade removida com sucesso.",
        "utilizador_id": utilizador_id,
    }