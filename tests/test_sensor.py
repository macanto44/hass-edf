"""Tests pour les sensor entities EDF Tempo."""

from __future__ import annotations

import pytest

from custom_components.edf_tempo.const import (
    CONTRACT_BASE,
    CONTRACT_HPHC,
    CONTRACT_TEMPO,
    PERIOD_HC,
)
from custom_components.edf_tempo.sensor import (
    BASE_ONLY_SENSORS,
    COMMON_SENSORS,
    HCHP_SHARED_SENSORS,
    HPHC_ONLY_SENSORS,
    TEMPO_SENSORS,
    EDFTempoSensor,
    async_setup_entry,
)
from conftest import collect_entities, make_mock_coordinator


# ---------------------------------------------------------------------------
# Tests création d'entités par contrat
# ---------------------------------------------------------------------------


async def test_sensor_tempo_entities_created(mock_hass):
    """Contrat Tempo → 14 sensors (1 common + 2 shared HC/HP + 11 tempo)."""
    expected_count = len(COMMON_SENSORS) + len(HCHP_SHARED_SENSORS) + len(TEMPO_SENSORS)
    assert expected_count == 14
    coordinator = make_mock_coordinator(CONTRACT_TEMPO, data={
        "abonnement_mensuel": 13.0,
        "tarif_actuel": 0.1056, "periode_actuelle": PERIOD_HC,
        "couleur_aujourd_hui": "Bleu", "couleur_demain": "Blanc",
        "tarif_bleu_hc": 0.1056, "tarif_bleu_hp": 0.1369,
        "tarif_blanc_hc": 0.1246, "tarif_blanc_hp": 0.1654,
        "tarif_rouge_hc": 0.1328, "tarif_rouge_hp": 0.7562,
        "jours_bleus_restants": 297, "jours_blancs_restants": 42,
        "jours_rouges_restants": 21,
    })
    entities = await collect_entities(mock_hass, coordinator, CONTRACT_TEMPO, async_setup_entry)
    assert len(entities) == expected_count


async def test_sensor_base_entities_created(mock_hass):
    """Contrat Base → 2 sensors (1 common + 1 base-only)."""
    coordinator = make_mock_coordinator(CONTRACT_BASE, data={
        "tarif_base": 0.2516, "abonnement_mensuel": 10.0,
    })
    entities = await collect_entities(mock_hass, coordinator, CONTRACT_BASE, async_setup_entry)
    expected_count = len(COMMON_SENSORS) + len(BASE_ONLY_SENSORS)
    assert expected_count == 2
    assert len(entities) == expected_count
    keys = {e.entity_description.key for e in entities}
    assert keys == {"tarif_ttc", "abonnement_mensuel"}


async def test_sensor_hphc_entities_created(mock_hass):
    """Contrat HPHC → 5 sensors (1 common + 2 shared + 2 hphc-only)."""
    coordinator = make_mock_coordinator(CONTRACT_HPHC, data={
        "abonnement_mensuel": 12.0,
        "tarif_hc": 0.1828, "tarif_hp": 0.2460,
        "tarif_actuel": 0.1828, "periode_actuelle": PERIOD_HC,
    })
    entities = await collect_entities(mock_hass, coordinator, CONTRACT_HPHC, async_setup_entry)
    expected_count = len(COMMON_SENSORS) + len(HCHP_SHARED_SENSORS) + len(HPHC_ONLY_SENSORS)
    assert expected_count == 5
    assert len(entities) == expected_count


# ---------------------------------------------------------------------------
# Tests propriétés
# ---------------------------------------------------------------------------


async def test_sensor_native_value():
    """native_value lit coordinator.data[key] directement."""
    coordinator = make_mock_coordinator(CONTRACT_TEMPO, data={
        "tarif_bleu_hc": 0.1056,
    })
    sensor = EDFTempoSensor(coordinator, TEMPO_SENSORS[2], "edf_tempo")  # tarif_bleu_hc
    assert sensor.native_value == pytest.approx(0.1056)


async def test_sensor_unique_id_format():
    """unique_id suit le format {entry_id}_{key}."""
    coordinator = make_mock_coordinator(CONTRACT_BASE, data={})
    sensor = EDFTempoSensor(coordinator, BASE_ONLY_SENSORS[0], "edf_base")
    assert sensor.unique_id == "test_entry_123_tarif_ttc"


async def test_sensor_available_false():
    """coordinator.last_update_success = False → available = False."""
    coordinator = make_mock_coordinator(CONTRACT_BASE, data={})
    coordinator.last_update_success = False
    sensor = EDFTempoSensor(coordinator, BASE_ONLY_SENSORS[0], "edf_base")
    assert sensor.available is False
