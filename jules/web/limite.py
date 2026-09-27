"""Limite d'essais du code d'acces (jules/web/app.py, route ``POST /api/session``).

Deux compteurs a fenetre glissante : un par adresse IP (contre le bourrinage depuis un seul
poste) et un global, toutes IP confondues (contre plusieurs appareils d'un meme reseau qui se
partagent les essais pour multiplier les fenetres). Le plafond global est plus large que celui
par IP : il ne doit pas gener une famille nombreuse sur le meme LAN qui se trompe une fois
chacun, seulement une attaque distribuee.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class LimiteEssais:
    """Compte les echecs de code sur une fenetre glissante, par IP et globalement."""

    def __init__(self, essais_max_ip: int, essais_max_global: int, fenetre_s: float = 600) -> None:
        self.essais_max_ip = essais_max_ip
        self.essais_max_global = essais_max_global
        self.fenetre_s = fenetre_s
        self._par_ip: dict[str, deque[float]] = defaultdict(deque)
        self._globale: deque[float] = deque()

    def _purger(self, fenetre: deque[float], maintenant: float) -> None:
        while fenetre and fenetre[0] < maintenant - self.fenetre_s:
            fenetre.popleft()

    def autorise(self, adresse: str, *, maintenant: float | None = None) -> bool:
        """Faux si l'adresse ou l'ensemble des adresses a deja atteint son plafond d'essais."""
        instant = time.time() if maintenant is None else maintenant
        fenetre_ip = self._par_ip[adresse]
        self._purger(fenetre_ip, instant)
        self._purger(self._globale, instant)
        return len(fenetre_ip) < self.essais_max_ip and len(self._globale) < self.essais_max_global

    def enregistrer_echec(self, adresse: str, *, maintenant: float | None = None) -> None:
        """A appeler apres un code refuse : compte l'essai pour l'IP et pour le total."""
        instant = time.time() if maintenant is None else maintenant
        self._par_ip[adresse].append(instant)
        self._globale.append(instant)
