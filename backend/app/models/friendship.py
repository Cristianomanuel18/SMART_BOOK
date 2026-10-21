from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class PedidoAmizade(Base):
    __tablename__ = "pedidos_amizade"

    __table_args__ = (
        UniqueConstraint(
            "remetente_id",
            "destinatario_id",
            name="uq_pedido_amizade_utilizadores",
        ),
        CheckConstraint(
            "remetente_id != destinatario_id",
            name="ck_pedido_amizade_sem_autoamizade",
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

    estado: Mapped[str] = mapped_column(
        String(20),
        default="pendente",
        nullable=False,
        index=True,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    data_resposta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )