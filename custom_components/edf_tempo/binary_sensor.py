"""Binary sensor entities pour l'intégration EDF Tempo."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CONTRACT_TYPE,
    CONTRACT_BASE,
    CONTRACT_HPHC,
    CONTRACT_TEMPO,
    DEVICE_NAME_MAP,
    DOMAIN,
    PERIOD_HC,
)

_CONTRACT_PREFIX = {
    CONTRACT_HPHC: "edf_hphc",
    CONTRACT_TEMPO: "edf_tempo",
}

HEURES_CREUSES_DESCRIPTION = BinarySensorEntityDescription(
    key="heures_creuses",
    translation_key="heures_creuses",
    icon="mdi:clock-time-eight",
)


class EDFTempoBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor Heures Creuses pour EDF Tempo."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: BinarySensorEntityDescription,
        entity_id_prefix: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self.entity_id = f"binary_sensor.{entity_id_prefix}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=DEVICE_NAME_MAP[coordinator.config_entry.data[CONF_CONTRACT_TYPE]],
            manufacturer="EDF",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool | None:
        """True si la période actuelle est Heures Creuses."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("periode_actuelle") == PERIOD_HC

    @property
    def available(self) -> bool:
        """Disponible si le coordinator a réussi sa dernière mise à jour."""
        return self.coordinator.last_update_success


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure le binary sensor HC selon le type de contrat."""
    contract = entry.data[CONF_CONTRACT_TYPE]

    if contract == CONTRACT_BASE:
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = _CONTRACT_PREFIX[contract]

    async_add_entities(
        [EDFTempoBinarySensor(coordinator, HEURES_CREUSES_DESCRIPTION, prefix)]
    )
