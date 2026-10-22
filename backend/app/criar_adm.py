
import os
import getpass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import or_

# Carregar a configuração do projeto.
RAIZ_PROJETO = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ_PROJETO / ".env")

# Para evitar alterar a base de dados errada, exigir DATABASE_URL.
if not os.getenv("DATABASE_URL"):
    raise SystemExit(
        "\nERRO: DATABASE_URL não está definida.\n"
        "Define a ligação à base de dados que pretendes utilizar "
        "antes de executar este script.\n"
    )

from app.database.connection import obter_sessao
from app.models.user import User
from app.security.auth import gerar_hash_password, verificar_password


EMAIL_ADMIN = "admin@smartbook.ao"
USERNAME_BASE = "smartbookadmin"
NOME_ADMIN = "Administrador SMART BOOK"


def escolher_username(db):
    username = USERNAME_BASE
    numero = 1

    while True:
        existente = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existente is None or existente.email.lower() == EMAIL_ADMIN:
            return username

        username = f"{USERNAME_BASE}{numero}"
        numero += 1


def main():
    print("\n===================================")
    print("     CRIAR ADMINISTRADOR")
    print("          SMART BOOK")
    print("===================================\n")

    password = getpass.getpass(
        "Introduz a palavra-passe do administrador: "
    )

    confirmacao = getpass.getpass(
        "Confirma a palavra-passe: "
    )

    if not password:
        raise SystemExit("ERRO: a palavra-passe não pode estar vazia.")

    if password != confirmacao:
        raise SystemExit("ERRO: as palavras-passe não coincidem.")

    # O hash será utilizado tanto na base de dados
    # como na configuração SMARTBOOK_ADMIN_PASSWORD_HASH.
    password_hash = gerar_hash_password(password)

    sessao = obter_sessao()
    db = next(sessao)

    try:
        admin = (
            db.query(User)
            .filter(User.email == EMAIL_ADMIN)
            .first()
        )

        if admin:
            print("\nA conta já existe. A atualizar permissões...")

            admin.nome_completo = NOME_ADMIN
            admin.ativo = True
            admin.administrador = True
            admin.password_hash = password_hash

            if not admin.username:
                admin.username = escolher_username(db)

        else:
            username = escolher_username(db)

            admin = User(
                nome_completo=NOME_ADMIN,
                username=username,
                email=EMAIL_ADMIN,
                password_hash=password_hash,
                ativo=True,
                administrador=True,
            )

            db.add(admin)

        db.commit()
        db.refresh(admin)

        # Confirmar que a conta foi gravada corretamente.
        if not verificar_password(password, admin.password_hash):
            raise RuntimeError(
                "A conta foi gravada, mas a validação da palavra-passe falhou."
            )

        print("\nSUCESSO: administrador criado/atualizado.")
        print(f"ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(f"Username: {admin.username}")
        print(f"Ativo: {admin.ativo}")
        print(f"Administrador: {admin.administrador}")

        print("\nHASH PARA CONFIGURAR NO RENDER:")
        print(password_hash)

        print(
            "\nNo serviço SMART BOOK do Render, configura estas "
            "variáveis de ambiente:"
        )
        print(f"SMARTBOOK_ADMIN_EMAIL={EMAIL_ADMIN}")
        print("SMARTBOOK_ADMIN_PASSWORD_HASH=<hash apresentado acima>")

        print(
            "\nDepois, guarda as alterações e deixa o Render "
            "concluir o redeploy."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        sessao.close()


if __name__ == "__main__":
    main()
