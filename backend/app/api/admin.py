
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from app.database.connection import obter_sessao
from app.models.user import User
from app.security.auth import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    obter_token,
    validar_token_acesso,
    verificar_password,
)
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env", override=True)

router = APIRouter(prefix="/api/adm", tags=["ADM"])

ADMIN_EMAIL = os.getenv("SMARTBOOK_ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD_HASH = os.getenv("SMARTBOOK_ADMIN_PASSWORD_HASH", "")


def obter_db():
    db = next(obter_sessao())
    try:
        yield db
    finally:
        db.close()


class LoginADM(BaseModel):
    email: str
    password: str


class EstadoConta(BaseModel):
    ativo: bool


def exigir_admin(
    token: str = Depends(obter_token),
    db: Session = Depends(obter_db),
):
    payload = validar_token_acesso(token)

    if payload.get("tipo") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Acesso exclusivo ao administrador.",
        )

    user_id = int(payload["sub"])

    admin = db.query(User).filter(User.id == user_id).first()

    if not admin or not admin.ativo or not admin.administrador:
        raise HTTPException(
            status_code=403,
            detail="Conta administrativa inválida ou suspensa.",
        )

    if admin.email.lower() != ADMIN_EMAIL:
        raise HTTPException(
            status_code=403,
            detail="Esta conta não está autorizada no sistema ADM.",
        )

    return admin

@router.post("/login")
def login_adm(
    dados: LoginADM,
    db: Session = Depends(obter_db),
):
    if not ADMIN_EMAIL or not ADMIN_PASSWORD_HASH:
        raise HTTPException(
            status_code=503,
            detail="Configuração administrativa incompleta no .env.",
        )

    email = dados.email.strip().lower()

    if email != ADMIN_EMAIL:
        print("[ADM DEBUG] O e-mail recebido não corresponde ao configurado.")
        raise HTTPException(
            status_code=401,
            detail="Credenciais administrativas inválidas.",
        )

    admin = (
        db.query(User)
        .filter(User.email == ADMIN_EMAIL)
        .first()
    )

    if not admin:
        print("[ADM DEBUG] Conta não encontrada.")
        raise HTTPException(
            status_code=401,
            detail="Credenciais administrativas inválidas.",
        )

    password_env_ok = verificar_password(
        dados.password,
        ADMIN_PASSWORD_HASH,
    )

    password_db_ok = verificar_password(
        dados.password,
        admin.password_hash,
    )

    print("[ADM DEBUG] Conta encontrada:", admin.id)
    print("[ADM DEBUG] Conta ativa:", admin.ativo)
    print("[ADM DEBUG] É administrador:", admin.administrador)
    print("[ADM DEBUG] Palavra-passe válida no .env:", password_env_ok)
    print("[ADM DEBUG] Palavra-passe válida na conta:", password_db_ok)

    if (
        not admin.ativo
        or not admin.administrador
        or not password_env_ok
        or not password_db_ok
    ):
        raise HTTPException(
            status_code=401,
            detail="Credenciais administrativas inválidas.",
        )

    agora = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": str(admin.id),
            "username": admin.username,
            "tipo": "admin",
            "iat": agora,
            "exp": agora + timedelta(hours=2),
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "tipo": "admin",
        "administrador": {
            "id": admin.id,
            "nome": admin.nome_completo,
            "email": admin.email,
        },
    }


@router.get("/estado")
def estado_adm(admin: User = Depends(exigir_admin)):
    return {
        "autenticado": True,
        "tipo": "admin",
        "nome": admin.nome_completo,
        "email": admin.email,
    }


@router.get("/dashboard")
def dashboard(
    admin: User = Depends(exigir_admin),
    db: Session = Depends(obter_db),
):
    total = db.query(User).count()

    ativos = (
        db.query(User)
        .filter(User.ativo.is_(True))
        .count()
    )

    suspensos = (
        db.query(User)
        .filter(User.ativo.is_(False))
        .count()
    )

    administradores = (
        db.query(User)
        .filter(User.administrador.is_(True))
        .count()
    )

    return {
        "total_utilizadores": total,
        "utilizadores_ativos": ativos,
        "utilizadores_suspensos": suspensos,
        "administradores": administradores,
        "administrador_atual": admin.nome_completo,
        "data_servidor": datetime.now(UTC).isoformat(),
    }


@router.get("/utilizadores")
def listar_utilizadores(
    pesquisa: str = Query(default="", max_length=100),
    limite: int = Query(default=100, ge=1, le=500),
    pagina: int = Query(default=1, ge=1),
    admin: User = Depends(exigir_admin),
    db: Session = Depends(obter_db),
):
    consulta = db.query(User)

    if pesquisa.strip():
        termo = f"%{pesquisa.strip()}%"
        consulta = consulta.filter(
            User.nome_completo.ilike(termo)
            | User.username.ilike(termo)
            | User.email.ilike(termo)
        )

    total = consulta.count()

    utilizadores = (
        consulta.order_by(User.id.desc())
        .offset((pagina - 1) * limite)
        .limit(limite)
        .all()
    )

    return {
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "utilizadores": [
            {
                "id": u.id,
                "nome_completo": u.nome_completo,
                "username": u.username,
                "email": u.email,
                "ativo": u.ativo,
                "administrador": u.administrador,
                "data_registo": (
                    u.data_registo.isoformat()
                    if u.data_registo
                    else None
                ),
            }
            for u in utilizadores
        ],
    }


@router.patch("/utilizadores/{utilizador_id}/estado")
def alterar_estado_utilizador(
    utilizador_id: int,
    dados: EstadoConta,
    admin: User = Depends(exigir_admin),
    db: Session = Depends(obter_db),
):
    utilizador = (
        db.query(User)
        .filter(User.id == utilizador_id)
        .first()
    )

    if not utilizador:
        raise HTTPException(
            status_code=404,
            detail="Utilizador não encontrado.",
        )

    if utilizador.id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Não podes suspender a tua própria conta administrativa.",
        )

    if utilizador.administrador:
        raise HTTPException(
            status_code=403,
            detail="Esta operação não pode suspender outra conta administrativa.",
        )

    utilizador.ativo = dados.ativo
    db.commit()
    db.refresh(utilizador)

    return {
        "sucesso": True,
        "mensagem": (
            "Conta ativada."
            if utilizador.ativo
            else "Conta suspensa."
        ),
        "utilizador_id": utilizador.id,
        "ativo": utilizador.ativo,
    }
