# Fiches visuelles — schéma d'un fichier

Une fiche visuelle vit dans une bibliothèque `type: fiches-visuelles` (voir `bibliotheque/README.md`) :

```
bibliotheque/<id-bibliotheque>/bibliotheque.yaml      # type: fiches-visuelles
bibliotheque/<id-bibliotheque>/fiches/<matiere>/<notion>.yaml
```

Le format complet, validé par Alex le 25/09/2026, est décrit avec un exemple dans un document de
cadrage tenu hors dépôt (personnel, non publié). Ce fichier résume les champs, tels que lus et
vérifiés par `jules/fiches_visuelles.py`.

## Champs du fichier

```yaml
notion: <id du référentiel, obligatoire>       # doit exister dans bibliotheque/programme/<niveau>/<matiere>.yaml
titre: "<titre affiché, sinon celui du référentiel>"
matiere: <id matière>          # informatif : la matière réelle vient du référentiel
niveau: <niveau>               # informatif : le niveau réel vient du référentiel
auteurs: ["..."]
licence: CC-BY-SA-4.0          # doit être une licence libre connue (jules/bibliotheques.py LICENCES_LIBRES)
sources:                       # au moins une, url https obligatoire, licence libre obligatoire
  - {titre: "...", url: "https://...", licence: CC-BY-SA-4.0}
relecture: {statut: a_relire}  # 'a_relire' ou 'relue'
blocs: [...]                   # entre 3 et 12 blocs, ids uniques
```

## Les types de blocs (8 de la maquette, +1 : `schema`)

Le bloc `attendus` n'est **jamais écrit dans le fichier** : il est ajouté automatiquement à
l'affichage, à partir des `attendus` du référentiel officiel pour cette `notion`. Les 7 autres
types se déclarent dans `blocs:`, chacun avec un `id` unique (minuscules, chiffres, tirets) et un
`jules:` optionnel (1 à 3 phrases, 320 caractères max).

| type | champs | limites |
|---|---|---|
| `formule` | `expression`, `termes: {lettre: {couleur, legende}}` | expression ≤ 80 car., légende ≤ 160 car. |
| `carte` | `noeuds: [{id, titre, sous_titre?, principal?}]`, `liens: [{de, vers, libelle?}]` | 2 à 8 nœuds, liens vers des id existants |
| `graphe` | `gabarit` (voir plus bas), `curseurs: [{id, nom, min, max, pas, depart}]`, `lectures: [{si, texte}]` | 1 à 6 curseurs, condition `si` limitée (voir plus bas) |
| `methode` | `etapes: ["...", ...]` | 2 à 6 étapes, chacune ≤ 260 car. |
| `piege` | `mauvaise_idee`, `pourquoi_faux`, `bonne_idee` | chacun ≤ 260 car. |
| `exemple` | `situation`, `calcul?`, `conclusion`, `figure?: {gabarit, curseurs}` | chaque champ ≤ 400 car. |
| `renfort` | `liens: [{icone?, titre, description?, outil?}]` | 1 à 6 liens |
| `schema` | `titre`, `svg` (SVG en ligne ou nom d'un fichier `.svg` à côté de la fiche) | titre ≤ 90 car. ; le SVG est nettoyé par liste blanche avant d'être servi (voir plus bas) |

### Le bloc `schema`

Ajouté avec le contrat d'extension (`docs/EXTENSIONS.md`) : un schéma fixe, dessiné en amont
(à la main ou avec le skill `concept-diagrams`), jamais généré à l'affichage. `svg` est soit un
SVG en ligne (commence par `<svg`), soit le nom d'un fichier `.svg` posé à côté du fichier de la
fiche (jamais un chemin absolu ni `..`).

Avant d'être servi, le SVG est **nettoyé par le code** (`jules/svg_sur.py`), par liste blanche
d'éléments (`svg`, `g`, `defs`, `marker`, `path`, `line`, `polyline`, `polygon`, `rect`, `circle`,
`ellipse`, `text`, `tspan`, `title`, `desc`) et d'attributs (géométrie, `class`, `transform`,
couleurs, `marker-end`/`marker-start` en ancre locale uniquement, `viewBox`...). Sont **toujours
refusés** : `<script>`, `foreignObject`, tout attribut `on*`, `href`/`xlink:href` externe, un
`style` contenant `url(`, et tout fichier avec `<!DOCTYPE` ou `<!ENTITY`. Une fiche dont le
schéma ne passe pas ce filtre est écartée comme n'importe quelle fiche non conforme.

L'affichage utilise les classes de couleur du système de design `concept-diagrams` (mode clair
uniquement, embarquées dans `accueil.css` sous `.bloc-schema`) : `.t .ts .th .box .arr .leader
.node` et `.c-purple .c-teal .c-coral .c-pink .c-gray .c-blue .c-green .c-amber .c-red`.

## Les conditions `si` d'un bloc `graphe`

Jamais d'`eval()`, ni côté serveur ni côté client. Une condition est une suite de comparaisons
`variable opérateur nombre` liées par `&&` :

- variable : le `nom` d'un curseur de ce bloc (sinon rejeté)
- opérateur : `<`, `<=`, `>`, `>=`, `==`, `!=`
- nombre : un littéral (`3`, `-2.5`)

Exemples valides : `"a > 0"`, `"a >= 1 && b < 0"`. Rejetés : tout ce qui contient un nom de
fonction, une parenthèse, un opérateur non listé, une variable inconnue du bloc.

## Gabarits de figures interactives connus

Un gabarit est un fichier `jules/web/static/gabarits/<id>.js` qui dessine du SVG à partir des
valeurs de curseurs, jamais de code libre embarqué dans la fiche :

- `droite-affine` : f(x) = ax + b (curseurs `a`, `b`)
- `triangle-thales` : configuration de Thalès (curseur `t`, position de M sur [AB])
- `triangle-rectangle` : triangle rectangle en C (curseurs `ac`, `bc`, hypoténuse calculée)
- `equation-solutions` : x² = a sur une droite graduée (curseur `a`)
- `probabilites-frequences` : fréquence observée qui se stabilise avec n (curseur `n`)

Ajouter un gabarit = déposer le fichier JS, l'ajouter à `GABARITS_CONNUS`
(`jules/fiches_visuelles.py`) et l'inclure dans `accueil.html`.

## Contrôles automatiques (voir `jules/fiches_visuelles.py`)

- `notion` existe dans le référentiel du niveau ; l'attendu du référentiel alimente le bloc
  `attendus` automatiquement.
- Chaque `id` de bloc est unique ; les types sont limités aux 7 listés ci-dessus (`attendus` est
  réservé).
- Le `gabarit` d'un `graphe` doit être dans `GABARITS_CONNUS` ; ses curseurs et lectures sont
  validés (bornes cohérentes, valeur de départ dans les bornes, conditions lisibles par
  l'analyseur sûr).
- Longueurs plafonnées partout (voir tableau ci-dessus) pour rester lisible sur tablette.
- Source(s) et licence obligatoires ; `relecture.statut` reste `a_relire` tant qu'un adulte n'a
  pas relu.
- Une fiche non conforme est écartée (avec le motif dans le journal) : Jules continue sans elle,
  jamais une fiche à moitié valide n'est affichée à l'élève.
