"""Client HTTP pour api-couleur-tempo.fr."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import aiohttp

from .const import (
    COLOR_INCONNU,
    COLOR_MAP,
    HTTP_TIMEOUT,
    URL_COULEUR_TEMPO_DATE,
    URL_COULEUR_TEMPO_NOW,
    URL_COULEUR_TEMPO_TODAY,
    URL_COULEUR_TEMPO_TOMORROW,
)
from .exceptions import CannotConnect, InvalidAuth, RateLimitExceeded

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)


def get_season_start(today: date | None = None) -> date:
    """Retourne la date de début de saison Tempo (1er septembre).

    Si le mois actuel est avant novembre, la saison a commencé en septembre
    de l'année précédente.
    """
    ref = today or date.today()
    if ref.month >= 11:
        return date(ref.year, 9, 1)
    return date(ref.year - 1, 9, 1)


class CouleurTempoClient:
    """Client pour l'API api-couleur-tempo.fr."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _get_json(self, url: str) -> dict:
        """Effectue une requête GET et retourne le JSON."""
        try:
            async with self._session.get(url, timeout=_TIMEOUT) as resp:
                if resp.status == 401:
                    raise InvalidAuth(f"HTTP 401 sur {url}")
                if resp.status == 429:
                    raise RateLimitExceeded(f"HTTP 429 sur {url}")
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise CannotConnect(str(err)) from err

    def _code_to_color(self, data: dict) -> str:
        """Convertit codeJour en nom de couleur. Retourne COLOR_INCONNU si inconnu."""
        code = data.get("codeJour")
        if code is None:
            return COLOR_INCONNU
        return COLOR_MAP.get(str(code), COLOR_INCONNU)

    async def get_today(self) -> str:
        """Retourne la couleur Tempo du jour."""
        data = await self._get_json(URL_COULEUR_TEMPO_TODAY)
        color = self._code_to_color(data)
        _LOGGER.debug("Couleur aujourd'hui : %s", color)
        return color

    async def get_tomorrow(self) -> str:
        """Retourne la couleur Tempo du lendemain (COLOR_INCONNU si non publiée)."""
        data = await self._get_json(URL_COULEUR_TEMPO_TOMORROW)
        color = self._code_to_color(data)
        _LOGGER.debug("Couleur demain : %s", color)
        return color

    async def get_now(self) -> dict:
        """Retourne le dict complet /api/now (codeCouleur, codeHoraire, tarifKwh, libTarif)."""
        return await self._get_json(URL_COULEUR_TEMPO_NOW)

    async def get_day(self, day: date) -> str:
        """Retourne la couleur Tempo pour un jour donné."""
        url = URL_COULEUR_TEMPO_DATE.format(date=day.isoformat())
        data = await self._get_json(url)
        return self._code_to_color(data)

    async def get_season_history(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> list[tuple[date, str]]:
        """Retourne l'historique des couleurs pour la saison en cours.

        Args:
            start: Date de début (défaut : 1er septembre de la saison courante).
            end: Date de fin (défaut : aujourd'hui).

        Returns:
            Liste de tuples (date, couleur) pour chaque jour de la plage.
        """
        today = date.today()
        start = start or get_season_start(today)
        end = end or today

        # TODO: Consider asyncio.gather with semaphore for concurrent requests
        # to improve performance on long season ranges (180+ days).
        result: list[tuple[date, str]] = []
        current = start
        while current <= end:
            color = await self.get_day(current)
            result.append((current, color))
            current += timedelta(days=1)

        _LOGGER.debug(
            "Historique saison chargé : %d jours du %s au %s",
            len(result),
            start,
            end,
        )
        return result
