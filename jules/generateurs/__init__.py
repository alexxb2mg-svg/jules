"""Générateurs d'exercices déterministes, un par notion du référentiel.

Un générateur fabrique un exercice au format fiches v2 (docs/FICHES-V2.md) à partir d'une graine :
même graine, même exercice ; autre graine, autre variante. Aucune IA : le code tire les valeurs,
calcule la réponse, rédige l'énoncé, les indices, les pièges et la solution. Le correcteur
(jules/fiches/correction.py) et le parcours (jules/fiches/parcours.py) servent ces exercices tels quels.

Chaque module de générateur expose `NOTION` (identifiant du référentiel), `VARIANTES` et
`generer(graine, difficulte, variante=None) -> dict`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from jules.generateurs.mathematiques import (
    calcul_nombres_rationnels,
    developper_factoriser_reduire,
    ecritures_et_comparaison_nombres,
    equations_premier_degre_et_produits,
    fractions_irreductibles,
    multiples_diviseurs_division_euclidienne,
    nombres_premiers_decomposition,
    pourcentages_coefficient_multiplicateur,
    problemes_mise_en_equation,
    racine_carree,
)

Generateur = Callable[..., dict[str, Any]]

MODULES: dict[str, Any] = {
    module.NOTION: module
    for module in (
        nombres_premiers_decomposition,
        pourcentages_coefficient_multiplicateur,
        multiples_diviseurs_division_euclidienne,
        racine_carree,
        equations_premier_degre_et_produits,
        problemes_mise_en_equation,
        calcul_nombres_rationnels,
        fractions_irreductibles,
        ecritures_et_comparaison_nombres,
        developper_factoriser_reduire,
    )
}
GENERATEURS: dict[str, Generateur] = {notion: module.generer for notion, module in MODULES.items()}


def generer(notion: str, graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 pour cette notion, ou KeyError si aucun générateur ne la couvre."""
    return GENERATEURS[notion](graine, difficulte, variante)


def serie_generee(notion: str, graine: int, prerequis: list[str] | None = None) -> dict[str, Any]:
    """Une « fiche » minimale faite d'exercices générés, que le parcours sert comme une fiche v2.

    Une série parcourt chaque variante du générateur, en difficulté croissante (1, 2, 3, 1, 2, 3...),
    avec une graine dérivée par exercice. Les identifiants restent uniques dans la série.
    """
    module = MODULES[notion]
    exercices: list[dict[str, Any]] = []
    vus: set[str] = set()
    for rang, variante in enumerate(module.VARIANTES):
        difficulte = rang % 3 + 1
        ex = module.generer(graine * 100 + rang * 10, difficulte, variante)
        for essai in range(1, 20):  # au cas où deux variantes tirent le même identifiant
            if ex["id"] not in vus:
                break
            ex = module.generer(graine * 100 + rang * 10 + essai, difficulte, variante)
        vus.add(ex["id"])
        exercices.append(ex)
    return {
        "format": 2,
        "notion": notion,
        "generee": True,
        "graine": graine,
        "prerequis": prerequis or [],
        "exercices": exercices,
    }
