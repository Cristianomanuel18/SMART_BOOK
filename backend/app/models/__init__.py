from app.models.user import User
from app.models.post import Post
from app.models.profile import Profile
from app.models.friendship import PedidoAmizade
from app.models.message import Mensagem
from app.models.notification import Notificacao
from app.models.video import Video

__all__ = [
    "User",
    "Post",
    "Profile",
    "PedidoAmizade",
    "Mensagem",
    "Notificacao",
    "Video",
    "Casa",
    "DivisaoCasa",
    "DispositivoInteligente",
    "AutomacaoCasa",
    "HistoricoCasa",
]

from app.models.home import (
    Casa,
    DivisaoCasa,
    DispositivoInteligente,
    AutomacaoCasa,
    HistoricoCasa,
)

from app.models.oportunidade import OportunidadeNegocio

__all__ = list(dict.fromkeys([
    *(globals().get("__all__", [])),
    "OportunidadeNegocio",
]))

from app.models.group import (
    Grupo,
    ParticipanteGrupo,
    MensagemGrupo,
)

__all__ = list(dict.fromkeys([
    *(globals().get("__all__", [])),
    "Grupo",
    "ParticipanteGrupo",
    "MensagemGrupo",
]))