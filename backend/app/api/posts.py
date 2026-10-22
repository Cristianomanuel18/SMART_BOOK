
from app.database.connection import obter_sessao
from app.models.post import Post
from app.models.user import User
from app.schemas.posts import CriarPublicacao
from app.security.auth import obter_token, validar_token_acesso
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/posts",
    tags=["Publicações"],
)


def utilizador_da_sessao(token: str, db: Session) -> User:
    payload = validar_token_acesso(token)

    utilizador_id = int(payload["sub"])

    utilizador = (
        db.query(User)
        .filter(User.id == utilizador_id)
        .first()
    )

    if not utilizador or not utilizador.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A conta não existe ou está desativada.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return utilizador


def representar_publicacao(
    publicacao: Post,
    autor: User,
) -> dict:
    return {
        "id": publicacao.id,
        "autor_id": autor.id,
        "autor_nome": autor.nome_completo,
        "autor_username": autor.username,
        "conteudo": publicacao.conteudo,
        "data_criacao": publicacao.data_criacao,
    }


@router.get("")
def listar_publicacoes(
    limite: int = Query(default=50, ge=1, le=100),
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador_da_sessao(token, db)

    resultados = (
        db.query(Post, User)
        .join(User, Post.autor_id == User.id)
        .filter(User.ativo.is_(True))
        .order_by(
            Post.data_criacao.desc(),
            Post.id.desc(),
        )
        .limit(limite)
        .all()
    )

    return [
        representar_publicacao(publicacao, autor)
        for publicacao, autor in resultados
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_publicacao(
    dados: CriarPublicacao,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    autor = utilizador_da_sessao(token, db)

    conteudo = dados.conteudo.strip()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Escreve alguma coisa antes de publicar.",
        )

    publicacao = Post(
        autor_id=autor.id,
        conteudo=conteudo,
    )

    db.add(publicacao)
    db.commit()
    db.refresh(publicacao)

    return representar_publicacao(publicacao, autor)


@router.delete(
    "/{publicacao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def apagar_publicacao(
    publicacao_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    autor = utilizador_da_sessao(token, db)

    publicacao = (
        db.query(Post)
        .filter(Post.id == publicacao_id)
        .first()
    )

    if not publicacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicação não encontrada.",
        )

    if (
        publicacao.autor_id != autor.id
        and not autor.administrador
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só podes apagar as tuas próprias publicações.",
        )

    db.delete(publicacao)
    db.commit()

