"""Tests de cohérence pour les fichiers de traduction EDF Tempo."""

from __future__ import annotations

import json
from pathlib import Path


COMPONENT_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "edf_tempo"


def _load_json(filename: str) -> dict:
    """Charge un fichier JSON depuis le dossier du composant."""
    with open(COMPONENT_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def _collect_keys(d: dict, prefix: str = "") -> set[str]:
    """Collecte récursivement toutes les clés feuilles d'un dict JSON."""
    keys: set[str] = set()
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(_collect_keys(v, full_key))
        else:
            keys.add(full_key)
    return keys


# ---------------------------------------------------------------------------
# Test : cohérence des clés entre strings.json, fr.json et en.json
# ---------------------------------------------------------------------------


def test_translation_keys_match():
    """Les 3 fichiers de traduction doivent avoir exactement les mêmes clés."""
    strings = _load_json("strings.json")
    fr = _load_json("translations/fr.json")
    en = _load_json("translations/en.json")

    strings_keys = _collect_keys(strings)
    fr_keys = _collect_keys(fr)
    en_keys = _collect_keys(en)

    # strings.json == en.json (strings.json est la ref anglaise)
    assert strings_keys == en_keys, (
        f"Clés différentes entre strings.json et en.json:\n"
        f"  Dans strings.json mais pas en.json: {strings_keys - en_keys}\n"
        f"  Dans en.json mais pas strings.json: {en_keys - strings_keys}"
    )

    # fr.json == en.json
    assert fr_keys == en_keys, (
        f"Clés différentes entre fr.json et en.json:\n"
        f"  Dans fr.json mais pas en.json: {fr_keys - en_keys}\n"
        f"  Dans en.json mais pas fr.json: {en_keys - fr_keys}"
    )


# ---------------------------------------------------------------------------
# Test : aucune valeur vide dans les traductions
# ---------------------------------------------------------------------------


def _collect_empty_values(d: dict, prefix: str = "") -> list[str]:
    """Retourne les clés dont la valeur est une string vide."""
    empty: list[str] = []
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            empty.extend(_collect_empty_values(v, full_key))
        elif isinstance(v, str) and not v.strip():
            empty.append(full_key)
    return empty


def test_no_empty_translation_values():
    """Aucune valeur de traduction ne doit être vide."""
    for filename in ("strings.json", "translations/fr.json", "translations/en.json"):
        data = _load_json(filename)
        empty = _collect_empty_values(data)
        assert not empty, f"Valeurs vides dans {filename}: {empty}"


# ---------------------------------------------------------------------------
# Test : les entity translation_keys du code sont dans strings.json
# ---------------------------------------------------------------------------


def test_sensor_translation_keys_in_strings():
    """Chaque translation_key de sensor.py doit avoir une entrée dans strings.json."""
    from custom_components.edf_tempo.sensor import (
        BASE_ONLY_SENSORS,
        COMMON_SENSORS,
        HCHP_SHARED_SENSORS,
        HPHC_ONLY_SENSORS,
        TEMPO_SENSORS,
    )

    strings = _load_json("strings.json")
    sensor_translations = strings.get("entity", {}).get("sensor", {})

    all_descriptions = (
        list(COMMON_SENSORS)
        + list(BASE_ONLY_SENSORS)
        + list(HCHP_SHARED_SENSORS)
        + list(HPHC_ONLY_SENSORS)
        + list(TEMPO_SENSORS)
    )

    for desc in all_descriptions:
        assert desc.translation_key in sensor_translations, (
            f"translation_key '{desc.translation_key}' manquant dans "
            f"strings.json entity.sensor"
        )
        assert "name" in sensor_translations[desc.translation_key], (
            f"Pas de 'name' pour entity.sensor.{desc.translation_key} dans strings.json"
        )


def test_binary_sensor_translation_keys_in_strings():
    """Chaque translation_key de binary_sensor.py doit avoir une entrée dans strings.json."""
    from custom_components.edf_tempo.binary_sensor import HEURES_CREUSES_DESCRIPTION

    strings = _load_json("strings.json")
    bs_translations = strings.get("entity", {}).get("binary_sensor", {})

    key = HEURES_CREUSES_DESCRIPTION.translation_key
    assert key in bs_translations, (
        f"translation_key '{key}' manquant dans strings.json entity.binary_sensor"
    )


# ---------------------------------------------------------------------------
# Test : les state translations couvrent les options enum
# ---------------------------------------------------------------------------


def test_enum_state_translations_match_options():
    """Les sensors ENUM doivent avoir des state translations pour chaque option."""
    from custom_components.edf_tempo.sensor import (
        HCHP_SHARED_SENSORS,
        TEMPO_SENSORS,
    )
    from homeassistant.components.sensor import SensorDeviceClass

    strings = _load_json("strings.json")
    sensor_translations = strings["entity"]["sensor"]

    all_enum_sensors = list(HCHP_SHARED_SENSORS) + list(TEMPO_SENSORS)
    for desc in all_enum_sensors:
        if desc.device_class != SensorDeviceClass.ENUM:
            continue

        entry = sensor_translations.get(desc.translation_key, {})
        state_translations = entry.get("state", {})

        for option in desc.options:
            assert option in state_translations, (
                f"Option '{option}' du sensor '{desc.key}' manquante dans "
                f"strings.json entity.sensor.{desc.translation_key}.state"
            )


# ---------------------------------------------------------------------------
# Test : config_flow step data keys correspondent aux constantes
# ---------------------------------------------------------------------------


def test_config_flow_data_keys():
    """Les clés data dans strings.json correspondent aux CONF_* de const.py."""
    from custom_components.edf_tempo.const import (
        CONF_CONTRACT_TYPE,
        CONF_HC_RANGES,
        CONF_POWER_KVA,
        CONF_SCAN_INTERVAL,
    )

    strings = _load_json("strings.json")
    config_steps = strings["config"]["step"]

    assert CONF_CONTRACT_TYPE in config_steps["user"]["data"]
    assert CONF_POWER_KVA in config_steps["power"]["data"]
    assert CONF_HC_RANGES in config_steps["hc_ranges"]["data"]
    assert CONF_SCAN_INTERVAL in config_steps["scan_interval"]["data"]

    # Options flow
    options_data = strings["options"]["step"]["init"]["data"]
    assert CONF_POWER_KVA in options_data
    assert CONF_SCAN_INTERVAL in options_data
    assert CONF_HC_RANGES in options_data
