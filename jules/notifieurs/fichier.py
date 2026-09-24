"""Notifieur 'fichier' : ecrit chaque notification dans donnees/notifications/AAAA-MM-JJ.log.

Toujours actif : c'est la trace de ce qui a ete envoye (ou aurait du l'etre).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from jules.config import Config


class Brique:
    def __init__(self, config: Config, reglages: dict[str, Any]) -> None:
        self.dossier = config.donnees / "notifications"
        self.dossier.mkdir(parents=True, exist_ok=True)

    def envoyer(self, sujet: str, texte: str, urgent: bool = False) -> None:
        instant = datetime.now().astimezone()
        drapeau = " [URGENT]" if urgent else ""
        bloc = f"=== {instant:%Y-%m-%d %H:%M:%S}{drapeau} {sujet}\n{texte}\n\n"
        with (self.dossier / f"{instant:%Y-%m-%d}.log").open("a", encoding="utf-8") as f:
            f.write(bloc)
