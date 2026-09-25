# Sources des fiches CM1 expérimentales

DONNÉES D'EXPÉRIMENTATION. Règle de cette bibliothèque : **sources officielles uniquement**.

## Admises
Ressources du ministère de l'Éducation nationale publiées sur eduscol.education.gouv.fr ou education.gouv.fr.
Le pied de page d'éduscol indique : « Sauf cas particuliers indiqués dans les mentions légales, les contenus de ce site sont sous licence etalab-2.0 » (vérifié le 24/09/2026 sur les pages d'accompagnement du cycle 3).
La Licence Ouverte etalab-2.0 permet la réutilisation, y compris commerciale et sous une autre licence, à condition de citer la source et la date de mise à jour.

- Programmes officiels du cycle 3 applicables en CM1 en 2026-2027 (liste et BO dans `../programme/CM1/*.yaml`).
- Ressources d'accompagnement éduscol : exemples de réussite CM1 (français, mathématiques), guide de la résolution de problèmes, guide de la lecture et de la compréhension, guide de la grammaire, terminologie grammaticale, livret EMC CM1, attendus de fin d'année d'anglais CM1, exemples en langues vivantes au cours moyen, repères d'éducation musicale et d'arts plastiques du cycle 3, supports cartographiques d'histoire-géographie des cycles 2-3 (2026).

Chaque fiche liste ses sources (titre, URL du PDF, licence, date de consultation, pages). L'outil de vérification des lots contrôle que chaque fiche est ancrée dans ces pages par des citations recopiées mot pour mot.

## Écartées
- Wikipédia, Vikidia, Wikiversité, Lumni, manuels scolaires, sites d'enseignants : pas des sources officielles.
- Ressources éduscol marquées © Réseau Canopé ou éditées par un tiers privé.
- Le guide du professeur des évaluations nationales « Repères CM1 » : il sert à évaluer, pas à enseigner.

## Ce que les fiches ne contiennent pas encore
- Histoire (14 notions) : le programme 2026 est neuf et éduscol n'a publié aucune ressource d'accompagnement pour le CM1 au 24/09/2026. Les fiches s'en tiennent au texte du programme (champ `couverture`).
- Sciences et technologie (16 notions) : même situation. Le vadémécum sciences de 2023 accompagne l'ancien programme ; il est écarté.
- Arts plastiques et histoire des arts : le programme ne nomme aucune œuvre, donc les fiches n'en citent aucune.

## Vérifications faites (24/09/2026)
- Chaque fiche est ancrée dans ses sources par au moins deux citations recopiées mot pour mot, à la bonne page du PDF officiel (outil `verif_lot.py`, hors dépôt).
- Calculs des exercices de mathématiques recontrôlés.
- Détection : 642 phrases d'élève inventées (2 à 4 par notion, sans nommer la notion) ; la bonne notion figure à chaque fois dans la liste envoyée au modèle.
