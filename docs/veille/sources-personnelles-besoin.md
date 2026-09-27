# Entrée de nouvelles sources : le besoin (Alex, 28/09/2026)

Note de cadrage, pas encore un contrat. À confronter à l'étude DinoBot avant d'écrire `SOURCES-CONTRAT.md`.

## Deux familles de sources

1. **Natives** : notre collecte documentaire. Elle alimente la restitution native (252 fiches visuelles, leçons, fiches v2).
2. **Personnelles** : apportées par l'élève. Exemple : Ellie photographie son exercice, son cours, son chapitre, comme dans DinoBot (lui-même inspiré de NotebookLM).

## Ce que l'outil fait d'une source personnelle

- Il **génère de nouvelles fiches**, uniquement dans le format déjà décidé (schéma des fiches visuelles). Aucun nouveau format.
- Les fiches vont dans une **bibliothèque personnelle**.
- Chaque fiche **rejoint la notion** à laquelle elle se rapporte. C'est **le LLM qui choisit** cette notion.
- Dans la barre latérale, une fiche **personnelle a une autre couleur** qu'une fiche native.
- Un **filtre** permet d'afficher les natives et les personnelles séparément.

## Décisions d'Alex (28/09/2026, après l'étude DinoBot)

1. **Entrées** : photo, PDF **et** texte collé.
2. **Validation** : pas de validation formelle, ni par Ellie ni par le parent. Mais **avant de quitter**
   l'écran de la fiche générée, une question lui demande **si on la garde**. Si oui, elle la range :
   - soit **dans la notion suggérée** par le LLM ;
   - soit **dans un dossier personnalisé** (qu'elle crée ou choisit).
   Si non, la fiche est abandonnée.
3. **Aucune notion trouvée** : la fiche va dans **« Non classé »**, avec la possibilité de la ranger
   directement dans un dossier personnalisé.

## Questions encore ouvertes

- Lecture des photos (OCR) : sur la machine ou par le modèle ?
- Garde-fous : même schéma, même validation que les fiches natives (`jules/fiches/…`) ; que faire si la notion est hors référentiel ?
- Une source peut-elle produire plusieurs fiches ou enrichir une fiche existante ?
