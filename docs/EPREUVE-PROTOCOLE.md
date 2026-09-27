# Épreuve sans aide — protocole

Ce document précise ce que fait réellement le module `jules/modules/epreuve.py` : quand une épreuve
est proposée, ce qui compte comme réussite, ce qui compte comme aide, ce que le code détecte
vraiment et ce qui repose seulement sur le prompt, et ce que voit le parent. Voir aussi
`docs/VISION.md` (section « Ce qui reste sans aide ») et `consignes/modes/epreuve.md` (la consigne
donnée au modèle pendant l'épreuve).

## Quand une épreuve est proposée

Réglages (`config.yaml`, section `epreuve`) :

- `delai_jours` (3 par défaut) : âge minimum d'une notion marquée « comprise » pour être reprise.
- `fenetre_jours` (30 par défaut) : au-delà, une notion trop ancienne n'est plus candidate (elle est
  considérée oubliée sans qu'on ait besoin de vérifier).
- `notions_max` (3 par défaut) : nombre de notions reprises en une seule épreuve.

`epreuve.candidates()` prend, pour chaque notion, le **dernier statut retenu** (voir « Hiérarchie des
origines » ci-dessous) ; seules les notions dont ce statut est `compris`, et dont la date se situe
entre `delai_jours` et `fenetre_jours` avant aujourd'hui, sont candidates. Les plus anciennes
d'abord (les plus exposées à l'oubli). Une épreuve par jour au plus : dès qu'une épreuve est lancée,
la proposition disparaît pour le reste de la journée, même si l'élève ne la termine pas.

## Déroulement et nombre d'items

Une question par notion candidate, dans l'ordre, une à la fois (`consignes/modes/epreuve.md`) :
une application directe, courte, sans piège ni question de cours à réciter. Pendant l'épreuve, Jules
ne doit ni aider, ni indiquer si la réponse est juste — il note et passe à la question suivante.
Après la dernière réponse, Jules fait le bilan (tenu / pas tenu par notion, avec la correction) et
termine par la ligne exacte « Épreuve terminée. », qui déclenche la lecture du bilan par le modèle
rapide (`epreuve.apres_echange`).

## Critère de réussite

Le modèle rapide lit la conversation complète et répond, pour chaque notion, `tenu: true` ou
`tenu: false` (`CONSIGNE_BILAN`). Une notion tenue passe à `acquis` **sauf si une aide a été détectée
pendant l'épreuve** (voir ci-dessous) ; dans ce cas elle reste `en_cours` malgré un `tenu: true`. Une
notion non tenue repasse `en_cours`.

## Ce qui compte comme aide, et ce que le code détecte réellement

Le protocole (`consignes/modes/epreuve.md`) demande à Jules de ne jamais aider pendant l'épreuve :
pas d'indice, pas de rappel de cours, pas de réaction à la justesse d'une réponse. C'est une consigne
de prompt — **rien ne garantit qu'un modèle la respecte toujours**. Le constat de revue du 27/09/2026
était que « sans aide » n'était vérifié par aucun code : si le modèle aidait, le bilan pouvait quand
même déclarer la notion tenue et l'écrire `acquis`.

`epreuve._aide_detectee()` ajoute une vérification **a posteriori**, sur les messages du bot
**avant** le message de bilan final (le bilan donne légitimement la correction, ce n'est pas de
l'aide au sens du protocole) :

1. **Formulations explicites** (`FORMULATIONS_AIDE`) : une liste courte et déterministe de tournures
   (« la réponse est », « voici la solution », « il faut faire », « un indice : », etc.). Si l'une
   apparaît dans un message du bot avant le bilan, l'aide est considérée détectée.
2. **Fuite d'une réponse de fiche connue** : si une leçon du module `cours` porte le même titre
   qu'une notion de l'épreuve et contient un bloc `exercice`, `jules.lecons.contient_la_reponse`
   (le même garde-fou que `jules/modules/cours.py`) est appliqué aux messages du bot : s'il détecte
   la réponse attendue de ce bloc, l'aide est considérée détectée.

Si une aide est détectée, l'événement `suivi` de la notion (même si `tenu: true`) porte le statut
`en_cours`, un résumé dédié (« Épreuve : Jules a aidé, résultat non retenu comme acquis »), et
l'événement `epreuve` porte `aide_detectee: true`.

**Ce que cette heuristique NE détecte PAS** (limite documentée, pas un défaut à corriger en devinant
davantage) :

- une aide implicite (question orientée, ton qui trahit que la réponse est fausse, silence
  significatif) ;
- une aide qui évite volontairement les tournures de `FORMULATIONS_AIDE` ;
- une aide donnée sur une notion qui n'a pas de leçon dans le module `cours` (la vérification 2 ne
  s'applique alors pas) ;
- une aide donnée par une voie qui ne laisse pas de message bot lisible (ex. contenu d'une image).

Le choix est délibérément conservateur : **mieux vaut rater une aide que déclasser `acquis` à
tort**. L'heuristique est un filet, pas une preuve ; elle ne remplace pas une vérification humaine
occasionnelle du déroulement d'une épreuve.

## Hiérarchie des origines (`acquis` > `analyse`)

Chaque événement `suivi` porte un champ `origine` (`analyse`, `epreuve`, `cours`, `exercices`,
`studio` ; les événements écrits avant l'introduction de ce champ sont traités comme `analyse`).
`jules.modules.suivi.dernier_statut` (utilisé par `cours`, `memoire`, `rapport` et `epreuve` partout
où « le dernier événement suivi » sert d'état d'une notion) applique une règle unique : un statut
`acquis` n'est retrogradé que par une origine qui reprend directement la notion (`epreuve`, `cours`,
`exercices`) — jamais par `analyse`, l'analyse en tâche de fond du modèle rapide sur un échange qui
peut être hors sujet. Les autres statuts (`compris`, `en_cours`, `bloque`) suivent toujours le
dernier événement, quelle que soit son origine.

## En cas d'échec

Une notion non tenue à l'épreuve (ou tenue avec aide détectée) repasse `en_cours` : ce n'est pas un
échec noté, elle sera retravaillée et redeviendra candidate à une future épreuve une fois de nouveau
marquée `compris`.

## Ce que voit le parent

Le bilan du soir (`jules/modules/rapport.py`) affiche, pour chaque épreuve du jour, le nombre de
notions tenues sur le total et la liste de celles à retravailler, et marque `[ACQUIS]` les notions
concernées dans la liste des notions du jour. Une ligne fixe rappelle que l'état affiché (`compris`,
`en_cours`, `bloqué`) est une estimation de l'IA et que seul `acquis` vient d'une épreuve sans aide.
