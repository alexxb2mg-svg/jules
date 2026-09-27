"""Assembler un exercice v2 et le vérifier avant de le rendre.

`exercice_v2(...)` est le seul constructeur : il filtre les pièges (briques/pieges.py), puis passe
l'exercice au vérificateur des fiches v2 (jules/fiches/schema.py). Un exercice généré non conforme
lève ErreurGeneration avec la liste des manquements et la graine : on corrige le générateur, jamais
le vérificateur.
"""

from __future__ import annotations

from typing import Any, TypeVar

from jules.fiches.schema import _verifier_exercice
from jules.generateurs.briques.pieges import Piege, filtrer_pieges

P = TypeVar("P")

DIFFICULTES_PERMISES = (1, 2, 3)


class ErreurGeneration(ValueError):
    """L'exercice fabriqué ne respecte pas le contrat v2 (bug du générateur, pas de l'élève).

    `exercice` porte l'exercice fautif tel qu'il allait être rendu, pour voir d'un coup d'œil ce qui fuit.
    """

    def __init__(self, message: str, exercice: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.exercice = exercice or {}


def palier(difficultes: dict[int, P], difficulte: int) -> P:
    """Le réglage d'un niveau de difficulté, avec un message clair si le niveau n'existe pas."""
    if difficulte not in DIFFICULTES_PERMISES:
        raise ValueError(f"difficulte vaut 1, 2 ou 3, pas {difficulte!r}")
    if difficulte not in difficultes:
        raise ValueError(f"pas de réglage pour la difficulté {difficulte} (définis : {sorted(difficultes)})")
    return difficultes[difficulte]


def exercice_v2(
    *,
    id: str,
    type: str,
    difficulte: int,
    enonce: str,
    reponse: dict[str, Any],
    indices: dict[str, str],
    pieges: list[Piege],
    solution: str,
    lieu: str = "",
) -> dict[str, Any]:
    """Un exercice v2 vérifié. `lieu` (notion/variante/graine) enrichit le message d'erreur."""
    ex: dict[str, Any] = {
        "id": id,
        "type": type,
        "difficulte": difficulte,
        "enonce": enonce,
        "reponse": reponse,
        "indices": dict(indices),
        "pieges": [],
        "solution": solution,
    }
    ex["pieges"] = filtrer_pieges(ex, pieges)
    erreurs: list[str] = []
    _verifier_exercice(ex, lieu or id, erreurs)
    if erreurs:
        raise ErreurGeneration("\n".join(erreurs), ex)
    return ex
