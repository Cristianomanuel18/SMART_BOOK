
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

ROOT_DIR = Path(__file__).resolve().parents[3]

load_dotenv(ROOT_DIR / ".env")


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY não está configurada no ficheiro .env."
    )


JWT_ALGORITHM = "HS256"
TOKEN_HORAS_VALIDADE = 2

password_hasher = PasswordHash.recommended()

esquema_bearer = HTTPBearer(auto_error=False)


def gerar_hash_password(password: str) -> str:
    """Gera um hash seguro para a palavra-passe."""
    return password_hasher.hash(password)


def verificar_password(
    password: str,
    password_hash: str,
) -> bool:
    """Verifica uma palavra-passe."""
    try:
        return password_hasher.verify(
            password,
            password_hash,
        )
    except Exception:
        return False


def criar_token_acesso(
    utilizador_id: int,
    username: str,
) -> str:
    """Cria um token JWT com validade limitada."""

    agora = datetime.now(UTC)

    payload = {
        "sub": str(utilizador_id),
        "username": username,
        "iat": agora,
        "exp": agora + timedelta(
            hours=TOKEN_HORAS_VALIDADE
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def validar_token_acesso(token: str) -> dict:
    """Valida um JWT e devolve os seus dados."""

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={
                "require": ["sub", "iat", "exp"],
            },
        )

        identificador = payload.get("sub")

        if not identificador:
            raise InvalidTokenError(
                "O token não contém um identificador."
            )

        if not str(identificador).isdigit():
            raise InvalidTokenError(
                "O identificador do token é inválido."
            )

        return payload

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Inicia sessão novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def obter_token(
    credenciais: HTTPAuthorizationCredentials | None = Depends(
        esquema_bearer
    ),
) -> str:
    """Obtém o token enviado no cabeçalho Authorization."""

    if credenciais is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credenciais.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esquema de autenticação inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credenciais.credentials
