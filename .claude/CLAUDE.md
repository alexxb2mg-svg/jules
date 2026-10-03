# Jules — Guide pour les agents CI

Ce fichier documente les patterns d'erreurs CI récurrents et les checklists
de prévention, construits à partir de l'historique réel du projet.

Pipeline CI : `ruff check` → `ruff format --check` → `mypy` → `pytest`
(le pipeline s'arrête au premier stade rouge).

Matrice : Python 3.10 / 3.12 / 3.13 sur ubuntu, Python 3.12 sur macos et windows.

Convention de merge : **squash-merge** sur `main`.

---

## 1. Cohérence README ↔ code

**Tests** : `tests/test_readme_coherence.py`

Le README affiche des compteurs et des listes que les tests vérifient
automatiquement. Tout ajout de contenu **doit** mettre à jour le README.

| Ce que le test vérifie | Ligne du test | Se casse quand… |
|---|---|---|
| Chaque module de `config.yaml` nommé dans le README | L34-36 | On ajoute un module sans l'écrire dans le README |
| Chaque module actif cité dans la ligne `\| Modules \|` du tableau | L84-97 | Idem (double vérification : présence + ligne tableau) |
| Nombre de leviers = fichiers YAML dans `adaptations/leviers/` | L40 | On ajoute un levier YAML |
| Nombre d'aménagements = fichiers YAML dans `adaptations/amenagements/` | L41 | On ajoute un aménagement YAML |
| Nombre d'extensions activées = `len(config["extensions"])` | L45 | On active/désactive une extension |
| Nombre de dossiers dans `extensions/` | L47 | On ajoute un dossier d'extension |
| Nombre de notions de mathématiques 3e = fichiers `.py` dans `jules/generateurs/mathematiques/` | L52 | On ajoute un générateur |
| Niveaux du `pyproject.toml` cités dans le README | L55-64 | On modifie la description du paquet |

### Prévention

Après toute modification de contenu (module, levier, extension, générateur,
niveau), lancer :

```bash
python -m pytest tests/test_readme_coherence.py -v
```

Si un test échoue, mettre à jour le nombre ou la liste correspondante dans
`README.md` **dans le même commit** que l'ajout de contenu.

---

## 2. Compteurs codés en dur dans les tests

Plusieurs tests assertent un nombre exact qui doit être mis à jour manuellement.

| Fichier | Ligne | Assertion | Se casse quand… |
|---|---|---|---|
| `tests/test_coeur.py` | L18-36 | Liste ordonnée exacte des 17 IDs de modules | Ajout/suppression/réordonnancement d'un module dans `config.yaml` |
| `tests/test_suivi_origine.py` | L35 | `set(ORIGINES_SUIVI) == {"analyse", "epreuve", "cours", "exercices", "studio", "annales"}` | Ajout d'une origine de suivi dans `jules/modules/suivi.py` |
| `tests/test_fiches_visuelles.py` | L150 | `len(fiches) == 23` | Ajout d'une fiche visuelle dans la bibliothèque |
| `tests/test_leviers.py` | L79 | `len(leviers) == 13` | Ajout d'un fichier YAML de levier |
| `tests/test_notions.py` | L398 | `len(maths) == 38` | Ajout d'une notion de maths 3e au référentiel |

### Prévention

Chercher les assertions numériques dans les tests touchés par le changement :

```bash
grep -rn 'len(.*) ==' tests/ | grep -v __pycache__
```

Mettre à jour chaque compteur dans le même commit que l'ajout de contenu.

---

## 3. mypy — attributs dynamiques des modules

**Pattern** : `self.tuteur.module("notions").catalogue` renvoie un `Module`
générique. L'accès aux attributs spécifiques (`catalogue`, `lecons`, etc.)
nécessite `# type: ignore[attr-defined]`.

**Pattern** : les valeurs JSON extraites par le LLM sont typées `int | float`.
Si le code attend `int`, il faut wrapper avec `int(valeur)` pour satisfaire mypy.

### Prévention

Tout nouveau module qui accède aux attributs d'un autre module via
`self.tuteur.module("xxx")` doit ajouter `# type: ignore[attr-defined]` sur
la ligne d'accès. Ne pas supprimer les ignores existants — ils sont structurels.

Lancer mypy avant de commit :

```bash
python -m mypy jules/
```

---

## 4. ruff format

**Fichiers récidivistes** : `tests/test_outils_hote.py` (3 corrections dans
l'historique), `jules/modules/exercices.py`, `jules/web/app.py`.

Les longues listes d'arguments `subprocess.run` et les appels multi-lignes
sont régulièrement reformatés différemment par ruff.

### Prévention

```bash
ruff format --check .
ruff format .  # pour corriger
```

Toujours lancer `ruff format` avant de commit, surtout après modification de
fichiers de test avec des signatures complexes.

---

## 5. Windows — viewport Chrome

**Test** : `tests/test_adaptations_robustesse.py`, L314-318

Sur Windows, `--hide-scrollbars` n'a pas d'effet sur Chrome (-16 px) et la
largeur minimum est ~500 px. Le test utilise une tolérance de 20 px sur
Windows (`sys.platform == "win32"`) vs une égalité stricte sur Linux.

**Historique** : corrigé au moins 3 fois (commits `1275e37`, `039eb6d`, `2485090`).

### Prévention

Ne pas toucher à la branche `if sys.platform == "win32"` dans ce test.
Si le test échoue sur Windows avec un écart de viewport, augmenter la
tolérance ou le seuil minimum, jamais l'inverse.

---

## 6. Windows — encodage UTF-8

Les tests Chromium sur Windows doivent ouvrir les fichiers avec
`encoding="utf-8"` explicite. Python sur Windows utilise `cp1252` par défaut.

### Prévention

Tout `open()` ou `.read_text()` dans du code qui sera exécuté en CI Windows
doit spécifier `encoding="utf-8"`.

---

## 7. Windows — timeout CI

Le job Windows (`Python 3.12, windows-latest`) peut dépasser le timeout
GitHub Actions (~25 min pour ~20 000 tests). Les tests passent mais le job
est tué par `KeyboardInterrupt`.

### Prévention

Ce n'est pas un bug de code. Si le job Windows est rouge avec
`KeyboardInterrupt` et que tous les tests sont passés : relancer les jobs
échoués via l'API GitHub Actions (`rerun_failed_jobs`). C'est un problème
d'infrastructure, pas de code.

---

## 8. CodeQL — injection de log et XSS

**Injection de log** : les paramètres d'URL loggés sans assainissement des
retours chariot (`\r\n`) déclenchent une alerte CodeQL. Nettoyer avec
`.replace("\r", "").replace("\n", "")` avant de logger.

**XSS** : les URL `createObjectURL` passées à `img src` depuis des données
utilisateur déclenchent un flux de taint. Utiliser `new URL(raw).href` pour
casser la chaîne de taint.

### Prévention

Ne jamais logger directement une entrée utilisateur (URL, paramètre de requête)
sans nettoyer les caractères de contrôle. Côté frontend, toujours valider/parser
les URL avant de les injecter dans le DOM.

---

## Checklists

### Ajout d'un nouveau module

1. Créer `jules/modules/<id>.py` avec la classe `Brique(Module)`
2. Ajouter l'entrée dans `config.yaml` (section `modules`)
3. Mettre à jour la liste ordonnée dans `tests/test_coeur.py` L18-36
4. Ajouter `` `<id>` `` dans la ligne `| Modules |` du tableau dans `README.md`
5. Si le module crée une nouvelle origine de suivi, ajouter dans `ORIGINES_SUIVI` (`jules/modules/suivi.py`) ET dans `tests/test_suivi_origine.py` L35
6. Lancer `ruff format . && mypy jules/ && pytest tests/test_readme_coherence.py tests/test_coeur.py -v`

### Ajout de contenu (fiches, leçons, leviers, notions)

1. Ajouter le contenu dans le bon répertoire
2. Mettre à jour le compteur dans `README.md` (trouver le nombre avec `grep -n "N <type>" README.md`)
3. Mettre à jour le compteur dans le test correspondant (voir table §2)
4. Lancer `pytest tests/test_readme_coherence.py -v`

### Avant chaque commit

```bash
ruff check .
ruff format --check .
mypy jules/
python -m pytest tests/test_readme_coherence.py tests/test_coeur.py -v
```

### Avant chaque push

```bash
python -m pytest -rs --cov --cov-report=term-missing
```
