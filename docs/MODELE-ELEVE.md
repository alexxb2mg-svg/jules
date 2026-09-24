# Modèle de l'élève : contrat

> Statut : **squelette**. Ce document fixe les formules, les formats et les signatures. Le code de
> `jules/apprentissage/` et de `jules/modules/modele_eleve.py` en découle ; en cas de désaccord entre
> le code et ce document, c'est ce document qui a raison, jusqu'à ce qu'une PR le change.
> Les fonctions marquées `NotImplementedError` sont à écrire ; les tests correspondants existent
> déjà dans `tests/test_modele_eleve.py`, marqués « à implémenter ».

## 1. Ce que ça doit faire

Jules juge aujourd'hui chaque échange en un mot (`compris`, `bloque`, `en_cours`), et le dernier mot
l'emporte. Ce jugement n'a pas de degré, pas de mémoire, et personne ne vérifie s'il est juste.

Le modèle de l'élève remplace ce mot par trois choses :

1. **Une croyance chiffrée par notion** : probabilité que la notion soit comprise, quantité de preuves
   derrière ce chiffre, et probabilité que ça tienne *aujourd'hui* sans aide.
2. **Un réglage de comportement pour le message suivant** (plus ou moins d'étayage, un cran plus facile
   ou plus exigeant, une pause), calculé à partir de l'état de la séance en cours.
3. **Une correction de soi** : chaque épreuve sans aide confronte ce que Jules prédisait à ce qui s'est
   passé. Jules en tire (a) la fiabilité réelle de chacun de ses indices pour *cet* élève, et (b) des
   leçons écrites, gardées tant que les épreuves suivantes leur donnent raison.

Trois lignes rouges, reprises des trois règles de l'essai (docs/VISION.md) :

- **Le modèle règle Jules, il ne l'autorise à rien de plus.** Aucun état, aucune leçon ne peut lever une
  règle de `consignes/pedagogie.md` ou `consignes/securite.md` : pas de réponse donnée, même à un élève
  « frustré ». La politique ne manipule que des curseurs listés au §6.
- **L'élève ne voit aucun chiffre.** Les scores sont pour l'adulte (page parent, bilan du soir). Un
  élève qui voit sa « maîtrise » à 42 % joue avec le chiffre ou se décourage.
- **Rien qui ressemble à un diagnostic.** Le carnet de leçons décrit des comportements de travail
  (« dit avoir compris avant d'avoir vérifié »), jamais un trouble, une capacité ou un trait de caractère.
  Les adaptations (troubles dys, attention) restent le chantier réservé de la VISION.

## 2. Le principe : le modèle de langage constate, les maths jugent

On ne demande **jamais** un nombre à un modèle de langage : ses probabilités ne sont pas calibrées et
dérivent d'un modèle à l'autre. On lui demande des **faits vérifiables** sur l'échange (l'élève a-t-il
tenté avant l'aide ? sa réponse était-elle juste ? quel niveau d'aide a-t-il reçu ?). Les chiffres
viennent d'un modèle probabiliste explicite, dont chaque paramètre a une valeur par défaut sourcée et est
ensuite recalé sur les épreuves de l'élève.

Conséquence sur le choix du modèle de langage : **l'extraction des observations tourne sur le modèle
`principal`**, pas sur `rapide`. Tout le reste en dépend ; une erreur d'extraction se propage à la
croyance, à la politique et à la calibration. Le passage au modèle rapide n'est permis que si un banc
d'essai (§9, `echanges_annotes.yaml`) montre un accord ≥ 0,90 avec l'annotation humaine sur le champ
`resultat` et ≥ 0,85 sur `aide`.

## 3. Les observations

Après chaque échange (hors mode `epreuve`), le modèle `principal` lit les derniers messages et renvoie,
pour **chaque tentative de l'élève** dans le dernier échange, un objet :

```json
{"notion": "fractions : addition", "matiere": "Mathématiques",
 "tentative": true, "resultat": "juste", "aide": 0, "premier_essai": true,
 "auto_correction": false, "explique_methode": false, "declare_compris": false,
 "affect": "neutre", "certitude": "haute"}
```

| Champ | Valeurs | Sens |
|---|---|---|
| `tentative` | bool | l'élève a produit une réponse, un calcul, une phrase (pas seulement une question) |
| `resultat` | `juste` `partiel` `faux` `sans_objet` | justesse de la production, jugée sur le fond |
| `aide` | 0 à 3 | aide reçue **avant** cette tentative sur cette marche : 0 aucune, 1 relance par une question, 2 indice, 3 indice fort ou exemple résolu voisin |
| `premier_essai` | bool | première tentative sur cette marche |
| `auto_correction` | bool | l'élève a repéré et corrigé sa propre erreur sans qu'on la lui montre |
| `explique_methode` | bool | l'élève a reformulé correctement la méthode avec ses mots |
| `declare_compris` | bool | l'élève dit avoir compris (« ok j'ai compris »), sans preuve dans l'échange |
| `affect` | `neutre` `hesitant` `frustre` `decourage` `enthousiaste` | ton du message, d'après les mots seulement |
| `certitude` | `haute` `moyenne` `basse` | l'extracteur est-il sûr de sa lecture (photo floue, réponse ambiguë) |

Chaque objet devient une ou plusieurs **observations** élémentaires, c'est-à-dire un couple
(capteur, valeur binaire) avec un poids :

| Capteur | Émis quand | Valeur |
|---|---|---|
| `tentative_aide0` … `tentative_aide3` | `tentative` et `resultat` ∈ {juste, partiel, faux} | juste → 1, faux → 0, partiel → 1 avec poids × 0,5 |
| `auto_correction` | `auto_correction` | 1 |
| `explication` | `explique_methode` | 1 |
| `declaration` | `declare_compris` | 1 |
| `jugement_ia` | statut du module `suivi` (`compris` → 1, `bloque` → 0) | 1 / 0 |
| `epreuve` | fin d'une épreuve sans aide | tenu → 1, pas tenu → 0 |

Poids de lecture : `certitude` haute 1, moyenne 0,7, basse 0,4. Une observation illisible est
ignorée, jamais devinée.

## 4. La croyance par notion (traçage bayésien des connaissances)

On suit, pour chaque notion, un état caché binaire : **L** (l'élève a compris la notion) ou **¬L**.
C'est le *Bayesian Knowledge Tracing* (Corbett et Anderson, 1995), étendu à plusieurs capteurs de
fiabilités différentes et à des poids.

### 4.1 Paramètres d'un capteur

Chaque capteur *k* a une sensibilité et une spécificité :

$$Se_k = P(x=1 \mid L), \qquad Sp_k = P(x=0 \mid \neg L)$$

(En BKT classique, $Se = 1-\text{slip}$ et $1-Sp = \text{guess}$.) Un capteur n'est informatif que si
$Se_k + Sp_k > 1$ ; la configuration refuse le contraire.

Valeurs par défaut (points de départ, recalés ensuite par la calibration §7) :

| Capteur | Se | Sp | Rapport de vraisemblance si 1 | si 0 | Justification |
|---|---|---|---|---|---|
| `tentative_aide0` | 0,85 | 0,80 | ×4,25 | ×0,19 | slip ≈ 0,15, guess ≈ 0,20 : ordres de grandeur usuels du BKT sur des exercices à réponse ouverte (Baker et al., 2008) |
| `tentative_aide1` | 0,85 | 0,65 | ×2,43 | ×0,23 | une relance aide un peu à « deviner » |
| `tentative_aide2` | 0,85 | 0,50 | ×1,70 | ×0,30 | l'indice porte une partie de la réponse |
| `tentative_aide3` | 0,90 | 0,35 | ×1,38 | ×0,29 | après un exemple voisin, réussir prouve peu, échouer prouve beaucoup |
| `auto_correction` | 0,45 | 0,92 | ×5,6 | – | rare, mais très parlant |
| `explication` | 0,55 | 0,90 | ×5,5 | – | reformuler juste une méthode est un bon signe |
| `declaration` | 0,90 | 0,25 | ×1,2 | – | « j'ai compris » ne prouve presque rien |
| `jugement_ia` | 0,85 | 0,60 | ×2,1 | ×0,25 | **le capteur à surveiller** : un juge IA est souvent trop optimiste |
| `epreuve` | voir §5.3 | | | | la référence, jamais recalée |

### 4.2 Mise à jour par une observation

En log-odds $\ell = \ln\frac{p}{1-p}$, une observation $(k, x, w)$ ajoute :

$$\Delta\ell = w \cdot \ln\frac{P(x \mid L)}{P(x \mid \neg L)}, \quad P(1\mid L)=Se_k,\ P(1\mid\neg L)=1-Sp_k$$

Le poids $w \in (0,1]$ **tempère** la vraisemblance (vraisemblance élevée à la puissance *w*). C'est la
façon standard de dire « cette preuve vaut moins qu'une preuve pleine » sans casser la règle de Bayes.

### 4.3 Les preuves répétées ne sont pas indépendantes

Dix bonnes réponses dans le même exercice ne sont pas dix preuves. Deux garde-fous, appliqués dans cet
ordre :

1. **Décroissance intra-séance** : la *j*-ième observation du même capteur sur la même notion dans la
   même séance reçoit $w_j = w / (1 + \rho\,(j-1))$, avec $\rho = 0{,}5$ par défaut.
2. **Plafond par séance** : la somme des $\Delta\ell$ d'une séance sur une notion est bornée à
   $[-c, +c]$, avec $c = 2{,}0$ par défaut (en probabilité : on ne passe pas de 0,5 à plus de 0,88 en
   une séance). L'épreuve n'est pas plafonnée.

### 4.4 L'élève apprend pendant la séance

Après chaque tentative (pas après `declaration` ni `jugement_ia`), l'état peut passer de ¬L à L :

$$p \leftarrow p + (1-p)\,T_a$$

$T_a$ dépend du niveau d'aide reçu, parce qu'une marche étayée est une occasion d'apprendre :
$T_0 = 0{,}10$, $T_1 = 0{,}12$, $T_2 = 0{,}15$, $T_3 = 0{,}15$. Pas de transition inverse pendant une
séance ; l'oubli est géré à part (§5).

### 4.5 Point de départ d'une notion nouvelle

Le prior d'une notion jamais vue est **tiré vers ce qu'on sait de l'élève dans la matière**
(individualisation à la Pardos et Heffernan, 2010) :

$$\ell_0 = \frac{\kappa\,\ell_{\text{global}} + \sum_{i \in \text{matière}} n_i\,\ell_i}{\kappa + \sum_i n_i}$$

avec $\ell_{\text{global}} = \text{logit}(0{,}30)$, $\kappa = 5$, $n_i$ le nombre effectif de preuves de
la notion *i*. Une élève forte en maths démarre une notion de maths nouvelle un peu plus haut, sans que
ça décide de quoi que ce soit.

### 4.6 Ce qu'on garde par notion

`EtatNotion` (voir `jules/apprentissage/etat.py`) : `p`, `n_eff` (somme des poids reçus), `stabilite`,
`difficulte`, `derniere_revision`, `derniere_observation`, et de quoi appliquer §4.3 et §5.1 dans la
séance en cours (`seance_courante`, `delta_seance`, `rangs_seance`, drapeaux de réussite). La prédiction
figée au lancement d'une épreuve est un événement `prediction` (§11), pas un champ de l'état.

**Fourchette affichée au parent** : intervalle de Wilson à 80 % sur $(p, n_{\text{eff}})$. C'est une
indication de la quantité de preuves, pas un intervalle de confiance au sens strict ; la page le dit.

## 5. L'oubli (courbe de FSRS-4.5)

« Compris pendant la séance » ne veut pas dire « tiendra dans dix jours ». La rétention suit la courbe
de FSRS-4.5 (Ye, 2022 ; wiki *The Algorithm* de open-spaced-repetition) :

$$R(t, S) = \left(1 + F\,\frac{t}{S}\right)^{D_c}, \quad D_c = -0{,}5,\quad F = \frac{19}{81}$$

*t* en jours depuis la dernière révision, *S* la stabilité en jours, telle que $R(S,S) = 0{,}9$.

### 5.1 Stabilité initiale

À la fin de la première séance sur la notion, on note la séance comme un premier passage FSRS :

| Séance | Note FSRS *G* | $S_0 = w_{G-1}$ |
|---|---|---|
| au moins une `tentative_aide0` juste, et `p` ≥ 0,7 | 3 (good) | 3,71 j |
| réussite seulement avec aide ≥ 1 | 2 (hard) | 1,40 j |
| aucune réussite | 1 (again) | 0,49 j |

Difficulté initiale $D_0(G) = w_4 - (G-3)\,w_5$, bornée à [1, 10].

### 5.2 Après une épreuve

- Tenu (G = 3) :
  $S' = S\left(1 + e^{w_8}(11-D)\,S^{-w_9}\,(e^{w_{10}(1-R)}-1)\right)$
- Pas tenu (G = 1) :
  $S' = w_{11}\,D^{-w_{12}}\,((S+1)^{w_{13}}-1)\,e^{w_{14}(1-R)}$
- Difficulté : $D' = w_7 D_0(3) + (1-w_7)(D - w_6(G-3))$, bornée à [1, 10].

Paramètres par défaut : le vecteur FSRS-4.5 publié,
`[0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474, 0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755]`.
Ils ont été ajustés sur des cartes mémoire Anki, pas sur des notions scolaires : ce sont des points de
départ. Leur réajustement sur les épreuves de l'élève n'est **pas** dans ce lot (il faut plusieurs
centaines de révisions ; voir questions ouvertes).

### 5.3 Prédire une épreuve, et la lire

Probabilité que la notion tienne à l'épreuve, *t* jours après la dernière révision :

$$\pi = p\,\big[R\,(1-s_e) + (1-R)\,g_e\big] + (1-p)\,g_e$$

avec $s_e = 0{,}05$ (erreur d'inattention) et $g_e = 0{,}10$ (réussir sans avoir compris). Ces deux
valeurs sont **fixes** : l'épreuve est l'ancre du système, la recaler la rendrait circulaire.

Le résultat met à jour `p` par la règle de Bayes avec ces mêmes vraisemblances (un échec dû à l'oubli
fait moins baisser `p` qu'un échec sur une notion jamais comprise), puis `S` et `D` par le §5.2.

### 5.4 Quand proposer une épreuve

Une notion est candidate quand sa rétention prédite passe sous la cible :

$$t^* = I(r, S) = \frac{S}{F}\left(r^{1/D_c} - 1\right), \qquad r = 0{,}85 \text{ par défaut}$$

Les candidates sont triées par $R$ croissant (les plus exposées d'abord), et limitées par
`epreuve.notions_max`. Cette règle remplace `delai_jours` du module `epreuve` quand le modèle de
l'élève est actif ; sinon `epreuve` garde son comportement actuel.

## 6. La politique : régler Jules pour le message suivant

### 6.1 Indicateurs de séance

Moyennes mobiles exponentielles, mises à jour à chaque observation de la séance :

$$s_t = \gamma\,x_t + (1-\gamma)\,s_{t-1}$$

- **Réussite** $s$ : $x$ = crédit de la tentative : juste sans aide 1 ; avec aide 1, 2, 3 : 0,75 / 0,5 /
  0,25 ; partiel : la moitié ; faux : 0. $\gamma = 0{,}4$ ; la première tentative de la séance initialise
  $s$ à la moyenne de son crédit et du $p$ de la notion.
- **Frustration** $f$ : $x$ = 1 si `affect` ∈ {frustre, decourage}, 0,5 si `hesitant`, et +0,5 (borné
  à 1) dès la 3e erreur d'affilée. $\gamma_f = 0{,}5$.
- **Durée** : minutes de travail effectif depuis le début de la séance (écarts > 10 min exclus, comme
  le bilan du soir).

### 6.2 États et seuils

| État | Condition d'entrée | Sortie (hystérésis) | Priorité |
|---|---|---|---|
| `frustration` | $f \ge 0{,}6$ | $f < 0{,}45$ | 1 |
| `fatigue` | durée ≥ 40 min et $s$ en baisse sur les 4 dernières tentatives | nouvelle séance | 2 |
| `decouverte` | $n_{\text{eff}} < 3$ sur la notion | $n_{\text{eff}} \ge 3$ | 3 |
| `fragile` | $s < 0{,}55$ | $s \ge 0{,}62$ | 4 |
| `trop_facile` | $s \ge 0{,}90$ et au moins 3 tentatives sans aide dans la séance | $s < 0{,}83$ | 5 |
| `zone_cible` | sinon | | 6 |

La plage visée, environ 60 à 85 % de réussite, s'appuie sur la « règle des 85 % » (Wilson et al.,
2019 : un taux d'erreur d'environ 15 % maximise la vitesse d'apprentissage dans une large famille
d'apprentissages par essais) et sur les difficultés désirables (Bjork et Bjork, 2011). Pour un élève
qui apprend avec un tuteur, et non une machine qu'on entraîne, c'est un **repère réglable**, pas une loi.

**Anti-oscillation** : un changement d'état ne s'applique qu'après `maintien` messages consécutifs dans
le nouvel état (2 par défaut), sauf vers `frustration`, qui s'applique tout de suite.

### 6.3 Curseurs réglés

Chaque état donne un `Reglage` :

| Curseur | Valeurs | Effet dans le prompt |
|---|---|---|
| `etayage` | 0 à 3 | niveau d'aide maximal autorisé avant une nouvelle tentative |
| `difficulte` | −1, 0, +1 | exercice suivant un cran plus simple, identique ou plus exigeant |
| `exiger_explication` | bool | faire reformuler la méthode avant de valider |
| `proposer_pause` | bool | proposer une pause ou un format plus court |

Le texte injecté dans le prompt vient de `consignes/politique.yaml` (un paragraphe par état, avec les
accords de genre de `jules/texte.py`). C'est un fichier de contenu, relu par des humains, pas généré.

## 7. La calibration : chaque épreuve corrige Jules

### 7.1 Ce qu'on apprend

Pour chaque capteur *k* : $Se_k$ et $Sp_k$ **pour cet élève**, puis par matière si les données le
permettent. Pas les paramètres de l'épreuve (l'ancre).

### 7.2 Méthode : EM avec a priori (MAP-EM)

Pour chaque notion, la suite de ses observations et de ses épreuves forme une chaîne de Markov cachée à
deux états (§4). L'algorithme alterne :

- **E** : passes avant-arrière (*forward-backward*) avec les paramètres courants, qui donnent pour
  chaque observation $i$ la probabilité lissée $\gamma_i = P(L_i \mid \text{toutes les données,
  épreuves comprises})$.
- **M** : pour chaque capteur, avec un a priori Beta centré sur la valeur par défaut, de force
  $\kappa_c$ (5 par défaut) :

$$\hat{Se}_k = \frac{\sum_{i\in k} w_i\,\gamma_i\,x_i + \kappa_c\,Se_k^{0}}{\sum_{i\in k} w_i\,\gamma_i + \kappa_c}
\qquad
\hat{Sp}_k = \frac{\sum_{i\in k} w_i\,(1-\gamma_i)(1-x_i) + \kappa_c\,Sp_k^{0}}{\sum_{i\in k} w_i\,(1-\gamma_i) + \kappa_c}$$

Arrêt quand la variation maximale d'un paramètre passe sous $10^{-4}$, ou après 50 itérations. Après
chaque M, on impose $Se_k + Sp_k \ge 1{,}02$ (projection sur la frontière si besoin) pour qu'un capteur
ne change jamais de sens. Les paramètres par matière ont pour a priori les valeurs de l'élève toutes
matières confondues (hiérarchie à deux niveaux).

Tant que l'élève a passé moins de `epreuves_min` épreuves (8 par défaut), on garde les valeurs par
défaut. La calibration se relance après chaque épreuve (quelques millisecondes pour quelques milliers
d'observations).

### 7.3 Ce que ça corrige, concrètement

Si Jules dit « compris » en géométrie et que ça ne tient qu'une fois sur deux, $\hat{Sp}$ de
`jugement_ia` en géométrie baisse : son « compris » y pèse moins, les épreuves y arrivent plus tôt, la
politique y reste plus longtemps en `fragile`. Rien n'est réécrit à la main.

### 7.4 Mesurer si Jules juge bien

À chaque épreuve, la prédiction $\pi$ (figée au lancement) et le résultat $y$ sont enregistrés. Sur une
fenêtre glissante (les 60 dernières épreuves par défaut) :

- **Score de Brier** $\frac1N\sum(\pi_i-y_i)^2$ et **perte logarithmique**
  $-\frac1N\sum[y_i\ln\pi_i + (1-y_i)\ln(1-\pi_i)]$ : règles de score propres (Gneiting et Raftery,
  2007), un modèle ne les améliore qu'en prédisant mieux.
- **Score de compétence** $1 - \text{Brier}/\text{Brier}_{\text{réf}}$ contre deux références : la
  climatologie (le taux de réussite moyen) et l'ancienne règle « dernier statut ». En dessous de 0, le
  modèle fait pire que la référence, et la page parent le dit.
- **Table de fiabilité** en 5 classes de $\pi$ et **erreur de calibration attendue (ECE)**.

## 8. Le carnet de leçons

La partie « ne pas refaire la même erreur », à la façon dont un agent tient ses notes de sessions.

### 8.1 Quand on écrit

Seulement sur **surprise** : la perte logarithmique de l'épreuve dépasse le seuil
$\text{surprise} = -\ln P(y) \ge \ln 4$ (Jules donnait 25 % ou moins à ce qui s'est passé). Le modèle
`principal` relit alors la séance d'origine et l'épreuve, et propose **au plus une** leçon :

```json
{"portee": "matiere", "cle": "Mathématiques", "sens": "surestimation",
 "texte": "En géométrie, faire refaire une figure seule avant de conclure qu'elle a compris."}
```

`portee` : `notion`, `matiere` ou `global`. `sens` : `surestimation` (Jules croyait que ça tiendrait)
ou `sous_estimation`. Le texte est une consigne de travail pour Jules, 200 caractères au plus.

### 8.2 Filtre avant d'enregistrer

Refusée si le texte : contient un vocabulaire de diagnostic ou de jugement de la personne (liste dans
`jules/apprentissage/carnet.py`, `MOTS_INTERDITS`) ; demande de donner une réponse ou un indice qui la
contient ; parle d'une autre personne que l'élève et Jules ; double une leçon active de même portée et
de même sens (similarité de mots ≥ 0,6).

### 8.3 Vérifier une leçon par les épreuves suivantes

Une leçon est une hypothèse : « depuis que je fais ça, je me trompe moins dans cette portée ». Sa
preuve est l'écart de perte logarithmique dans sa portée, avant et après son entrée en vigueur :

$$\Delta = \overline{\text{perte}}_{\text{avant}} - \overline{\text{perte}}_{\text{après}}$$

- **confirmée** si, après au moins 3 épreuves dans sa portée, $\Delta > 0$ ;
- **retirée** si, après 5 épreuves, $\Delta \le 0$ ; ou à expiration (45 jours sans épreuve dans sa
  portée) ;
- **budget** : au plus 12 leçons actives ; au-delà, on retire d'abord les non confirmées, les plus
  anciennes en premier.

C'est une preuve faible (une seule élève, peu d'épreuves, d'autres choses changent en même temps) ;
la page parent l'affiche comme « semble aider » et « n'a pas aidé », jamais comme un résultat.

### 8.4 Ce qui entre dans le prompt

Les leçons actives de portée `global`, de la matière de la séance et de sa notion, dans une section
« Ce que tu as appris de tes erreurs avec {prenom} », au plus 5, confirmées d'abord.

Le parent voit tout le carnet, peut retirer une leçon, et le carnet part dans l'export du dossier.

## 9. Le simulateur, et comment on accepte le code

Avant de toucher un vrai élève, tout se mesure sur des élèves virtuels (`jules/apprentissage/simulateur.py`).
Un élève virtuel a, par notion : un état caché vrai qui évolue (apprentissage selon l'aide, oubli selon
une vraie stabilité), des vrais slip/guess, et un juge IA **biaisé** (paramètre `biais_juge` : il dit
« compris » à tort avec une probabilité donnée). Le simulateur produit des séances, des observations et
des épreuves, avec une graine fixée pour que les tests soient reproductibles.

Critères d'acceptation (tests `test_modele_eleve.py`, sur 200 élèves virtuels × 20 notions × 60 jours) :

| # | Critère | Seuil |
|---|---|---|
| A1 | Brier du modèle < Brier de la règle « dernier statut » | écart ≥ 0,03 |
| A2 | Score de compétence contre la climatologie | > 0,10 |
| A3 | ECE après 60 jours | < 0,08 |
| A4 | Juge biaisé (`biais_juge` = 0,4) : $\hat{Sp}$ de `jugement_ia` recalé à ±0,10 de la vraie valeur | 80 % des élèves |
| A5 | Juge non biaisé : la calibration ne dégrade pas le Brier | écart ≤ 0,005 |
| A6 | Politique : pas plus de 1 changement d'état par tranche de 4 messages, en moyenne | sur toutes les séances simulées |
| A7 | Aucune leçon qui passe le filtre du §8.2 avec les textes du fichier de tests négatifs | 0 |
| A8 | Temps de mise à jour après un échange (hors appel au modèle de langage) | < 5 ms |

Banc d'essai de l'extracteur : `tests/cas/modele_eleve/echanges_annotes.yaml` contient des échanges
annotés à la main. Il sert en CI avec le moteur factice (forme du JSON), et hors CI avec un vrai modèle
(accord, §2).

## 10. Configuration

```yaml
- id: modele_eleve
  actif: false                 # squelette : ne pas activer avant les lots 1 a 4
  reglages:
    modele_analyse: principal  # jamais 'rapide' sans le banc d'essai du §2
    estimateur: bkt            # bkt | dernier_statut (reference, pour comparer)
    capteurs: { ... }          # voir config.yaml, valeurs du §4.1
    apprentissage: {aide0: 0.10, aide1: 0.12, aide2: 0.15, aide3: 0.15}
    prior: {global: 0.30, force: 5}
    repetition: {decroissance: 0.5, plafond_seance: 2.0}
    oubli: {retention_cible: 0.85, glissement_epreuve: 0.05, chance_epreuve: 0.10}
    politique: { ... }         # seuils du §6.2
    calibration: {actif: true, epreuves_min: 8, force_a_priori: 5, fenetre_mesure: 60}
    carnet: {actif: true, seuil_surprise: 1.386, max_lecons: 12, expiration_jours: 45}
```

Tous les réglages sont lus et validés par `jules/apprentissage/parametres.py` ; une valeur absurde
(capteur non informatif, seuil hors de [0, 1], hystérésis inversée) arrête `jules verifier` avec un
message clair.

## 11. Stockage

Aucune table nouvelle. Tout passe par les deux mécanismes existants de `jules/stockage.py` :

| Quoi | Où | Clé |
|---|---|---|
| observation élémentaire | événement `observation` | une par capteur |
| prédiction figée d'une épreuve | événement `prediction` | au lancement |
| état d'une notion | état, espace `modele_eleve` | `notion:<matière> : <notion>` |
| état de la séance | état, espace `modele_eleve` | `seance:<conversation>` |
| paramètres calibrés | état, espace `modele_eleve` | `calibration` |
| carnet | état, espace `modele_eleve` | `carnet` |

L'état se **reconstruit** entièrement à partir des événements (`reconstruire()`), ce qui rend le
réglage des paramètres rejouable et l'effacement du dossier propre.

## 12. Découpage du travail

| Lot | Fichiers (exclusifs) | Dépend de |
|---|---|---|
| 1. Observations | `apprentissage/observations.py`, `tests/cas/modele_eleve/` | – |
| 2. Estimateur et oubli | `apprentissage/estimateurs.py`, `apprentissage/oubli.py` | 1 (format) |
| 3. Simulateur | `apprentissage/simulateur.py` | 2 (signatures) |
| 4. Calibration et mesures | `apprentissage/calibration.py`, `apprentissage/mesures.py` | 2, 3 |
| 5. Politique | `apprentissage/politique.py`, `consignes/politique.yaml` | 2 |
| 6. Carnet | `apprentissage/carnet.py` | 4 |
| 7. Brique et intégration | `modules/modele_eleve.py`, `modules/epreuve.py`, `config.yaml`, page parent | tous |

Les signatures publiques de `jules/apprentissage/*.py` sont gelées par ce squelette. Les changer passe
par une modification de ce document dans la même PR.

## 13. Questions ouvertes

- Recaler les paramètres FSRS sur l'élève : à partir de combien d'épreuves est-ce raisonnable ?
  (FSRS demande des centaines de révisions ; une élève en fera peut-être 300 par an.)
- Relier les notions entre elles (prérequis) pour propager une croyance : une notion de 4e bloquée
  explique peut-être une notion de 3e. Demande un graphe de prérequis dans les bibliothèques.
- La page parent : quels chiffres montrer, et comment dire l'incertitude sans noyer l'adulte ?
- Mesurer si la politique aide vraiment (et pas seulement si elle est bien calibrée) : il faudrait
  comparer des périodes avec et sans, ce qui pose une question d'éthique pour un seul enfant.

## Références

- A. T. Corbett, J. R. Anderson (1995). *Knowledge tracing: Modeling the acquisition of procedural
  knowledge*. User Modeling and User-Adapted Interaction 4, 253–278.
- R. S. J. d. Baker, A. T. Corbett, V. Aleven (2008). *More accurate student modeling through
  contextual estimation of slip and guess probabilities in Bayesian Knowledge Tracing*. ITS 2008.
- Z. A. Pardos, N. T. Heffernan (2010). *Modeling individualization in a Bayesian networks
  implementation of knowledge tracing*. UMAP 2010.
- J. Ye et al. (2022). *A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition
  Scheduling*. KDD 2022. Formules FSRS-4.5 : wiki *The Algorithm*, dépôt open-spaced-repetition/awesome-fsrs.
- R. C. Wilson, A. Shenhav, M. Straccia, J. D. Cohen (2019). *The Eighty Five Percent Rule for optimal
  learning*. Nature Communications 10, 4646.
- E. L. Bjork, R. A. Bjork (2011). *Making things hard on yourself, but in a good way: Creating
  desirable difficulties to enhance learning*.
- A. P. Dempster, N. M. Laird, D. B. Rubin (1977). *Maximum likelihood from incomplete data via the EM
  algorithm*. JRSS B 39, 1–38.
- T. Gneiting, A. E. Raftery (2007). *Strictly proper scoring rules, prediction, and estimation*.
  JASA 102, 359–378.
- G. W. Brier (1950). *Verification of forecasts expressed in terms of probability*. Monthly Weather
  Review 78, 1–3.
