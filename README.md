# EDF Tempo pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io/)

Integration Home Assistant (HACS) pour suivre les tarifs et couleurs **EDF Tempo**, **HP/HC** et **Base** en temps reel.

## Fonctionnalites

- **3 types de contrat** : Base, HP/HC, Tempo
- **Tarifs en temps reel** depuis les donnees ouvertes data.gouv.fr
- **Couleurs Tempo** (Bleu/Blanc/Rouge) aujourd'hui et demain via api-couleur-tempo.fr
- **Jours restants** par couleur sur la saison en cours
- **Periode actuelle** (Heures Creuses / Heures Pleines)
- **Binary sensor** heures creuses (on/off)
- **Config Flow** guide en 4 etapes (pas de YAML)
- **Traductions** francais et anglais

## Entites creees

### Contrat Base (2 sensors)

| Entite | Description |
|---|---|
| `sensor.edf_base_abonnement_mensuel` | Abonnement mensuel |
| `sensor.edf_base_tarif_ttc` | Tarif TTC |

### Contrat HP/HC (5 sensors + 1 binary)

| Entite | Description |
|---|---|
| `sensor.edf_hphc_abonnement_mensuel` | Abonnement mensuel |
| `sensor.edf_hphc_tarif_actuel` | Tarif actuel (HC ou HP) |
| `sensor.edf_hphc_periode_actuelle` | Periode en cours (HC/HP) |
| `sensor.edf_hphc_tarif_hc` | Tarif Heures Creuses |
| `sensor.edf_hphc_tarif_hp` | Tarif Heures Pleines |
| `binary_sensor.edf_hphc_heures_creuses` | Heures creuses actives |

### Contrat Tempo (14 sensors + 1 binary)

| Entite | Description |
|---|---|
| `sensor.edf_tempo_abonnement_mensuel` | Abonnement mensuel |
| `sensor.edf_tempo_tarif_actuel` | Tarif actuel |
| `sensor.edf_tempo_periode_actuelle` | Periode en cours (HC/HP) |
| `sensor.edf_tempo_couleur_aujourd_hui` | Couleur du jour |
| `sensor.edf_tempo_couleur_demain` | Couleur de demain |
| `sensor.edf_tempo_tarif_bleu_hc` | Tarif Bleu HC |
| `sensor.edf_tempo_tarif_bleu_hp` | Tarif Bleu HP |
| `sensor.edf_tempo_tarif_blanc_hc` | Tarif Blanc HC |
| `sensor.edf_tempo_tarif_blanc_hp` | Tarif Blanc HP |
| `sensor.edf_tempo_tarif_rouge_hc` | Tarif Rouge HC |
| `sensor.edf_tempo_tarif_rouge_hp` | Tarif Rouge HP |
| `sensor.edf_tempo_jours_bleus_restants` | Jours Bleu restants |
| `sensor.edf_tempo_jours_blancs_restants` | Jours Blanc restants |
| `sensor.edf_tempo_jours_rouges_restants` | Jours Rouge restants |
| `binary_sensor.edf_tempo_heures_creuses` | Heures creuses actives |

## Installation

### Via HACS (recommande)

1. Ouvrir HACS dans Home Assistant
2. Cliquer sur **Integrations** > menu 3 points > **Custom repositories**
3. Ajouter `https://github.com/macanto44/hass-edf` avec la categorie **Integration**
4. Chercher **EDF Tempo** et installer
5. Redemarrer Home Assistant

### Installation manuelle

1. Copier le dossier `custom_components/edf_tempo/` dans votre dossier `config/custom_components/`
2. Redemarrer Home Assistant

## Configuration

1. Aller dans **Parametres** > **Appareils et services** > **Ajouter une integration**
2. Chercher **EDF Tempo**
3. Suivre l'assistant :
   - **Etape 1** : Type de contrat (Base / HP/HC / Tempo)
   - **Etape 2** : Puissance souscrite (3 / 6 / 9 / 12 / 15 kVA)
   - **Etape 3** : Plages heures creuses *(HP/HC et Tempo uniquement)* — defaut : 22:00-06:00
   - **Etape 4** : Frequence de mise a jour (15min / 1h / 6h / 1j) — defaut : 6h

### Modifier les parametres

**Parametres** > **Appareils et services** > **EDF Tempo** > **Configurer**

Modifiable apres installation : puissance, plages HC, frequence. Le type de contrat necessite une reconfiguration.

## Sources de donnees

| Source | Donnees | Contrats |
|---|---|---|
| [data.gouv.fr](https://www.data.gouv.fr) (CRE) | Tarifs, abonnements | Tous |
| [api-couleur-tempo.fr](https://www.api-couleur-tempo.fr) | Couleur du jour/demain, jours restants | Tempo |

Aucune cle API requise.

## Licence

MIT
