# ============================================================
# SMART BOOK — MODELOS DOS GRUPOS
# Criado por Cristiano Manzo
# ============================================================

from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


# ============================================================
# GRUPOS
# ============================================================

class Grupo(Base):

    __tablename__ = "grupos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    nome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    criador_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Fotografia do grupo
    imagem_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Imagem de capa do grupo
    capa_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )


# ============================================================
# PARTICIPANTES DOS GRUPOS
# ============================================================

class ParticipanteGrupo(Base):

    __tablename__ = "participantes_grupo"

    __table_args__ = (
        UniqueConstraint(
            "grupo_id",
            "utilizador_id",
            name="uq_participante_grupo",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    grupo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("grupos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    utilizador_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    data_entrada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ============================================================
# MENSAGENS DOS GRUPOS
# ============================================================

class MensagemGrupo(Base):

    __tablename__ = "mensagens_grupo"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    grupo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("grupos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    remetente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    conteudo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )