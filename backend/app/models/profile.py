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


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    foto_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    capa_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    biografia: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    localizacao: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )