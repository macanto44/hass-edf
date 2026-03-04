"""Client HTTP pour les datasets CSV CRE sur data.gouv.fr."""

from __future__ import annotations

import csv
import io
import logging

import aiohttp

from .const import (
    CSV_REQUIRED_COLS_BASE,
    CSV_REQUIRED_COLS_HCHP,
    CSV_REQUIRED_COLS_TEMPO,
    CSV_SEPARATOR,
    HTTP_TIMEOUT,
    URL_DATAGOUV_BASE_HCHP,
    URL_DATAGOUV_HCHP_POWER,
    URL_DATAGOUV_TEMPO,
)
from .exceptions import CannotConnect, ParseError

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)


class DataGouvClient:
    """Client pour les datasets tarifaires CRE sur data.gouv.fr."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _download_csv(self, url: str) -> str:
        """Télécharge un CSV et retourne son contenu texte."""
        try:
            async with self._session.get(url, timeout=_TIMEOUT) as resp:
                resp.raise_for_status()
                return await resp.text(encoding="utf-8")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CannotConnect(str(err)) from err

    def _parse_csv(
        self,
        content: str,
        required_cols: set[str],
        power_kva: int,
    ) -> dict[str, float]:
        """Parse un CSV CRE et retourne les valeurs de la dernière ligne correspondant à power_kva.

        Args:
            content: Contenu brut du CSV (UTF-8, séparateur ';').
            required_cols: Colonnes obligatoires à valider.
            power_kva: Puissance souscrite à filtrer.

        Returns:
            Dict {nom_colonne: valeur_float} pour la dernière ligne valide.

        Raises:
            ParseError: Si aucune ligne ne correspond ou si des colonnes manquent.
        """
        reader = csv.DictReader(io.StringIO(content), delimiter=CSV_SEPARATOR)
        rows = [
            row
            for row in reader
            if row.get("P_SOUSCRITE", "").strip() == str(power_kva)
        ]

        if not rows:
            raise ParseError(
                f"Aucune ligne trouvée pour P_SOUSCRITE={power_kva} dans le CSV"
            )

        last_row = rows[-1]  # dernière ligne = tarif en vigueur

        missing = required_cols - last_row.keys()
        if missing:
            raise ParseError(f"Colonnes manquantes dans le CSV : {missing}")

        result: dict[str, float] = {}
        for col in required_cols - {"P_SOUSCRITE"}:
            raw = last_row[col].strip().replace(",", ".")
            try:
                result[col] = float(raw)
            except ValueError as err:
                raise ParseError(
                    f"Valeur non numérique pour la colonne {col!r} : {raw!r}"
                ) from err

        return result

    async def get_tarifs_tempo(self, power_kva: int) -> dict[str, float]:
        """Retourne les tarifs Tempo €/kWh et l'abonnement mensuel pour la puissance donnée.

        Colonnes retournées :
          PART_FIXE_TTC          → abonnement annuel €/an (÷12 pour €/mois)
          PART_VARIABLE_HCBleu_TTC, PART_VARIABLE_HPBleu_TTC
          PART_VARIABLE_HCBlanc_TTC, PART_VARIABLE_HPBlanc_TTC
          PART_VARIABLE_HCRouge_TTC, PART_VARIABLE_HPRouge_TTC
        """
        content = await self._download_csv(URL_DATAGOUV_TEMPO)
        data = self._parse_csv(content, CSV_REQUIRED_COLS_TEMPO, power_kva)
        _LOGGER.debug("Tarifs Tempo chargés pour %d kVA", power_kva)
        return data

    async def get_tarifs_hchp(self, power_kva: int) -> dict[str, float]:
        """Retourne les tarifs HP/HC €/kWh et l'abonnement mensuel.

        Colonnes retournées :
          PART_FIXE_TTC            → abonnement annuel €/an
          PART_VARIABLE_HC_TTC     → tarif HC €/kWh
          PART_VARIABLE_HP_TTC     → tarif HP €/kWh
        """
        content = await self._download_csv(URL_DATAGOUV_HCHP_POWER)
        data = self._parse_csv(content, CSV_REQUIRED_COLS_HCHP, power_kva)
        _LOGGER.debug("Tarifs HP/HC chargés pour %d kVA", power_kva)
        return data

    async def get_tarifs_base(self, power_kva: int) -> dict[str, float]:
        """Retourne le tarif Base €/kWh et l'abonnement mensuel.

        Colonnes retournées :
          PART_FIXE_TTC       → abonnement annuel €/an
          PART_VARIABLE_TTC   → tarif kWh TTC €/kWh
        """
        content = await self._download_csv(URL_DATAGOUV_BASE_HCHP)
        data = self._parse_csv(content, CSV_REQUIRED_COLS_BASE, power_kva)
        _LOGGER.debug("Tarifs Base chargés pour %d kVA", power_kva)
        return data
