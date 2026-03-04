"""Tests pour le coordinator EDF Tempo."""

from __future__ import annotations

from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.edf_tempo.const import (
    COLOR_BLEU,
    COLOR_BLANC,
    COLOR_INCONNU,
    COLOR_ROUGE,
    CONF_CONTRACT_TYPE,
    CONF_HC_RANGES,
    CONF_POWER_KVA,
    CONTRACT_BASE,
    CONTRACT_HPHC,
    CONTRACT_TEMPO,
    MAX_JOURS_BLANC,
    MAX_JOURS_BLEU,
    MAX_JOURS_ROUGE,
    PERIOD_HC,
    PERIOD_HP,
)
from custom_components.edf_tempo.coordinator import (
    EDFTempoCoordinator,
    is_hc_period,
    TIMEZONE_PARIS,
)
from custom_components.edf_tempo.exceptions import CannotConnect, InvalidAuth


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_ha_session():
    """Patch async_get_clientsession pour tous les tests du module."""
    with patch(
        "custom_components.edf_tempo.coordinator.async_get_clientsession",
        return_value=MagicMock(),
    ):
        yield


def _make_coordinator(mock_hass, contract_type, power_kva=6, hc_ranges="22:00-06:00"):
    """Helper pour créer un coordinator avec un contrat spécifique."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        CONF_CONTRACT_TYPE: contract_type,
        CONF_POWER_KVA: power_kva,
        CONF_HC_RANGES: hc_ranges,
    }
    entry.options = {}
    return EDFTempoCoordinator(mock_hass, entry)


# ---------------------------------------------------------------------------
# Tests is_hc_period
# ---------------------------------------------------------------------------


def test_is_hc_period_dans_plage():
    """23h00 avec plage 22:00-06:00 → HC."""
    now = datetime(2026, 1, 15, 23, 0, tzinfo=TIMEZONE_PARIS)
    assert is_hc_period("22:00-06:00", now) is True


def test_is_hc_period_hors_plage():
    """14h00 avec plage 22:00-06:00 → HP."""
    now = datetime(2026, 1, 15, 14, 0, tzinfo=TIMEZONE_PARIS)
    assert is_hc_period("22:00-06:00", now) is False


def test_is_hc_period_cross_midnight():
    """02h00 avec plage 22:00-06:00 → HC (après minuit)."""
    now = datetime(2026, 1, 15, 2, 0, tzinfo=TIMEZONE_PARIS)
    assert is_hc_period("22:00-06:00", now) is True


# ---------------------------------------------------------------------------
# Tests refresh contrats
# ---------------------------------------------------------------------------


async def test_refresh_tempo_success(mock_hass):
    """Contrat Tempo — vérifie toutes les clés de coordinator.data."""
    coordinator = _make_coordinator(mock_hass, CONTRACT_TEMPO)

    with (
        patch.object(coordinator, "_fetch_tarifs", new_callable=AsyncMock) as mock_tarifs,
        patch.object(coordinator, "_fetch_couleurs", new_callable=AsyncMock) as mock_couleurs,
        patch(
            "custom_components.edf_tempo.coordinator.is_hc_period", return_value=True
        ),
    ):
        mock_tarifs.return_value = {
            "abonnement_mensuel": 13.0,
            "tarif_bleu_hc": 0.1056,
            "tarif_bleu_hp": 0.1369,
            "tarif_blanc_hc": 0.1246,
            "tarif_blanc_hp": 0.1654,
            "tarif_rouge_hc": 0.1328,
            "tarif_rouge_hp": 0.7562,
        }
        mock_couleurs.return_value = {
            "couleur_aujourd_hui": COLOR_BLEU,
            "couleur_demain": COLOR_BLANC,
            "jours_bleus_consommes": 3,
            "jours_bleus_restants": MAX_JOURS_BLEU - 3,
            "jours_blancs_consommes": 1,
            "jours_blancs_restants": MAX_JOURS_BLANC - 1,
            "jours_rouges_consommes": 1,
            "jours_rouges_restants": MAX_JOURS_ROUGE - 1,
        }

        data = await coordinator._async_update_data()

    assert data["couleur_aujourd_hui"] == COLOR_BLEU
    assert data["couleur_demain"] == COLOR_BLANC
    assert data["abonnement_mensuel"] == 13.0
    assert data["tarif_bleu_hc"] == pytest.approx(0.1056)
    assert data["periode_actuelle"] == PERIOD_HC
    assert data["tarif_actuel"] == pytest.approx(0.1056)
    assert data["jours_bleus_consommes"] == 3
    assert data["jours_bleus_restants"] == MAX_JOURS_BLEU - 3
    assert data["jours_rouges_consommes"] == 1


async def test_refresh_base_no_colors(mock_hass):
    """Contrat Base — pas d'appel couleur ni historique."""
    coordinator = _make_coordinator(mock_hass, CONTRACT_BASE)

    with patch.object(coordinator, "_fetch_tarifs", new_callable=AsyncMock) as mock_tarifs:
        mock_tarifs.return_value = {
            "abonnement_mensuel": 10.0,
            "tarif_base": 0.2516,
        }

        data = await coordinator._async_update_data()

    assert data["tarif_base"] == pytest.approx(0.2516)
    assert data["abonnement_mensuel"] == pytest.approx(10.0)
    assert "couleur_aujourd_hui" not in data
    assert "periode_actuelle" not in data
    assert "jours_bleus_consommes" not in data


async def test_refresh_hchp_no_counters(mock_hass):
    """Contrat HPHC — tarifs HP/HC + période, pas de compteurs saison."""
    coordinator = _make_coordinator(mock_hass, CONTRACT_HPHC)

    with (
        patch.object(coordinator, "_fetch_tarifs", new_callable=AsyncMock) as mock_tarifs,
        patch(
            "custom_components.edf_tempo.coordinator.is_hc_period", return_value=False
        ),
    ):
        mock_tarifs.return_value = {
            "abonnement_mensuel": 12.0,
            "tarif_hc": 0.1828,
            "tarif_hp": 0.2460,
        }

        data = await coordinator._async_update_data()

    assert data["tarif_hc"] == pytest.approx(0.1828)
    assert data["tarif_hp"] == pytest.approx(0.2460)
    assert data["periode_actuelle"] == PERIOD_HP
    assert data["tarif_actuel"] == pytest.approx(0.2460)
    assert "couleur_aujourd_hui" not in data
    assert "jours_bleus_consommes" not in data


# ---------------------------------------------------------------------------
# Tests fallback / erreurs
# ---------------------------------------------------------------------------


async def test_fallback_couleur_cache(mock_hass):
    """CannotConnect sur couleurs avec cache → couleurs ET compteurs conservés."""
    coordinator = _make_coordinator(mock_hass, CONTRACT_TEMPO)
    # Simuler un cache existant avec compteurs
    coordinator.data = {
        "couleur_aujourd_hui": COLOR_ROUGE,
        "couleur_demain": COLOR_BLEU,
        "abonnement_mensuel": 13.0,
        "tarif_bleu_hc": 0.1056,
        "jours_bleus_consommes": 10,
        "jours_bleus_restants": MAX_JOURS_BLEU - 10,
        "jours_blancs_consommes": 2,
        "jours_blancs_restants": MAX_JOURS_BLANC - 2,
        "jours_rouges_consommes": 1,
        "jours_rouges_restants": MAX_JOURS_ROUGE - 1,
    }

    with (
        patch.object(coordinator, "_fetch_tarifs", new_callable=AsyncMock) as mock_tarifs,
        patch.object(
            coordinator, "_fetch_couleurs", new_callable=AsyncMock, side_effect=CannotConnect("timeout")
        ),
        patch(
            "custom_components.edf_tempo.coordinator.is_hc_period", return_value=True
        ),
    ):
        mock_tarifs.return_value = {
            "abonnement_mensuel": 13.0,
            "tarif_bleu_hc": 0.1056,
            "tarif_bleu_hp": 0.1369,
            "tarif_blanc_hc": 0.1246,
            "tarif_blanc_hp": 0.1654,
            "tarif_rouge_hc": 0.1328,
            "tarif_rouge_hp": 0.7562,
        }

        data = await coordinator._async_update_data()

    # Couleurs fallback depuis le cache
    assert data["couleur_aujourd_hui"] == COLOR_ROUGE
    assert data["couleur_demain"] == COLOR_BLEU
    # Compteurs fallback depuis le cache
    assert data["jours_bleus_consommes"] == 10
    assert data["jours_bleus_restants"] == MAX_JOURS_BLEU - 10
    assert data["jours_rouges_consommes"] == 1
    # Tarifs frais
    assert data["abonnement_mensuel"] == pytest.approx(13.0)


async def test_first_refresh_failure(mock_hass):
    """self.data est None + erreur tarifs → UpdateFailed."""
    coordinator = _make_coordinator(mock_hass, CONTRACT_TEMPO)
    assert coordinator.data is None

    with (
        patch.object(
            coordinator, "_fetch_tarifs", new_callable=AsyncMock, side_effect=CannotConnect("down")
        ),
        pytest.raises(UpdateFailed, match="Impossible de charger les tarifs"),
    ):
        await coordinator._async_update_data()


async def test_invalid_auth_reauth(mock_hass):
    """InvalidAuth → async_start_reauth appelé + UpdateFailed."""
    coordinator = _make_coordinator(mock_hass, CONTRACT_TEMPO)

    with (
        patch.object(
            coordinator, "_fetch_tarifs", new_callable=AsyncMock, side_effect=InvalidAuth("401")
        ),
        pytest.raises(UpdateFailed, match="Authentification invalide"),
    ):
        await coordinator._async_update_data()

    coordinator._entry.async_start_reauth.assert_called_once_with(mock_hass)


# ---------------------------------------------------------------------------
# Tests tarif_actuel
# ---------------------------------------------------------------------------


async def test_tarif_actuel_tempo_bleu_hc(mock_hass):
    """Couleur Bleu + HC → tarif_bleu_hc."""
    coordinator = _make_coordinator(mock_hass, CONTRACT_TEMPO)

    with (
        patch.object(coordinator, "_fetch_tarifs", new_callable=AsyncMock) as mock_tarifs,
        patch.object(coordinator, "_fetch_couleurs", new_callable=AsyncMock) as mock_couleurs,
        patch(
            "custom_components.edf_tempo.coordinator.is_hc_period", return_value=True
        ),
    ):
        mock_tarifs.return_value = {
            "abonnement_mensuel": 13.0,
            "tarif_bleu_hc": 0.1056,
            "tarif_bleu_hp": 0.1369,
            "tarif_blanc_hc": 0.1246,
            "tarif_blanc_hp": 0.1654,
            "tarif_rouge_hc": 0.1328,
            "tarif_rouge_hp": 0.7562,
        }
        mock_couleurs.return_value = {
            "couleur_aujourd_hui": COLOR_BLEU,
            "couleur_demain": COLOR_BLANC,
            "jours_bleus_consommes": 3,
            "jours_bleus_restants": MAX_JOURS_BLEU - 3,
            "jours_blancs_consommes": 0,
            "jours_blancs_restants": MAX_JOURS_BLANC,
            "jours_rouges_consommes": 0,
            "jours_rouges_restants": MAX_JOURS_ROUGE,
        }

        data = await coordinator._async_update_data()

    assert data["tarif_actuel"] == pytest.approx(0.1056)


# ---------------------------------------------------------------------------
# Tests compteurs saison
# ---------------------------------------------------------------------------


def test_compteurs_saison(mock_hass):
    """Historique 5 jours (3 Bleu, 1 Blanc, 1 Rouge) → restants corrects."""
    coordinator = _make_coordinator(mock_hass, CONTRACT_TEMPO)

    history = [
        (date(2025, 9, 1), COLOR_BLEU),
        (date(2025, 9, 2), COLOR_BLEU),
        (date(2025, 9, 3), COLOR_BLEU),
        (date(2025, 9, 4), COLOR_BLANC),
        (date(2025, 9, 5), COLOR_ROUGE),
    ]

    counters = coordinator._compute_counters(history)

    assert counters["jours_bleus_consommes"] == 3
    assert counters["jours_bleus_restants"] == MAX_JOURS_BLEU - 3
    assert counters["jours_blancs_consommes"] == 1
    assert counters["jours_blancs_restants"] == MAX_JOURS_BLANC - 1
    assert counters["jours_rouges_consommes"] == 1
    assert counters["jours_rouges_restants"] == MAX_JOURS_ROUGE - 1
