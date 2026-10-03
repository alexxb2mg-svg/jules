# Veille : tuteurs IA et applis de soutien scolaire (marché français, collège / 3e)

*Veille faite le 28/09/2026, uniquement sur sources publiques : pages produit, pages d'aide, fiches App Store / Google Play (description et captures récupérées via l'API publique iTunes `itunes.apple.com/lookup`), articles de presse. Aucun compte créé, aucune connexion. DinoBot est exclu (déjà étudié dans `DinoBot_exploration_2026-09-26.docx`).*

**Convention.** Chaque affirmation renvoie à une source `[n]` (liste en fin de document).
- **(vu)** : lu sur la page ou visible sur une capture publique.
- **(déduit)** : mon interprétation à partir de ce qui est vu, non confirmée par l'éditeur.

Les prénoms des captures marketing sont remplacés par `<prénom>`. Dans ce document, « l'élève » désigne l'utilisatrice de Jules.

---

## 1. Tableau récapitulatif

| Produit | URL | Public | Prix (vu) | Forme du tuteur IA | Fiches / flashcards | Révision espacée | Gamification | Suivi parent | Dys / accessibilité | Import photo / PDF |
|---|---|---|---|---|---|---|---|---|---|---|
| **Kartable + Alfa** | kartable.fr | CE1 → Tle | 7,99 à 14,99 €/mois, Alfa inclus avec plafond mensuel [1][2] | Chat « prof particulier IA » ; photo d'exercice → guidage pas à pas sans donner la réponse [2] | Fiches de révision PDF, quiz [1] | Non annoncée | XP, gemmes, barres de progression par matière (captures) [3] | Tableau de suivi parental, courbe de progression, lacunes [1] | Rien d'annoncé | Photo du cours → interro sur mesure ; photo d'exercice → guidage [2] |
| **SchoolMouv** | schoolmouv.fr | CP → Tle | Abonnement, prix sur `offres.schoolmouv.fr` (non chiffré sur la page) [4] | « Coach IA par tchat » + tchat avec de vrais profs [4][5] | Fiches, flashcards « Je l'apprends / Je le savais », studygrams [5][6] | « Quiz quotidien IA » [6] | Défis, série (flamme) (capture) [6] | Page parents, pas de tableau de bord décrit [5] | Rien d'annoncé | Scan du cours ou titre → fiche, quiz, flashcards, exercice générés [6] |
| **Nomad Education (Nomad'IA, coach Nono)** | nomadeducation.fr | Primaire → Sup | Gratuit + Nomad+ [9][10] | Coach Nono (mascotte) ; chat « Ton coach » qui crée un chapitre depuis une photo [9][12] | Mini-cours, fiches « Essentiels », flashcards, « paires parfaites » [12] | « Programme de révision personnalisé » [9] | Note /20 animée, « Bravo, tu es une star ! », partage [12] | Compte Parent : moyenne, temps passé, progression, notifications [11] | Rien d'annoncé | Photo de notes → chapitre IA [9][12] |
| **Knowunity (Knowie)** | knowunity.fr | Collège / lycée, 30 M d'élèves annoncés | Gratuit + Premium [13] | Chat avec la mascotte Knowie, vocal, photo d'exercice ; un chat par matière [14] | Cartes mémo générées, quiz, résumés, 1 M de fiches d'élèves [14][15] | Plan jour par jour vers la date d'examen, cartes ratées qui reviennent [14][15] | Série, XP, ligues hebdo Bronze → Or [14] | Rien de trouvé | Rien d'annoncé | PDF, diapos, photos, manuscrit, texte, YouTube → fiches/quiz [14] |
| **digiSchool** | digischool.fr | Collège → BTS | 4,99 €/sem. à 14,49 €/mois ; SOLO Éducation 1 an 29,99 € [17] | « Coach IA » d'aide aux devoirs 7 j/7 [17] | « Fiches de révision IA en 3 secondes » [17] | « Rappels de révisions » à heure fixe (capture) [18] | Challenges, trophées, Superquiz, « mort subite » [18] | Rien de trouvé | Rien d'annoncé | Génération de fiche IA [17] |
| **myMaxicours** | maxicours.com | CP → Tle | Plateforme dès 6,95 €/mois ; profs en ligne dès 11,95 € [20] | Humain : profs de l'Éducation nationale, 17 h-20 h, 6 j/7 [20] | Vidéos, podcasts, quiz [20] | « Programmes de révision » [20] | Rien de précis | Tableau de bord des progrès de l'enfant [20] | Rien d'annoncé | Non |
| **EvidenceB : Adaptiv'Collège / MIA** | evidenceb.fr | Collège (Adaptiv'Collège), lycée (MIA) | Établissements ; MIA gratuit pour le public et le privé sous contrat [21][23] | Pas de chat : moteur adaptatif (ZPDES, ~75 % de réussite visée) [23] | Non | Adaptatif, pas espacé | Sobre (mascotte) | Tableau de bord enseignant [22] | « Interface pensée pour favoriser la concentration » [21] | Non |
| **Le Livre Scolaire / Doc'Adapt** | lelivrescolaire.fr | Collège / lycée | Manuels ; Doc'Adapt gratuit [36] | Non | Manuel numérique | Non | Non | Suivi de progression côté prof [36] | Mode dyslexie en 1 clic (OpenDyslexic) [35] ; Doc'Adapt : PDF/photo → support lisible DYS « en 3 clics » [36] | Oui (Doc'Adapt) [36] |
| **Quizlet** | quizlet.com | Tous | Gratuit + Plus [25][26] | Q-Chat [25] | Flashcards, « Notes magiques », mode Apprendre, Test [25] | Learn = intra-session ; Memory Score / Scheduled Review payants [26] | Compteurs « appris / à revoir » [25] | Non | Non | Notes → flashcards/tests [25] |
| **NotebookLM (Gemini Notebook)** | app iOS | Tous (référence d'inspiration) | Gratuit [27] | Chat ancré dans les sources, citations en ligne [27] | Notes, « Studio » | Non | Non | Non | Audio (podcast à 2 voix) [27] | PDF, site, YouTube, texte, audio [27] |
| **Khanmigo / Khan Academy** | khanmigo.ai | Surtout US (Khan Academy existe en FR) | 4 $/mois [28] | Chat « qui ne donne jamais la réponse », désormais intégré à l'exercice [28][29] | Non | Points de maîtrise [31] | Points d'énergie → chapeaux pour l'avatar [28] | Oui (enseignant, district) [29] | Rien de précis | Non |
| **Photomath / Gauth / Brainly** | — | Collège / lycée, grand public | Freemium [32][33][34] | Scan → solution étape par étape ; tuteurs humains (Gauth, Brainly) [32][34] | Non | Non | Non | Non | Non | Photo d'exercice, cœur du produit [33] |

Écartés ou non confirmés :
- Mon Tuteur IA / MaîtreRenard, Educ'Ark, StudyTracker, « Mon Cahier IA » : aucune trace d'un produit scolaire français actif trouvée.
- Superprof : sa seule « IA » trouvée est une expérience de blog (« Dr Supernabot »), pas un produit.
- Toutapprendre : plateforme pour CSE et bibliothèques, pas un tuteur.
- Acadomia : prise de parole sur l'IA, pas de produit élève visible.
- Lalilo (primaire, mascotte Lilo qui montre la consigne à l'écran) : noté seulement [38].

---

## 2. Fiches produit

### 2.1 Kartable + Alfa (Kartable, Magnard)

- **Existence et activité.** Page d'accueil « Programmes officiels 2026-2027 » ; Alfa marqué « Nouveauté » [1] (vu). App iOS 8.0.11 publiée le 03/06/2026, note 4,5 [3] (vu).
- **Prix.** 14,99 €/mois, 9,99 €/mois sur l'année scolaire, 7,99 €/mois sur 2 ans. Alfa est inclus « soumis à une limite d'usage mensuelle variable selon le type de demandes » [1] (vu).
- **Tuteur Alfa.** Trois usages annoncés [2] (vu) :
  1. un chat (« reformule les notions complexes », « exemples concrets ») ;
  2. des « interros de cours sur-mesure » : l'élève prend son cours en photo, Alfa génère des questions et « cible les notions à retravailler » ;
  3. des « entraînements sur les exercices de votre prof » : photo de l'exercice, guidage pas à pas, « sans jamais donner la réponse directement ».

  Promesse de fiabilité : « Contexte maîtrisé et sécurisé. Pas d'hallucinations, pas de hors programmes », « cadre de conversation strictement scolaire » [2] (vu). Le tuteur est donc ancré sur les contenus rédigés par les 200 enseignants (déduit).
- **Écrans (captures App Store) [3] (vu).**
  1. Cours : texte aéré, mots-clés en gras, encadré gris « EXEMPLE », carte.
  2. Exercice QCM : barre de progression en haut, petit avatar au bout de la barre, compteur de cœurs, bouton « Télécharger hors-ligne ».
  3. Écran de réussite : confettis, trophée, « BRAVO ! », « +10 XP ».
  4. Accueil : niveau (« Seconde ») en liste déroulante, gemmes (67), barre de progression globale (23 %), puis une ligne par matière avec icône, barre verte et pourcentage.
- **Navigation.** Niveau → matière → chapitre → cours / exercices (vu sur l'accueil [3] ; profondeur déduite).
- **Parents.** « Suivi de progression en temps réel », « courbe de progression de chaque enfant », « identification des lacunes ». FAQ : « jusqu'au collège… faire le point 15 minutes par semaine avec lui pour valider son travail et son planning » [1] (vu).
- **Dys.** Rien d'annoncé. Point notable : « toutes les fiches téléchargeables au format PDF… pour travailler sans écran » [1] (vu).
- **Captures :**
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/60/ca/1e/60ca1ee3-2830-43b0-aec4-e8f58246e4d2/665aea00-bfda-4566-a62f-02844695efa8_2.png/392x696bb.png (exercice)
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/32/7b/f2/327bf234-1745-32b3-32c8-fa3b97d7e407/6fe7efee-750d-4cc2-8bde-b1a536666cc8_4.png/392x696bb.png (accueil par matière)

### 2.2 SchoolMouv

- **Existence et activité.** App iOS 2.30.0 publiée le 10/09/2026, note 4,6 [6] (vu). Le site annonce 3 millions d'élèves et 16 000 contenus « validés par des professeurs » [4] (vu).
- **Ressources.** Ancres de la page parents : Cours, Vidéos, Synthèses, Flashcards, Studygrams, Quiz, Exercices, Défis, Méthode, Plannings de révision, Annales, Assistant IA, Tchat Prof [5] (vu). Un « assistant IA… guide l'élève dans ses devoirs, génère des contenus personnalisés » ; le tchat avec de vrais profs sert à « débloquer une notion incomprise » [5] (vu).
- **Fiches.** Elles mettent « en avant les éléments essentiels à maîtriser pour favoriser la mémoire visuelle (définitions, notions à retenir, points d'attention, illustrations) ». Elles sont imprimables, « pour annoter, surligner » [7] (vu).
- **Écrans (6 captures App Store FR) [6] (vu).**
  1. Accueil « Bonjour `<prénom>` » : sélecteur « Classe de 5e », compteur flamme (série), liste verticale des matières avec une grande illustration colorée par matière, barre d'onglets en bas.
  2. Fiche de cours : titre, sous-titre « À l'échelle mondiale : … », mots-clés en gras colorés, carte.
  3. Vidéo de cours.
  4. Quiz « Question 1/10 » : 4 grandes cartes-réponses empilées.
  5. Flashcards : barre « 2/10 », carte recto/verso animée, « Clique pour revoir la question », deux gros boutons « Je l'apprends » (orange, gauche) et « Je le savais » (vert, droite).
  6. Générateur IA : l'élève scanne son cahier ou tape un titre ; la page du chapitre porte l'étiquette « Généré par scan » et 4 tuiles (Révision, Quiz, Flashcards, Exercice) ; une tuile encore vide montre un bouton « Générer ».
- **Généré ou vérifié.** Le catalogue est « validé par des profs » [4] ; ce que l'élève génère porte l'étiquette « Généré par scan » [6] (vu). Les deux circuits sont séparés (déduit).
- **Captures :**
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource211/v4/52/82/4e/52824e15-5659-f600-c9cc-93c6c3000a67/Android_-_1290_x_2796_pixels.png/320x480bb.jpg (accueil)
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/25/71/10/25711089-5391-256f-ad50-c25b2dd61c73/1290_x_2796_pixels-1.png/320x480bb.jpg
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/ea/29/96/ea2996b6-e6cd-84d8-5a71-8001f0440cb0/1290_x_2796_pixels-5.png/320x480bb.jpg (générateur)

### 2.3 Nomad Education (Nomad'IA, coach Nono)

- **Existence et activité.** Version 10.1.0 publiée le 25/09/2026. Note de version : « Nouvelle DA + Ton coach Nono débarque » ; « Nomad'IA génère ton programme de révision personnalisé depuis tes notes prises en cours » [12][9] (vu). 5 M+ téléchargements, 4,6 sur Google Play [10] (vu). « Brevet 2027 », 3e incluse [9] (vu).
- **Contenu.** « 100 % réalisé par 300 professeurs de l'Éducation Nationale » : 20 000 mini-cours et fiches, 120 000 QCM corrigés [9] (vu).
- **Écrans (captures) [12] (vu).**
  1. **Page de chapitre Nomad'IA** (« La seconde Guerre mondiale »). En tête, une légende : « IA = contenu enrichi par l'IA » / « Profs = contenu créé par des profs ». Chaque ressource (Mini-cours, Quiz, Fiches « Essentiels », Paires parfaites) porte ses badges `IA` et/ou `Profs`.
  2. **Résultat** : jauge circulaire « 18/20 », « Bravo, tu es une star ! ». Boutons Recommencer / Correction / Partager, bouton « Montre à tes parents que tu gères », puis une carte « Prochain exercice suggéré : Flashcards » et « Exercice suivant ».
  3. **Grille des matières** avec une tuile « Mes chapitres IA » en premier.
  4. **Chat « Ton coach »** en bulles. Le coach : « Super, tu veux créer ton chapitre comment ? » ; bouton « Prendre une photo » ; photo du cours dans le fil ; le coach : « laisse-moi analyser ton contenu… ».
- **Parents.** Compte Parent créé depuis l'app, jusqu'à 5 enfants via un « code famille », notifications parentales activables, statistiques « moyenne, temps passé, progression » [11] (vu).
- **Captures :**
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource211/v4/e1/d0/72/e1d072f2-41f7-c46c-2c87-4bed43278749/5.png/320x480bb.jpg (badges IA/Profs)
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource211/v4/48/48/97/48489754-683e-efad-0fc1-8150078df2c3/9.png/320x480bb.jpg (résultat)
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/06/2b/ef/062bef2e-2c0f-ac07-191e-268324fdc7f0/2.png/320x480bb.jpg (chat coach)

### 2.4 Knowunity (mascotte Knowie)

- **Existence et activité.** Version 6.39.2 publiée le 25/09/2026, note 4,7 [16] (vu). 30 M d'élèves, 1,6 M de fiches, 32 pays [13] (vu).
- **Organisation.** Selon la fiche App Store, « tout passe par un seul endroit : ton plan de révision », construit « autour de ta date d'examen et de tes chapitres ». On peut y ajouter son emploi du temps, et « tu vois toujours ce qui est acquis et ce qui vient ensuite » [14] (vu).
- **Tuteur.**
  - Chat avec Knowie, mode vocal ; photo d'un exercice → « explique étape par étape le raisonnement, pas seulement la réponse » [14] (vu).
  - « Garde un chat séparé par matière pour ne rien mélanger » [14] (vu).
  - « Révision vocale : tu dis ta réponse de mémoire et je la vérifie avec toi » [14] (vu).
- **Écrans (captures) [16] (vu).**
  1. Accueil : mascotte, bulle « L'examen est demain ? On gère ça », gros bouton « Continuer le plan d'étude ».
  2. Chat, fond sombre : compteur d'énergie ⚡ en haut ; réponse structurée (titre, schéma, liste numérotée, termes clés soulignés) ; champ « Demande à Knowie… » avec boutons +, appareil photo et micro ; 5 onglets en bas (chat, calendrier, objectifs, recherche, trophée).
  3. Plan d'une matière : « In 3 days », « Grade Goal: 20 », carte « Predicted score: 10 – Tap to see where you can improve ». Chapitre présenté en **chemin vertical d'étapes** : Lesson recap → Explain out loud → Quiz → Mock exam.
  4. Quiz : 4 réponses, bandeau « Super ! », boutons « Pourquoi ? » et « Continuer ».
- **Flashcards.** Fin de série : « Tu as mémorisé 18 cartes sur 20 », XP, score, « EN FEU », bouton « Revoir les cartes ratées ». Écran « Où tu en es » : « Tu maîtrises ces mots » / « À retravailler ». Knowie « refait remonter plus tard » les points faibles [15] (vu).
- **Gamification.** Série, XP, « ligue hebdomadaire jusqu'à 30 camarades… de Bronze à Or » [14] (vu).
- **Import.** « PDF, diapos, photos ou notes manuscrites, texte et liens… vidéo YouTube » → fiches, quiz, résumés « prêts à entrer dans ton plan » [14] (vu).
- **Captures :**
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/c2/9b/6d/c29b6d87-a410-f8d6-dd26-7d7389fafc8e/2.jpg/320x480bb.jpg (chat)
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/b1/7b/a3/b17ba3d0-47ac-c9c3-3ea6-0fcbc3cc0ace/3.jpg/320x480bb.jpg (plan en chemin)
  - https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/f2/91/8d/f2918dd4-5403-98d8-61a5-b9bdc5ac9cfe/6.jpg/320x480bb.jpg (quiz « Pourquoi ? »)

### 2.5 digiSchool

- **Existence et activité.** Version 5.9 publiée le 22/07/2026, note 4,5 [18] (vu). « Génère tes fiches de révisions IA en seulement 3 secondes », « Coach IA… 7 jours sur 7 », mode hors ligne, statistiques [17] (vu).
- **Écrans (captures) [18] (vu).**
  1. **Accueil « Mon coach »** (« Hello `<prénom>` ») : bloc « Mes challenges » (Superquiz, dernier score 12/20), « Mes trophées » (badges), « Mes rappels de révisions » (cartes horodatées 18:30 + « Ajouter un rappel »).
  2. **Quiz** : feedback vert « Bonne réponse ! » avec l'explication juste en dessous.
  3. **Fiche IA** « Ma fiche : Histoire – Napoléon Bonaparte : Résumé historique » : sections à étiquettes surlignées (Contexte, Organisation politique, Réformes), puces courtes.
  4. **Statistiques** : « temps passé à réviser ce mois-ci » en anneau (cours, quiz, mort subite, superquiz, flashcards), taux de réussite général et par matière, complétion (« cours lus 2/54 », « quiz 12/53 »), carte « Tu peux le faire ! Refais les questions que tu n'as pas réussies ».
- **Capture :** https://is1-ssl.mzstatic.com/image/thumb/PurpleSource211/v4/0a/dc/f4/0adcf470-eaee-0afa-5fbb-e0d915a891b9/Screenshots_AppStore_-_E_U0301ducation_-_6.5_inch_-_5.jpg/320x480bb.jpg (probablement l'écran statistiques ; ordre des fichiers non garanti)

### 2.6 myMaxicours (Bordas)

- **Offre.** Plateforme dès 6,95 €/mois, « Profs en ligne » dès 11,95 €/mois (enseignants de l'Éducation nationale, 6 j/7, 17 h-20 h), pack Premium dès 15,90 € [20] (vu). Contenus de l'éditeur Bordas [20] (vu).
- **Écrans.** Liste marketing : vidéos, programmes de révision, « un tableau de bord pour suivre les progrès de son enfant », podcasts, quiz et exercices [20] (vu). Pas d'IA élève visible sur la page d'accueil.
- **Intérêt pour Jules.** Le **podcast** comme format de révision (utile en dys, déduit).
- **Lien dys.** Bordas édite aussi SONDO, des manuels numériques et audio pour élèves dys [37] (vu).

### 2.7 EvidenceB : Adaptiv'Collège et MIA Seconde / MIA Lycée

- **Adaptiv'Collège.**
  - 8 modules. Maths : organisation et gestion de données, proportion et fractions, espace et géométrie, calcul littéral. Français : orthographe, grammaire, verbe, lexique [21] (vu).
  - « Interface pensée pour favoriser la concentration » ; le produit se dit « pas un manuel » mais un outil d'« évaluation formative » [21] (vu).
- **Écran élève (capture publique) [21] (vu).**
  - Barre du haut : Accueil / Mon travail / Ressources / Mes bilans / Guide.
  - Fond beige clair, beaucoup de blanc, mascotte discrète, « Bienvenue `<prénom>` ».
  - « Mes bilans » : bascule Français / Mathématiques ; colonne gauche « Points forts » (haut niveau de maîtrise) et « Points faibles » (faible niveau de maîtrise), chacun formulé en compétence (« Effectuer des transformations sur des figures ») ; à droite, une carte par module avec barre segmentée, pastilles « Terminé : 1 / En cours : 4 / À explorer : 1 » et lien « Voir le plan ».
  - Capture : https://evidenceb.fr/wp-content/uploads/2025/06/UI-shots_AdaptivCollege_student-dashboard_homepage_mes-bilans-scaled.png
- **MIA.**
  - Devient « MIA Lycée » en 2026-2027 : 24 modules, 20 000 exercices, interface élève et interface enseignant, mode hors ligne [22] (vu).
  - Test de positionnement, puis l'algorithme ZPDES (Inria) vise « une zone de réussite d'environ 75 % » [23] (vu).
  - Critiques relevées par la presse spécialisée : design « années 80 », contenu jugé « infantilisant » pour un élève de niveau standard [23] (vu). Leçon pour une élève de 3e (déduit) : ne pas avoir l'air d'un logiciel de remédiation pour petits.

### 2.8 Le Livre Scolaire (mode dyslexie, Doc'Adapt)

- **Mode dyslexie.** Accessible « d'un clic dès la page d'accueil » : police OpenDyslexic sur les 20 manuels, 10 000 documents et 15 000 exercices ; se désactive d'un clic [35] (vu).
- **Doc'Adapt.** « Transformez n'importe quel document (un texte en pdf, une photo de manuel, une page d'exercices) en un support lisible par des élèves DYS en 3 clics », outil gratuit [36] (vu).
- **Autres outils des manuels numériques.** Lecteurs audio, cartes interactives, manipulation de figures [36] (vu).
- **Intérêt pour Jules.** C'est le seul acteur trouvé qui traite l'**import de document** sous l'angle dys (mise en forme), et non sous l'angle génération de quiz (déduit).

### 2.9 Quizlet (référence flashcards)

- **Existence et activité.** Version 10.53 publiée le 22/09/2026, note 4,7 [25] (vu).
- **Écrans (captures) [25] (vu).**
  1. Flashcard : bandeau vert « Appris ! », progression « 16/20 », deux compteurs latéraux (8 à revoir en orange, 12 appris en vert), schéma sur la carte.
  2. « Notes magiques » : résumé créé à partir des notes, bouton « Raccourcir », 4 icônes de génération.
  3. Mode « Apprendre » : question illustrée, « Essayons à nouveau », puis « Bon travail ! ».
  4. Liste de cartes avec les actions Cartes / Apprendre.
  5. Accueil avec carte « Découvrez Q-Chat ».
- **Répétition espacée.** Le mode Apprendre ordonne les cartes **dans la session**. L'ancien planificateur « Long-Term Learning » a été retiré parce que « 95 % » des utilisateurs étudient une liste sur 4 jours au plus. L'espacement entre sessions (Memory Score, Scheduled Review) est payant [26] (vu ; blog d'un concurrent, à lire avec prudence).
- **Leçon (déduit).** Le palier fixe de Jules (1-3-7-15-30-60) est déjà plus « vrai » que Quizlet gratuit. Ce qu'il faut soigner, c'est la **liste du jour** entre deux sessions.

### 2.10 NotebookLM / Gemini Notebook (inspiration)

- **Écrans (captures App Store) [27] (vu).**
  1. Liste de carnets (titre, nombre de sources, date).
  2. « Upload sources » : PDF, Audio, Website, YouTube, Copied text.
  3. Lecteur « Audio Overview » : onde sonore, bouton « Join » pour intervenir dans la discussion.
  4. Chat avec « in-line citations » : chaque phrase renvoie à la source.
  5. Onglets en bas : Sources / Chat / Studio.
- **Leçon (déduit).** Le triptyque **Sources | Chat | Productions** et la citation cliquable vers le passage du cours correspondent exactement au besoin « le contenu affiché est joint au contexte du chat ».

### 2.11 Khanmigo / Khan Academy (référence tuteur)

- **Promesse et personnalisation.** « Never giving you the answer » ; l'élève gagne des points d'énergie qui lui permettent d'acheter des **chapeaux pour l'avatar Khanmigo** [28] (vu).
- **Maquette (visuel promo) [28] (vu).** Panneau gauche « Activities » (Writing with the AI, Tutor me, Coach…, Talking to historical characters, Debate), fil de bulles à droite, **puces de suggestions** cliquables sous le premier message, champ de saisie avec micro.
- **Usage réel.**
  - Seuls ~15 % des élèves qui y ont accès l'utilisent [29] (vu).
  - Dans une étude sur des collégiens, l'usage est « thin » ; beaucoup de messages hors sujet ou de tentatives pour obtenir la réponse [30] (vu).
- **Refonte 2026 [29][30] (vu).**
  - Khanmigo est « plus visible pendant que l'élève travaille ».
  - Il « offre de l'aide au moment où il en a besoin », sans attendre « la question parfaite ».
  - Il se comporte différemment **avant et après une tentative**, et selon qu'il s'agit d'une première découverte ou d'une révision.
  - Sal Khan : « The AI could not just sit next to the content. It had to be woven into it. »
  - Dans une autre expérience, un chatbot qui apparaît sans que l'élève le demande, avec passage à la suite uniquement après une bonne réponse [30] (vu).
- **Captures Khan Academy FR [31] (vu).** Page de cours « Arithmétique – 8 190 / 19 400 points de maîtrise », carte « Défi de maîtrise », liste d'unités ; exercice QCM avec bouton « Vérifier ».

### 2.12 Photomath / Gauth / Brainly (usages réels des collégiens)

- **Photomath** : scan d'un problème imprimé ou manuscrit → étapes, « plusieurs méthodes de résolution », graphiques interactifs [33] (vu).
- **Gauth** : étapes « STEP 1, STEP 2 » avec des astuces « how » et « why », et des tuteurs humains [34] (vu).
- **Brainly** : réponses « vérifiées par des experts », scan photo [32] (vu).
- **Leçon (déduit).** Le réflexe « photo → réponse » est déjà installé chez les élèves. Le bouton photo de Jules doit donc exister, mais déboucher sur un **guidage** (comme Alfa) et non sur une solution.

---

## 3. Motifs d'UI récurrents

1. **Accueil = une action principale + un indicateur de continuité.**
   - Knowunity : « Continuer le plan d'étude » [16].
   - Nomad : « Exercice suivant » / « Prochain exercice suggéré » [12].
   - digiSchool : rappels de révisions [18].
   - Personne n'ouvre sur un catalogue.
2. **Liste des matières = cartes illustrées + barre de progression** (Kartable, SchoolMouv, Nomad) [3][6][12].
3. **Chapitre = une page-hub avec 4 ou 5 tuiles** (fiche, quiz, flashcards, exercice), ou un **chemin vertical d'étapes** (Knowunity : récap → expliquer à voix haute → quiz → examen blanc) [6][12][16].
4. **Tuteur = chat en bulles avec mascotte** (Knowie, Nono, Khanmigo). Le champ de saisie propose **photo + micro** [16][12][28]. Des puces de suggestions évitent la page blanche [28].
5. **Tuteur intégré à l'exercice plutôt qu'à côté** : Khan le fait en 2026 après avoir constaté la sous-utilisation [29][30] ; Alfa travaille sur la photo de l'exercice [2].
6. **Feedback immédiat + « Pourquoi ? »** : bandeau vert, explication juste sous la réponse, bouton « Pourquoi ? » (Knowunity, digiSchool, Quizlet) [16][18][25].
7. **Flashcards à deux boutons binaires** : « Je l'apprends / Je le savais » (SchoolMouv), compteurs « à revoir / appris » (Quizlet), « Revoir les cartes ratées » (Knowunity) [6][25][15].
8. **Import photo/PDF → chapitre perso** avec étiquette d'origine : « Généré par scan » (SchoolMouv), badges `IA` / `Profs` (Nomad), « Mes chapitres IA » en premier dans la grille [6][12].
9. **Gamification** : XP, série (flamme), gemmes, trophées, ligues [3][6][14][18]. Chez Khan, les points servent à personnaliser l'avatar du tuteur [28].
10. **Bilan en compétences** plutôt qu'en notes : points forts / points faibles formulés en verbes d'action (Adaptiv'Collège) [21] ; « Tu maîtrises ces mots / À retravailler » (Knowunity) [15].
11. **Parent** : compte séparé, code famille, stats (moyenne, temps, progression) et notifications (Nomad) [11] ; courbe et lacunes (Kartable) [1] ; bouton côté élève « Montre à tes parents que tu gères » (Nomad) [12].
12. **Accessibilité dys** : quasi absente chez les applis grand public. On la trouve chez les éditeurs : mode dyslexie en 1 clic, Doc'Adapt, manuels audio [35][36][37].

---

## 4. Idées à fort potentiel pour un tuteur dys de 3e (classées)

Chaque idée est compatible avec les contrats existants de Jules : fiche visuelle, exercices v2, cartes mémoire à palier fixe, sources personnelles (déduit ; à valider par Alex).

1. **Tuteur « tissé » dans l'exercice, qui change de rôle avant et après la tentative.**
   - Avant la réponse : l'aide propose l'échelle d'indices à 3 barreaux.
   - Après une erreur : Jules commente la réponse de l'élève.
   - L'aide s'affiche d'elle-même au bon moment, sans attendre que l'élève ose demander.
   - Sources : Khanmigo 2026 [29][30], Alfa [2].
2. **Accueil « on continue » avec un seul gros bouton** (« Continuer : Thalès, étape 2/4 ») et la prochaine révision due juste en dessous. Sources : Knowunity [16], Nomad [12], digiSchool [18].
3. **Chapitre présenté en chemin d'étapes court et vertical** : fiche → dire / reformuler → exercices → mini-brevet. L'élève voit où elle en est ; une seule étape est active à la fois (moins de charge visuelle qu'une grille). Source : Knowunity [16] ; hub à tuiles de SchoolMouv / Nomad en variante [6][12].
4. **Étiquette d'origine partout.** Badge « Jules / vérifié » ou « PERSO / généré depuis ta photo » sur chaque fiche et chaque exercice, avec une légende en tête de page. C'est la version Nomad du « PERSO + sparkles » déjà décidé. Sources : Nomad [12], SchoolMouv « Généré par scan » [6].
5. **Import pensé dys, pas seulement pour générer.**
   - Une photo ou un PDF du cours donne d'abord une **version lisible** : police, interlignage, découpage, lecture vocale.
   - Ensuite seulement viennent fiche, cartes et quiz.
   - Plus un mode dyslexie activable en 1 clic, visible dès l'accueil.
   - Sources : Doc'Adapt [36], mode dyslexie Le Livre Scolaire [35], SONDO [37] ; pipeline de génération de Knowunity [14].
6. **Voix dans les deux sens.**
   - Micro dans le champ du tuteur.
   - Étape « Explique à voix haute » : l'élève dit sa réponse, Jules la vérifie.
   - Lecture audio des fiches, format podcast pour réviser.
   - Sources : Knowunity [14][16], NotebookLM Audio [27], podcasts myMaxicours [20].
7. **Flashcards à deux gros boutons et fin de série orientée erreurs** : « Je savais / À revoir », puis « Revoir les 2 cartes ratées ». Un écran « Ce que tu maîtrises / À retravailler », rattaché au palier fixe 1-3-7-15-30-60, et une **liste du jour** qui persiste entre les sessions (le point faible de Quizlet). Sources : SchoolMouv [6], Knowunity [15], Quizlet [25][26].
8. **Bilan en compétences formulées en verbes**, points forts avant points faibles, pastilles Terminé / En cours / À explorer par chapitre. C'est une alternative au jargon « Attendu 1..4 » que l'élève ne doit pas voir. Source : Adaptiv'Collège [21].
9. **Chat ancré dans la page, avec citations cliquables** : chaque explication du tuteur renvoie au bloc précis de la fiche ou de la leçon, qui s'illumine. Source : NotebookLM [27].
10. **Feedback « Bonne réponse ! + pourquoi » placé directement sous la question**, avec un bouton « Pourquoi ? » même quand la réponse est juste. Sources : digiSchool [18], Knowunity [16].
11. **Espace parent minimal et positif.**
    - Côté élève : un bouton « Montrer à papa ce que j'ai fait ».
    - Côté parent : temps passé, chapitres travaillés, lacunes, sans note prédictive anxiogène.
    - Sources : Nomad [11][12], Kartable [1] (courbe, lacunes, rituel de 15 min par semaine).
12. **Gamification légère et non compétitive.** Série et XP modestes, célébration de fin d'exercice. Les points servent à personnaliser Jules (comme les chapeaux de Khanmigo) plutôt qu'à des ligues. Sources : Khanmigo [28], Kartable [3] ; ligues Knowunity [14] à écarter pour une élève fragile (déduit).

**À ne pas reprendre (déduit) :**
- une interface qui ressemble à un logiciel de remédiation (« années 80 », « infantilisant ») [23] ;
- un chat à côté du contenu qu'il faut aller chercher [29][30] ;
- le score prédit / la note cible mis en avant (Knowunity [16]), risqué pour une élève dys en manque de confiance.

---

## Sources

[1] https://www.kartable.fr
[2] https://www.kartable.fr/cours-particuliers-alfa
[3] https://itunes.apple.com/search?term=kartable&country=fr&entity=software (fiche App Store Kartable id825500330 : description, version, captures)
[4] https://www.schoolmouv.fr
[5] https://www.schoolmouv.fr/parent
[6] https://itunes.apple.com/lookup?id=1353761629&country=fr (fiche App Store FR SchoolMouv : description, captures)
[7] https://reussite.schoolmouv.fr/presentation-fiche-cours-revision/
[8] https://reussite.schoolmouv.fr/presentation-quiz-exercices/
[9] https://apps.apple.com/fr/app/nomad-education-brevet-bac-sup/id1441761075
[10] https://play.google.com/store/apps/details?id=com.nomadeducation.nomadeducation&hl=fr
[11] https://support.nomadeducation.fr/fr/articles/12549031-comment-creer-et-gerer-un-compte-parent-dans-l-application-nomad-education
[12] https://itunes.apple.com/lookup?id=1441761075&country=fr (captures et notes de version Nomad)
[13] https://knowunity.fr
[14] https://apps.apple.com/fr/app/knowunity-ton-coach-scolaire/id1484296272
[15] https://knowunity.fr/ai/flashcards
[16] https://itunes.apple.com/lookup?id=1484296272&country=fr (captures Knowunity)
[17] https://apps.apple.com/fr/app/digischool-education-2027/id6443938926
[18] https://itunes.apple.com/lookup?id=6443938926&country=fr (captures digiSchool)
[19] https://play.google.com/store/apps/details?id=com.digischool.education.community&hl=fr
[20] https://www.maxicours.com
[21] https://evidenceb.fr/produits/adaptivcollege
[22] https://evidenceb.fr/produits/miaseconde
[23] https://www.ia-edu.fr/mia-seconde-avis-enseignants-eleves
[24] https://evidenceb.fr/produits/
[25] https://itunes.apple.com/lookup?id=546473125&country=fr (Quizlet : description, captures)
[26] https://nebulearn.app/blog/quizlet-is-not-spaced-repetition
[27] https://itunes.apple.com/lookup?id=6737527615&country=fr (Gemini Notebook / NotebookLM : description, captures)
[28] https://www.khanmigo.ai/learners
[29] https://blog.khanacademy.org/learning-in-the-open-what-ai-is-and-isnt-changing
[30] https://www.chalkbeat.org/2026/08/25/ai-tutoring-students-khanmigo-khan-academy-engagement-study
[31] https://itunes.apple.com/lookup?id=469863705&country=fr (Khan Academy : captures FR)
[32] https://play.google.com/store/apps/details?id=co.brainly&hl=fr
[33] https://play.google.com/store/apps/details?id=com.microblink.photomath&hl=fr
[34] https://www.gauthmath.com
[35] https://profpower.lelivrescolaire.fr/lecture-contenus-adaptes-dyslexiques
[36] https://www.lelivrescolaire.fr/informations-innovation-numerique
[37] https://www.editions-bordas.fr/sondo-les-manuels-scolaires-accessibles-aux-eleves-dys.html
[38] https://www.lalilo.com/en (extrait de résultat de recherche seulement)

*Limites.*
- Les écrans sont décrits d'après les captures marketing des stores, qui sont souvent idéalisées ; les parcours réels (profondeur de navigation, nombre de clics) n'ont pas pu être vérifiés sans compte.
- Le prix SchoolMouv n'a pas été trouvé en clair.
- Pas de transcription vidéo exploitée.
- La page Doc'Adapt (docadapt.fr) n'a pas pu être extraite ; la description vient de la page Le Livre Scolaire [36].
