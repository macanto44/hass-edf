# EDF Tarifs pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Intégration Home Assistant (HACS) pour suivre les **tarifs EDF** et les **couleurs Tempo** en temps réel. Compatible avec les contrats **Base**, **HP/HC** et **Tempo**.

## Pourquoi cette intégration ?

- Visualisez vos tarifs EDF directement dans Home Assistant
- Anticipez les jours Rouge Tempo pour adapter votre consommation
- Créez des automatisations basées sur la couleur du jour ou la période HC/HP
- Suivez les jours restants par couleur sur la saison en cours

## Fonctionnalités

- **3 types de contrat** : Base, HP/HC, Tempo
- **Tarifs en temps réel** depuis les données ouvertes [data.gouv.fr](https://www.data.gouv.fr) (CRE)
- **Couleurs Tempo** (Bleu/Blanc/Rouge) aujourd'hui et demain via [api-couleur-tempo.fr](https://www.api-couleur-tempo.fr)
- **Compteurs saison** : jours consommés et restants par couleur
- **Période actuelle** : Heures Creuses / Heures Pleines
- **Binary sensor** heures creuses (on/off) pour les automatisations
- **Transitions HC/HP exactes** : les entités basculent à la seconde près, indépendamment de la fréquence de polling
- **Assistant de configuration** guidé (pas de YAML à écrire)
- **Traductions** français et anglais
- **Cache intelligent** : l'historique saison est mis en cache pour éviter les appels API redondants
- **Aucune clé API requise**

## Captures d'écran

*TODO: ajouter des captures d'écran du dashboard*

## Installation

### Via HACS (recommandé)

1. Ouvrir HACS dans Home Assistant
2. Cliquer sur **Intégrations** > menu 3 points > **Dépôts personnalisés**
3. Ajouter l'URL du dépôt avec la catégorie **Intégration**
4. Chercher **EDF Tarifs** et installer
5. Redémarrer Home Assistant

### Installation manuelle

1. Télécharger le [dernier release](../../releases/latest)
2. Copier le dossier `custom_components/edf_tarifs/` dans votre dossier `config/custom_components/`
3. Redémarrer Home Assistant

## Configuration

1. Aller dans **Paramètres** > **Appareils et services** > **Ajouter une intégration**
2. Chercher **EDF Tarifs**
3. Suivre l'assistant :
   - **Étape 1** : Type de contrat (Base / HP/HC / Tempo)
   - **Étape 2** : Puissance souscrite (3 / 6 / 9 / 12 / 15 kVA)
   - **Étape 3** : Plages heures creuses *(HP/HC et Tempo uniquement)* — défaut : `22:00-06:00`
   - **Étape 4** : Fréquence de mise à jour (1h / 6h / 1j) — défaut : 6h

### Modifier les paramètres

**Paramètres** > **Appareils et services** > **EDF Tarifs** > **Configurer**

Vous pouvez modifier après installation : la puissance, les plages HC et la fréquence de mise à jour. Le type de contrat nécessite de supprimer et recréer l'intégration.

## Entités créées

### Contrat Base (2 sensors)

| Entité | Description | Type |
|---|---|---|
| `sensor.edf_base_abonnement_mensuel` | Abonnement mensuel | Monétaire |
| `sensor.edf_base_tarif_ttc` | Tarif TTC au kWh | Monétaire |

### Contrat HP/HC (5 sensors + 1 binary sensor)

| Entité | Description | Type |
|---|---|---|
| `sensor.edf_hphc_abonnement_mensuel` | Abonnement mensuel | Monétaire |
| `sensor.edf_hphc_tarif_actuel` | Tarif actuel (HC ou HP) | Monétaire |
| `sensor.edf_hphc_periode_actuelle` | Période en cours (HC/HP) | Enum |
| `sensor.edf_hphc_tarif_hc` | Tarif Heures Creuses | Monétaire |
| `sensor.edf_hphc_tarif_hp` | Tarif Heures Pleines | Monétaire |
| `binary_sensor.edf_hphc_heures_creuses` | Heures creuses actives | Booléen |

### Contrat Tempo (16 sensors + 1 binary sensor)

| Entité | Description | Type |
|---|---|---|
| `sensor.edf_tempo_abonnement_mensuel` | Abonnement mensuel | Monétaire |
| `sensor.edf_tempo_tarif_actuel` | Tarif actuel selon couleur et période | Monétaire |
| `sensor.edf_tempo_periode_actuelle` | Période en cours (HC/HP) | Enum |
| `sensor.edf_tempo_couleur_aujourd_hui` | Couleur du jour (Bleu/Blanc/Rouge) | Enum |
| `sensor.edf_tempo_couleur_demain` | Couleur de demain | Enum |
| `sensor.edf_tempo_tarif_bleu_hc` | Tarif Bleu HC | Monétaire |
| `sensor.edf_tempo_tarif_bleu_hp` | Tarif Bleu HP | Monétaire |
| `sensor.edf_tempo_tarif_blanc_hc` | Tarif Blanc HC | Monétaire |
| `sensor.edf_tempo_tarif_blanc_hp` | Tarif Blanc HP | Monétaire |
| `sensor.edf_tempo_tarif_rouge_hc` | Tarif Rouge HC | Monétaire |
| `sensor.edf_tempo_tarif_rouge_hp` | Tarif Rouge HP | Monétaire |
| `sensor.edf_tempo_jours_bleus_restants` | Jours Bleu restants sur la saison | Compteur |
| `sensor.edf_tempo_jours_blancs_restants` | Jours Blanc restants sur la saison | Compteur |
| `sensor.edf_tempo_jours_rouges_restants` | Jours Rouge restants sur la saison | Compteur |
| `sensor.edf_tempo_couleur_aujourd_hui_visuel` | Couleur du jour (pictogramme coloré) | Visuel |
| `sensor.edf_tempo_couleur_demain_visuel` | Couleur de demain (pictogramme coloré) | Visuel |
| `binary_sensor.edf_tempo_heures_creuses` | Heures creuses actives | Booléen |

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
          message: "Pensez à réduire votre consommation."
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
├── __init__.py           # Setup de l'intégration
├── config_flow.py        # Assistant de configuration (4 étapes)
├── coordinator.py        # DataUpdateCoordinator (orchestration + cache)
├── sensor.py             # Sensors (tarifs, couleurs, compteurs)
├── binary_sensor.py      # Binary sensor heures creuses
├── api_couleur_tempo.py  # Client API couleur-tempo.fr
├── api_datagouv.py       # Client API data.gouv.fr (tarifs CRE)
├── const.py              # Constantes et configuration
├── icon.png              # Icône de l'intégration
├── exceptions.py         # Exceptions métier
├── strings.json          # Traductions (référence)
├── translations/
│   ├── fr.json           # Français
│   └── en.json           # Anglais
└── manifest.json         # Métadonnées HACS
```

### Sources de données

| Source | Données | Contrats | Auth |
|---|---|---|---|
| [data.gouv.fr](https://www.data.gouv.fr) (CRE) | Tarifs, abonnements (CSV) | Tous | Aucune |
| [api-couleur-tempo.fr](https://www.api-couleur-tempo.fr) | Couleur jour/demain, historique saison | Tempo | Aucune |

### Cache intelligent

L'historique des couleurs de la saison est mis en cache en mémoire. Au premier démarrage, toutes les couleurs sont récupérées (~186 appels). Aux rafraîchissements suivants, seul le jour courant est revérifié (1 appel). Le cache est purgé automatiquement au changement de saison (1er septembre).

### Transitions HC/HP en temps réel

Les entités `periode_actuelle`, `tarif_actuel` et `heures_creuses` basculent à l'heure exacte de transition HC/HP (ex : 22:00 et 06:00), indépendamment de l'intervalle de polling configuré. Ce mécanisme repose sur des listeners `async_track_time_change` enregistrés sur chaque frontière des plages heures creuses.

## Développement

### Prérequis

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
├── conftest.py               # Fixtures partagées
├── test_sensor.py            # Tests sensors
├── test_binary_sensor.py     # Tests binary sensor
├── test_coordinator.py       # Tests coordinator + cache
├── test_api_couleur_tempo.py # Tests client API couleur
├── test_api_datagouv.py      # Tests client API data.gouv
├── test_config_flow.py       # Tests config flow
└── test_translations.py      # Tests traductions
```

## Contribuer

Les contributions sont les bienvenues ! Merci d'ouvrir une [issue](../../issues) avant de soumettre une PR pour discuter des changements proposés.

## Licence

[MIT](LICENSE)
