from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import User, Mensagem, PedidoAmizade
from app.security.auth import obter_token, validar_token_acesso
from app.schemas.messages import CriarMensagem
from app.services.notifications import notificar_mensagem


router = APIRouter(
    prefix="/api/mensagens",
    tags=["Mensagens"],
)


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def obter_utilizador_atual(
    token: str = Depends(obter_token),
    db: Session = Depends(get_db),
) -> User:
    """Obtém o utilizador autenticado através do token JWT."""

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
            detail="Token sem identificador de utilizador.",
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
# VERIFICAR AMIZADE
# ============================================================

def verificar_amizade(
    db: Session,
    utilizador_a_id: int,
    utilizador_b_id: int,
) -> bool:
    """
    Só permite mensagens privadas entre utilizadores
    cuja amizade tenha sido aceite.
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
# FORMATAÇÃO
# ============================================================

def formatar_mensagem(
    mensagem: Mensagem,
    db: Session,
) -> dict:
    """Devolve os dados de uma mensagem sem expor dados privados."""

    remetente = (
        db.query(User)
        .filter(User.id == mensagem.remetente_id)
        .first()
    )

    destinatario = (
        db.query(User)
        .filter(User.id == mensagem.destinatario_id)
        .first()
    )

    return {
        "id": mensagem.id,
        "remetente_id": mensagem.remetente_id,
        "destinatario_id": mensagem.destinatario_id,
        "conteudo": mensagem.conteudo,
        "lida": mensagem.lida,
        "data_criacao": mensagem.data_criacao,
        "remetente": (
            {
                "id": remetente.id,
                "nome_completo": remetente.nome_completo,
                "username": remetente.username,
            }
            if remetente
            else None
        ),
        "destinatario": (
            {
                "id": destinatario.id,
                "nome_completo": destinatario.nome_completo,
                "username": destinatario.username,
            }
            if destinatario
            else None
        ),
    }


# ============================================================
# ENVIAR MENSAGEM PRIVADA
# ============================================================

@router.post(
    "/{utilizador_id}",
    status_code=status.HTTP_201_CREATED,
)
def enviar_mensagem(
    utilizador_id: int,
    dados: CriarMensagem,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Envia uma mensagem privada a um amigo.

    A mensagem e a respetiva notificação são gravadas
    na mesma transação da base de dados.
    """

    if utilizador_id == atual.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não podes enviar uma mensagem a ti próprio.",
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
            detail="Destinatário não encontrado ou conta desativada.",
        )

    if not verificar_amizade(
        db,
        atual.id,
        destinatario.id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só podes enviar mensagens a utilizadores que sejam teus amigos.",
        )

    conteudo = dados.conteudo.strip()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A mensagem não pode estar vazia.",
        )

    mensagem = Mensagem(
        remetente_id=atual.id,
        destinatario_id=destinatario.id,
        conteudo=conteudo,
        lida=False,
        data_criacao=datetime.now(timezone.utc),
    )

    try:
        db.add(mensagem)
        db.flush()

        notificar_mensagem(
            db,
            remetente_id=atual.id,
            destinatario_id=destinatario.id,
            mensagem_id=mensagem.id,
            nome_remetente=atual.nome_completo,
        )

        db.commit()
        db.refresh(mensagem)

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Mensagem enviada com sucesso.",
        "dados": formatar_mensagem(mensagem, db),
    }


# ============================================================
# HISTÓRICO DE CONVERSA
# ============================================================

@router.get("/{utilizador_id}")
def obter_conversa(
    utilizador_id: int,
    limite: int = Query(default=100, ge=1, le=200),
    antes_id: int | None = Query(default=None, ge=1),
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Devolve o histórico de mensagens entre a conta autenticada
    e outro utilizador.

    As mensagens recebidas são marcadas como lidas.
    O parâmetro antes_id permite carregar mensagens anteriores.
    """

    if utilizador_id == atual.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não podes abrir uma conversa contigo próprio.",
        )

    outro_utilizador = (
        db.query(User)
        .filter(
            User.id == utilizador_id,
            User.ativo.is_(True),
        )
        .first()
    )

    if not outro_utilizador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )

    if not verificar_amizade(
        db,
        atual.id,
        outro_utilizador.id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só podes consultar conversas com os teus amigos.",
        )

    consulta = db.query(Mensagem).filter(
        or_(
            and_(
                Mensagem.remetente_id == atual.id,
                Mensagem.destinatario_id == utilizador_id,
            ),
            and_(
                Mensagem.remetente_id == utilizador_id,
                Mensagem.destinatario_id == atual.id,
            ),
        )
    )

    if antes_id is not None:
        consulta = consulta.filter(
            Mensagem.id < antes_id,
        )

    # Busca as mais recentes primeiro para limitar a consulta.
    mensagens = (
        consulta
        .order_by(Mensagem.id.desc())
        .limit(limite)
        .all()
    )

    # O histórico é devolvido da mais antiga para a mais recente.
    mensagens.reverse()

    # Marca como lidas apenas as mensagens recebidas
    # que fazem parte do histórico consultado.
    mensagens_nao_lidas = [
        mensagem
        for mensagem in mensagens
        if (
            mensagem.destinatario_id == atual.id
            and not mensagem.lida
        )
    ]

    try:
        for mensagem in mensagens_nao_lidas:
            mensagem.lida = True

        if mensagens_nao_lidas:
            db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "conversa_com": {
            "id": outro_utilizador.id,
            "nome_completo": outro_utilizador.nome_completo,
            "username": outro_utilizador.username,
        },
        "total": len(mensagens),
        "mensagens": [
            formatar_mensagem(mensagem, db)
            for mensagem in mensagens
        ],
        "tem_mais": len(mensagens) == limite,
    }


# ============================================================
# LISTAR CONVERSAS
# ============================================================

@router.get("")
def listar_conversas(
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Lista as conversas da conta autenticada.

    Para cada conversa, apresenta a mensagem mais recente
    e a quantidade de mensagens ainda não lidas.
    """

    mensagens = (
        db.query(Mensagem)
        .filter(
            or_(
                Mensagem.remetente_id == atual.id,
                Mensagem.destinatario_id == atual.id,
            )
        )
        .order_by(Mensagem.id.desc())
        .all()
    )

    conversas_por_utilizador = {}

    for mensagem in mensagens:
        if mensagem.remetente_id == atual.id:
            outro_id = mensagem.destinatario_id
        else:
            outro_id = mensagem.remetente_id

        if outro_id not in conversas_por_utilizador:
            conversas_por_utilizador[outro_id] = {
                "ultima_mensagem": mensagem,
                "nao_lidas": 0,
            }

        if (
            mensagem.destinatario_id == atual.id
            and not mensagem.lida
        ):
            conversas_por_utilizador[outro_id]["nao_lidas"] += 1

    resultado = []

    for outro_id, dados in conversas_por_utilizador.items():
        outro_utilizador = (
            db.query(User)
            .filter(
                User.id == outro_id,
                User.ativo.is_(True),
            )
            .first()
        )

        if not outro_utilizador:
            continue

        # Não expõe conversas com utilizadores que já não são amigos.
        if not verificar_amizade(
            db,
            atual.id,
            outro_id,
        ):
            continue

        ultima_mensagem = dados["ultima_mensagem"]

        resultado.append(
            {
                "utilizador": {
                    "id": outro_utilizador.id,
                    "nome_completo": outro_utilizador.nome_completo,
                    "username": outro_utilizador.username,
                },
                "ultima_mensagem": formatar_mensagem(
                    ultima_mensagem,
                    db,
                ),
                "mensagens_nao_lidas": dados["nao_lidas"],
            }
        )

    resultado.sort(
        key=lambda conversa: (
            conversa["ultima_mensagem"]["data_criacao"]
            or datetime.min.replace(tzinfo=timezone.utc)
        ),
        reverse=True,
    )

    return {
        "total": len(resultado),
        "conversas": resultado,
    }


# ============================================================
# ELIMINAR MENSAGEM
# ============================================================

@router.delete("/mensagem/{mensagem_id}")
def eliminar_mensagem(
    mensagem_id: int,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(get_db),
):
    """
    Elimina uma mensagem enviada pela conta autenticada.

    Não permite eliminar mensagens enviadas por outros utilizadores.
    """

    mensagem = (
        db.query(Mensagem)
        .filter(Mensagem.id == mensagem_id)
        .first()
    )

    if not mensagem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensagem não encontrada.",
        )

    if mensagem.remetente_id != atual.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só podes eliminar as mensagens que enviaste.",
        )

    try:
        db.delete(mensagem)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "mensagem": "Mensagem eliminada com sucesso.",
        "mensagem_id": mensagem_id,
    }