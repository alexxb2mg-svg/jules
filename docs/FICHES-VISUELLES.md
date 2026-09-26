# Fiches visuelles : la charte de génération

Une fiche visuelle est le condensé illustré d'une notion : ce que l'élève regarde pour réviser,
affiché sans aucun appel au modèle d'IA. Ce document est le **patron** commun à toutes les fiches
visuelles, quelle que soit la matière : il fixe le fond, la forme et la boucle de contrôle. Il est
repris tel quel dans le paquet de génération (`jules chantier visuel`), si bien qu'une IA, un
contributeur ou un enseignant produisent des fiches de la même facture.

- Le **format** (champs, limites, contrôles du code) : `bibliotheque/SCHEMA-FICHE-VISUELLE.md`.
- La **charte** (ce document) : comment bien remplir ce format.
- La **filière** : paquet → écriture → contrôle et aperçu → relecture (en bas de page).

Une règle de la charte qui peut être contrôlée par le code l'est (validateur de
`jules/fiches_visuelles.py`) : la charte ne dépend pas de la bonne volonté de celui qui génère.

## 1. Le fond : une fiche de révision

- **On explique et on donne les réponses.** La règle « ne jamais donner la réponse » vaut pour
  les exercices, pas pour les fiches ni pour les cartes mentales. Les exemples vont jusqu'au
  résultat et le justifient ; aucune valeur n'est cachée « pour ne pas donner la réponse ».
- **La bulle de Jules (`jules:`) est un complément d'explication** : le pourquoi, ce qu'il faut
  retenir, une confusion fréquente, un moyen de s'en souvenir, un ordre de grandeur. Elle apporte
  quelque chose que le bloc ne dit pas. Jamais une question laissée ouverte (une question
  rhétorique n'est permise que si la phrase suivante y répond). Tutoiement, ton direct.
- **Cohérence avec la fiche v2** de la même notion : mêmes définitions, même piège principal,
  mêmes notations. La fiche v2 et le référentiel sont les sources de contenu.
- **Les notations de l'élève**, celles de son cahier : la division s'écrit **÷** (`ρ = m ÷ V`), jamais
  `/` ; la barre n'existe que dans une unité (m/s, g/cm³). La multiplication s'écrit **×**. Le
  validateur refuse une barre de division dans le texte et dans les schémas.
- **Exactitude** au niveau du programme : unités SI, notations officielles, chaque chiffre vérifié
  deux fois, arrondis justes. Aucune source ni URL inventée : seulement celles de la fiche v2 ou du
  référentiel.

## 2. La structure

Dans cet ordre, 5 à 8 blocs :

| bloc | quand | rôle |
|---|---|---|
| `formule` | si la notion a une relation ou une notation clé | l'essentiel en une ligne, chaque lettre expliquée |
| `carte` | toujours | comment les idées s'articulent (1 nœud principal + 2 à 4 notions ; au-delà, l'affichage passe en colonne) |
| `schema` | dès qu'un dessin aide (presque toujours) | le visuel de la notion |
| `graphe` | si un gabarit existe pour la notion | la notion qui bouge avec des curseurs |
| `methode` | toujours | 3 à 5 étapes, dans l'ordre où l'élève les fait |
| `piege` | toujours | le piège le plus fréquent (celui de la fiche v2 de préférence) |
| `exemple` | toujours (1 ou 2) | situation concrète, calcul complet, conclusion |
| `renfort` | toujours | exercices corrigés, cartes mémoire |

## 3. La mise en valeur

- **Notions clés `**ainsi**`** : grandeurs, lois, concepts qui portent le sens (**masse
  volumique**, **en dérivation**, **corps pur**). Jamais les mots de liaison. Sobriété : 1 à 3 par
  champ, aucun si rien ne ressort ; dans un calcul, seulement le résultat.
- **Le sens des lettres (`variables:`)** : chaque lettre de grandeur des formules et calculs
  (v, d, t, Ec, ρ, U, I...) reçoit une définition courte (« la vitesse, en m/s ou en km/h »).
  L'élève la retrouve en survolant la lettre, sur toutes les pages de Jules. Jamais les symboles
  chimiques (H, O, C...), qui ne sont pas des grandeurs.
- **Les symboles** (≤, ≈, √, π, Ω, °C...) n'ont rien à déclarer : leur nom s'affiche au survol
  partout (`jules/web/static/symboles.js`).

## 4. Les schémas (SVG)

- `viewBox="0 0 680 H"` (H ≤ 480), texte en français, jamais de texte qui déborde ou se chevauche.
- Classes du système de design (voir le format) : `.t` texte, `.ts` petit texte, `.th` titre ;
  boîtes `<g class="node c-blue"><rect/><text class="th"/></g>` ; flèches `class="arr"` avec un
  `marker` défini dans `<defs>` ; `.leader` pour les traits de rappel.
- La couleur d'un groupe `c-*` ne s'applique qu'à `rect`, `circle`, `ellipse` et au texte : un
  `path` ou un `polygon` reçoit `fill`/`stroke` explicites.
- 2 ou 3 couleurs par schéma, chacune avec un sens constant (ex. `c-coral` = chaud, énergie
  perdue ; `c-blue` = froid, électrique). Symboles normalisés pour les circuits (lampe = cercle
  barré d'une croix, résistor = rectangle, A et V dans un cercle).
- « Pas à l'échelle » écrit quand c'est le cas.

## 5. La boucle de contrôle (obligatoire)

1. `jules chantier apercu DOSSIER NOTION...` : chaque fiche passe le validateur (motif affiché
   sinon), puis un aperçu hors ligne est construit avec la vraie page « Mes fiches » ; avec
   `--captures` (Chromium installé), une capture PNG par fiche.
2. Regarder chaque capture : schéma lisible, rien de tronqué, carte lisible, formule juste.
3. Relire en élève : juste, clair, complet.
4. `relecture: {statut: a_relire}` jusqu'à la relecture d'un adulte (enseignant de préférence).

## La filière

```
jules chantier visuel NOTION... [--par PSEUDO] [--sortie paquet.md]   # le paquet à donner à l'IA
# ... l'IA écrit fiches/<matiere>/<notion>.yaml (+ .svg) dans une bibliothèque de type fiches-visuelles
jules chantier apercu DOSSIER [NOTION...] --sortie apercu/ [--captures]  # contrôle + aperçu
```

Le paquet porte une version (`fiche-visuelle/<empreinte>`) : elle change dès que la charte ou le
format change, et la fiche la note dans `generation.paquet` pour savoir de quelles règles elle vient.
