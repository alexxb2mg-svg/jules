# Le chantier des fiches : un appel à contributions

Jules a besoin d'une fiche v2 ([contrat](FICHES-V2.md)) pour chacune des 683 notions de son référentiel
(CM1 158, 5e 132, 4e 141, 3e 252). C'est trop pour une personne, et une fiche v2 se prête bien au don :
elle s'écrit avec une IA, se vérifie par le code, puis se relit par un enseignant. Chacun peut donc prendre
une ou plusieurs notions, les faire écrire par l'IA de son choix et proposer le résultat.

## Deux dépôts

| Dépôt | Contient | Relu par |
|---|---|---|
| [`jules`](https://github.com/alexxb2mg-svg/jules) (celui-ci) | le code, le référentiel du programme (`bibliotheque/programme/`), le contrat des fiches v2, le vérificateur, le générateur de paquets | des développeurs |
| [`jules-bibliotheques`](https://github.com/alexxb2mg-svg/jules-bibliotheques) | les fiches v2 produites par la communauté, une bibliothèque par niveau (`fiches-v2-cm1`, `fiches-v2-5e`, `fiches-v2-4e`, `fiches-v2-3e`), le tableau de bord `CHANTIER.md` | des enseignants |

On sépare les deux dépôts pour trois raisons. Les contributions de contenu ne passent pas par la CI du code,
qui dure plusieurs minutes. Les relecteurs de contenu n'ont pas à suivre les pull requests de code. Et la
licence est propre à chaque dépôt : le code est sous MIT, les fiches sous CC BY-SA 4.0.

Le référentiel reste dans `jules` parce que le code en a besoin au démarrage et qu'il sert à tout le reste :
une fiche d'un autre dépôt s'y rattache par l'identifiant de notion.

### Brancher le dépôt de fiches sur Jules

```bash
git clone https://github.com/alexxb2mg-svg/jules-bibliotheques ../jules-bibliotheques
```

puis dans `config.local.yaml` :

```yaml
bibliotheques_externes: ["../jules-bibliotheques"]   # chemin relatif au dossier de Jules, ou absolu
```

Le module `exercices` de `config.yaml` cite déjà `fiches-v2-3e`, `fiches-v2-4e`, `fiches-v2-5e` et
`fiches-v2-cm1`. Tant que le dépôt n'est pas déclaré, ces bibliothèques sont ignorées sans erreur.

Une bibliothèque est cherchée d'abord dans `bibliotheque/`, puis dans chaque dépôt externe, dans l'ordre de la
liste. `jules fiches verifier` sans argument parcourt aussi les dépôts externes.

## La filière

```
choisir ──> réserver ──> générer (paquet + IA) ──> vérifier et signer en local ──> pull request ──> CI ──> relecture
 CHANTIER.md   ticket     jules chantier paquet     jules fiches verifier / signer       idem      enseignant
```

1. **Choisir** une ou plusieurs notions « à faire » dans `CHANTIER.md` (dépôt `jules-bibliotheques`). Il vaut
   mieux les prendre dans le même chapitre : les prérequis et le vocabulaire se recoupent.
2. **Réserver** : ouvrir un ticket « Je réserve des notions », avec un identifiant par ligne. Le tableau de
   bord l'affiche à la prochaine mise à jour. Une réservation sans nouvelles pendant 21 jours tombe d'elle-même.
3. **Générer** : `jules chantier paquet <notion> [<notion>...] --par <pseudo> --sortie paquet.md` produit
   un texte à coller tel quel dans une IA. Il contient les règles, le contrat (extrait de ce dépôt, donc
   toujours à jour), une fiche modèle et, pour chaque notion, les attendus officiels, les limites, les textes
   officiels citables et les prérequis possibles. Tout le monde part du même paquet ; la version du paquet
   (`fiche-v2/<empreinte>`) est inscrite dans `generation.paquet` de chaque fiche.
4. **Vérifier** : `jules fiches verifier <dossier>` jusqu'à « Conforme. ». En cas de manquement, on renvoie la
   sortie du vérificateur à l'IA, qui corrige seulement ce qui est signalé.
5. **Signer et proposer** : `jules fiches signer <dossier>` scelle les fiches conformes (`verifiee`,
   `empreinte`) ; puis une pull request sur `jules-bibliotheques`. La CI relance le vérificateur, qui refuse
   aussi une fiche modifiée après signature. Une fois fusionnée, Jules sert la fiche sans IA, marquée
   expérimentale. Le contributeur peut signer lui-même : la signature ne vaut que conformité au contrat,
   le vérificateur est déterministe et la CI le rejoue.
6. **Relire** : un enseignant relit, corrige si besoin et renseigne `relecture` ; la fiche passe `relue`.

### Plusieurs générations pour une notion

Une notion qui a déjà sa fiche, ou qui est réservée, peut quand même recevoir d'autres générations, comme
**propositions** : `propositions/<matiere>/<notion>/<pseudo>.yaml`. Le vérificateur les contrôle comme des
fiches, mais elles ne sont **jamais servies**. Un relecteur les compare : il garde la meilleure (en la
déplaçant vers `fiches/`), reprend un exercice ou un piège de l'une dans l'autre, ou les laisse en attente.
Le tableau de bord compte les propositions par notion.

Pour l'instant, on compare et on fusionne à la main. Un outil de fusion assistée (reprendre les exercices
d'une proposition dans la fiche servie) pourra venir si les propositions se multiplient.

## Ce qui garde la qualité

| Garde-fou | Où |
|---|---|
| Le contrat refuse tout champ inconnu, tout corrigé que le code ne retrouve pas, tout indice qui contient la réponse, tout YAML illisible | `jules/fiches/schema.py`, `jules/fiches/commande.py` |
| Le paquet interdit d'inventer une source ou une URL : sans accès au web, seuls les textes officiels fournis (etalab-2.0) sont cités | `jules/chantier.py` (`CONSIGNES`) |
| On génère à partir du référentiel et des sources, **jamais** à partir d'autres fiches générées, pour que les erreurs ne s'accumulent pas | le paquet ne contient qu'une fiche modèle, pour la forme, jamais celle de la notion demandée |
| `generation` dit qui, quand, avec quelle IA et quel paquet | chaque fiche |
| Une fiche modifiée après signature n'est plus servie sans IA (« à re-vérifier » dans le tableau de bord) | `empreinte` |
| Rien n'est `relue` sans un enseignant nommé et daté | `relecture` |

Un essai a été fait le 26/09/2026 sur la notion `ratio` (3e), avec une IA qui suivait le paquet. La première
version avait trois défauts, tous signalés par le vérificateur : un YAML cassé par un « : » non protégé, un
indice qui contenait la réponse (« 1 800 ÷ 9 » quand la réponse est 800) et un exercice ouvert sans échelle
d'indices. Deux allers-retours ont suffi pour arriver à « Conforme. ». Depuis cet essai, le paquet rappelle
la règle des guillemets et le vérificateur signale un YAML cassé au lieu de s'arrêter. La fiche obtenue est la première de `jules-bibliotheques` (`fiches-v2-3e`), en attente de relecture.

## Commandes

```text
jules chantier paquet NOTION [NOTION...] [--par PSEUDO] [--sortie FICHIER.md]
jules chantier etat DOSSIER... [--reservations TICKETS.json] [--depot PROPRIETAIRE/DEPOT] [--sortie CHANTIER.md]
jules fiches verifier [DOSSIER...]
jules fiches signer DOSSIER...
```

`--reservations` lit la sortie de
`gh issue list --label reservation --state open --json number,title,body,author,updatedAt`. Seules comptent les
lignes du ticket faites uniquement d'identifiants de notions : une phrase qui contient le mot « ratio » ne
réserve rien.

## Ce qui reste à faire

- Les leçons et les fiches visuelles, avec le même mécanisme (un paquet par format).
- La conversion des 252 fiches v1 de 3e et des 158 de CM1 : le paquet ne les inclut pas volontairement.
  Un contributeur peut s'en inspirer, mais la fiche v2 doit se fonder sur les attendus et les sources.
- Une aide à la comparaison des propositions.
