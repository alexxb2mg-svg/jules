# Licences

Ce dépôt mélange plusieurs types de contenus, sous des licences différentes.

## Code, consignes, persona

Sous licence **MIT** (texte complet : [LICENSE](LICENSE)) :

- le code (`jules/`, `tests/`, scripts) ;
- les consignes servies au modèle (`consignes/*.md`, `consignes/modes/*.md`,
  `consignes/amenagements/*.md`) ;
- la persona par défaut (`persona/jules/*.md`, `persona/jules/persona.yaml`, et toute persona
  ajoutée sur ce modèle), à l'exception de l'avatar (voir plus bas).

## Contenus de `bibliotheque/`

Chaque bibliothèque déclare sa propre licence dans son fichier `bibliotheque.yaml` (champ
`licence`). Ce champ fait foi ; à la date de cette page :

| Bibliothèque | Fichier | Licence |
|---|---|---|
| `bibliotheque/exemple-direction-enseignant/` | `bibliotheque.yaml:6` | MIT |
| `bibliotheque/fiches-3e-experimentales/` | `bibliotheque.yaml:6` | CC BY-SA 4.0 |
| `bibliotheque/fiches-cm1-experimentales/` | `bibliotheque.yaml:7` | CC BY-SA 4.0 |
| `bibliotheque/fiches-v2-demonstration/` | `bibliotheque.yaml:6` | CC BY-SA 4.0 |
| `bibliotheque/fiches-visuelles-3e-experimentales/` | `bibliotheque.yaml:6` | CC BY-SA 4.0 |
| `bibliotheque/lecons-3e-experimentales/` | `bibliotheque.yaml:6` | CC BY-SA 4.0 |
| `bibliotheque/programme/` | `bibliotheque.yaml:6` | Licence Ouverte etalab-2.0 (le résumé du programme officiel est ensuite publié sous la licence du dépôt, MIT) |

Une fiche cite en plus ses propres sources, avec leur licence (champ `sources` de chaque fiche,
voir [bibliotheque/README.md](bibliotheque/README.md)) : la plupart des fiches sont des
reformulations de contenus sous Licence Ouverte etalab-2.0 (ressources éduscol) ou sous licence
libre équivalente, redistribuées en CC BY-SA 4.0 par la bibliothèque qui les héberge.

## Logo, avatar, images

- `persona/jules/avatar.png` (avatar de la persona par défaut) ;
- `docs/jules-logo.png` ;
- les autres images de `docs/` (par exemple `docs/maquette-cours.png`).

**Licence à préciser par l'auteur.** Ces fichiers n'ont pas encore de licence explicite dans ce
dépôt. Proposition, à valider par le mainteneur : CC BY 4.0. Tant que ce point n'est pas tranché,
ne pas réutiliser ces images en dehors de ce projet sans demander à l'auteur.

## Voir aussi

[README.md](README.md#licence), [GOUVERNANCE.md](GOUVERNANCE.md) (ce qui n'est pas accepté en
matière de licence), [bibliotheque/README.md](bibliotheque/README.md) (règles pour publier une
bibliothèque).
