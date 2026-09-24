# Référentiel du programme officiel — format des fichiers

Un fichier YAML par classe et par matière : `bibliotheque/programme/<classe>/<matiere>.yaml` (UTF-8), avec `<classe>` parmi `5e`, `4e`, `3e`.
Seule la classe de l'élève est chargée (champ `classe` du profil) ; sans classe, les trois sont chargées ensemble, d'où la règle d'identifiants uniques sur tous les niveaux.
C'est le référentiel : les fiches des autres bibliothèques s'y rattachent par l'identifiant de notion (voir `bibliotheque/README.md`).

```yaml
matiere: Mathématiques            # nom affiché
id: mathematiques                 # = nom du fichier, minuscules, tirets
niveau: 3e
annee_scolaire: "2026-2027"
textes_officiels:                 # TOUS les textes utilisés, avec lien direct
  - intitule: "Programme du cycle 4 (annexe 3)"
    reference: "BO n° 31 du 30 juillet 2020"
    url: "https://..."
    consulte_le: "2026-09-23"
  - intitule: "Attendus de fin d'année et repères annuels de progression 3e"
    reference: "éduscol, 2019"
    url: "https://..."
    consulte_le: "2026-09-23"
perimetre: >                      # ce qui est strictement 3e vs cycle 4 entier, en 2-4 phrases
  ...
brevet:                           # si la matière est évaluée au DNB session 2027
  evalue: true
  epreuve: "Épreuve écrite de mathématiques, 2 h, ..."
  source: "https://..."
themes:
  - id: nombres-et-calculs
    titre: "Nombres et calculs"
    chapitres:
      - id: arithmetique
        titre: "Arithmétique"
        notions:
          - id: nombres-premiers
            titre: "Nombres premiers, décomposition en facteurs premiers"
            niveau_programme: "3e"      # "3e" si le texte le place en 3e ; "cycle 4" si non précisé
            attendus:                   # formulations reprises ou résumées fidèlement du texte officiel
              - "Déterminer si un entier est premier ..."
            mots_cles: [premier, diviseur, décomposition]
            brevet: true                # notion susceptible de tomber au DNB
            source: "Attendus 3e, p. 4" # où c'est dans le texte officiel (page ou section)
```

Règles :
- Aucune notion inventée : chaque notion vient d'un texte officiel cité dans `textes_officiels`.
- `attendus` : fidèle au texte (citation ou résumé serré), jamais d'ajout personnel.
- Ids : minuscules, sans accents, tirets. Uniques sur **toute** la bibliothèque, tous niveaux confondus (en 4e et 5e, préfixés par la classe : `4e-...`, `5e-...`).
- Programmes réécrits : quand un nouveau programme s'applique déjà à la classe l'année indiquée dans `annee_scolaire` (par exemple français et mathématiques en 5e à la rentrée 2026, arrêté du 18-2-2026), c'est lui qui est cité, pas l'ancien. Le dire dans `perimetre`.
- En cas de doute sur l'appartenance à la classe : `niveau_programme: "cycle 4"`, pas de supposition.
