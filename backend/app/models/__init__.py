from app.models.friendship import PedidoAmizade
from app.models.message import Mensagem
from app.models.notification import Notificacao
from app.models.post import Post
from app.models.profile import Profile
from app.models.user import User
from app.models.video import Video

__all__ = [
    "AutomacaoCasa",
    "Casa",
    "DispositivoInteligente",
    "DivisaoCasa",
    "HistoricoCasa",
    "Mensagem",
    "Notificacao",
    "PedidoAmizade",
    "Post",
    "Profile",
    "User",
    "Video",
]

from app.models.home import (
    AutomacaoCasa,
    Casa,
    DispositivoInteligente,
    DivisaoCasa,
    HistoricoCasa,
)
from app.models.oportunidade import OportunidadeNegocio

__all__ = list(dict.fromkeys([
    *(globals().get("__all__", [])),
    "OportunidadeNegocio",
]))

from app.models.group import (
    Grupo,
    MensagemGrupo,
    ParticipanteGrupo,
)

__all__ = list(dict.fromkeys([
    *(globals().get("__all__", [])),
    "Grupo",
    "ParticipanteGrupo",
    "MensagemGrupo",
]))