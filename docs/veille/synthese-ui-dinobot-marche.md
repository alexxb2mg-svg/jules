# Synthèse de veille UI : DinoBot + tuteurs IA du marché français (28/09/2026)

**Statut : proposition, à trancher par Alex.** Aucune idée n'est adoptée tant qu'il n'a pas choisi.
Principe : on s'inspire, on n'adopte que ce qui est vraiment meilleur que l'existant de Jules.

Sources :
- `docs/veille/DinoBot_exploration_2026-09-26.docx` et `docs/veille/dinobot-generation-fiches.md` (études précédentes) ;
- visite DinoBot du 28/09 (compte de l'élève, écrans : accueil/chat, sélecteur de matière, Exercice, Évaluation, Brevet, Historique, Aide) ;
- `docs/veille/tuteurs-ia-marche-fr.md` (12 produits, sources publiques, 38 références).

## 1. DinoBot : ce qui n'avait pas encore été relevé (visite du 28/09)

| Élément | Ce qu'on voit | Jules aujourd'hui |
|---|---|---|
| **Sélecteur de matière global** | Une pastille colorée en haut au centre, avec l'icône de la matière. Elle ouvre une liste où chaque matière a sa couleur et son icône. Les matières non prêtes sont marquées « Bientôt disponible ». Le choix vaut pour **tous** les écrans. | La matière se choisit dans chaque écran (bibliothèque, supports). |
| **Accueil = une question** | Mascotte, « Bonjour <prénom> 👋 », « Que souhaites-tu savoir aujourd'hui ? », grand champ avec 📎 (image/PDF) et calculatrice de formules, **suggestions de questions en carrousel** propres à la matière. | Notre accueil pose « devoir ou révision ? » (validé par Alex). Il n'a pas de suggestions de questions. |
| **Choix de source en 2 cartes** | « Base de données » / « À partir d'un fichier ». Le même écran sert pour Exercice, Fiches et Cours illustré. | **Déjà repris** (« Mes cours Jules » / « Mon document »). |
| **Formulaire de génération** | Carte centrée : chapitre, durée en 3 cases hh:mm:ss, nombre d'exercices et de questions, difficulté en **curseur 1-3**, consigne libre de 1 000 caractères, un seul bouton. | Nos générateurs n'ont pas de réglages exposés à l'élève. |
| **Brevet** | Sélecteurs Année et Localisation, puis état vide « Aucun examen trouvé ». En physique-chimie il n'y avait aucun sujet : l'état vide ne propose rien d'autre. | Les annales sont balisées (`balisage_annales_maths_2024-2026.jsonl`) mais pas encore affichées. |
| **Historique** | Replié dans la barre latérale : Chats et Documents. Aucune fiche générée n'y est gardée. | Nous avons la bibliothèque personnelle, les dossiers et Non classé. |
| **Pastilles « NOUVEAU »** dans la barre latérale | Signalent une fonction récente. | — |
| **Accessibilité** | Cantoo (lecture, dictée), à activer dans le profil, invisible ailleurs. | Adaptations dys natives, `lecture-vocale.js` (voix locales seulement). |
| **Données personnelles** | Le profil stocke nom, date de naissance, téléphone et établissement. | Rien de tout ça : **garder cette sobriété**. |

## 2. Marché français : ce qui revient partout

Voir `tuteurs-ia-marche-fr.md` §3. En bref :
- une **reprise en un clic** (« Continuer ») ;
- un **parcours de chapitre en étapes** ;
- des **flashcards à deux boutons** ;
- une **étiquette d'origine** sur les contenus (IA ou vérifié) ;
- **la voix** (micro et lecture) ;
- un **espace parent** positif ;
- une **gamification** légère.

Leçon de Khanmigo, refait en 2026 : un tuteur posé à côté du contenu, qu'il faut aller chercher, est peu utilisé (~15 %). **L'aide doit venir d'elle-même au bon moment.**

## 3. Tableau de décision (à trancher)

Légende de l'effort : S = moins d'une demi-journée, M = une journée, L = plusieurs jours.

| # | Idée | Vu chez | Jules a déjà… | Proposition | Effort |
|---|---|---|---|---|---|
| A | **Sélecteur de matière global** en haut (couleur et icône de `matieres-couleurs.css`), mémorisé, qui filtre tous les écrans | DinoBot | matière par écran | **Prendre** | M |
| B | **Suggestions de questions** sous le champ du chat, propres à la matière et au chapitre en cours, tirées de nos fiches (titres « À retenir », pièges) et **non générées** | DinoBot, Knowunity | chat sans suggestions | **Prendre** (depuis nos contenus) | S |
| C | **Bouton « Continuer »** en tête d'accueil (dernière fiche, leçon ou série), avec la révision du jour juste en dessous | Knowunity, Nomad, digiSchool | accueil « devoir ou révision ? » | **Prendre, en plus** de la question validée | S |
| D | **Aide qui vient d'elle-même** : après une erreur, la bulle d'indice (échelle à 3 barreaux déjà existante) s'ouvre toute seule dans l'exercice, sans passer par le chat | Khanmigo 2026, Alfa | indices à la demande | **Prendre** | S |
| E | **Chapitre = chemin vertical d'étapes** : fiche → exercices → cartes → mini-brevet, une seule étape active | Knowunity | parcours matière → chapitre → fiche | **Prendre** (réutilise `config/parcours.ts`) | M |
| F | **Flashcards : 2 gros boutons + « revoir les ratées »** | SchoolMouv, Knowunity | révision en 3 niveaux (facile, difficile, raté) sur palier fixe | **Garder nos 3 niveaux**, ajouter seulement « revoir les ratées » à la fin | S |
| G | **Étiquette d'origine partout** avec légende | Nomad, SchoolMouv | pastille PERSO (sources perso) | **Prendre** : légende « Jules · Perso » en tête de bibliothèque | S |
| H | **Version lisible d'abord** : une photo ou un PDF importé s'affiche d'abord en texte adapté dys (police, interligne, lecture vocale), la fiche vient ensuite | Le Livre Scolaire, Doc'Adapt | import → fiche directement | **Prendre** : c'est notre différence dys | M |
| I | **Micro dans le chat** (dictée) | Knowunity, DinoBot/Cantoo | lecture vocale seulement | **À discuter** : la dictée du navigateur envoie souvent la voix à un serveur tiers. Seulement si c'est faisable en local. | M |
| J | **Citations cliquables** : la réponse de Jules renvoie au bloc de la fiche, qui s'illumine | NotebookLM | écran partagé fiche \| Jules | **Prendre** | M |
| K | **« Pourquoi ? »** aussi sur une bonne réponse | digiSchool, Knowunity | explication après une erreur | **Prendre** | S |
| L | **Bilan en verbes** (« Tu sais calculer une probabilité »), points forts d'abord, pastilles Terminé / En cours / À explorer | Adaptiv'Collège | espace parent | **Prendre** pour l'élève et le parent | M |
| M | **Évaluation chronométrée** avec réglages (durée, nombre, difficulté en curseur) | DinoBot | séries d'exercices | **Plus tard**, avec les annales (juste/faux par le code) | L |
| N | **Annales du Brevet** choisies par année et centre, sujet à gauche et Jules à droite | DinoBot | balisage maths 2024-2026 | **Prendre**, mais avec un état vide utile (proposer une autre année ou matière) | L |
| O | **Gamification légère** (série, célébration de fin) | Khanmigo, Kartable | — | **À discuter** : risque de pression pour l'élève | S |
| P | **Pastilles « Nouveau »** dans la barre | DinoBot | — | **Prendre** (configurable) | S |

**À écarter :**
- les pages entières générées par l'IA ;
- une note fixée par l'IA ;
- le modèle à crédits et le compte à rebours commercial ;
- la note prédite (Knowunity) ;
- les ligues et classements ;
- le look « logiciel de remédiation » (MIA) ;
- la collecte de téléphone et de date de naissance.

## 4. Ordre proposé si tout est validé

1. S rapides : C, D, K, G, P, F (« revoir les ratées »), B.
2. A (sélecteur global), puis E (chemin de chapitre).
3. H (version lisible de l'import), J (citations).
4. L (bilan), puis N et M (annales et évaluation).
