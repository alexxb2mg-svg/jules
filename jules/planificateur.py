"""Planificateur minimal : lance les taches des modules a heure fixe (heure locale), une fois par jour.

La date du dernier lancement est gardee en base : un redemarrage ne relance pas la tache,
et un PC allume apres l'heure la rattrape (sauf si la journee est finie).
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime

from jules.modules.base import Tache
from jules.stockage import Stockage

journal = logging.getLogger("jules.planificateur")
ESPACE = "planificateur"


def est_due(tache: Tache, instant: datetime, dernier_jour: str | None) -> bool:
    jour = instant.date().isoformat()
    return dernier_jour != jour and instant.strftime("%H:%M") >= tache.heure


class Planificateur:
    def __init__(
        self,
        taches: list[Tache],
        stockage: Stockage,
        periode_s: int = 30,
        veilles: list[Callable[[], object]] | None = None,
    ) -> None:
        self.taches = taches
        self.veilles = veilles or []  # verifications sans heure fixe, refaites a chaque tour
        self.stockage = stockage
        self.periode_s = periode_s
        self._arret = threading.Event()
        self._fil: threading.Thread | None = None

    def tourner_une_fois(self, instant: datetime | None = None) -> list[str]:
        instant = instant or datetime.now().astimezone()
        lancees = []
        for tache in self.taches:
            if not est_due(tache, instant, self.stockage.lire_etat(ESPACE, tache.nom)):
                continue
            self.stockage.ecrire_etat(ESPACE, tache.nom, instant.date().isoformat())
            try:
                tache.action()
                lancees.append(tache.nom)
            except Exception:
                journal.exception("Tache %s en echec", tache.nom)
        for veille in self.veilles:
            try:
                veille()
            except Exception:
                journal.exception("Veille en echec")
        return lancees

    def demarrer(self) -> None:
        def boucle() -> None:
            while not self._arret.wait(self.periode_s):
                self.tourner_une_fois()

        self._fil = threading.Thread(target=boucle, name="jules-planificateur", daemon=True)
        self._fil.start()

    def arreter(self) -> None:
        self._arret.set()
