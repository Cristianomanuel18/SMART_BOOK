
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.connection import obter_sessao
from app.models.user import User

from app.schemas.auth import (
    RegistoUtilizador,
    LoginUtilizador,
    RespostaAutenticacao,
    UtilizadorPublico,
)

from app.security.auth import (
    gerar_hash_password,
    verificar_password,
    criar_token_acesso,
    validar_token_acesso,
    obter_token,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticação"],
)


@router.post(
    "/register",
    response_model=RespostaAutenticacao,
    status_code=status.HTTP_201_CREATED,
)
def registar_utilizador(
    dados: RegistoUtilizador,
    db: Session = Depends(obter_sessao),
):
    nome_completo = " ".join(
        dados.nome_completo.split()
    )

    username = dados.username.strip().lower()
    email = str(dados.email).strip().lower()

    if len(nome_completo) < 2:
        raise HTTPException(
            status_code=400,
            detail="Introduz o teu nome completo.",
        )

    existente = db.query(User).filter(
        or_(
            User.username == username,
            User.email == email,
        )
    ).first()

    if existente:
        if existente.username == username:
            raise HTTPException(
                status_code=409,
                detail="Este nome de utilizador já está em uso.",
            )

        raise HTTPException(
            status_code=409,
            detail="Este email já está registado.",
        )

    utilizador = User(
        nome_completo=nome_completo,
        username=username,
        email=email,
        password_hash=gerar_hash_password(
            dados.password
        ),
        ativo=True,
        administrador=False,
    )

    try:
        db.add(utilizador)
        db.commit()
        db.refresh(utilizador)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível criar a conta. "
                "Tenta novamente."
            ),
        )

    token = criar_token_acesso(
        utilizador_id=utilizador.id,
        username=utilizador.username,
    )

    return {
        "mensagem": "Conta criada com sucesso!",
        "access_token": token,
        "token_type": "bearer",
        "utilizador": utilizador,
    }


@router.post(
    "/login",
    response_model=RespostaAutenticacao,
)
def iniciar_sessao(
    dados: LoginUtilizador,
    db: Session = Depends(obter_sessao),
):
    identificador = dados.identificador.strip().lower()

    utilizador = db.query(User).filter(
        or_(
            User.email == identificador,
            User.username == identificador,
        )
    ).first()

    if (
        not utilizador
        or not verificar_password(
            dados.password,
            utilizador.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas.",
        )

    if not utilizador.ativo:
        raise HTTPException(
            status_code=403,
            detail="Esta conta encontra-se desativada.",
        )

    token = criar_token_acesso(
        utilizador_id=utilizador.id,
        username=utilizador.username,
    )

    return {
        "mensagem": "Sessão iniciada com sucesso!",
        "access_token": token,
        "token_type": "bearer",
        "utilizador": utilizador,
    }


@router.get(
    "/me",
    response_model=UtilizadorPublico,
)
def consultar_utilizador_atual(
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    """
    Devolve os dados públicos do utilizador autenticado.
    """

    payload = validar_token_acesso(token)

    utilizador_id = int(payload["sub"])

    utilizador = db.query(User).filter(
        User.id == utilizador_id
    ).first()

    if not utilizador or not utilizador.ativo:
        raise HTTPException(
            status_code=401,
            detail="A conta não existe ou está desativada.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return utilizador
