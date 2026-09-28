# Performances de Jules : où part le temps, et quoi faire

> **Statut : chantier mis de côté le 28/09/2026, à la demande d'Alex (« à garder pour plus tard »).**
> - Fait : §1, lecteur YAML en C (commits 8da5f5f, 4baaca5). Sur la branche `ui/refonte-2026-09-27`,
>   **pas encore déployé sur l'instance 8799**.
> - À reprendre, rien n'est décidé : cache disque des fiches (§1), pistes (a) à (c) du chat (§2).

Mesures du 28/09/2026 sur le PC d'Alex (Windows, Python 3.14). Scripts de mesure : `profil_demarrage.py`,
`compare_yaml.py`, `mesure_llm.py` (dans le dossier de travail de l'assistant ; à verser dans `outils/perf/`
si on les garde).

## Règle

On mesure avant de réécrire. Un passage en C/C++/Rust ne se justifie que pour une brique **mesurée** comme
lente, **à cause du calcul** (et non d'une attente réseau, disque ou IA), et **qui tourne souvent**.

## 1. Démarrage : 42,7 s → 7,8 s (fait, commit ci-dessous)

Le premier affichage de `/app` appelait `/api/infos`, qui charge une fois pour toutes les fiches :
- 412 fiches v2 (exercices, 4,4 Mo de YAML) : 28,2 s ;
- 270 fiches visuelles : 10,3 s ;
- leçons, référentiel : ~1,2 s.

**Cause : la lecture du YAML par le lecteur écrit en Python** (PyYAML `SafeLoader`), pas le code de Jules.
PyYAML contient déjà un lecteur écrit en C (`CSafeLoader`, sur libyaml), installé sur ce PC et déjà utilisé
par `jules/bibliotheques.py`.

| Lecteur | 1 241 fichiers YAML (dépôt + jules-bibliotheques) | Données obtenues |
|---|---|---|
| Python (`SafeLoader`) | 17,0 s | référence |
| C (`CSafeLoader`) | 1,6 s (×10,5) | **identiques, 0 différence** |

Changement : `jules/yaml_rapide.py` (lecteur C si présent, sinon le lecteur Python : même résultat), utilisé
par les trois chargeurs lourds (fiches v2, fiches visuelles, leçons). Aucune logique changée.

| Étape (mesure identique avant/après) | Avant | Après |
|---|---|---|
| Imports + Tuteur + app | 2,5 s | 2,2 s |
| Premier `/api/infos` (chargement des fiches) | 39,9 s | 5,3 s |
| **Total jusqu'aux premières pages** | **42,7 s** | **7,8 s** |
| Pages suivantes | 0,01 à 0,1 s | inchangé |

C'est exactement la démarche « passer en C » : on a mis du C sous la brique lente, sans écrire de C
nous-mêmes (libyaml est mûr, testé, déjà là).

### Ce qui reste dans les 5,3 s (par ordre de taille)

1. Lecture YAML restante (lecteur C) : ~2,7 s. Piste : **cache disque** des fiches déjà lues et validées
   (clé = empreinte du fichier ; format binaire `pickle`/`marshal` local). Démarrage attendu < 1 s. Pur Python,
   pas de C nécessaire.
2. Contrôles des fiches visuelles (`_verifier_bloc`, `nettoyer_svg`) : ~1,2 s. Le cache ci-dessus les évite aussi
   (une fiche inchangée n'est revérifiée que si le validateur change : mettre sa version dans la clé).
3. Chargement **au démarrage du serveur** plutôt qu'à la première page : l'élève ne voit plus l'attente.

## 2. Une réponse de Jules dans le chat : l'essentiel est l'IA, pas notre code

Chemin de production (`claude_cli`, modèle haiku), mesuré sur 3 appels :

| Cas | Médiane |
|---|---|
| Appel minimal (lancer le CLI + réponse d'un mot) | 4,2 s |
| Prompt système réaliste + question d'élève | 8,7 s |

- **~4 s par appel sont du lancement** : chaque message démarre un nouveau processus `claude` (Node).
- Quand la notion n'est pas encore connue, un **2ᵉ appel** (détection de notion, modèle « rapide ») est fait
  **avant** la réponse (`notions.avant_echange`) : +4 à 5 s sur les premiers messages d'une conversation.
- Notre propre code (assemblage du prompt, base, modules) : quelques millisecondes.

Pistes, **à trancher par Alex** (aucune n'est du C/C++) :
- (a) **Détection de notion en parallèle** de la réponse (au lieu d'avant) : −4 à 5 s sur les premiers
  messages. Contrepartie : la toute première réponse n'a pas encore les infos de la notion dans son prompt.
- (b) **Réponse affichée au fil de l'eau** (streaming, `--output-format stream-json` déjà utilisé) : même
  durée totale, mais le premier mot arrive en ~2 s au lieu de ~9 s.
- (c) **API directe au lieu du CLI** (backend `anthropic` déjà présent dans `jules/llm/`) : supprime les ~4 s
  de lancement par appel. Contrepartie : une clé API et une facturation à l'usage au lieu de l'abonnement.

## 3. Ce qui ne vaut PAS une réécriture en C/C++

| Brique | Temps mesuré | Verdict |
|---|---|---|
| Correction des exercices (`correction.py`) | ~ms par réponse | inutile, et c'est une brique de confiance : on garde Python, lisible et testé |
| Générateurs d'exercices | ~ms | inutile |
| Pages et API (hors premier chargement) | 10 à 100 ms | inutile |
| Nettoyage SVG | ~0,7 s au démarrage seulement | réglé par le cache disque |
| Génération de fiche perso (sources) | ~85 s | 99 % = l'IA ; le C n'y changerait rien |
| Réponse du chat | 4 à 9 s | 99 % = lancement du CLI + l'IA ; voir §2 |

## 4. Si un jour il faut du natif

Pas en C/C++ écrit à la main dans ce dépôt (risque mémoire, compilation Windows, contributeurs) :
1. d'abord une bibliothèque existante déjà compilée (comme libyaml ici) ;
2. sinon Rust via `maturin`/PyO3, avec la version Python gardée comme référence et un test « mêmes
   résultats » sur tout le corpus (comme `compare_yaml.py`).
