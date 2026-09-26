# Où va Jules : vision et feuille de route

Ce document décrit la direction du projet. Rien de ce qui suit n'est encore construit, sauf mention contraire. Les formats de fichiers sont des **propositions** : ils sont là pour lancer la discussion, pas pour la clore. Pour réagir, ouvrez un ticket « Idée » ou une discussion.

## L'idée en une phrase

Jules est un **harnais** qui s'adapte à l'élève : au départ il ne sait rien d'un niveau ou d'une matière. Il charge ce qu'il faut pour l'élève qu'il a en face de lui, puis il s'enrichit de ce que l'élève lui apporte.

```text
Profil de l'élève          ce que Jules charge                  ce qui l'enrichit ensuite
(âge, classe,        --->  bibliothèques de son niveau   --->   cours photographiés, devoirs,
 matières, besoins)        outils de ses matières               notions comprises ou bloquées,
                           adaptations (troubles dys...)        remarques du parent
```

Aujourd'hui Jules est un tuteur par conversation, avec quatre bibliothèques du programme officiel (CM1, 5e, 4e, 3e). La suite le fait évoluer sur quatre axes.

## Trois règles qui tiennent sur tous les axes

Ces règles viennent de l'essai dont Jules est né, [*Après la dernière main levée*](essai/). Elles servent à juger chaque proposition, y compris celles des mainteneurs.

1. **L'élève essaie d'abord.** Jules n'aide qu'après une tentative, et une intervention non demandée est toujours une question, jamais une réponse ni un indice qui la contient. Un outil qui « remarque l'hésitation et la comble » fait le travail à la place de l'élève, même avec de bonnes intentions.
2. **L'élève produit, Jules relit.** Une fiche, une carte mentale ou un quiz fabriqués par la machine ne laissent presque rien à l'élève. Jules peut proposer un modèle vide, poser des questions, corriger ; c'est l'élève qui écrit.
3. **L'adulte d'à côté compte plus que le réglage.** Les études sur les tuteurs à l'IA montrent des progrès quand un adulte est dans la boucle, pas quand l'enfant est seul avec l'outil. Ce que Jules dit au parent est donc aussi important que ce qu'il dit à l'élève.

## 1. Des bibliothèques qui se branchent

Une bibliothèque est un dossier de contenus : un programme officiel, le cours d'un enseignant, une méthode de lecture, une collection d'exercices. Chaque bibliothèque se présente dans un petit fichier qui dit à qui elle s'adresse. Jules charge celles qui correspondent au profil de l'élève et ignore les autres.

Proposition de fiche d'identité (`bibliotheque/<id>/bibliotheque.yaml`) :

```yaml
id: programme-fr-college-3e
titre: "Programme officiel français - 3e"
pays: FR
niveaux: [3e]              # CP ... CM2, 6e ... 3e, 2de, 1re, Tle
ages: [14, 15]             # indicatif, sert quand la classe n'est pas connue
matieres: [mathematiques, francais, histoire, geographie, ...]
source: officielle         # officielle | enseignant | communaute
licence: "Licence ouverte / MIT"
```

Le programme officiel est décrit à ce format sur quatre niveaux (CM1, 5e, 4e, 3e ; `bibliotheque/programme/`). Les notions gardent leur identifiant et leur source officielle, pour que Jules puisse toujours dire d'où vient ce qu'il enseigne.

**À construire avec la communauté :** les autres classes du primaire (cycles 2 et 3, hors CM1) et du collège (6e), et le lycée.

## 2. Des outils par matière

**En partie construite (étape 3).** Le contrat des outils (`docs/OUTILS-CONTRAT.md`), le chargeur (`jules/outils.py`) et le module qui les sert (`jules/modules/outils.py`) sont écrits : chaque outil tourne dans un cadre isolé (`iframe` sandbox, en-têtes propres), sans accès au réseau ni aux données de l'élève. Trois outils de référence existent comme extensions (`extensions/frise-chronologique`, `extensions/calculatrice`, `extensions/lexique`). Ce qui manque : le bloc `outil` d'une leçon n'ouvre pas encore l'outil dans la page `/cours` (il affiche « à venir », voir `jules/web/static/cours.js`), et le protocole de validation communautaire (section 4) reste à durcir avant d'accepter un outil extérieur.

La leçon ou Jules peuvent ouvrir un outil (« ouvre la frise avec ces cinq dates ») et l'outil peut dire à Jules ce que fait l'élève (« l'élève a placé Verdun avant la mobilisation »). C'est ce qui permet à Jules de réagir à une erreur sans donner la réponse : il attend que l'élève ait fini sa tentative, puis il pose une question (« Qu'est-ce qui se passe d'abord, la mobilisation ou la bataille ? »).

Proposition de fiche d'identité d'un outil (`outils/<id>/outil.yaml`) :

```yaml
id: frise-chronologique
titre: "Frise chronologique"
matieres: [histoire, histoire-des-arts]
niveaux: [CM1, CM2, 6e, 5e, 4e, 3e, 2de, 1re, Tle]
entree: index.html          # la page de l'outil
actions:                    # ce que Jules peut demander à l'outil
  - afficher_periode
  - ajouter_evenement
  - exercice_remettre_dans_l_ordre
evenements:                 # ce que l'outil peut dire à Jules
  - evenement_consulte
  - reponse_proposee
permissions: []             # vide = aucun accès en dehors de l'outil (cas normal)
auteurs: ["pseudo-github"]
licence: MIT
```

Une règle de fond s'applique aux outils comme au reste : **un outil ne fait pas le travail à la place de l'élève.** Une calculatrice qui résout l'équation posée en devoir n'a pas sa place dans Jules ; une calculatrice qui fait les opérations et laisse l'élève poser le raisonnement, oui.

## 3. Une interface de cours, pas de chat

**Construite (étape 2).** L'élève ne parle plus à une fenêtre de conversation pour suivre une leçon : il suit une **leçon en blocs**, avec Jules à côté. Voir la [maquette](maquette-cours.png), qui reste la cible visuelle (outils de matière et studio non encore branchés).

- **Au centre, le cours** : les blocs `objectifs`, `texte`, `exemple`, `exercice` (nombre, réponse courte, QCM), `question_ouverte` et `synthese` s'enchaînent avec une barre de progression. Le bloc `outil` est prévu au format (étape 3) mais affiché comme « à venir ».
- **À côté, Jules** : il voit la leçon, le bloc en cours, la réponse attendue et les tentatives déjà faites, mais ne les révèle jamais. Il ne parle de lui-même qu'après une tentative de l'élève, toujours par une question, jamais par la réponse ; un garde-fou serveur (`contient_la_reponse`) rejoue l'échange si Jules se trompe. Après plusieurs tentatives fausses, l'explication s'affiche sans qu'il ait à la répéter.
- **Le parcours** (à gauche) : les notions de la matière choisie, groupées par chapitre, avec leur état (compris, en cours, bloqué, à venir) — une estimation de l'IA, affichée comme telle. Les notions qui ont une leçon sont cliquables.
- **Le studio** (étape 4) : construit. L'élève fabrique une fiche, une carte mentale, un quiz ou des cartes mémoire, Jules relit ; les cartes mémoire suivent une répétition espacée (`jules/revisions.py`). La fin d'une leçon écrit déjà un événement de suivi qui alimente le bilan du soir et l'épreuve sans aide, comme un échange en conversation classique.

19 leçons expérimentales existent aujourd'hui (8 matières : mathématiques, français, histoire, géographie, EMC, physique-chimie, SVT, technologie — par exemple le théorème de Pythagore, l'accord du participe passé avec avoir, la guerre totale 1914-1918), dans `bibliotheque/lecons-3e-experimentales/`, format décrit dans [`bibliotheque/README.md`](../bibliotheque/README.md) et `bibliotheque/SCHEMA-LECON.md`. Elles sont marquées `a_relire` : un enseignant doit les valider avant un usage réel.

**Reste à faire sur cet axe** : d'autres leçons (19 notions sur 252 ont aujourd'hui une leçon en blocs, les autres n'ont qu'une fiche de repères pour l'aide aux devoirs), le bloc `outil` une fois l'étape 3 avancée, et le studio de révision (étape 4).

Proposition de format d'une leçon (documentée en détail dans `docs/COURS-CONTRAT.md`, qui reste la référence technique) :

```yaml
notion: guerre-totale-1914-1918      # identifiant dans la bibliothèque
blocs:
  - type: objectifs
  - type: texte
    contenu: "..."
  - type: outil
    outil: frise-chronologique
    action: afficher_periode
    donnees: {debut: 1914, fin: 1918, evenements: [...]}
  - type: exercice
    outil: frise-chronologique
    action: exercice_remettre_dans_l_ordre
  - type: question_ouverte
    question: "Pourquoi dit-on que les civils sont aussi en guerre ?"
    indices: ["...", "...", "..."]
```

La conversation actuelle ne disparaît pas : elle reste disponible pour l'aide aux devoirs avec photo, qui est un usage à part entière.

## 2 bis. Des fiches visuelles, sans appel à l'IA

**Construite (étape 2 bis).** L'écran d'accueil de l'élève (`/`, « Mes fiches ») affiche, pour
chaque notion qui en a une, une fiche visuelle en 8 types de blocs (`attendus`, `formule`,
`carte`, `graphe` interactif, `methode`, `piege`, `exemple`, `renfort`), un rail à gauche pour
naviguer entre les notions, et Jules qui commente en bulles préécrites (jamais générées) quand
l'élève clique sur un bloc. Le format complet est décrit dans
[`bibliotheque/SCHEMA-FICHE-VISUELLE.md`](../bibliotheque/SCHEMA-FICHE-VISUELLE.md) ;
`jules/fiches_visuelles.py` lit et vérifie chaque fiche (source et licence obligatoires, gabarit
de figure connu, conditions `si` analysées sans jamais d'`eval()`).

Contrairement au chat et à la leçon en blocs, cette page ne fait **aucun appel au modèle d'IA** :
tout le contenu est préécrit, relu, et rendu par du code déterministe (cadrage
`jules_cadrage_interface.md`). Le chat existant est déplacé sur `/discuter` (« Discuter avec
Jules ») ; ouvrir la petite fenêtre de chat depuis une fiche y renvoie avec la notion de la fiche
déjà choisie.

Cinq fiches expérimentales de mathématiques 3e existent dans
`bibliotheque/fiches-visuelles-3e-experimentales/` (fonctions linéaires et affines, Thalès et
triangles semblables, théorème de Pythagore, équations, probabilités), marquées `a_relire`.

**Reste à faire sur cet axe** : les autres matières et niveaux, plus de gabarits de figures, et
brancher plus finement la fenêtre de chat flottante à la conversation en cours si l'élève y est
déjà.

## 4. La sécurité des outils

Jules est utilisé par des enfants. Des outils écrits par n'importe qui ne peuvent y entrer qu'avec des garanties fortes. Ce protocole est une proposition à durcir ensemble **avant** d'accepter le premier outil extérieur.

### Isolement technique

- Chaque outil tourne dans un cadre isolé (`iframe` en mode *sandbox*, sans accès à la page de Jules ni à ses données).
- **Aucun accès au réseau** : pas de requête vers Internet, pas de police, d'image ou de script chargé depuis l'extérieur. Tout ce dont l'outil a besoin est dans son dossier.
- L'outil ne voit **que ce que la leçon lui transmet** : jamais le prénom de l'élève, son profil, ses conversations ou ses photos.
- L'outil et Jules ne communiquent que par messages, et seulement avec les actions et événements déclarés dans sa fiche. Tout le reste est ignoré.
- Une permission supplémentaire (par exemple le micro pour un outil de prononciation) doit être déclarée, justifiée, validée par les mainteneurs, puis acceptée par le parent.

### Validation avant publication

Un outil ne rejoint le catalogue qu'après toutes ces étapes, dans l'ordre :

1. **Contrôles automatiques** : fiche conforme, aucune adresse externe dans le code, taille limitée, pas d'exécution de code dynamique, licence compatible, tests de l'outil qui passent.
2. **Relecture du code** par deux mainteneurs, dont un qui n'a pas participé à l'outil.
3. **Relecture pédagogique** : l'outil aide à apprendre et ne donne pas la réponse.
4. **Relecture d'accessibilité** : utilisable au clavier, contrastes suffisants, compatible avec les adaptations (section 5).
5. **Empreinte enregistrée** : le catalogue retient l'empreinte exacte de la version validée. Jules refuse de charger un outil dont le contenu ne correspond pas.

Chaque mise à jour repasse par les mêmes étapes. Un outil qui pose problème peut être retiré du catalogue : Jules le désactive alors chez tout le monde à la prochaine mise à jour.

Par défaut, Jules n'installe que des outils du catalogue validé. Installer un outil non validé demande une action volontaire du parent, avec un avertissement clair.

## 5. Une interface qui s'adapte à l'élève

**Emplacement réservé : ce pan du projet sera conçu plus tard.**

Le profil de l'élève pourra indiquer des besoins particuliers. Ils changeront à la fois **l'affichage** et **la façon dont Jules s'exprime**. Chaque besoin sera une brique à part, une **adaptation**, rangée dans le dossier [`adaptations/`](../adaptations/).

Les troubles dys en sont le cœur : dyslexie, dysorthographie, dyscalculie, dyspraxie, dysgraphie, dysphasie... Chacun a ses particularités et ses besoins, parfois opposés d'un trouble à l'autre, et un même élève peut en cumuler plusieurs. Le champ s'étend aussi aux troubles de l'attention, à la déficience visuelle ou auditive, etc. C'est un chantier à part entière, qui se construira avec des orthophonistes, des ergothérapeutes, des enseignants spécialisés et des familles concernées.

Ce qui est déjà posé, pour que l'architecture laisse la place :

- une adaptation par besoin, et plusieurs adaptations peuvent se combiner chez un même élève ;
- une adaptation agit sur toute l'interface, y compris sur les outils des matières : c'est une condition pour qu'un outil soit validé (section 4) ;
- elle peut aussi modifier les consignes données à Jules (rythme, longueur des phrases, découpage) ;
- les besoins sont indiqués par le parent : Jules ne pose jamais de diagnostic.

## 6. Le parent, et la mesure

**Le bilan qui souffle une question.** Le bilan du soir dit ce qui a été travaillé et ce qui bloque. Il propose aussi au parent une ou deux questions à poser à l'enfant, faites pour être posées sans savoir faire l'exercice soi-même (« Explique-moi comment tu sais qu'un nombre est premier »). C'est le moyen le moins cher de remettre un adulte dans la boucle ; l'essai y consacre son chapitre VIII.

**Ce qui reste sans aide.** Le suivi mesure ce qui se passe pendant qu'on utilise Jules, pas ce que l'élève a appris. Pour s'en approcher, Jules propose, quelques jours après (3 jours par défaut), une courte épreuve sans aide sur les notions marquées comprises : ce qui tient est acquis, ce qui ne tient pas repasse en cours, et le bilan du soir le dit au parent (`jules/modules/epreuve.py`). Ce n'est pas une étude scientifique, mais c'est le bon critère.

## Ce que Jules ne fait pas encore

À dire honnêtement à qui l'installe :

- **Le suivi des notions est une estimation.** L'état (comprise, en cours, bloquée) est déduit par le modèle d'IA à partir des conversations. Les grands modèles sont médiocres à cet exercice ; la recherche sur le suivi des connaissances des élèves n'a pas encore de méthode fiable à proposer. Exception : pour les fiches v2 (`docs/FICHES-V2.md`), les exercices sont corrigés par le code, pas estimés par un modèle.
- **Aucune mesure des progrès.** Jules n'a été essayé que dans une famille. Rien ne montre encore qu'il fait progresser un élève ; un tuteur bien réglé évite surtout que l'IA fasse perdre. Un banc d'essai d'élèves simulés (`evaluation/eleves/`, 9 profils, plus de 35 scénarios, jugés par un modèle) existe pour repérer des pièges de conversation, mais il ne mesure rien chez un vrai élève.
- **Les petits modèles locaux cèdent.** Un modèle de 8 milliards de paramètres a fini par donner la réponse quand l'élève insistait. Pour l'instant, gratuit et fiable ne vont pas ensemble.

## Feuille de route proposée

| Étape | Contenu | État |
|---|---|---|
| 0 | Tuteur par conversation, bilan parent, vigilance, bibliothèque 3e | fait |
| 0 bis | Bilan du soir avec une ou deux questions pour le parent ; effacement complet et export du dossier par le parent | fait |
| 1 | Bibliothèques : fiche d'identité, chargement selon le niveau et l'âge, programme 3e migré | en partie fait : fiche d'identité, chargement selon le niveau, quatre niveaux migrés (CM1, 5e, 4e, 3e) ; reste le chargement selon l'âge et les autres niveaux |
| 2 | Interface de cours : leçons en blocs, Jules à côté du cours | fait (module `cours`, page `/cours`, 19 leçons expérimentales `a_relire`, 8 matières) ; reste le bloc `outil` |
| 2 bis | Fiches visuelles : écran d'accueil « Mes fiches », 8 types de blocs, rendu sans appel IA | fait (module `fiches_visuelles`, page `/`, cinq fiches expérimentales `a_relire` en mathématiques 3e) ; reste les autres matières et niveaux |
| 3 | Outils : contrat, isolement, protocole de validation, trois outils de référence (frise, calculatrice, lexique) | en partie fait : contrat (`docs/OUTILS-CONTRAT.md`), isolement (iframe sandbox), trois outils de référence livrés comme extensions ; reste l'ouverture du bloc `outil` depuis une leçon et le protocole de validation communautaire |
| 4 | Studio : l'élève fabrique carte mentale, fiche, quiz, cartes mémoire avec répétition espacée ; Jules relit | fait (`jules/modules/studio.py`, `jules/studio.py`, `jules/revisions.py`, page `/studio`, `docs/STUDIO-CONTRAT.md`) |
| 4 bis | Épreuve sans aide quelques jours après, sur les notions marquées comprises | fait (conversation et interface de cours : les deux alimentent le même suivi) |
| 4 ter | Exercices sans IA, corrigés par le code (fiches v2) | en cours : contrat (`docs/FICHES-V2.md`), module `exercices`, deux fiches de démonstration ; reste la conversion des 252 fiches v1 |
| 5 | Catalogue communautaire de bibliothèques et d'outils | en cours : contrat d'extension (`docs/EXTENSIONS.md`, `jules/extensions.py`), 10 extensions d'exemple ; reste le catalogue et l'installation par empreinte |
| à part | Adaptations (troubles dys, attention...) : chantier à part entière, à ouvrir avec des professionnels. D'ici là, chaque étape leur laisse la place. | emplacement réservé |

## Questions ouvertes

- **Qui écrit les leçons ?** Des contributeurs, Jules à partir d'une notion, ou les deux (Jules propose, un humain valide) ?
- **Quand Jules parle-t-il sans qu'on l'appelle ?** Combien de temps attendre, et que considérer comme une tentative (une réponse fausse, un silence, un effacement) ?
- **Modèles installés sur l'ordinateur.** Les petits modèles savent mal piloter des outils. Faut-il des leçons plus guidées quand Jules tourne sans connexion ?
- **Hébergement du catalogue** : dans ce dépôt, ou dans un dépôt séparé avec ses propres mainteneurs ?
- **Gouvernance** : qui peut valider une bibliothèque, un outil, une adaptation ?

Vos avis sont les bienvenus dans les tickets et les discussions du dépôt.
