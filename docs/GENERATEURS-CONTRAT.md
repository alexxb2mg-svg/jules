# Générateurs d'exercices : le contrat

Statut : en vigueur depuis la deuxième notion (pourcentages), qui a été écrite avec le gabarit sans
toucher aux briques. Ce document dit ce qu'un générateur promet, comment on en écrit un, et où va un
correctif quand quelque chose casse.

## Ce qu'un générateur promet

Un générateur fabrique, pour une notion du référentiel, des exercices **v2** (voir `docs/FICHES-V2.md`)
que Jules sert **sans IA** : le correcteur juge la réponse, les pièges relancent, les indices montent
d'un cran. Le générateur promet :

1. **Déterminisme** : même notion, même graine, même difficulté, même variante = même exercice, octet
   pour octet. Tout tirage passe par le `random.Random` reçu ; jamais le module `random`.
2. **Conformité** : chaque exercice rendu passe `_verifier_exercice` (le vérificateur des fiches v2)
   tel quel. Le constructeur `exercice_v2` le garantit : il refuse de rendre un exercice non conforme
   (`ErreurGeneration`, qui porte l'exercice fautif). C'est un bug du générateur, jamais de l'élève.
3. **Un type connu du correcteur** : `nombre`, `expression`, `texte_court`, `choix`, `ordre`,
   `association`. Un générateur n'invente **jamais** un type ni une forme de réponse : s'il en manque
   un, c'est le correcteur qu'on étend (cas 3 ci-dessous), avec ses propres tests.
4. **Au moins un piège** par exercice, chacun étant une vraie erreur que le correcteur reconnaît. Les
   pièges qui ne serviraient jamais (valeur = bonne réponse, valeur illisible, doublon) sont écartés
   automatiquement par `filtrer_pieges` ; le générateur peut donc proposer un piège « au cas où ».
5. **Aucune fuite** : ni les indices ni les relances ne contiennent la réponse, même écrite autrement.
   Le vérificateur découpe les textes en mots : « 1,25 » contient « 25 », « 1 150 € » contient « 150 ».
   Quand une valeur citée par un indice risque de contenir la réponse, on **filtre le tirage** avec
   `collision(...)` (briques/tirage.py), on ne tord pas l'indice.
6. **De la variété** : sur 60 graines, au moins 30 exercices différents par variante **et par
   difficulté** (un palier 1 étroit ressert les mêmes exercices à l'élève qui débute). « Différent » se
   mesure sur l'énoncé ET la réponse attendue : un exercice `association` ou `ordre` garde souvent une
   consigne fixe et fait varier ses paires ou ses éléments.
7. **Trois difficultés** (1, 2, 3), réglées par un dictionnaire de paliers lu avec `palier(...)`.

Le test générique `tests/test_generateurs.py` vérifie tout cela pour **toute notion** de
`jules/generateurs/<matiere>/` (`MODULES`, rempli par découverte des modules) : 60 graines × 3 difficultés × chaque variante. Une notion
nouvelle est couverte dès son enregistrement, sans écrire un test. `jules generateurs eprouver` fait
la même chose sur 300 graines, à la main.

## Écrire une notion

1. Copier `jules/generateurs/GABARIT.py` sous `jules/generateurs/<matiere>/<notion>.py` (le nom du
   fichier est l'identifiant de la notion, tirets remplacés par des soulignés).
2. Fixer `NOTION` (identifiant exact du référentiel `bibliotheque/programme/...`) et `VARIANTES`.
3. Écrire une fonction par variante : `(rng, difficulte) -> exercice_v2(...)`. Chaque fonction :
   - tire ses valeurs avec les briques (`tirage.py`) et les paliers ;
   - calcule la réponse et les erreurs typiques **en exact** (`Fraction`, entiers), jamais en flottant ;
   - écrit l'énoncé et les indices avec `format_fr.py` (« 1 234,5 », « 12,5 % », « 80 € ») et
     `habillage.py` (personnages, objets, articles) ;
   - donne la réponse au correcteur avec `nombre_machine(...)` (« 1.15 », jamais « 1,15 ») ;
   - propose ses pièges avec `piege_valeur`, `piege_contient`, `piege_diagnostic` ;
   - passe `lieu=f"{NOTION}/<variante>/<résumé du tirage>"` pour des erreurs lisibles.
4. Le point d'entrée est toujours `generer(graine, difficulte=1, variante=None)` =
   `generer_notion(NOTION, _VARIANTES, ...)`.
5. Rien à enregistrer : `MODULES` (`jules/generateurs/__init__.py`) découvre tout module du paquet
   de matière qui expose `NOTION`. Ne pas modifier `__init__.py` dans une PR de notion.
6. Lancer `jules generateurs eprouver <notion>` jusqu'à « tous conformes », puis lire une dizaine
   d'exercices avec `jules generateurs apercu <notion> --variante X --difficulte 2 --nombre 3` :
   un exercice conforme peut rester mal écrit, et ça, seul un humain le voit.
7. `pytest tests/test_generateurs.py` : le test générique couvre la notion.

Ce qu'on ne fait pas : un type inventé, un `random` global, un flottant dans une réponse, un indice
réécrit pour contourner une fuite, un `try/except` autour de `exercice_v2`.

## Branches et PR

- **Nouvelle notion = nouvelle branche depuis `origin/main` à jour, jamais empilée** sur une PR ouverte
  (`git fetch && git worktree add ../jules-gen-<notion> -b generateurs/<notion> origin/main`). Une PR
  empilée entre en conflit dès que sa base est fusionnée en squash (même contenu, autre commit).
- Une PR par notion. Elle ne touche que `jules/generateurs/<matiere>/<notion>.py`, ses tests propres
  et, si besoin, une brique **nouvelle** (fichier ou fonction ajoutés, jamais une fonction existante
  modifiée tant que d'autres notions sont en cours).
- **Une PR de notion ne modifie pas `docs/GENERATEURS-COUVERTURE.md`** ni `jules/generateurs/__init__.py`.
  Les notes de la notion vont dans le corps de la PR ; la table est mise à jour par la session qui
  relit, dans une PR à part.

## Où va un correctif

| Ce qui casse | Où corriger | Comment vérifier |
|---|---|---|
| Un exercice d'une notion est faux, mal écrit, fuit | **la notion** (`<matiere>/<notion>.py`) | `eprouver <notion>` + relecture `apercu` |
| Le même défaut dans deux notions, ou un besoin commun (nouveau format, nouvel habillage, nouveau filtre) | **une brique** (`briques/*.py`), avec son test unitaire dans `test_generateurs.py` | toute la suite ; non-régression : les exercices déjà générés ne changent pas (même graine, même sortie) |
| Le correcteur ne lit pas une réponse légitime, ou un type de réponse manque | **le correcteur** (`jules/fiches/correction.py`) + `_verifier_exercice`, avec leurs tests | `pytest tests` entier : les fiches écrites à la main passent par le même code |

Règle de précédence : on corrige au niveau le plus **bas** qui explique le défaut. Une notion ne
contourne jamais une brique, une brique ne contourne jamais le correcteur.

## Non-régression

Une brique modifiée ne doit pas changer les exercices déjà générés : la graine est une promesse (un
élève qui rejoue la graine 42 retrouve sa série). Avant de toucher une brique, capturer les sorties
(`jules generateurs eprouver` ne suffit pas : il vérifie la conformité, pas l'identité) :

    py - <<'EOF'
    import json, itertools
    from jules.generateurs import MODULES
    base = {f"{n}/{v}/{d}/{g}": m.generer(g, d, v) for n, m in MODULES.items()
            for v, d, g in itertools.product(m.VARIANTES, (1, 2, 3), range(200))}
    json.dump(base, open("base.json", "w", encoding="utf-8"), ensure_ascii=False)
    EOF

puis comparer après. Si une sortie **doit** changer (une erreur de contenu corrigée), le dire dans le
message de commit : c'est une nouvelle version de la notion.

## Commande

    jules generateurs                               notions couvertes et leurs variantes
    jules generateurs apercu NOTION [--variante V] [--difficulte 1|2|3] [--graine N] [--nombre K]
    jules generateurs eprouver [NOTION...] [--graines N]
