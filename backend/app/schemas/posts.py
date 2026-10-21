
from datetime import datetime

from pydantic import BaseModel, Field


class CriarPublicacao(BaseModel):
    conteudo: str = Field(
        min_length=1,
        max_length=2000,
    )


class PublicacaoPublica(BaseModel):
    id: int
    autor_id: int
    autor_nome: str
    autor_username: str
    conteudo: str
    data_criacao: datetime
