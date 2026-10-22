
import uuid
from pathlib import Path

from app.database.connection import obter_sessao
from app.models.group import Grupo, MensagemGrupo, ParticipanteGrupo
from app.models.user import User
from app.security.auth import obter_token, validar_token_acesso
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/grupos",
    tags=["Grupos"],
)


# ============================================================
# AUTENTICAÇÃO E UTILIZADOR ATUAL
# ============================================================

def obter_utilizador_atual(
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
) -> User:
    dados = validar_token_acesso(token)
    utilizador_id = int(dados["sub"])

    utilizador = db.get(User, utilizador_id)

    if not utilizador or not utilizador.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizador inválido ou conta desativada.",
        )

    return utilizador


# ============================================================
# ARMAZENAMENTO DE IMAGENS DOS GRUPOS
# ============================================================

PASTA_IMAGENS_GRUPOS = (
    Path(__file__).resolve().parents[3]
    / "media"
    / "grupos"
)

PASTA_IMAGENS_GRUPOS.mkdir(
    parents=True,
    exist_ok=True,
)

TIPOS_IMAGEM_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024


# ============================================================
# ATUALIZAR FOTOGRAFIA OU CAPA DO GRUPO
# POST /api/grupos/{grupo_id}/imagem
# ============================================================

@router.post("/{grupo_id}/imagem")
async def atualizar_imagem_grupo(
    grupo_id: int,
    tipo: str = "perfil",
    ficheiro: UploadFile = File(...),
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    grupo = verificar_grupo(db, grupo_id)

    if grupo.criador_id != atual.id:
        raise HTTPException(
            status_code=403,
            detail="Só o criador pode alterar as imagens do grupo.",
        )

    if tipo not in {"perfil", "capa"}:
        raise HTTPException(
            status_code=400,
            detail="Tipo de imagem inválido.",
        )

    extensao = TIPOS_IMAGEM_PERMITIDOS.get(
        ficheiro.content_type or ""
    )

    if not extensao:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Usa JPG, PNG, WEBP ou GIF.",
        )

    conteudo = await ficheiro.read(
        TAMANHO_MAXIMO_IMAGEM + 1
    )

    if not conteudo:
        raise HTTPException(
            status_code=400,
            detail="O ficheiro está vazio.",
        )

    if len(conteudo) > TAMANHO_MAXIMO_IMAGEM:
        raise HTTPException(
            status_code=413,
            detail="A imagem não pode ultrapassar 5 MB.",
        )

    # Verificação básica da assinatura do ficheiro.
    assinaturas = {
        ".jpg": (b"\xff\xd8\xff",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".webp": (b"RIFF",),
        ".gif": (b"GIF87a", b"GIF89a"),
    }

    assinaturas_validas = assinaturas[extensao]

    if not any(
        conteudo.startswith(assinatura)
        for assinatura in assinaturas_validas
    ):
        raise HTTPException(
            status_code=400,
            detail="O conteúdo do ficheiro não corresponde a uma imagem válida.",
        )

    nome_ficheiro = f"{uuid.uuid4().hex}{extensao}"

    destino = PASTA_IMAGENS_GRUPOS / nome_ficheiro

    destino.write_bytes(conteudo)

    caminho_publico = f"/media/grupos/{nome_ficheiro}"

    if tipo == "perfil":
        grupo.imagem_url = caminho_publico
    else:
        grupo.capa_url = caminho_publico

    try:
        db.commit()
        db.refresh(grupo)
    except Exception:
        db.rollback()

        destino.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Não foi possível guardar a imagem do grupo.",
        )

    return {
        "mensagem": "Imagem atualizada com sucesso.",
        "id": grupo.id,
        "imagem_url": grupo.imagem_url,
        "capa_url": grupo.capa_url,
    }

# ============================================================
# MODELOS DOS PEDIDOS
# ============================================================

class CriarGrupoPedido(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    descricao: str | None = Field(default=None, max_length=2000)
    participantes: list[int] = Field(default_factory=list)


class EnviarMensagemPedido(BaseModel):
    conteudo: str = Field(min_length=1, max_length=10000)


class AdicionarParticipantePedido(BaseModel):
    utilizador_id: int


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def verificar_participante(
    db: Session,
    grupo_id: int,
    utilizador_id: int,
) -> bool:
    participante = db.scalar(
        select(ParticipanteGrupo).where(
            ParticipanteGrupo.grupo_id == grupo_id,
            ParticipanteGrupo.utilizador_id == utilizador_id,
        )
    )

    return participante is not None


def verificar_grupo(
    db: Session,
    grupo_id: int,
) -> Grupo:
    grupo = db.get(Grupo, grupo_id)

    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo não encontrado.",
        )

    return grupo


def dados_utilizador(utilizador: User) -> dict:
    return {
        "id": utilizador.id,
        "nome_completo": utilizador.nome_completo,
        "username": utilizador.username,
    }


def dados_grupo(
    db: Session,
    grupo: Grupo,
    utilizador_id: int,
) -> dict:
    participantes = db.scalars(
        select(ParticipanteGrupo).where(
            ParticipanteGrupo.grupo_id == grupo.id
        )
    ).all()

    criador = db.get(User, grupo.criador_id)

    return {
        "id": grupo.id,
        "nome": grupo.nome,
        "descricao": grupo.descricao,
        "criador_id": grupo.criador_id,
        "imagem_url": grupo.imagem_url,
         "capa_url": grupo.capa_url,
        "criador": (
            dados_utilizador(criador)
            if criador else None
        ),
        "total_participantes": len(participantes),
        "sou_criador": grupo.criador_id == utilizador_id,
        "data_criacao": grupo.data_criacao.isoformat(),
    }


# ============================================================
# LISTAR UTILIZADORES PARA ADICIONAR AO GRUPO
# GET /api/grupos/utilizadores
# ============================================================

@router.get("/utilizadores")
def listar_utilizadores(
    pesquisa: str | None = None,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    consulta = select(User).where(
        User.ativo.is_(True),
        User.id != atual.id,
    )

    if pesquisa and pesquisa.strip():
        termo = f"%{pesquisa.strip()}%"

        consulta = consulta.where(
            (User.nome_completo.ilike(termo))
            | (User.username.ilike(termo))
        )

    utilizadores = db.scalars(
        consulta.order_by(User.nome_completo).limit(100)
    ).all()

    return [
        dados_utilizador(utilizador)
        for utilizador in utilizadores
    ]


# ============================================================
# CRIAR GRUPO
# POST /api/grupos
# ============================================================

@router.post("", status_code=status.HTTP_201_CREATED)
def criar_grupo(
    dados: CriarGrupoPedido,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    nome = dados.nome.strip()

    if not nome:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O nome do grupo é obrigatório.",
        )

    grupo = Grupo(
        nome=nome,
        descricao=(
            dados.descricao.strip()
            if dados.descricao and dados.descricao.strip()
            else None
        ),
        criador_id=atual.id,
    )

    db.add(grupo)
    db.flush()

    # O criador também é participante do grupo.
    ids_participantes = set(dados.participantes)
    ids_participantes.add(atual.id)

    utilizadores_validos = db.scalars(
        select(User).where(
            User.id.in_(ids_participantes),
            User.ativo.is_(True),
        )
    ).all()

    ids_validos = {
        utilizador.id
        for utilizador in utilizadores_validos
    }

    if atual.id not in ids_validos:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível adicionar o criador ao grupo.",
        )

    for utilizador_id in ids_validos:
        db.add(
            ParticipanteGrupo(
                grupo_id=grupo.id,
                utilizador_id=utilizador_id,
            )
        )

    db.commit()
    db.refresh(grupo)

    return dados_grupo(db, grupo, atual.id)


# ============================================================
# LISTAR GRUPOS DO UTILIZADOR
# GET /api/grupos
# ============================================================

@router.get("")
def listar_grupos(
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    participacoes = db.scalars(
        select(ParticipanteGrupo).where(
            ParticipanteGrupo.utilizador_id == atual.id
        )
    ).all()

    ids_grupos = [
        participacao.grupo_id
        for participacao in participacoes
    ]

    if not ids_grupos:
        return []

    grupos = db.scalars(
        select(Grupo)
        .where(Grupo.id.in_(ids_grupos))
        .order_by(Grupo.data_criacao.desc())
    ).all()

    return [
        dados_grupo(db, grupo, atual.id)
        for grupo in grupos
    ]


# ============================================================
# DETALHES DE UM GRUPO
# GET /api/grupos/{grupo_id}
# ============================================================

@router.get("/{grupo_id}")
def obter_grupo(
    grupo_id: int,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    grupo = verificar_grupo(db, grupo_id)

    if not verificar_participante(db, grupo_id, atual.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não és participante deste grupo.",
        )

    return dados_grupo(db, grupo, atual.id)


# ============================================================
# LISTAR PARTICIPANTES
# GET /api/grupos/{grupo_id}/participantes
# ============================================================

@router.get("/{grupo_id}/participantes")
def listar_participantes(
    grupo_id: int,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    verificar_grupo(db, grupo_id)

    if not verificar_participante(db, grupo_id, atual.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não és participante deste grupo.",
        )

    participacoes = db.scalars(
        select(ParticipanteGrupo).where(
            ParticipanteGrupo.grupo_id == grupo_id
        )
    ).all()

    resultado = []

    for participacao in participacoes:
        utilizador = db.get(
            User,
            participacao.utilizador_id,
        )

        if utilizador:
            resultado.append(
                dados_utilizador(utilizador)
            )

    return resultado


# ============================================================
# ADICIONAR PARTICIPANTE
# POST /api/grupos/{grupo_id}/participantes
# ============================================================

@router.post(
    "/{grupo_id}/participantes",
    status_code=status.HTTP_201_CREATED,
)
def adicionar_participante(
    grupo_id: int,
    dados: AdicionarParticipantePedido,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    grupo = verificar_grupo(db, grupo_id)

    if grupo.criador_id != atual.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só o criador pode adicionar participantes.",
        )

    utilizador = db.get(User, dados.utilizador_id)

    if not utilizador or not utilizador.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado ou desativado.",
        )

    if verificar_participante(
        db,
        grupo_id,
        dados.utilizador_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este utilizador já pertence ao grupo.",
        )

    participante = ParticipanteGrupo(
        grupo_id=grupo_id,
        utilizador_id=dados.utilizador_id,
    )

    db.add(participante)
    db.commit()

    return {
        "mensagem": "Participante adicionado com sucesso.",
        "participante": dados_utilizador(utilizador),
    }


# ============================================================
# REMOVER PARTICIPANTE
# DELETE /api/grupos/{grupo_id}/participantes/{utilizador_id}
# ============================================================

@router.delete(
    "/{grupo_id}/participantes/{utilizador_id}"
)
def remover_participante(
    grupo_id: int,
    utilizador_id: int,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    grupo = verificar_grupo(db, grupo_id)

    if grupo.criador_id != atual.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só o criador pode remover participantes.",
        )

    if utilizador_id == grupo.criador_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O criador não pode ser removido do próprio grupo.",
        )

    participante = db.scalar(
        select(ParticipanteGrupo).where(
            ParticipanteGrupo.grupo_id == grupo_id,
            ParticipanteGrupo.utilizador_id == utilizador_id,
        )
    )

    if not participante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este utilizador não pertence ao grupo.",
        )

    db.delete(participante)
    db.commit()

    return {
        "mensagem": "Participante removido com sucesso."
    }


# ============================================================
# LISTAR MENSAGENS
# GET /api/grupos/{grupo_id}/mensagens
# ============================================================

@router.get("/{grupo_id}/mensagens")
def listar_mensagens(
    grupo_id: int,
    limite: int = 100,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    verificar_grupo(db, grupo_id)

    if not verificar_participante(db, grupo_id, atual.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não és participante deste grupo.",
        )

    limite = max(1, min(limite, 200))

    mensagens = db.scalars(
        select(MensagemGrupo)
        .where(MensagemGrupo.grupo_id == grupo_id)
        .order_by(MensagemGrupo.data_criacao.desc())
        .limit(limite)
    ).all()

    resultado = []

    for mensagem in reversed(mensagens):
        remetente = db.get(
            User,
            mensagem.remetente_id,
        )

        resultado.append({
            "id": mensagem.id,
            "grupo_id": mensagem.grupo_id,
            "remetente_id": mensagem.remetente_id,
            "remetente": (
                dados_utilizador(remetente)
                if remetente else None
            ),
            "conteudo": mensagem.conteudo,
            "data_criacao": mensagem.data_criacao.isoformat(),
            "minha": mensagem.remetente_id == atual.id,
        })

    return resultado


# ============================================================
# ENVIAR MENSAGEM
# POST /api/grupos/{grupo_id}/mensagens
# ============================================================

@router.post(
    "/{grupo_id}/mensagens",
    status_code=status.HTTP_201_CREATED,
)
def enviar_mensagem(
    grupo_id: int,
    dados: EnviarMensagemPedido,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    verificar_grupo(db, grupo_id)

    if not verificar_participante(db, grupo_id, atual.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não és participante deste grupo.",
        )

    conteudo = dados.conteudo.strip()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A mensagem não pode estar vazia.",
        )

    mensagem = MensagemGrupo(
        grupo_id=grupo_id,
        remetente_id=atual.id,
        conteudo=conteudo,
    )

    db.add(mensagem)
    db.commit()
    db.refresh(mensagem)

    return {
        "id": mensagem.id,
        "grupo_id": mensagem.grupo_id,
        "remetente_id": mensagem.remetente_id,
        "remetente": dados_utilizador(atual),
        "conteudo": mensagem.conteudo,
        "data_criacao": mensagem.data_criacao.isoformat(),
        "minha": True,
    }


# ============================================================
# ELIMINAR GRUPO
# DELETE /api/grupos/{grupo_id}
# ============================================================

@router.delete("/{grupo_id}")
def eliminar_grupo(
    grupo_id: int,
    atual: User = Depends(obter_utilizador_atual),
    db: Session = Depends(obter_sessao),
):
    grupo = verificar_grupo(db, grupo_id)

    if grupo.criador_id != atual.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só o criador pode eliminar o grupo.",
        )

    db.delete(grupo)
    db.commit()

    return {
        "mensagem": "Grupo eliminado com sucesso."
    }
# ============================================================
# CARREGAR FOTO DE PERFIL OU CAPA DO GRUPO
# ============================================================

@router.post("/{grupo_id}/imagem")
async def atualizar_imagem_grupo(
    grupo_id: int,
    tipo: str = Form(...),
    ficheiro: UploadFile = File(...),
    db: Session = Depends(obter_sessao),
    utilizador: User = Depends(obter_utilizador_atual),
):
    if tipo not in ("perfil", "capa"):
        raise HTTPException(
            status_code=400,
            detail="Tipo de imagem inválido.",
        )

    grupo = db.scalar(
        select(Grupo).where(Grupo.id == grupo_id)
    )

    if not grupo:
        raise HTTPException(
            status_code=404,
            detail="Grupo não encontrado.",
        )

    if grupo.criador_id != utilizador.id:
        raise HTTPException(
            status_code=403,
            detail="Só o criador do grupo pode alterar as imagens.",
        )

    extensoes = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }

    extensao = extensoes.get(ficheiro.content_type or "")

    if not extensao:
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Usa JPG, PNG, WebP ou GIF.",
        )

    conteudo = await ficheiro.read(5 * 1024 * 1024 + 1)

    if not conteudo:
        raise HTTPException(
            status_code=400,
            detail="O ficheiro está vazio.",
        )

    if len(conteudo) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="A imagem não pode ultrapassar 5 MB.",
        )

    # SMART_BOOK/media/grupos
    pasta = Path(__file__).resolve().parents[3] / "media" / "grupos"
    pasta.mkdir(parents=True, exist_ok=True)

    nome_ficheiro = (
        f"grupo_{grupo_id}_{tipo}_{uuid.uuid4().hex}{extensao}"
    )

    caminho = pasta / nome_ficheiro

    try:
        caminho.write_bytes(conteudo)

        url = f"/media/grupos/{nome_ficheiro}"

        if tipo == "perfil":
            grupo.imagem_url = url
        else:
            grupo.capa_url = url

        db.commit()
        db.refresh(grupo)

    except Exception:
        db.rollback()

        if caminho.exists():
            caminho.unlink()

        raise HTTPException(
            status_code=500,
            detail="Não foi possível guardar a imagem.",
        )

    return {
        "mensagem": "Imagem atualizada com sucesso.",
        "imagem_url": grupo.imagem_url,
        "capa_url": grupo.capa_url,
    }