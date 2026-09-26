# Spécification : adaptations (lot 1, socle)

Statut : **brouillon**, à relire par un professionnel (orthophoniste, ergothérapeute) avant tout
réglage de valeur. Ce lot ne fixe aucune valeur de levier : il pose le transport, la protection
des données et les prérequis techniques. La liste des leviers viendra au lot 2, à partir de
`docs/spec/collecte-adaptations.md`.

Références : `docs/VISION.md` §5, `adaptations/README.md`, `docs/OUTILS-CONTRAT.md`.

## 1. Modèle en trois couches

- **Levier** : réglage atomique, mesurable, avec une valeur neutre (espacement, interligne,
  lecture vocale...). Liste fixée au lot 2.
- **Aménagement** : ce que le parent coche, calqué sur le vocabulaire du PAP. Un aménagement
  est un fichier qui donne des valeurs à des leviers.
- **Règle de combinaison** : chaque levier déclare comment se résout un conflit entre deux
  aménagements (max, min, désactivé, arbitrage parent). Un conflit est montré au parent,
  jamais tranché en silence.

Le profil ne stocke que des identifiants d'aménagements, jamais un nom de trouble.

## 2. Exigences du lot 1

### Transport vers les outils (iframe isolée)

- **EX-001** — Poignée de main. L'outil charge avec son contenu masqué et envoie
  `{type: "pret"}` à `window.parent`. L'hôte, après avoir vérifié
  `event.source === iframe.contentWindow`, répond `{type: "adaptations", leviers: {...}}`.
  L'outil n'affiche son contenu qu'après avoir appliqué les leviers. L'hôte répond à
  **chaque** `pret` reçu de l'iframe, pas seulement au premier : si l'iframe se recharge
  (même `contentWindow`), elle refait la poignée de main et reçoit de nouveau ses leviers.
- **EX-002** — Délai. Sans réponse de l'hôte après 500 ms, l'outil s'affiche avec les
  valeurs neutres et envoie `{type: "adaptations-absentes"}` à l'hôte. Un message
  `adaptations` valide reçu après ce délai est **appliqué** (mieux vaut un saut d'affichage
  qu'un élève privé de ses adaptations pour toute la séance).
- **EX-003** — Contrôles. L'outil n'accepte `adaptations` que si
  `event.source === window.parent` ; il ignore sans erreur les leviers inconnus. L'hôte
  ignore tout message dont la source n'est pas l'iframe.
  *Vérification EX-001 à 003* : test automatisé couvrant réponse reçue, délai dépassé,
  réponse reçue après le délai (appliquée), message d'une autre source (des deux côtés),
  levier inconnu, rechargement de l'iframe (deuxième `pret` → deuxième réponse).

### Données de l'élève

- **EX-004** — Les identifiants d'aménagement ne sont jamais transmis au modèle de langue :
  ils sont retirés des champs libres du profil avant l'assemblage du prompt
  (`jules/composition.py`). *Vérification* : test qui assemble le prompt avec
  `profils/test-cumul.yaml` et vérifie qu'aucun identifiant d'aménagement n'y figure.
- **EX-005** — Le modèle ne reçoit que les consignes d'expression découlant des
  aménagements actifs (phrases courtes, découpage...), réunies dans un bloc unique
  « Expression adaptée » sans titre par aménagement, sans nom d'aménagement ni de trouble.
  *Vérification* : même test, qui contrôle **uniquement les blocs issus des aménagements**
  (le prompt est construit sans contenu de leçon), vérifie la présence du bloc attendu et
  l'absence des termes listés dans `docs/spec/termes-interdits.txt` (noms de troubles) et
  des identifiants d'aménagement. La liste vit sous `docs/`, hors du champ d'EX-008.
  Elle appartient à la spec (le code testé ne la modifie pas) et ses règles de recherche,
  écrites en tête du fichier, sont obligatoires : insensible à la casse et aux accents,
  radicaux en sous-chaîne, sigles préfixés `mot:` en mot entier. Le test contient un
  cas témoin qui vérifie que « Dyslexique » et « DYSPRAXIE » sont bien détectés, ainsi que
  « déficiences visuelles », « déficit de l’attention » (apostrophe typographique) et
  « handicapé ». Le périmètre de la liste dépasse VISION §5 (autisme, surdité, cécité) :
  le « etc. » de VISION est lu au sens large.
- **EX-008** — Aucun fichier de données versionné (`.yaml`, `.yml`, `.json`, `.md` hors
  `README.md`) sous `profils/`, `adaptations/`, `consignes/` et `tests/` ne contient un nom
  de trouble ni le prénom d'un élève réel. Ne sont pas concernés : `docs/`, les `README.md`
  (documentation du périmètre), le code Python des tests, le contenu pédagogique
  (`bibliotheque/`, `extensions/` : ils ne sont pas dans le périmètre et y restent, un cours
  d'histoire peut parler de « personnes handicapées »), et les jeux de données qui
  testent justement le filtrage de ces termes, listés nommément ici :
  `tests/cas/modele_eleve/lecons_filtre.yaml`. Toute nouvelle exemption passe par la spec.
  *Vérification* : test d'hygiène en deux parties.
  (a) Noms de troubles : recherche insensible à la casse des termes de
  `docs/spec/termes-interdits.txt`.
  (b) Prénoms réels : si la surcouche privée est présente, le test lit le champ `prenom` des
  profils qu'elle contient et les cherche dans les trois dossiers ; sinon il est marqué
  « ignoré » avec la raison affichée, jamais « réussi ».
- **EX-011** — Le champ libre `remarques` reste transmis au modèle. Partout où ce champ
  est rédigé, un avertissement l'accompagne : il est lu par le moteur en ligne et ne doit
  contenir aucune information médicale. Aujourd'hui le champ n'existe que dans le YAML du
  profil (la page parent ne l'expose pas) : l'avertissement est un commentaire dans
  `profils/exemple.yaml` et dans le YAML généré par l'assistant d'installation. Si un jour
  la page parent expose ce champ, l'avertissement y est obligatoire.
  *Vérification* : test qui vérifie la présence de l'avertissement au-dessus ou sur la
  ligne de `remarques` dans `profils/exemple.yaml` et dans le YAML produit par
  `jules/installation.py`. Le libellé de l'avertissement ne contient aucun terme de
  `termes-interdits.txt` (sinon EX-008 échoue).

### Lecture vocale

- **EX-006** — La lecture vocale n'utilise que des voix `localService === true`, filtre sur
  cette propriété et jamais sur le nom. S'il n'y en a aucune, le bouton de lecture n'est pas
  affiché. La liste est relue à l'événement `voiceschanged`.
  *Vérification* : test automatisé avec `speechSynthesis.getVoices()` simulé, quatre cas :
  voix locales présentes ; uniquement des voix en ligne ; aucune voix ; liste vide puis
  remplie après `voiceschanged`. Le résultat ne doit pas dépendre de la machine.
  Vérification manuelle complémentaire (non bloquante) : script de relevé des voix, rejoué
  sur l'appareil réel de l'élève.
- **EX-007** — La page parent indique si la lecture vocale est disponible sur cet appareil,
  en constatant le résultat du filtre, sans nommer de navigateur.
  *Vérification* : les quatre cas simulés d'EX-006, en contrôlant le texte affiché sur la
  page parent (disponible / indisponible, et passage de l'un à l'autre après
  `voiceschanged`).

### Prérequis techniques

- **EX-009** — La page hôte crée l'iframe d'outil et applique la vérification décrite dans
  `docs/OUTILS-CONTRAT.md` (section sécurité, « page hôte »). Prérequis d'EX-001.
- **EX-010** — Aucune taille de police n'est écrite en `px` dans **tous** les CSS de
  `jules/web/static/`, y compris dans la forme raccourcie `font:` : `rem` ou variables.
  Exceptions listées dans ce document si nécessaire.
  *Vérification* : test qui parcourt tous les `*.css` du dossier (pas une liste fixe) et
  détecte `font-size: …px` et `font: … …px`, sans résultat hors exceptions ; captures à
  100 % identiques avant/après sur l'accueil, une fiche, le studio, le cours et une bulle
  d'aide des symboles.

- **EX-013** — Le filtre anti-diagnostic du carnet (`jules/apprentissage/carnet.py`) lit
  `docs/spec/termes-interdits.txt` **en plus** de ses propres termes, qu'il garde (il est
  volontairement plus large : vocabulaire de jugement, `dys` en sous-chaîne...).
  *Vérification* : assertion que chaque terme de la liste de la spec est refusé par le
  carnet ; `tests/cas/modele_eleve/lecons_filtre.yaml` relancé à l'identique, sans
  régression.

### Règle de preuve commune

- **EX-012** — Les tests qui ouvrent un navigateur (EX-001 à 003, EX-006, EX-007, EX-009)
  comptent seulement s'ils ont réellement tourné. *Vérification* : exécution avec
  `JULES_CHROMIUM` défini et `pytest -rs` ; zéro test de navigateur ignoré. Un test ignoré
  vaut un échec pour la revue.

### Source unique de la liste

- `docs/spec/termes-interdits.txt` n'a qu'une version qui fait foi : celle de la branche
  spec. Toute branche de code qui en porte une copie la garde **identique octet pour
  octet** au dernier commit de la spec ; la revue le vérifie par un diff vide.

## 3. Hors périmètre du lot 1

- **Dictée vocale** : la reconnaissance vocale des navigateurs envoie la voix à un serveur
  tiers. Exclue tant qu'aucune solution locale n'est retenue.
- Valeurs des leviers, liste des aménagements, règles de combinaison : lot 2.
- Emplacement du bouton de lecture côté élève : lot 2. Le lot 1 livre le module
  (`lecture-vocale.js`, EX-006/007) ; son branchement dans l'interface dépend du levier
  « lecture vocale » (proposée / automatique) et de l'aménagement qui l'active.
- Activation du module `outils` dans `config.yaml` (inactif aujourd'hui) : décision
  produit d'Alex, hors lot 1. Les tests d'EX-001 à 003 et 009 n'en dépendent pas.
- Exécution des tests de navigateur en CI (installer Chromium dans le workflow) : hors lot 1.
  EX-012 s'applique à la revue, sur la machine du relecteur.
- Message propre à un navigateur dans la page parent : non validé tant que le comportement
  d'Edge en affichage normal n'est pas mesuré.

## 4. Décisions d'Alex (26/09/2026)

- Champ `remarques` : transmis au modèle, avec avertissement (EX-011).
- Pas encore de relecteur professionnel officiel : la spec et le code avancent sur la base
  documentée (collecte sourcée, niveau de preuve par levier). Les valeurs du lot 2 restent
  marquées « à relire par un professionnel » jusqu'à ce qu'un relecteur les valide.

## 5. Risques

- L'appareil de l'élève n'est pas celui du développement (accès par le réseau local depuis
  une tablette) : les mesures faites sur la tour ne valent pas pour lui.
- PR #40 fusionnée dans `main` (`260adfe`) : plus de chevauchement avec EX-009.
