"""Constants for the EDF Tempo integration."""

from datetime import timedelta

DOMAIN = "edf_tempo"

# ---------------------------------------------------------------------------
# Update intervals
# ---------------------------------------------------------------------------

SCAN_INTERVAL_15MIN = timedelta(minutes=15)
SCAN_INTERVAL_1H = timedelta(hours=1)
SCAN_INTERVAL_6H = timedelta(hours=6)
SCAN_INTERVAL_1D = timedelta(days=1)

DEFAULT_SCAN_INTERVAL = SCAN_INTERVAL_6H

AVAILABLE_SCAN_INTERVALS: dict[str, timedelta] = {
    "15min": SCAN_INTERVAL_15MIN,
    "1h": SCAN_INTERVAL_1H,
    "6h": SCAN_INTERVAL_6H,
    "1d": SCAN_INTERVAL_1D,
}

# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

HTTP_TIMEOUT = 10  # seconds

# ---------------------------------------------------------------------------
# API — api-couleur-tempo.fr
# ---------------------------------------------------------------------------

URL_COULEUR_TEMPO_BASE = "https://www.api-couleur-tempo.fr/api"
URL_COULEUR_TEMPO_TODAY = f"{URL_COULEUR_TEMPO_BASE}/jourTempo/today"
URL_COULEUR_TEMPO_TOMORROW = f"{URL_COULEUR_TEMPO_BASE}/jourTempo/tomorrow"
URL_COULEUR_TEMPO_NOW = f"{URL_COULEUR_TEMPO_BASE}/now"
# Use as: URL_COULEUR_TEMPO_DATE.format(date="2025-01-15")
URL_COULEUR_TEMPO_DATE = f"{URL_COULEUR_TEMPO_BASE}/jourTempo/{{date}}"

# ---------------------------------------------------------------------------
# API — data.gouv.fr CRE (CSV datasets)
# ---------------------------------------------------------------------------

URL_DATAGOUV_BASE_HCHP = (
    "https://www.data.gouv.fr/api/1/datasets/r/c13d05e5-9e55-4d03-bf7e-042a2ade7e49"
)
URL_DATAGOUV_HCHP_POWER = (
    "https://www.data.gouv.fr/api/1/datasets/r/f7303b3a-93c7-4242-813d-84919034c416"
)
URL_DATAGOUV_TEMPO = (
    "https://www.data.gouv.fr/api/1/datasets/r/0c3d1d36-c412-4620-8566-e5cbb4fa2b5a"
)

# ---------------------------------------------------------------------------
# API — RTE OAuth2 (post-MVP)
# ---------------------------------------------------------------------------

URL_RTE_TOKEN = "https://digital.iservices.rte-france.com/token/oauth/"
URL_RTE_TEMPO = (
    "https://digital.iservices.rte-france.com"
    "/open_api/tempo_like_supply_contract/v1/tempo_like_calendars"
)

# ---------------------------------------------------------------------------
# Contract types
# ---------------------------------------------------------------------------

CONTRACT_BASE = "base"
CONTRACT_HPHC = "hphc"
CONTRACT_TEMPO = "tempo"

AVAILABLE_CONTRACTS = [CONTRACT_BASE, CONTRACT_HPHC, CONTRACT_TEMPO]

# ---------------------------------------------------------------------------
# Config entry keys
# ---------------------------------------------------------------------------

CONF_CONTRACT_TYPE = "contract_type"
CONF_HC_RANGES = "hc_ranges"
CONF_POWER_KVA = "power_kva"
CONF_RTE_CLIENT_ID = "rte_client_id"
CONF_RTE_CLIENT_SECRET = "rte_client_secret"
CONF_SCAN_INTERVAL = "scan_interval"

# ---------------------------------------------------------------------------
# Tempo colors
# ---------------------------------------------------------------------------

COLOR_BLEU = "Bleu"
COLOR_BLANC = "Blanc"
COLOR_ROUGE = "Rouge"
COLOR_INCONNU = "Inconnu"

# codeCouleur integer → color name
COLOR_MAP: dict[str, str] = {
    "1": COLOR_BLEU,
    "2": COLOR_BLANC,
    "3": COLOR_ROUGE,
}

# ---------------------------------------------------------------------------
# Tempo season day counters (max per season)
# ---------------------------------------------------------------------------

MAX_JOURS_BLEU = 300
MAX_JOURS_BLANC = 43
MAX_JOURS_ROUGE = 22

# ---------------------------------------------------------------------------
# HC/HP periods
# ---------------------------------------------------------------------------

PERIOD_HC = "HC"
PERIOD_HP = "HP"

# Default HC ranges for Tempo (22h–6h)
DEFAULT_HC_RANGES_TEMPO = "22:00-06:00"

# ---------------------------------------------------------------------------
# Available subscribed powers (kVA)
# ---------------------------------------------------------------------------

AVAILABLE_POWERS = [3, 6, 9, 12, 15]

# ---------------------------------------------------------------------------
# CSV parsing — required columns per contract
# ---------------------------------------------------------------------------

# Colonnes vérifiées sur les CSV réels data.gouv.fr (Story 1.2)
# Base  (c13d05e5): PART_VARIABLE_TTC, PART_FIXE_TTC
# HP/HC (f7303b3a): PART_VARIABLE_HC_TTC, PART_VARIABLE_HP_TTC, PART_FIXE_TTC
# Tempo (0c3d1d36): PART_VARIABLE_HCBleu_TTC … PART_VARIABLE_HPRouge_TTC, PART_FIXE_TTC
# PART_FIXE_TTC = abonnement annuel €/an → diviser par 12 pour €/mois

CSV_REQUIRED_COLS_TEMPO = {
    "P_SOUSCRITE",
    "PART_FIXE_TTC",
    "PART_VARIABLE_HCBleu_TTC",
    "PART_VARIABLE_HPBleu_TTC",
    "PART_VARIABLE_HCBlanc_TTC",
    "PART_VARIABLE_HPBlanc_TTC",
    "PART_VARIABLE_HCRouge_TTC",
    "PART_VARIABLE_HPRouge_TTC",
}

CSV_REQUIRED_COLS_HCHP = {
    "P_SOUSCRITE",
    "PART_FIXE_TTC",
    "PART_VARIABLE_HC_TTC",
    "PART_VARIABLE_HP_TTC",
}

CSV_REQUIRED_COLS_BASE = {
    "P_SOUSCRITE",
    "PART_FIXE_TTC",
    "PART_VARIABLE_TTC",
}

CSV_SEPARATOR = ";"
