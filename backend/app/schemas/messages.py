from datetime import datetime

from pydantic import BaseModel, Field


class CriarMensagem(BaseModel):
    conteudo: str = Field(
        min_length=1,
        max_length=5000,
    )


class MensagemPublica(BaseModel):
    id: int
    remetente_id: int
    destinatario_id: int
    conteudo: str
    lida: bool
    data_criacao: datetime


class ConversaPublica(BaseModel):
    utilizador_id: int
    nome_completo: str
    username: str
    ultima_mensagem: str
    data_ultima_mensagem: datetime
    mensagens_nao_lidas: int