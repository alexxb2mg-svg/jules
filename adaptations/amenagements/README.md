# Aménagements

Un fichier `<identifiant>.yaml` par aménagement : un item du PAP (modèle officiel, circulaire
2015-016) que coche le parent et sur lequel un logiciel peut agir. Liste et règles :
`docs/spec/ADAPTATIONS-LOT2.md`, §3 (exigence EX-103). Format et validation :
`jules/amenagements.py` ; test : `tests/test_amenagements.py`.

Champs : `id` (égal au nom du fichier), `libelles` (par niveau : `maternelle`, `elementaire`,
`college`, `lycee`, chacun `{page, texte}`) et `leviers` (valeur donnée à chaque levier de
`adaptations/leviers/`).

Les libellés sont recopiés en entier depuis `docs/spec/pap-libelles.txt` (texte affiché du PDF
officiel, espaces irrégulières comprises) ; le test les compare caractère pour caractère. Un niveau
sans libellé est affiché sous la rubrique du PAP « Autres aménagements et adaptations », avec la
mention « à inscrire par l'équipe éducative » ; la maternelle n'a pas cette rubrique.

Un aménagement ne règle jamais `police` ni `fond` (préférences du parent) et ne met jamais la
lecture vocale en automatique (choix explicite du parent, §4). Les valeurs de leviers sont des
valeurs de départ sourcées, à relire par un professionnel avant tout réglage pour un élève.
`temps-majore` est reporté au lot 3.
