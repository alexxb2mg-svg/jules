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
  L'outil n'affiche son contenu qu'après avoir appliqué les leviers.
- **EX-002** — Délai. Sans réponse de l'hôte après 500 ms, l'outil s'affiche avec les
  valeurs neutres et envoie `{type: "adaptations-absentes"}` à l'hôte.
- **EX-003** — Contrôles. L'outil n'accepte `adaptations` que si
  `event.source === window.parent` ; il ignore sans erreur les leviers inconnus. L'hôte
  ignore tout message dont la source n'est pas l'iframe.
  *Vérification EX-001 à 003* : test automatisé couvrant réponse reçue, délai dépassé,
  message d'une autre source (des deux côtés), levier inconnu.

### Données de l'élève

- **EX-004** — Les identifiants d'aménagement ne sont jamais transmis au modèle de langue :
  ils sont retirés des champs libres du profil avant l'assemblage du prompt
  (`jules/composition.py`). *Vérification* : test qui assemble le prompt avec
  `profils/test-cumul.yaml` et vérifie qu'aucun identifiant d'aménagement n'y figure.
- **EX-005** — Le modèle ne reçoit que les consignes d'expression découlant des
  aménagements actifs (phrases courtes, découpage...), sans nom d'aménagement ni de trouble.
  *Vérification* : même test, qui vérifie la présence du bloc de consignes attendu et
  l'absence de toute liste de termes interdits (noms de troubles, identifiants).
- **EX-008** — Aucun fichier de données versionné (profils, aménagements, tests) ne contient
  un prénom réel ni un nom de trouble. La documentation n'est pas concernée.
  *Vérification* : test d'hygiène sur `profils/`, `adaptations/` et `tests/`.

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

### Prérequis techniques

- **EX-009** — La page hôte crée l'iframe d'outil et applique la vérification décrite dans
  `docs/OUTILS-CONTRAT.md` (section sécurité, « page hôte »). Prérequis d'EX-001.
- **EX-010** — Aucune taille de police n'est écrite en `px` dans les CSS de
  `jules/web/static/` : `rem` ou variables. Exceptions listées dans ce document si
  nécessaire. *Vérification* : grep sans résultat hors exceptions, et captures à 100 %
  identiques avant/après sur l'accueil, une fiche, le studio et le cours.

## 3. Hors périmètre du lot 1

- **Dictée vocale** : la reconnaissance vocale des navigateurs envoie la voix à un serveur
  tiers. Exclue tant qu'aucune solution locale n'est retenue.
- Valeurs des leviers, liste des aménagements, règles de combinaison : lot 2.
- Message propre à un navigateur dans la page parent : non validé tant que le comportement
  d'Edge en affichage normal n'est pas mesuré.

## 4. Questions ouvertes (décision d'Alex)

- Champ libre `remarques` du profil : continuer à le transmettre au modèle ? Proposition :
  oui, avec un avertissement sur la page parent.
- Relecture par un professionnel avant ou après le premier code du lot 2.

## 5. Risques

- L'appareil de l'élève n'est pas celui du développement (accès par le réseau local depuis
  une tablette) : les mesures faites sur la tour ne valent pas pour lui.
- La PR #40 en cours touche `jules/web/static/accueil.js` : pas de conflit avec EX-010 (CSS
  uniquement), mais EX-009 devra être ordonnée après sa fusion si elle touche le même JS.
