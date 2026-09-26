# Jules — le contrat d'extension

Statut : deuxième étape (voir `jules_architecture_plugins.md`, ordre de réalisation). Le
chargeur (`jules/extensions.py`) est branché pour deux familles : les **figures** (les cinq
gabarits des fiches visuelles sont des extensions) et les **outils** (les trois outils de
référence sont des extensions). Les autres familles (modules, moteurs, notifieurs,
bibliothèques) fonctionnent encore comme avant, sans passer par ce contrat.

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
  modules: []            # ids de jules/modules/<id>.py fournis par cette extension
  moteurs: []            # ids de jules/llm/<id>.py
  notifieurs: []         # ids de jules/notifieurs/<id>.py
  outils: []             # ids d'outils (voir « Figures et outils » ci-dessous)
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

## Figures et outils (branchés à l'étape 2)

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

**Outils.** Un outil fourni garde exactement le format de `docs/OUTILS-CONTRAT.md`
(`outil.yaml` + `index.html`, `.js`, `.css`), vérifié et servi de la même façon, sous
`/api/eleve/outils/<id>`. Son dossier est l'extension elle-même si l'outil porte l'id de
l'extension (cas des trois outils de référence), sinon le sous-dossier `extensions/<ext>/<id>/`.
Le dossier `outils/` reste lu en premier (rétrocompatibilité) ; un id en double est écarté.

## Le cœur ne connaît aucune extension par son nom

Comme dans Hermes : si une capacité manque, on élargit le contrat (une nouvelle clé sous
`fournit:` ou `permissions:`), on n'ajoute jamais un cas particulier pour l'id d'une extension
précise dans le code du cœur.

## Points d'accroche prévus (documentés, pas encore branchés)

Ces événements existeront pour que les extensions réagissent au parcours de l'élève, sans
appeler le modèle d'IA elles-mêmes ni voir plus que ce que l'événement leur donne :

| Point d'accroche | Se déclenche quand |
|---|---|
| `bloc_consulte(adresse)` | l'élève clique sur un bloc de fiche visuelle ou de leçon |
| `exercice_repondu` | l'élève valide une réponse dans un outil ou une leçon |
| `question_eleve` | l'élève pose une question dans le chat |
| `fin_de_seance` | l'élève ferme l'application ou change de notion après un moment d'inactivité |
| `rapport_du_soir` | le bilan quotidien pour le parent est généré |

Aucun de ces points n'est câblé pour l'instant : ils sont réservés pour Jules commentateur et
le rapport mémoire de fin de séance (étape 2 de `jules_architecture_plugins.md`).

## Validation du manifeste

`jules/extensions.py` refuse une extension avec un message clair (en français) si :
- `extension.yaml` est absent, illisible, ou n'est pas un objet YAML ;
- `id` ne correspond pas au nom du dossier, ou n'est pas au format `minuscules-et-tirets` ;
- `titre`, `version` ou `licence` manquent ;
- `fournit` ou `permissions` contiennent une clé inconnue du contrat ci-dessus ;
- une valeur de `fournit.*` n'est pas une liste de textes, ou une valeur de `permissions.*`
  n'est pas un booléen ;
- elle fournit des figures sans `gabarit.js`, ou avec un motif interdit dans ce fichier.

Une extension refusée est écartée et journalisée (comme une bibliothèque ou un outil invalide) :
Jules continue sans elle, jamais un chargement à moitié fait.

## Ordre de réalisation (rappel de `jules_architecture_plugins.md`)

1. **Ce document et le chargeur**, en gardant les briques existantes inchangées (fait ici).
2. Transformer les 5 figures et les 3 outils en extensions : preuve que le contrat tient
   (fait : voir « Figures et outils » ci-dessus ; `extensions/exemple-figure/` reste un exemple
   non activé).
3. Brancher les points d'accroche `bloc_consulte` et `fin_de_seance`.
4. Le catalogue communautaire et l'installation par empreinte.
