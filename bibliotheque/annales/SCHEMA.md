# Format des sujets d'annales

Chaque sujet est un fichier YAML dans `bibliotheque/annales/<session>/<matiere>/<centre>.yaml`.

## Structure

```yaml
sujet:
  id: "mathematiques-2024-metropole"        # identifiant unique
  session: "2024"                            # année de la session
  matiere: "Mathématiques"                   # nom de la matière
  centre: "Métropole"                        # centre d'examen
  titre: "Mathématiques — DNB 2024 Métropole"
  duree: "2 heures"
  examen: "dnb"                              # dnb | bac
  serie: "generale"                          # generale | professionnelle
  consignes_generales: |
    L'usage de la calculatrice est autorisé pour la partie 2.
    Le sujet comporte X exercices indépendants.

  exercices:
    - numero: 1
      titre: "Automatismes"
      partie: "Partie 1 — sans calculatrice"  # regroupement visuel
      bareme: 6                                # points sur le total
      enonce: |
        Texte complet de l'exercice, avec les questions numérotées.
        1. Calculer ...
        2. ...
      notions:                                 # ids du référentiel (Notion.id)
        - calcul-litteral
        - fractions-operations
      sous_questions:                          # optionnel, pour le barème détaillé
        - id: "1a"
          enonce: "Calculer ..."
          bareme: 1
        - id: "1b"
          enonce: "Développer ..."
          bareme: 1
      figure: |                                # optionnel, SVG ou description
        <svg>...</svg>
      tableau: |                               # optionnel, données tabulaires
        | x | 1 | 2 | 3 |
        |---|---|---|---|
        | f(x) | ? | 4 | ? |

    - numero: 2
      titre: "Fonctions"
      partie: "Partie 2 — avec calculatrice"
      bareme: 14
      enonce: |
        ...
      notions:
        - fonctions-lineaires
        - lecture-graphique

  source:
    titre: "DNB 2024 — Mathématiques — Métropole"
    url: "https://eduscol.education.fr/..."
    licence: "domaine public (sujet d'examen)"
```

## Champs obligatoires

- `sujet.id` — identifiant unique
- `sujet.session` — année
- `sujet.matiere` — nom de la matière
- `sujet.exercices` — au moins un exercice avec `numero`, `enonce`, `bareme`

## Champs optionnels

- `centre`, `titre`, `duree`, `examen`, `serie`, `consignes_generales`
- Par exercice : `titre`, `partie`, `notions`, `sous_questions`, `figure`, `tableau`
- `source` — référence du sujet original

## Lien avec le référentiel

Le champ `notions` de chaque exercice contient les identifiants exacts des notions
du référentiel (`bibliotheque/programme/<niveau>/<matiere>.yaml`). Le module utilise
ces identifiants pour enregistrer le suivi de l'élève après le bilan.

Les notions marquées `brevet: true` dans le référentiel sont celles qui tombent au brevet.
