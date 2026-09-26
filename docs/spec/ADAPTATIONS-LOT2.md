# Spécification : adaptations (lot 2, leviers et aménagements)

Statut : **brouillon de structure**. Aucune valeur ne sera réglée pour un élève avant la relecture
par un professionnel (décision d'Alex du 26/09 : on prépare le terrain sans relecteur officiel).
Les valeurs chiffrées ci-dessous sont des **valeurs de départ sourcées**, marquées comme telles.

Base : `docs/spec/collecte-adaptations.md` au commit `a16e23a`, avec les corrections demandées
par REVIEWER (deuxième passe). Les lignes touchées par une correction en attente sont marquées
**[en attente collecte]**. Le lot 1 (`ADAPTATIONS.md`, EX-001 à EX-013) reste en vigueur.

## 1. Principes de lecture de la collecte

- Une valeur tirée d'une étude n'est reprise que si l'étude l'a isolée. Zorzi 2012 a augmenté
  **ensemble** l'espacement des lettres (+2,5 pt sur du 14 pt), celui des mots (triple) et
  l'interligne (double) : on en tire un **aménagement « texte aéré » qui règle les trois leviers
  ensemble**, pas une valeur isolée d'espacement des lettres.
- Marinus 2016 attribue le gain de la police Dyslexie à son espacement : c'est un argument pour
  le levier d'espacement et contre tout levier de police spéciale.
- Le fond coloré et la coloration syllabique relèvent de l'usage, sans preuve : ils sont
  proposés comme **préférence** du parent, jamais présentés comme une aide démontrée.
- Tout ce qui vient du guide BDA est « usage ». La règle BDA 2023 des 60 à 70 caractères porte
  sur la longueur des phrases, pas des lignes : la longueur de ligne s'appuie sur WCAG 1.4.8.

## 2. Leviers

Un levier a : un identifiant, un type, une valeur neutre (celle d'aujourd'hui), une plage
autorisée, une règle de combinaison, un canal (affichage CSS, consigne au modèle, comportement JS).

| Id | Canal | Neutre | Plage autorisée (départ sourcé) | Combinaison | Source |
|---|---|---|---|---|---|
| `espacement-lettres` | CSS | 0 | 0 à 0,18em (Zorzi : 2,5 pt / 14 pt) | max | étude |
| `espacement-mots` | CSS | 0 | 0 à 0,5em | max | étude (Zorzi, ×3) / usage (BDA) |
| `interligne` | CSS | actuel (1,55 ; bulles 1,45) | jusqu'à 2,0, jamais sous la valeur actuelle | max | norme WCAG 1.4.8 / usage BDA |
| `longueur-ligne` | CSS | actuelle | 60 à 80ch | min | norme WCAG 1.4.8 (≤ 80) |
| `taille-texte` | CSS | 1,125rem | 1 à 1,5 × la neutre | max | norme WCAG 1.4.4 / usage BDA |
| `police` | CSS | `--police-texte` | liste fermée de sans-serif, aucune police « spéciale » | arbitrage parent | étude (Wery 2017, Kuster 2018, Marinus 2016) |
| `fond` | CSS | blanc | blanc, crème, bleu pâle ; contraste ≥ 4,5:1 | arbitrage parent | norme WCAG 1.4.3 / préférence |
| `densite` | JS | tout affiché | tout / un exercice à la fois | le plus restrictif | usage (PAP) |
| `lecture-vocale` | JS | absente | absente / proposée (bouton) / automatique | voir §4 | usage (PAP) |
| `consignes-decoupees` | consigne + JS | non | non / oui | ou | usage (PAP) |
| `phrases-courtes` | consigne | non | non / oui (≤ 15 mots, départ FALC) | ou | usage (FALC) |
| `reperes-rang-chiffres` | CSS + outils | non | non / oui (unités, dizaines, centaines) | ou, conflit §4 | usage (PAP, libellé exact) |
| `surlignage-mots-cles` | consigne + CSS | non | non / oui | ou, conflit §4 | usage (PAP) |
| `temps-majore` | JS (modes épreuve, contrôle) | 1 | **[en attente collecte]** | max | droit, à re-sourcer |

Exclus du lot 2 : **coloration syllabique** (il faut un découpage syllabique fiable du
français : chantier à part, lot 3) et **dictée** (hors périmètre, lot 1).

## 3. Aménagements (ce que coche le parent)

Chaque aménagement porte le **libellé exact du PAP** (collecte §PAP) et un identifiant neutre.
Seuls les items sur lesquels un logiciel peut agir sont repris ; les autres (installation en
classe, tutorat, clé USB...) sont hors champ.

| Id | Libellé PAP affiché au parent | Leviers réglés |
|---|---|---|
| `supports-aeres-agrandis` | « Proposer des supports écrits aérés et agrandis » | espacement-lettres, espacement-mots, interligne, taille-texte, longueur-ligne |
| `lecture-oralisee` | « Proposer à l'élève une lecture oralisée [...] ou une écoute audio » | lecture-vocale = proposée |
| `consignes-decomposees` | « Décomposer les consignes et informations complexes » | consignes-decoupees, phrases-courtes |
| `reformulation` | « Aider à la compréhension par une explicitation ou une reformulation » | phrases-courtes |
| `diminuer-quantite-ecrit` | « Diminuer la quantité d'écrit sur chaque feuille » | densite = un exercice |
| `reperes-couleur-calcul` | « Présenter les calculs en colonnes avec des repères de couleur » | reperes-rang-chiffres |
| `surligner-mots-cles` | « Surligner des mots clés / passages importants » | surlignage-mots-cles |
| `temps-majore` | « Accorder un temps majoré » | temps-majore **[en attente collecte]** |

Préférences hors PAP (réglées par le parent sans aménagement) : `police`, `fond`,
`lecture-vocale = automatique`.

## 4. Conflits connus (montrés au parent, jamais tranchés en silence)

- `taille-texte` élevée avec `densite = un exercice` : peu de contenu visible. Les deux
  s'appliquent ; le parent voit un avertissement.
- `reperes-rang-chiffres` ou `surlignage-mots-cles` avec `densite = un exercice` : ajout
  d'information visuelle. Même traitement.
- `lecture-vocale = automatique` : peut gêner un élève en difficulté de compréhension orale.
  Jamais activée par un aménagement, seulement par choix explicite du parent.

## 5. Exigences

- **EX-101** — Chaque levier est déclaré une seule fois (fichier sous `adaptations/leviers/`)
  avec les champs du §2. *Vérification* : test qui charge tous les leviers et contrôle les
  champs, la valeur neutre dans la plage, et une règle de combinaison connue.
- **EX-102** — Avec tous les leviers à leur valeur neutre, le rendu est identique à
  aujourd'hui. *Vérification* : captures avant/après identiques (méthode d'EX-010).
- **EX-103** — Chaque aménagement est un fichier sous `adaptations/amenagements/` avec son
  identifiant, son libellé PAP exact et les valeurs de leviers ; il ne cite aucun terme de
  `termes-interdits.txt`. *Vérification* : test de chargement + test d'hygiène d'EX-008 ;
  chaque libellé est comparé à la liste PAP de la collecte.
- **EX-104** — La combinaison de plusieurs aménagements suit la règle de chaque levier, et
  tout conflit du §4 est renvoyé comme conflit. *Vérification* : test avec `test-cumul.yaml`
  (valeurs attendues calculées à la main) et un cas par conflit du §4.
- **EX-105** — Les leviers CSS s'appliquent par variables CSS sur `<body>` dans la page et
  par le message `adaptations` (EX-001 à 003) dans les outils. *Vérification* : test
  navigateur (EX-012) qui mesure les styles calculés dans la page et dans un outil.
- **EX-106** — Robustesse : aucun contenu n'est coupé ni ne se superpose, ni aux valeurs du
  test WCAG 1.4.12 (interligne 1,5 ; paragraphes 2× ; lettres 0,12em ; mots 0,16em), ni aux
  **valeurs maximales** des plages du §2, qui sont plus fortes. *Vérification* : test
  navigateur sur accueil, fiche, cours et un outil, détection de débordement.
- **EX-107** — Aucune police « spéciale dys » n'est proposée. *Vérification* : la liste
  fermée du levier `police` est comparée à une liste d'exclusion dans le test.
- **EX-108** — La page parent présente les aménagements avec leur libellé PAP, montre les
  conflits du §4 et n'affiche aucun nom de trouble. *Vérification* : test navigateur sur
  `parent.html` avec `test-cumul.yaml`.
- **EX-109** — Le bouton de lecture côté élève apparaît quand `lecture-vocale` vaut
  « proposée » ou « automatique » et qu'une voix locale existe (EX-006), sur chaque bulle de
  Jules et chaque consigne. *Vérification* : test navigateur, avec voix simulées.

## 6. Hors périmètre du lot 2

Coloration syllabique ; dictée ; temps majoré tant que sa source n'est pas corrigée ;
réglage fin des valeurs (attend un professionnel) ; activation du module `outils` dans
`config.yaml` (décision d'Alex).
