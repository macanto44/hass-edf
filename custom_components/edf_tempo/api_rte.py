"""Client HTTP stub pour l'API RTE OAuth2 (post-MVP)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import aiohttp


class RTEClient:
    """Stub MVP pour l'API RTE Tempo.

    L'implémentation complète OAuth2 (récupération de token + calendrier Tempo)
    est reportée post-MVP. Ce stub garantit que le coordinator peut instancier
    RTEClient sans erreur de compilation ou d'import.

    Références :
      - URL token  : URL_RTE_TOKEN dans const.py
      - URL API    : URL_RTE_TEMPO dans const.py
      - Credentials: CONF_RTE_CLIENT_ID / CONF_RTE_CLIENT_SECRET dans config entry
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_tempo_color(self) -> str:
        """Retourne la couleur Tempo du jour via l'API RTE.

        Non implémenté en MVP. L'API RTE nécessite une authentification OAuth2
        (client_id / client_secret fournis par RTE).
        Implémentation prévue post-MVP.

        Raises:
            NotImplementedError: Toujours — stub MVP.
        """
        raise NotImplementedError("RTE API not implemented in MVP")
