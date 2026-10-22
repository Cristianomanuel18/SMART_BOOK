from pathlib import Path
from fastapi.responses import FileResponse

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.caren import router as caren_router
from app.api.friendships import router as friendships_router
from app.api.groups import router as groups_router
from app.api.home import router as home_router
from app.api.messages import router as messages_router
from app.api.notifications import router as notifications_router
from app.api.oportunidades import router as oportunidades_router
from app.api.posts import router as posts_router
from app.api.profile import router as profile_router
from app.api.videos import router as videos_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ============================================================
# APLICAÇÃO
# ============================================================

app = FastAPI(
    title="SMART BOOK API",
    description=(
        "API da rede social SMART BOOK, "
        "criada por Cristiano Manzo."
    ),
    version="0.3.0",
)


# ============================================================
# PASTAS DE FICHEIROS
# ============================================================

RAIZ_PROJETO = Path(__file__).resolve().parents[2]

PASTA_MEDIA = RAIZ_PROJETO / "media"
PASTA_IMAGENS_PERFIS = PASTA_MEDIA / "perfis"
PASTA_IMAGENS_GRUPOS = PASTA_MEDIA / "grupos"
PASTA_VIDEOS = PASTA_MEDIA / "videos"
PASTA_FRONTEND = RAIZ_PROJETO / "frontend" / "dist"
FICHEIRO_INDEX = PASTA_FRONTEND / "index.html"

for pasta in (
    PASTA_IMAGENS_PERFIS,
    PASTA_IMAGENS_GRUPOS,
    PASTA_VIDEOS,
):
    pasta.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# SERVIR FOTOGRAFIAS E VÍDEOS
# ============================================================

app.mount(
    "/media/perfis",
    StaticFiles(directory=str(PASTA_IMAGENS_PERFIS)),
    name="imagens-perfis",
)

app.mount(
    "/media/grupos",
    StaticFiles(directory=str(PASTA_IMAGENS_GRUPOS)),
    name="imagens-grupos",
)

app.mount(
    "/media/videos",
    StaticFiles(directory=str(PASTA_VIDEOS)),
    name="videos",
)


# ============================================================
# CORS — LIGAÇÃO AO FRONTEND
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


# ============================================================
# MÓDULOS DA REDE SOCIAL
# ============================================================

app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(friendships_router)
app.include_router(messages_router)
app.include_router(notifications_router)
app.include_router(videos_router)
app.include_router(profile_router)
app.include_router(caren_router)
app.include_router(home_router)
app.include_router(admin_router)
app.include_router(oportunidades_router)
app.include_router(groups_router)


# ============================================================
# INFORMAÇÕES DO SISTEMA
# ============================================================

@app.get("/")
def inicio():
    return {
        "nome": "SMART BOOK",
        "criador": "Cristiano Manzo",
        "mensagem": "API da rede social SMART BOOK",
        "estado": "online",
    }


@app.get("/api/health")
def verificar_estado():
    return {
        "estado": "online",
    }


@app.get("/api/info")
def informacoes():
    return {
        "nome": "SMART BOOK",
        "versao": "0.3.0",
        "assistente_ia": "Caren",
        "modulos": [
            "autenticacao",
            "publicacoes",
            "amizades",
            "perfis",
            "grupos",
            "videos",
        ],
    }
# ============================================================
# FRONTEND REACT — SMART BOOK
# ============================================================

if PASTA_FRONTEND.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(PASTA_FRONTEND), html=True),
        name="frontend",
    )