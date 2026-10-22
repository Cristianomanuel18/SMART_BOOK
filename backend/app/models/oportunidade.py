from datetime import UTC, datetime

from app.database.connection import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column


def agora_utc():
    return datetime.now(UTC)


class OportunidadeNegocio(Base):
    """
    SMART BOOK — Negócio com Oportunidade.

    Guarda perfis profissionais e empreendimentos
    publicados pelos utilizadores.
    """

    __tablename__ = "oportunidades_negocio"

    __table_args__ = (
        Index(
            "ix_oportunidade_tipo_criada",
            "tipo",
            "data_criacao",
        ),
        Index(
            "ix_oportunidade_area",
            "area",
        ),
    )

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

    tipo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="profissional",
    )

    nome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    area: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    habilidades: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    experiencia: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    escolaridade: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    localizacao: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    telefone: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    disponibilidade: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=agora_utc,
        nullable=False,
    )

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=agora_utc,
        onupdate=agora_utc,
        nullable=False,
    )