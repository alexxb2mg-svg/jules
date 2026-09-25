# Jules — le contrat d'extension

Statut : première étape (voir `jules_architecture_plugins.md`, ordre de réalisation). Le
chargeur (`jules/extensions.py`) existe et est testé, mais rien dans le cœur ne dépend encore
d'une extension : les six familles historiques (modules, moteurs, notifieurs, outils, figures,
bibliothèques) continuent de fonctionner exactement comme avant, sans passer par ce contrat.
C'est une couche ajoutée, pas un remplacement.

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
  outils: []             # ids de outils/<id>/
  figures: [exemple-cercle]        # ids de gabarits (jules/web/static/gabarits/<id>.js)
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
  n'est pas un booléen.

Une extension refusée est écartée et journalisée (comme une bibliothèque ou un outil invalide) :
Jules continue sans elle, jamais un chargement à moitié fait.

## Ordre de réalisation (rappel de `jules_architecture_plugins.md`)

1. **Ce document et le chargeur**, en gardant les briques existantes inchangées (fait ici).
2. Transformer les 5 figures et les 3 outils en extensions : preuve que le contrat tient
   (reste à faire — une seule figure d'exemple existe pour l'instant, voir `extensions/exemple-figure/`).
3. Brancher les points d'accroche `bloc_consulte` et `fin_de_seance`.
4. Le catalogue communautaire et l'installation par empreinte.
