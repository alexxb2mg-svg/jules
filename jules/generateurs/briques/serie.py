"""Séries statistiques : tirer une série dans un contexte, l'écrire, calculer ses indicateurs en exact.

Une série s'écrit comme en classe, valeurs séparées par des points-virgules (« 12 ; 7 ; 15 ») : la
virgule est réservée aux décimaux. Les indicateurs sont rendus en `Fraction` : jamais de flottant,
l'arrondi se décide dans la notion.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction

from jules.generateurs.briques.format_fr import nombre_fr


@dataclass(frozen=True)
class ContexteSerie:
    """Ce que mesure une série, et la plage de valeurs vraisemblables (entiers)."""

    quoi: str  # « les notes sur 20 obtenues à un contrôle » : complète « Voici ... »
    bas: int
    haut: int
    unite: str = ""  # « °C », « cm » : écrit après chaque valeur citée seule

    def valeur(self, x: Fraction | int) -> str:
        """Une valeur citée avec son unité : « 18 °C », « 12,5 »."""
        return f"{nombre_fr(x)} {self.unite}".rstrip()


CONTEXTES_SERIE = (
    ContexteSerie("les notes sur 20 obtenues à un contrôle par des élèves", 4, 20),
    ContexteSerie("les températures maximales, en °C, relevées chaque jour", 8, 31, "°C"),
    ContexteSerie("les nombres de pompes réalisées en une minute par des élèves", 8, 45),
    ContexteSerie("les masses, en kg, de valises pesées à l'enregistrement", 7, 23, "kg"),
    ContexteSerie("les nombres de points marqués par une équipe de handball à chaque match", 18, 39),
    ContexteSerie("les durées, en minutes, du trajet domicile-collège d'élèves", 5, 40, "min"),
    ContexteSerie("les nombres de livres lus dans l'année par des élèves", 0, 16),
)


def contexte_serie(rng: random.Random) -> ContexteSerie:
    return rng.choice(CONTEXTES_SERIE)


def tirer_valeurs(rng: random.Random, n: int, bas: int, haut: int) -> list[int]:
    """n entiers entre bas et haut (répétitions possibles), dans l'ordre du tirage : une série non rangée."""
    return [rng.randint(bas, haut) for _ in range(n)]


def serie_fr(valeurs: list[int] | list[Fraction]) -> str:
    """[12, 7, 15] -> « 12 ; 7 ; 15 »."""
    return " ; ".join(nombre_fr(v) for v in valeurs)


def total(valeurs: list[int] | list[Fraction]) -> Fraction:
    return Fraction(sum(valeurs))


def moyenne(valeurs: list[int] | list[Fraction]) -> Fraction:
    return total(valeurs) / len(valeurs)


def mediane(valeurs: list[int] | list[Fraction]) -> Fraction:
    """Valeur du milieu de la série rangée ; effectif pair : moyenne des deux valeurs centrales."""
    rangees = sorted(Fraction(v) for v in valeurs)
    n = len(rangees)
    if n % 2:
        return rangees[n // 2]
    return (rangees[n // 2 - 1] + rangees[n // 2]) / 2


def etendue(valeurs: list[int] | list[Fraction]) -> Fraction:
    return Fraction(max(valeurs)) - Fraction(min(valeurs))


def moyenne_ponderee(valeurs: list[int], effectifs: list[int]) -> Fraction:
    """Somme des (valeur × effectif) divisée par l'effectif total."""
    return Fraction(sum(v * e for v, e in zip(valeurs, effectifs, strict=True)), sum(effectifs))


def decimal_exact(x: Fraction, chiffres: int = 2) -> bool:
    """x s'écrit-il exactement avec au plus `chiffres` chiffres après la virgule ?"""
    return (x * 10**chiffres).denominator == 1


def arrondi_dixieme(x: Fraction) -> Fraction:
    """Arrondi au dixième le plus proche, en exact (demi vers le haut, comme en classe)."""
    return Fraction(int(x * 10 + Fraction(1, 2)) if x >= 0 else -int(-x * 10 + Fraction(1, 2)), 10)
