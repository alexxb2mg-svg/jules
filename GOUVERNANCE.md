# Gouvernance

## Qui décide

Jules a aujourd'hui un mainteneur unique : Alex Baillon, compte GitHub
[alexxb2mg-svg](https://github.com/alexxb2mg-svg). Toutes les décisions (acceptation d'une
contribution, publication d'une version, retrait d'une extension ou d'une fiche) passent par lui.
S'il y a un jour plusieurs mainteneurs, ce document sera mis à jour en conséquence.

## Comment une décision est prise

- Les changements de code, de contenu ou de documentation passent par une pull request sur
  [github.com/alexxb2mg-svg/jules](https://github.com/alexxb2mg-svg/jules). Le mainteneur relit et
  décide de fusionner, de demander des changements, ou de refuser en expliquant pourquoi.
- Les désaccords ou les idées qui changent la direction du projet se discutent dans une
  [Discussion GitHub](https://github.com/alexxb2mg-svg/jules/discussions) ou une issue « Idée »
  avant d'être codées, pour éviter le travail jeté.
- En cas de doute sur une règle du projet (pédagogie, sécurité, licence), c'est le document de
  référence concerné (`docs/VISION.md`, `SECURITY.md`, `LICENCES.md`, ce document) qui fait foi ;
  s'il est muet ou ambigu, le mainteneur tranche et met le document à jour.

## Relecture d'une fiche v2

Le contrat complet des fiches v2 est dans [docs/FICHES-V2.md](docs/FICHES-V2.md). Le champ
`relecture` d'une fiche (`bibliotheque/<id>/fiches/<matiere>/<notion>.yaml`) porte trois
informations : `statut`, `par`, `le`. Le circuit :

1. **`generee`** : la fiche est écrite (par un contributeur ou par un modèle), pas encore passée
   au vérificateur. Elle n'est jamais servie sans IA.
2. **`verifiee`** : `jules fiches verifier` n'a trouvé aucun défaut, puis `jules fiches signer` a
   scellé la fiche (une empreinte est écrite dans `empreinte`). C'est un contrôle automatique,
   pas une relecture humaine : la fiche est servie, marquée expérimentale.
3. **`relue`** : un enseignant identifié a relu le contenu et l'a jugé correct. Il l'indique en
   remplissant `relecture.par` (par exemple « professeur de mathématiques ») et `relecture.le`
   (la date) dans le fichier YAML de la fiche, puis en passant `relecture.statut` à `relue`. Si le
   contenu change après cette relecture, `jules fiches signer` doit resceller la fiche et la
   relecture est à refaire : elle portait sur l'ancien contenu.

Une fiche v1 (`bibliotheque/<id>/fiches/<matiere>/<id-de-notion>.yaml`, sans `format: 2`) suit le
même principe avec un `relecture` plus simple : `statut` vaut `a_relire` ou `relue`, `par` et `le`
une fois relue (voir [bibliotheque/README.md](bibliotheque/README.md)).

## Retrait d'une extension ou d'une fiche

Le mainteneur peut retirer une extension (`extensions/<id>/`), un outil (`outils/<id>/`) ou une
fiche déjà publiée, notamment si elle est jugée non conforme à la 1ʳᵉ règle du projet (« Jules ne
donne jamais la réponse »), non sourcée, ou si elle pose un problème de sécurité ou de licence.

- Le retrait est annoncé par une issue GitHub qui explique le motif, et repris dans la note de
  version (`CHANGELOG` ou description de la prochaine release) qui suit le retrait.
- Un retrait pour raison de sécurité peut être immédiat (avant l'annonce) si l'attente ferait
  courir un risque ; l'annonce suit alors dans les meilleurs délais.
- Une extension ou une fiche retirée reste dans l'historique git, mais n'est plus chargée par
  défaut : retirer son identifiant de `config.yaml` (extensions) ou du dossier `bibliotheque/`
  concerné (fiches) suffit à l'écarter.

## Ce qui ne sera pas accepté

- Un contenu (fiche, exercice, indice, relance) qui donne la réponse attendue avant que l'élève
  ait cherché, ou qui la rend devinable presque sans effort.
- Un outil ou une extension qui fait un appel réseau, même vers un service jugé de confiance : le
  contrat technique (`docs/OUTILS-CONTRAT.md`) l'interdit par construction (iframe isolée, CSP
  sans `connect-src`).
- Un contenu de fiche sans source, ou dont la source n'est pas sous une licence libre compatible
  (voir [bibliotheque/README.md](bibliotheque/README.md), section « Règles pour publier une
  bibliothèque »).
- Des données d'élève réelles : prénom, conversation, photo, bilan. Voir
  [CONTRIBUTING.md](CONTRIBUTING.md), règle 3.
