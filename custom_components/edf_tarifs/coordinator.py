"""DataUpdateCoordinator pour l'intégration EDF Tarifs."""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_couleur_tempo import CouleurTempoClient, get_season_start
from .api_datagouv import DataGouvClient
from .const import (
    AVAILABLE_SCAN_INTERVALS,
    COLOR_BLEU,
    COLOR_BLANC,
    COLOR_INCONNU,
    COLOR_ROUGE,
    CONF_CONTRACT_TYPE,
    CONF_HC_RANGES,
    CONF_POWER_KVA,
    CONF_SCAN_INTERVAL,
    CONTRACT_BASE,
    CONTRACT_HPHC,
    CONTRACT_TEMPO,
    DEFAULT_HC_RANGES_TEMPO,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_JOURS_BLANC,
    MAX_JOURS_BLEU,
    MAX_JOURS_ROUGE,
    PERIOD_HC,
    PERIOD_HP,
)
from .exceptions import CannotConnect, InvalidAuth

_LOGGER = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef]

TIMEZONE_PARIS = ZoneInfo("Europe/Paris")

# Mapping colonnes CSV → clés coordinator.data
_TARIF_KEY_MAP_TEMPO = {
    "PART_VARIABLE_HCBleu_TTC": "tarif_bleu_hc",
    "PART_VARIABLE_HPBleu_TTC": "tarif_bleu_hp",
    "PART_VARIABLE_HCBlanc_TTC": "tarif_blanc_hc",
    "PART_VARIABLE_HPBlanc_TTC": "tarif_blanc_hp",
    "PART_VARIABLE_HCRouge_TTC": "tarif_rouge_hc",
    "PART_VARIABLE_HPRouge_TTC": "tarif_rouge_hp",
}

_TARIF_KEY_MAP_HCHP = {
    "PART_VARIABLE_HC_TTC": "tarif_hc",
    "PART_VARIABLE_HP_TTC": "tarif_hp",
}


def is_hc_period(hc_ranges: str, now: datetime | None = None) -> bool:
    """True si l'heure actuelle est en période Heures Creuses."""
    now = now or datetime.now(TIMEZONE_PARIS)
    current_time = now.time()

    for range_str in hc_ranges.split(","):
        try:
            start_str, end_str = range_str.strip().split("-")
            start = time.fromisoformat(start_str.strip())
            end = time.fromisoformat(end_str.strip())
        except (ValueError, TypeError):
            _LOGGER.warning("Format HC invalide ignoré : %r", range_str.strip())
            continue

        if start <= end:
            if start <= current_time < end:
                return True
        else:
            # Cross-midnight (ex: 22:00-06:00)
            if current_time >= start or current_time < end:
                return True

    return False


class EDFTempoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator qui orchestre toutes les sources de données EDF Tarifs."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        scan_key = entry.data.get(CONF_SCAN_INTERVAL, "6h")
        interval = AVAILABLE_SCAN_INTERVALS.get(scan_key, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=interval,
        )
        self._entry = entry
        self._contract_type: str = entry.data[CONF_CONTRACT_TYPE]
        self._power_kva: int = entry.data[CONF_POWER_KVA]
        self._hc_ranges: str = entry.data.get(CONF_HC_RANGES, DEFAULT_HC_RANGES_TEMPO)
        self._season_cache: dict[date, str] = {}
        self._unsub_hc_listeners: list[Callable] = []

    @staticmethod
    def _parse_hc_boundaries(hc_ranges: str) -> list[time]:
        """Extrait les heures de début et fin de chaque plage HC."""
        boundaries: list[time] = []
        for range_str in hc_ranges.split(","):
            try:
                start_str, end_str = range_str.strip().split("-")
                boundaries.append(time.fromisoformat(start_str.strip()))
                boundaries.append(time.fromisoformat(end_str.strip()))
            except (ValueError, TypeError):
                _LOGGER.warning("Format HC invalide ignoré : %r", range_str.strip())
        return boundaries

    def setup_hc_listeners(self) -> None:
        """Planifie un refresh du coordinator aux transitions HC/HP."""
        from homeassistant.helpers.event import async_track_time_change

        boundaries = self._parse_hc_boundaries(self._hc_ranges)
        for boundary in boundaries:
            unsub = async_track_time_change(
                self.hass,
                self._handle_hc_boundary,
                hour=boundary.hour,
                minute=boundary.minute,
                second=0,
            )
            self._unsub_hc_listeners.append(unsub)
        if boundaries:
            _LOGGER.debug(
                "HC boundary listeners registered at: %s",
                [b.strftime("%H:%M") for b in boundaries],
            )

    async def _handle_hc_boundary(self, _now: datetime) -> None:
        """Callback déclenché aux transitions HC/HP."""
        _LOGGER.debug("HC/HP boundary reached, requesting coordinator refresh")
        await self.async_request_refresh()

    def shutdown_hc_listeners(self) -> None:
        """Désinscrit les listeners de transition HC."""
        for unsub in self._unsub_hc_listeners:
            unsub()
        self._unsub_hc_listeners.clear()

    def _map_tarifs(self, raw: dict[str, float], key_map: dict[str, str]) -> dict[str, Any]:
        """Convertit les clés CSV en clés coordinator.data et calcule abonnement_mensuel."""
        data: dict[str, Any] = {}
        data["abonnement_mensuel"] = raw["PART_FIXE_TTC"] / 12
        for csv_key, coord_key in key_map.items():
            if csv_key in raw:
                data[coord_key] = raw[csv_key]
        return data

    def _compute_tarif_actuel(self, data: dict[str, Any]) -> float | None:
        """Calcule le tarif en cours selon contrat, couleur et période."""
        periode = data.get("periode_actuelle", "").lower()
        if self._contract_type == CONTRACT_BASE:
            return data.get("tarif_base")
        if self._contract_type == CONTRACT_HPHC:
            return data.get(f"tarif_{periode}")
        # Tempo
        couleur = data.get("couleur_aujourd_hui", "").lower()
        if couleur and periode:
            return data.get(f"tarif_{couleur}_{periode}")
        return None

    def _compute_counters(self, history: list[tuple[Any, str]]) -> dict[str, int]:
        """Calcule les compteurs de jours par couleur pour la saison."""
        counts = {COLOR_BLEU: 0, COLOR_BLANC: 0, COLOR_ROUGE: 0}
        for _, color in history:
            if color in counts:
                counts[color] += 1

        return {
            "jours_bleus_consommes": counts[COLOR_BLEU],
            "jours_bleus_restants": MAX_JOURS_BLEU - counts[COLOR_BLEU],
            "jours_blancs_consommes": counts[COLOR_BLANC],
            "jours_blancs_restants": MAX_JOURS_BLANC - counts[COLOR_BLANC],
            "jours_rouges_consommes": counts[COLOR_ROUGE],
            "jours_rouges_restants": MAX_JOURS_ROUGE - counts[COLOR_ROUGE],
        }

    async def _async_update_data(self) -> dict[str, Any]:
        """Orchestre la collecte de toutes les données selon le type de contrat."""
        session = async_get_clientsession(self.hass)
        data: dict[str, Any] = {}

        # ── 1. Tarifs depuis data.gouv.fr ──
        try:
            data.update(await self._fetch_tarifs(session))
        except InvalidAuth:
            self._entry.async_start_reauth(self.hass)
            raise UpdateFailed("Authentification invalide — re-auth demandée")
        except CannotConnect:
            if self.data:
                _LOGGER.warning("Erreur tarifs, utilisation du cache")
                data.update(
                    {k: self.data[k] for k in self.data if k.startswith("tarif_") or k == "abonnement_mensuel"}
                )
            else:
                raise UpdateFailed("Impossible de charger les tarifs")

        # ── 2. Couleurs Tempo ──
        if self._contract_type == CONTRACT_TEMPO:
            try:
                data.update(await self._fetch_couleurs(session))
            except InvalidAuth:
                self._entry.async_start_reauth(self.hass)
                raise UpdateFailed("Authentification invalide — re-auth demandée")
            except CannotConnect:
                if self.data:
                    _LOGGER.warning("Erreur couleurs, utilisation du cache")
                    data["couleur_aujourd_hui"] = self.data.get("couleur_aujourd_hui", COLOR_INCONNU)
                    data["couleur_demain"] = self.data.get("couleur_demain", COLOR_INCONNU)
                    for key in self.data:
                        if key.startswith("jours_"):
                            data[key] = self.data[key]
                else:
                    raise UpdateFailed("Impossible de charger les couleurs Tempo")

        # ── 3. Période HC/HP et tarif actuel ──
        if self._contract_type != CONTRACT_BASE:
            data["periode_actuelle"] = PERIOD_HC if is_hc_period(self._hc_ranges) else PERIOD_HP
            data["tarif_actuel"] = self._compute_tarif_actuel(data)

        return data

    async def _fetch_tarifs(self, session: Any) -> dict[str, Any]:
        """Charge les tarifs selon le type de contrat."""
        client = DataGouvClient(session)

        if self._contract_type == CONTRACT_BASE:
            raw = await client.get_tarifs_base(self._power_kva)
            result: dict[str, Any] = {"abonnement_mensuel": raw["PART_FIXE_TTC"] / 12}
            result["tarif_base"] = raw["PART_VARIABLE_TTC"]
            return result

        if self._contract_type == CONTRACT_HPHC:
            raw = await client.get_tarifs_hchp(self._power_kva)
            return self._map_tarifs(raw, _TARIF_KEY_MAP_HCHP)

        # Tempo
        raw = await client.get_tarifs_tempo(self._power_kva)
        return self._map_tarifs(raw, _TARIF_KEY_MAP_TEMPO)

    async def _fetch_couleurs(
        self, session: Any, _today: date | None = None
    ) -> dict[str, Any]:
        """Charge les couleurs Tempo et les compteurs saison (cache incrémental)."""
        client = CouleurTempoClient(session)
        today_color = await client.get_today()
        tomorrow_color = await client.get_tomorrow()

        today = _today or date.today()
        season_start = get_season_start(today)

        # Purger les entrées hors saison courante
        self._season_cache = {
            d: c for d, c in self._season_cache.items() if d >= season_start
        }

        # Toujours re-fetcher aujourd'hui (la couleur peut changer)
        self._season_cache.pop(today, None)

        # Identifier les jours manquants
        days_to_fetch: list[date] = []
        current = season_start
        while current <= today:
            if current not in self._season_cache:
                days_to_fetch.append(current)
            current += timedelta(days=1)

        # Ne fetcher que les jours manquants
        if days_to_fetch:
            _LOGGER.debug(
                "Season cache: fetching %d day(s) out of %d total",
                len(days_to_fetch),
                (today - season_start).days + 1,
            )
            for day in days_to_fetch:
                color = await client.get_day(day)
                self._season_cache[day] = color

        # Construire l'historique depuis le cache pour _compute_counters
        history: list[tuple[date, str]] = sorted(self._season_cache.items())

        result: dict[str, Any] = {
            "couleur_aujourd_hui": today_color,
            "couleur_demain": tomorrow_color,
        }
        result.update(self._compute_counters(history))
        return result
