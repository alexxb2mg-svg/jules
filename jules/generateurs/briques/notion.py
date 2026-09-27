"""Le point d'entrée commun d'une notion : graine, difficulté, choix de la variante.

Un module de notion déclare `NOTION`, `VARIANTES` (tuple de noms) et une fonction par variante
`(rng, difficulte) -> exercice`, puis délègue :

    def generer(graine, difficulte=1, variante=None):
        return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)

La graine est mélangée au nom de la notion : la graine 7 ne donne pas « le même exercice » d'une
notion à l'autre, et un changement de nom de notion change tous les tirages (voulu : l'identifiant
fait partie du contrat).
"""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping
from typing import Any

from jules.generateurs.briques.exercice import DIFFICULTES_PERMISES

Variante = Callable[[random.Random, int], dict[str, Any]]


class ErreurParametre(ValueError):
    """Difficulté ou variante hors contrat."""


def generer_notion(
    notion: str, variantes: Mapping[str, Variante], graine: int, difficulte: int = 1, variante: str | None = None
) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    if difficulte not in DIFFICULTES_PERMISES:
        raise ErreurParametre(f"difficulte vaut 1, 2 ou 3, pas {difficulte!r}")
    rng = random.Random(f"{notion}/{graine}")  # noqa: S311 - pas de cryptographie, un tirage rejouable
    choisie = variante or rng.choice(tuple(variantes))
    if choisie not in variantes:
        raise ErreurParametre(f"variante inconnue : {choisie!r} ({', '.join(variantes)})")
    return variantes[choisie](rng, difficulte)
