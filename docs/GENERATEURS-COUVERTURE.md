# Générateurs : couverture des notions de mathématiques 3e

Table de distribution pour les sessions qui écrivent des notions en parallèle. Une session **prend une
ligne** (met son nom dans « Qui »), suit `docs/GENERATEURS-CONTRAT.md`, et ne touche pas aux briques
sans l'écrire dans « Notes ». Quand deux lignes ont besoin de la même brique nouvelle, celle qui la
termine la première la pousse ; l'autre se rebase.

Légende « Faisabilité » : **A** = tout se corrige avec les types actuels (nombre, expression, choix,
ordre, association, texte_court) ; **B** = faisable, mais une brique manque (à écrire, cas 2 du
contrat) ; **C** = le correcteur doit être étendu d'abord (cas 3) ; **D** = notion pas adaptée à la
génération sans IA (production ouverte, figure, programme).

## Nombres et calculs

| Notion | Brevet | Faisabilité | Variantes envisagées | Qui | État | Notes |
|---|---|---|---|---|---|---|
| ecritures-et-comparaison-nombres | oui | A | comparer (choix), ranger (ordre), fraction↔décimal (nombre) | | à faire | |
| puissances-notation-scientifique | oui | A | calculer aⁿ×aᵐ (nombre, forme puissance ?), écriture scientifique (nombre forme scientifique), ordre de grandeur (choix) | | à faire | vérifier que `forme: scientifique` lit « 3,2 × 10⁴ » ; sinon C |
| racine-carree | oui | A | calculer (√k², √(a + b), √ décimal ou produit), aire_cote, carres_parfaits (choix multiple), encadrer (nombre entier) | session 2 | PR ouverte | x² = a traité dans equations-premier-degre-et-produits ; valeurs bornées aux carrés connus (jusqu'à 144, quelques carrés ronds 400, 900…) |
| calcul-nombres-rationnels | oui | A | somme/produit de fractions (nombre forme fraction), priorités (nombre), relatifs (nombre) | | à faire | le correcteur lit « 23/20 » ✔ |
| multiples-diviseurs-division-euclidienne | oui | A | division euclidienne (nombre × 2 : quotient, reste → deux exercices), critères (choix), diviseurs d'un nombre (texte_court liste ?) | | à faire | « liste de diviseurs » = B (brique liste d'entiers) ou choix multiple |
| nombres-premiers-decomposition | oui | A | decomposer, reconnaitre, sachets, fraction | session 1 | **fait** | modèle du pattern |
| fractions-irreductibles | oui | A | simplifier (nombre forme fraction), est-elle irréductible (choix), PGCD (nombre) | | à faire | réutiliser `couple_premiers_entre_eux`, `decomposer` |
| problemes-divisibilite | oui | A | engrenages/PPCM (nombre), conjonction de phénomènes (nombre) | | à faire | brique PPCM à ajouter dans tirage/format |

## Calcul littéral et équations

| Notion | Brevet | Faisabilité | Variantes envisagées | Qui | État | Notes |
|---|---|---|---|---|---|---|
| developper-factoriser-reduire | oui | A | développer (expression), réduire (expression), factoriser (expression), identité remarquable (expression) | | à faire | le correcteur compare des expressions équivalentes : vérifier qu'une factorisation attendue n'accepte pas la forme développée (sinon C : critère « forme factorisée ») |
| equations-premier-degre-et-produits | oui | A | premier_degre, deux_membres (nombre, fraction exacte au palier 3), produit_nul, carre (choix) | session 2 | PR ouverte | brique `algebre.py` créée (affine_fr, facteur_fr, nombre_signe_fr, valeur_machine : « 7/3 » exact, pas de décimal tronqué) ; solutions multiples en choix |
| problemes-mise-en-equation | oui | A | âge, périmètre, prix (nombre) ; choisir la bonne équation (choix) | | à faire | habillage : personnages ✔, articles ✔ |

## Statistiques et probabilités

| Notion | Brevet | Faisabilité | Variantes envisagées | Qui | État | Notes |
|---|---|---|---|---|---|---|
| indicateurs-position | oui | A | moyenne (nombre), médiane (nombre), moyenne pondérée (nombre), comparer deux séries (choix) | | à faire | brique « série de valeurs » (tirage + format « 12 ; 15 ; 9 ») à créer |
| effectifs-et-frequences | oui | A | fréquence d'une valeur (nombre %), effectif depuis fréquence (nombre), compléter tableau (association ?) | | à faire | même brique série |
| histogrammes | oui | D→B | lecture (nombre) possible avec description textuelle des classes ; graphique = D | | plus tard | dépend des fiches visuelles |
| etendue-serie-statistique | oui | A | étendue (nombre), série la plus dispersée (choix) | | à faire | même brique série |
| probabilites-experiences-simples | oui | A | dé, urne, roue (nombre forme fraction), événement contraire (nombre), équiprobabilité (choix) | | à faire | habillage « urne : n boules rouges, m bleues » à ajouter |
| probabilites-deux-epreuves | oui | A | deux tirages avec/sans remise (nombre forme fraction), arbre : compléter (association) | | à faire | |

## Proportionnalité et fonctions

| Notion | Brevet | Faisabilité | Variantes envisagées | Qui | État | Notes |
|---|---|---|---|---|---|---|
| ratio | non | A | partage selon un ratio (nombre), ratio depuis quantités (texte_court « 2:3 » ?) | | à faire | « 2:3 » = C (forme ratio) ou réponse « 2 » puis « 3 » |
| modelisation-fonction-lineaire | oui | A | coefficient depuis un tableau (nombre), 4e proportionnelle (nombre), est-ce proportionnel (choix) | | à faire | |
| pourcentages-coefficient-multiplicateur | oui | A | coefficient, appliquer, taux, initial, successives | session 1 | **fait** | épreuve du pattern ; brique `collision` née ici |
| proportionnalite-en-geometrie | oui | A | échelle (nombre), agrandissement (nombre) | | à faire | recoupe proportionnalite-configurations-geometriques |
| vocabulaire-notations-fonctions | oui | A | f(3)=… (nombre), lire une notation (choix) | | à faire | |
| modes-representation-fonction | oui | A→D | tableau → formule (choix), formule → tableau (nombre) ; graphique = D | | à faire | |
| image-et-antecedent | oui | A | image (nombre), antécédent linéaire (nombre), antécédents de x² (choix) | | à faire | brique « expression en x » (format « 3x − 2 ») à créer |
| fonctions-lineaires-affines | oui | A | coefficient et ordonnée (nombre × 2), linéaire ou affine (choix), calculer a depuis deux points (nombre forme fraction) | | à faire | même brique expression |
| modelisation-et-problemes-par-fonctions | oui | A | tarif A/B, à partir de combien (nombre) | | à faire | |

## Grandeurs, géométrie

| Notion | Brevet | Faisabilité | Variantes envisagées | Qui | État | Notes |
|---|---|---|---|---|---|---|
| volume-boule-et-assemblages | oui | A | volume boule (nombre, arrondi), cylindre + demi-boule (nombre) | | à faire | `reponse.tolerance` existe dans le correcteur (vérifié) : `{valeur: '113.1', tolerance: 0.1}` |
| grandeurs-composees-et-conversions | oui | A | km/h ↔ m/s (nombre), conversions d'aires/volumes (nombre), débit (nombre) | | à faire | |
| grandeurs-et-transformations | oui | A | aire ×k² (nombre), volume ×k³ (nombre) | | à faire | |
| proportionnalite-configurations-geometriques | oui | A | Thalès numérique (nombre), rapport d'homothétie (nombre) | | à faire | figure = décrite en texte (« AB = 4, AM = 6… ») |
| reperage-sur-une-sphere | non | A | lire latitude/longitude (choix), hémisphère (choix) | | plus tard | faible priorité |
| representations-de-solides | oui | D | sections planes : nature de la section (choix) possible | | plus tard | |
| parallelisme-triangles-pythagore | oui | A | hypoténuse (nombre, arrondi), réciproque (choix), contraposée (choix) | | à faire | tolérance ✔ ; triplets exacts (3-4-5, 5-12-13) en difficulté 1 |
| thales-triangles-semblables-trigonometrie | oui | A | Thalès (nombre), cos/sin/tan (nombre, arrondi), angle (nombre, arrondi) | | à faire | tolérance ✔ |
| rotations-et-homotheties | oui | D | image d'un point par homothétie de centre O (nombre × 2 : coordonnées) faisable | | plus tard | |

## Algorithmique

| Notion | Brevet | Faisabilité | Variantes envisagées | Qui | État | Notes |
|---|---|---|---|---|---|---|
| algorithmique-niveau-1 | oui | A | résultat d'une boucle « répéter n fois » (nombre), position finale (nombre × 2) | | à faire | programme décrit en texte |
| algorithmique-niveau-2 | oui | A | valeur d'une variable après séquence (nombre), ordre des instructions (ordre) | | à faire | |
| algorithmique-niveau-3 | oui | A→D | boucles imbriquées : nombre de répétitions (nombre) ; écrire un programme = D | | plus tard | |

## Briques à créer (recensées ci-dessus)

- `tirage.py` : PPCM, série de valeurs entières (n valeurs dans un intervalle, moyenne entière ou non).
- `format_fr.py` : série « 12 ; 15 ; 9 », puissance
  (« 10⁴ »), écriture scientifique.
- ~~expression en x~~ : fait dans `algebre.py` (session 2).
- `habillage.py` : urne (couleurs, effectifs), tarifs (A/B), figures décrites (triangle ABC, longueurs).
- Correcteur : rien d'identifié pour l'instant (la tolérance d'arrondi `reponse.tolerance` existe déjà).

## Ordre conseillé

1. fractions-irreductibles, calcul-nombres-rationnels (briques existantes, rendement immédiat).
2. equations-premier-degre-et-produits, developper-factoriser-reduire (type expression, déjà lu).
3. probabilités (deux notions), statistiques (trois notions) : une brique série + une brique urne.
4. fonctions (cinq notions) : une brique expression en x.
5. géométrie numérique (Pythagore, Thalès, trigonométrie, volumes) avec `tolerance`.
