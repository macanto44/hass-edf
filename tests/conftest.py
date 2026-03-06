"""Shared pytest fixtures for EDF Tempo tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.edf_tarifs.const import (
    CONF_CONTRACT_TYPE,
    CONF_HC_RANGES,
    CONF_POWER_KVA,
    CONTRACT_TEMPO,
    DOMAIN,
)


@pytest.fixture
def mock_hass():
    """Return a mock HomeAssistant instance."""
    hass = MagicMock()
    hass.data = {}
    return hass


@pytest.fixture
def mock_config_entry():
    """Return a mock ConfigEntry pre-configured for Tempo contract."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id_123"
    entry.title = "EDF Tempo"
    entry.data = {
        CONF_CONTRACT_TYPE: CONTRACT_TEMPO,
        CONF_HC_RANGES: "22:00-06:00",
        CONF_POWER_KVA: 6,
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_aiohttp_session():
    """Return a mock aiohttp ClientSession."""
    session = MagicMock()
    response = AsyncMock()
    response.raise_for_status = AsyncMock()
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    session.get = MagicMock(return_value=response)
    return session


def make_mock_coordinator(contract_type, data=None):
    """Crée un mock coordinator avec les données spécifiées."""
    coordinator = MagicMock()
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_123"
    coordinator.config_entry.data = {
        CONF_CONTRACT_TYPE: contract_type,
    }
    coordinator.data = data or {}
    coordinator.last_update_success = True
    return coordinator


async def collect_entities(hass, coordinator, contract_type, setup_func):
    """Appelle async_setup_entry et collecte les entités créées."""
    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.data = {CONF_CONTRACT_TYPE: contract_type}

    hass.data = {DOMAIN: {entry.entry_id: coordinator}}

    entities = []
    await setup_func(hass, entry, lambda e: entities.extend(list(e)))
    return entities
