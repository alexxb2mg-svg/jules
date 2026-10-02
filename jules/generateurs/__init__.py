"""Générateurs d'exercices déterministes, un par notion du référentiel.

Un générateur fabrique un exercice au format fiches v2 (docs/FICHES-V2.md) à partir d'une graine :
même graine, même exercice ; autre graine, autre variante. Aucune IA : le code tire les valeurs,
calcule la réponse, rédige l'énoncé, les indices, les pièges et la solution. Le correcteur
(jules/fiches/correction.py) et le parcours (jules/fiches/parcours.py) servent ces exercices tels quels.

Chaque module de générateur expose `NOTION` (identifiant du référentiel), `VARIANTES` et
`generer(graine, difficulte, variante=None) -> dict`. Un module déposé dans `mathematiques/` est
enregistré tout seul (découverte par `pkgutil`) : aucune liste à tenir, donc aucun conflit entre PR de notion.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from typing import Any

from jules.generateurs import mathematiques

Generateur = Callable[..., dict[str, Any]]

_PAQUETS = (mathematiques,)  # un paquet par matière ; une notion = un module qui expose NOTION


def _decouvrir() -> dict[str, Any]:
    """Les modules de générateurs, trouvés dans les paquets de matière (plus de liste tenue à la main).

    Ordre stable : alphabétique par nom de module. Deux modules qui déclarent la même notion : erreur.
    """
    modules: dict[str, Any] = {}
    for paquet in _PAQUETS:
        for info in sorted(pkgutil.iter_modules(paquet.__path__), key=lambda i: i.name):
            if info.name.startswith("_"):
                continue
            module = importlib.import_module(f"{paquet.__name__}.{info.name}")
            notion = getattr(module, "NOTION", None)
            if notion is None:
                continue
            if notion in modules:
                raise ValueError(
                    f"notion {notion!r} déclarée deux fois ({modules[notion].__name__}, {module.__name__})"
                )
            modules[notion] = module
    return modules


MODULES: dict[str, Any] = _decouvrir()
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
