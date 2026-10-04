# Jules — le contrat d'extension

Statut : troisième étape (voir `jules_architecture_plugins.md`, ordre de réalisation). Le
chargeur (`jules/extensions.py`) est branché pour trois familles : les **figures** (les cinq
gabarits des fiches visuelles sont des extensions), les **outils** (les trois outils de
référence sont des extensions) et les **modules** (ceux qu'une extension fournit, pour observer
les points d'accroche ci-dessous). Les autres familles (moteurs, notifieurs, bibliothèques)
fonctionnent encore comme avant, sans passer par ce contrat.

## Principe

Une extension est un dossier du dépôt principal, `extensions/<id>/`, qui se présente dans un
manifeste `extension.yaml` :

```yaml
id: exemple-figure                 # doit être le nom du dossier (minuscules, chiffres, tirets)
titre: "Une figure d'exemple"
version: "1.0.0"
licence: MIT
auteurs: ["pseudo-github"]
fournit:
  modules: []            # ids de modules : le code est dans extensions/<id>/<module>.py
  moteurs: []            # ids de jules/llm/<id>.py
  notifieurs: []         # ids de jules/notifieurs/<id>.py
  outils: []             # ids d'outils (voir « Figures, outils et modules » ci-dessous)
  figures: [exemple-cercle]        # ids de gabarits, dont le code est dans gabarit.js
  types_de_blocs: []     # types de blocs de fiche visuelle ajoutés par l'extension
  bibliotheques: []      # ids de bibliotheque/<id>/
permissions:
  reseau: false                 # accès réseau depuis le code serveur de l'extension
  appel_ia: false                # peut interroger un moteur d'IA
  ecriture_dossier_eleve: false   # peut écrire dans le dossier de données de l'élève
  notification_parent: false      # peut déclencher une notification au parent
```

Toutes les clés de `fournit:` et de `permissions:` sont optionnelles ; absentes, elles valent
liste vide ou `false`. Une extension peut fournir plusieurs choses à la fois (par exemple un
pack « Géométrie 3e » = des figures et des fiches dans une bibliothèque).

## Activation

Rien ne se charge sans être déclaré. Une extension n'est prise en compte que si son id figure
dans la nouvelle clé `extensions:` de `config.yaml` (ou `config.local.yaml`) :

```yaml
extensions:
  - exemple-figure
```

Absente ou vide, cette clé signifie : aucune extension externe. C'est la même logique que pour
les modules (`modules:` dans `config.yaml`).

## Figures, rappels, outils et modules (branchés aux étapes 2 et 3)

**Figures.** Une extension qui fournit des figures met leur code dans un seul fichier,
`extensions/<id>/gabarit.js`, qui enregistre chaque figure de `fournit.figures` dans
`window.GABARITS["<id de la figure>"]` (voir `extensions/droite-affine/gabarit.js`). Ce code
s'exécute dans la page de l'élève : au chargement, il passe le même premier filtre que le code
d'un outil (pas de `eval(`, `fetch(`, adresse externe... ; les lignes de commentaire entières et
l'espace de noms SVG `http://www.w3.org/2000/svg` sont admis) ; absent ou suspect, l'extension
est écartée. Le cœur en tire deux choses, sans connaître aucune figure par son nom :
- une fiche visuelle n'accepte que les gabarits fournis par les extensions actives ;
- la page d'accueil charge un seul script, `/gabarits.js`, qui met bout à bout les `gabarit.js`
  des extensions actives (dans l'ordre de `extensions:`). Ajouter une figure = ajouter une
  extension et l'activer, sans toucher à `accueil.html`.

**Figures dans la discussion (clé `discussion`).** Jules peut montrer une figure dans sa réponse, jamais
la dessiner : le modèle n'écrit qu'un bloc de code markdown de langage `figure` contenant du JSON
`{"gabarit": "<id>", "valeurs": {...}}`, et la bulle le dessine avec le gabarit de l'extension
(`FigureGabarit`, `front/src/modules/fiches/blocs.tsx`). Une figure n'est proposée dans la discussion
que si son extension la déclare, sous une clé de premier niveau `discussion:` (activation volontaire,
figure par figure ; sans déclaration, elle reste utilisable dans les fiches seulement) :

```yaml
discussion:
  droite-affine:                     # doit figurer dans fournit.figures
    quand: "Pour faire voir une fonction affine f(x) = ax + b..."   # une phrase pour le modèle
    valeurs:                         # toutes les valeurs du gabarit, chacune avec ses quatre bornes
      a: {min: -3, max: 3, pas: 0.5, defaut: 1}
      b: {min: -4, max: 4, pas: 1, defaut: 0}
```

Le module `figures` (`jules/modules/figures.py`, placé **après** `notions` et `cours` dans
`config.yaml`) donne ces déclarations au modèle dans les modes autorisés (`reglages.modes`, par défaut
`aide-devoirs` et `reexplique` ; `config.yaml` du dépôt y ajoute `cours`, le panneau de Jules dans une leçon), puis relit chaque réponse : un bloc valide (gabarit déclaré, mode
autorisé, objet `{gabarit, valeurs}` sans autre clé, chaque valeur un nombre dans `[min ; max]` et sur
le `pas`, valeurs absentes = `defaut`) est récrit en JSON compact ; tout autre bloc est retiré sans
bruit (une seule figure par message) et l'événement `figure_ecartee` est journalisé avec sa raison.
Aucun SVG ni code ne vient du modèle : seulement un id de la liste blanche et des nombres bornés.

**Figure dynamique dans la bulle.** Sous la figure, la bulle affiche un curseur par valeur (même
composant `Graphe` que le bloc graphe des fiches) : départ = les valeurs choisies par Jules, bornes et
pas = la déclaration `discussion` ci-dessus, servie au front par `/api/infos` (clé `figures`, module
`figures`). Les mêmes bornes valent donc pour le modèle et pour l'élève.

**Figures qui montrent la réponse (`revele: true`).** Certaines figures donnent la réponse d'un exercice
(`equation-solutions` place −√a et √a). Leur déclaration porte
`revele: true` (facultatif, booléen, défaut `false`). Écrire une étape décisive suffit : l'aire des trois carrés de
`triangle-rectangle` 2.0 (36, 64 et 100 pour AC = 6, BC = 8) ne laissait que la racine carrée à prendre. Quand c'est
possible, mieux vaut une figure qui montre sans écrire : `urne-tirage` place une flèche sur une échelle impossible /
une chance sur deux / certain sans écrire « peu probable » ni « probable », et n'est pas `revele`. Autre voie, une
valeur qui masque l'étape décisive : `triangle-rectangle` 2.1 a une valeur `reponse` (0 ou 1, défaut 0) ; à 0, le
carré de l'hypoténuse porte « ? » et aucune valeur de AB ni de AB² n'est écrite, la figure n'est donc plus `revele`
(proposée en aide aux devoirs et en cours) ; `reponse: 1` écrit AC² + BC², réservé à la réexplication. Une fiche
visuelle fige `reponse` à 0 par un curseur min = max (non affiché).

**Valeurs qui montrent la réponse (`valeurs_revele`).** Une phrase `quand` ne suffit pas à tenir la règle : le
modèle peut écrire `reponse: 1` en aide aux devoirs, et l'élève pousser un curseur. La déclaration liste donc ces
valeurs : `valeurs_revele: [reponse]` (facultatif, noms pris dans `valeurs`, sans doublon). Le code
(`jules/modules/figures.py`) applique alors, hors des modes `modes_revele` (config.yaml, `reexplique`) :

- la valeur est forcée à son `defaut` à la normalisation, quoi qu'ait écrit le modèle (le bloc est gardé, la
  figure montre « ? ») ;
- elle n'apparaît pas dans la liste des valeurs donnée au modèle (ni dans l'exemple) ;
- dans tous les modes, `/api/infos` la sert figée (min = max = défaut) : jamais de curseur sous la figure de la
  bulle ; en réexplication la bulle garde la valeur écrite par Jules (`reponse: 1`), sans curseur non plus.

Le mécanisme vaut pour toute figure `revele: true` dont une seule valeur porte la réponse (balance-equation,
redistribution-atomes…) : déclarer cette valeur dans `valeurs_revele` avec un défaut qui la cache permet de passer
la figure en `revele: false`. Carte à venir, gabarit par gabarit.

```yaml
discussion:
  equation-solutions:
    quand: "Pour faire voir combien de solutions a l'équation x² = a..."
    revele: true                     # la figure montre la réponse
    valeurs:
      a: {min: -25, max: 81, pas: 1, defaut: 49}
```

Une telle figure n'est proposée au modèle **et** acceptée dans sa réponse que si le mode de la
conversation figure dans `reglages.modes_revele` du module `figures` (`config.yaml`, défaut
`[reexplique]`) ; dans les autres modes autorisés (`aide-devoirs`), elle est absente de la liste donnée
au modèle et un bloc qui la cite est retiré (`figure_ecartee`, raison « gabarit non autorise »). Ne
jamais mettre `aide-devoirs` dans `modes_revele` : la figure ferait l'exercice à la place de l'élève.

**Gabarits livrés.** 134 figures, toutes déclarées pour la discussion (liste détaillée par matière dans
`bibliotheque/SCHEMA-FICHE-VISUELLE.md`, § gabarits) : mathématiques 3e (25) ; mathématiques CM1 (20) ;
physique-chimie 3e (17) ; SVT 3e (14) ; technologie 3e (10) ; sciences CM1 (7) ; histoire-géographie et EMC (11) ;
français (9) ; langues vivantes (7) ; éducation musicale, arts plastiques et histoire des arts (14). Révèlent la
réponse (`revele: true`, raison écrite en commentaire dans chaque `extension.yaml`) : `aire-attraction`,
`atome-constructeur`, `autonomie-batterie`, `balance-equation`, `bande-fractions-comparees`, `barre-evolution`,
`carte-tuiles-europe`, `cercle-couleurs`, `chaine-accords`, `construction-pas-a-pas`, `courbe-evolution`,
`courbe-point-mobile`, `demi-droite-decimaux`, `demi-droite-graduee`, `deux-droites`, `droite-graduee`,
`droite-graduee-somme`, `echelle-intensite`, `echelles-paralleles`, `equation-solutions`, `frise`,
`frise-temps-verbaux`, `glisse-nombre`, `grille-deplacement`, `grille-deux-epreuves`, `itineraire-carte`,
`jauge-decibels`, `nombre-binaire`, `onde-sonore`, `patron-cube`, `redistribution-atomes`, `spectre-ondes`,
`symetrie-axe`, `trace-programme` : 34 figures.

**Périodes multiples de `frise`.** La fiche peut surligner jusqu'à trois périodes au-dessus de l'axe : `de`/`à`
(ou `a`), puis `de2`/`a2` et `de3`/`a3`, toutes en curseurs figés (min = max, donc non affichés à l'élève).
Une période n'existe que si ses deux bornes sont données ; elle est vive quand le repère `date` est dedans,
pâle sinon ; des périodes qui se chevauchent sont décalées en hauteur (jusqu'à trois rangées). Ces noms ne
sont pas dans la `discussion` (un défaut ajouterait une période à toutes les frises) : c'est leur présence
qui ajoute une période, d'où leur entrée dans `LUES_HORS_DISCUSSION`.

**Ajouter un gabarit, côté tests.** Rien à recopier : `tests/registre_figures.py` lit la clé `discussion` de chaque
`extensions/*/extension.yaml` et la liste `extensions:` de `config.yaml`. Chaque gabarit déclaré est alors contrôlé
tout seul : déclaration chargée à l'identique par `jules/extensions.py`, `revele` booléen, bornes cohérentes
(min < max, pas > 0, défaut dans les bornes et sur un cran), noms de valeurs lus par `gabarit.js` = noms déclarés
(exception justifiée : `LUES_HORS_DISCUSSION`, curseurs que seule une fiche porte), figure active = figure
déclarée, bornes et drapeau `revele` appliqués selon le mode (`tests/test_figures_discussion.py`, mode cours dans
`tests/test_figures_cours.py`).

Ce qui lit les messages sans les dessiner (analyse du module `suivi`) passe par
`texte_sans_figures(texte)` (`jules/modules/figures.py`) : chaque bloc `figure` y devient
« [figure : <gabarit>] » (et un schéma, « [schéma : <id-notion>] »).

**Schéma de la fiche visuelle dans la discussion (toutes matières).** En plus des gabarits, Jules peut
citer le schéma SVG de la fiche visuelle d'une notion, par son seul identifiant :

```figure
{"schema": "parallelisme-triangles-pythagore"}
```

Forme choisie : une clé `schema` seule, plutôt que `{"gabarit": "schema", "notion": ...}`, parce que ce
n'est pas un gabarit (aucun dessin paramétré, aucune extension, aucune valeur bornée) : le modèle cite un
dessin déjà écrit et vérifié par le code au chargement de la fiche (`jules/fiches_visuelles.py`). Le SVG
ne passe jamais par le modèle ni par le message : le front le lit par la route existante
`GET /api/eleve/fiches_visuelles/notions/<id>` et le dessine avec le même rendu que la fiche
(`SchemaNotion` puis `Schema`, `front/src/modules/fiches/blocs.tsx` : `importNode`, jamais `innerHTML` ;
bouton « Agrandir le schéma » ; feuille claire en thème sombre ; largeur bornée par la bulle).

Liste blanche, par conversation (`FiguresBrique.schemas`, `jules/modules/figures.py`) : la notion de la
conversation (module `notions`, `conv.notion`) puis ses prérequis (champ `prerequis` de sa fiche, module
`notions` ou fiches v2 du module `exercices`, au plus 4), s'ils ont une fiche visuelle chargée avec un bloc
`schema`. Le prompt ne reçoit que ces identifiants, jamais les 410 : une phrase courte « Tu peux montrer le
schéma de la notion « <titre> » avec ce bloc, quand une image aide (toujours accompagné de ton explication
en mots) ». Sans notion rattachée, pas de schéma. Validation stricte : un bloc `schema` avec une autre clé,
un identifiant inconnu ou hors de cette liste est retiré (`figure_ecartee`, `gabarit: "schema:<id>"`,
raison « schema non autorise » ou « attendu {schema} »). Même règle d'une figure par message, mêmes modes
que les gabarits (`reglages.modes`, jamais `epreuve`, `exercice`, `controle`). Un schéma de fiche
est un support de cours, pas la réponse d'un exercice : il n'a pas de drapeau `revele` et vaut dans
`aide-devoirs`. Seul le schéma est cité ; les blocs `formule` et `carte` de la fiche ne le sont pas (non
livré : le bloc `formule` devrait suivre les règles de `modes_revele`). Réglage `schemas: false` du module
`figures` pour couper ce type de bloc.

**Mode `cours` et dessin en caractères.** Dans le panneau de Jules d'une leçon, la notion est celle de la leçon
(module `cours`), les gabarits `revele` restent exclus, et une figure ou un schéma qui montrerait la réponse de
l'exercice actif est retiré (raison « revelerait la reponse ») ; le panneau dessine le bloc avec le même
composant que la bulle du chat (`FigureBulle`). Dans TOUS les modes, même sans figure (`epreuve` compris), la
contribution du module dit au modèle de ne jamais dessiner en caractères (traits, barres, schéma ASCII).

**Schéma au-dessus de l'énoncé des exercices sans IA.** Le module `exercices` (réglage
`schema_en_exercice`, défaut `true`, `config.yaml`) ajoute à chaque exercice présenté (`commencer`,
`generer`, exercice suivant, `etat`) un champ `schema` : l'identifiant de la notion si sa fiche visuelle a
un schéma, sinon `null`. L'écran d'entraînement l'affiche, ouvert, au-dessus de l'énoncé, avec un bouton
« Masquer le schéma » / « Voir le schéma » (même composant `SchemaNotion`). Garde-fou : `schema` est
`null` pour un exercice dont la réponse est écrite dans le schéma (`schema_revele` : valeur attendue, texte
d'une bonne option ou d'une réponse acceptée, deux éléments d'une association ; toujours pour un exercice
« ordre », qu'une frise résout). Le schéma reste alors dans la fiche, pas sur cet exercice.

**Rappels (bulles au survol).** Sur toutes les pages, ce qui est abrégé ou symbolique montre ce
qu'il veut dire dans une petite bulle (souris, toucher, clavier). Le cœur,
`jules/web/static/symboles.js`, ne connaît aucune règle de matière : il parcourt le texte affiché,
tient le contexte de la notion (matière, lettres des formules et abréviations de sa fiche
visuelle) et affiche les bulles. Les règles viennent des extensions qui déclarent
`fournit: rappels: [<ids des règles>]` et mettent leur code dans `extensions/<id>/rappels.js`
(même premier filtre que `gabarit.js`). La page charge un seul script, `/rappels.js`, qui met bout à
bout les `rappels.js` des extensions actives, juste après le cœur. Deux façons d'écrire une règle :

```js
// Des données seules : une abréviation par ligne, reconnue comme mot entier.
Symboles.dictionnaire({ id: "grammaire", matieres: ["francais"], entrees: { COD: "complément d'objet direct" } });

// Une règle : un texte en entrée, les passages à expliquer en sortie.
Symboles.enregistrer({
  id: "siecles", matieres: ["histoire", "geographie", "emc"], rang: 2,   // rang petit = prioritaire
  trouver(texte, ctx, outils) { return [{ debut, fin, sens: "XIXe : le 19e siècle : de 1801 à 1900" }]; },
});
// Ou une mise en forme (formules du texte en gras) : mettreEnForme(texte, ctx, outils) -> [{debut, fin, classe}].
```

`matieres` limite la règle aux notions de ces matières (identifiants du référentiel) ; quand la
matière est inconnue (discussion sans notion), toutes les règles s'appliquent. `ctx` donne la
matière, les lettres et abréviations de la notion, et dit si le texte est dans une formule ;
`outils` offre les aides communes (mot isolé, mot avant, mot devant une parenthèse...). Quand
deux règles reconnaissent le même endroit, la lecture la plus longue l'emporte, puis le rang.
Extensions livrées : `rappels-sciences` (unités, chimie, formules en gras), `rappels-histoire`
(siècles, numéros de règne, av. J.-C., sigles d'histoire-géographie et d'EMC), `rappels-francais`
(abréviations de grammaire), `rappels-anglais` (sons de l'alphabet phonétique, abréviations
sb/sth/BV/V-ing, niveaux du CECRL, structures « BE + V-ing » en gras). Ajouter les règles d'une matière = ajouter une extension et
l'activer dans `extensions:`, sans toucher au cœur ni aux pages.

**Outils.** Un outil fourni garde exactement le format de `docs/OUTILS-CONTRAT.md`
(`outil.yaml` + `index.html`, `.js`, `.css`), vérifié et servi de la même façon, sous
`/api/eleve/outils/<id>`. Son dossier est l'extension elle-même si l'outil porte l'id de
l'extension (cas des trois outils de référence), sinon le sous-dossier `extensions/<ext>/<id>/`.
Le dossier `outils/` reste lu en premier (rétrocompatibilité) ; un id en double est écarté.

**Modules.** Une extension qui fournit des modules met le code de chacun dans
`extensions/<id>/<module>.py`, avec une classe `Brique(Module)` — le même contrat que les modules
de `jules/modules/` (voir `jules/modules/base.py`). Ils sont instanciés au démarrage, **après** les
modules de `config.yaml`, avec des réglages vides, et traités exactement comme eux : contribution
au prompt, tâches, routes (`/api/modules/<id-du-module>`, `/api/eleve/<id-du-module>`) et points
d'accroche. Un module dont l'id est déjà pris, ou qui ne se charge pas, est écarté et journalisé.
Un manifeste qui déclare un module dont le fichier est absent est refusé. Attention : ce code
s'exécute dans le serveur avec les droits de Jules ; c'est pourquoi une extension n'est chargée que
si la famille l'a activée dans `extensions:`, et pourquoi ses permissions se déclarent.

## Le cœur ne connaît aucune extension par son nom

Comme dans Hermes : si une capacité manque, on élargit le contrat (une nouvelle clé sous
`fournit:` ou `permissions:`), on n'ajoute jamais un cas particulier pour l'id d'une extension
précise dans le code du cœur.

## Points d'accroche

Ces événements du parcours de l'élève permettent aux extensions de réagir, sans appeler le modèle
d'IA elles-mêmes ni voir plus que ce que l'événement leur donne. Un point d'accroche est une
méthode de `Module` (`jules/modules/base.py`) qui ne fait rien par défaut : un module n'implémente
que ceux dont il a besoin, et tous les modules chargés (ceux de `config.yaml` comme ceux des
extensions actives) sont prévenus, sans aucun cas particulier par nom.

| Point d'accroche | Se déclenche quand | État |
|---|---|---|
| `bloc_consulte(conv, adresse, notion)` | l'élève clique sur un bloc de fiche visuelle | **câblé** |
| `fin_de_seance(conv)` | l'élève ferme l'application ou reste inactif | **câblé** |
| `exercice_repondu` | l'élève valide une réponse dans un outil ou une leçon | réservé |
| `question_eleve` | l'élève pose une question dans le chat | réservé |
| `rapport_du_soir` | le bilan quotidien pour le parent est généré | réservé |

Les trois derniers sont réservés pour Jules commentateur et le rapport mémoire de fin de séance.

**Ce que reçoit un module.**
- `bloc_consulte(conv, adresse, notion=None)` : `adresse` est l'adresse du bloc ou de l'élément
  touché (`fiche/<id>`, `fiche/<id>/<sous-id>`, `carte/<id>`, `graphe/<id>`... : celle de
  `data-adresse` dans la page, la plus précise sous le clic) ; `notion` est l'id de la notion de la
  fiche ouverte. `conv` est la conversation en cours si la page en a une, sinon `None` — la page
  « Mes fiches » n'en a pas, donc `None` en pratique.
- `fin_de_seance(conv)` : `conv` est la dernière conversation touchée pendant la séance, ou `None`.
- Rien d'autre : pas d'accès au dossier de l'élève au-delà de ce que le module obtient déjà par
  son `tuteur`, aucun appel IA déclenché par le mécanisme. Un module qui veut interroger un modèle
  le fait dans son propre code, avec `appel_ia: true` dans son manifeste. Recevoir un événement ne
  demande aucune permission ; seul agir dessus (réseau, appel IA, écriture, notification) en demande.
- Les modules sont prévenus en tâche de fond (même fil que `apres_echange`) : un clic n'attend
  jamais un module lent, et une exception dans un module est journalisée sans gêner les autres.

**Du clic au module.** `accueil.js` envoie `POST /api/seance/bloc_consulte`
(`{adresse, notion, conversation?}`, code élève requis, adresse validée) ; le serveur appelle
`Tuteur.bloc_consulte`, qui prévient tous les modules.

**Choix pour `fin_de_seance` : deux signaux, une seule séance.** Le serveur tient une « séance » :
elle s'ouvre à la première activité de l'élève (un bloc consulté, un message envoyé) et se prolonge
à chaque activité. Elle se termine — une seule fois, l'événement n'est jamais émis deux fois —
dès qu'un de ces signaux arrive :
1. **Fermeture de la page** : `commun.js` envoie `navigator.sendBeacon("/api/seance/fin")` à
   `pagehide` (plus fiable que `fetch` à la fermeture d'un onglet, et pas déclenché par un simple
   changement d'onglet, contrairement à `visibilitychange`). Passer de « Mes fiches » au chat
   ferme aussi la page, donc la séance, puis en ouvre une autre : acceptable, une séance courte
   vaut mieux qu'une séance perdue.
2. **Inactivité** (`INACTIVITE_S`, 20 minutes dans `jules/moteur.py`) : la boucle du planificateur
   (`Planificateur(veilles=[tuteur.verifier_inactivite])`, toutes les 30 s) clôt la séance d'un élève
   parti sans signal (tablette éteinte, navigateur tué). Et si l'élève revient après une longue
   pause avant que la veille ait tourné, la séance périmée est close *avant* d'en ouvrir une
   nouvelle (cas du « changement de notion après inactivité »).

Pas de séance ouverte : le signal de fermeture ne fait rien (un beacon peut partir sans qu'on ait
rien fait, ou plusieurs fois).

## Validation du manifeste

`jules/extensions.py` refuse une extension avec un message clair (en français) si :
- `extension.yaml` est absent, illisible, ou n'est pas un objet YAML ;
- `id` ne correspond pas au nom du dossier, ou n'est pas au format `minuscules-et-tirets` ;
- `titre`, `version` ou `licence` manquent ;
- `fournit` ou `permissions` contiennent une clé inconnue du contrat ci-dessus ;
- une valeur de `fournit.*` n'est pas une liste de textes, ou une valeur de `permissions.*`
  n'est pas un booléen ;
- elle fournit des figures sans `gabarit.js`, ou avec un motif interdit dans ce fichier ;
- sa clé `discussion` cite un gabarit absent de `fournit.figures`, n'a pas de phrase `quand`, porte
  un `revele` qui n'est pas un booléen, ou
  déclare une valeur sans exactement `min`, `max`, `pas`, `defaut` numériques avec `pas > 0` et
  `min ≤ defaut ≤ max` (mêmes règles que les curseurs d'une fiche visuelle) ;
- elle fournit un module dont le fichier `<module>.py` est absent, ou dont l'id n'est pas de la forme
  `minuscules_et_underscores`.

Une extension refusée est écartée et journalisée (comme une bibliothèque ou un outil invalide) :
Jules continue sans elle, jamais un chargement à moitié fait.

## Ordre de réalisation (rappel de `jules_architecture_plugins.md`)

1. **Ce document et le chargeur**, en gardant les briques existantes inchangées (fait ici).
2. Transformer les 5 figures et les 3 outils en extensions : preuve que le contrat tient
   (fait : voir « Figures, outils et modules » ci-dessus ; `extensions/exemple-figure/` reste un exemple
   non activé).
3. Brancher les points d'accroche `bloc_consulte` et `fin_de_seance` (fait : voir « Points
   d'accroche » ci-dessus ; `extensions/exemple-observateur/` en est l'exemple, non activé).
4. Le catalogue communautaire et l'installation par empreinte.
