
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class HomeAssistantConexao(Base):
    """
    Liga uma conta SMART BOOK a uma instalação
    individual do Home Assistant.
    """

    __tablename__ = "home_assistant_conexoes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="Minha casa",
    )

    url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    token_criptografado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metodo_autenticacao: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="token",
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    ultima_verificacao: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    estado_conexao: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="por_verificar",
    )

    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class HomeAssistantEntidade(Base):
    """
    Guarda o registo das entidades descobertas
    numa instalação Home Assistant.
    """

    __tablename__ = "home_assistant_entidades"

    __table_args__ = (
        UniqueConstraint(
            "conexao_id",
            "entity_id",
            name="uq_ha_entidade_conexao_entity",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    conexao_id: Mapped[int] = mapped_column(
        ForeignKey(
            "home_assistant_conexoes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    nome: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    dominio: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    estado: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    atributos: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    area: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    sincronizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class HomeAssistantHistorico(Base):
    """
    Regista as ações solicitadas através do SMART BOOK.
    Não guarda tokens nem credenciais nos registos.
    """

    __tablename__ = "home_assistant_historico"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    conexao_id: Mapped[int] = mapped_column(
        ForeignKey(
            "home_assistant_conexoes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    servico: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    resultado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pendente",
    )

    detalhes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
