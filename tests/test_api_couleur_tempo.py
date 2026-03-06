"""Tests pour CouleurTempoClient (api_couleur_tempo.py)."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock

import aiohttp
import pytest

from custom_components.edf_tempo.api_couleur_tempo import CouleurTempoClient
from custom_components.edf_tempo.exceptions import (
    CannotConnect,
    InvalidAuth,
    RateLimitExceeded,
)


async def test_get_today_bleu(mock_aiohttp_session):
    """codeJour=1 → 'Bleu'."""
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.json = AsyncMock(
        return_value={"codeJour": 1}
    )
    client = CouleurTempoClient(mock_aiohttp_session)
    assert await client.get_today() == "Bleu"


async def test_get_today_blanc(mock_aiohttp_session):
    """codeJour=2 → 'Blanc'."""
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.json = AsyncMock(
        return_value={"codeJour": 2}
    )
    client = CouleurTempoClient(mock_aiohttp_session)
    assert await client.get_today() == "Blanc"


async def test_get_today_rouge(mock_aiohttp_session):
    """codeJour=3 → 'Rouge'."""
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.json = AsyncMock(
        return_value={"codeJour": 3}
    )
    client = CouleurTempoClient(mock_aiohttp_session)
    assert await client.get_today() == "Rouge"


async def test_get_today_inconnu(mock_aiohttp_session):
    """codeJour inconnu → 'Inconnu' sans lever d'exception."""
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.json = AsyncMock(
        return_value={"codeJour": 99}
    )
    client = CouleurTempoClient(mock_aiohttp_session)
    assert await client.get_today() == "Inconnu"


async def test_get_today_timeout(mock_aiohttp_session):
    """Timeout réseau → CannotConnect."""
    mock_aiohttp_session.get.side_effect = aiohttp.ServerTimeoutError()
    client = CouleurTempoClient(mock_aiohttp_session)
    with pytest.raises(CannotConnect):
        await client.get_today()


async def test_get_today_rate_limit(mock_aiohttp_session):
    """HTTP 429 → RateLimitExceeded."""
    mock_aiohttp_session.get.return_value.status = 429
    client = CouleurTempoClient(mock_aiohttp_session)
    with pytest.raises(RateLimitExceeded):
        await client.get_today()


async def test_get_today_invalid_auth(mock_aiohttp_session):
    """HTTP 401 → InvalidAuth."""
    mock_aiohttp_session.get.return_value.status = 401
    client = CouleurTempoClient(mock_aiohttp_session)
    with pytest.raises(InvalidAuth):
        await client.get_today()


async def test_get_tomorrow_inconnu_si_vide(mock_aiohttp_session):
    """Réponse sans codeJour → 'Inconnu' (couleur non encore publiée)."""
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.json = AsyncMock(return_value={})
    client = CouleurTempoClient(mock_aiohttp_session)
    assert await client.get_tomorrow() == "Inconnu"


async def test_get_now(mock_aiohttp_session):
    """get_now retourne le dict complet de /api/now sans transformation."""
    expected = {
        "codeCouleur": 1,
        "codeHoraire": 1,
        "tarifKwh": 0.1612,
        "libTarif": "Bleu-HP",
    }
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.json = AsyncMock(return_value=expected)
    client = CouleurTempoClient(mock_aiohttp_session)
    result = await client.get_now()
    assert result == expected


async def test_get_season_history(mock_aiohttp_session):
    """Plage de 3 jours → liste de 3 tuples (date, couleur) dans l'ordre."""
    mock_aiohttp_session.get.return_value.status = 200
    mock_aiohttp_session.get.return_value.json = AsyncMock(
        side_effect=[
            {"codeJour": 1},
            {"codeJour": 2},
            {"codeJour": 3},
        ]
    )
    client = CouleurTempoClient(mock_aiohttp_session)
    start = date(2025, 9, 1)
    end = date(2025, 9, 3)

    result = await client.get_season_history(start, end)

    assert len(result) == 3
    assert result[0] == (date(2025, 9, 1), "Bleu")
    assert result[1] == (date(2025, 9, 2), "Blanc")
    assert result[2] == (date(2025, 9, 3), "Rouge")
