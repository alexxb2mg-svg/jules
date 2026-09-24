"""Moteur 'demo' : aucun service d'IA, aucune cle, aucun reseau.

Il sert a decouvrir l'interface juste apres l'installation. Il repond toujours la meme
chose (en guidant, sans donner de reponse) et rappelle comment brancher une vraie IA.
Les analyses de fond (suivi, vigilance) recoivent un JSON neutre.
"""

from __future__ import annotations

from typing import Any

from jules.llm.base import Tour

MESSAGE = (
    "Je tourne en **mode démo** : je ne suis pas encore relié à une intelligence artificielle, "
    "donc je ne peux pas vraiment t'aider pour l'instant.\n\n"
    "Pour l'adulte qui a installé Jules : lance `python lancer.py installer` pour choisir "
    "une IA (un modèle gratuit sur l'ordinateur avec Ollama, ou une clé API)."
)


class Brique:
    def __init__(self, reglages: dict[str, Any] | None = None) -> None:
        self.reglages = reglages or {}

    def repondre(self, systeme: str, tours: list[Tour], modele: str = "principal") -> str:
        if modele == "principal":
            return MESSAGE
        if "JSON" in systeme:
            return '{"niveau": "aucun", "motif": "", "statut": "hors_scolaire", "notion": "", "titre": "Démo"}'
        return "Mode démo : aucune synthèse."
