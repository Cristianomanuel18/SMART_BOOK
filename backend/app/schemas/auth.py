from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegistoUtilizador(BaseModel):
    nome_completo: str = Field(
        min_length=2,
        max_length=120,
    )

    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_.]+$",
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class LoginUtilizador(BaseModel):
    identificador: str = Field(
        min_length=1,
        max_length=255,
    )

    password: str = Field(
        min_length=1,
        max_length=128,
    )


class UtilizadorPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    username: str
    email: EmailStr
    ativo: bool
    administrador: bool


class RespostaAutenticacao(BaseModel):
    mensagem: str
    access_token: str
    token_type: str = "bearer"
    utilizador: UtilizadorPublico