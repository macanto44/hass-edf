"""Tests pour les binary sensor entities EDF Tempo."""

from __future__ import annotations

from custom_components.edf_tempo.const import (
    CONTRACT_BASE,
    CONTRACT_HPHC,
    CONTRACT_TEMPO,
    DOMAIN,
    PERIOD_HC,
    PERIOD_HP,
)
from custom_components.edf_tempo.binary_sensor import (
    HEURES_CREUSES_DESCRIPTION,
    EDFTempoBinarySensor,
    async_setup_entry,
)
from conftest import collect_entities, make_mock_coordinator


# ---------------------------------------------------------------------------
# Tests création
# ---------------------------------------------------------------------------


async def test_binary_sensor_tempo_created(mock_hass):
    """Contrat Tempo → 1 binary_sensor créé."""
    coordinator = make_mock_coordinator(CONTRACT_TEMPO, data={
        "periode_actuelle": PERIOD_HC,
    })
    entities = await collect_entities(mock_hass, coordinator, CONTRACT_TEMPO, async_setup_entry)
    assert len(entities) == 1
    assert entities[0].entity_description.key == "heures_creuses"


async def test_binary_sensor_base_not_created(mock_hass):
    """Contrat Base → 0 binary_sensor."""
    coordinator = make_mock_coordinator(CONTRACT_BASE)
    entities = await collect_entities(mock_hass, coordinator, CONTRACT_BASE, async_setup_entry)
    assert len(entities) == 0


# ---------------------------------------------------------------------------
# Tests is_on
# ---------------------------------------------------------------------------


async def test_binary_sensor_is_on_hc():
    """periode_actuelle == HC → is_on = True."""
    coordinator = make_mock_coordinator(CONTRACT_TEMPO, data={
        "periode_actuelle": PERIOD_HC,
    })
    sensor = EDFTempoBinarySensor(coordinator, HEURES_CREUSES_DESCRIPTION, "edf_tempo")
    assert sensor.is_on is True


async def test_binary_sensor_is_on_hp():
    """periode_actuelle == HP → is_on = False."""
    coordinator = make_mock_coordinator(CONTRACT_TEMPO, data={
        "periode_actuelle": PERIOD_HP,
    })
    sensor = EDFTempoBinarySensor(coordinator, HEURES_CREUSES_DESCRIPTION, "edf_tempo")
    assert sensor.is_on is False


# ---------------------------------------------------------------------------
# Tests DeviceInfo
# ---------------------------------------------------------------------------


async def test_binary_sensor_device_info_tempo():
    """Contrat Tempo → device_info name='EDF Tempo'."""
    coordinator = make_mock_coordinator(CONTRACT_TEMPO, data={})
    sensor = EDFTempoBinarySensor(coordinator, HEURES_CREUSES_DESCRIPTION, "edf_tempo")
    assert sensor.device_info is not None
    assert sensor.device_info["identifiers"] == {(DOMAIN, "test_entry_123")}
    assert sensor.device_info["name"] == "EDF Tempo"
    assert sensor.device_info["manufacturer"] == "EDF"


async def test_binary_sensor_device_info_hphc():
    """Contrat HPHC → device_info name='EDF HP/HC'."""
    coordinator = make_mock_coordinator(CONTRACT_HPHC, data={})
    sensor = EDFTempoBinarySensor(coordinator, HEURES_CREUSES_DESCRIPTION, "edf_hphc")
    assert sensor.device_info is not None
    assert sensor.device_info["name"] == "EDF HP/HC"
