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

Une fiche visuelle est une **fiche de révision** : elle donne les réponses et les explique. Le
`jules:` d'un bloc (la bulle affichée quand l'élève clique dessus) est un **complément
d'explication** (le pourquoi, ce qu'il faut retenir, une confusion fréquente, un moyen de s'en
souvenir), jamais une question laissée ouverte. La règle « ne jamais donner la réponse » vaut
pour les exercices, pas pour les fiches ni pour les cartes mentales.

| type | champs | limites |
|---|---|---|
| `formule` | `expression`, `termes: {lettre: {couleur, legende}}` | expression ≤ 80 car., légende ≤ 160 car. |
| `carte` | `noeuds: [{id, titre, sous_titre?, principal?}]`, `liens: [{de, vers, libelle?}]` | 2 à 8 nœuds, liens vers des id existants |
| `graphe` | `gabarit` (voir plus bas), `curseurs: [{id, nom, min, max, pas, depart}]`, `lectures: [{si, texte}]` | 1 à 6 curseurs mobiles, 12 au total figés compris (voir plus bas), condition `si` limitée (voir plus bas) |
| `methode` | `etapes: ["...", ...]` | 2 à 6 étapes, chacune ≤ 260 car. |
| `piege` | `mauvaise_idee`, `pourquoi_faux`, `bonne_idee` | chacun ≤ 260 car. |
| `exemple` | `situation`, `calcul?`, `conclusion`, `figure?: {gabarit, curseurs}` | chaque champ ≤ 400 car. |
| `renfort` | `liens: [{icone?, titre, description?, outil?}]` | 1 à 6 liens |
| `schema` | `titre`, `svg` (SVG en ligne ou nom d'un fichier `.svg` à côté de la fiche) | titre ≤ 90 car. ; le SVG est nettoyé par liste blanche avant d'être servi (voir plus bas) |

### Notions clés : `**ainsi**`

Dans le texte courant d'une fiche (légendes de `formule`, étapes de `methode`, les trois champs
de `piege`, `situation`/`calcul`/`conclusion` d'`exemple`, `lectures` d'un `graphe`, et `jules:`),
une notion clé s'écrit entre doubles astérisques : `la **masse** se conserve`. L'affichage la met en
gras avec un léger coup de surligneur, pour qu'elle se détache des mots de liaison. On marque les
notions, grandeurs, unités et lois qui portent le sens, jamais les mots d'articulation (sauf s'ils
sont eux-mêmes la clé, comme « **en série** » / « **en dérivation** »).

Contrôlé par le code : au plus 4 notions clés par champ, 40 caractères chacune, sans espace au
bord, au plus 60 % du texte mis en valeur, marques bien fermées ; les limites de longueur se
comptent sans les `**`. Ailleurs (titres, carte, identifiants) la marque est refusée : elle
s'afficherait telle quelle.

### Le sens des lettres : `variables:`

Champ de premier niveau, facultatif : `variables: {v: "la vitesse, en m/s ou en km/h", d: "la distance
parcourue, en m ou en km"}`. Chaque lettre de grandeur des formules et calculs de la fiche y reçoit une
définition courte ; l'élève la retrouve en survolant la lettre dans une formule, sur toutes les pages de
Jules (fiche, discussion, entraînement, cours de la notion). Nom : une lettre latine ou grecque suivie
d'au plus 3 lettres, chiffres ou indices (`v`, `Ec`, `ρ`, `U1`, `V₁`) ; 12 lettres au plus ; 120
caractères par définition. Seules les lettres déclarées ont une bulle : jamais les symboles chimiques
(H, O, CO₂) ni les unités. Même principe pour `abreviations:` (`{ua: "unité astronomique", URSS: "Union des républiques
socialistes soviétiques"}`, 20 au plus, 1 à 16 caractères) : une abréviation propre à la notion,
rappelée au survol partout où elle apparaît. Les deux sont servis par
`GET /api/eleve/fiches_visuelles/notions/<id>/rappels`.

Ce qui est commun à tout le programme n'a rien à déclarer : symboles (`<`, `≤`, `≈`, `√`, `→`...),
unités (`s`, `kg`, `N`, `km/h`...), éléments et espèces chimiques (`Fe`, `CO₂`, `Cu²⁺`...) ont leur
bulle sur toutes les pages grâce au cœur `jules/web/static/symboles.js` et aux extensions de la
famille `rappels` (règles par matière, voir `docs/EXTENSIONS.md`). Les formules écrites dans
le texte (« P = m × g ») passent seules en gras. Seul le texte des schémas SVG n'est pas concerné.

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

## Curseurs figés d'un bloc `graphe`

Un curseur dont `min` = `max` (donc `depart` = `min`) est un **paramètre figé** par la fiche : bornes d'une
frise, période surlignée, grandeur tenue constante pendant qu'une autre varie. Sa valeur est transmise au
gabarit et utilisable dans les conditions `si`, mais il n'est **pas affiché** à l'élève (ni libellé, ni
glissière, ni pastille de valeur). Un bloc dont tous les curseurs sont figés affiche la figure seule. Pas de
clé `fixe` : min = max suffit.

Deux plafonds, chacun avec son message d'erreur : **6 curseurs mobiles** (min < max), ceux que l'élève fait
bouger ; **12 curseurs au total**, figés compris.

## Les conditions `si` d'un bloc `graphe`

Jamais d'`eval()`, ni côté serveur ni côté client. Une condition est une suite de comparaisons
`variable opérateur nombre` liées par `&&` :

- variable : le `nom` d'un curseur de ce bloc (sinon rejeté)
- opérateur : `<`, `<=`, `>`, `>=`, `==`, `!=`
- nombre : un littéral (`3`, `-2.5`)

Exemples valides : `"a > 0"`, `"a >= 1 && b < 0"`. Rejetés : tout ce qui contient un nom de
fonction, une parenthèse, un opérateur non listé, une variable inconnue du bloc.

## Gabarits de figures interactives connus

Un gabarit est fourni par une extension active (`extensions/<id>/gabarit.js`, voir
`docs/EXTENSIONS.md`) et dessine du SVG à partir des valeurs de curseurs, jamais de code libre
embarqué dans la fiche. Les gabarits livrés (134, vagues 1 du 03/10/2026 et 2 du 04/10/2026 ; curseurs et
bornes dans la clé `discussion` de chaque `extensions/<id>/extension.yaml`), rangés par matière principale
(un gabarit sert souvent dans plusieurs matières) :

- **Mathématiques 3e** (25) : `droite-affine` (f(x) = ax + b), `triangle-thales`, `triangle-rectangle` (carrés sur
  les trois côtés, AC² et BC² écrits ; carré de l'hypoténuse « ? » tant que `reponse` = 0, son aire AC² + BC²
  avec `reponse` = 1 ; une fiche fige `reponse` à 0 par un curseur min = max),
  `equation-solutions` (x² = a), `probabilites-frequences`,
  `droite-graduee` (n/d sur une droite), `droite-graduee-somme` (a + b comme un saut), `balance-equation`
  (ax + b = c), `courbe-point-mobile` (image, antécédent), `engrenages` (divisibilité) ; vague 2 :
  `carre-aire-cote`, `deux-droites`, `echelle-puissances-dix`, `jetons-en-rangees`, `rectangle-multiplication`,
  `barre-evolution`, `barre-ratio`, `diagramme-barres`, `grille-deux-epreuves`, `serie-statistique`,
  `globe-latitude-longitude`, `homothetie-rotation`, `lutin-trace`, `section-solide`, `boule-cylindre`.
- **Mathématiques CM1** (20) : `bande-fractions`, `bande-fractions-comparees`, `demi-droite-graduee`,
  `demi-droite-decimaux`, `plaque-dixiemes-centiemes`, `glisse-nombre` (× et ÷ par 10), `schema-en-barres`,
  `angle`, `symetrie-axe`, `quadrilatere-deformable`, `rectangle-quadrille` (périmètre, aire), `horloge`
  (durées), `urne-tirage` (probabilité), `paquets-proportionnels` (proportionnalité) ; vague 2 :
  `assemblage-cubes`, `construction-pas-a-pas`, `grille-deplacement`, `patron-cube`, `suite-motifs`,
  `recipient-gradue`.
- **Physique-chimie 3e** (17) : `circuit-serie-derivation`, `palier-changement-etat`, `redistribution-atomes`,
  `rampe-energie`, `chronophotographie` (mouvement, référentiel), `poids-astres`, `onde-sonore` (aussi en
  éducation musicale) ; vague 2 : `atome-constructeur`, `echelle-ph`, `flotte-coule`, `verre-dissolution`,
  `chaine-energetique`, `courbe-energie-cinetique`, `effet-de-serre`, `rectangle-puissance-duree`,
  `vecteur-force`, `spectre-ondes`.
- **SVT 3e** (14) : `effort-frequences` ; vague 2 : `deplacement-plaques`, `eclairement-latitude`, `matrice-risque`,
  `photosynthese-facteurs`, `reservoir-flux`, `arbre-generations`, `brassage-chromosomes`,
  `selection-naturelle`, `action-enzyme`, `cycle-menstruel`, `parcours-message-nerveux`,
  `reponse-immunitaire`, `tube-digestif`.
- **Technologie 3e** (10) : `capteur-seuil` (chaîne d'information, algorithme) ; vague 2 : `force-mot-de-passe`,
  `nombre-binaire`, `numerisation-signal`, `reseau-routage`, `autonomie-batterie`, `bilan-cycle-de-vie`,
  `poutre-flexion`, `trace-programme`, `diagramme-gantt`.
- **Sciences CM1** (7) : `cycle-lune`, `ombre-portee`, `balance-plateaux` ; vague 2 : `courbe-releves`,
  `reseau-populations`, `courbe-croissance`, `illusion-optique`.
- **Histoire-géographie et EMC** (11) : `frise` (frise générique à curseur date, repères portés par la fiche, jusqu'à trois
  périodes surlignées `de`/`à`, `de2`/`a2`, `de3`/`a3`),
  `distance-temps-transports` (CM1) ; vague 2 : `carte-tuiles-europe`, `aire-attraction`, `courbe-evolution`,
  `journee-repartition`, `itineraire-carte`, `carre-densite`, `arbre-multiplication` (EMC, aussi en SVT),
  `barre-vote`, `effet-cumule`.
- **Français** (9) : `frise-temps-verbaux`, `chaine-accords` ; vague 2 : `barre-objectif`, `echelle-intensite`,
  `phrase-en-blocs`, `schema-narratif`, `caricature-grossissement`, `jauge-voix`, `mots-par-regard`.
- **Langues vivantes** (7) : `position-objet` (in, on, under…) ; vague 2 : `bocal-quantite`, `dizaines-unites`,
  `pres-loin`, `rythme-intonation`, `echelles-paralleles`, `empreinte-carbone-trajet`.
- **Éducation musicale, arts plastiques et histoire des arts** (14) : `jauge-decibels` (dose : 8 h à 85 dB,
  durée divisée par 2 tous les 3 dB), `forme-musicale`, `frise-pulsations`,
  `cercle-couleurs` ; vague 2 : `figuratif-abstrait`, `perspective-point-de-fuite`, `decomposition-mouvement`,
  `point-de-vue`, `equilibre-empilement`, `pavage-motif`, `pistes-superposees`, `pixellisation`, `trace-geste`,
  `spatialisation-stereo`.

Ajouter un gabarit = créer une extension `extensions/<id>/` (`extension.yaml` avec
`fournit: figures: [<id>]`, et `gabarit.js`) puis l'activer dans `extensions:` de `config.yaml` :
ni `jules/fiches_visuelles.py` ni `accueil.html` ne changent.

## Contrôles automatiques (voir `jules/fiches_visuelles.py`)

- `notion` existe dans le référentiel du niveau ; l'attendu du référentiel alimente le bloc
  `attendus` automatiquement.
- Chaque `id` de bloc est unique ; les types sont limités aux 7 listés ci-dessus (`attendus` est
  réservé).
- Le `gabarit` d'un `graphe` doit être fourni par une extension active ; ses curseurs et lectures sont
  validés (bornes cohérentes, valeur de départ dans les bornes, conditions lisibles par
  l'analyseur sûr).
- Longueurs plafonnées partout (voir tableau ci-dessus) pour rester lisible sur tablette.
- Source(s) et licence obligatoires ; `relecture.statut` reste `a_relire` tant qu'un adulte n'a
  pas relu.
- Une fiche non conforme est écartée (avec le motif dans le journal) : Jules continue sans elle,
  jamais une fiche à moitié valide n'est affichée à l'élève.
