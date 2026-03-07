# EDF Tarifs pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Integration Home Assistant (HACS) pour suivre les **tarifs EDF** et les **couleurs Tempo** en temps reel. Supporte les contrats **Base**, **HP/HC** et **Tempo**.

## Pourquoi cette integration ?

- Visualisez vos tarifs EDF directement dans Home Assistant
- Anticipez les jours Rouge Tempo et adaptez votre consommation
- Creez des automatisations basees sur la couleur du jour ou la periode HC/HP
- Suivez les jours restants par couleur sur la saison

## Fonctionnalites

- **3 types de contrat** : Base, HP/HC, Tempo
- **Tarifs en temps reel** depuis les donnees ouvertes [data.gouv.fr](https://www.data.gouv.fr) (CRE)
- **Couleurs Tempo** (Bleu/Blanc/Rouge) aujourd'hui et demain via [api-couleur-tempo.fr](https://www.api-couleur-tempo.fr)
- **Compteurs saison** : jours consommes et restants par couleur
- **Periode actuelle** : Heures Creuses / Heures Pleines
- **Binary sensor** heures creuses (on/off) pour les automatisations
- **Transitions HC/HP exactes** : les entites basculent a la seconde pres, independamment de la frequence de polling
- **Config Flow** guide (pas de YAML)
- **Traductions** francais et anglais
- **Cache intelligent** : l'historique saison est mis en cache pour eviter les appels API redondants
- **Aucune cle API requise**

## Captures d'ecran

*TODO: ajouter captures d'ecran du dashboard*

## Installation

### Via HACS (recommande)

1. Ouvrir HACS dans Home Assistant
2. Cliquer sur **Integrations** > menu 3 points > **Depots personnalises**
3. Ajouter l'URL du depot avec la categorie **Integration**
4. Chercher **EDF Tarifs** et installer
5. Redemarrer Home Assistant

### Installation manuelle

1. Telecharger le [dernier release](../../releases/latest)
2. Copier le dossier `custom_components/edf_tarifs/` dans votre dossier `config/custom_components/`
3. Redemarrer Home Assistant

## Configuration

1. Aller dans **Parametres** > **Appareils et services** > **Ajouter une integration**
2. Chercher **EDF Tarifs**
3. Suivre l'assistant :
   - **Etape 1** : Type de contrat (Base / HP/HC / Tempo)
   - **Etape 2** : Puissance souscrite (3 / 6 / 9 / 12 / 15 kVA)
   - **Etape 3** : Plages heures creuses *(HP/HC et Tempo uniquement)* — defaut : `22:00-06:00`
   - **Etape 4** : Frequence de mise a jour (1h / 6h / 1j) — defaut : 6h

### Modifier les parametres

**Parametres** > **Appareils et services** > **EDF Tarifs** > **Configurer**

Modifiable apres installation : puissance, plages HC, frequence. Le type de contrat necessite une reconfiguration.

## Entites creees

### Contrat Base (2 sensors)

| Entite | Description | Type |
|---|---|---|
| `sensor.edf_base_abonnement_mensuel` | Abonnement mensuel | Monetaire |
| `sensor.edf_base_tarif_ttc` | Tarif TTC au kWh | Monetaire |

### Contrat HP/HC (5 sensors + 1 binary sensor)

| Entite | Description | Type |
|---|---|---|
| `sensor.edf_hphc_abonnement_mensuel` | Abonnement mensuel | Monetaire |
| `sensor.edf_hphc_tarif_actuel` | Tarif actuel (HC ou HP) | Monetaire |
| `sensor.edf_hphc_periode_actuelle` | Periode en cours (HC/HP) | Enum |
| `sensor.edf_hphc_tarif_hc` | Tarif Heures Creuses | Monetaire |
| `sensor.edf_hphc_tarif_hp` | Tarif Heures Pleines | Monetaire |
| `binary_sensor.edf_hphc_heures_creuses` | Heures creuses actives | Booleen |

### Contrat Tempo (14 sensors + 1 binary sensor)

| Entite | Description | Type |
|---|---|---|
| `sensor.edf_tempo_abonnement_mensuel` | Abonnement mensuel | Monetaire |
| `sensor.edf_tempo_tarif_actuel` | Tarif actuel selon couleur et periode | Monetaire |
| `sensor.edf_tempo_periode_actuelle` | Periode en cours (HC/HP) | Enum |
| `sensor.edf_tempo_couleur_aujourd_hui` | Couleur du jour (Bleu/Blanc/Rouge) | Enum |
| `sensor.edf_tempo_couleur_demain` | Couleur de demain | Enum |
| `sensor.edf_tempo_tarif_bleu_hc` | Tarif Bleu HC | Monetaire |
| `sensor.edf_tempo_tarif_bleu_hp` | Tarif Bleu HP | Monetaire |
| `sensor.edf_tempo_tarif_blanc_hc` | Tarif Blanc HC | Monetaire |
| `sensor.edf_tempo_tarif_blanc_hp` | Tarif Blanc HP | Monetaire |
| `sensor.edf_tempo_tarif_rouge_hc` | Tarif Rouge HC | Monetaire |
| `sensor.edf_tempo_tarif_rouge_hp` | Tarif Rouge HP | Monetaire |
| `sensor.edf_tempo_jours_bleus_restants` | Jours Bleu restants sur la saison | Compteur |
| `sensor.edf_tempo_jours_blancs_restants` | Jours Blanc restants sur la saison | Compteur |
| `sensor.edf_tempo_jours_rouges_restants` | Jours Rouge restants sur la saison | Compteur |
| `binary_sensor.edf_tempo_heures_creuses` | Heures creuses actives | Booleen |

## Exemples d'automatisations

### Notification jour Rouge demain

```yaml
automation:
  - alias: "Alerte Tempo Rouge demain"
    trigger:
      - platform: state
        entity_id: sensor.edf_tempo_couleur_demain
        to: "Rouge"
    action:
      - service: notify.mobile_app
        data:
          title: "Tempo Rouge demain !"
          message: "Pensez a reduire votre consommation."
```

### Couper le chauffe-eau en jour Rouge HP

```yaml
automation:
  - alias: "Couper chauffe-eau Rouge HP"
    trigger:
      - platform: state
        entity_id: binary_sensor.edf_tempo_heures_creuses
        to: "off"
    condition:
      - condition: state
        entity_id: sensor.edf_tempo_couleur_aujourd_hui
        state: "Rouge"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.chauffe_eau
```

## Architecture technique

```
custom_components/edf_tarifs/
├── __init__.py           # Setup de l'integration
├── config_flow.py        # Assistant de configuration (4 etapes)
├── coordinator.py        # DataUpdateCoordinator (orchestration + cache)
├── sensor.py             # Sensors (tarifs, couleurs, compteurs)
├── binary_sensor.py      # Binary sensor heures creuses
├── api_couleur_tempo.py  # Client API couleur-tempo.fr
├── api_datagouv.py       # Client API data.gouv.fr (tarifs CRE)
├── const.py              # Constantes et configuration
├── exceptions.py         # Exceptions metier
├── strings.json          # Traductions (reference)
├── translations/
│   ├── fr.json           # Francais
│   └── en.json           # Anglais
└── manifest.json         # Metadonnees HACS
```

### Sources de donnees

| Source | Donnees | Contrats | Auth |
|---|---|---|---|
| [data.gouv.fr](https://www.data.gouv.fr) (CRE) | Tarifs, abonnements (CSV) | Tous | Aucune |
| [api-couleur-tempo.fr](https://www.api-couleur-tempo.fr) | Couleur jour/demain, historique saison | Tempo | Aucune |

### Cache intelligent

L'historique des couleurs de la saison est mis en cache en memoire. Au premier demarrage, toutes les couleurs sont recuperees (~186 appels). Aux rafraichissements suivants, seul le jour courant est re-verifie (1 appel). Le cache est purge automatiquement lors du changement de saison (1er septembre).

### Transitions HC/HP en temps reel

Les entites `periode_actuelle`, `tarif_actuel` et `heures_creuses` basculent a l'heure exacte de transition HC/HP (ex: 22:00 et 06:00), independamment de l'intervalle de polling configure. Ceci est realise via des listeners `async_track_time_change` enregistres sur chaque frontiere des plages heures creuses.

## Developpement

### Pre-requis

- Python 3.11+
- Home Assistant 2024.1+

### Lancer les tests

```bash
pip install pytest pytest-asyncio aiohttp
python -m pytest tests/ -v
```

### Structure des tests

```
tests/
├── conftest.py               # Fixtures partagees
├── test_sensor.py            # Tests sensors
├── test_binary_sensor.py     # Tests binary sensor
├── test_coordinator.py       # Tests coordinator + cache
├── test_api_couleur_tempo.py # Tests client API couleur
├── test_api_datagouv.py      # Tests client API data.gouv
├── test_config_flow.py       # Tests config flow
└── test_translations.py      # Tests traductions
```

## Contribuer

Les contributions sont les bienvenues ! Merci d'ouvrir une [issue](../../issues) avant de soumettre une PR pour discuter des changements proposes.

## Licence

[MIT](LICENSE)
