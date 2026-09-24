# Bibliothèques

Une bibliothèque, c'est ce que Jules sait **sur une notion du programme** : ce qu'on attend de l'élève, des repères de cours, et, si un enseignant en fournit une, sa façon de faire.
Quand l'élève choisit une notion (bouton « Choisir une notion ») ou quand Jules la reconnaît dans son message ou sur la photo de son exercice, ce qui concerne cette notion est ajouté aux consignes de Jules, à côté du profil de l'élève.

> **État actuel : expérimental.** Les bibliothèques publiées ici servent à tester le mécanisme. Aucune n'est validée par l'Éducation nationale ni par un enseignant. Le jour où des bibliothèques certifiées, ou les contenus d'un enseignant, seront disponibles, elles se brancheront au même endroit, sans toucher au code.

## Les trois types

| Type | Rôle | Exemple ici |
|---|---|---|
| `referentiel` | La liste des notions (un identifiant par notion). Tout le reste s'y rattache. Un seul à la fois. | `programme/` : programme officiel de 3e, 252 notions |
| `fiches` | Des repères par notion : essentiel du cours, méthode, erreurs fréquentes, exemple, exercices avec indices. | `fiches-3e-experimentales/` : 8 notions de maths |
| `direction` | La direction pédagogique d'un enseignant : approche, rédaction attendue, vocabulaire, ce qu'il faut éviter. | `exemple-direction-enseignant/` : enseignant fictif |

Chaque bibliothèque déclare aussi un **statut**, que Jules transmet au modèle et que l'élève voit dans le sélecteur :

| Statut | Signification | Comment Jules s'en sert |
|---|---|---|
| `experimentale` | Contenu de test, non validé | Appui seulement : « si le cours de l'élève dit autrement, c'est son cours qui fait foi » |
| `exemple` | Contenu fictif, pour montrer le format | Même prudence ; ne pas l'activer pour un vrai élève |
| `enseignant` | Fourni par le professeur de l'élève | Sa direction est prioritaire sur les repères des fiches |
| `certifiee` | Validée par un organisme reconnu (réservé pour plus tard) | — |

Un statut `experimentale` ou `exemple` sans `avertissement` est refusé au chargement.

## Choisir les bibliothèques

Dans `config.yaml` (ou `config.local.yaml` pour une famille) :

```yaml
modules:
  - id: notions
    reglages:
      bibliotheques:            # ordre = priorité
        - programme             # le référentiel
        - direction-mme-martin  # la direction du professeur passe avant...
        - fiches-3e-experimentales   # ...les fiches génériques
      detection: true           # reconnaître la notion dans le texte ou la photo
```

- **Priorité** : pour une même notion, si deux bibliothèques de fiches remplissent le même champ (par exemple `methode`), c'est la première de la liste qui l'emporte ; les champs manquants sont complétés par les suivantes.
- **Directions** : elles s'additionnent (celle de la matière, puis celle de la notion). Jules les suit en priorité, sans jamais passer outre ses règles de pédagogie et de sécurité.
- **Niveau** : seules les notions du niveau de l'élève sont chargées (déduit de `classe` dans son profil : « 3e », « 3ème », « troisième »...).
- Une bibliothèque illisible est signalée dans le journal et ignorée : Jules continue sans elle.

## Format

### `bibliotheque.yaml` (obligatoire, à la racine du dossier)

```yaml
id: fiches-3e-experimentales   # = nom du dossier (minuscules, chiffres, tirets)
titre: "Fiches 3e expérimentales"
type: fiches                   # referentiel | fiches | direction
statut: experimentale          # experimentale | exemple | enseignant | certifiee
licence: CC-BY-SA-4.0          # identifiant SPDX de la licence du contenu
pays: FR
niveaux: [3e]
avertissement: >-              # obligatoire si experimentale ou exemple ; montré à l'élève
  ...
description: >-
  ...
```

### Référentiel

`<niveau>/<matiere>.yaml`, format décrit dans [`programme/SCHEMA.md`](programme/SCHEMA.md). Les fichiers qui commencent par `_` sont des annexes (ex. `_brevet.yaml`) et ne contiennent pas de notions.

### Fiches : `fiches/<matiere>/<id-de-notion>.yaml`

Tous les champs de contenu sont facultatifs ; `notion`, `sources` et `relecture` sont obligatoires.

```yaml
notion: racine-carree            # identifiant exact du référentiel
couverture: "..."                # si la fiche ne couvre qu'une partie de la notion
essentiel: |                     # le cours en quelques lignes
  ...
methode:                         # étapes, dans l'ordre
  - ...
vocabulaire:
  - {terme: "...", definition: "..."}
erreurs_frequentes:
  - ...
exemple:                         # exemple résolu
  enonce: "..."
  solution: "..."
exercices:                       # la solution n'est jamais donnée avant que l'élève ait cherché
  - enonce: "..."
    indices: ["...", "..."]
    solution: "..."
direction: {...}                 # facultatif : direction propre à cette notion (voir plus bas)
sources:                         # d'où vient le contenu, avec la licence de chaque source
  - titre: "..."
    url: "https://..."           # lien vers la version consultée (révision précise si possible)
    auteurs: "..."
    licence: CC-BY-SA-4.0
    consulte_le: "2026-09-24"
    usage: "reformulé et résumé"
relecture:
  statut: a_relire               # a_relire | relue
  par: ""                        # qui a relu (ex. « professeur de mathématiques »)
  le: ""
```

Une fiche dont la `notion` n'existe pas dans le référentiel est ignorée (et signalée).

### Direction d'un enseignant

- `matieres/<id-de-matiere>.yaml` : ce qui vaut pour toute la matière ;
- `fiches/<id-de-notion>.yaml` avec un champ `direction` : ce qui vaut pour une notion.

```yaml
matiere: mathematiques
direction:
  approche: "..."
  redaction_attendue: "..."
  vocabulaire: ["..."]
  a_privilegier: ["..."]
  a_eviter: ["..."]
  remarques: "..."
```

Les clés ci-dessus ont un libellé prévu ; toute autre clé est transmise telle quelle.

## Règles pour publier une bibliothèque ici

1. **Contenu libre uniquement.** Licences acceptées : domaine public, CC0, CC BY, CC BY-SA, Licence Ouverte (etalab-2.0), GFDL, MIT. Refusées : NC (pas d'usage commercial), ND (pas de modification), « droits réservés », « usage en classe seulement », licence non indiquée. La liste des sources vérifiées est dans [`fiches-3e-experimentales/SOURCES.md`](fiches-3e-experimentales/SOURCES.md).
2. **Chaque fiche cite ses sources**, avec leur licence et le lien vers la version consultée. Un contenu adapté d'une source CC BY-SA reste en CC BY-SA.
3. **Rien de copié tel quel depuis un manuel ou un site non libre**, même « gratuit ».
4. **Les calculs des exercices sont vérifiés** avant publication.
5. Tant qu'aucun enseignant n'a relu une fiche, elle reste `relecture.statut: a_relire`.

Les tests (`tests/test_notions.py`) vérifient automatiquement la fiche d'identité, les licences, les sources, la relecture et le rattachement de chaque fiche à une notion existante.

## Et demain

Le format est pensé pour accueillir, sans changer le code :

- une bibliothèque **certifiée** (statut `certifiee`) publiée par un éditeur ou une institution ;
- la **direction d'un professeur** pour sa classe (statut `enseignant`), placée en tête de liste ;
- d'autres niveaux (primaire, lycée) : un autre référentiel et ses fiches ;
- d'autres pays ou programmes : un autre référentiel.
