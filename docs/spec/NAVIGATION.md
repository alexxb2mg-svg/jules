# Jules : navigation unique, sur le modele DinoBot

Statut : v2 du 26/09/2026. Decisions D1 a D4 tranchees par Alex ; bloquants et remarques de la relecture
REVIEWER du 26/09 integres. A relire par REVIEWER avant creation des cartes DEV.
Numerotation : lot 3, EX-201 a EX-2xx (EX-0xx et EX-1xx sont pris par la spec adaptations).

**Base de reference : `origin/main` `23c6262` (#43).** Les numeros de ligne cites sont lus sur cette base.
Toute carte DEV part de la tete d'`origin/main` obtenue apres les fusions prealables (section 8).

## 1. Demande

Alex, 26/09/2026 : « la navigation est franchement pourrie. On avait un super exemple avec dinobot pour
organiser ca de facon coherente et logique, simple et fluide, la c'est l'enfer, il va falloir revoir ca. »

## 2. Etat de depart (lu sur `23c6262`)

| Page | Route | Navigation propre a la page |
|---|---|---|
| Mes fiches | `/` (accueil.html) | rail gauche : Mes fiches, Discuter avec Jules, M'entraîner (`/studio`), Mon suivi (`/parent`) + liste des notions groupee par matiere |
| Discuter | `/discuter` (eleve.html) | colonne gauche d'historique + un seul bouton « Mes fiches » |
| Cours | `/cours` (cours.html) | panneau « Parcours » (☰) avec son propre `select-matiere`, logo -> `/`, panneau Jules a droite. **Absent du rail.** |
| M'entraîner | `/studio` (studio.html) | panneau « Mes supports » (☰) avec son propre `select-matiere`, logo -> `/`, panneau Jules a droite |
| Espace parent | `/parent` (parent.html) | bouton « Page élève » |

Defauts constates :
- Cinq pages, cinq systemes de navigation ; le rail n'existe que sur `/`.
- Depuis `/discuter`, `/cours`, `/studio`, `/parent`, on ne peut que revenir a `/`.
- `/cours` n'est atteignable depuis aucun menu.
- « Mon suivi » cote eleve pointe vers `/parent`, protege par le code parent.
- Trois choix de matiere independants (`/cours`, `/studio`, liste groupee de `/`).

Donnees deja disponibles sans nouvel appel : chacune des trois pages de contenu recoit deja la liste
`matieres [{id, nom}]` de son propre point d'API (`/api/eleve/fiches_visuelles/notions`,
`/api/eleve/cours/parcours`, `/api/eleve/studio/notions`) ; `/api/infos` renvoie deja `prenom`.

Contraintes existantes que le composant doit respecter (releve DEV) : aucun `<script>` en ligne, aucun
`onX=`, aucun `style=` dans les HTML (`tests/test_web.py`, CSP `script-src 'self'`) ; ordre de chargement
`symboles.js < /rappels.js < commun.js` (`tests/test_symboles.py`) ; `/discuter` servi sans code.
Aucun test existant ne controle la navigation : les tests EX-2xx sont tous neufs.

## 3. Le modele DinoBot (compte d'essai, captures du 26/09/2026)

- Une barre laterale unique, identique sur tous les ecrans, groupee en rubriques titrees, entree active
  surlignee, icone + libelle court, repliable, prenom de l'eleve en pied.
- Un selecteur de matiere unique en haut au centre, qui s'applique a toutes les activites.

On reprend la structure, pas l'habillage. Le cadrage interface du 25/09 reste valable pour l'ecran d'une fiche.

## 4. Arborescence cible

```
[Barre laterale, sur toutes les pages eleve]
  Jules (marque)                         [replier]
  APPRENDRE
    Mes fiches               /
    Mes leçons               /cours
  M'ENTRAÎNER
    Exercices et supports    /studio
  DISCUTER
    Discuter avec Jules      /discuter   (l'historique reste DANS la page)
  MON ESPACE
    Espace parent            /parent     (icone cadenas)
  pied : prenom de l'eleve

[En-tete, centre] selecteur de matiere sur /, /cours, /studio
```

La reference fait foi : `docs/spec/navigation-reference.json` (ecrite par SPEC, DEV ne la modifie pas).

## 5. Exigences

**EX-201 - Une seule barre laterale.** Les pages eleve (`/`, `/cours`, `/studio`, `/discuter`) affichent la
meme barre, produite par un seul composant partage (un JS et un CSS communs, en fichiers externes, dans le
respect des contraintes de la section 2).
*Verification* : test Chromium (section 6) qui compare la liste ordonnee (rubrique, libelle, href) de la barre
sur les 4 pages : identique. Test statique limite aux balises `<a>` et `<nav>` des `jules/web/static/*.html` :
aucun libelle de la barre en dur hors composant (`<title>`, `document.title`, commentaires et tests exclus).

**EX-202 - Contenu, ordre et libelles.** Rubriques et entrees exactement comme `navigation-reference.json`.
Les libelles affiches portent leurs accents (« Mes leçons », « M'entraîner »).
*Verification* : comparaison **exacte** au JSON apres seulement retrait des emojis et normalisation des espaces ;
accents et casse compares. Cas temoin negatif dans le test : « Mes lecons » doit echouer.

**EX-203 - Entree active.** L'entree de la page courante porte `aria-current="page"` et un style distinct ;
une seule a la fois. Elle se choisit sur `location.pathname` seul, parametres `?...` ignores.
*Verification* : par page, exactement 1 `[aria-current=page]` dont le href est le chemin charge ; cas
`/discuter?notion=x` -> « Discuter avec Jules » active.

**EX-204 - Tout ecran a un clic de tout autre.** Depuis chaque page eleve, chaque entree de la reference est un
lien present dans la barre.
*Verification* : test pour chaque couple (page A, entree B).

**EX-205 - Suppression des navigations concurrentes.** Disparaissent : le bouton « Mes fiches » d'`eleve.html`,
les liens logo -> `/` de `cours.html` et `studio.html`, les liens de sections du rail d'`accueil.html` (la liste
des notions reste), les deux `select-matiere` internes de `/cours` et `/studio` (remplaces par EX-209). Les
panneaux internes (Parcours, Mes supports, historique) restent, sans lien vers une autre section.
Exemptions nommees, et seulement elles : `#chat-flottant-lien` d'`accueil.html` (lien `/discuter?notion=...`
voulu par le cadrage du 25/09) et `#retour-eleve` de `parent.html` (EX-206).
*Verification* : test statique : aucun `<a href>` vers une route de section dans les HTML hors composant, sauf
ces deux identifiants.

**EX-206 - Espace parent separe.** L'entree « Espace parent » porte une icone cadenas et l'indication « code
parent » (texte ou `aria-label`). `/parent` n'affiche pas la barre eleve ; son unique lien de retour a l'id
`retour-eleve`, le libelle « Retour à l'espace élève » et le href `/`. Plus aucune entree « Mon suivi ».
*Verification* : `/parent` sans `<nav aria-label="Sections de Jules">` ; `#retour-eleve` present ; aucun libelle
« Mon suivi » dans les HTML ni dans le composant.

**EX-207 - Tablette et telephone.** Sous 900 px de large, la barre devient un tiroir ouvert par un bouton ☰
unique, au meme endroit sur les 4 pages ; il se ferme apres un clic sur une entree et par Echap. A partir de
900 px, la barre est visible et repliable en icones ; l'etat replie est memorise en localStorage (cle
`jules.nav.repliee`, booleen, rien d'autre).
*Verification* : scenario section 6, a 768 x 1024 et 1280 x 800, sur les 4 pages.

**EX-208 - Accessibilite, controles explicites (pas d'axe-core).** La barre est un
`<nav aria-label="Sections de Jules">` ; chaque rubrique est un titre ; chaque entree est un `<a>` dont le nom
accessible est son libelle ; les emojis sont dans un `<span aria-hidden="true">` ; le bouton ☰ tient
`aria-expanded` et `aria-controls` a jour ; une regle `:focus-visible` couvre entrees et bouton ; l'ordre DOM
suit l'ordre visuel ; tailles en `rem`.
*Verification* : test statique (DOM et CSS) + scenario section 6 : `aria-expanded` bascule a l'ouverture et a
Echap ; chaque entree accepte `focus()` et une regle `:focus-visible` la cible.

**EX-209 - Selecteur de matiere commun (D1 = oui).** Un seul selecteur, dans l'en-tete, sur `/`, `/cours` et
`/studio`. Pas sur `/discuter` (la discussion couvre toutes les matieres). Il est rempli avec la liste
`matieres [{id, nom}]` que la page recoit deja de son propre point d'API : **aucun appel ajoute, aucun champ
ajoute a `/api/infos` ni a aucune reponse.** Le choix est memorise en localStorage (cle `jules.matiere`, valeur =
l'`id` de matiere seul, aucune donnee de l'eleve) et filtre la page.
Matiere memorisee absente de la liste de la page :
- `/cours` et `/studio` envoient l'id memorise tel quel (`?matiere=<id>`), en un seul appel ; le serveur
  retombe deja sur sa matiere par defaut quand l'id est inconnu (`jules/modules/cours.py`, `parcours()` :
  `matiere_id if matiere_id in ids_dispo else ...`, repris par `studio.notions()`) et renvoie la matiere
  retenue dans le champ `matiere`. La page affiche cette matiere retenue et **n'ecrase pas** la memoire.
- `/` (liste deja complete) affiche la premiere matiere de sa liste, sans ecraser la memoire.
Notion demandee a l'ouverture : **seule `/` est concernee dans ce lot**, par le fragment `#<id>` qu'elle lit
deja (`accueil.js`) ; toutes les matieres y sont chargees, donc la page ouvre la notion, aligne le selecteur
sur sa matiere et memorise cette matiere. L'ouverture d'une notion par l'URL sur `/cours` et `/studio` est
hors lot (section 7).
*Verification* : scenario section 6 : (a) choisir une matiere sur `/`, ouvrir `/studio` puis `/cours` -> meme
matiere selectionnee et liste filtree ; (b) `/#<notion d'une autre matiere que la memorisee>` -> la notion
s'ouvre, le selecteur suit et `jules.matiere` vaut sa matiere ; (c) `jules.matiere = "inconnue"` puis `/cours`
-> un seul appel `parcours?matiere=inconnue`, la page affiche la matiere renvoyee par le serveur, et
`jules.matiere` vaut toujours `"inconnue"` ; (d) test API : `GET /api/eleve/cours/parcours?matiere=inconnue`
-> 200, `matiere` = la premiere matiere du catalogue qui a au moins une lecon (sinon la premiere tout court),
calculee par le test a partir du catalogue et des lecons, pas codee en dur (idem `studio/notions`) ; (e) appels
reseau conformes a EX-210.

**EX-210 - Pas de regression, pas de donnee nouvelle.** Routes inchangees (HTTP 200 sur `/`, `/cours`,
`/studio`, `/discuter`, `/parent`) ; aucune route ni champ d'API ajoute ; pied de barre = `prenom` de
`/api/infos`, deja expose, rien d'autre du profil (ni niveau, ni age, ni etablissement).
*Verification* : `pytest` complet vert ; le diff de la carte ne touche aucun `*.py` de `jules/` (routes,
`infos_interface`) ; test statique : le composant ne lit que `persona` et `prenom` dans les infos ; scenario
section 6 : sur chaque page, l'ensemble des **chemins** `/api/...` appeles au chargement (parametres de requete
ignores, `?matiere=` autorise) est identique avant et apres la carte, et chaque chemin n'est appele qu'une fois.

## 6. Methode de test navigateur (EX-201, 203, 207, 208, 209)

- Outillage existant seulement : Chromium headless `--dump-dom`, comme `tests/test_symboles.py`.
  **Aucune dependance nouvelle** (ni Playwright, ni axe-core, ni client websocket).
- Le test sert la page par une app de test qui injecte, **uniquement en test**, un script de scenario
  (`/_test/scenario-nav.js`). Ce script clique (`element.click()`), envoie un `keydown` Echap, lit
  `localStorage`, `getComputedStyle` et les `aria-*`, et ecrit ses resultats en JSON dans un
  `<pre id="resultat-scenario">` relu par `--dump-dom`. Taille par `--window-size`. Le HTML de production
  n'est pas modifie pour le test.
- La touche Tab ne se simule pas : le parcours clavier est couvert par l'ordre DOM et `focus()` (EX-208).
- **Un test ignore compte comme un echec** : avec `JULES_CHROMIUM_OBLIGATOIRE=1`, ces tests echouent (pas de
  `skip`) si Chromium manque ; la revue exige `pytest -rs` avec 0 test EX-2xx ignore.

## 7. Hors perimetre (decisions d'Alex du 26/09/2026)

- **D1** : selecteur de matiere en haut, oui (EX-209).
- **D2** : « Mon suivi » cote eleve retire ; le suivi reste dans l'espace parent.
- **D3** : page et entree « Brevet » (annales a gauche, Jules a droite) : chantier futur, aucune entree d'ici la.
- **D4** : « Mes fiches » et « Mes leçons » restent deux entrees ; leur fusion est un autre chantier.
- Ouvrir une notion par l'URL sur `/cours` et `/studio` (ni `?notion=` ni `#<id>` n'y sont lus aujourd'hui,
  et leurs API ne renvoient que la matiere demandee) : lot suivant.
- Design fin, contenu des pages, espace parent (hors lien de retour), cablage de Jules sur les adresses.

## 8. Prealables et ordre de fusion

1. `adaptations/ex-010-rem` (CSS global en `rem`) fusionnee sur `origin/main`.
2. `adaptations/ex-001-002-003-poignee` fusionnee. **Decision SPEC : c'est elle qu'on garde.** Elle contient
   deja les deux commits d'`adaptations/ex-009-iframe` (69c7592, 0ac5e64 ; verifie par
   `git merge-base --is-ancestor`) : son `outils-hote.js` prolonge celui d'EX-009, ce n'est pas une version
   concurrente. `ex-009-iframe` n'est pas fusionnee a part ; la branche reste en place.
3. Carte navigation : ne demarre qu'apres 1 et 2, sur la tete d'`origin/main` qui en resulte.
`ex-006-007-voix` et `ex-013-carnet` (risque faible) peuvent passer avant ou apres ; si apres, rebase sur la navigation.

## 9. Risques

- Branches anciennes `origin/cours-*`, `studio-*`, `interface-cours` sur les memes HTML : a confirmer abandonnees
  par Alex ; ignorees par ce lot, rien n'est supprime.
