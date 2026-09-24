# Format d'une leçon — guide pour un contributeur

Ce document explique comment écrire une leçon pour Jules, sans savoir programmer.
Le contrat technique complet (pour les développeurs) est dans `docs/COURS-CONTRAT.md` ;
ce document-ci en est la version pratique, pour écrire un fichier.

## 1. Où va une leçon

Une leçon est un fichier YAML, dans une **bibliothèque de type `lecons`** :

```
bibliotheque/<id-de-la-bibliotheque>/
  bibliotheque.yaml              # fiche d'identité de la bibliothèque (voir bibliotheque/README.md)
  lecons/
    <matiere>/
      <notion>.yaml               # une leçon = un fichier
```

- `<matiere>` est un dossier libre, pour s'y retrouver (ex. `maths`, `francais`).
- `<notion>` (nom du fichier, sans `.yaml`) n'a pas besoin de correspondre à l'identifiant de la
  notion : c'est le champ `notion` **à l'intérieur** du fichier qui compte.
- La bibliothèque elle-même a `type: lecons` dans son `bibliotheque.yaml`, avec un `statut`
  (`experimentale`, `exemple`, `enseignant`, `certifiee`) et une `licence`, comme les autres
  bibliothèques. Voir `bibliotheque/README.md` pour ces champs communs.

## 2. Une leçon porte sur une seule notion

La notion doit déjà exister dans le référentiel du programme (`bibliotheque/programme/`).
Si l'identifiant que vous écrivez n'existe pas, la leçon est refusée au chargement.

Pour trouver l'identifiant exact d'une notion, cherchez son fichier dans
`bibliotheque/programme/3e/<matiere>.yaml`.

## 3. Squelette d'une leçon

```yaml
notion: parallelisme-triangles-pythagore   # obligatoire : identifiant exact du référentiel
titre: "Le théorème de Pythagore"          # obligatoire
duree_minutes: 25                          # indicatif, pour information seulement
auteurs: ["pseudo"]                        # facultatif
licence: CC-BY-SA-4.0                      # obligatoire (ou héritée de la bibliothèque)

sources:                                   # obligatoire : au moins une
  - titre: "Manuel de mathématiques 3e"
    url: "https://..."
    licence: CC-BY-SA-4.0

relecture:
  statut: a_relire                         # a_relire | relue

blocs:                                     # obligatoire : entre 3 et 20
  - type: objectifs
    ...
  - type: texte
    ...
  # ... 1 à 18 blocs de plus, voir la liste des types plus bas
```

Une leçon a **entre 3 et 20 blocs**. En dessous, ce n'est pas une vraie leçon ; au-dessus,
c'est trop long pour une séance et doit être coupé en plusieurs leçons.

## 4. Les sept types de blocs

Chaque bloc a un champ `type`. Voici les sept types possibles, avec un exemple court.

### `objectifs` — ce que l'élève va savoir faire

```yaml
- type: objectifs
  items:
    - "Calculer la longueur d'un côté d'un triangle rectangle"
    - "Reconnaître un triangle rectangle dans une figure"
```

### `texte` — un morceau de cours

```yaml
- type: texte
  titre: "L'idée"
  contenu: |
    Dans un triangle rectangle, le carré de l'hypoténuse est égal à la somme des carrés
    des deux autres côtés : **BC² = AB² + AC²**.
```

`contenu` accepte un Markdown restreint (gras, italique, listes, tableaux) — pas de HTML,
pas de scripts.

### `exemple` — un exercice déjà résolu, montré à l'élève

Choisissez un exercice **différent** de ceux de la leçon : le but est de montrer la méthode,
pas de donner la réponse d'un exercice que l'élève va devoir faire.

```yaml
- type: exemple
  enonce: "Le triangle DEF est rectangle en D, DE = 3 cm, DF = 4 cm. Calcule EF."
  etapes:
    - "L'angle droit est en D, donc l'hypoténuse est EF."
    - "EF² = DE² + DF² = 9 + 16 = 25"
    - "EF = 5 cm"
```

### `exercice` — l'élève doit essayer avant que Jules aide

C'est le bloc le plus riche. Trois formes possibles : `nombre`, `reponse_courte`, `qcm`.

```yaml
- type: exercice
  enonce: "Le triangle ABC est rectangle en A, AB = 6 cm, AC = 8 cm. Calcule BC."
  forme: nombre                # nombre | reponse_courte | qcm
  reponse: 10                  # NE QUITTE JAMAIS LE SERVEUR (voir §6)
  tolerance: 0.01               # forme nombre seulement : écart accepté
  unite: cm                     # affichée à côté du champ de réponse
  indices:                      # progressifs, demandés par l'élève un par un
    - "Quel est le plus grand côté du triangle ?"
    - "Écris l'égalité de Pythagore."
  explication: "BC² = AB² + AC² = 36 + 64 = 100, donc BC = 10 cm."   # NE QUITTE JAMAIS LE SERVEUR
```

- Forme `reponse_courte` : ajoutez `reponses_acceptees: [...]` pour les variantes admises
  (Jules ignore déjà la casse, les accents et la ponctuation finale).
- Forme `qcm` : ajoutez `choix: ["...", "..."]` (au moins deux) ; `reponse` est soit le
  numéro du bon choix (0 pour le premier), soit son texte exact.
- **Un indice ne doit jamais contenir la réponse.** Une leçon avec un indice du genre
  « la réponse est 10 cm » est refusée au chargement.

### `question_ouverte` — Jules relit, ne corrige pas comme un exercice fermé

```yaml
- type: question_ouverte
  question: "Pourquoi l'hypoténuse est-elle toujours le plus grand côté ?"
  indices:
    - "Regarde où se trouve l'angle droit."
  criteres:                    # NE QUITTE JAMAIS LE SERVEUR : ce que Jules regarde pour relire
    - "L'élève relie la position de l'angle droit à la longueur du côté opposé"
```

### `synthese` — l'élève écrit ce qu'il retient, avec ses mots

```yaml
- type: synthese
  consigne: "Écris en deux phrases ce que tu retiens du théorème de Pythagore."
```

Jules ne génère jamais ce résumé à la place de l'élève (règle 2 du contrat).

### `outil` — réservé pour plus tard (étape 3)

Le format est accepté dès maintenant, mais l'outil n'est pas encore branché : il s'affiche
« à venir » à l'élève.

```yaml
- type: outil
  outil: frise-chronologique
  action: afficher_periode
  donnees: {}
```

## 5. Ce qui fait refuser une leçon au chargement

Une leçon non conforme n'empêche pas les autres de se charger : elle est simplement écartée,
avec un message clair dans le journal du serveur. Voici les raisons de refus :

| Raison | Détail |
|---|---|
| Notion inconnue | le champ `notion` n'existe pas dans le référentiel chargé |
| Titre manquant | `titre` vide ou absent |
| Type de bloc inconnu | autre chose que les sept types du §4 |
| Exercice sans réponse | un bloc `exercice` sans champ `reponse` |
| Exercice sans énoncé | un bloc `exercice` sans champ `enonce` |
| Forme d'exercice inconnue | autre chose que `nombre`, `reponse_courte`, `qcm` |
| QCM sans choix | moins de deux `choix` |
| QCM avec une réponse hors choix | `reponse` ne correspond à aucun élément de `choix` |
| Exercice `nombre` avec une réponse non numérique | `reponse` doit pouvoir se lire comme un nombre |
| Un indice contient la réponse | garde-fou automatique, voir §4 |
| Question ouverte sans question | bloc `question_ouverte` sans champ `question` |
| Synthèse sans consigne | bloc `synthese` sans champ `consigne` |
| Moins de 3 blocs ou plus de 20 | une leçon doit tenir dans cette fourchette |
| Aucune source | `sources` vide ou absent |
| Licence non libre | voir §7 |
| Fichier trop gros | plus de 200 ko : une leçon est un texte court, pas un manuel |
| YAML illisible | erreur de syntaxe dans le fichier |

## 6. La réponse ne quitte jamais le serveur

Les champs `reponse`, `reponses_acceptees`, `tolerance`, `explication`, `criteres` ne sont
**jamais** envoyés au navigateur de l'élève, à aucun moment, même après une tentative
(l'élève reçoit seulement juste/faux, puis l'explication au bon moment — voir le contrat §3).
C'est vérifié automatiquement par les tests (`tests/test_lecons.py`) : ils cherchent la valeur
de la réponse dans tout ce que la leçon publie et échouent si elle s'y trouve.

Pourquoi : si la réponse partait avec la page, n'importe qui pourrait la lire dans les outils
du navigateur avant même d'essayer. La règle « l'élève essaie d'abord » (règle 1 du contrat)
ne tiendrait pas.

Conséquence pour vous, contributeur : ne mettez **jamais** la réponse ailleurs que dans les
champs prévus (`reponse`, `reponses_acceptees`, `tolerance`, `explication`, `criteres`) — pas
dans `enonce`, pas dans un `indice`, pas dans `contenu`. Ces autres champs partent tels quels
vers l'élève.

## 7. Licences acceptées

Comme pour les fiches (`bibliotheque/README.md`), le contenu doit être publiable et réutilisable
librement. Licences acceptées : domaine public, CC0, CC BY, CC BY-SA, Licence Ouverte
(`etalab-2.0`), GFDL, MIT. Refusées : NC (pas d'usage commercial), ND (pas de modification),
« droits réservés », « usage en classe seulement », ou toute licence non reconnue.

La `licence` se met soit sur la leçon elle-même, soit elle est héritée de la bibliothèque
(`bibliotheque.yaml`) si le fichier de la leçon ne la précise pas.

## 8. Avant de proposer une leçon

1. Vérifiez que la notion existe dans `bibliotheque/programme/3e/<matiere>.yaml`.
2. Relisez vos calculs : une réponse fausse dans une leçon envoie l'élève sur une fausse piste.
3. Vérifiez qu'aucun indice ne donne la réponse.
4. Citez vos sources, avec leur licence.
5. Laissez `relecture: {statut: a_relire}` tant qu'un enseignant n'a pas relu le contenu.
