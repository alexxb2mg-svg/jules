"""Modele de l'eleve : ce que Jules croit savoir de l'eleve, avec quelle confiance, et comment il se corrige.

Paquet de calcul pur : aucune entree-sortie, aucun appel d'IA, aucun acces au stockage. Tout ce qui
touche la base, le modele de langage ou le prompt vit dans la brique `jules/modules/modele_eleve.py`.
Le contrat complet (formules, parametres, criteres d'acceptation) est dans docs/MODELE-ELEVE.md.

Les cinq etages, du plus rapide au plus lent :

  observations  un echange -> des faits constates (tentative juste/fausse, niveau d'aide recu...)
                Le modele de langage CONSTATE, les maths JUGENT : on ne lui demande jamais un nombre.
  estimateurs   faits -> probabilite de maitrise par notion (inference bayesienne, capteurs ponderes)
  oubli         maitrise + temps -> probabilite que ca tienne sans aide (courbe de FSRS-4.5)
  politique     etat de seance -> reglage du comportement de Jules pour le message suivant
  calibration   epreuves sans aide -> fiabilite reelle de chaque capteur POUR CET ELEVE (EM, MAP)
  carnet        grosses surprises -> lecons ecrites, verifiees par les epreuves suivantes, oubliees sinon

L'epreuve sans aide (module `epreuve`) est la seule verite terrain. Tout le reste est un indice.
"""
