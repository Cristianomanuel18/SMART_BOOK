from datetime import UTC, datetime

from app.database.connection import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    autor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    descricao: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    nome_ficheiro: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    url_video: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    tipo_mime: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    tamanho_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )