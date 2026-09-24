# Fiches v2 : des fiches que Jules sait servir sans IA

Statut : **brouillon de contrat**, à discuter. Rien n'est encore branché sur la conversation : ce document,
le vérificateur et deux fiches de démonstration servent à éprouver le format avant de convertir les 252 fiches.

## Pourquoi

Jules doit rester utile quel que soit le budget de la famille, du « niveau 0 » sans aucune IA jusqu'à un
modèle en ligne haut de gamme. Pour cela, tout ce qui peut être décidé par du code doit l'être :
reconnaître la notion, corriger une réponse, choisir la relance ou l'indice suivant, tenir le suivi. Le
modèle, quand il y en a un, ne fait plus que **router et reformuler**. Un petit modèle installé sur
l'ordinateur suffit alors, parce qu'on ne lui demande plus de juger.

Tout repose sur les fiches. Une fiche v1 (le format actuel) est écrite pour être lue par un modèle : ses
solutions sont des phrases (« Réussite si… »), elle a un seul indice, ses exercices n'ont pas d'identifiant.
Une fiche v2 est écrite pour être **exécutée** : chaque exercice fermé se corrige par le code, a une échelle
de trois indices et des pièges qui relient une erreur typique à sa relance.

## Les principes

1. **La fiche se prouve elle-même.** Le vérificateur (`jules fiches verifier`) corrige chaque exercice avec
   sa propre bonne réponse, vérifie que la solution rédigée aboutit à la réponse attendue, qu'aucun indice ni
   aucune relance ne contient la réponse (même écrite autrement : 2 × 2 × 2 × 3² × 5 pour 2³ × 3² × 5), que
   chaque piège est une vraie erreur que le correcteur sait reconnaître, et qu'aucun piège n'est masqué par un
   autre.
2. **Aucun champ inconnu.** Une faute de frappe dans un nom de champ est une erreur, pas un champ ignoré.
3. **Des identifiants stables partout** : la notion (celle du référentiel), l'exercice (`decomposer-360`),
   le palier d'indice (`relance`, `methode`, `etape`). Le suivi de l'élève peut ainsi dire « exercice
   decomposer-360, réussi après l'indice méthode ».
4. **Une fiche vérifiée est scellée.** `jules fiches signer` calcule une empreinte du contenu. Si le contenu
   change ensuite, la fiche n'est plus servie sans IA tant qu'elle n'a pas été re-vérifiée ; si elle avait
   été relue par un enseignant, la relecture est à refaire (elle portait sur l'ancien contenu).
5. **La machine écrit, le code vérifie, l'humain relit.** Trois états, dans cet ordre :

   | État | Qui | Servie sans IA ? |
   |---|---|---|
   | `generee` | écrite (par un modèle ou un contributeur), pas encore passée au vérificateur | non |
   | `verifiee` | conforme au contrat, scellée par `jules fiches signer` | oui, marquée expérimentale |
   | `relue` | relue par un enseignant (`relecture.par`, `relecture.le`) | oui |

   Un corrigé faux est pire que pas de corrigé : le niveau 0 ne sert jamais une fiche `generee`.

## Le format

Un fichier par notion : `fiches/<matiere>/<id-de-notion>.yaml`. Le nom du fichier est l'identifiant de la notion.

```yaml
format: 2
notion: nombres-premiers-decomposition   # identifiant exact du référentiel
version: 1                               # augmente à chaque changement de contenu déjà scellé
etat: generee                            # generee | verifiee | relue (écrit par `jules fiches signer`)
declencheurs: [nombre premier, facteurs premiers, décomposer en produit]   # au moins 3, sans doublon
prerequis: [multiples-diviseurs-division-euclidienne]   # notions à revoir si ça bloque (liste vide si aucune)
couverture: "..."                        # facultatif : ce que la fiche ne couvre pas encore
essentiel: |                             # le cours en quelques lignes
  ...
methode: [...]                           # étapes, dans l'ordre
vocabulaire:                             # facultatif
  - {terme: "...", definition: "..."}
erreurs_frequentes: [...]
exemple: {enonce: "...", solution: "..."}
exercices:                               # au moins 3 corrigés sans IA, dont un de difficulté 1
  - id: decomposer-360                   # minuscules et tirets, unique dans la fiche
    type: nombre                         # voir « Les types d'exercice »
    difficulte: 1                        # 1, 2 ou 3
    enonce: Décompose 360 en produit de facteurs premiers.
    reponse: {valeur: 360, forme: produit_premiers}
    indices:                             # l'échelle, du plus léger au plus fort ; jamais la réponse
      relance: Par quel nombre premier 360 est-il divisible ?        # une question qui relance
      methode: Divise par 2 tant que c'est possible, puis essaie 3…  # la méthode
      etape: "Première étape : 360 = 2 × 180. Continue avec 180."    # la première étape faite
    pieges:                              # erreurs typiques -> relance ciblée (dite une seule fois)
      - si: {diagnostic: facteur_non_premier}
        relance: Ton produit fait bien 360, mais un de tes facteurs n'est pas premier. Lequel ?
    solution: "360 = 2 × 180 = … = 2³ × 3² × 5."   # montrée seulement quand l'élève a épuisé l'échelle
sources: [...]                           # comme en v1 : titre, url (https), auteurs, licence libre, consulte_le, usage
relecture: {statut: a_relire, par: "", le: ""}
generation:                              # facultatif : qui a écrit la fiche, et à partir de quoi
  par: "..."
  le: "2026-09-24"
  a_partir_de: "..."
empreinte: sha256:...                    # écrite par `jules fiches signer`, ne pas modifier à la main
```

## Les types d'exercice

| Type | `reponse` | Ce que le code corrige | Diagnostics (pour les pièges) |
|---|---|---|---|
| `nombre` | `valeur` (entier, décimal ou `a/b`), `forme` (`libre`, `entier`, `fraction_irreductible`, `produit_premiers`), `tolerance` | la valeur exacte (fractions, virgule, espaces de milliers, « en 1914 ») et la forme demandée | `valeur_fausse`, `produit_faux`, `facteur_non_premier`, `non_irreductible`, `pas_une_fraction` |
| `expression` | `valeur`, `variables` (`[x]`), `forme` (`libre`, `developpee`, `factorisee`) | l'égalité des deux expressions (calcul exact en plusieurs points), puis la forme | `non_equivalente`, `pas_developpee`, `pas_factorisee` |
| `choix` | `options` (`{id, texte}`), `bonnes` | l'ensemble des options choisies (par identifiant ou par texte) | `incomplet`, `mauvais_choix` ; `contient: [id]` vise une option fausse précise |
| `texte_court` | `acceptees`, `fautes_tolerees` (0 à 2) | le mot ou la courte expression, sans casse, accents ni article ; une faute tolérée est signalée | `mauvaise_reponse` |
| `ordre` | `elements` (`{id, texte}`) dans le bon ordre | l'ordre complet ; les éléments sont présentés mélangés, jamais dans le bon ordre | `inversion_voisine`, `ordre_faux` |
| `association` | `gauche`, `droite`, `paires` | chaque association | `une_erreur`, `associations_fausses` |
| `ouverte` | pas de `reponse`, mais des `criteres` (2 au moins) | rien : un adulte ou un modèle relit, avec les critères | aucun |

Un piège se déclenche sur une **valeur** précise (`si: {valeur: 1918}`), sur une **option fausse** choisie
(`si: {contient: [b]}`, exercices `choix`) ou sur un **diagnostic** (`si: {diagnostic: non_irreductible}`).
Les pièges sont lus dans l'ordre : le premier qui correspond est dit, une seule fois par exercice.

Le lecteur d'expressions n'exécute jamais la réponse de l'élève : il la lit comme un arbre de calcul et
refuse tout ce qui n'est pas nombre, variable, `+ − × ÷` ou puissance entière, ainsi que les nombres géants.

## Le parcours sans IA

`jules/fiches/parcours.py` déroule un exercice avec la seule logique du code :

1. l'élève voit l'énoncé (et les options, les éléments à ranger), jamais la réponse ni les indices ;
2. une réponse illisible n'est pas une tentative : Jules redit la forme attendue (« écris un nombre ») ;
3. une réponse fausse déclenche d'abord le piège qui lui correspond, sinon le palier suivant de l'échelle
   (relance, puis méthode, puis étape) ;
4. après le dernier palier, ou six tentatives, Jules montre la correction et propose les prérequis ;
5. chaque tentative produit une observation pour le modèle de l'élève (`docs/MODELE-ELEVE.md`, PR 14) :
   `tentative_aide0` à `tentative_aide3` selon l'aide déjà reçue, avec un poids de 0,5 pour une réponse
   à moitié juste (valeur exacte mais forme non demandée, facteur non premier, une inversion…).

C'est le niveau 0 de Jules. Aux niveaux supérieurs, le parcours ne change pas : un modèle reformule les
messages, relit les exercices `ouverte` avec leurs critères, et converse librement autour.

Le module `jules/modules/exercices.py` branche ce parcours sur la conversation : il ouvre une conversation
en mode caché `exercice` (comme `epreuve`), et répond lui-même à chaque message tant que ce mode est actif
(`Module.repondre_a_la_place`, `jules/moteur.py`) — aucun appel au modèle de langage n'a lieu pendant cette
conversation. Réglage (`config.yaml`) : `bibliotheques`, la liste des dossiers de `bibliotheque/` à
parcourir pour trouver des fiches v2 servables sans IA, par ordre de priorité. À la fin de la série, un
événement `suivi` est écrit (même forme que le module `cours`) : l'épreuve sans aide et le bilan du soir
voient la notion travaillée comme n'importe quelle autre.

## Le vérificateur

```
jules fiches verifier                     # toutes les bibliothèques qui contiennent des fiches v2
jules fiches verifier bibliotheque/xxx    # une bibliothèque
jules fiches signer bibliotheque/xxx      # scelle les fiches conformes (état, empreinte, version)
```

`verifier` liste tous les défauts, fiche par fiche, et sort en erreur (code 1) s'il en trouve un seul. Il
signale aussi les **collisions de déclencheurs** : un même déclencheur revendiqué par deux notions de la
bibliothèque (« virgule » pour la ponctuation et pour les nombres) rend la détection ambiguë. Chaque
collision doit être levée (déclencheur plus précis) avant de publier.

## Filière de production : l'IA nourrit le niveau 0

Les fiches v2 sont faites pour être **générées par un modèle puissant, une fois**, puis servies sans IA à
tout le monde :

1. un modèle écrit la fiche à partir du référentiel (les attendus officiels) et des sources libres citées,
   jamais à partir d'autres fiches générées (les erreurs s'accumuleraient) ;
2. `jules fiches verifier` la refuse tant qu'elle n'est pas conforme ; le modèle corrige ;
3. `jules fiches signer` la scelle : elle est servie, marquée expérimentale ;
4. un enseignant la relit ; elle passe `relue`.

Plus tard, l'usage réel peut proposer des améliorations (tournures d'élèves qui devraient déclencher la
notion, erreurs fréquentes non prévues, indice après lequel les élèves trouvent). Ces propositions restent
**chez la famille** : ce sont des données de mineurs. Rien ne remonte vers une bibliothèque publique sans
anonymisation et sans l'accord explicite du parent.

## Où vivent les fiches

Le contrat (ce document, `jules/fiches/`, les tests) vit dans ce dépôt. Les fiches elles-mêmes ont vocation
à vivre dans un dépôt de bibliothèques à part, avec ses propres relecteurs (des enseignants plutôt que des
développeurs) et une intégration continue qui lance `jules fiches verifier` sur chaque proposition. D'ici là,
`bibliotheque/fiches-v2-demonstration/` contient deux fiches pour éprouver le format :

| Fiche | Exercices corrigés sans IA | Types |
|---|---|---|
| mathématiques, `nombres-premiers-decomposition` | 4 sur 5 | nombre (produit de premiers, fraction irréductible), choix multiple, texte court, ouverte |
| histoire, `guerre-totale-1914-1918` | 6 sur 7 | nombre, choix, association, ordre, texte court, ouverte |

L'histoire est la matière la plus difficile à corriger par le code : la fiche montre qu'on y arrive pour
les repères (dates, acteurs, camps, chronologie, vocabulaire), le développement construit restant `ouverte`.

## Ce qui reste à faire

- ~~Brancher le parcours sur la conversation (un mode « exercice » servi sans IA quand la fiche est
  `verifiee`)~~ : fait, module `exercices` (voir « Le parcours sans IA » ci-dessus).
- Aux niveaux avec IA, ne plus mettre les solutions dans le prompt quand le code corrige : le modèle n'a
  pas besoin de connaître une réponse qu'il ne doit jamais donner.
- Convertir les 252 fiches v1, matière par matière, avec la filière ci-dessus.
- Lever les 28 collisions de déclencheurs déjà mesurées sur les fiches v1.
- Mesurer la détection de notion sans IA sur des phrases d'élèves écrites **indépendamment** des
  déclencheurs (les mesures actuelles sont optimistes : phrases et déclencheurs ont été écrits ensemble).
