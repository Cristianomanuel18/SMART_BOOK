
import os
import json
import urllib.request
import urllib.error

from datetime import datetime, timezone
from typing import Any, Literal

from dotenv import load_dotenv
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import obter_sessao
from app.models import (
    User,
    Casa,
    DivisaoCasa,
    DispositivoInteligente,
    AutomacaoCasa,
    HistoricoCasa,
)
from app.security.auth import obter_token, validar_token_acesso


# ============================================================
# CONFIGURAÇÃO
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")

router = APIRouter(
    prefix="/api/casa-inteligente",
    tags=["Casa Inteligente"],
)


# ============================================================
# AUTENTICAÇÃO E PROPRIEDADE
# ============================================================

def obter_utilizador(
    token: str,
    db: Session,
) -> User:

    try:
        payload = validar_token_acesso(token)
        utilizador_id = int(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida ou expirada.",
        )

    utilizador = (
        db.query(User)
        .filter(
            User.id == utilizador_id,
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


def obter_casa_do_utilizador(
    db: Session,
    casa_id: int,
    utilizador_id: int,
) -> Casa:

    casa = (
        db.query(Casa)
        .filter(
            Casa.id == casa_id,
            Casa.proprietario_id == utilizador_id,
        )
        .first()
    )

    if casa is None:
        raise HTTPException(
            status_code=404,
            detail="Casa não encontrada.",
        )

    return casa


def obter_dispositivo_da_casa(
    db: Session,
    casa_id: int,
    dispositivo_id: int,
) -> DispositivoInteligente:

    dispositivo = (
        db.query(DispositivoInteligente)
        .filter(
            DispositivoInteligente.id == dispositivo_id,
            DispositivoInteligente.casa_id == casa_id,
            DispositivoInteligente.ativo.is_(True),
        )
        .first()
    )

    if dispositivo is None:
        raise HTTPException(
            status_code=404,
            detail="Dispositivo não encontrado ou desativado.",
        )

    return dispositivo


# ============================================================
# MODELOS DE ENTRADA
# ============================================================

class CriarCasa(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=2000)
    endereco: str | None = Field(default=None, max_length=255)


class AtualizarCasa(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=2000)
    endereco: str | None = Field(default=None, max_length=255)
    ativa: bool | None = None


class CriarDivisao(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=2000)
    icone: str | None = Field(default=None, max_length=80)


class CriarDispositivo(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    tipo: str = Field(min_length=1, max_length=60)
    divisao_id: int | None = None
    marca: str | None = Field(default=None, max_length=100)
    modelo: str | None = Field(default=None, max_length=120)
    integracao: Literal["manual", "home_assistant"] = "manual"
    identificador_integracao: str | None = Field(
        default=None,
        max_length=255,
    )
    entidade_externa: str | None = Field(
        default=None,
        max_length=255,
    )
    capacidades: dict[str, Any] = Field(default_factory=dict)


class ComandoDispositivo(BaseModel):
    comando: Literal[
        "ligar",
        "desligar",
        "alternar",
        "definir_temperatura",
        "definir_brilho",
        "definir_volume",
        "pausar",
        "retomar",
        "parar",
    ]
    parametros: dict[str, Any] = Field(default_factory=dict)


class CriarAutomacao(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=2000)
    tipo_ativacao: Literal["manual", "horario", "evento"] = "manual"
    configuracao: dict[str, Any] = Field(default_factory=dict)
    ativa: bool = False


class AtualizarAutomacao(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=2000)
    tipo_ativacao: Literal["manual", "horario", "evento"] | None = None
    configuracao: dict[str, Any] | None = None
    ativa: bool | None = None


# ============================================================
# RESPOSTAS
# ============================================================

def casa_para_dict(casa: Casa) -> dict:
    return {
        "id": casa.id,
        "nome": casa.nome,
        "descricao": casa.descricao,
        "endereco": casa.endereco,
        "ativa": casa.ativa,
        "data_criacao": casa.data_criacao,
        "data_atualizacao": casa.data_atualizacao,
    }


def divisao_para_dict(divisao: DivisaoCasa) -> dict:
    return {
        "id": divisao.id,
        "casa_id": divisao.casa_id,
        "nome": divisao.nome,
        "descricao": divisao.descricao,
        "icone": divisao.icone,
        "data_criacao": divisao.data_criacao,
    }


def automacao_para_dict(automacao: AutomacaoCasa) -> dict:
    return {
        "id": automacao.id,
        "casa_id": automacao.casa_id,
        "nome": automacao.nome,
        "descricao": automacao.descricao,
        "tipo_ativacao": automacao.tipo_ativacao,
        "configuracao": automacao.configuracao or {},
        "ativa": automacao.ativa,
        "criada_por_ia": automacao.criada_por_ia,
        "data_criacao": automacao.data_criacao,
        "data_atualizacao": automacao.data_atualizacao,
    }


def dispositivo_para_dict(
    dispositivo: DispositivoInteligente,
) -> dict:
    return {
        "id": dispositivo.id,
        "casa_id": dispositivo.casa_id,
        "divisao_id": dispositivo.divisao_id,
        "nome": dispositivo.nome,
        "tipo": dispositivo.tipo,
        "marca": dispositivo.marca,
        "modelo": dispositivo.modelo,
        "integracao": dispositivo.integracao,
        "identificador_integracao": dispositivo.identificador_integracao,
        "entidade_externa": dispositivo.entidade_externa,
        "capacidades": dispositivo.capacidades,
        "estado_conhecido": dispositivo.estado_conhecido,
        "online": dispositivo.online,
        "ativo": dispositivo.ativo,
        "data_criacao": dispositivo.data_criacao,
        "data_atualizacao": dispositivo.data_atualizacao,
    }


# ============================================================
# CASAS
# ============================================================

@router.post(
    "/casas",
    status_code=status.HTTP_201_CREATED,
)
def criar_casa(
    dados: CriarCasa,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    casa = Casa(
        proprietario_id=utilizador.id,
        nome=dados.nome.strip(),
        descricao=dados.descricao,
        endereco=dados.endereco,
        ativa=True,
    )

    db.add(casa)

    try:
        db.commit()
        db.refresh(casa)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível criar a casa.",
        )

    return {
        "mensagem": "Casa criada com sucesso.",
        "casa": casa_para_dict(casa),
    }


@router.get("/casas")
def listar_casas(
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    casas = (
        db.query(Casa)
        .filter(Casa.proprietario_id == utilizador.id)
        .order_by(Casa.id.desc())
        .all()
    )

    return {
        "total": len(casas),
        "casas": [casa_para_dict(casa) for casa in casas],
    }


@router.get("/casas/{casa_id}")
def consultar_casa(
    casa_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    casa = obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    return casa_para_dict(casa)


@router.patch("/casas/{casa_id}")
def atualizar_casa(
    casa_id: int,
    dados: AtualizarCasa,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    casa = obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    alteracoes = dados.model_dump(exclude_unset=True)

    if "nome" in alteracoes and alteracoes["nome"] is not None:
        alteracoes["nome"] = alteracoes["nome"].strip()

    for campo, valor in alteracoes.items():
        setattr(casa, campo, valor)

    try:
        db.commit()
        db.refresh(casa)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível atualizar a casa.",
        )

    return {
        "mensagem": "Casa atualizada.",
        "casa": casa_para_dict(casa),
    }


@router.delete("/casas/{casa_id}")
def eliminar_casa(
    casa_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    casa = obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    db.delete(casa)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível eliminar a casa.",
        )

    return {"mensagem": "Casa eliminada com sucesso."}


# ============================================================
# DIVISÕES
# ============================================================

@router.post(
    "/casas/{casa_id}/divisoes",
    status_code=status.HTTP_201_CREATED,
)
def criar_divisao(
    casa_id: int,
    dados: CriarDivisao,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    nome = dados.nome.strip()

    existente = (
        db.query(DivisaoCasa)
        .filter(
            DivisaoCasa.casa_id == casa_id,
            DivisaoCasa.nome.ilike(nome),
        )
        .first()
    )

    if existente:
        raise HTTPException(
            status_code=409,
            detail="Já existe uma divisão com esse nome.",
        )

    divisao = DivisaoCasa(
        casa_id=casa_id,
        nome=nome,
        descricao=dados.descricao,
        icone=dados.icone,
    )

    db.add(divisao)

    try:
        db.commit()
        db.refresh(divisao)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível criar a divisão.",
        )

    return {
        "mensagem": "Divisão criada com sucesso.",
        "divisao": divisao_para_dict(divisao),
    }


@router.get("/casas/{casa_id}/divisoes")
def listar_divisoes(
    casa_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    divisoes = (
        db.query(DivisaoCasa)
        .filter(DivisaoCasa.casa_id == casa_id)
        .order_by(DivisaoCasa.nome.asc())
        .all()
    )

    return {
        "total": len(divisoes),
        "divisoes": [
            divisao_para_dict(divisao)
            for divisao in divisoes
        ],
    }


@router.delete("/casas/{casa_id}/divisoes/{divisao_id}")
def eliminar_divisao(
    casa_id: int,
    divisao_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    divisao = (
        db.query(DivisaoCasa)
        .filter(
            DivisaoCasa.id == divisao_id,
            DivisaoCasa.casa_id == casa_id,
        )
        .first()
    )

    if divisao is None:
        raise HTTPException(
            status_code=404,
            detail="Divisão não encontrada.",
        )

    db.delete(divisao)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível eliminar a divisão.",
        )

    return {"mensagem": "Divisão eliminada com sucesso."}


# ============================================================
# DISPOSITIVOS
# ============================================================

@router.post(
    "/casas/{casa_id}/dispositivos",
    status_code=status.HTTP_201_CREATED,
)
def adicionar_dispositivo(
    casa_id: int,
    dados: CriarDispositivo,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    if dados.divisao_id is not None:
        divisao = (
            db.query(DivisaoCasa)
            .filter(
                DivisaoCasa.id == dados.divisao_id,
                DivisaoCasa.casa_id == casa_id,
            )
            .first()
        )

        if divisao is None:
            raise HTTPException(
                status_code=404,
                detail="A divisão indicada não pertence a esta casa.",
            )

    identificador = (
        dados.identificador_integracao.strip()
        if dados.identificador_integracao
        else None
    )

    if identificador:
        existente = (
            db.query(DispositivoInteligente)
            .filter(
                DispositivoInteligente.casa_id == casa_id,
                DispositivoInteligente.identificador_integracao
                == identificador,
            )
            .first()
        )

        if existente:
            raise HTTPException(
                status_code=409,
                detail="Este identificador já está registado nesta casa.",
            )

    dispositivo = DispositivoInteligente(
        casa_id=casa_id,
        divisao_id=dados.divisao_id,
        nome=dados.nome.strip(),
        tipo=dados.tipo.strip().lower(),
        marca=dados.marca,
        modelo=dados.modelo,
        integracao=dados.integracao,
        identificador_integracao=identificador,
        entidade_externa=dados.entidade_externa,
        capacidades=dados.capacidades,
        estado_conhecido={},
        online=None,
        ativo=True,
    )

    db.add(dispositivo)

    try:
        db.commit()
        db.refresh(dispositivo)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível registar o dispositivo.",
        )

    return {
        "mensagem": "Dispositivo registado com sucesso.",
        "dispositivo": dispositivo_para_dict(dispositivo),
    }


@router.get("/casas/{casa_id}/dispositivos")
def listar_dispositivos(
    casa_id: int,
    divisao_id: int | None = None,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    consulta = (
        db.query(DispositivoInteligente)
        .filter(
            DispositivoInteligente.casa_id == casa_id,
            DispositivoInteligente.ativo.is_(True),
        )
    )

    if divisao_id is not None:
        consulta = consulta.filter(
            DispositivoInteligente.divisao_id == divisao_id
        )

    dispositivos = consulta.order_by(
        DispositivoInteligente.nome.asc()
    ).all()

    return {
        "total": len(dispositivos),
        "dispositivos": [
            dispositivo_para_dict(dispositivo)
            for dispositivo in dispositivos
        ],
    }


@router.patch("/casas/{casa_id}/dispositivos/{dispositivo_id}/divisao")
def mover_dispositivo(
    casa_id: int,
    dispositivo_id: int,
    divisao_id: int | None,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    dispositivo = obter_dispositivo_da_casa(
        db,
        casa_id,
        dispositivo_id,
    )

    if divisao_id is not None:
        divisao = (
            db.query(DivisaoCasa)
            .filter(
                DivisaoCasa.id == divisao_id,
                DivisaoCasa.casa_id == casa_id,
            )
            .first()
        )

        if divisao is None:
            raise HTTPException(
                status_code=404,
                detail="Divisão não encontrada nesta casa.",
            )

    dispositivo.divisao_id = divisao_id

    try:
        db.commit()
        db.refresh(dispositivo)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível mover o dispositivo.",
        )

    return {
        "mensagem": "Divisão do dispositivo atualizada.",
        "dispositivo": dispositivo_para_dict(dispositivo),
    }


@router.delete("/casas/{casa_id}/dispositivos/{dispositivo_id}")
def desativar_dispositivo(
    casa_id: int,
    dispositivo_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    dispositivo = obter_dispositivo_da_casa(
        db,
        casa_id,
        dispositivo_id,
    )

    # Mantém o histórico e o registo do aparelho.
    dispositivo.ativo = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível desativar o dispositivo.",
        )

    return {"mensagem": "Dispositivo desativado."}


# ============================================================
# INTEGRAÇÃO COM HOME ASSISTANT
# ============================================================

def executar_home_assistant(
    entidade: str,
    comando: str,
    parametros: dict,
) -> dict:

    base_url = os.getenv("HOME_ASSISTANT_URL", "").rstrip("/")
    token = os.getenv("HOME_ASSISTANT_TOKEN", "")

    if not base_url or not token:
        raise HTTPException(
            status_code=503,
            detail=(
                "A integração com Home Assistant não está configurada. "
                "O dispositivo foi registado, mas não recebeu nenhum comando."
            ),
        )

    if "." not in entidade:
        raise HTTPException(
            status_code=400,
            detail="A entidade externa do dispositivo é inválida.",
        )

    dominio, nome_entidade = entidade.split(".", 1)

    if not nome_entidade:
        raise HTTPException(
            status_code=400,
            detail="A entidade externa do dispositivo é inválida.",
        )

    servicos_permitidos = {
        "light": {
            "ligar": ("turn_on", {}),
            "desligar": ("turn_off", {}),
            "alternar": ("toggle", {}),
            "definir_brilho": ("turn_on", {"brightness_pct": "percentagem"}),
        },
        "switch": {
            "ligar": ("turn_on", {}),
            "desligar": ("turn_off", {}),
            "alternar": ("toggle", {}),
        },
        "fan": {
            "ligar": ("turn_on", {}),
            "desligar": ("turn_off", {}),
            "alternar": ("toggle", {}),
        },
        "climate": {
            "ligar": ("turn_on", {}),
            "desligar": ("turn_off", {}),
            "definir_temperatura": (
                "set_temperature",
                {"temperature": "temperatura"},
            ),
        },
        "media_player": {
            "ligar": ("turn_on", {}),
            "desligar": ("turn_off", {}),
            "alternar": ("toggle", {}),
            "pausar": ("media_pause", {}),
            "retomar": ("media_play", {}),
            "parar": ("media_stop", {}),
            "definir_volume": (
                "volume_set",
                {"volume_level": "volume"},
            ),
        },
    }

    if dominio not in servicos_permitidos:
        raise HTTPException(
            status_code=400,
            detail="Este tipo de dispositivo não suporta comandos nesta integração.",
        )

    definicao = servicos_permitidos[dominio].get(comando)

    if definicao is None:
        raise HTTPException(
            status_code=400,
            detail="Este comando não é compatível com o dispositivo.",
        )

    servico, mapeamento = definicao

    dados_servico = {
        "entity_id": entidade,
    }

    for campo, origem in mapeamento.items():
        if origem not in parametros:
            raise HTTPException(
                status_code=422,
                detail=f"Falta o parâmetro obrigatório: {origem}.",
            )

        valor = parametros[origem]

        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise HTTPException(
                status_code=422,
                detail=f"O parâmetro {origem} deve ser numérico.",
            )

        if campo == "brightness_pct" and not 1 <= valor <= 100:
            raise HTTPException(
                status_code=422,
                detail="A percentagem de brilho deve estar entre 1 e 100.",
            )

        if campo == "temperature" and not -50 <= valor <= 100:
            raise HTTPException(
                status_code=422,
                detail="A temperatura está fora do intervalo permitido.",
            )

        if campo == "volume_level" and not 0 <= valor <= 1:
            raise HTTPException(
                status_code=422,
                detail="O volume deve estar entre 0 e 1.",
            )

        dados_servico[campo] = valor

    url = f"{base_url}/api/services/{dominio}/{servico}"

    pedido = urllib.request.Request(
        url,
        data=json.dumps(dados_servico).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(pedido, timeout=10) as resposta:
            return {
                "sucesso": resposta.status in (200, 201),
                "resposta": resposta.read().decode("utf-8"),
            }

    except urllib.error.HTTPError as erro:
        raise HTTPException(
            status_code=502,
            detail=f"O Home Assistant rejeitou o comando (HTTP {erro.code}).",
        )

    except (urllib.error.URLError, TimeoutError):
        raise HTTPException(
            status_code=502,
            detail="Não foi possível contactar o Home Assistant.",
        )


# ============================================================
# EXECUTAR COMANDOS
# ============================================================

@router.post(
    "/casas/{casa_id}/dispositivos/{dispositivo_id}/comando"
)
def comandar_dispositivo(
    casa_id: int,
    dispositivo_id: int,
    dados: ComandoDispositivo,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)
    obter_casa_do_utilizador(db, casa_id, utilizador.id)
    dispositivo = obter_dispositivo_da_casa(db, casa_id, dispositivo_id)

    historico = HistoricoCasa(
        casa_id=casa_id,
        dispositivo_id=dispositivo.id,
        utilizador_id=utilizador.id,
        origem="manual",
        comando=dados.comando,
        parametros=dados.parametros,
        estado_execucao="pendente",
    )
    db.add(historico)

    try:
        db.flush()
        estado = dict(dispositivo.estado_conhecido or {})

        if dispositivo.integracao == "home_assistant":
            if not dispositivo.entidade_externa:
                historico.estado_execucao = "erro"
                historico.resultado = "Falta a entidade externa do dispositivo."
                db.commit()
                raise HTTPException(status_code=422, detail="Configura a entidade externa do dispositivo.")
            resultado = executar_home_assistant(
                dispositivo.entidade_externa, dados.comando, dados.parametros
            )
            if not resultado.get("sucesso"):
                raise HTTPException(status_code=502, detail="O controlador externo não confirmou o comando.")
            mensagem = "Comando enviado ao controlador externo."
            historico.resultado = mensagem
        else:
            # Controlador interno: mantém o estado lógico do dispositivo na SMART BOOK.
            # Não afirma controlar fisicamente um aparelho sem uma integração real.
            mensagem = "Estado interno atualizado. Nenhum comando físico foi enviado."
            historico.resultado = mensagem

        agora = datetime.now(timezone.utc).isoformat()
        estado["ultimo_comando"] = dados.comando
        estado["ultima_execucao"] = agora
        if dados.comando == "ligar":
            estado["ligado"] = True
        elif dados.comando == "desligar":
            estado["ligado"] = False
        elif dados.comando == "alternar":
            estado["ligado"] = not bool(estado.get("ligado", False))
        elif dados.comando == "definir_temperatura":
            valor = dados.parametros.get("temperatura")
            if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not -50 <= valor <= 100:
                raise HTTPException(status_code=422, detail="A temperatura deve ser um número entre -50 e 100.")
            estado["temperatura"] = valor
        elif dados.comando == "definir_brilho":
            valor = dados.parametros.get("percentagem")
            if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not 1 <= valor <= 100:
                raise HTTPException(status_code=422, detail="A percentagem de brilho deve estar entre 1 e 100.")
            estado["brilho"] = valor
        elif dados.comando == "definir_volume":
            valor = dados.parametros.get("volume")
            if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not 0 <= valor <= 1:
                raise HTTPException(status_code=422, detail="O volume deve estar entre 0 e 1.")
            estado["volume"] = valor
        elif dados.comando in ("pausar", "retomar", "parar"):
            estado["reproducao"] = {"pausar": "pausada", "retomar": "a reproduzir", "parar": "parada"}[dados.comando]

        dispositivo.estado_conhecido = estado
        if dispositivo.integracao == "home_assistant":
            dispositivo.online = True
        historico.estado_execucao = "concluido"
        db.commit()
        db.refresh(dispositivo)
        db.refresh(historico)
        return {
            "sucesso": True,
            "mensagem": mensagem,
            "historico_id": historico.id,
            "dispositivo": dispositivo_para_dict(dispositivo),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao processar o comando.")


# ============================================================
# AUTOMAÇÕES INTERNAS
# configuracao aceita: {"acoes": [{"dispositivo_id": 1, "comando": "ligar", "parametros": {}}]}
# ============================================================

@router.post("/casas/{casa_id}/automacoes", status_code=status.HTTP_201_CREATED)
def criar_automacao(
    casa_id: int,
    dados: CriarAutomacao,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)
    obter_casa_do_utilizador(db, casa_id, utilizador.id)
    automacao = AutomacaoCasa(
        casa_id=casa_id,
        nome=dados.nome.strip(),
        descricao=dados.descricao,
        tipo_ativacao=dados.tipo_ativacao,
        configuracao=dados.configuracao,
        ativa=dados.ativa,
        criada_por_ia=False,
    )
    db.add(automacao)
    try:
        db.commit()
        db.refresh(automacao)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Não foi possível criar a automação.")
    return {"mensagem": "Automação criada.", "automacao": automacao_para_dict(automacao)}


@router.get("/casas/{casa_id}/automacoes")
def listar_automacoes(
    casa_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)
    obter_casa_do_utilizador(db, casa_id, utilizador.id)
    itens = db.query(AutomacaoCasa).filter(AutomacaoCasa.casa_id == casa_id).order_by(AutomacaoCasa.id.desc()).all()
    return {"total": len(itens), "automacoes": [automacao_para_dict(item) for item in itens]}


@router.patch("/casas/{casa_id}/automacoes/{automacao_id}")
def atualizar_automacao(
    casa_id: int,
    automacao_id: int,
    dados: AtualizarAutomacao,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)
    obter_casa_do_utilizador(db, casa_id, utilizador.id)
    automacao = db.query(AutomacaoCasa).filter(AutomacaoCasa.id == automacao_id, AutomacaoCasa.casa_id == casa_id).first()
    if automacao is None:
        raise HTTPException(status_code=404, detail="Automação não encontrada.")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        if campo == "nome" and valor is not None:
            valor = valor.strip()
        setattr(automacao, campo, valor)
    try:
        db.commit()
        db.refresh(automacao)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Não foi possível atualizar a automação.")
    return {"mensagem": "Automação atualizada.", "automacao": automacao_para_dict(automacao)}


@router.delete("/casas/{casa_id}/automacoes/{automacao_id}")
def eliminar_automacao(
    casa_id: int,
    automacao_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)
    obter_casa_do_utilizador(db, casa_id, utilizador.id)
    automacao = db.query(AutomacaoCasa).filter(AutomacaoCasa.id == automacao_id, AutomacaoCasa.casa_id == casa_id).first()
    if automacao is None:
        raise HTTPException(status_code=404, detail="Automação não encontrada.")
    db.delete(automacao)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Não foi possível eliminar a automação.")
    return {"mensagem": "Automação eliminada."}


@router.post("/casas/{casa_id}/automacoes/{automacao_id}/executar")
def executar_automacao_interna(
    casa_id: int,
    automacao_id: int,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)
    obter_casa_do_utilizador(db, casa_id, utilizador.id)
    automacao = db.query(AutomacaoCasa).filter(AutomacaoCasa.id == automacao_id, AutomacaoCasa.casa_id == casa_id).first()
    if automacao is None:
        raise HTTPException(status_code=404, detail="Automação não encontrada.")
    acoes = (automacao.configuracao or {}).get("acoes", [])
    if not isinstance(acoes, list) or not acoes:
        raise HTTPException(status_code=422, detail="A automação precisa de uma lista 'acoes' com dispositivo_id e comando.")
    resultados = []
    for acao in acoes:
        if not isinstance(acao, dict) or not acao.get("dispositivo_id") or acao.get("comando") not in {"ligar", "desligar", "alternar", "definir_temperatura", "definir_brilho", "definir_volume", "pausar", "retomar", "parar"}:
            raise HTTPException(status_code=422, detail="Cada ação precisa de dispositivo_id e de um comando válido.")
        dispositivo = obter_dispositivo_da_casa(db, casa_id, int(acao["dispositivo_id"]))
        comando = acao["comando"]
        parametros = acao.get("parametros") or {}
        estado = dict(dispositivo.estado_conhecido or {})
        if dispositivo.integracao == "home_assistant":
            if not dispositivo.entidade_externa:
                raise HTTPException(status_code=422, detail=f"Falta a entidade externa do dispositivo {dispositivo.nome}.")
            executar_home_assistant(dispositivo.entidade_externa, comando, parametros)
            dispositivo.online = True
        if comando == "ligar": state_value = True
        elif comando == "desligar": state_value = False
        elif comando == "alternar": state_value = not bool(estado.get("ligado", False))
        else: state_value = None
        if state_value is not None: estado["ligado"] = state_value
        if comando == "definir_temperatura": estado["temperatura"] = parametros.get("temperatura")
        if comando == "definir_brilho": estado["brilho"] = parametros.get("percentagem")
        if comando == "definir_volume": estado["volume"] = parametros.get("volume")
        if comando in ("pausar", "retomar", "parar"):
            estado["reproducao"] = {"pausar": "pausada", "retomar": "a reproduzir", "parar": "parada"}[comando]
        estado["ultimo_comando"] = comando
        estado["ultima_execucao"] = datetime.now(timezone.utc).isoformat()
        dispositivo.estado_conhecido = estado
        db.add(HistoricoCasa(casa_id=casa_id, dispositivo_id=dispositivo.id, utilizador_id=utilizador.id, origem="automacao", comando=comando, parametros=parametros, resultado="Ação da automação processada; em modo manual, apenas o estado interno foi atualizado.", estado_execucao="concluido"))
        resultados.append({"dispositivo_id": dispositivo.id, "comando": comando, "sucesso": True})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Falha ao guardar a execução da automação.")
    return {"sucesso": True, "mensagem": "Automação executada.", "resultados": resultados}


# ============================================================
# HISTÓRICO
# ============================================================

@router.get("/casas/{casa_id}/historico")
def consultar_historico(
    casa_id: int,
    limite: int = 50,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):
    utilizador = obter_utilizador(token, db)

    obter_casa_do_utilizador(
        db,
        casa_id,
        utilizador.id,
    )

    limite = max(1, min(limite, 200))

    registos = (
        db.query(HistoricoCasa)
        .filter(HistoricoCasa.casa_id == casa_id)
        .order_by(HistoricoCasa.data_criacao.desc())
        .limit(limite)
        .all()
    )

    return {
        "total": len(registos),
        "historico": [
            {
                "id": registo.id,
                "casa_id": registo.casa_id,
                "dispositivo_id": registo.dispositivo_id,
                "utilizador_id": registo.utilizador_id,
                "origem": registo.origem,
                "comando": registo.comando,
                "parametros": registo.parametros,
                "resultado": registo.resultado,
                "estado_execucao": registo.estado_execucao,
                "data_criacao": registo.data_criacao,
            }
            for registo in registos
        ],
    }
