"""Chargement des briques par convention : famille/<id>.py expose une classe `Brique`.

Ajouter une brique = deposer jules/<famille>/<id>.py puis citer l'id dans config.yaml.
"""

from __future__ import annotations

import importlib
from typing import Any

FAMILLES = ("modules", "notifieurs", "llm")


class ErreurBrique(RuntimeError):
    pass


def classe_brique(famille: str, identifiant: str) -> type[Any]:
    if famille not in FAMILLES:
        raise ErreurBrique(f"Famille inconnue : {famille}")
    if not identifiant.replace("_", "").isalnum():
        raise ErreurBrique(f"Identifiant de brique invalide : {identifiant!r}")
    try:
        module = importlib.import_module(f"jules.{famille}.{identifiant}")
    except ModuleNotFoundError as err:
        raise ErreurBrique(f"Brique introuvable : jules/{famille}/{identifiant}.py") from err
    classe = getattr(module, "Brique", None)
    if classe is None:
        raise ErreurBrique(f"jules/{famille}/{identifiant}.py ne definit pas de classe Brique")
    return classe
