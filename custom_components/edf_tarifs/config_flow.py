"""Config flow et Options flow pour l'intégration EDF Tarifs."""

from __future__ import annotations

import re
from datetime import time
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    AVAILABLE_CONTRACTS,
    AVAILABLE_POWERS,
    CONF_CONTRACT_TYPE,
    CONF_HC_RANGES,
    CONF_POWER_KVA,
    CONTRACT_BASE,
    DEFAULT_HC_RANGES_TEMPO,
    DOMAIN,
)

HC_PATTERN = re.compile(
    r"^\d{2}:\d{2}-\d{2}:\d{2}(\s*,\s*\d{2}:\d{2}-\d{2}:\d{2})*$"
)


def validate_hc_ranges(value: str) -> str:
    """Valide le format des plages HC (HH:MM-HH:MM,...)."""
    value = value.strip()
    if not HC_PATTERN.match(value):
        raise vol.Invalid("invalid_hc_format")
    for range_str in value.split(","):
        start_str, end_str = range_str.strip().split("-")
        try:
            time.fromisoformat(start_str.strip())
            time.fromisoformat(end_str.strip())
        except ValueError as err:
            raise vol.Invalid("invalid_hc_format") from err
    return value


class EDFTempoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow pour l'intégration EDF Tarifs."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow for this handler."""
        return EDFTempoOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 1 : type de contrat."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_power()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONTRACT_TYPE): vol.In(AVAILABLE_CONTRACTS),
                }
            ),
        )

    async def async_step_power(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 2 : puissance souscrite."""
        if user_input is not None:
            self._data.update(user_input)
            if self._data[CONF_CONTRACT_TYPE] == CONTRACT_BASE:
                return self._create_entry()
            return await self.async_step_hc_ranges()

        return self.async_show_form(
            step_id="power",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POWER_KVA, default=6): vol.In(AVAILABLE_POWERS),
                }
            ),
        )

    async def async_step_hc_ranges(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 3 : plages horaires HC (HPHC et Tempo uniquement)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                user_input[CONF_HC_RANGES] = validate_hc_ranges(
                    user_input[CONF_HC_RANGES]
                )
                self._data.update(user_input)
                return self._create_entry()
            except vol.Invalid:
                errors["base"] = "invalid_hc_format"

        return self.async_show_form(
            step_id="hc_ranges",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HC_RANGES, default=DEFAULT_HC_RANGES_TEMPO
                    ): str,
                }
            ),
            errors=errors,
        )

    def _create_entry(self) -> FlowResult:
        """Crée l'entrée de configuration."""
        contract = self._data[CONF_CONTRACT_TYPE]
        power = self._data[CONF_POWER_KVA]
        title = f"EDF {contract.upper()} {power} kVA"
        return self.async_create_entry(title=title, data=self._data)


class EDFTempoOptionsFlow(OptionsFlow):
    """Options flow pour l'intégration EDF Tarifs."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape unique : modifier fréquence, puissance, plages HC."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Valider HC si présent
            if CONF_HC_RANGES in user_input:
                try:
                    user_input[CONF_HC_RANGES] = validate_hc_ranges(
                        user_input[CONF_HC_RANGES]
                    )
                except vol.Invalid:
                    errors["base"] = "invalid_hc_format"

            if not errors:
                new_data = {**self._entry.data, **user_input}
                self.hass.config_entries.async_update_entry(
                    self._entry, data=new_data
                )
                await self.hass.config_entries.async_reload(self._entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        # Pré-remplir avec valeurs actuelles
        current = self._entry.data
        contract = current.get(CONF_CONTRACT_TYPE, CONTRACT_BASE)

        schema_dict: dict[Any, Any] = {
            vol.Required(
                CONF_POWER_KVA,
                default=current.get(CONF_POWER_KVA, 6),
            ): vol.In(AVAILABLE_POWERS),
        }

        if contract != CONTRACT_BASE:
            schema_dict[
                vol.Required(
                    CONF_HC_RANGES,
                    default=current.get(CONF_HC_RANGES, DEFAULT_HC_RANGES_TEMPO),
                )
            ] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )
