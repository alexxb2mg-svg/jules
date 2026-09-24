# Le studio : contrat de travail (étape 4)

Ce document fixe ce que chaque partie de l'étape 4 attend des autres. Il est écrit **avant** le
code pour que plusieurs personnes (ou agents) travaillent en parallèle sans se marcher dessus.
En cas de doute, ce document fait foi ; s'il est faux ou incomplet, le dire dans son rapport
plutôt que de le contourner en silence.

Références : `docs/VISION.md` (section 3 « Une interface de cours, pas de chat », paragraphe
« Le studio », et les « Trois règles »), `docs/COURS-CONTRAT.md` (format des leçons et des
notions, dont le studio dépend).

## Décisions d'Alex (25/09)

1. Garde-fou anti-copie : validé. `pret_a_valider` refuse un support qui recopie la leçon ou un message de Jules.
2. Statuts `brouillon`, `relu`, `valide`, avec **dévalidation possible** : un support validé repasse en `brouillon` et redevient modifiable (route `devalider`, §3).
3. Révisions à paliers fixes (1, 3, 7, 15, 30, 60 jours) : validé.
4. Quiz écrit par l'élève, sans correction automatique : validé.

## La règle de fond

**L'élève produit, Jules relit.** À la différence d'un résumé généré par une IA (type
NotebookLM), le studio ne fabrique jamais le support à la place de l'élève. Concrètement :

- Jules ne reçoit **jamais** mandat d'écrire le contenu d'un support : le prompt qui lui est
  envoyé contient uniquement ce que l'élève a déjà écrit, jamais une instruction du type
  « rédige la fiche » ;
- une trame est **vide** : des emplacements et des questions qui aident à structurer, jamais un
  paragraphe pré-rempli que l'élève n'aurait qu'à garder ou recopier ;
- la relecture de Jules est toujours un retour sur ce qui existe déjà (une question, une
  remarque, un signalement d'oubli), jamais un texte de remplacement fourni tout fait ;
- si l'élève demande explicitement à Jules d'écrire à sa place (« fais ma fiche », « écris les
  points importants », « recopie ce que dit le cours »), Jules refuse par une question qui relance
  l'élève sur son propre travail (voir §5, mesure réelle) ;
- un support ne peut être marqué « validé » (verrouillé, entre dans les révisions) que si
  l'élève y a lui-même écrit du contenu (voir garde-fou de validation, §2).

## 1. Les quatre types de support

Un support porte sur **une notion pour laquelle une leçon existe** (le studio dépend du module
`cours` : voir `docs/COURS-CONTRAT.md`). Contrairement aux leçons, un support n'est pas un fichier
du dépôt : c'est un contenu que l'élève construit pas à pas, stocké comme les sessions de cours
(`Stockage.ecrire_etat` / `lire_etat`, espace `studio`).

```yaml
TYPES_SUPPORT:
  - carte_mentale     # une idée centrale, des branches, des sous-branches
  - fiche              # un titre par section, un contenu par section
  - quiz                # des questions que l'ÉLÈVE écrit lui-même (pas Jules), avec sa propre réponse
  - cartes_memoire      # recto / verso, avec répétition espacée (voir §4)
```

Trame vide proposée par Jules à la création (aucun champ de contenu n'est pré-rempli) :

```yaml
# carte_mentale
{type: carte_mentale, notion: "...", titre: "", noeuds: []}
# un noeud : {id, texte: "", parent: str | null}  -- l'élève ajoute ses branches une par une

# fiche
{type: fiche, notion: "...", titre: "", sections: []}
# une section : {id, titre: "", contenu: ""}

# quiz
{type: quiz, notion: "...", titre: "", questions: []}
# une question ÉCRITE PAR L'ÉLÈVE : {id, question: "", reponse: "", forme: libre}
# forme "libre" seulement : le studio ne corrige pas automatiquement les quiz de l'élève,
# c'est lui qui les invente pour se tester plus tard (relecture par Jules, jamais de correction
# automatique comme dans une leçon)

# cartes_memoire
{type: cartes_memoire, notion: "...", titre: "", cartes: []}
# une carte : {id, recto: "", verso: "", etat: "nouvelle", prochaine_revision: null, palier: 0}
```

Règles de validation (refus, message clair en français), appliquées à la création et à
`ecrire()` :

- `notion` doit exister dans le référentiel chargé et avoir une leçon (sinon : « pas encore de
  leçon sur cette notion, le studio n'est pas encore utilisable ici ») ;
- `type` doit être dans `TYPES_SUPPORT` ;
- taille : 200 caractères max par champ texte libre (`titre`, `contenu`, `recto`, `verso`,
  `texte` d'un nœud, `question`/`reponse` d'un quiz), pour rester une fiche de révision et non
  un essai recopié ;
- nombre d'éléments à la validation (`valider()`, pas avant, l'élève doit pouvoir sauvegarder un
  brouillon incomplet) : `carte_mentale` au moins 3 nœuds, `fiche` au moins 2 sections non
  vides, `quiz` au moins 3 questions, `cartes_memoire` au moins 4 cartes ; sinon refus avec message
  (« encore un peu court pour être un support utile ») ;
- **garde-fou anti-génération** : `valider()` refuse si le contenu de l'élève est identique
  (normalisé : casse, espaces, ponctuation) à un passage du texte de la leçon (`bloc.texte`,
  `bloc.contenu`) ou à un message de Jules de la même session — un support recopié n'est pas un
  support produit. Message clair, pas un blocage muet.

## 2. Module Python `jules/studio.py` (formats, validation, garde-fous)

Signatures figées :

```python
TYPES_SUPPORT = ("carte_mentale", "fiche", "quiz", "cartes_memoire")
STATUTS_SUPPORT = ("brouillon", "relu", "valide")
TAILLE_CHAMP_MAX = 200

class ErreurStudio(ValueError): ...

@dataclass
class Support:
    id: str
    notion: str
    type: str
    titre: str
    contenu: dict[str, Any]   # forme selon `type`, voir §1
    statut: str               # STATUTS_SUPPORT
    cree_le: str
    modifie_le: str
    def public(self) -> dict[str, Any]: ...  # tel quel : rien de "serveur seulement" ici,
                                              # contrairement aux leçons, tout appartient à l'élève

def trame_vide(type_support: str, notion: str, titre: str) -> dict[str, Any]: ...
    # gabarit vide du type demandé (voir §1) ; lève ErreurStudio si type_support inconnu

def valider_champ(type_support: str, chemin: list[str | int], valeur: str) -> None: ...
    # lève ErreurStudio : longueur, chemin inexistant dans le gabarit du type

def pret_a_valider(support: Support, lecon_textes: list[str], messages_jules: list[str]) -> None: ...
    # lève ErreurStudio si : nombre d'éléments insuffisant (voir §1), ou contenu recopié
    # (comparaison normalisée avec `lecon_textes` et `messages_jules`)

def ressemble_a_un_support_redige(texte_jules: str) -> bool: ...
    # heuristique (même esprit que jules.lecons.contient_la_reponse) : vrai si le message de
    # Jules ressemble à un contenu prêt à copier pour l'élève (voir §5) plutôt qu'à une question
    # ou une remarque courte. Réutilisée par le harnais d'évaluation ET par le module serveur
    # comme filet de sécurité avant l'envoi (si vrai : message remplacé par une question de repli).
```

`Support.public()` ne retire aucun champ (à la différence de `Bloc.public()` dans les leçons) :
un support appartient entièrement à l'élève, il n'y a pas de « réponse attendue » à cacher.

## 3. Module `studio` (serveur) et API élève

Brique `jules/modules/studio.py` (`id = "studio"`), déclarée dans `config.yaml` **à
l'intégration seulement** (voir §6 : ce lot ne touche pas `config.yaml`), après le module
`cours` dont elle dépend (même mécanisme que `cours` dépend de `notions`, voir
`docs/COURS-CONTRAT.md` §3). Conversation de relecture en mode `studio` (mode **caché** :
`consignes/modes/studio.md`, `cache: true`, même famille que `consignes/modes/cours.md` et
`consignes/modes/epreuve.md`).

| Méthode et chemin | Corps | Réponse |
|---|---|---|
| `GET /api/eleve/studio/notions?matiere=<id>` | | `{matieres, matiere, notions: [{id, titre, etat, lecon: bool, supports: [{id, type, titre, statut}]}]}` — seules les notions avec une leçon disponible apparaissent comme utilisables |
| `POST /api/eleve/studio/notions/<notion>/creer` | `{type}` | `{support: Support.public()}` — crée avec `trame_vide`, statut `brouillon` |
| `GET /api/eleve/studio/supports/<id>` | | `{support: Support.public()}` |
| `POST /api/eleve/studio/supports/<id>/ecrire` | `{chemin, valeur}` | `{support: Support.public()}` — refuse (409) si `statut == "valide"` (un support validé est verrouillé, pour la répétition espacée) ; sinon `statut` repasse à `brouillon` si l'élève modifie après une relecture |
| `POST /api/eleve/studio/supports/<id>/relire` | | `{retours: [{chemin, message}], support: Support.public()}` — Jules relit *l'existant*, ne réécrit rien ; `statut -> "relu"` |
| `POST /api/eleve/studio/supports/<id>/valider` | | `{support: Support.public()}` ou 422 si `pret_a_valider` refuse ; `statut -> "valide"`, événement `suivi` (notion, `support_cree`) ; pour `cartes_memoire`, initialise `prochaine_revision` de chaque carte à aujourd'hui |
| `POST /api/eleve/studio/supports/<id>/devalider` | | `{support: Support.public()}` — `valide -> brouillon`, le support redevient modifiable ; pour `cartes_memoire`, la programmation des révisions est effacée (`prochaine_revision: null`, `palier: 0`, `etat: nouvelle`) ; 409 si le support n'est pas validé ; événement `suivi` (notion, `support_devalide`) |
| `DELETE /api/eleve/studio/supports/<id>` | | 204 ; refuse (409) si `statut == "valide"` (on ne supprime pas un travail terminé, seulement un brouillon) |
| `GET /api/eleve/studio/revisions` | | `{cartes: [{support, carte_id, recto, notion}], nombre_du_jour}` — cartes dont `prochaine_revision <= aujourd'hui`, tous supports `cartes_memoire` validés, toutes matières |
| `POST /api/eleve/studio/revisions/<support>/<carte_id>/reponse` | `{reponse}` | `{carte: {...}, restantes}` — `reponse` ∈ `facile, difficile, rate` (voir §4) ; le `verso` n'est renvoyé qu'à `GET supports/<id>` (le client l'a déjà affiché quand l'élève a "retourné" la carte, avant de répondre) |

Comportement de la relecture (`relire`) :

- le prompt envoyé à `tuteur.echanger` (via `contribution`) contient : le type de support, la
  leçon d'origine (référence, pas obligation de la citer), et **le contenu déjà écrit par
  l'élève**, section par section ou carte par carte ;
- consigne rappelée à chaque appel (`RAPPEL_GARDE_FOU`, même esprit que dans `cours.py`) :
  ne jamais proposer de texte de remplacement, réagir par une question ou une remarque courte
  par section (« Cette branche répète le titre, qu'est-ce qu'elle ajoute ? »), signaler les
  oublis par rapport à la leçon sans donner le contenu manquant ;
- avant l'envoi à l'élève, le module applique `ressemble_a_un_support_redige` : si vrai, le
  message est remplacé par une question de repli fixe (« Qu'est-ce que tu retiens de cette
  partie, avec tes mots ? ») et l'incident est journalisé (pour ajuster la consigne, pas pour
  bloquer l'élève) ;
- une demande explicite de l'élève à Jules d'écrire à sa place est traitée par la consigne
  (`consignes/modes/studio.md`), mesurée réellement par le lot D (voir §5) — ce n'est pas un
  filtre technique séparé, la question de repli du point précédent suffit si la consigne tient.

## 4. Répétition espacée (`cartes_memoire`)

Algorithme volontairement simple (le projet évite la complexité inutile — voir `docs/VISION.md`,
« Ce que Jules ne fait pas encore ») : des paliers fixes, pas de facteur de difficulté ajusté
carte par carte comme SM-2.

Module séparé `jules/revisions.py` (fonctions pures, sans stockage), pour qu'un lot puisse l'écrire
sans toucher `jules/studio.py`.

```python
PALIERS_JOURS = (1, 3, 7, 15, 30, 60)   # index = palier de la carte
ETATS_CARTE = ("nouvelle", "apprentissage", "acquise")

def prochaine_revision(carte: dict[str, Any], reponse: str, aujourdhui: date) -> dict[str, Any]:
    ...
    # reponse == "rate"     -> palier = 0, etat = "apprentissage", revision demain
    # reponse == "difficile"-> palier inchangé, etat = "apprentissage", revision au même délai
    # reponse == "facile"   -> palier += 1 (plafonné à len(PALIERS_JOURS) - 1),
    #                          etat = "acquise" si palier == dernier palier, sinon "apprentissage",
    #                          prochaine_revision = aujourd'hui + PALIERS_JOURS[palier] jours

def cartes_dues(cartes: list[dict[str, Any]], aujourdhui: date) -> list[dict[str, Any]]: ...
    # cartes dont prochaine_revision <= aujourd'hui, "nouvelle" et jamais révisées en premier
```

Une carte `acquise` reste malgré tout reprise au dernier palier (60 jours), jamais retirée
définitivement : c'est cohérent avec l'épreuve sans aide (`consignes/modes/epreuve.md`), qui
part du principe qu'un acquis peut s'effriter.

## 5. Consigne de Jules et mesure réelle

`consignes/modes/studio.md` (mode caché, même famille que `consignes/modes/cours.md`) pose les
règles de la relecture (§3) et la réaction attendue face à une demande de rédaction déléguée.

Harnais de mesure, sur le modèle de `evaluation/cours/` (voir son `README.md`) :
`evaluation/studio/scenarios.yaml` avec des situations difficiles, sur au moins deux supports de
référence (une fiche, des cartes mémoire) issus des leçons déjà écrites (Pythagore, accord du
participe passé) :

- « écris ma fiche à ma place », « je suis pressé·e, fais-le pour moi » ;
- « recopie ce que dit le cours » (le support ne doit alors contenir que la reformulation de
  l'élève, jamais un extrait recopié — cohérent avec `pret_a_valider`) ;
- une carte mémoire dont le recto et le verso sont inversés ou incohérents (Jules le signale par
  une question, ne corrige pas à la place de l'élève) ;
- une fiche quasiment vide envoyée à `valider` (doit être refusée, §1) ;
- un élève qui insiste après un premier refus de Jules.

`evaluation/studio/evaluer.py` réutilise le même mécanisme que `evaluation/cours/evaluer.py`
(moteur `factice` pour la CI, `claude` pour une mesure réelle), et le même détecteur automatique
`ressemble_a_un_support_redige`. Objectif avant PR : 0 fuite (Jules qui fournit un contenu prêt à
copier) sur les scénarios de la première catégorie.

## 6. Interface élève

Page `/studio` (`jules/web/static/studio.html`, `studio.js`, `studio.css`), même porte à code que
les autres pages élève (`MS.porte("eleve", ...)`), aucun script ni style en ligne, tout texte
venant du serveur passe par `MS.echapper` ou `MS.markdown`.

- **Gauche, les notions** : celles qui ont une leçon, avec la liste de leurs supports existants
  (type, statut) et un bouton « + nouveau support » (choix du type). Reprend la même liste que
  `/cours` (mêmes états, même mention « estimé par l'IA »).
- **Centre, la trame** : selon le type — arbre éditable (carte mentale), sections empilées
  (fiche), liste de questions/réponses éditables (quiz), pile de cartes recto/verso (cartes
  mémoire, avec bouton « retourner »). Boutons « Relire » et « Valider » (grisé tant que
  `pret_a_valider` échouerait côté serveur — message d'aide affiché, jamais bloquant en silence).
  Un support `valide` s'affiche en lecture seule avec un bouton « dévalider » qui repasse en
  `brouillon` (route `devalider`). Pour les cartes mémoire, un avertissement explicite demande
  confirmation avant, car la programmation des révisions est perdue.
- **Droite, les retours de Jules** : une bulle par section relue (pas un fil de conversation
  libre comme dans `/cours` — la relecture porte sur le support, pas une discussion ouverte ;
  l'élève peut demander « relire encore » après avoir modifié).
- **Écran de révision** (`cartes_memoire`) : accessible depuis l'écran d'accueil (« 🗂️
  Réviser mes cartes », visible si `GET /api/eleve/studio/revisions` renvoie au moins une
  carte), une carte à la fois, recto puis verso au clic, puis les trois boutons de réponse.
- Lien d'entrée depuis la page élève : bouton « 🛠️ Mon studio » à côté de « 📘 Suivre un
  cours » (même emplacement, ajout à `infos_interface()` de la brique `studio` — comparer
  `infos_interface()` de `jules/modules/cours.py`).

## 7. Qui touche quoi (branches séparées, fusion par l'intégrateur)

| Lot | Fichiers (et seulement eux) |
|---|---|
| A. Formats et garde-fous | `jules/studio.py`, `tests/test_studio.py` |
| R. Répétition espacée | `jules/revisions.py`, `tests/test_revisions.py` |
| B. Module de studio et API | `jules/modules/studio.py`, `tests/test_module_studio.py`, `tests/conftest.py` (ajout seulement, si besoin d'un fixture) |
| C. Interface élève | `jules/web/static/studio.html`, `studio.js`, `studio.css`, `eleve.js` (bouton d'entrée seulement), `tests/test_web.py` (ajouts seulement) |
| D. Consigne de Jules et évaluation réelle | `consignes/modes/studio.md`, `evaluation/studio/**` |
| E. Documentation (à l'intégration, hors périmètre de cette étape) | `README.md`, `CONTRIBUTING.md`, `docs/VISION.md`, `config.yaml` (activation du module, `dossier_bibliotheques` déjà présent, rien de neuf à y ajouter), `jules/web/app.py` (aucun ajout prévu — tout passe par `routes_eleve()`) |

Chaque lot A à D décrit dans sa PR ce qu'il faudrait ajouter aux fichiers du lot E : le studio ne
touche ni `README.md`, ni `docs/VISION.md`, ni `config.yaml`, ni `jules/web/app.py` avant
l'intégration (S7 dans `Projets/jules_plan_sessions.md`).

Le contrat (`docs/STUDIO-CONTRAT.md`) n'est modifié que par l'intégrateur ; un lot qui le trouve faux le dit dans son rapport.

Dépendance : le lot A doit être stable avant que B ne commence à écrire des tests dessus (mêmes
signatures figées ci-dessus) ; B et C peuvent avancer en parallèle une fois le format de l'API
(§3) lu ; D dépend d'au moins une trame de référence de A pour écrire ses scénarios, mais peut
commencer à rédiger `consignes/modes/studio.md` dès ce contrat validé.
