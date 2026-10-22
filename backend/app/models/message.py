from datetime import UTC, datetime

from app.database.connection import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column


class Mensagem(Base):
    __tablename__ = "mensagens"

    __table_args__ = (
        CheckConstraint(
            "remetente_id != destinatario_id",
            name="ck_mensagem_utilizadores_diferentes",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    remetente_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    destinatario_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    conteudo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    lida: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )