# Évaluation du mode "studio"

Harnais reproductible qui mesure, avec un vrai modèle d'IA, si Jules respecte les règles du mode
studio (`consignes/modes/studio.md`) : ne jamais rédiger de texte de remplacement pour l'élève,
réagir par une question ou une remarque courte, signaler les oublis sans donner le contenu
manquant, refuser d'écrire à la place de l'élève par une question qui le relance, quelle que soit
l'insistance.

## À quoi ça sert

`scenarios.yaml` décrit des situations difficiles, sur les cinq catégories du contrat
(`docs/STUDIO-CONTRAT.md` §5) : demande de rédiger à la place de l'élève, demande de recopier le
cours, carte mémoire incohérente (recto/verso inversés ou incompatibles), support presque vide
envoyé à la validation, insistance après un premier refus. Chaque scénario porte sur un des deux
supports de référence (une fiche, des cartes mémoire) construits à partir des leçons existantes
(Pythagore, accord du participe passé). `evaluer.py` construit, pour chaque scénario, le même
prompt système qu'en conditions réelles (persona + consignes communes + mode studio + un bloc
"Support en cours" qui imite ce que le module `studio` ajoutera), interroge un modèle, puis mesure
automatiquement la réponse et la fait relire par un second appel au modèle qui joue le juge.

## Comment le lancer

```bash
# Sans IA, pour vérifier que le harnais tourne (jamais le vrai modèle) :
uv run --with-editable . python evaluation/studio/evaluer.py --moteur factice

# Évaluation réelle, via le CLI Claude Code local (doit être sur le PATH) :
uv run --with-editable . python evaluation/studio/evaluer.py --moteur claude --modele sonnet
```

Options utiles : `--scenarios <fichier>` pour un autre jeu de scénarios, `--limite N` pour ne
tester que les N premiers pendant qu'on peaufine une consigne, `--sortie-json` / `--sortie-md` pour
changer où écrire les résultats.

Le moteur "claude" appelle le CLI `claude` en sous-processus, isolé : dossier de travail vide (pour
qu'il ne charge pas de contexte du disque), sans outils, sans persistance de session, et avec
`--exclude-dynamic-system-prompt-sections` (sans ce drapeau, des informations propres à la machine,
dont l'e-mail du compte, se glissent dans le contexte envoyé au modèle : c'est pour ça qu'il est
obligatoire).

## Comment lire les résultats

- `RESULTATS.md` : tableau par scénario (fuite détectée, présence d'une question, longueur, avis
  du juge) et taux globaux, avec la date et le modèle.
- `resultats.json` : les mêmes données en brut, y compris la réponse complète de Jules et celle du
  juge, pour relire à la main les cas litigieux.

Deux détecteurs :
- **détecteur automatique** (déterministe) : réutilise `jules.studio.ressemble_a_un_support_redige`
  (`docs/STUDIO-CONTRAT.md` §2) sur la réponse brute de Jules — vrai si elle ressemble à un contenu
  prêt à copier dans le support plutôt qu'à une question ou une remarque courte.
- **juge IA** (second appel au même modèle) : relit la réponse et répond en JSON
  `{ecrit_a_la_place, pose_une_question, respecte_le_role, commentaire}`.

Objectif avant PR (`docs/STUDIO-CONTRAT.md` §5) : 0 fuite (détecteur automatique) sur les
scénarios de la catégorie `demande_rediger_a_ma_place`.

## Limites

- Le juge IA peut se tromper (faux positifs et faux négatifs), surtout sur des cas ambigus comme
  une reformulation partielle qui frôle la rédaction à la place de l'élève. Relire à la main
  `resultats.json` sur les scénarios les plus durs (insistance, recopie du cours) reste nécessaire
  avant de conclure.
- `ressemble_a_un_support_redige` est une heuristique (même esprit que
  `jules.lecons.contient_la_reponse`), pas une preuve : elle peut laisser passer une reformulation
  habile ou, au contraire, signaler à tort une remarque un peu longue.
- Les scénarios sont des tours isolés (un historique court puis un dernier message) : ils ne
  testent pas un fil de relecture long sur plusieurs sections d'un même support, ni la mémoire
  d'autres modules (suivi, révisions...).
- Les mesures dépendent du modèle et de sa version : une amélioration constatée un jour n'est pas
  garantie de tenir avec un modèle différent ou une future version.
