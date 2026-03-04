"""Tests pour le Config Flow et Options Flow EDF Tempo."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.edf_tempo.const import (
    CONF_CONTRACT_TYPE,
    CONF_HC_RANGES,
    CONF_POWER_KVA,
    CONF_SCAN_INTERVAL,
    CONTRACT_BASE,
    CONTRACT_HPHC,
    CONTRACT_TEMPO,
)
from custom_components.edf_tempo.config_flow import (
    EDFTempoConfigFlow,
    EDFTempoOptionsFlow,
    validate_hc_ranges,
)

import voluptuous as vol


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_flow(hass=None):
    """Crée un ConfigFlow initialisé."""
    flow = EDFTempoConfigFlow()
    flow.hass = hass or MagicMock()
    return flow


def _create_options_flow(contract_type=CONTRACT_TEMPO, data=None):
    """Crée un OptionsFlow avec une entry mock."""
    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.data = data or {
        CONF_CONTRACT_TYPE: contract_type,
        CONF_POWER_KVA: 6,
        CONF_HC_RANGES: "22:00-06:00",
        CONF_SCAN_INTERVAL: "6h",
    }
    options_flow = EDFTempoOptionsFlow(entry)
    options_flow.hass = MagicMock()
    options_flow.hass.config_entries = MagicMock()
    options_flow.hass.config_entries.async_update_entry = MagicMock()
    options_flow.hass.config_entries.async_reload = AsyncMock()
    return options_flow


# ---------------------------------------------------------------------------
# Tests Config Flow — parcours complets
# ---------------------------------------------------------------------------


async def test_config_flow_base_complete():
    """Contrat Base → 3 étapes (pas d'étape HC), entry créée."""
    flow = _create_flow()

    # Étape 1 : contrat
    result = await flow.async_step_user({CONF_CONTRACT_TYPE: CONTRACT_BASE})
    assert result["type"] == "form"
    assert result["step_id"] == "power"

    # Étape 2 : puissance → saute HC, va directement à scan_interval
    result = await flow.async_step_power({CONF_POWER_KVA: 9})
    assert result["type"] == "form"
    assert result["step_id"] == "scan_interval"

    # Étape 3 : fréquence → création entry
    result = await flow.async_step_scan_interval({CONF_SCAN_INTERVAL: "1h"})
    assert result["type"] == "create_entry"
    assert result["title"] == "EDF BASE 9 kVA"
    assert result["data"][CONF_CONTRACT_TYPE] == CONTRACT_BASE
    assert result["data"][CONF_POWER_KVA] == 9
    assert result["data"][CONF_SCAN_INTERVAL] == "1h"
    assert CONF_HC_RANGES not in result["data"]


async def test_config_flow_tempo_complete():
    """Contrat Tempo → 4 étapes complètes, entry créée."""
    flow = _create_flow()

    # Étape 1 : contrat
    result = await flow.async_step_user({CONF_CONTRACT_TYPE: CONTRACT_TEMPO})
    assert result["type"] == "form"
    assert result["step_id"] == "power"

    # Étape 2 : puissance
    result = await flow.async_step_power({CONF_POWER_KVA: 6})
    assert result["type"] == "form"
    assert result["step_id"] == "hc_ranges"

    # Étape 3 : plages HC
    result = await flow.async_step_hc_ranges({CONF_HC_RANGES: "22:00-06:00"})
    assert result["type"] == "form"
    assert result["step_id"] == "scan_interval"

    # Étape 4 : fréquence → création entry
    result = await flow.async_step_scan_interval({CONF_SCAN_INTERVAL: "6h"})
    assert result["type"] == "create_entry"
    assert result["title"] == "EDF TEMPO 6 kVA"
    assert result["data"][CONF_CONTRACT_TYPE] == CONTRACT_TEMPO
    assert result["data"][CONF_HC_RANGES] == "22:00-06:00"


async def test_config_flow_hphc_complete():
    """Contrat HPHC → 4 étapes, plages HC multiples acceptées."""
    flow = _create_flow()

    result = await flow.async_step_user({CONF_CONTRACT_TYPE: CONTRACT_HPHC})
    result = await flow.async_step_power({CONF_POWER_KVA: 12})
    assert result["step_id"] == "hc_ranges"

    result = await flow.async_step_hc_ranges(
        {CONF_HC_RANGES: "01:30-07:30, 12:30-14:30"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "scan_interval"

    result = await flow.async_step_scan_interval({CONF_SCAN_INTERVAL: "15min"})
    assert result["type"] == "create_entry"
    assert result["data"][CONF_HC_RANGES] == "01:30-07:30, 12:30-14:30"


# ---------------------------------------------------------------------------
# Tests validation HC
# ---------------------------------------------------------------------------


async def test_config_flow_invalid_hc_format():
    """Format HC invalide → erreur affichée, reste sur l'étape."""
    flow = _create_flow()
    flow._data = {CONF_CONTRACT_TYPE: CONTRACT_TEMPO, CONF_POWER_KVA: 6}

    # Format complètement invalide
    result = await flow.async_step_hc_ranges({CONF_HC_RANGES: "abc"})
    assert result["type"] == "form"
    assert result["step_id"] == "hc_ranges"
    assert result["errors"]["base"] == "invalid_hc_format"

    # Format regex OK mais heure invalide (25:00)
    result = await flow.async_step_hc_ranges({CONF_HC_RANGES: "25:00-06:00"})
    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_hc_format"


def test_validate_hc_ranges_valid():
    """Formats HC valides acceptés."""
    assert validate_hc_ranges("22:00-06:00") == "22:00-06:00"
    assert validate_hc_ranges("01:30-07:30, 12:30-14:30") == "01:30-07:30, 12:30-14:30"
    assert validate_hc_ranges("  22:00-06:00  ") == "22:00-06:00"


def test_validate_hc_ranges_invalid():
    """Formats HC invalides rejetés."""
    with pytest.raises(vol.Invalid):
        validate_hc_ranges("abc")
    with pytest.raises(vol.Invalid):
        validate_hc_ranges("22:00")
    with pytest.raises(vol.Invalid):
        validate_hc_ranges("25:00-06:00")


# ---------------------------------------------------------------------------
# Tests valeurs par défaut
# ---------------------------------------------------------------------------


async def test_config_flow_default_values():
    """Vérifier les valeurs par défaut (6h scan, 22:00-06:00 HC)."""
    flow = _create_flow()

    # Étape user → formulaire affiché
    result = await flow.async_step_user(None)
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    # Étape power → défaut 6 kVA
    result = await flow.async_step_user({CONF_CONTRACT_TYPE: CONTRACT_TEMPO})
    result = await flow.async_step_power(None)
    assert result["type"] == "form"
    schema_keys = list(result["data_schema"].schema.keys())
    power_key = schema_keys[0]
    assert power_key.default() == 6

    # Étape hc_ranges → défaut 22:00-06:00
    flow._data = {CONF_CONTRACT_TYPE: CONTRACT_TEMPO, CONF_POWER_KVA: 6}
    result = await flow.async_step_hc_ranges(None)
    schema_keys = list(result["data_schema"].schema.keys())
    hc_key = schema_keys[0]
    assert hc_key.default() == "22:00-06:00"


# ---------------------------------------------------------------------------
# Tests Options Flow
# ---------------------------------------------------------------------------


async def test_options_flow_update():
    """Options Flow → modifier fréquence et puissance."""
    options_flow = _create_options_flow(CONTRACT_TEMPO)

    result = await options_flow.async_step_init(
        {CONF_POWER_KVA: 9, CONF_SCAN_INTERVAL: "1h", CONF_HC_RANGES: "23:00-07:00"}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"

    # Vérifier que async_update_entry a été appelé avec les bonnes données
    options_flow.hass.config_entries.async_update_entry.assert_called_once()
    call_args = options_flow.hass.config_entries.async_update_entry.call_args
    new_data = call_args.kwargs["data"]
    assert new_data[CONF_POWER_KVA] == 9
    assert new_data[CONF_SCAN_INTERVAL] == "1h"
    assert new_data[CONF_HC_RANGES] == "23:00-07:00"
    # contract_type preserved from original entry
    assert new_data[CONF_CONTRACT_TYPE] == CONTRACT_TEMPO


async def test_options_flow_base_no_hc():
    """Contrat Base → pas de champ HC dans le formulaire options."""
    options_flow = _create_options_flow(
        CONTRACT_BASE,
        data={
            CONF_CONTRACT_TYPE: CONTRACT_BASE,
            CONF_POWER_KVA: 6,
            CONF_SCAN_INTERVAL: "6h",
        },
    )

    result = await options_flow.async_step_init(None)
    assert result["type"] == "form"
    # Vérifier que HC n'est PAS dans le schema
    schema_keys = {str(k) for k in result["data_schema"].schema.keys()}
    assert CONF_HC_RANGES not in schema_keys
    assert CONF_POWER_KVA in schema_keys
    assert CONF_SCAN_INTERVAL in schema_keys
