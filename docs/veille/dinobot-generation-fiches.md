# DinoBot : génération de fiches (étude du 28/09/2026)

Visite sur le compte de l'élève (formule d'essai Étudiant+), dans la matière physique-chimie. Deux fiches générées :
- une depuis leur base (chapitre « Les ions », 3 parties) ;
- une depuis un fichier (PDF de notre fiche « Guerre totale 1914-1918 »).

Captures : `…/cache/scratch/dino/`. Même parcours pour « Cours illustré », « Exercice » et « Évaluation ».

## Le parcours

1. **Sélecteur de matière** en haut, global (bouton vert « Sciences physique-chimie »).
2. **Choix de la source** : deux cartes.
   - **Base de données** : leur programme officiel. On choisit **un chapitre** (liste numérotée, 10 en physique-chimie, plus « Autre »), puis **une ou plusieurs parties** (cases à cocher, « Sélectionner tout », recherche).
   - **À partir d'un fichier** : **PDF uniquement, 10 Mo au maximum** (« votre sujet et optionnellement la correction »). La photo passe par le chat (« Ajouter un fichier Image ou PDF »), pas par les fiches.
3. Dans les deux cas, un **prompt de personnalisation facultatif** (1 000 caractères) et un bouton « Générer la fiche ».
4. **« Génération en cours… »** pendant environ 30 s, puis écran partagé : **document à gauche, chat de DinoBot à droite**. Des boutons en haut à droite affichent la fiche seule, les deux ou le chat seul.
5. Trois **onglets générés depuis la même source** :
   - **Fiche** : cours rédigé en markdown. Titres numérotés (Définition, parties, Méthode, Exemples, Points importants, Pièges courants), listes, gras, formules KaTeX.
   - **Infos clés** : une dizaine d'affirmations d'une phrase, chacune avec son idée en gras.
   - **Flashcards** : 8 cartes question/réponse, à retourner au clic, avec « Précédent/Suivant ».
6. Actions sur le document : **Régénérer, Copier, Télécharger en PDF, Imprimer**.

## Ce qu'on constate

- **Rien n'est conservé.** « Historique > Documents » affiche « 0 document stocké » après deux générations. La fiche est jetable : il faut la télécharger ou l'imprimer. Il n'y a **pas de bibliothèque personnelle**.
- **Aucun rattachement à une notion.**
  - Depuis la base, la fiche est rattachée par construction au chapitre et aux parties choisis, mais n'est rangée nulle part ensuite.
  - Depuis un fichier, **aucune détection de matière ni de notion** : notre PDF d'histoire, envoyé alors que la matière choisie était la physique-chimie, a donné une fiche d'histoire sans aucun signalement.
- **Un format générique, sans schéma.** Du texte rédigé, sans visuel : pas de frise, de schéma, de tableau à compléter ni d'encadré typé. Le visuel de la source est perdu : notre fiche visuelle devient du texte.
- **Des ajouts sans le dire.** La fiche tirée du PDF développe au-delà de la source (causes détaillées, phases année par année) sans distinguer ce qui vient du document de ce que le modèle ajoute.
- **Le chat reste à côté du document**, avec toujours le même accueil (« Bonjour <prénom>, que souhaites-tu savoir ? »).
- Les **flashcards ne sont pas branchées sur une révision espacée** : il n'y a pas de bouton « je savais / je ne savais pas ».

## Face à Jules et à ce que veut Alex

| | DinoBot | Jules aujourd'hui | Besoin d'Alex |
|---|---|---|---|
| Deux sources | base / fichier | natif seulement | natif / personnel |
| Entrée | PDF (fiches), image (chat) | aucune | photo de cours, chapitre, exercice |
| Format produit | markdown libre | schéma de fiche visuelle (blocs typés) | **notre schéma**, rien d'autre |
| Rattachement | chapitre choisi à la main, rien pour un fichier | notion du référentiel | **le LLM choisit la notion** |
| Conservation | aucune | bibliothèque native | **bibliothèque personnelle** |
| Distinction | sans objet | sans objet | **autre couleur dans la barre latérale et filtre natif/personnel** |
| Dérivés | infos clés et flashcards générées | exercices v2, cartes du studio (à paliers) | à décider |

## À reprendre (inspiration, pas copie)

1. **Le choix de la source en deux cartes**, puis le formulaire (bon pour une élève de 14 ans).
2. **Le choix « chapitre puis parties »** avec cases à cocher et « tout sélectionner », qui recouvre nos notions et sous-notions.
3. **Plusieurs vues pour une même source** (fiche, essentiel, cartes). Chez nous, ces vues existent déjà comme blocs du schéma (encadré « à retenir », cartes du studio) : il faut les *présenter*, pas en inventer.
4. **L'écran partagé document | tuteur**, qu'on a déjà.
5. **Le prompt de personnalisation facultatif**, à encadrer (voir les garde-fous).

## À ne pas reprendre

- Le markdown libre : il casse notre modularité et notre rendu visuel.
- La fiche jetable : chez nous, tout va en bibliothèque, rattaché à une notion.
- L'absence de contrôle de la matière et de la notion.
- Mélanger la source et les ajouts du modèle sans le signaler.
