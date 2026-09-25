"""Mesures : Jules juge-t-il bien ? (docs/MODELE-ELEVE.md, §7.4)

Regles de score propres (Gneiting et Raftery, 2007) : un modele ne les ameliore qu'en predisant mieux.
Fonctions pures, entierement ecrites : elles servent de reference aux autres lots.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

EPS = 1e-9


def _verifier(predictions: Sequence[float], resultats: Sequence[int]) -> None:
    if len(predictions) != len(resultats):
        raise ValueError("autant de predictions que de resultats")
    if any(not 0 <= p <= 1 for p in predictions):
        raise ValueError("une prediction est une probabilite dans [0, 1]")
    if any(y not in (0, 1) for y in resultats):
        raise ValueError("un resultat vaut 0 ou 1")


def brier(predictions: Sequence[float], resultats: Sequence[int]) -> float:
    """Moyenne de (pi - y)^2. 0 parfait, 0,25 pour qui repond toujours 0,5."""
    _verifier(predictions, resultats)
    if not predictions:
        return math.nan
    return sum((p - y) ** 2 for p, y in zip(predictions, resultats, strict=True)) / len(predictions)


def perte_log(pi: float, y: int) -> float:
    """-ln P(y) : la « surprise » d'une epreuve (§8.1)."""
    p = min(1 - EPS, max(EPS, pi))
    return -math.log(p if y else 1 - p)


def perte_log_moyenne(predictions: Sequence[float], resultats: Sequence[int]) -> float:
    _verifier(predictions, resultats)
    if not predictions:
        return math.nan
    return sum(perte_log(p, y) for p, y in zip(predictions, resultats, strict=True)) / len(predictions)


def competence(score: float, score_reference: float) -> float:
    """1 - score / reference. > 0 : mieux que la reference ; < 0 : pire."""
    if score_reference == 0:
        return math.nan
    return 1 - score / score_reference


def brier_climatologie(resultats: Sequence[int]) -> float:
    """Brier de la reference « toujours le taux de reussite moyen » : p(1 - p)."""
    if not resultats:
        return math.nan
    p = sum(resultats) / len(resultats)
    return p * (1 - p)


@dataclass(frozen=True)
class Classe:
    borne_basse: float
    borne_haute: float
    effectif: int
    prediction_moyenne: float
    frequence_observee: float


def table_fiabilite(predictions: Sequence[float], resultats: Sequence[int], classes: int = 5) -> list[Classe]:
    """Classes de largeur egale sur [0, 1] ; les classes vides sont omises."""
    _verifier(predictions, resultats)
    seaux: list[list[tuple[float, int]]] = [[] for _ in range(classes)]
    for p, y in zip(predictions, resultats, strict=True):
        seaux[min(classes - 1, int(p * classes))].append((p, y))
    table = []
    for i, seau in enumerate(seaux):
        if not seau:
            continue
        table.append(
            Classe(
                borne_basse=i / classes,
                borne_haute=(i + 1) / classes,
                effectif=len(seau),
                prediction_moyenne=sum(p for p, _ in seau) / len(seau),
                frequence_observee=sum(y for _, y in seau) / len(seau),
            )
        )
    return table


def ece(predictions: Sequence[float], resultats: Sequence[int], classes: int = 5) -> float:
    """Erreur de calibration attendue : moyenne ponderee des |prediction moyenne - frequence observee|."""
    n = len(predictions)
    if n == 0:
        return math.nan
    return sum(
        c.effectif / n * abs(c.prediction_moyenne - c.frequence_observee)
        for c in table_fiabilite(predictions, resultats, classes)
    )
