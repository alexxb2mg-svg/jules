# Les outils : contrat de travail (étape 3)

Ce document fixe ce que chaque partie de l'étape 3 attend des autres, écrit **avant** le code
pour que plusieurs personnes (ou agents) travaillent en parallèle sans se marcher dessus.
En cas de doute, ce document fait foi ; s'il est faux ou incomplet, le dire dans son rapport
plutôt que de le contourner en silence.

Références : `docs/VISION.md` (section 2 « Des outils par matière », section 4 « La sécurité
des outils », et les « Trois règles »).

## La règle de fond

**Un outil ne fait pas le travail à la place de l'élève.** Une calculatrice qui résout
l'équation posée en devoir n'a pas sa place dans Jules ; une calculatrice qui fait les
opérations et laisse l'élève poser le raisonnement, oui. Un outil qui « remarque l'hésitation
et la comble » fait le travail à la place de l'élève, même avec de bonnes intentions
(1re règle du projet). Concrètement :

- un outil d'exercice ne reçoit **jamais** la réponse attendue (voir la frise chronologique :
  la variante « exercice » ne reçoit que des titres d'événements, jamais leurs dates) ;
- un outil ne corrige pas lui-même : il décrit à Jules ce que l'élève a fait (un événement)
  et c'est Jules, côté serveur, qui réagit — par une question, jamais par la réponse
  (2e partie de la 1re règle) ;
- un outil qui affiche un contenu déjà donné (le lexique, la frise en mode « afficher ») ne
  fabrique rien à la place de l'élève : il montre ce que la leçon lui a transmis.

## 1. Fiche d'identité (`outils/<id>/outil.yaml`)

```yaml
id: frise-chronologique          # doit être le nom du dossier
titre: "Frise chronologique"
matieres: [histoire, histoire-des-arts]
niveaux: [CM1, CM2, 6e, 5e, 4e, 3e, 2de, 1re, Tle]
entree: index.html                # page de l'outil, relative au dossier, jamais ".." ni absolue
actions:                          # ce que Jules (ou la leçon) peut demander à l'outil
  - afficher_periode
  - exercice_remettre_dans_l_ordre
evenements:                       # ce que l'outil peut dire à Jules
  - evenement_consulte
  - reponse_proposee
permissions: []                   # vide = aucun accès en dehors de l'outil (cas normal, voir §4)
auteurs: ["pseudo-github"]
licence: MIT
```

Champs obligatoires : `id` (identique au nom du dossier, minuscules et tirets), `titre`,
`entree` (fichier existant dans le dossier), `licence` (non vide). `actions` et `evenements`
sont des listes d'identifiants `minuscules_avec_underscores` (peuvent être vides). `matieres`
et `niveaux` sont informatifs (choix de l'outil dans une leçon).

### Chargeur (`jules/outils.py`)

`lire_outil(dossier) -> Outil` lit et vérifie une fiche ; refuse (message clair en français) :
fiche absente ou illisible, `id` différent du nom du dossier, `entree` absente ou hors du
dossier, `actions`/`evenements` mal formés, **permission non explicitement validée**
(`PERMISSIONS_CONNUES`, vide pour l'instant — voir §4), licence manquante, et tout motif
interdit détecté dans le code de l'outil (voir §4, premier filtre automatique).

`charger_outils(racine, dossiers_extensions) -> dict[str, Outil]` charge tous les dossiers de
`outils/`, puis ceux des outils fournis par les extensions actives (`docs/EXTENSIONS.md` ; les
trois outils de référence vivent dans `extensions/<id>/` depuis l'étape 2 des extensions) ; un outil
qui échoue à la vérification est écarté et journalisé, Jules continue sans lui (même logique
que `jules/bibliotheques.py`). `Outil.publique()` ne renvoie jamais le contenu des fichiers,
seulement l'identité (id, titre, matières, niveaux, actions, évènements) : c'est ce que
l'interface (et Jules) peuvent connaître d'un outil sans l'ouvrir.

## 2. Actions et évènements : le seul canal

L'outil et Jules ne communiquent que par `postMessage`, et seulement avec les actions et
évènements déclarés dans sa fiche. Tout le reste est ignoré, sans erreur ni effet de bord.

```yaml
# dans une leçon (jules-cours, format déjà accepté par jules/lecons.py, bloc "outil")
- type: outil
  outil: frise-chronologique
  action: afficher_periode
  donnees: {debut: 1914, fin: 1918, evenements: [{id: "verdun", titre: "Bataille de Verdun", annee: 1916}]}
```

**Jules → outil** (message envoyé à l'iframe) :

```json
{"type": "action", "action": "afficher_periode", "donnees": {"...": "..."}}
```

**Outil → Jules** (message envoyé par l'iframe à la page) :

```json
{"type": "evenement", "evenement": "evenement_consulte", "donnees": {"...": "..."}}
```

### Schéma et validation (des deux côtés)

- Un message reçu qui n'est pas un objet, dont `type` n'est pas `"action"` (côté outil) ou
  `"evenement"` (côté page), ou dont l'`action`/l'`evenement` n'est pas dans la liste connue
  (celle déclarée dans la fiche) est **ignoré silencieusement** : pas d'exception, pas
  d'affichage, pas de transmission. C'est ce qui permet à n'importe quelle page de coexister
  sans qu'un outil mal intentionné ou buggé perturbe l'autre.
- `donnees` est relu champ par champ (jamais transmis tel quel à l'affichage ou au DOM sans
  échappement) : un outil affiche des textes fournis par la leçon, jamais du HTML.
- Chaque outil de référence embarque sa propre petite fonction de validation (voir
  `outils/*/outil.js`, fonction `recu(event)`) : c'est volontairement dupliqué (pas de fichier
  partagé entre outils) pour qu'un outil reste un dossier autonome, lisible et vérifiable seul.

### Origine opaque : un choix documenté

L'iframe tourne en `sandbox="allow-scripts"` **sans** `allow-same-origin` : son origine est
donc opaque (`null`), à la fois pour elle-même et vue par la page hôte. Deux conséquences,
assumées :

1. Quand l'outil répond (`window.parent.postMessage(message, "*")`), il ne peut pas viser une
   origine précise puisqu'il ne connaît pas celle de la page hôte de façon fiable : `"*"` est
   le seul choix possible ici. Ce n'est pas une fuite de données : le message ne doit jamais
   contenir d'information que l'outil ne connaît pas déjà (jamais de prénom, de profil, de
   photo — l'outil ne reçoit que ce que la leçon lui transmet, cf. §4).
2. C'est donc à la **page hôte** de se protéger : vérifier `event.source === iframe.contentWindow`
   (jamais se fier à `event.origin`, qui vaudra `"null"`), puis valider strictement le schéma
   avant d'utiliser `donnees`. Ce sera la responsabilité du code d'intégration (`cours.js`,
   à l'étape suivante) — documenté ici pour que l'intégrateur ne l'oublie pas.

## 3. Isolement technique

- Chaque outil tourne dans une `iframe sandbox="allow-scripts"`, **sans** `allow-same-origin` :
  il n'a donc accès ni au cookie de session, ni au DOM de la page de Jules, ni à `localStorage`
  du site (origine opaque).
- **Aucun accès réseau** : la CSP servie avec chaque fichier de l'outil est
  `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self';
  connect-src 'none'; frame-src 'none'; frame-ancestors 'self'; form-action 'none'; base-uri 'none'`.
  `connect-src 'none'` bloque `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, les
  `<img>`/`<link>` externes sont bloquées par `img-src 'self'`/`style-src 'self'` : tout ce dont
  l'outil a besoin doit être dans son propre dossier (voir aussi le premier filtre automatique
  ci-dessous, qui refuse déjà `fetch(`, `XMLHttpRequest`, `WebSocket`, une adresse `http(s)://`
  en dur, ainsi que `eval(`, `new Function(`, `import()` dynamique et `document.cookie`).
- `frame-ancestors 'self'` remplace, pour les seules routes de l'outil, le
  `X-Frame-Options: DENY` par défaut de l'application (voir `ENTETES_SECURITE` dans
  `jules/web/app.py`) : sans quoi l'iframe ne s'afficherait même pas depuis la page `/cours`
  du même site. `jules/modules/outils.py` fixe explicitement `X-Frame-Options: SAMEORIGIN`
  sur ses réponses pour la même raison (l'en-tête par défaut n'écrase jamais un en-tête déjà
  posé par la route, voir le middleware `entetes_securite`, qui utilise `setdefault`).
- L'outil ne voit **que ce que la leçon lui transmet** dans `donnees` : jamais le prénom de
  l'élève, son profil, ses conversations ou ses photos. C'est la leçon (et Jules) qui décident
  quoi transmettre ; l'outil ne demande jamais rien de plus.
- Une permission supplémentaire (par exemple le micro pour un outil de prononciation) doit
  être déclarée dans `permissions`, mais **aucune n'est validée pour l'instant**
  (`PERMISSIONS_CONNUES` est vide dans `jules/outils.py`) : tant qu'une permission n'a pas été
  ajoutée à cette liste après discussion avec les mainteneurs, la fiche qui la déclare est
  refusée au chargement. Les trois outils de référence de cette étape déclarent `permissions: []`.

### Premier filtre automatique (avant la relecture humaine)

`jules/outils.py` (`_controler_code`) relit chaque fichier `.html`/`.js`/`.css` de l'outil et
refuse au chargement s'il contient une adresse `http(s)://` en dur, ou l'un des motifs
`fetch(`, `XMLHttpRequest`, `WebSocket`, `eval(`, `new Function(`, `import(` dynamique,
`new Worker(`, `navigator.sendBeacon`, `document.cookie`. Ce n'est **pas** la protection
principale (elle peut être contournée par de l'obfuscation) : la vraie barrière est l'iframe
sandbox et la CSP ci-dessus. C'est un filtre de premier niveau, qui écarte tout de suite les
outils manifestement hors contrat, avant même l'étape 1 de la validation ci-dessous.

## 4. Validation avant publication (rappel de `docs/VISION.md`, section 4)

1. **Contrôles automatiques** : fiche conforme, aucune adresse externe dans le code, taille
   limitée, pas d'exécution de code dynamique (voir le filtre ci-dessus), licence compatible,
   tests de l'outil qui passent.
2. **Relecture du code** par deux mainteneurs, dont un qui n'a pas participé à l'outil.
3. **Relecture pédagogique** : l'outil aide à apprendre et ne donne pas la réponse.
4. **Relecture d'accessibilité** : utilisable au clavier, contrastes suffisants.
5. **Empreinte enregistrée** : le catalogue retiendra l'empreinte de la version validée
   (mécanisme à construire à une étape suivante ; non implémenté ici).

## 5. Comment un outil est servi (`jules/modules/outils.py`)

Le module `outils` (`jules/modules/outils.py`, `id = "outils"`) charge les fiches
(`charger_outils(config.racine / "outils")`) et les sert **sans toucher à
`jules/web/app.py`**, via le mécanisme existant `routes_eleve()` (monté automatiquement sous
`/api/eleve/outils`, cookie élève exigé — cohérent avec le fait qu'un outil ne s'ouvre que
depuis une leçon déjà en cours) :

| Méthode et chemin | Réponse |
|---|---|
| `GET /api/eleve/outils/catalogue` | `[Outil.publique(), ...]` |
| `GET /api/eleve/outils/<id>` ou `/<id>/` | le fichier `entree` de l'outil |
| `GET /api/eleve/outils/<id>/<chemin>` | un fichier du dossier de l'outil |

Toute réponse de fichier porte les en-têtes de §3 (CSP propre à l'outil, `X-Frame-Options:
SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
`Cache-Control: no-store`). `outil.yaml` n'est jamais servi ; un chemin qui sort du dossier de
l'outil (`..`, chemin absolu) est refusé (404) ; seules les extensions `.html`, `.js`, `.css`
sont servies (pas de `.json`, pas de police, pas d'image : les trois outils de référence
embarquent leurs données directement dans leur script, précisément pour ne pas avoir besoin
d'un appel réseau même same-origin — que `connect-src 'none'` bloquerait de toute façon).

Pour activer le module, ajouter dans `config.yaml` (voir `docs/exemples/config-outils.exemple.yaml`,
livré avec `actif: false` — l'activation réelle et l'accrochage au bloc `outil` des leçons se
feront à l'intégration, décrits dans la description de la pull request de cette étape) :

```yaml
modules:
  - id: outils
    actif: false
```

## 6. Qui touche quoi (branches séparées, fusion par l'intégrateur)

| Lot | Fichiers (et seulement eux) |
|---|---|
| Chargeur et contrat | `jules/outils.py`, `docs/OUTILS-CONTRAT.md`, `tests/test_outils.py` |
| Service HTTP | `jules/modules/outils.py`, `jules/config.py` (ajout de `dossier_outils`), `tests/test_module_outils.py` |
| Outils de référence | `outils/frise-chronologique/**`, `outils/calculatrice/**`, `outils/lexique/**` |
| Exemple de configuration | `docs/exemples/config-outils.exemple.yaml` |
| Intégration (étape suivante, hors périmètre ici) | `config.yaml` (activation), `jules/web/static/cours.js` (ouverture de l'iframe, écoute des évènements), `jules/lecons.py` (déjà prêt : le bloc `outil` est accepté depuis l'étape 2) |
