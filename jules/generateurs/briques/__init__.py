"""Briques communes aux générateurs d'exercices : ce qui se répète d'une notion à l'autre.

Un fichier par famille (voir docs/GENERATEURS-CONTRAT.md) :

  tirage.py     tirer des valeurs sous contraintes, avec un nombre d'essais borné
  format_fr.py  écrire les nombres et les calculs comme on les écrit en classe
  habillage.py  personnages, objets, situations pour habiller un énoncé
  pieges.py     construire les pièges et écarter ceux qui ne se déclencheraient jamais
  exercice.py   assembler et vérifier un exercice v2, choisir un palier de difficulté
  notion.py     le point d'entrée commun `generer(...)` d'une notion

Une notion importe ce dont elle a besoin ; elle ne recopie jamais une brique.
"""

from __future__ import annotations

from jules.generateurs.briques.exercice import DIFFICULTES_PERMISES, ErreurGeneration, exercice_v2, palier
from jules.generateurs.briques.notion import ErreurParametre, Variante, generer_notion
from jules.generateurs.briques.pieges import piege_contient, piege_diagnostic, piege_valeur

__all__ = [
    "DIFFICULTES_PERMISES",
    "ErreurGeneration",
    "ErreurParametre",
    "Variante",
    "exercice_v2",
    "generer_notion",
    "palier",
    "piege_contient",
    "piege_diagnostic",
    "piege_valeur",
]
