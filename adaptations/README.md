# Adaptations

Socle construit, contenus expérimentaux : les valeurs de départ sont sourcées mais n'ont pas encore été relues par un professionnel.

| Dossier | Contenu |
|---|---|
| [`leviers/`](leviers/README.md) | 13 réglages élémentaires de l'affichage, du comportement ou de l'expression de Jules (police, fond, interligne, espacements, taille du texte, longueur de ligne, surlignage des mots clés, repères de rang des chiffres, phrases courtes, consignes découpées, lecture vocale, densité) |
| [`amenagements/`](amenagements/README.md) | 7 aménagements du PAP (modèle officiel, circulaire 2015-016), avec leurs libellés par niveau et la valeur qu'ils donnent à chaque levier |

Le parent coche les aménagements et ses préférences dans l'espace parent ; les conflits entre aménagements lui sont montrés, jamais tranchés en silence. Tant que rien n'est coché, tous les leviers sont neutres et Jules s'affiche comme avant. Spécifications : `docs/spec/ADAPTATIONS.md` (lot 1) et `docs/spec/ADAPTATIONS-LOT2.md` (lot 2) ; reste à faire : `docs/spec/LOT3-A-TRAITER.md`.

Ce dossier accueille les **adaptations** : des briques qui changent l'affichage de Jules et sa façon de s'exprimer selon les besoins particuliers d'un élève. Les troubles dys (dyslexie, dysorthographie, dyscalculie, dyspraxie, dysgraphie, dysphasie...) en sont le cœur, mais le champ est plus large : troubles de l'attention, déficience visuelle ou auditive, etc.

Chaque trouble a ses propres besoins, parfois opposés d'un trouble à l'autre, et un même élève peut en avoir plusieurs. C'est un pan entier du projet. Il se construit avec des orthophonistes, des ergothérapeutes, des enseignants spécialisés et des familles concernées, et n'est pas deviné par des développeurs : aucune valeur ne doit être réglée pour un élève avant leur relecture.

Principes déjà posés :

- une adaptation par besoin, et plusieurs adaptations peuvent se combiner chez un même élève ;
- les besoins sont indiqués par le parent : Jules ne pose jamais de diagnostic, et aucun nom de trouble n'est enregistré ni envoyé au modèle ;
- une adaptation s'applique à toute l'interface, y compris aux outils des matières.

Pour participer à la réflexion, voir [docs/VISION.md](../docs/VISION.md#5-une-interface-qui-sadapte-à-lélève) et ouvrir une discussion sur le dépôt.
