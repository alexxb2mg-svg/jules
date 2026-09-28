# Les sources personnelles : contrat de travail

> **Implémenté le 28/09/2026** (branche `ui/refonte-2026-09-27`) :
> - moteur `jules/sources.py`, module `jules/modules/sources.py`, tests `tests/test_sources.py` ;
> - validateur `valider_fiche(..., origine="personnelle")` ;
> - front `front/src/modules/sources/*` et `config/sources.ts`.
>
> Le module est activé dans `config.local.yaml` (serveur de test 8795), pas encore dans `config.yaml`.

**Statut : validé par Alex le 28/09/2026 (« oui à tout » : Q0 à Q8, première option à chaque fois).**

Ce document fixe comment une source apportée par l'élève (photo, PDF, texte) devient une fiche
rangée dans sa bibliothèque personnelle. Il est écrit **avant** le code. En cas de doute, il fait
foi ; s'il est faux ou incomplet, le dire plutôt que le contourner.

Références :
- `docs/veille/sources-personnelles-besoin.md` (le besoin) ;
- `docs/veille/dinobot-generation-fiches.md` (l'étude) ;
- `docs/FICHES-VISUELLES.md` (la charte) ;
- `bibliotheque/SCHEMA-FICHE-VISUELLE.md` (le format) ;
- `docs/VISION.md` (les trois règles).

## Décisions d'Alex (28/09/2026)

1. **Deux familles de sources.**
   - **Natives** : notre collecte documentaire, la restitution actuelle (bibliothèques du dépôt).
   - **Personnelles** : apportées par l'élève.
2. **Entrées** : photo, PDF et texte collé.
3. **Format** : une source personnelle produit une fiche **au format des fiches visuelles**, et
   aucun autre.
4. **Rattachement** : c'est le LLM qui propose la notion à laquelle la fiche se rapporte.
5. **Pas de validation formelle.** Avant de quitter une fiche générée, l'élève répond à la question
   « on la garde ? ». Si oui, elle la range :
   - **dans la notion suggérée**,
   - **ou dans un dossier personnalisé**.
6. **Aucune notion trouvée** : la fiche va dans **« Non classé »**, ou directement dans un
   dossier personnalisé.
7. **Distinction** : dans la barre latérale, une fiche personnelle a une **autre couleur** qu'une
   fiche native, et un **filtre** affiche les unes ou les autres.

## 0. À trancher d'abord : la règle « l'élève produit, Jules relit »

La vision (`docs/VISION.md`, règle 2) dit : « Une fiche, une carte mentale ou un quiz fabriqués par
la machine ne laissent presque rien à l'élève. » Le studio a été construit sur cette règle. Or une
fiche générée depuis une source est précisément une fiche fabriquée par la machine.

**Proposition** : ce n'est pas contradictoire si l'on tient la ligne suivante.

- Une fiche personnelle est une **restitution du document de l'élève**, comme une fiche native
  est une restitution de notre collecte. C'est un **support de lecture**, pas le travail de
  l'élève.
- Le studio reste le seul endroit où l'élève **produit** (ses supports à elle, que Jules relit).
  Une fiche personnelle n'est jamais comptée comme un support produit par l'élève, ni dans le
  suivi du parent, ni dans le modèle de l'élève.
- La génération reste **fidèle à la source** (§5, règle de fidélité) : on reformule et on met en
  forme ce que le cours dit, on n'invente pas un cours.

**Question 0 pour Alex : cette ligne te convient-elle ?** Si non, il faut revoir la règle 2 de
`VISION.md` avant d'aller plus loin.

## 1. Vocabulaire

| terme | sens |
|---|---|
| **source** | ce que l'élève apporte : 1 à 5 photos, **ou** un PDF, **ou** un texte collé |
| **fiche personnelle** | fiche visuelle générée depuis une source, propriété de l'élève, jamais diffusée |
| **fiche native** | fiche d'une bibliothèque du dépôt (`bibliotheque/…`), comme aujourd'hui |
| **à ranger** | fiche générée pour laquelle l'élève n'a pas encore répondu à « on la garde ? » |
| **dossier** | dossier personnalisé créé par l'élève (nom libre) |
| **Non classé** | dossier fixe : fiches gardées sans notion ni dossier |

## 2. Le parcours

```
déposer ─► lire ─► proposer la notion ─► générer ─► contrôler ─► afficher (à ranger)
                                                                        │
                           « On garde cette fiche ? » avant de quitter ◄┘
                             ├─ Oui, dans « <notion suggérée> »
                             ├─ Oui, dans un dossier…  (choisir ou créer)
                             ├─ Oui, dans Non classé     (proposé si aucune notion trouvée)
                             └─ Non, ne pas garder       (fiche et source supprimées)
```

1. **Déposer** (§3). L'élève choisit « Mon document ». La matière est **facultative** : elle sert
   d'indice pour la recherche de notion (§4), pas de filtre.
2. **Lire**. La source est rendue lisible par le modèle (§3, extraction).
3. **Proposer la notion** (§4). Liste fermée du référentiel, contrôlée par le code.
4. **Générer** (§5). Le modèle écrit la fiche au format YAML des fiches visuelles.
5. **Contrôler**. Le **même validateur** que les fiches natives (`jules/fiches_visuelles.py`),
   adapté (§5). En cas de refus, **un seul** nouvel essai, avec le motif du refus renvoyé au
   modèle (c'est la boucle de contrôle de la charte). Si le second essai échoue aussi, on
   affiche « Je n'ai pas réussi à en faire une fiche propre », sans jamais afficher une fiche à
   moitié valide.
6. **Afficher**. Écran partagé fiche | Jules, rendu par **les mêmes composants** que les fiches
   natives (`front/src/modules/fiches/*`), sans aucun composant nouveau pour les blocs.
7. **Ranger** (§7). La question est posée avant de quitter la fiche.

## 3. Les entrées

| entrée | limites | extraction |
|---|---|---|
| photos | 1 à 5, JPEG/PNG/WebP (HEIC converti ?, voir Q3), 8 Mo chacune (comme le chat) | envoyées **telles quelles** au modèle (vision), comme les photos du chat |
| PDF | 1 fichier, 10 Mo, **20 pages** au plus | texte du PDF ; s'il n'a pas de texte (scan), voir Q2 |
| texte collé | 30 000 caractères au plus | tel quel |

- Le contenu réel est vérifié, pas seulement l'extension (`extension_reelle`, déjà utilisée par le
  chat). Un PDF protégé ou illisible est refusé avec un message clair.
- La source originale est gardée **tant que la fiche existe** (pour « voir mon document » et pour
  régénérer), dans les données privées de l'élève. Elle n'est jamais servie à un tiers. « Ne pas
  garder » la supprime.

## 4. Le rattachement à une notion

- Le modèle reçoit la **liste fermée** des notions du référentiel du niveau de l'élève (id, titre,
  matière, chapitre), jamais le référentiel entier en texte libre. Si l'élève a indiqué une
  matière, ses notions sont listées en premier.
- Il répond par un objet : `{notion: "<id>" | null, matiere: "<id>" | null, raison: "<1 phrase>"}`.
- **Le code vérifie** que l'id existe dans le référentiel. Un id inventé vaut `null`. Il ne
  « corrige » jamais au plus proche.
- `notion: null` : la question de rangement propose Non classé et les dossiers (décision 6).
- Si la matière détectée diffère de celle choisie par l'élève, on l'indique sans bloquer :
  « Ça ressemble à de l'histoire, pas à de la physique. » (C'est une faiblesse relevée chez DinoBot.)
- Une notion peut recevoir **plusieurs** fiches personnelles. La fiche native reste unique.

## 5. Le format et ses garde-fous

Une fiche personnelle est un fichier **au format des fiches visuelles**
(`bibliotheque/SCHEMA-FICHE-VISUELLE.md`), écrit selon la charte (`docs/FICHES-VISUELLES.md`) :
- mêmes types de blocs ;
- mêmes limites ;
- `**notions clés**`, `variables:`, `abreviations:`, bulle `jules:` ;
- SVG nettoyé par `jules/svg_sur.py` ;
- `graphe` seulement avec un gabarit d'extension active.

Le paquet de génération est **celui de `jules chantier visuel`** (même charte, même version
`fiche-visuelle/<empreinte>`), auquel s'ajoute la source de l'élève. On ne rédige pas de
deuxième prompt.

Écarts, **tous dans le code du validateur, jamais dans le format** :

| champ | fiche native | fiche personnelle |
|---|---|---|
| `notion` | obligatoire, dans le référentiel | dans le référentiel **ou absente** (Non classé, dossier) ; absente, pas de bloc `attendus` |
| `sources` | ≥ 1, url https et licence libre | exactement 1 : `{titre: "Mon document du 28/09", personnelle: <id source>}` ; pas d'url, pas de licence |
| `licence` | libre, obligatoire | `personnel` : jamais diffusée, jamais versée dans une bibliothèque du dépôt |
| `relecture` | `a_relire` / `relue` | toujours `a_relire` (pas de relecteur, décision 5) |
| `origine` | absent (= native) | `personnelle` : **seul champ ajouté**, lu par l'affichage pour la couleur et le filtre (§8) |

**Règle de fidélité** (voir §0 ; faiblesse relevée chez DinoBot) :
- Le contenu vient de la source. On reformule, structure et met en valeur ; on n'ajoute pas de
  notions absentes du document.
- La **carte**, la **méthode** et le **piège** peuvent être déduits de la source.
- Un **exemple** ou un **schéma** absent de la source est permis s'il illustre ce que dit la
  source ; la bulle `jules:` du bloc le signale alors (« Exemple ajouté par Jules »).
- **Q4 : faut-il un marquage plus visible que la bulle ?** Un champ `ajout: true` sur le bloc, par
  exemple, ferait un deuxième écart de format.
- Si la source est trop pauvre pour 3 blocs (le minimum du format), on ne génère pas : « Ton
  document est trop court pour une fiche ; ajoute une photo ou colle plus de texte. »

## 6. La bibliothèque personnelle (stockage)

- Elle vit dans les **données de l'élève** (`donnees/`, par profil), **jamais dans `bibliotheque/`**
  (qui est versionné et partageable).
- Une fiche = un fichier YAML (le format ci-dessus). Un index tenu par le module donne, pour
  chaque fiche : `{id, notion|null, dossier|null, etat: a_ranger|rangee, source, cree_le}`.
- Un dossier = `{id, nom}` (nom libre, 40 caractères). Non classé n'est pas un dossier stocké :
  c'est `notion = null` et `dossier = null` pour une fiche rangée.
- « Ranger dans la notion » : `notion` = la notion suggérée, `dossier` = null. « Ranger dans un
  dossier » : `dossier` renseigné ; la notion suggérée est **gardée si elle existe**, pour que la
  fiche apparaisse aussi dans la notion. **Q5 : ou le dossier seul ?**
- On peut ensuite déplacer une fiche, la renommer, supprimer une fiche (avec sa source),
  supprimer un dossier (ses fiches vont dans Non classé) ou régénérer une fiche.

## 7. « On garde cette fiche ? »

- La question est posée dès que l'élève quitte une fiche **à ranger** :
  - navigation interne ;
  - retour ;
  - clic dans la barre latérale.
- Les boutons :
  - **Oui, dans « <titre de la notion> »** (si notion trouvée, bouton principal) ;
  - **Oui, dans un dossier…** (liste des dossiers + « Nouveau dossier ») ;
  - **Oui, dans Non classé** (bouton principal si aucune notion) ;
  - **Non, ne pas garder**, toujours présent mais jamais en premier.
- Il n'y a pas d'autre choix. « Plus tard » n'existe pas ; fermer la question sans répondre
  revient à rester sur la fiche.
- **Fermeture brutale** (onglet fermé, coupure) : un navigateur ne permet pas de poser une question
  personnalisée à ce moment-là. La fiche reste **à ranger** et la question revient à la prochaine
  ouverture de Jules. Les fiches à ranger ne sont **pas** supprimées automatiquement. **Q6 : ou au
  bout de 7 jours ?**

## 8. L'affichage

- **« Mes fiches »** : une seule bibliothèque visible, natives et personnelles mêlées par matière
  et par notion, comme aujourd'hui.
- **Couleur** : une fiche personnelle porte l'accent **violet** de Jules (nouvelle variable CSS
  `--j-perso`, déclarée dans la config des matières, jamais en dur dans un composant) et une
  pastille « perso ». Cela vaut :
  - dans la barre latérale ;
  - sur les cartes de la bibliothèque ;
  - dans l'en-tête de la fiche.

  Les couleurs de matière restent celles de la matière.
- **Filtre**, sur la bibliothèque et la barre latérale : « Toutes · Fiches Jules · Mes fiches ».
  Il est mémorisé. Les libellés vont dans `config/`, pas dans les composants.
- **Section « Mes dossiers »** sous les matières : les dossiers de l'élève, puis Non classé (masqué
  s'il est vide).
- **Page d'une notion** qui a des fiches personnelles : la fiche native d'abord, puis « Mes fiches
  sur cette notion » (sélecteur d'onglets).
- **Entrée** : un bouton « + Ajouter mon cours » dans « Mes fiches ». Deux cartes sources,
  « Mes cours Jules » (natif, ce qui existe) et « Mon document » (photo, PDF, texte). On reprend
  le patron de DinoBot, pas son style.
- **Pendant la génération** (30 à 60 s) : la progression réelle par étape (lecture, notion,
  écriture, vérification), jamais une barre qui fait semblant.

## 9. API élève (module `sources`)

```
POST   /api/eleve/sources/deposer             multipart : photos[] | pdf | texte, matiere? -> {source, fiche?} ou erreur
GET    /api/eleve/sources/fiches              ?filtre=toutes|natives|perso -> index (notion, dossier, etat)
GET    /api/eleve/sources/fiches/<id>         fiche publique (même forme que /fiches_visuelles/notions/<id>)
POST   /api/eleve/sources/fiches/<id>/ranger  {mode: notion|dossier|non_classe, dossier?} ; ne pas garder = DELETE
DELETE /api/eleve/sources/fiches/<id>         supprime fiche et source
POST   /api/eleve/sources/fiches/<id>/regenerer
GET/POST/PATCH/DELETE /api/eleve/sources/dossiers
GET    /api/eleve/sources/a_ranger            fiches en attente de réponse (question au démarrage)
```

PATCH  /api/eleve/sources/fiches/<id>         {titre}
GET    /api/parent/sources/fiches             liste parent (lecture seule + suppression)
DELETE /api/parent/sources/fiches/<id>

La génération est **synchrone** (Q7) : la réponse de `deposer` est un flux NDJSON d'étapes
(`notion` → `ecriture` avec la suggestion → `verification` → `fin` avec la fiche, ou `erreur`).
Le front affiche ces étapes réelles, jamais une progression simulée.

## 10. Coût, parent, confidentialité

- **Coût** : une génération = 1 appel au modèle principal (plus 1 en cas de nouvel essai),
  réglé par le **même backend** que le reste (`llm:` de `config.yaml`). Un quota réglable
  `sources.generations_par_jour` (défaut 10) évite les dérapages. Le backend `demo` renvoie une
  fiche fixe pour tester sans IA.
- **Parent** (règle 3) : l'espace parent voit la liste des fiches personnelles (titre, notion,
  date) et **peut en supprimer**. L'événement de suivi est propre au module ; ce n'est **pas** un
  `suivi` de notion (même règle que le studio : une fiche générée ne dit rien de ce que l'élève
  sait).
- **Confidentialité** : les sources et les fiches personnelles ne sortent jamais de la machine
  sauf vers le modèle configuré, au moment de la génération. Elles ne sont ni journalisées en
  clair, ni exportées dans le chantier.

## 11. Tests (avant le code, avec le backend factice)

- L'id de notion inventé par le modèle est ramené à `null`, et la fiche est proposée dans Non
  classé.
- Une fiche générée non conforme est refusée ; exactement un nouvel essai a lieu, avec le motif.
- La fiche personnelle passe le validateur avec les écarts du §5 ; une fiche native, elle, doit
  toujours avoir url et licence (non-régression).
- Sur « ne pas garder », la fiche et la source sont supprimées. Supprimer un dossier envoie ses
  fiches dans Non classé.
- Le filtre natives/perso donne des listes disjointes.
- Le quota journalier est respecté. PDF trop long, image invalide, texte vide : message clair.
- Aucune fiche personnelle ne se trouve sous `bibliotheque/`. Rien n'apparaît dans `suivi`.

## 12. Qui touche quoi

- `jules/sources.py` (nouveau) : extraction, rattachement, appel du paquet, validation, stockage.
- `jules/fiches_visuelles.py` : **uniquement** le mode `personnelle` du validateur (§5), sans
  toucher au chemin des fiches natives.
- `jules/modules/sources.py` (nouveau) : routes §9, quota, événements parent.
- Front :
  - `front/src/modules/sources/*` (nouveau) : dépôt, progression, question de rangement,
    dossiers ;
  - `config/` : couleur perso et libellés du filtre ;
  - `Bibliotheque.tsx` et `Nav.tsx` : filtre et couleur, **via la config**.
- Tests : `tests/test_sources.py` (nouveau), plus la non-régression du validateur.

## Réponses d'Alex (28/09/2026)

- **Q0** : oui. Une fiche personnelle est une restitution du document, pas la production de l'élève.
- **Q1** : 5 photos au plus par source.
- **Q2** : un PDF sans texte (scanné) est converti en images de pages (`pypdfium2`), 20 pages au plus.
- **Q3** : les photos HEIC sont converties en JPEG (`pillow-heif`).
- **Q4** : la mention dans la bulle `jules:` suffit (« Exemple ajouté par Jules »). Pas de champ en plus.
- **Q5** : une fiche rangée dans un dossier garde sa notion suggérée ; elle apparaît aux deux endroits.
- **Q6** : les fiches à ranger ne sont jamais supprimées d'office.
- **Q7** : génération synchrone, étapes renvoyées en flux.
- **Q8** : quota de 10 générations par jour, réglable (`sources.generations_par_jour`).

Dépendances : `pypdfium2` (Apache-2.0/BSD-3) et `pillow-heif` (BSD-3), plus `Pillow` qu'elle tire
(MIT-CMU), déclarées dans l'extra `sources` de `pyproject.toml`. Sans elles, le module se replie :
PDF à texte seulement, pas de HEIC, avec un message clair.
