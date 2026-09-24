"""Moteur 'factice' : reponses programmables, pour les tests (aucun appel reseau)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from jules.llm.base import Tour


class Brique:
    def __init__(self, reglages: dict[str, Any] | None = None) -> None:
        self.appels: list[dict[str, Any]] = []
        self.regle: Callable[[str, list[Tour], str], str] = lambda s, t, m: "Réponse factice."

    def repondre(self, systeme: str, tours: list[Tour], modele: str = "principal") -> str:
        self.appels.append({"systeme": systeme, "tours": list(tours), "modele": modele})
        return self.regle(systeme, tours, modele)
