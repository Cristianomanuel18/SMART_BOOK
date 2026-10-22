import uuid
from pathlib import Path

from app.database.connection import obter_sessao
from app.models import User, Video
from app.security.auth import obter_token, validar_token_acesso
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/videos",
    tags=["Vídeos"],
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

RAIZ_PROJETO = Path(__file__).resolve().parents[3]

PASTA_VIDEOS = RAIZ_PROJETO / "media" / "videos"

PASTA_VIDEOS.mkdir(
    parents=True,
    exist_ok=True,
)

TAMANHO_MAXIMO = 100 * 1024 * 1024  # 100 MB

FORMATOS_PERMITIDOS = {
    ".mp4": {"video/mp4"},
    ".webm": {"video/webm"},
    ".mov": {"video/quicktime"},
    ".mkv": {"video/x-matroska"},
}

CHUNK_SIZE = 1024 * 1024


# ============================================================
# AUTENTICAÇÃO
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
# FORMATAR VÍDEO
# ============================================================

def formatar_video(video: Video, autor: User):
    return {
        "id": video.id,
        "titulo": video.titulo,
        "descricao": video.descricao,
        "url_video": video.url_video,
        "tipo_mime": video.tipo_mime,
        "tamanho_bytes": video.tamanho_bytes,
        "data_criacao": video.data_criacao,
        "autor": {
            "id": autor.id,
            "nome_completo": autor.nome_completo,
            "username": autor.username,
        },
        "pode_apagar": False,
    }


# ============================================================
# PUBLICAR VÍDEO
# ============================================================

@router.post("")
async def publicar_video(
    titulo: str = Form(..., max_length=200),
    descricao: str = Form(default="", max_length=5000),
    ficheiro: UploadFile = File(...),
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    titulo = titulo.strip()

    if not titulo:
        raise HTTPException(
            status_code=400,
            detail="O título do vídeo é obrigatório.",
        )

    extensao = Path(ficheiro.filename or "").suffix.lower()

    if extensao not in FORMATOS_PERMITIDOS:
        raise HTTPException(
            status_code=415,
            detail="Formato não suportado. Utiliza MP4, WebM, MOV ou MKV.",
        )

    tipo_mime = (ficheiro.content_type or "").lower()

    if tipo_mime not in FORMATOS_PERMITIDOS[extensao]:
        raise HTTPException(
            status_code=415,
            detail="O formato declarado do vídeo não corresponde à extensão.",
        )

    nome_seguro = f"{uuid.uuid4().hex}{extensao}"
    caminho = PASTA_VIDEOS / nome_seguro

    tamanho = 0

    try:
        with caminho.open("xb") as destino:
            while True:
                bloco = await ficheiro.read(CHUNK_SIZE)

                if not bloco:
                    break

                tamanho += len(bloco)

                if tamanho > TAMANHO_MAXIMO:
                    raise HTTPException(
                        status_code=413,
                        detail="O vídeo ultrapassa o limite de 100 MB.",
                    )

                destino.write(bloco)

        if tamanho == 0:
            raise HTTPException(
                status_code=400,
                detail="O ficheiro de vídeo está vazio.",
            )

        video = Video(
            autor_id=atual.id,
            titulo=titulo,
            descricao=descricao.strip(),
            nome_ficheiro=nome_seguro,
            url_video=f"/media/videos/{nome_seguro}",
            tipo_mime=tipo_mime,
            tamanho_bytes=tamanho,
        )

        db.add(video)
        db.commit()
        db.refresh(video)

        resposta = formatar_video(video, atual)
        resposta["pode_apagar"] = True

        return {
            "mensagem": "Vídeo publicado com sucesso.",
            "video": resposta,
        }

    except HTTPException:
        db.rollback()

        if caminho.exists():
            caminho.unlink()

        raise

    except Exception:
        db.rollback()

        if caminho.exists():
            caminho.unlink()

        raise HTTPException(
            status_code=500,
            detail="Não foi possível guardar o vídeo.",
        )

    finally:
        await ficheiro.close()


# ============================================================
# LISTAR VÍDEOS
# ============================================================

@router.get("")
def listar_videos(
    limite: int = 30,
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    limite = max(1, min(limite, 100))

    videos = (
        db.query(Video)
        .join(User, Video.autor_id == User.id)
        .filter(User.ativo.is_(True))
        .order_by(
            Video.data_criacao.desc(),
            Video.id.desc(),
        )
        .limit(limite)
        .all()
    )

    resultado = []

    for video in videos:
        autor = db.query(User).filter(
            User.id == video.autor_id,
        ).first()

        if not autor:
            continue

        item = formatar_video(video, autor)
        item["pode_apagar"] = (
            video.autor_id == atual.id
            or atual.administrador
        )

        resultado.append(item)

    return {
        "total": len(resultado),
        "videos": resultado,
    }


# ============================================================
# CONSULTAR UM VÍDEO
# ============================================================

@router.get("/{video_id}")
def consultar_video(
    video_id: int,
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    video = db.query(Video).filter(
        Video.id == video_id,
    ).first()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Vídeo não encontrado.",
        )

    autor = db.query(User).filter(
        User.id == video.autor_id,
        User.ativo.is_(True),
    ).first()

    if not autor:
        raise HTTPException(
            status_code=404,
            detail="O autor deste vídeo não está disponível.",
        )

    resultado = formatar_video(video, autor)

    resultado["pode_apagar"] = (
        video.autor_id == atual.id
        or atual.administrador
    )

    return resultado


# ============================================================
# APAGAR VÍDEO
# ============================================================

@router.delete("/{video_id}")
def apagar_video(
    video_id: int,
    db: Session = Depends(obter_sessao),
    atual: User = Depends(obter_utilizador_atual),
):
    video = db.query(Video).filter(
        Video.id == video_id,
    ).first()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Vídeo não encontrado.",
        )

    if (
        video.autor_id != atual.id
        and not atual.administrador
    ):
        raise HTTPException(
            status_code=403,
            detail="Não tens permissão para apagar este vídeo.",
        )

    caminho = PASTA_VIDEOS / video.nome_ficheiro

    try:
        db.delete(video)
        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Não foi possível apagar o registo do vídeo.",
        )

    # Apagar o ficheiro depois de confirmar a eliminação
    # do registo na base de dados.
    try:
        if caminho.exists():
            caminho.unlink()
    except OSError:
        # O registo foi apagado; uma falha de disco não deve
        # transformar a resposta numa falsa indicação de sucesso.
        raise HTTPException(
            status_code=500,
            detail="O registo foi apagado, mas não foi possível "
                   "remover o ficheiro do disco.",
        )

    return {
        "mensagem": "Vídeo apagado com sucesso.",
        "id": video_id,
    }