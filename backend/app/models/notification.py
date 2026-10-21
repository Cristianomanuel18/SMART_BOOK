from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Notificacao(Base):
    __tablename__ = "notificacoes"

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

    autor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    tipo: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    titulo: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    mensagem: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    referencia_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    lida: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )