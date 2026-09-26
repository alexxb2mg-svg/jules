# Relevé des voix de lecture vocale

Vérification manuelle complémentaire d'EX-006 (`docs/spec/ADAPTATIONS.md`), **non bloquante** :
la vérification qui fait foi est `tests/test_lecture_vocale.py`, qui simule `speechSynthesis` et
ne dépend donc pas de la machine.

`voix.js` liste les voix de synthèse vocale d'un navigateur avec leur propriété `localService`, puis
donne le même verdict que `jules/web/static/lecture-vocale.js` : la lecture vocale n'est disponible
que s'il existe au moins une voix locale (`localService === true`). Une voix « en ligne » enverrait
le texte de l'élève à un serveur tiers : elle n'est jamais utilisée.

## Lancer

Sur un ordinateur, avec Node 22 ou plus et un navigateur de la famille Chromium :

```bash
node evaluation/voix/voix.js "<chemin de l'exécutable du navigateur>"          # voix locales et françaises
node evaluation/voix/voix.js "<chemin de l'exécutable du navigateur>" --tout   # toutes les voix
```

Sur l'appareil de l'élève (tablette, autre ordinateur du réseau local), le plus simple est d'ouvrir
la page parent de Jules **sur cet appareil** : la carte « Lecture vocale » donne le verdict (EX-007).
On peut aussi coller `voix.js` dans la console de développement du navigateur.

## Limite connue

Le script lance le navigateur en mode headless. Un navigateur headless peut ne voir aucune voix
locale alors que le même navigateur, ouvert normalement, en voit : le relevé headless est un indice,
pas une preuve. Ce qui compte est le constat fait sur l'appareil réel de l'élève.

## Relevé du 26/09/2026 (ordinateur de développement, Windows, headless)

| Navigateur | Voix | Locales | Locales fr |
|---|---|---|---|
| Chromium (Chrome) | 3 | 3 | 3 |
| Chromium (Edge) | 321 | 0 | 0 |

Ces chiffres ne valent que pour cette machine (voir `docs/spec/ADAPTATIONS.md`, §5 Risques).
