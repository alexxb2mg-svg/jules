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

## Figures, outils et modules (branchés aux étapes 2 et 3)

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
