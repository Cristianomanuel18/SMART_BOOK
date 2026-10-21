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


# ============================================================
# SMART BOOK — CASA INTELIGENTE
# Criado por Cristiano Manzo
# ============================================================


def agora_utc():
    return datetime.now(timezone.utc)


# ============================================================
# CASAS
# ============================================================

class Casa(Base):
    __tablename__ = "casas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    proprietario_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
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

    endereco: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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


# ============================================================
# DIVISÕES DA CASA
# ============================================================

class DivisaoCasa(Base):
    __tablename__ = "divisoes_casa"

    __table_args__ = (
        UniqueConstraint(
            "casa_id",
            "nome",
            name="uq_divisao_nome_casa",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    casa_id: Mapped[int] = mapped_column(
        ForeignKey("casas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    icone: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=agora_utc,
        nullable=False,
    )


# ============================================================
# DISPOSITIVOS INTELIGENTES
# ============================================================

class DispositivoInteligente(Base):
    __tablename__ = "dispositivos_inteligentes"

    __table_args__ = (
        UniqueConstraint(
            "casa_id",
            "identificador_integracao",
            name="uq_dispositivo_integracao_casa",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    casa_id: Mapped[int] = mapped_column(
        ForeignKey("casas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    divisao_id: Mapped[int | None] = mapped_column(
        ForeignKey("divisoes_casa.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    nome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    marca: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    modelo: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    integracao: Mapped[str] = mapped_column(
        String(60),
        default="manual",
        nullable=False,
    )

    identificador_integracao: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entidade_externa: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    capacidades: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    estado_conhecido: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    online: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        default=None,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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


# ============================================================
# AUTOMATIZAÇÕES
# ============================================================

class AutomacaoCasa(Base):
    __tablename__ = "automacoes_casa"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    casa_id: Mapped[int] = mapped_column(
        ForeignKey("casas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tipo_ativacao: Mapped[str] = mapped_column(
        String(40),
        default="manual",
        nullable=False,
    )

    configuracao: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    criada_por_ia: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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


# ============================================================
# HISTÓRICO DE COMANDOS
# ============================================================

class HistoricoCasa(Base):
    __tablename__ = "historico_casa"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    casa_id: Mapped[int] = mapped_column(
        ForeignKey("casas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dispositivo_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "dispositivos_inteligentes.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    utilizador_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    origem: Mapped[str] = mapped_column(
        String(40),
        default="manual",
        nullable=False,
    )

    comando: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    parametros: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    resultado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    estado_execucao: Mapped[str] = mapped_column(
        String(40),
        default="pendente",
        nullable=False,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=agora_utc,
        nullable=False,
        index=True,
    )