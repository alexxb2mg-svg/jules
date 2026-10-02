"""Lecture YAML rapide et sure, partagee par tout le projet.

Le lecteur C de PyYAML (CSafeLoader, adosse a libyaml) donne EXACTEMENT les memes donnees que le lecteur
Python (SafeLoader), environ 10 fois plus vite : verifie le 28/09/2026 sur les 1 241 fichiers YAML du depot
et de jules-bibliotheques, 0 difference (docs/PERFORMANCES.md). C'est le choix deja fait par
jules/bibliotheques.py ; ce module le rend commun.

Si libyaml n'est pas installe (PyYAML compile sans lui), on retombe sur le lecteur Python : meme resultat,
plus lent. Les deux sont des lecteurs « surs » (aucune construction d'objet Python arbitraire).
"""

from __future__ import annotations

from typing import Any

import yaml

LECTEUR = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
RAPIDE = LECTEUR is not yaml.SafeLoader


def charger(texte: str) -> Any:
    """Equivalent de yaml.safe_load(texte), avec le lecteur C quand il existe."""
    return yaml.load(texte, Loader=LECTEUR)  # noqa: S506 - CSafeLoader/SafeLoader sont des lecteurs surs
