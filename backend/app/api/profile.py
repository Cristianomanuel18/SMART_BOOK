from pathlib import Path
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session

from app.database.connection import obter_sessao
from app.models import Profile, User
from app.schemas.profile import (
    AtualizarPerfil,
    PerfilPublico,
)
from app.security.auth import (
    obter_token,
    validar_token_acesso,
)


router = APIRouter(
    prefix="/api/profile",
    tags=["Perfis"],
)


# =========================================================
# CONFIGURAÇÃO DAS IMAGENS
# =========================================================

RAIZ_PROJETO = Path(__file__).resolve().parents[3]

PASTA_IMAGENS_PERFIS = (
    RAIZ_PROJETO / "media" / "perfis"
)

PASTA_IMAGENS_PERFIS.mkdir(
    parents=True,
    exist_ok=True,
)

TIPOS_IMAGEM_PERMITIDOS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024


# =========================================================
# OBTER UTILIZADOR AUTENTICADO
# =========================================================

def obter_utilizador_autenticado(
    token: str,
    db: Session,
) -> User:

    try:
        payload = validar_token_acesso(token)
    except Exception:
        payload = None

    if not payload or not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida. Inicia sessão novamente.",
        )

    identificador = payload.get("sub")

    if identificador is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token não identifica um utilizador.",
        )

    try:
        utilizador_id = int(identificador)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificação de utilizador inválida.",
        )

    utilizador = (
        db.query(User)
        .filter(User.id == utilizador_id)
        .first()
    )

    if utilizador is None or not utilizador.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A conta não existe ou está desativada.",
        )

    return utilizador


# =========================================================
# OBTER OU CRIAR PERFIL
# =========================================================

def obter_ou_criar_perfil(
    db: Session,
    utilizador_id: int,
) -> Profile:

    perfil = (
        db.query(Profile)
        .filter(Profile.user_id == utilizador_id)
        .first()
    )

    if perfil is None:
        perfil = Profile(
            user_id=utilizador_id,
        )

        db.add(perfil)
        db.flush()

    return perfil


# =========================================================
# PREPARAR RESPOSTA PÚBLICA
# =========================================================

def preparar_perfil_publico(
    utilizador: User,
    perfil: Profile,
) -> dict:

    return {
        "id": utilizador.id,
        "nome_completo": utilizador.nome_completo,
        "username": utilizador.username,
        "foto_url": perfil.foto_url,
        "capa_url": perfil.capa_url,
        "biografia": perfil.biografia,
        "localizacao": perfil.localizacao,
        "data_registo": utilizador.data_registo,
        "data_atualizacao": perfil.data_atualizacao,
    }


# =========================================================
# MEU PERFIL
# GET /api/profile/me
# =========================================================

@router.get(
    "/me",
    response_model=PerfilPublico,
)
def meu_perfil(
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):

    utilizador = obter_utilizador_autenticado(
        token,
        db,
    )

    perfil = obter_ou_criar_perfil(
        db,
        utilizador.id,
    )

    db.commit()
    db.refresh(perfil)

    return preparar_perfil_publico(
        utilizador,
        perfil,
    )


# =========================================================
# ATUALIZAR FOTOGRAFIA DE PERFIL OU CAPA
# POST /api/profile/me/imagem
#
# tipo = perfil ou capa
# ficheiro = imagem selecionada no dispositivo
# =========================================================

@router.post("/me/imagem")
async def carregar_imagem_perfil(
    tipo: str = Form(...),
    ficheiro: UploadFile = File(...),
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):

    utilizador = obter_utilizador_autenticado(
        token,
        db,
    )

    if tipo not in ("perfil", "capa"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de imagem inválido. Escolhe perfil ou capa.",
        )

    if ficheiro.content_type not in TIPOS_IMAGEM_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Escolhe uma imagem JPG, PNG ou WebP.",
        )

    conteudo = await ficheiro.read()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O ficheiro selecionado está vazio.",
        )

    if len(conteudo) > TAMANHO_MAXIMO_IMAGEM:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A imagem não pode ultrapassar 5 MB.",
        )

    perfil = obter_ou_criar_perfil(
        db,
        utilizador.id,
    )

    extensao = TIPOS_IMAGEM_PERMITIDOS[
        ficheiro.content_type
    ]

    nome_ficheiro = (
        f"{utilizador.id}_{tipo}_{uuid.uuid4().hex}{extensao}"
    )

    caminho_ficheiro = (
        PASTA_IMAGENS_PERFIS / nome_ficheiro
    )

    try:
        with caminho_ficheiro.open("wb") as imagem:
            imagem.write(conteudo)

        endereco_imagem = (
            f"/media/perfis/{nome_ficheiro}"
        )

        if tipo == "perfil":
            perfil.foto_url = endereco_imagem
        else:
            perfil.capa_url = endereco_imagem

        db.commit()
        db.refresh(perfil)

    except Exception:
        db.rollback()

        # Se a gravação na base de dados falhar,
        # não deixa a imagem recém-carregada abandonada.
        try:
            caminho_ficheiro.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível guardar a imagem. Tenta novamente.",
        )

    finally:
        await ficheiro.close()

    return {
        "mensagem": (
            "Fotografia de perfil atualizada."
            if tipo == "perfil"
            else "Fotografia de capa atualizada."
        ),
        "foto_url": perfil.foto_url,
        "capa_url": perfil.capa_url,
        "perfil": preparar_perfil_publico(
            utilizador,
            perfil,
        ),
    }


# =========================================================
# ATUALIZAR OS OUTROS DADOS DO PERFIL
# PUT /api/profile/me
# =========================================================

@router.put(
    "/me",
    response_model=PerfilPublico,
)
def atualizar_meu_perfil(
    dados: AtualizarPerfil,
    token: str = Depends(obter_token),
    db: Session = Depends(obter_sessao),
):

    utilizador = obter_utilizador_autenticado(
        token,
        db,
    )

    perfil = obter_ou_criar_perfil(
        db,
        utilizador.id,
    )

    alteracoes = dados.model_dump(
        exclude_unset=True,
    )

    # As fotografias passam a ser carregadas através
    # do endpoint próprio, usando ficheiros do dispositivo.
    # Não aceitamos URLs de imagens neste endpoint.
    alteracoes.pop("foto_url", None)
    alteracoes.pop("capa_url", None)

    for campo, valor in alteracoes.items():
        setattr(
            perfil,
            campo,
            valor,
        )

    try:
        db.commit()
        db.refresh(perfil)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível atualizar o perfil.",
        )

    return preparar_perfil_publico(
        utilizador,
        perfil,
    )


# =========================================================
# PERFIL PÚBLICO DE OUTRO UTILIZADOR
# GET /api/profile/{username}
# =========================================================

@router.get(
    "/{username}",
    response_model=PerfilPublico,
)
def consultar_perfil_publico(
    username: str,
    db: Session = Depends(obter_sessao),
):

    utilizador = (
        db.query(User)
        .filter(
            User.username == username,
            User.ativo.is_(True),
        )
        .first()
    )

    if utilizador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este perfil não foi encontrado.",
        )

    perfil = (
        db.query(Profile)
        .filter(
            Profile.user_id == utilizador.id,
        )
        .first()
    )

    if perfil is None:
        perfil = Profile(
            user_id=utilizador.id,
        )

        db.add(perfil)
        db.commit()
        db.refresh(perfil)

    return preparar_perfil_publico(
        utilizador,
        perfil,
    )