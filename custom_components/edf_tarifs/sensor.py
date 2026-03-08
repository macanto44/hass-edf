"""Sensor entities pour l'intégration EDF Tarifs."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COLOR_BLANC,
    COLOR_BLEU,
    COLOR_HEX_MAP,
    COLOR_INCONNU,
    COLOR_ROUGE,
    CONF_CONTRACT_TYPE,
    CONTRACT_BASE,
    CONTRACT_HPHC,
    CONTRACT_TEMPO,
    DEVICE_NAME_MAP,
    DOMAIN,
    PERIOD_HC,
    PERIOD_HP,
)


@dataclass(frozen=True, kw_only=True)
class EDFTempoSensorEntityDescription(SensorEntityDescription):
    """Description étendue pour les sensors EDF Tarifs."""

    coordinator_key: str


# ---------------------------------------------------------------------------
# Préfixe entity_id par contrat
# ---------------------------------------------------------------------------

_CONTRACT_PREFIX = {
    CONTRACT_BASE: "edf_base",
    CONTRACT_HPHC: "edf_hphc",
    CONTRACT_TEMPO: "edf_tempo",
}

# ---------------------------------------------------------------------------
# Descriptions déclaratives par contrat
# ---------------------------------------------------------------------------

# Sensors communs à tous les contrats
COMMON_SENSORS: tuple[EDFTempoSensorEntityDescription, ...] = (
    EDFTempoSensorEntityDescription(
        key="abonnement_mensuel",
        coordinator_key="abonnement_mensuel",
        translation_key="abonnement_mensuel",
        native_unit_of_measurement="€/mo",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
    ),
)

# Sensors exclusifs au contrat Base
BASE_ONLY_SENSORS: tuple[EDFTempoSensorEntityDescription, ...] = (
    EDFTempoSensorEntityDescription(
        key="tarif_ttc",
        coordinator_key="tarif_base",
        translation_key="tarif_ttc",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
)

# Sensors partagés HC/HP (HPHC + Tempo)
HCHP_SHARED_SENSORS: tuple[EDFTempoSensorEntityDescription, ...] = (
    EDFTempoSensorEntityDescription(
        key="tarif_actuel",
        coordinator_key="tarif_actuel",
        translation_key="tarif_actuel",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
    EDFTempoSensorEntityDescription(
        key="periode_actuelle",
        coordinator_key="periode_actuelle",
        translation_key="periode_actuelle",
        device_class=SensorDeviceClass.ENUM,
        options=[PERIOD_HC, PERIOD_HP],
    ),
)

# Sensors exclusifs au contrat HPHC
HPHC_ONLY_SENSORS: tuple[EDFTempoSensorEntityDescription, ...] = (
    EDFTempoSensorEntityDescription(
        key="tarif_hc",
        coordinator_key="tarif_hc",
        translation_key="tarif_hc",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
    EDFTempoSensorEntityDescription(
        key="tarif_hp",
        coordinator_key="tarif_hp",
        translation_key="tarif_hp",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
)

TEMPO_SENSORS: tuple[EDFTempoSensorEntityDescription, ...] = (
    EDFTempoSensorEntityDescription(
        key="couleur_aujourd_hui",
        coordinator_key="couleur_aujourd_hui",
        translation_key="couleur_aujourd_hui",
        device_class=SensorDeviceClass.ENUM,
        options=[COLOR_BLEU, COLOR_BLANC, COLOR_ROUGE, COLOR_INCONNU],
    ),
    EDFTempoSensorEntityDescription(
        key="couleur_demain",
        coordinator_key="couleur_demain",
        translation_key="couleur_demain",
        device_class=SensorDeviceClass.ENUM,
        options=[COLOR_BLEU, COLOR_BLANC, COLOR_ROUGE, COLOR_INCONNU],
    ),
    EDFTempoSensorEntityDescription(
        key="tarif_bleu_hc",
        coordinator_key="tarif_bleu_hc",
        translation_key="tarif_bleu_hc",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
    EDFTempoSensorEntityDescription(
        key="tarif_bleu_hp",
        coordinator_key="tarif_bleu_hp",
        translation_key="tarif_bleu_hp",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
    EDFTempoSensorEntityDescription(
        key="tarif_blanc_hc",
        coordinator_key="tarif_blanc_hc",
        translation_key="tarif_blanc_hc",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
    EDFTempoSensorEntityDescription(
        key="tarif_blanc_hp",
        coordinator_key="tarif_blanc_hp",
        translation_key="tarif_blanc_hp",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
    EDFTempoSensorEntityDescription(
        key="tarif_rouge_hc",
        coordinator_key="tarif_rouge_hc",
        translation_key="tarif_rouge_hc",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
    EDFTempoSensorEntityDescription(
        key="tarif_rouge_hp",
        coordinator_key="tarif_rouge_hp",
        translation_key="tarif_rouge_hp",
        native_unit_of_measurement="€/kWh",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
    ),
    EDFTempoSensorEntityDescription(
        key="jours_bleus_restants",
        coordinator_key="jours_bleus_restants",
        translation_key="jours_bleus_restants",
        native_unit_of_measurement="d",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    EDFTempoSensorEntityDescription(
        key="jours_blancs_restants",
        coordinator_key="jours_blancs_restants",
        translation_key="jours_blancs_restants",
        native_unit_of_measurement="d",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    EDFTempoSensorEntityDescription(
        key="jours_rouges_restants",
        coordinator_key="jours_rouges_restants",
        translation_key="jours_rouges_restants",
        native_unit_of_measurement="d",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

# Sensors visuels Tempo (cercle SVG coloré)
TEMPO_VISUAL_SENSORS: tuple[EDFTempoSensorEntityDescription, ...] = (
    EDFTempoSensorEntityDescription(
        key="couleur_aujourd_hui_visuel",
        coordinator_key="couleur_aujourd_hui",
        translation_key="couleur_aujourd_hui_visuel",
    ),
    EDFTempoSensorEntityDescription(
        key="couleur_demain_visuel",
        coordinator_key="couleur_demain",
        translation_key="couleur_demain_visuel",
    ),
)

_VISUAL_SENSOR_KEYS = {desc.key for desc in TEMPO_VISUAL_SENSORS}


class EDFTempoSensor(CoordinatorEntity, SensorEntity):
    """Sensor générique pour l'intégration EDF Tarifs."""

    entity_description: EDFTempoSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: EDFTempoSensorEntityDescription,
        entity_id_prefix: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self.entity_id = f"sensor.{entity_id_prefix}_{description.key}"
        self._coordinator_key = description.coordinator_key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=DEVICE_NAME_MAP[coordinator.config_entry.data[CONF_CONTRACT_TYPE]],
            manufacturer="EDF",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType:
        """Retourne la valeur depuis coordinator.data."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._coordinator_key)

    @property
    def available(self) -> bool:
        """Disponible si le coordinator a réussi sa dernière mise à jour."""
        return self.coordinator.last_update_success


class EDFTempoVisualSensor(EDFTempoSensor):
    """Sensor visuel avec cercle SVG coloré pour les couleurs Tempo."""

    @property
    def entity_picture(self) -> str | None:
        """Retourne un cercle SVG coloré selon la couleur Tempo."""
        color = self.native_value
        if color is None:
            return None
        hex_val = COLOR_HEX_MAP.get(color, "#9E9E9E")
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
            f"<circle cx='12' cy='12' r='10' fill='{hex_val}'/>"
            "</svg>"
        )
        return f"data:image/svg+xml,{svg}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les sensors selon le type de contrat."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    contract = entry.data[CONF_CONTRACT_TYPE]
    prefix = _CONTRACT_PREFIX[contract]

    descriptions: list[EDFTempoSensorEntityDescription] = list(COMMON_SENSORS)
    if contract == CONTRACT_BASE:
        descriptions += list(BASE_ONLY_SENSORS)
    if contract in (CONTRACT_HPHC, CONTRACT_TEMPO):
        descriptions += list(HCHP_SHARED_SENSORS)
    if contract == CONTRACT_HPHC:
        descriptions += list(HPHC_ONLY_SENSORS)
    if contract == CONTRACT_TEMPO:
        descriptions += list(TEMPO_SENSORS)
        descriptions += list(TEMPO_VISUAL_SENSORS)

    async_add_entities(
        EDFTempoVisualSensor(coordinator, desc, prefix)
        if desc.key in _VISUAL_SENSOR_KEYS
        else EDFTempoSensor(coordinator, desc, prefix)
        for desc in descriptions
    )
