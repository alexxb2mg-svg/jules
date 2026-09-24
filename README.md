# Jules

**Un tuteur de devoirs libre et gratuit pour les collégiens. Il guide pas à pas et ne donne jamais la réponse.**

Jules aide un enfant à faire ses devoirs comme le ferait un bon répétiteur : il demande ce qui a déjà été essayé, découpe le problème en petites marches et laisse l'enfant trouver. Il retient ce qui bloque et envoie chaque soir un court bilan au parent. Si l'enfant parle de harcèlement ou de mal-être, le parent est prévenu tout de suite.

Le projet est ouvert à tous : parents, enseignants, étudiants, développeurs. Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Ce que fait Jules

- **Aide aux devoirs** avec la photo de l'exercice, sans jamais donner la réponse, même si l'enfant insiste.
- **Cinq modes** : aide aux devoirs, réexplique-moi, quiz, fiche de révision, préparer un contrôle.
- **Suivi des notions** (comprise, en cours, bloquée) et **bilan du soir** pour le parent.
- **Vigilance** : un message inquiétant déclenche une alerte immédiate au parent, et l'enfant est orienté vers le 3018 et le 119.
- **Programme officiel de 3e** découpé en notions, avec la source officielle de chacune (`bibliotheque/`).
- **Données à la maison** : conversations, photos et bilans restent sur l'ordinateur familial. Pas de compte, pas de publicité.

## Installation

Il faut Python 3.10 ou plus récent ([python.org](https://www.python.org/downloads/)).

```bash
git clone https://github.com/alexxb2mg-svg/jules.git
cd jules
python -m venv .venv
# Windows : .venv\Scripts\activate    macOS / Linux : source .venv/bin/activate
python -m pip install -e .
jules installer
jules
```

Ouvrir ensuite <http://127.0.0.1:8795/> (page de l'élève) et <http://127.0.0.1:8795/parent> (espace parent).

Sans installation par pip, `python lancer.py <commande>` fait la même chose que `jules <commande>`.

### Choisir l'intelligence artificielle

`jules installer` pose quelques questions (prénom, genre, classe) puis propose un moteur d'IA :

| Moteur | Coût | Où vont les messages | À prévoir |
|---|---|---|---|
| **Démo** (par défaut) | gratuit | nulle part | rien : pour découvrir l'interface, Jules ne répond pas vraiment |
| **Ollama** | gratuit | restent sur l'ordinateur | [ollama.com](https://ollama.com), puis `ollama pull qwen3-vl:8b` ; un ordinateur assez récent |
| **Mistral AI** | payant à l'usage | Mistral (France) | une clé sur [console.mistral.ai](https://console.mistral.ai) |
| **Anthropic (Claude)** | payant à l'usage | Anthropic | une clé sur [console.anthropic.com](https://console.anthropic.com) |
| **OpenAI** | payant à l'usage | OpenAI | une clé sur [platform.openai.com](https://platform.openai.com) |

Tout service compatible avec le format OpenAI (LM Studio, vLLM, OpenRouter...) fonctionne aussi : voir `config.local.exemple.yaml`.

> **À savoir :** les petits modèles locaux respectent moins bien la règle « ne jamais donner la réponse ». Lors de nos essais, un modèle de 8 milliards de paramètres a fini par céder quand l'élève insistait. Pour un usage quotidien, un moteur en ligne reste plus fiable. Améliorer ce point avec les modèles locaux fait partie des chantiers ouverts.

La clé API se colle dans le fichier `.env`, créé par l'assistant. Elle n'est jamais écrite ailleurs ni affichée. Avec un service payant, fixez un plafond de dépense mensuel dans sa console.

**Âge des utilisateurs.** Les conditions des fournisseurs d'IA encadrent l'usage par des mineurs : c'est l'adulte qui ouvre le compte, accepte les conditions et reste responsable de l'usage. Lisez-les avant de choisir.

### Utiliser Jules sur une tablette

1. Définir les deux codes d'accès : `jules code eleve`, puis `jules code parent`.
2. Dans `config.local.yaml`, mettre `serveur: {hote: 0.0.0.0}`.
3. Sur la tablette, reliée au même wifi, ouvrir `http://<adresse-de-l-ordinateur>:8795/`.

Jules refuse de démarrer sur le réseau tant que les deux codes ne sont pas définis. Ne l'exposez jamais sur Internet.

## Commandes

```text
jules installer            assistant : profil de l'enfant et choix du moteur d'IA
jules                      démarre le serveur
jules verifier             charge toutes les briques et affiche le prompt assemblé
jules code eleve|parent    définit un code d'accès (seule son empreinte est enregistrée)
jules rapport [AAAA-MM-JJ] affiche le bilan d'un jour, sans l'envoyer
```

## Comment c'est construit

Tout se branche par la configuration, sans toucher au cœur :

| Brique | Où | Rôle |
|---|---|---|
| Persona | `persona/<id>/` | La personnalité : nom, ton, couleurs, avatar, en fichiers texte |
| Profil | `profils/<id>.yaml` | Ce que Jules sait de l'élève. Seul `exemple.yaml` est publié |
| Consignes | `consignes/*.md` | Pédagogie, sécurité, format : communes à toutes les personas |
| Modes | `consignes/modes/*.md` | Un fichier = un bouton sur la page de l'élève |
| Modules | `jules/modules/<id>.py` | Mémoire, suivi, vigilance, bilan du soir... |
| Notifieurs | `jules/notifieurs/<id>.py` | Canaux vers le parent : fichier, Telegram |
| Moteurs d'IA | `jules/llm/<id>.py` | demo, openai_compatible, anthropic |

Les textes s'accordent selon le genre indiqué dans le profil (fille, garçon ou neutre) : `{{elle|il|iel}}` dans un fichier de consignes donne la bonne forme. Les variables `{prenom}`, `{classe}` et `{parent}` viennent aussi du profil.

Les consignes de sécurité sont toujours placées en dernier dans le prompt : elles passent avant la persona et le mode choisi.

## Configuration

| Fichier | Contenu | Publié ? |
|---|---|---|
| `config.yaml` | réglages communs, sûrs par défaut | oui |
| `config.local.yaml` | réglages de la famille : profil, codes, moteur, accès tablette | **jamais** |
| `.env` | clés API | **jamais** |
| `profils/<prenom>.yaml` | profil réel de l'enfant | **jamais** |
| `donnees/` | conversations, photos, bilans | **jamais** |

Des tests et un contrôle au moment du commit empêchent ces fichiers privés d'entrer dans le dépôt.

## Vie privée et sécurité

- Rien ne sort de l'ordinateur, sauf les messages envoyés au moteur d'IA choisi (aucun avec Démo ou Ollama).
- Les codes d'accès sont stockés sous forme d'empreinte salée (scrypt), jamais en clair.
- Les pages web refusent tout script ou style venu d'ailleurs (Content-Security-Policy).
- Les photos sont vérifiées (vraie image, 8 Mo au plus) avant d'être enregistrées.

Signaler une faille : voir [SECURITY.md](SECURITY.md).

## Contribuer

Fiches de cours, nouvelles personas, modes, modules, relecture pédagogique, tests avec de vrais élèves, accessibilité : toutes les aides comptent. Pas besoin de savoir coder pour écrire une fiche. Le guide est dans [CONTRIBUTING.md](CONTRIBUTING.md), le code de conduite dans [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Licence

[MIT](LICENSE). Le nom rend hommage à Jules Ferry et à l'école gratuite pour tous.
