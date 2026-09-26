# Collecte des referentiels -- Adaptations troubles dys

Collecte realisee le 26/09/2026. Chaque source a ete ouverte et verifiee a cette date.
Les niveaux de preuve suivent l'echelle : etude (etude controlee publiee), norme (standard
ou texte reglementaire), usage (pratique professionnelle courante sans etude controlee).


## Tableau des leviers

| Levier | Valeur neutre | Valeur / plage recommandee | Amenagement PAP lie (libelle officiel circulaire 2015-016) | Conflits connus | Niveau de preuve | Source (DOI ou URL ouverte le 26/09) |
|---|---|---|---|---|---|---|
| Espacement inter-lettres | `normal` (navigateur) | +2.5 pt au-dessus de la valeur par defaut (police Times-Roman 14pt dans l'etude) | "Proposer des supports ecrits aeres et agrandis" (college, p. 1) | Peut degrader la lisibilite a forte dose ; allonge les lignes | Etude (effet positif sur vitesse et precision, replication partielle) | Zorzi et al. 2012 DOI: 10.1073/pnas.1205566109 -- 74 enfants (34 IT + 40 FR), 8-14 ans, espacement +2.5 pt, erreurs reduites d'un facteur 2, vitesse +0.3 syll/s. Replication partielle : Duranovic et al. 2018 DOI: 10.1007/s11881-018-0164-z (amelioration de la precision mais pas de la vitesse, population bosniaque). Marinus et al. 2016 DOI: 10.1002/dys.1527 (pas d'effet en neerlandais, mais etudiait la police Dyslexie, pas l'espacement seul). |
| Espacement inter-mots | `normal` | >= 3.5x l'espacement inter-lettres (BDA) | "Proposer des supports ecrits aeres et agrandis" | Allonge les lignes, conflit avec longueur de ligne reduite | Usage | BDA Dyslexia Style Guide 2018, section "Readable Fonts" -- PDF archive : https://www.targetdyslexia.org/app/download/11639293/BDA%2BDyslexia%2BFriendly%2BContent%2B-%2BFonts.pdf (page originale bdadyslexia.org.uk supprimee, 404 le 26/09). Version 2023 : https://www2.worc.ac.uk/disabilityanddyslexia/documents/British%20Dyslexia%20Association%20Style%20Guide.pdf |
| Interligne | 1.55 (valeur actuelle Jules) | >= 1.5 (BDA, WCAG 1.4.8 AAA) ; 1.5-2.0 (BDA) | "Proposer des supports ecrits aeres et agrandis" | Reduit le nombre de lignes visibles ; conflit avec densite reduite si fort agrandissement | Norme (WCAG 1.4.8 AAA) / Usage (BDA) | WCAG 2.2 critere 1.4.8 : https://www.w3.org/TR/WCAG22/#visual-presentation -- BDA Style Guide 2018 (meme PDF que ci-dessus) |
| Longueur de ligne | illimitee (CSS par defaut) | 60-70 caracteres (BDA) ; <= 80 caracteres (WCAG 1.4.8 AAA) | "Proposer des supports ecrits aeres et agrandis" | Contraint la mise en page des outils dans l'iframe | Norme (WCAG 1.4.8 AAA) / Usage (BDA) | WCAG 2.2 critere 1.4.8 : https://www.w3.org/TR/WCAG22/#visual-presentation -- BDA Style Guide 2018 |
| Taille du texte | variable (en rem depuis EX-010) | Reglable par l'utilisateur, pas de perte de contenu jusqu'a 200% (WCAG) ; 12-14 pt ou equivalent (BDA) | "Agrandir les formats des supports ecrits (A3)" (elementaire, p. 1) ; "Proposer des supports ecrits aeres et agrandis (exemple : ARIAL14)" (college, p. 1) | Agrandissement + densite reduite = tres peu de contenu visible ; arbitrage parent | Norme (WCAG 1.4.4 -- pas de seuil en pt, seulement redimensionnement a 200%) / Usage (BDA pour le seuil 12-14 pt) | WCAG 2.2 critere 1.4.4 : https://www.w3.org/TR/WCAG22/#resize-text -- BDA Style Guide 2018 |
| Police de caracteres | `--police-texte` (variable CSS) | Sans-serif a largeur reguliere (Arial, Verdana, Calibri). Pas de police "speciale dys". | "Proposer des supports ecrits aeres et agrandis" | Aucun conflit connu | Usage (les polices speciales dys n'ont pas de benefice mesure) | Wery & Diliberto 2017 DOI: 10.1007/s11881-016-0127-1 -- "The effect of a specialized dyslexia font, OpenDyslexic, on reading rate and accuracy" (Crossref verifie 26/09, titre exact). Kuster et al. 2018 DOI: 10.1007/s11881-017-0154-6 -- "Dyslexie font does not benefit reading in children with or without dyslexia" (Crossref verifie 26/09). BDA Style Guide 2018 |
| Densite d'ecran (elements visibles) | tout affiche | Reduire le nombre d'elements simultanes, un exercice a la fois | "Limiter la copie (synthese du cours photocopiee)" (college, p. 1) ; libelle non verifie: "Limiter la quantite d'informations" | Surcharge visuelle possible si combine avec coloration syllabique ; arbitrage parent | Usage | FFDys -- https://www.ffdys.com/actualites/amenagements-aux-examens-4-dec-2020-publication-du-decret-et-de-la-circulaire/ (page specifique aux amenagements d'examen, pas page generale -- le lien /troubles-dys/amenagements redirige ici) ; pratiques orthophonistes |
| Lecture vocale | desactivee | Proposee (bouton), jamais automatique sauf amenagement explicite | "Proposer a l'eleve une lecture oralisee (enseignant ou autre eleve) ou une ecoute audio des textes supports de la seance" (elementaire, p. 2) | Gene un eleve en difficulte de comprehension orale ; arbitrage parent | Usage | PAP circulaire 2015-016, annexe PDF elementaire p. 2 -- source du PDF : https://aefe.gouv.fr/sites/default/files/asset/file/modele-plan-accompagnement-personnalise-pap-education-nationale.pdf (telecharge et lu le 26/09) |
| Consigne decoupee en etapes | consigne complete | Une etape affichee a la fois, avec possibilite de revoir les precedentes | "Decomposer les consignes et informations complexes (Utiliser de preference des consignes simples)" (maternelle, p. 1) ; "Aider a la comprehension des consignes et des informations (reformulation, ...)" (maternelle, p. 1) | Aucun conflit connu | Usage | PAP circulaire 2015-016, annexe PDF maternelle p. 1 |
| Longueur des phrases de Jules | libre | <= 15 mots par phrase, structure sujet-verbe-complement | libelle non verifie: "Simplifier les enonces" | Peut paraitre infantilisant pour un eleve plus age ; levier reglable | Usage | Methode FALC (Facile a Lire et a Comprendre) : https://www.culture.gouv.fr/thematiques/culture-et-handicap/ressources-handicap/facile-a-lire-et-a-comprendre-falc-une-methode-utile (page ouverte le 26/09, titre : "Facile a lire et a comprendre (FALC) : une methode utile, Ministere de la Culture") |
| Reperes colores -- syllabes | desactive | Alternance de 2 couleurs par syllabe, couleurs a contraste suffisant (ratio >= 3:1 sur fond) | "Surligner des mots cles / passages importants pour faciliter la lecture de l'eleve" (elementaire, p. 2) ; "Utiliser des couleurs pour segmenter les mots, les phrases" (elementaire, langues vivantes) | Surcharge visuelle possible ; arbitrage parent | Usage | Pratique orthophoniste courante ; pas d'etude controlee identifiee. Le libelle PAP le plus proche est celui cite ; "Surligner les syllabes" n'est pas un libelle officiel du PAP. |
| Reperes colores -- rang des chiffres (unites/dizaines/centaines) | desactive | Couleurs distinctes par rang, coherentes sur toute l'application | "Presenter les calculs en colonnes avec des reperes de couleur (ex : colonne des unites en rouge, des dizaines en bleu et des centaines en vert)" (elementaire, mathematiques) | Ajout d'information visuelle, conflit modere avec densite reduite | Usage | PAP circulaire 2015-016, annexe PDF elementaire, section mathematiques |
| Temps supplementaire | temps standard | +33% (valeur PAP : "ne peut exceder le tiers du temps") ou +50% (valeur PPS), facteur reglable | "Accorder un temps majore" (elementaire et college, evaluations) | Aucun conflit connu | Norme (droit) | PAP circulaire 2015-016, annexe PDF -- Code de l'education art. D351-27 : https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006527303 (lu le 26/09 : "Une majoration du temps imparti [...] qui ne peut exceder le tiers du temps normalement prevu") |
| Saisie : clavier ou dictee | clavier | Clavier avec prediction ou dictee vocale | "Permettre l'utilisation de l'ordinateur et de la tablette" (elementaire et college) | Dictee hors perimetre v1 (voix d'enfant mineur vers serveur distant, cf. decision de la spec) | Usage / Norme (droit PAP) | PAP circulaire 2015-016, annexe PDF |
| Contraste texte/fond | contraste par defaut du theme | Ratio >= 4.5:1 (WCAG AA) ; fond non blanc pur (creme, bleu pale au choix) | "Proposer des supports ecrits aeres et agrandis" | Le choix de fond colore est subjectif ; laisser le parent choisir | Norme (WCAG 1.4.3 AA) / Usage (BDA pour le fond colore) | WCAG 2.2 critere 1.4.3 : https://www.w3.org/TR/WCAG22/#contrast-minimum -- BDA Style Guide 2018. Sur le fond colore : pas de preuve d'un effet specifique. Uccula et al. 2014 (DOI: 10.3389/fpsyg.2014.00833, Frontiers in Psychology, vol. 5, art. 833 -- revue de la litterature, PMC4114255) conclut a des resultats controverses sur les overlays colores. |
| Test de robustesse WCAG 1.4.12 | pas de reglage | Aucun contenu de Jules ne doit etre coupe ni se superposer quand on impose : interligne 1.5, espacement des paragraphes 2x la taille du texte, lettres 0.12em, mots 0.16em | (pas un amenagement PAP, c'est un test technique) | Aucun | Norme (WCAG 1.4.12 AA) | WCAG 2.2 critere 1.4.12 : https://www.w3.org/TR/WCAG22/#text-spacing -- ce critere ne recommande pas de valeurs, il exige que le contenu supporte les valeurs ci-dessus sans perte. |


## Referentiel PAP -- Amenagements officiels (circulaire 2015-016)

Source : annexe PDF de la circulaire n. 2015-016 du 22-1-2015.
PDF telecharge via : https://aefe.gouv.fr/sites/default/files/asset/file/modele-plan-accompagnement-personnalise-pap-education-nationale.pdf
(verifie le 26/09/2026, titre PDF : "Plan d'accompagnement personnalise").
Les libelles ci-dessous sont les items exacts du document officiel (coches a cocher).

### Maternelle

- Organisation spatiale, temporelle et materielle
  - Veiller a la bonne installation de l'eleve dans la classe en fonction des temps d'activites
  - Visibilite et clarte des affichages
  - Mise a disposition d'outils individuels et adaptes
  - Aides visuelles pour la gestion du temps
- Realisation des taches et amenagement des supports
  - Aider a la comprehension des consignes et des informations (reformulation, ...)
  - Decomposer les consignes et informations complexes (Utiliser de preference des consignes simples)
  - Adapter et amenager les supports
  - Faciliter la prehension
  - Finaliser et faire evoluer le plan de travail et les amenagements avec l'enfant
- Aider l'eleve dans la classe
  - Accepter des modes d'expressions specifiques de l'eleve (mots, gestes...)
  - Mettre en place des dispositifs de cooperation entre eleves
  - Prendre en compte les contraintes associees : fatigue, lenteur, surcharge... (accepter de differer le travail)
  - Utiliser differents canaux dans les differentes activites (expression, psychomotricite ...)

### Elementaire

Adaptations transversales :
- Installer l'eleve face au tableau
- Veiller a la lisibilite et a la clarte de l'affichage
- Utiliser un code couleur par matiere
- Privilegier l'agenda au cahier de textes
- Verifier que l'agenda soit lisiblement renseigne
- Agrandir les formats des supports ecrits (A3)
- Donner des supports de travail ou d'exercices deja ecrits (QCM par exemple)
- Fournir des photocopies pour privilegier l'apprentissage et le sens donne
- Surligner les enonces ; surligner une ligne sur deux
- Proposer a l'eleve des outils d'aide (cache, regle ...)
- Fournir a l'eleve des moyens mnemotechniques
- S'assurer de la comprehension du vocabulaire specifique
- Aider a la comprehension par une explicitation ou une reformulation de la part de l'enseignant
- Mettre en place un tutorat par l'intermediaire d'un eleve qui lit a voix haute les consignes
- Enoncer l'objectif de la seance et en faire une synthese a la fin
- Proposer des activites qui pourront etre achevees avec succes, qui valoriseront l'eleve
- Autoriser l'utilisation d'une calculatrice simple (permettant les quatre operations) dans toutes les disciplines
- Permettre l'utilisation de l'ordinateur et de la tablette
- Permettre l'utilisation d'une clef USB
- Permettre l'utilisation de logiciel ou d'application specifique
- Permettre a l'eleve d'imprimer ses productions

Evaluations :
- Accorder un temps majore
- Donner les consignes a l'oral
- Adapter la situation, les supports de l'evaluation de facon a limiter l'ecrit : proposer des QCM ; proposer des schemas a legender ; proposer des exercices a trous, a cocher, a relier
- Autoriser differents supports (tables de calcul, fiches chronologiques, fiches memoire)
- Privilegier les evaluations sur le mode oral
- N'evaluer l'orthographe que si c'est l'objet de l'evaluation
- Ne pas penaliser le soin, l'ecriture, la realisation de figures...
- Evaluer les progres pour encourager les reussites

Lecture / langage oral :
- Recourir de maniere privilegiee a des jeux proposant un travail de la conscience phonologique
- Accentuer le travail sur la combinatoire
- Avant meme de lire le texte, lire les questions qui seront posees afin de faciliter la prise d'indices par l'eleve
- Proposer a l'eleve une lecture oralisee (enseignant ou autre eleve) ou une ecoute audio des textes supports de la seance
- Surligner des mots cles / passages importants pour faciliter la lecture de l'eleve
- Proposer a l'eleve un schema chronologique du recit

Production d'ecrits :
- Simplifier les regles en introduisant des indices visuels (pictogrammes, croquis en plus du texte)
- Adapter les quantites d'ecrit (dictee a trous, a choix, ...)
- Privilegier l'apprentissage des mots en passant par l'oral (epeler, faire le geste dans l'espace) et non par la copie
- Limiter les exigences sur l'emploi de regles precises
- Recourir a la dictee a l'enseignant
- Diminuer la quantite d'ecrit sur chaque feuille

Mathematiques :
- Autoriser l'utilisation des tables de multiplication (ou de la calculatrice) pendant les cours et les controles
- Privilegier la presentation des calculs en ligne
- Presenter les calculs en colonnes avec des reperes de couleur (ex : colonne des unites en rouge, des dizaines en bleu et des centaines en vert)
- Admettre que la reponse ne soit pas redigee si les calculs sont justes
- Ne pas sanctionner les traces en geometrie
- Laisser compter sur les doigts
- Utiliser la manipulation (pliages, objets 3D...)
- Travailler sur les "qui...qui" et les syllogismes
- Colorier les differentes colonnes des tableaux a double entree (en utilisant des couleurs differentes)
- Favoriser, autoriser la resolution des problemes avec recours a la schematisation

Langues vivantes :
- Veiller a ce que la perception de depart soit correcte : prononcer le plus distinctement possible et pas trop vite, ecrire clairement au tableau en gros caracteres
- Travailler la prononciation des sons meme exagerement
- Utiliser un enseignement multi sensoriel ; entendre, lire, voir (images), ecrire
- Grouper les mots par similitude orthographique/phonologique, faire des listes
- Utiliser des couleurs pour segmenter les mots, les phrases
- Expliquer et traduire la grammaire, les tournures de phrases

### College

(Les items du PAP college reprennent en grande partie ceux de l'elementaire. Seuls les items specifiques ou reformules sont listes.)

Pour toutes les disciplines :
- Proposer des supports ecrits aeres et agrandis (exemple : ARIAL14)
- Permettre l'utilisation de trieurs ou de pochettes a rabats
- Limiter la copie (synthese du cours photocopiee)
- Mettre en place un tutorat (prise de notes...)
- Autoriser les abreviations
- Privilegier l'agenda ainsi que l'espace numerique de travail
- Utiliser le surligneur
- Faire construire une fiche memoire et permettre a l'eleve de l'utiliser, y compris durant l'evaluation
- Proposer une aide methodologique
- Aider a l'organisation
- Definir systematiquement le vocabulaire spatial et temporel utilise
- Prendre en compte les contraintes associees (fatigue, lenteur, ...)

### Lycee

(Meme structure que le college. Items specifiques :)
- Favoriser, dans le choix des ouvrages, les livres ayant une version audio
- Proposer l'utilisation de supports numeriques
- Utiliser la schematisation en situation probleme
- Proposer a l'eleve des fiches outils (tables, definitions, theoremes ...)
- Autoriser la lecture de document avec un guide de lecture, un cache


## Recommandations non liees a un levier

| Recommandation | Source | Niveau de preuve | Note |
|---|---|---|---|
| Ne pas utiliser l'italique pour de longs passages | BDA Style Guide 2018 | Usage | Concerne le contenu des cours, pas un reglage CSS |
| Eviter le texte justifie (preferer aligne a gauche) | BDA Style Guide 2018 ; WCAG 1.4.8 AAA | Norme | Aucun `text-align: justify` dans les CSS au commit 6717025 |
| Eviter le souligne hors liens | BDA Style Guide 2018 | Usage | Convention web standard |
| Numeroter les lignes pour les textes longs | Pratique orthophoniste | Usage | Pertinent pour les cours de francais, pas pour les consignes de Jules |
| Fournir un lexique des mots difficiles | PAP circulaire 2015-016 (college : "S'assurer de la comprehension du vocabulaire specifique") | Norme (PAP) | L'outil lexique existe deja dans Jules |
| Autoriser les aides memoire et tables de reference | PAP circulaire 2015-016 (evaluations : "Autoriser differents supports") | Norme (PAP) | Concerne le contenu pedagogique, pas un levier technique |


## Notes methodologiques

### Zorzi et al. 2012

- Reference : Zorzi M, Barbiero C, Facoetti A, Lonciari I, Carrozzi M, Montico M, Bravar L, George F, Pech-Georgel C, Ziegler JC. Extra-large letter spacing improves reading in dyslexia. PNAS 2012;109(28):11455-11459.
- DOI : 10.1073/pnas.1205566109 (Crossref verifie le 26/09, titre exact : "Extra-large letter spacing improves reading in dyslexia")
- Population : 74 enfants (34 italiens, 40 francais), 8-14 ans, moyenne 10.4 ans (SD 1.5). Un deuxieme groupe de 20 enfants italiens dans l'experience 2. 30 controles italiens apparies par niveau de lecture.
- Methode : texte en Times-Roman 14 pt, espacement inter-lettres augmente de exactement 2.5 pt (exemple : 2.7 pt normal -> 5.2 pt espace). Mots separes par 3 espaces, interligne double.
- Resultats : erreurs reduites d'un facteur 2 (F(1,70)=35.16, p<0.0001) ; vitesse amelioree d'environ 0.3 syllabe/s (correspondant a 1 an de progression pour un enfant dyslexique italien). Effet specifique aux dyslexiques (pas significatif pour les controles apparies).
- Replication : partielle. Duranovic 2018 retrouve l'amelioration de la precision mais pas de la vitesse. Marinus 2016 etudiait la police Dyslexie, pas l'espacement seul. L'effet depend probablement de la langue et de la police.

### Polices speciales dys

- Wery & Diliberto 2017, DOI : 10.1007/s11881-016-0127-1 (Crossref verifie le 26/09, titre : "The effect of a specialized dyslexia font, OpenDyslexic, on reading rate and accuracy"). L'ancien DOI cite (10.1177/0022219416678407) pointait vers "Cognitive Clusters in Specific Learning Disorder", un article different.
- Kuster et al. 2018, DOI : 10.1007/s11881-017-0154-6 (Crossref verifie le 26/09, titre : "Dyslexie font does not benefit reading in children with or without dyslexia").
- Conclusion : absence de benefice mesurable d'OpenDyslexic ou Dyslexie par rapport a Arial ou Times New Roman. L'effet subjectif (preference) existe mais ne se traduit pas en performance de lecture.

### Fond colore

- Uccula et al. 2014, DOI : 10.3389/fpsyg.2014.00833 (Frontiers in Psychology, vol. 5, art. 833 -- PMC4114255, ouvert le 26/09). L'ancien DOI cite (10.1177/0264619614551622) renvoyait une erreur 404 sur doi.org et n'etait pas trouve dans Crossref.
- L'article est une revue critique de la litterature sur les overlays colores, pas une etude controlee. Les resultats sur l'efficacite des overlays colores sont controverses. On propose le fond colore comme option parent, pas comme recommandation.

### Sources dont le lien est mort ou redirige

| Source | URL citee | Etat le 26/09 | Remplacement |
|---|---|---|---|
| BDA Dyslexia Style Guide | https://www.bdadyslexia.org.uk/advice/employers/creating-a-dyslexia-friendly-workplace/dyslexia-friendly-style-guide | 404 (page supprimee, pas de redirection) | PDF 2018 : https://www.targetdyslexia.org/app/download/11639293/BDA%2BDyslexia%2BFriendly%2BContent%2B-%2BFonts.pdf -- PDF 2023 : https://www2.worc.ac.uk/disabilityanddyslexia/documents/British%20Dyslexia%20Association%20Style%20Guide.pdf |
| FALC culture.gouv.fr | https://www.culture.gouv.fr/Thematiques/Langue-francaise-et-langues-de-France/La-langue-francaise/Le-francais-facile-a-lire-et-a-comprendre-FALC | 404 | https://www.culture.gouv.fr/thematiques/culture-et-handicap/ressources-handicap/facile-a-lire-et-a-comprendre-falc-une-methode-utile |
| FFDys amenagements | https://www.ffdys.com/troubles-dys/amenagements | Redirige vers article specifique sur les amenagements d'examen (dec. 2020) | https://www.ffdys.com/actualites/amenagements-aux-examens-4-dec-2020-publication-du-decret-et-de-la-circulaire/ -- page reelle mais pas une page generale sur les amenagements pedagogiques |
| Eduscol PAP /1214/ | https://eduscol.education.fr/1214/plan-d-accompagnement-personnalise | 403 (anti-robot). Contenu probablement valide, non verifiable automatiquement. | PDF officiel de l'annexe telecharge via AEFE : https://aefe.gouv.fr/sites/default/files/asset/file/modele-plan-accompagnement-personnalise-pap-education-nationale.pdf -- Bulletin officiel : https://www.education.gouv.fr/bo/15/Hebdo5/MENE1501296C.htm |
