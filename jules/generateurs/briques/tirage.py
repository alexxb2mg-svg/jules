"""Tirer des valeurs sous contraintes.

Tout tirage passe par le `random.Random` reçu du générateur (jamais le module `random`), pour que
la même graine redonne le même exercice. Un tirage sous contrainte est une boucle « tirer, tester »
bornée : si la contrainte est impossible, on le sait tout de suite au lieu de boucler sans fin.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from fractions import Fraction
from typing import TypeVar

T = TypeVar("T")

ESSAIS_MAX = 10_000


def tirer(rng: random.Random, fabrique: Callable[[], T], accepte: Callable[[T], bool], essais: int = ESSAIS_MAX) -> T:
    """La première valeur de `fabrique()` qui vérifie `accepte`, ou ValueError après `essais` tirages."""
    for _ in range(essais):
        valeur = fabrique()
        if accepte(valeur):
            return valeur
    raise ValueError(f"aucune valeur acceptable en {essais} tirages : la contrainte est trop stricte")


def entier_produit_de_premiers(rng: random.Random, nb_facteurs: int, premiers: Sequence[int], maximum: int) -> int:
    """Un entier produit d'exactement `nb_facteurs` nombres premiers (avec répétition), au plus `maximum`.

    Au moins deux nombres premiers distincts : une puissance d'un seul premier (27 = 3³) rend illisibles
    les indices, où le facteur apparaît forcément, et n'exerce pas les divisions successives.
    """

    def fabrique() -> list[int]:
        return [rng.choice(premiers) for _ in range(nb_facteurs)]

    tires = tirer(rng, fabrique, lambda t: math.prod(t) <= maximum and len(set(t)) >= 2)
    return math.prod(tires)


def couple_premiers_entre_eux(rng: random.Random, minimum: int, maximum: int) -> tuple[int, int]:
    """Deux entiers distincts de [minimum, maximum], premiers entre eux (pour un PGCD ou une fraction voulus)."""

    def fabrique() -> tuple[int, int]:
        x, y = rng.sample(range(minimum, maximum + 1), 2)
        return x, y

    return tirer(rng, fabrique, lambda c: math.gcd(*c) == 1)


def entier_multiple(rng: random.Random, pas: int, minimum: int, maximum: int) -> int:
    """Un multiple de `pas` dans [minimum, maximum] (prix « ronds », effectifs, durées...)."""
    bas = -(-minimum // pas)  # premier multiple >= minimum
    haut = maximum // pas
    if haut < bas:
        raise ValueError(f"aucun multiple de {pas} entre {minimum} et {maximum}")
    return rng.randint(bas, haut) * pas


def collision(reponse: object, *valeurs: object) -> bool:
    """La réponse apparaît-elle, telle que le vérificateur la lit, dans une des valeurs citées par l'énoncé ?

    Le vérificateur des fiches découpe les textes en mots (« 1,25 » devient « 1 25 », « 1 150 € » devient
    « 1 150 ») : une réponse 25 fuit dès qu'un indice cite le coefficient 1,25, une réponse 90 fuit si le
    prix de départ est 90 €. Un générateur teste ses tirages avec cette fonction et retire ceux qui
    collent, plutôt que de tordre ses indices.
    """
    from jules.fiches.schema import cle_texte  # import tardif : schema importe aussi le correcteur
    from jules.generateurs.briques.format_fr import nombre_fr

    def cle(valeur: object) -> str:
        texte = (
            nombre_fr(valeur)
            if isinstance(valeur, int | float | Fraction) and not isinstance(valeur, bool)
            else str(valeur)
        )
        return f" {cle_texte(texte)} "

    attendu = cle(reponse)
    return any(attendu in cle(v) for v in valeurs)
