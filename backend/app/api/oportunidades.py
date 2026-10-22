from typing import Literal

from app.database.connection import obter_sessao
from app.models import OportunidadeNegocio, User
from app.security.auth import obter_token, validar_token_acesso
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/negocio-oportunidade",
    tags=["Negócio com Oportunidade"],
)


# =========================================================
# AUTENTICAÇÃO
# =========================================================

def obter_utilizador_atual(
    token: str,
    db: Session,
) -> User:

    try:
        payload = validar_token_acesso(token)
        user_id = int(payload["sub"])

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida. Inicia sessão novamente.",
        )

    utilizador = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.ativo.is_(True),
        )
        .first()
    )

    if utilizador is None:
        raise HTTPException(
            status_code=401,
            detail="Utilizador não encontrado ou desativado.",
        )

    return utilizador


# =========================================================
# MODELOS DE ENTRADA
# =========================================================

class RegistoEntrada(BaseModel):

    tipo: Literal["profissional", "empresa"] = "profissional"

    nome: str = Field(min_length=2, max_length=120)

    area: str = Field(min_length=2, max_length=120)

    habilidades: str = Field(min_length=2, max_length=500)

    experiencia: str | None = Field(
        default=None,
        max_length=500,
    )

    escolaridade: str | None = Field(
        default=None,
        max_length=120,
    )

    localizacao: str | None = Field(
        default=None,
        max_length=120,
    )

    telefone: str | None = Field(
        default=None,
        max_length=40,
    )

    descricao: str | None = Field(
        default=None,
        max_length=1500,
    )

    disponibilidade: str | None = Field(
        default=None,
        max_length=120,
    )


class RegistoAtualizacao(BaseModel):

    tipo: Literal["profissional", "empresa"] | None = None

    nome: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    area: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    habilidades: str | None = Field(
        default=None,
        min_length=2,
        max_length=500,
    )

    experiencia: str | None = Field(
        default=None,
        max_length=500,
    )

    escolaridade: str | None = Field(
        default=None,
        max_length=120,
    )

    localizacao: str | None = Field(
        default=None,
        max_length=120,
    )

    telefone: str | None = Field(
        default=None,
        max_length=40,
    )

    descricao: str | None = Field(
        default=None,
        max_length=1500,
    )

    disponibilidade: str | None = Field(
        default=None,
        max_length=120,
    )


# =========================================================
# FORMATAÇÃO DAS RESPOSTAS
# =========================================================

def converter_registo(registo, username=None):

    return {
        "id": registo.id,
        "utilizador_id": registo.utilizador_id,
        "username": username,
        "tipo": registo.tipo,
        "nome": registo.nome,
        "area": registo.area,
        "habilidades": registo.habilidades,
        "experiencia": registo.experiencia,
        "escolaridade": registo.escolaridade,
        "localizacao": registo.localizacao,
        "telefone": registo.telefone,
        "descricao": registo.descricao,
        "disponibilidade": registo.disponibilidade,
        "data_criacao": registo.data_criacao,
        "data_atualizacao": registo.data_atualizacao,
    }


# =========================================================
# PESQUISAR PROFISSIONAIS E EMPREENDIMENTOS
# =========================================================

@router.get("/pesquisar")
def pesquisar(
    q: str = Query(default="", max_length=120),

    tipo: Literal[
        "todos",
        "profissional",
        "empresa",
    ] = "todos",

    limite: int = Query(
        default=100,
        ge=1,
        le=200,
    ),

    token: str = Depends(obter_token),

    db: Session = Depends(obter_sessao),
):

    obter_utilizador_atual(token, db)

    consulta = (
        db.query(
            OportunidadeNegocio,
            User.username,
        )
        .join(
            User,
            User.id == OportunidadeNegocio.utilizador_id,
        )
        .filter(User.ativo.is_(True))
    )

    if tipo != "todos":
        consulta = consulta.filter(
            OportunidadeNegocio.tipo == tipo
        )

    termo = q.strip()

    if termo:
        padrao = f"%{termo}%"

        consulta = consulta.filter(
            or_(
                OportunidadeNegocio.nome.ilike(padrao),
                OportunidadeNegocio.area.ilike(padrao),
                OportunidadeNegocio.habilidades.ilike(padrao),
                OportunidadeNegocio.experiencia.ilike(padrao),
                OportunidadeNegocio.escolaridade.ilike(padrao),
                OportunidadeNegocio.localizacao.ilike(padrao),
                OportunidadeNegocio.descricao.ilike(padrao),
            )
        )

    resultados = (
        consulta
        .order_by(
            OportunidadeNegocio.data_criacao.desc()
        )
        .limit(limite)
        .all()
    )

    registos = [
        converter_registo(registo, username)
        for registo, username in resultados
    ]

    return {
        "total": len(registos),
        "registos": registos,
    }


# =========================================================
# OS MEUS REGISTOS
# =========================================================

@router.get("/meus")
def meus_registos(
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):

    utilizador = obter_utilizador_atual(token, db)

    resultados = (
        db.query(OportunidadeNegocio)
        .filter(
            OportunidadeNegocio.utilizador_id
            == utilizador.id
        )
        .order_by(
            OportunidadeNegocio.data_criacao.desc()
        )
        .all()
    )

    return {
        "total": len(resultados),
        "registos": [
            converter_registo(
                registo,
                utilizador.username,
            )
            for registo in resultados
        ],
    }


# =========================================================
# CRIAR PERFIL OU EMPREENDIMENTO
# =========================================================

@router.post(
    "/registos",
    status_code=status.HTTP_201_CREATED,
)
def criar_registo(
    dados: RegistoEntrada,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):

    utilizador = obter_utilizador_atual(token, db)

    valores = dados.model_dump()

    for campo in ("nome", "area", "habilidades"):
        valores[campo] = valores[campo].strip()

    for campo in (
        "experiencia",
        "escolaridade",
        "localizacao",
        "telefone",
        "descricao",
        "disponibilidade",
    ):
        if valores[campo] is not None:
            valores[campo] = valores[campo].strip() or None

    registo = OportunidadeNegocio(
        utilizador_id=utilizador.id,
        **valores,
    )

    try:
        db.add(registo)
        db.commit()
        db.refresh(registo)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Erro ao guardar o registo na base de dados.",
        )

    return {
        "mensagem": "Publicado com sucesso.",
        "registo": converter_registo(
            registo,
            utilizador.username,
        ),
    }


# =========================================================
# ATUALIZAR REGISTO PRÓPRIO
# =========================================================

@router.put("/registos/{registo_id}")
def atualizar_registo(
    registo_id: int,
    dados: RegistoAtualizacao,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):

    utilizador = obter_utilizador_atual(token, db)

    registo = (
        db.query(OportunidadeNegocio)
        .filter(
            OportunidadeNegocio.id == registo_id,
            OportunidadeNegocio.utilizador_id
            == utilizador.id,
        )
        .first()
    )

    if registo is None:
        raise HTTPException(
            status_code=404,
            detail="Registo não encontrado na tua conta.",
        )

    for campo, valor in dados.model_dump(
        exclude_unset=True
    ).items():

        if isinstance(valor, str):
            valor = valor.strip() or None

        setattr(registo, campo, valor)

    try:
        db.commit()
        db.refresh(registo)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar o registo.",
        )

    return {
        "mensagem": "Registo atualizado.",
        "registo": converter_registo(
            registo,
            utilizador.username,
        ),
    }


# =========================================================
# ELIMINAR REGISTO PRÓPRIO
# =========================================================

@router.delete("/registos/{registo_id}")
def eliminar_registo(
    registo_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):

    utilizador = obter_utilizador_atual(token, db)

    registo = (
        db.query(OportunidadeNegocio)
        .filter(
            OportunidadeNegocio.id == registo_id,
            OportunidadeNegocio.utilizador_id
            == utilizador.id,
        )
        .first()
    )

    if registo is None:
        raise HTTPException(
            status_code=404,
            detail="Registo não encontrado na tua conta.",
        )

    try:
        db.delete(registo)
        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Erro ao eliminar o registo.",
        )

    return {
        "mensagem": "Registo eliminado com sucesso."
    }