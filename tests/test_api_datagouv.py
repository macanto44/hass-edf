"""Tests pour DataGouvClient (api_datagouv.py)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import aiohttp
import pytest

from custom_components.edf_tempo.api_datagouv import DataGouvClient
from custom_components.edf_tempo.const import (
    CSV_REQUIRED_COLS_HCHP,
    CSV_REQUIRED_COLS_TEMPO,
)
from custom_components.edf_tempo.exceptions import CannotConnect, ParseError

_CSV_TEMPO_HEADER = (
    "P_SOUSCRITE;PART_FIXE_TTC;"
    "PART_VARIABLE_HCBleu_TTC;PART_VARIABLE_HPBleu_TTC;"
    "PART_VARIABLE_HCBlanc_TTC;PART_VARIABLE_HPBlanc_TTC;"
    "PART_VARIABLE_HCRouge_TTC;PART_VARIABLE_HPRouge_TTC"
)

_CSV_HCHP_HEADER = (
    "P_SOUSCRITE;PART_FIXE_TTC;PART_VARIABLE_HC_TTC;PART_VARIABLE_HP_TTC"
)


def test_parse_csv_tempo_derniere_ligne(mock_aiohttp_session):
    """La dernière ligne pour P_SOUSCRITE=6 est retournée (tarif en vigueur)."""
    csv_content = (
        f"{_CSV_TEMPO_HEADER}\n"
        "6;100,00;0,0788;0,1269;0,1264;0,1654;0,1228;0,7562\n"
        "9;150,00;0,0788;0,1269;0,1264;0,1654;0,1228;0,7562\n"
        "6;120,00;0,0800;0,1300;0,1300;0,1700;0,1300;0,7700\n"
    )
    client = DataGouvClient(mock_aiohttp_session)
    result = client._parse_csv(csv_content, CSV_REQUIRED_COLS_TEMPO, 6)

    assert result["PART_FIXE_TTC"] == pytest.approx(120.0)
    assert result["PART_VARIABLE_HCBleu_TTC"] == pytest.approx(0.08)
    assert result["PART_VARIABLE_HPRouge_TTC"] == pytest.approx(0.77)


def test_parse_csv_colonne_manquante(mock_aiohttp_session):
    """CSV avec colonne requise absente → ParseError avec nom de la colonne."""
    # PART_VARIABLE_HPRouge_TTC manquante dans le header
    csv_content = (
        "P_SOUSCRITE;PART_FIXE_TTC;"
        "PART_VARIABLE_HCBleu_TTC;PART_VARIABLE_HPBleu_TTC;"
        "PART_VARIABLE_HCBlanc_TTC;PART_VARIABLE_HPBlanc_TTC;"
        "PART_VARIABLE_HCRouge_TTC\n"
        "6;100,00;0,0788;0,1269;0,1264;0,1654;0,1228\n"
    )
    client = DataGouvClient(mock_aiohttp_session)
    with pytest.raises(ParseError):
        client._parse_csv(csv_content, CSV_REQUIRED_COLS_TEMPO, 6)


def test_parse_csv_power_not_found(mock_aiohttp_session):
    """Aucune ligne pour la puissance demandée → ParseError."""
    csv_content = (
        f"{_CSV_TEMPO_HEADER}\n"
        "3;100,00;0,0788;0,1269;0,1264;0,1654;0,1228;0,7562\n"
    )
    client = DataGouvClient(mock_aiohttp_session)
    with pytest.raises(ParseError):
        client._parse_csv(csv_content, CSV_REQUIRED_COLS_TEMPO, 6)


async def test_get_tarifs_tempo_timeout(mock_aiohttp_session):
    """Timeout lors du téléchargement CSV → CannotConnect."""
    mock_aiohttp_session.get.side_effect = aiohttp.ServerTimeoutError()
    client = DataGouvClient(mock_aiohttp_session)
    with pytest.raises(CannotConnect):
        await client.get_tarifs_tempo(6)


async def test_get_tarifs_hchp(mock_aiohttp_session):
    """CSV HP/HC valide → dict avec PART_VARIABLE_HC_TTC et PART_VARIABLE_HP_TTC."""
    csv_content = (
        f"{_CSV_HCHP_HEADER}\n"
        "6;100,00;0,1056;0,1834\n"
    )
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.text = AsyncMock(return_value=csv_content)

    client = DataGouvClient(mock_aiohttp_session)
    result = await client.get_tarifs_hchp(6)

    assert result["PART_VARIABLE_HC_TTC"] == pytest.approx(0.1056)
    assert result["PART_VARIABLE_HP_TTC"] == pytest.approx(0.1834)
    assert result["PART_FIXE_TTC"] == pytest.approx(100.0)


async def test_get_tarifs_base(mock_aiohttp_session):
    """CSV Base valide → dict avec PART_VARIABLE_TTC et PART_FIXE_TTC."""
    csv_content = (
        "P_SOUSCRITE;PART_FIXE_TTC;PART_VARIABLE_TTC\n"
        "6;110,00;0,2516\n"
    )
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.text = AsyncMock(return_value=csv_content)

    client = DataGouvClient(mock_aiohttp_session)
    result = await client.get_tarifs_base(6)

    assert result["PART_VARIABLE_TTC"] == pytest.approx(0.2516)
    assert result["PART_FIXE_TTC"] == pytest.approx(110.0)
    assert "P_SOUSCRITE" not in result
