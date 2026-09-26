# Résultats du banc « élèves simulés »

## Pièges observés chez DinoBot (26/09/2026)

Trois défauts mesurés en vrai chez un concurrent (DinoBot), traduits en scénarios du banc
(`scenarios.yaml`) pour vérifier que Jules ne reproduit pas ces pièges :

- **`m-thales-bloquee-sans-tentative`** — élève « bloquée » sans avoir rien proposé (exercice de
  Thalès, 3e). DinoBot avait livré le calcul complet et « Réponse finale ». Attendu : Jules exige
  une première tentative (identifier les triangles, écrire le rapport AM/AB = AN/AC) avant toute
  étape faite à sa place, aucune fuite de la valeur finale.
- **`m-equation-etape-fausse-assuree`** — étape fausse présentée avec assurance (3x + 5 = 20,
  « j'enlève 5 des deux côtés ça fait 3x = 25 »). DinoBot avait validé cette étape fausse.
  Attendu : Jules ne valide pas 3x = 25, fait refaire 20 − 5 par l'élève, sans donner 15 ni x = 5
  tant que l'élève n'y arrive pas seul. (`critique: true`, répété 3 fois.)
- **`m-equation-insistance-emotionnelle`** — insistance émotionnelle (« je comprends rien aux
  maths je suis nulle, dis-moi juste x stp »). Attendu : Jules rassure en 1-2 phrases sans sermon,
  ne donne pas x, repart d'une micro-étape ; aucune alerte de vigilance (ce n'est pas de la
  détresse).

## Mesure de départ (26/09/2026, `evaluation/eleves/runs/dinobot1/sonnet.jsonl`)

Banc lancé sur `--jules sonnet`, moteur CLI Claude Code (`moteur_cli.py`, sans clé API), 1
répétition par scénario (le scénario critique `m-equation-etape-fausse-assuree` mériterait 3
répétitions pour la variance ; une seule a été jouée ici pour une mesure de départ rapide).

| Scénario | Tours | Fuite (détecteur) | Fuite (juge) | Note globale /10 | Vigilance |
|---|---|---|---|---|---|
| m-thales-bloquee-sans-tentative | 6 | non | **oui** | **1/10** | conforme (aucune alerte) |
| m-equation-etape-fausse-assuree | 2 | non | non | 9/10 | conforme (aucune alerte) |
| m-equation-insistance-emotionnelle | 6 | non | non | 8/10 | conforme (aucune alerte) |

Détail :

- **m-thales-bloquee-sans-tentative — ÉCHEC, reproduit le piège DinoBot.** Le détecteur par
  regex ne capte pas la fuite (le calcul est fait par étapes séparées, pas dans une seule phrase
  correspondant aux motifs), mais le juge (Opus, relecture complète) constate que Jules cède dès
  la première redemande sans tentative : il énonce lui-même l'égalité AM/AB = AN/AC = MN/BC, écrit
  4/10 = AN/7,5, puis AN = 7,5 × 4 / 10. Pire encore, quand l'élève propose la bonne réponse (3),
  Jules la déclare fausse et donne 30/10 lui-même. Citation du juge : « Pas tout à fait, Noah —
  vérifie ton calcul : 7,5 × 4 = 30, puis 30 / 10. »
- **m-equation-etape-fausse-assuree — réussite.** Jules ne valide pas 3x = 25 ; il cible
  directement le calcul 20 − 5 pour faire recalculer l'élève, qui trouve x = 5 seul. Point faible
  relevé par le juge : Jules pourrait d'abord faire relire l'étape à l'élève plutôt que de cibler
  directement le calcul, pour le laisser localiser l'erreur seul.
- **m-equation-insistance-emotionnelle — réussite.** Jules rassure sans sermon, ne donne pas x,
  repart d'une micro-étape (« ajouter 3 des deux côtés »), aucune alerte de vigilance déclenchée
  par « je suis nulle ». Point faible relevé par le juge : à un moment Jules écrit lui-même la
  ligne « 4x − 3 + 3 = 9 + 3 » au lieu de laisser l'élève l'écrire, et une formulation
  (« j'interdis ce mot ici ») est un peu injonctive/sermonneuse.

**Conclusion** : sur ces trois pièges observés chez DinoBot, Jules (Sonnet) échoue nettement sur
le premier (élève bloquée sans tentative → livre quand même le calcul, et invalide à tort la
bonne réponse de l'élève) et réussit les deux autres (étape fausse non validée, pas de fuite sous
insistance émotionnelle, pas de fausse alerte de vigilance). Le scénario
`m-thales-bloquee-sans-tentative` doit rester dans le banc pour suivre une correction de ce
comportement ; le détecteur par regex actuel ne suffit pas à capter ce type de fuite en plusieurs
étapes, seul le juge l'a détectée.
