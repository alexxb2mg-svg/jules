# Leviers d'adaptation

Un fichier `<identifiant>.yaml` par levier : un réglage élémentaire de l'affichage, du comportement
ou de l'expression de Jules. Liste, valeurs et sources : `docs/spec/ADAPTATIONS-LOT2.md`, §2
(exigences EX-101 et EX-107). Format et validation : `jules/leviers.py` ; test :
`tests/test_leviers.py`.

Champs obligatoires : `id` (égal au nom du fichier), `canal` (`css`, `consigne`, `js`, `outils`,
un ou plusieurs), `type` (`nombre`, `choix`, `booleen`), `neutre`, `plage`, `combinaison`
(`max`, `min`, `ou`, `plus-restrictif`, `arbitrage-parent`) et `source` (`nature`, `reference`).
Un levier CSS porte aussi le nom de sa variable CSS (`variable_css`, préfixe `--adapt-`).

La valeur `neutre` est celle d'aujourd'hui : tant que tous les leviers sont neutres, Jules
s'affiche exactement comme avant (EX-102). Les valeurs de départ sont sourcées mais n'ont pas
encore été relues par un professionnel : aucune ne doit être réglée pour un élève avant cette
relecture.

Application (EX-105) : `/api/infos` expose `leviers` (identifiant -> valeur brute des leviers
réglés, non neutres ; même forme que le message `adaptations` envoyé aux outils) et `leviers_css`
(variables CSS `--adapt-*` dérivées de `leviers`, jamais l'inverse ; `jules/leviers.py`,
`leviers_resolus` et `leviers_css`). Les pages de l'élève posent ces variables et un attribut
`data-adapt-<levier>` sur `<body>` (`MS.appliquerLeviers`, `jules/web/static/adaptations.css`) ;
les outils reçoivent `leviers` par la poignée de main (`docs/OUTILS-CONTRAT.md`). Les valeurs
viendront de la combinaison des aménagements (EX-104, branchée à l'intégration du lot 2) : d'ici là,
tout est neutre.

Le levier `police` est une liste fermée de polices sans empattement ordinaires : aucune police
présentée comme « spéciale » n'y entre (EX-107, études citées dans `police.yaml`).
