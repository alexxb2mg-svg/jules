# Adaptations : points reportés au lot 3

Points non bloquants relevés pendant le lot 2 (spec figée au tag `spec-lot2-fige`).

- **Polices écrites en dur hors `--police-texte`** : formules en Cambria (`accueil.css`, section des
  formules) et code en `ui-monospace` (PR #43, `.bloc-schema`). Le levier `police` n'agit que sur
  `--police-texte` et ne les touche donc pas. À décider : exceptions nommées (formules et code gardent
  leur police) ou variables dédiées (`--police-formule`, `--police-code`). Les leviers d'espacement et
  de taille s'y appliquent déjà.
- **Liste des termes interdits hors dépôt** : sans `docs/` (installation non éditable), le carnet
  refuse toutes les leçons. Embarquer la liste dans le paquet le jour où Jules s'installe autrement
  que depuis le dépôt.
- **Temps majoré** : plage en attente d'une source juridique correcte (D351-27 = examens seulement).
- **Coloration syllabique** : demande un découpage syllabique fiable du français.
