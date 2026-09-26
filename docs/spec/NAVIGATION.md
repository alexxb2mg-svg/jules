# Jules : navigation unique, sur le modele DinoBot

Statut : brouillon SPEC du 26/09/2026, a relire par REVIEWER et a valider par Alex (decisions D1 a D4).
Numerotation : lot 3, EX-201 a EX-2xx (EX-0xx et EX-1xx sont pris par la spec adaptations).

## 1. Demande

Alex, 26/09/2026 : « la navigation est franchement pourrie. On avait un super exemple avec dinobot pour
organiser ca de facon coherente et logique, simple et fluide, la c'est l'enfer, il va falloir revoir ca. »

## 2. Etat de depart (mesure sur main 6717025, fichiers `jules/web/static/*.html` et `jules/web/app.py`)

| Page | Route | Navigation propre a la page |
|---|---|---|
| Mes fiches | `/` (accueil.html) | rail gauche : Mes fiches, Discuter avec Jules, M'entrainer (`/studio`), Mon suivi (`/parent`) |
| Discuter | `/discuter` (eleve.html) | colonne gauche d'historique + un seul bouton « Mes fiches » |
| Cours | `/cours` (cours.html) | panneau « Parcours » (☰), logo -> `/`, panneau Jules a droite. **Absent du rail.** |
| M'entrainer | `/studio` (studio.html) | panneau « Mes supports » (☰), logo -> `/`, panneau Jules a droite |
| Espace parent | `/parent` (parent.html) | bouton « Page eleve » |

Defauts constates :
- Cinq pages, cinq systemes de navigation differents ; le rail n'existe que sur `/`.
- Depuis `/discuter`, `/cours`, `/studio`, `/parent`, on ne peut que revenir a `/` : pas de passage direct d'une section a l'autre.
- `/cours` (les lecons) n'est atteignable depuis aucun menu.
- « Mon suivi » cote eleve pointe vers `/parent`, protege par le code parent : l'eleve tombe sur un ecran de code.
- Aucun choix de matiere commun : chaque page gere son propre choix de notion.

## 3. Le modele DinoBot (vu dans le compte d'essai, captures du 26/09/2026)

- Une **barre laterale unique**, identique sur tous les ecrans, groupee en rubriques titrees :
  ACTIVITES (Chat, Fiches, Cours illustre, Exercice, Brevet, Evaluation, Historique),
  MON ESPACE (Mes cours, Mes informations, Mes offres), INFORMATIONS & SUPPORT (Aide).
  Entree active surlignee, icone + libelle court, repliable, profil de l'eleve en pied.
- **Un selecteur de matiere unique en haut au centre**, qui s'applique a toutes les activites.
- Dans une activite, **contenu a gauche, tuteur a droite**, bascule d'affichage en haut a droite.

On reprend la structure, pas l'habillage. Le cadrage interface du 25/09 reste valable pour l'ecran d'une
fiche (cours au centre, Jules en bulles et fenetre flottante) : cette spec ne porte que sur le passage
d'un ecran a l'autre.

## 4. Arborescence cible

```
[Barre laterale, sur toutes les pages eleve]
  Jules (marque)                         [replier]
  APPRENDRE
    Mes fiches            /              (accueil)
    Mes lecons            /cours
  M'ENTRAINER
    Exercices et supports /studio
    Brevet                (D3, non livre dans ce lot)
  DISCUTER
    Discuter avec Jules   /discuter      (l'historique des discussions reste DANS la page)
  MON ESPACE
    Mon suivi             (D2)
    Espace parent         /parent        (code parent, icone cadenas)
  pied : prenom de l'eleve, niveau

[En-tete, centre] selecteur de matiere (D1)
```

## 5. Exigences

**EX-201 - Une seule barre laterale.** Toutes les pages eleve (`/`, `/cours`, `/studio`, `/discuter`)
affichent la meme barre laterale, produite par un seul composant partage (un fichier JS et un fichier CSS
communs), et non recopiee dans chaque HTML.
*Verification* : test qui charge les 4 pages et compare la liste ordonnee (libelle, href) des liens de la
barre : identique partout ; `git grep` montre que les libelles de la barre n'existent que dans le composant.

**EX-202 - Contenu et ordre de la barre.** Rubriques et entrees exactement comme en section 4 (hors entrees
soumises a D2/D3 tant qu'elles ne sont pas tranchees). Libelles en francais, sans jargon technique.
*Verification* : le test d'EX-201 compare a une liste de reference ecrite par SPEC (`docs/spec/navigation-reference.json`), pas par DEV.

**EX-203 - Entree active.** L'entree de la page courante porte `aria-current="page"` et un style distinct ;
une seule entree active a la fois.
*Verification* : test par page : exactement 1 element `[aria-current=page]` dans la barre, dont le href est la route chargee.

**EX-204 - Tout ecran est a un clic de tout autre.** Depuis n'importe quelle page eleve, chaque section est
atteignable en un clic via la barre. Plus aucune page eleve atteignable seulement par l'URL.
*Verification* : test qui, pour chaque couple (page A, section B), trouve dans A un lien vers B.

**EX-205 - Suppression des navigations concurrentes.** Les boutons « Mes fiches » de `/discuter`, le lien
logo -> `/` de `/cours` et `/studio` et le rail propre a `accueil.html` disparaissent au profit de la barre.
Les panneaux internes a une page (« Parcours » de `/cours`, « Mes supports » de `/studio`, historique de
`/discuter`) restent, mais ne contiennent plus aucun lien vers une autre section.
*Verification* : `git grep` sur `jules/web/static/*.html` : aucun `href="/..."` de section hors composant ; revue visuelle REVIEWER.

**EX-206 - Espace parent separe.** L'entree « Espace parent » porte une icone cadenas et un libelle qui
annonce le code. `/parent` ne montre pas la barre eleve ; il garde un seul lien « Retour a l'espace eleve ».
Aucune entree eleve ne mene a un ecran de code sans le signaler.
*Verification* : test : `/parent` sans barre eleve ; l'entree « Mon suivi » (si D2 = page eleve) ne pointe pas vers `/parent`.

**EX-207 - Tablette et telephone.** En dessous de 900 px de large, la barre se replie en tiroir ouvert par un
bouton ☰ unique, place au meme endroit sur toutes les pages ; le tiroir se ferme apres un clic sur une entree
et par Echap. Au-dessus, la barre est visible et repliable en icones, et l'etat replie est memorise (localStorage).
*Verification* : test navigateur (Chromium, 0 test ignore) a 768 px et 1280 px sur les 4 pages.

**EX-208 - Accessibilite.** La barre est un `<nav aria-label="Sections de Jules">`, les rubriques sont des
titres, tout est utilisable au clavier (Tab, Entree, Echap) avec un focus visible ; les emojis des libelles
sont `aria-hidden`. Compatible avec les reglages d'adaptation existants (police, taille en rem).
*Verification* : test clavier navigateur + controle axe-core sans erreur « serious/critical » sur la barre.

**EX-209 - Selecteur de matiere commun (soumis a D1).** Un selecteur unique dans l'en-tete, identique sur les
pages eleve, liste les matieres disponibles pour le niveau de l'eleve (lues dans le programme charge, jamais
codees en dur). Le choix est memorise et filtre Mes fiches, Mes lecons et M'entrainer.
*Verification* : test : changer la matiere sur `/` puis ouvrir `/studio` : meme matiere affichee et liste filtree.

**EX-210 - Pas de regression.** Les routes existantes repondent toujours (y compris liens deja partages et
favoris de l'ecran d'accueil de la tablette), la suite de tests reste verte, aucun appel API ajoute par la navigation.
*Verification* : `pytest` complet vert ; test HTTP 200 sur `/`, `/cours`, `/studio`, `/discuter`, `/parent`.

## 6. Decisions attendues d'Alex

- **D1 - Selecteur de matiere en haut, comme DinoBot ?** Proposition : oui (EX-209).
- **D2 - « Mon suivi » cote eleve** : a) une page eleve simple (notions vues, reussites, temps), a specifier
  dans un lot suivant, l'entree est masquee d'ici la ; b) on retire l'entree, le suivi reste reserve au parent.
  Proposition : b pour ce lot.
- **D3 - Entree « Brevet »** (annales PDF a gauche, Jules a droite, repris de DinoBot) : a specifier plus tard ;
  l'entree n'apparait pas tant que la page n'existe pas. Proposition : hors de ce lot.
- **D4 - Fiches et lecons** : on garde deux entrees (« Mes fiches » = condense visuel, « Mes lecons » = cours
  complet) ; les fusionner est un chantier a part. Proposition : deux entrees.

## 7. Hors perimetre

Design fin (couleurs, icones definitives), contenu des pages, page Brevet, page de suivi eleve, espace parent
(hors lien de retour), cablage de Jules sur les adresses.

## 8. Risques

- Les tests existants qui cherchent le rail ou le bouton « Mes fiches » (`tests/test_web.py`,
  `tests/test_fiches_visuelles_web.py`) casseront : a mettre a jour dans la meme carte, pas a supprimer.
- Les branches en cours qui touchent les memes HTML (adaptations EX-006/007/009/010) : conflits probables,
  a fusionner avant de commencer.
