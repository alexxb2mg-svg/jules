# Checklist référentiel : ajout et modification de matière

Statut : **actif** — ce document est mis à jour à chaque correctif CI lié au référentiel.

Références : `bibliotheque/programme/SCHEMA.md` (format YAML), `docs/spec/matieres-couleurs.json`
(couleurs), `docs/FICHES-V2.md` (contrat des fiches).

## Règle générale

Quand un problème CI récurrent est corrigé sur le référentiel, le correctif est ajouté ici
**dans le même commit**. Ce document accumule les leçons ; un agent ou un contributeur le lit
avant de toucher au référentiel et vérifie chaque point applicable avant de pousser.

---

## 1. Ajout d'une matière

### 1.1 Programme (`bibliotheque/programme/`)

- [ ] Un fichier `<matiere>.yaml` dans **chaque niveau déclaré** (`CM1`, `5e`, `4e`, `3e`).
  Le test `test_fichiers_4e_5e_au_format` vérifie que 4e et 5e ont exactement les mêmes stems
  que 3e. Un fichier manquant dans un seul niveau casse la CI.
- [ ] Chaque fichier commence par `# DONNÉES D'EXPÉRIMENTATION` (accents obligatoires : É, É).
  Le test `test_referentiel_marque_donnees_d_experimentation` vérifie la première ligne de
  **tous** les YAML de **tous** les niveaux.
- [ ] Champs obligatoires : `statut: experimentale`, `relecture: a_relire`,
  `avertissement` contenant le mot `expérimentation` (avec accent).
- [ ] Ids de notions **uniques sur toute la bibliothèque** : préfixer par matière et/ou niveau
  (`espagnol-`, `4e-espagnol-`, `cm1-espagnol-`). Le test
  `test_les_trois_niveaux_ensemble_sans_doublon` charge tous les niveaux d'un coup et échoue
  sur un doublon.
- [ ] `niveau_programme` : soit le niveau (`"3e"`, `"4e"`, `"CM1"`), soit `"cycle 4"` /
  `"cours moyen"` / `"cycle 3"`. Le test vérifie les valeurs autorisées par niveau.

### 1.2 Fiches (`bibliotheque/fiches-cm1-experimentales/`, `bibliotheque/fiches-v2-3e/`…)

- [ ] **CM1** : une fiche par notion dans `fiches-cm1-experimentales/fiches/<matiere>/`.
  Le test `test_fiches_cm1_experimentales` vérifie `sorted(fiches) == sorted(cat.notions)` —
  une notion sans fiche ou une fiche orpheline casse la CI.
- [ ] Chaque fiche : `essentiel`, `methode`, `erreurs_frequentes` non vides ; `exemple` avec
  `solution` ; au moins 2 `exercices` avec `enonce`, `indices`, `solution` ;
  `sources` avec `licence: etalab-2.0` et URL `education.gouv.fr` ; `relecture.statut: a_relire`.
- [ ] Le fichier commence par `# DONNÉES D'EXPÉRIMENTATION` (mêmes accents que le programme).
- [ ] Le répertoire parent de la fiche = la matière (`fichier.parent.name == notion.matiere`).

### 1.3 Tests — compteurs à mettre à jour

| Fichier | Test | Ce qui change |
|---|---|---|
| `tests/test_programme.py` | `test_la_3e_ne_change_pas` | Nombre total de notions 3e |
| `tests/test_notions.py` | `test_referentiel_cm1` | Nombre de notions CM1 + set des matières |
| `tests/test_chantier.py` | `test_etat_du_chantier` | Ligne markdown du tableau 3e (total et « à faire ») |

### 1.4 Couleurs et front-end

- [ ] Entrée dans `docs/spec/matieres-couleurs.json` (fond, texte, accent — contraste WCAG).
- [ ] Variables CSS dans `jules/web/static/matieres-couleurs.css`.
- [ ] Variables dark mode dans `front/src/themes/cahier.css` (`color-mix` avec l'accent).
- [ ] `--color-<matiere>` dans `front/src/index.css`.
- [ ] `ICONES_MATIERES` et `ORDRE_MATIERES` dans `front/src/config/matieres.ts`.

### 1.5 Validation locale

Avant de pousser, lancer :

```bash
pytest tests/test_programme.py tests/test_notions.py tests/test_chantier.py -x
```

---

## 2. Erreurs connues et correctifs passés

| Date | Erreur | Cause | Correctif |
|---|---|---|---|
| 2026-10-03 | `test_fichiers_4e_5e_au_format[4e]` rouge | 3e avait espagnol.yaml mais pas 4e | Créer le fichier dans tous les niveaux, pas seulement celui demandé |
| 2026-10-03 | `test_referentiel_marque_donnees_d_experimentation` rouge | Header 5e sans accents (`DONNEES` au lieu de `DONNÉES`) | Toujours copier le header depuis un fichier existant validé, jamais le taper à la main |
| 2026-10-03 | `test_fiches_cm1_experimentales` rouge | 24 notions CM1 espagnol ajoutées sans fiches | Toujours créer les fiches en même temps que le programme CM1 |
| 2026-10-03 | Compteurs tests cassés (252→269, 158→182) | Assertions codées en dur non mises à jour | Mettre à jour les compteurs dans le même commit que l'ajout |
| 2026-10-03 | `avertissement` 5e sans accent (`experimentation`) | Texte saisi sans accents par l'agent | Vérifier que `avertissement` contient `expérimentation` (avec accent) |
