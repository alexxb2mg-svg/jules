"""Habiller un énoncé : personnages, objets, situations.

Les listes sont courtes et neutres ; les prénoms sont variés et chaque personnage porte son pronom,
pour que l'énoncé s'accorde sans effort (« Léa ... Elle veut... »).
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Personnage:
    prenom: str
    pronom: str  # « il » ou « elle »

    @property
    def Pronom(self) -> str:
        return self.pronom.capitalize()


PERSONNAGES = (
    Personnage("Léa", "elle"),
    Personnage("Nour", "elle"),
    Personnage("Inès", "elle"),
    Personnage("Sami", "il"),
    Personnage("Théo", "il"),
    Personnage("Malik", "il"),
)


@dataclass(frozen=True)
class Lots:
    """Deux sortes d'objets à répartir en lots identiques (partage, PGCD)."""

    objets_a: str
    objets_b: str
    lots: str

    @property
    def lot(self) -> str:
        return self.lots[:-1]


LOTS = (
    Lots("billes rouges", "billes bleues", "sachets"),
    Lots("stylos", "crayons", "trousses"),
    Lots("roses", "tulipes", "bouquets"),
    Lots("pommes", "poires", "paniers"),
    Lots("perles dorées", "perles argentées", "bracelets"),
)


@dataclass(frozen=True)
class Article:
    """Quelque chose qui a un prix, pour les pourcentages, les proportions, les évolutions."""

    nom: str  # avec son article : « un jean », « une console »
    le: str  # « le jean », « la console »

    @property
    def du(self) -> str:
        """« du jean », « de la console », « de l'abonnement » : le complément (le prix du jean)."""
        if self.le.startswith("le "):
            return "du " + self.le[3:]
        if self.le.startswith("la "):
            return "de " + self.le
        return "de " + self.le  # l'abonnement

    @property
    def Nom(self) -> str:
        return self.nom[0].upper() + self.nom[1:]


ARTICLES = (
    Article("un jean", "le jean"),
    Article("une console de jeux", "la console"),
    Article("un vélo", "le vélo"),
    Article("une paire de baskets", "la paire de baskets"),
    Article("un abonnement mensuel", "l'abonnement"),
    Article("un billet de train", "le billet"),
    Article("une place de concert", "la place"),
)


def personnage(rng: random.Random) -> Personnage:
    return rng.choice(PERSONNAGES)


def lots(rng: random.Random) -> Lots:
    return rng.choice(LOTS)


def article(rng: random.Random) -> Article:
    return rng.choice(ARTICLES)
