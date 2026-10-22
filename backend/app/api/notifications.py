from app.database.connection import obter_sessao
from app.models import Notificacao, User
from app.security.auth import obter_token, validar_token_acesso
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/notificacoes",
    tags=["Notificações"],
)


# ============================================================
# UTILIZADOR AUTENTICADO
# ============================================================

def obter_utilizador_atual(
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    dados = validar_token_acesso(token)

    identificador = (
        dados.get("sub")
        or dados.get("utilizador_id")
        or dados.get("id")
    )

    if identificador is None:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida.",
        )

    try:
        utilizador_id = int(identificador)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Identificação inválida.",
        )

    utilizador = db.query(User).filter(
        User.id == utilizador_id,
        User.ativo.is_(True),
    ).first()

    if not utilizador:
        raise HTTPException(
            status_code=401,
            detail="Conta inexistente ou desativada.",
        )

    return utilizador


# ============================================================
# FORMATAR NOTIFICAÇÃO
# ============================================================

def formatar_notificacao(
    notificacao: Notificacao,
    autor: User | None = None,
):
    return {
        "id": notificacao.id,
        "tipo": notificacao.tipo,
        "titulo": notificacao.titulo,
        "mensagem": notificacao.mensagem,
        "autor": (
            {
                "id": autor.id,
                "nome_completo": autor.nome_completo,
                "username": autor.username,
            }
            if autor
            else None
        ),
        "referencia_id": notificacao.referencia_id,
        "lida": notificacao.lida,
        "data_criacao": notificacao.data_criacao,
    }


# ============================================================
# LISTAR NOTIFICAÇÕES
# ============================================================

@router.get("")
def listar_notificacoes(
    limite: int = Query(default=30, ge=1, le=100),
    apenas_nao_lidas: bool = False,
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    consulta = db.query(Notificacao).filter(
        Notificacao.utilizador_id == atual.id,
    )

    if apenas_nao_lidas:
        consulta = consulta.filter(
            Notificacao.lida.is_(False),
        )

    notificacoes = (
        consulta
        .order_by(
            Notificacao.data_criacao.desc(),
            Notificacao.id.desc(),
        )
        .limit(limite)
        .all()
    )

    resultado = []

    for notificacao in notificacoes:
        autor = None

        if notificacao.autor_id is not None:
            autor = db.query(User).filter(
                User.id == notificacao.autor_id,
            ).first()

        resultado.append(
            formatar_notificacao(notificacao, autor)
        )

    nao_lidas = db.query(Notificacao).filter(
        Notificacao.utilizador_id == atual.id,
        Notificacao.lida.is_(False),
    ).count()

    return {
        "total": len(resultado),
        "nao_lidas": nao_lidas,
        "notificacoes": resultado,
    }


# ============================================================
# CONTAR NOTIFICAÇÕES NÃO LIDAS
# ============================================================

@router.get("/contagem")
def contar_notificacoes(
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    quantidade = db.query(Notificacao).filter(
        Notificacao.utilizador_id == atual.id,
        Notificacao.lida.is_(False),
    ).count()

    return {
        "nao_lidas": quantidade,
    }


# ============================================================
# MARCAR UMA NOTIFICAÇÃO COMO LIDA
# ============================================================

@router.patch("/{notificacao_id}/ler")
def marcar_como_lida(
    notificacao_id: int,
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    notificacao = db.query(Notificacao).filter(
        Notificacao.id == notificacao_id,
        Notificacao.utilizador_id == atual.id,
    ).first()

    if not notificacao:
        raise HTTPException(
            status_code=404,
            detail="Notificação não encontrada.",
        )

    notificacao.lida = True

    db.commit()

    return {
        "mensagem": "Notificação marcada como lida.",
        "id": notificacao.id,
        "lida": True,
    }


# ============================================================
# MARCAR TODAS COMO LIDAS
# ============================================================

@router.patch("/ler-todas")
def marcar_todas_como_lidas(
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    quantidade = db.query(Notificacao).filter(
        Notificacao.utilizador_id == atual.id,
        Notificacao.lida.is_(False),
    ).update(
        {Notificacao.lida: True},
        synchronize_session=False,
    )

    db.commit()

    return {
        "mensagem": "Todas as notificações foram marcadas como lidas.",
        "quantidade_atualizada": quantidade,
    }


# ============================================================
# APAGAR NOTIFICAÇÃO
# ============================================================

@router.delete("/{notificacao_id}")
def apagar_notificacao(
    notificacao_id: int,
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    notificacao = db.query(Notificacao).filter(
        Notificacao.id == notificacao_id,
        Notificacao.utilizador_id == atual.id,
    ).first()

    if not notificacao:
        raise HTTPException(
            status_code=404,
            detail="Notificação não encontrada.",
        )

    db.delete(notificacao)
    db.commit()

    return {
        "mensagem": "Notificação apagada.",
        "id": notificacao_id,
    }