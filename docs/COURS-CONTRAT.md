# Interface de cours : contrat de travail (étape 2)

Ce document fixe ce que chaque partie de l'étape 2 attend des autres. Il est écrit **avant** le code
pour que plusieurs personnes (ou agents) travaillent en parallèle sans se marcher dessus.
En cas de doute, ce document fait foi ; s'il est faux ou incomplet, le dire dans son rapport
plutôt que de le contourner en silence.

Références : `docs/VISION.md` (section 3 « Une interface de cours, pas de chat », et les
« Trois règles »), maquette `docs/maquette-cours.png`.

## Les trois règles, appliquées au cours

1. **L'élève essaie d'abord.** Jules ne parle de lui-même qu'après une tentative de l'élève
   (réponse à un exercice ou à une question ouverte), et seulement par une question.
   Les indices sont progressifs et demandés par l'élève.
2. **L'élève produit, Jules relit.** Le bloc `synthese` fait écrire l'élève ; Jules relit.
   Aucun bloc ne génère un résumé à la place de l'élève.
3. **L'adulte compte plus que le réglage.** Les tentatives et le résultat alimentent le suivi,
   donc le bilan du soir.

**La réponse attendue ne quitte jamais le serveur** avant la tentative : les champs
`reponse`, `reponses_acceptees`, `tolerance`, `explication`, `criteres` sont retirés de tout ce
qui part vers le navigateur (`Bloc.public()`). `explication` n'est envoyée qu'après une
tentative juste, ou après `TENTATIVES_AVANT_CORRECTION` (3) tentatives.

## 1. Format d'une leçon (fichier YAML)

Une leçon porte sur **une notion du référentiel** (identifiant du programme, ex.
`parallelisme-triangles-pythagore`). Les leçons vivent dans une bibliothèque de type `lecons` :

```
bibliotheque/<id>/bibliotheque.yaml     # type: lecons (statut, licence, avertissement comme les autres)
bibliotheque/<id>/lecons/<matiere>/<notion>.yaml
```

```yaml
notion: parallelisme-triangles-pythagore   # obligatoire, doit exister dans le référentiel chargé
titre: "Le théorème de Pythagore"          # obligatoire
duree_minutes: 25                           # indicatif
auteurs: ["pseudo"]
licence: CC-BY-SA-4.0                        # licence libre (liste LICENCES_LIBRES de bibliotheques.py)
sources:                                     # d'où vient le contenu (au moins une)
  - titre: "..."
    url: "https://..."
    licence: CC-BY-SA-4.0
relecture: {statut: a_relire}                # a_relire | relue
blocs:                                       # 3 à 20 blocs
  - type: objectifs
    items: ["Calculer la longueur d'un côté d'un triangle rectangle", "..."]
  - type: texte
    titre: "L'idée"
    contenu: "Markdown restreint (gras, italique, listes, tableaux)."
  - type: exemple            # exemple résolu sur un AUTRE exercice que ceux de la leçon
    enonce: "..."
    etapes: ["...", "..."]
  - type: exercice
    enonce: "Le triangle ABC est rectangle en A, AB = 6 cm, AC = 8 cm. Calcule BC."
    forme: nombre            # nombre | reponse_courte | qcm
    reponse: 10              # SERVEUR SEULEMENT
    tolerance: 0.01          # SERVEUR SEULEMENT (nombre)
    unite: cm                # affichée
    reponses_acceptees: []   # SERVEUR SEULEMENT (reponse_courte : variantes admises)
    choix: []                # qcm : liste affichée ; reponse = index (0...) ou texte exact du choix
    indices: ["Quel est le plus grand côté ?", "Écris l'égalité de Pythagore.", "BC² = 36 + 64"]
    explication: "BC² = AB² + AC² = 36 + 64 = 100, donc BC = 10 cm."   # SERVEUR SEULEMENT
  - type: question_ouverte
    question: "Pourquoi l'hypoténuse est-elle toujours le plus grand côté ?"
    indices: ["...", "..."]
    criteres: ["...", "..."]  # SERVEUR SEULEMENT : ce que Jules regarde pour relire
  - type: synthese
    consigne: "Écris en deux phrases ce que tu retiens, avec tes mots."
  - type: outil              # étape 3 : format accepté, affiché comme « outil à venir »
    outil: frise-chronologique
    action: afficher_periode
    donnees: {}
```

Règles de validation (refus au chargement, message clair en français) : notion inconnue,
type de bloc inconnu, exercice sans `reponse`, `forme` inconnue, `qcm` sans `choix` ou avec une
réponse hors des choix, `indices` qui contiennent la réponse d'un exercice `nombre` ou
`reponse_courte` (garde-fou : un indice n'est pas la réponse), moins de 3 ou plus de 20 blocs,
aucune source, licence non libre, fichier > 200 ko.

## 2. Module Python `jules/lecons.py` (lecture, vérification)

Signatures figées (le squelette est dans le dépôt) :

```python
TYPES_BLOCS = ("objectifs", "texte", "exemple", "exercice", "question_ouverte", "synthese", "outil")
FORMES_EXERCICE = ("nombre", "reponse_courte", "qcm")
CHAMPS_SERVEUR = ("reponse", "reponses_acceptees", "tolerance", "explication", "criteres")
TENTATIVES_AVANT_CORRECTION = 3

class ErreurLecon(ValueError): ...
@dataclass class Bloc:  type: str; donnees: dict; def public(self) -> dict
@dataclass class Lecon: notion, titre, matiere, niveau, bibliotheque, statut, licence,
                        duree_minutes, blocs, sources, avertissement; def publique(self) -> dict
def lire_lecon(chemin: Path, notions: dict[str, Notion], bibliotheque: Bibliotheque) -> Lecon
def charger_lecons(racine: Path, ids: list[str], notions: dict[str, Notion]) -> dict[str, Lecon]
    # racine = dossier bibliotheque/ ; ids = bibliothèques de type lecons, par ordre de priorité ;
    # une notion = une leçon (la première bibliothèque qui en fournit une l'emporte)
def verifier_reponse(bloc: Bloc, reponse: object) -> bool | None
    # None = pas de correction automatique (question_ouverte, synthese) ; sinon juste / faux.
    # nombre : virgule ou point, espaces, unité facultative, tolérance ;
    # reponse_courte : casse, accents, espaces, ponctuation finale ignorés, variantes admises ;
    # qcm : index ou texte exact.
def contient_la_reponse(texte: str, bloc: Bloc) -> bool
    # vrai si `texte` (message de Jules) donne la réponse attendue d'un exercice : garde-fou serveur.
```

`Lecon.publique()` renvoie : `{notion, titre, matiere, niveau, statut, avertissement, duree_minutes,
sources, blocs: [Bloc.public() ...]}` (chaque bloc public porte aussi `index`).

## 3. Module `cours` (serveur) et API élève

Brique `jules/modules/cours.py` (`id = "cours"`), ajoutée à `config.yaml` après `notions`,
réglages : `bibliotheques: [lecons-3e-experimentales]`. Routes élève montées sous
`/api/eleve/cours` (mécanisme `routes_eleve` existant). Conversation de la leçon en mode
`cours` (mode **caché** : fichier `consignes/modes/cours.md` avec `cache: true`).

| Méthode et chemin | Corps | Réponse |
|---|---|---|
| `GET /api/eleve/cours/parcours?matiere=<id>` | | `{matieres: [{id, nom}], matiere, notions: [{id, titre, chapitre, etat, lecon: bool}], estimation: "..."}` ; `etat` ∈ `a_venir, en_cours, bloque, compris, acquis` (dernier suivi connu), `estimation` = phrase qui dit que l'état est estimé par l'IA |
| `POST /api/eleve/cours/lecons/<notion>/ouvrir` | | `{session, conversation, lecon: Lecon.publique(), progression}` ; reprend la session en cours de cette notion si elle existe |
| `GET /api/eleve/cours/sessions/<session>` | | `{session, conversation, lecon, progression}` |
| `POST /api/eleve/cours/sessions/<session>/blocs/<index>/tentative` | `{reponse}` | `{juste: bool\|null, tentatives, explication: str\|null, jules: str\|null, progression}` |
| `POST /api/eleve/cours/sessions/<session>/blocs/<index>/indice` | | `{indice: str\|null, restants, progression}` (indices dans l'ordre, un par appel) |
| `POST /api/eleve/cours/sessions/<session>/blocs/<index>/fait` | | `{progression}` (blocs sans tentative : texte, objectifs, exemple, outil) |

`progression` = `{bloc_courant, blocs: [{index, etat, tentatives, indices_vus}], termine: bool}` ;
`etat` d'un bloc ∈ `a_faire, en_cours, reussi, a_revoir, fait`.

Comportement de la tentative :
- enregistre la tentative (état `cours`, espace de stockage `cours`) et ajoute à la conversation un
  message élève lisible : `📝 Ma réponse (bloc <n>) : <reponse>` ;
- `juste is True` : pas d'appel au modèle ; `explication` renvoyée ; bloc `reussi` ;
- `juste is False` : Jules réagit via `tuteur.echanger` (le module ajoute au prompt, par
  `contribution`, la leçon, le bloc, la réponse attendue et les critères, en rappelant les
  règles) ; si `contient_la_reponse(jules, bloc)`, **un** nouvel essai, puis à défaut une question
  de repli fixe (« Qu'est-ce qui te fait penser ça ? Reprends l'énoncé étape par étape. ») ;
  après 3 tentatives fausses : `explication` renvoyée, bloc `a_revoir` ;
- `juste is None` (question ouverte, synthèse) : Jules relit par `tuteur.echanger` (retour court,
  une question s'il manque quelque chose, jamais de corrigé rédigé à la place de l'élève) ;
  bloc `fait`.
- À la fin de la leçon (`termine`), un événement `suivi` est écrit pour la notion avec le statut
  déduit : tous les exercices réussis sans correction → `compris` ; un exercice `a_revoir` →
  `en_cours` ; ce qui nourrit l'épreuve sans aide et le bilan du soir.

Le panneau Jules « à côté » réutilise l'API existante :
`POST /api/conversations/<conversation>/messages` (l'élève peut lui écrire à tout moment).

## 4. Interface élève

Page `/cours` (`jules/web/static/cours.html`, `cours.js`, `cours.css`), même porte à code que la
page élève (`MS.porte("eleve", ...)`), aucun script ni style en ligne (politique de sécurité),
tout texte venant du serveur passe par `MS.echapper` ou `MS.markdown`.

- **Gauche, le parcours** : la matière (liste déroulante), ses notions groupées par chapitre avec
  leur état (pastilles), mention visible que l'état est estimé par l'IA. Les notions avec leçon
  sont cliquables ; les autres affichent « pas encore de leçon ».
- **Centre, la leçon** : un bloc à la fois ou en défilement, barre de progression, boutons
  « Valider », « Un indice » (compteur), « J'ai lu » ; l'explication n'apparaît qu'après la
  tentative (règle ci-dessus). Avertissement de la bibliothèque visible (contenu expérimental).
- **Droite, Jules** : le fil de la conversation de la leçon ; les réactions de Jules aux
  tentatives y arrivent ; l'élève peut écrire. Sur tablette (< 900 px), Jules devient un panneau
  qu'on ouvre d'un bouton.
- Lien d'entrée depuis la page élève : un bouton « 📘 Suivre un cours » sur l'écran d'accueil.

## 5. Qui touche quoi (branches séparées, fusion par l'intégrateur)

| Lot | Fichiers (et seulement eux) |
|---|---|
| A. Leçons : format et vérification | `jules/lecons.py`, `jules/bibliotheques.py` (type `lecons`), `bibliotheque/SCHEMA-LECON.md`, `tests/test_lecons.py`, contrôle des leçons dans `jules verifier` (`jules/cli.py`) |
| B. Contenu : trois leçons de 3e | `bibliotheque/lecons-3e-experimentales/**` |
| C. Module de cours et API | `jules/modules/cours.py`, `config.yaml`, `tests/test_cours.py`, `tests/conftest.py` (règle factice pour le mode cours, si besoin) |
| D. Interface élève | `jules/web/static/cours.html`, `cours.js`, `cours.css`, `eleve.js` (bouton d'entrée seulement), `tests/test_web.py` (ajouts seulement) |
| E. Consigne de Jules et évaluation réelle | `consignes/modes/cours.md`, `evaluation/cours/**` |
| F. Documentation | `README.md`, `CONTRIBUTING.md`, `docs/VISION.md`, `bibliotheque/README.md` |

La route de page `/cours` et ce contrat sont déjà dans la branche de base `interface-cours`.
