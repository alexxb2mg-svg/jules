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

Aujourd'hui Jules est un tuteur par conversation, avec une seule bibliothèque (le programme de 3e). La suite le fait évoluer sur quatre axes.

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

Le programme de 3e existant deviendra la première bibliothèque à ce format. Les notions gardent leur identifiant et leur source officielle, pour que Jules puisse toujours dire d'où vient ce qu'il enseigne.

**À construire avec la communauté :** les programmes du primaire (cycles 2 et 3), des autres classes de collège, et du lycée.

## 2. Des outils par matière

Un outil est une petite application qui s'ouvre dans la leçon : frise chronologique en histoire, calculatrice ou géométrie dynamique en maths, carte muette en géographie, conjugueur en français, tableau périodique en physique-chimie. Chaque matière peut avoir les siens, écrits par la communauté.

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

L'élève ne parle plus à une fenêtre de conversation : il suit une **leçon**, faite de blocs qui s'enchaînent. Voir la [maquette](maquette-cours.png).

- **Au centre, le cours** : objectifs, explication, outil, exercice, question ouverte. Une barre de progression montre où en est l'élève.
- **À côté, Jules** : il voit ce que fait l'élève dans le cours. Il le laisse d'abord essayer, puis pose des questions, donne des indices progressifs et renvoie vers le bon endroit du cours au lieu de répondre. Il ne parle de lui-même qu'après une tentative, et seulement par une question.
- **Le parcours** : les notions de la matière, avec leur état (comprise, en cours, à venir). Cet état est une estimation de l'IA, affichée comme telle.
- **Le studio** : à partir de la leçon, l'élève fabrique ses supports de révision (carte mentale, fiche, quiz, cartes mémoire avec répétition espacée). À la différence de NotebookLM, Jules ne les génère pas : il propose une trame vide, pose des questions, puis relit et corrige ce que l'élève a écrit.

Proposition de format d'une leçon (un fichier par leçon, écrit par un contributeur ou préparé par Jules à partir d'une notion) :

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

**Ce qui reste sans aide.** Le suivi mesure ce qui se passe pendant qu'on utilise Jules, pas ce que l'élève a appris. Pour s'en approcher, Jules proposera, quelques jours après, une courte épreuve sans aide sur les notions marquées comprises : ce qui tient est acquis, ce qui ne tient pas repasse en cours. Ce n'est pas une étude scientifique, mais c'est le bon critère.

## Ce que Jules ne fait pas encore

À dire honnêtement à qui l'installe :

- **Le suivi des notions est une estimation.** L'état (comprise, en cours, bloquée) est déduit par le modèle d'IA à partir des conversations. Les grands modèles sont médiocres à cet exercice ; la recherche sur le suivi des connaissances des élèves n'a pas encore de méthode fiable à proposer.
- **Aucune mesure des progrès.** Jules n'a été essayé que dans une famille. Rien ne montre encore qu'il fait progresser un élève ; un tuteur bien réglé évite surtout que l'IA fasse perdre.
- **Les petits modèles locaux cèdent.** Un modèle de 8 milliards de paramètres a fini par donner la réponse quand l'élève insistait. Pour l'instant, gratuit et fiable ne vont pas ensemble.

## Feuille de route proposée

| Étape | Contenu | État |
|---|---|---|
| 0 | Tuteur par conversation, bilan parent, vigilance, bibliothèque 3e | fait |
| 0 bis | Bilan du soir avec une ou deux questions pour le parent ; effacement complet et export du dossier par le parent | fait |
| 1 | Bibliothèques : fiche d'identité, chargement selon le niveau et l'âge, programme 3e migré | à faire |
| 2 | Interface de cours : leçons en blocs, Jules à côté du cours | à faire |
| 3 | Outils : contrat, isolement, protocole de validation, trois outils de référence (frise, calculatrice, lexique) | à faire |
| 4 | Studio : l'élève fabrique carte mentale, fiche, quiz, cartes mémoire avec répétition espacée ; Jules relit | à faire |
| 4 bis | Épreuve sans aide quelques jours après, sur les notions marquées comprises | à faire |
| 5 | Catalogue communautaire de bibliothèques et d'outils | à faire |
| à part | Adaptations (troubles dys, attention...) : chantier à part entière, à ouvrir avec des professionnels. D'ici là, chaque étape leur laisse la place. | emplacement réservé |

## Questions ouvertes

- **Qui écrit les leçons ?** Des contributeurs, Jules à partir d'une notion, ou les deux (Jules propose, un humain valide) ?
- **Quand Jules parle-t-il sans qu'on l'appelle ?** Combien de temps attendre, et que considérer comme une tentative (une réponse fausse, un silence, un effacement) ?
- **Modèles installés sur l'ordinateur.** Les petits modèles savent mal piloter des outils. Faut-il des leçons plus guidées quand Jules tourne sans connexion ?
- **Hébergement du catalogue** : dans ce dépôt, ou dans un dépôt séparé avec ses propres mainteneurs ?
- **Gouvernance** : qui peut valider une bibliothèque, un outil, une adaptation ?

Vos avis sont les bienvenus dans les tickets et les discussions du dépôt.
