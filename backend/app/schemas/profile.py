from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AtualizarPerfil(BaseModel):
    biografia: str | None = Field(
        default=None,
        max_length=1000,
    )

    localizacao: str | None = Field(
        default=None,
        max_length=150,
    )

    foto_url: str | None = Field(
        default=None,
        max_length=500,
    )

    capa_url: str | None = Field(
        default=None,
        max_length=500,
    )


class PerfilPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    username: str

    foto_url: str | None = None
    capa_url: str | None = None
    biografia: str | None = None
    localizacao: str | None = None

    data_registo: datetime
    data_atualizacao: datetime | None = None