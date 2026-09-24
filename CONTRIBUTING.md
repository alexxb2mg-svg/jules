# Contribuer à Jules

Merci de votre intérêt. Jules est un projet de parents, d'enseignants et de bénévoles, pour les enfants. Toute aide compte, même petite.

## Par où commencer

| Vous êtes... | Vous pouvez... | Il faut coder ? |
|---|---|---|
| Enseignant, étudiant | écrire ou relire une fiche de cours, relire les consignes pédagogiques | non |
| Parent | tester Jules avec votre enfant et raconter ce qui coince (issue « Retour d'usage ») | non |
| Enseignant du primaire, du collège ou du lycée | décrire le programme d'un autre niveau, en suivant le format de `bibliotheque/programme/SCHEMA.md` | non |
| Orthophoniste, ergothérapeute, famille concernée | aider à concevoir les adaptations (mode dys, attention) : voir [docs/VISION.md](docs/VISION.md) | non |
| Spécialiste de l'accessibilité | proposer des améliorations (dyslexie, lecture à voix haute, contrastes) | pas forcément |
| Enseignant ou développeur | imaginer un outil pour une matière (frise, géométrie, conjugueur...) : décrivez-le dans un ticket « Idée » | pas pour le décrire |
| Créatif | créer une nouvelle persona (personnalité, avatar, couleurs) | non |
| Développeur Python | modules, moteurs d'IA, notifieurs, tests | oui |
| Développeur web | interface de l'élève et du parent (HTML, CSS, JavaScript sans framework) | oui |

Les tickets marqués **good first issue** sont prévus pour une première contribution.

## Règles de fond

1. **Jules ne donne jamais la réponse.** Toute contribution qui l'amènerait à faire le devoir à la place de l'enfant sera refusée.
2. **La sécurité des enfants passe avant tout.** Les fichiers `consignes/securite.md` et `jules/modules/vigilance.py` demandent la relecture de deux mainteneurs.
3. **Rien de personnel dans le dépôt** : pas de prénom réel, d'adresse, de photo d'enfant, de conversation réelle, de clé API. Pour un exemple, utilisez l'élève fictive « Camille ».
4. **Tout en français**, dans des mots simples : le code, les commentaires, les messages et la documentation.
5. **Pas de nouvelle dépendance sans discussion** dans un ticket : chaque bibliothèque ajoutée doit être maintenue, populaire et sous licence compatible avec MIT.

## Contribuer sans coder

### Une fiche de cours

Le programme de 3e est décrit dans `bibliotheque/programme/3e/`, une matière par fichier, au format expliqué dans `bibliotheque/programme/SCHEMA.md`. Chaque notion a un identifiant et sa source officielle. Pour proposer une fiche, ouvrez un ticket « Fiche de cours » en indiquant la notion. Vous pouvez y coller votre texte directement : un mainteneur s'occupe de le mettre au bon format.

Une bonne fiche contient : l'essentiel du cours en quelques lignes, la méthode pas à pas, un exemple rédigé et deux ou trois exercices corrigés. Citez vos sources ; ne copiez pas un manuel protégé.

### Une persona

Copiez `persona/jules/` vers `persona/<nouvel-id>/`, puis adaptez `persona.yaml` (nom, message d'accueil, couleurs), les fichiers `.md` (identité, ton, petites manies) et l'avatar (`avatar.png`, carré, fond transparent ; un `.svg` marche aussi). Les règles de pédagogie et de sécurité ne sont pas dans la persona : elles restent les mêmes pour toutes. Pour essayer : `persona: <nouvel-id>` dans `config.local.yaml`, puis `jules verifier`.

Dans les textes, écrivez les accords sous la forme `{{elle|il|iel}}` (fille, garçon, neutre) ou `{{e|}}` pour une terminaison. Utilisez `{prenom}` et `{parent}` plutôt qu'un prénom.

### Un mode

Un mode est un seul fichier dans `consignes/modes/`, avec un en-tête (nom, icône, description, ordre) puis les consignes. Il apparaît tout seul comme bouton sur la page de l'élève.

## Contribuer au code

### Préparer son poste

```bash
git clone https://github.com/alexxb2mg-svg/jules.git
cd jules
python -m venv .venv
# Windows : .venv\Scripts\activate    macOS / Linux : source .venv/bin/activate
python -m pip install -e ".[dev]"
pre-commit install
```

`pre-commit` lance à chaque commit : ruff (style et erreurs), la détection de secrets (gitleaks) et le blocage des fichiers privés.

### Vérifier avant d'envoyer

```bash
ruff check .
ruff format --check .
mypy
python -m pytest --cov
```

Tout doit passer : la CI de GitHub lance les mêmes contrôles sous Linux, Windows et macOS, plus une analyse de sécurité (CodeQL) et un audit des dépendances.

### Écrire un module

Une classe `Brique(Module)` dans `jules/modules/<id>.py`, déclarée dans `config.yaml`. Elle peut :

- `contribution(conv)` : ajouter un bloc au prompt système ;
- `apres_echange(conv, eleve, bot)` : agir après chaque échange, en tâche de fond ;
- `taches()` : déclarer une tâche quotidienne à heure fixe ;
- `routes()` : exposer une API sous `/api/modules/<id>/`, réservée au parent.

Ses réglages arrivent dans `self.reglages`. Chaque module a ses tests dans `tests/`.

### Écrire un moteur d'IA

Une classe `Brique` dans `jules/llm/<id>.py` avec une méthode `repondre(systeme, tours, modele) -> str`. La clé API se lit dans la variable d'environnement nommée par `cle_env`, jamais dans un fichier suivi. Les tests remplacent le réseau par un faux transport `httpx.MockTransport` : aucun test n'appelle un vrai service.

### Proposer sa modification

1. Une branche par sujet, à partir de `main`.
2. Des commits courts, avec un message qui dit ce qui change et pourquoi.
3. Une pull request qui remplit le modèle proposé. Un mainteneur relit sous quelques jours.

En contribuant, vous acceptez que votre travail soit publié sous la [licence MIT](LICENSE) du projet.
