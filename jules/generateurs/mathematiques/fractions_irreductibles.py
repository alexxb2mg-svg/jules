"""Générateur déterministe pour la notion `fractions-irreductibles` (mathématiques, 3e).

Trois variantes :

  - simplifier    : rendre une fraction irréductible                       (nombre, fraction_irreductible)
  - irreductible  : la fraction donnée est-elle déjà irréductible ?        (choix : oui / non)
  - pgcd          : le PGCD du numérateur et du dénominateur d'une paire   (nombre, entier)

Tout est calculé : un couple d'entiers premiers entre eux (p, q) et un facteur commun g donnent
une fraction a/b = (g×p)/(g×q) dont le PGCD est g et la forme irréductible p/q. Les fonctions de
calcul viennent du correcteur (jules/fiches/correction.py : `decomposer`), les écritures et le
tirage sous contrainte des briques communes (jules/generateurs/briques/), comme pour
`nombres-premiers-decomposition` (qui a une variante `fraction` voisine, mais isolée : ici la notion
est celle de fraction irréductible en tant que telle, avec sa propre progression de paliers).
"""

from __future__ import annotations

import random
from typing import Any

from jules.fiches.correction import decomposer
from jules.generateurs.briques import (
    exercice_v2,
    generer_notion,
    palier,
    piege_contient,
    piege_diagnostic,
    piege_valeur,
)
from jules.generateurs.briques.format_fr import joli_produit, produit_developpe
from jules.generateurs.briques.tirage import collision, couple_premiers_entre_eux, tirer

NOTION = "fractions-irreductibles"
VARIANTES = ("simplifier", "irreductible", "pgcd")

# Paliers communs à `simplifier` et `irreductible` : facteurs communs possibles, plus grand cofacteur,
# et un plafond sur le dénominateur final (les dénominateurs restent petits en difficulté 1, et le
# PGCD peut avoir plusieurs facteurs premiers en difficulté 3, comme demandé).
_PALIERS_FACTEURS = {
    1: ((2, 3, 4, 5), 9, 29),
    2: ((6, 7, 8, 9, 10, 12), 12, 99),
    3: ((12, 18, 20, 24, 28, 30, 36, 40, 42, 45, 48, 60), 15, 400),
}

_PALIERS_PGCD = {
    1: ((2, 3, 4, 5, 6), 9, 60),
    2: ((6, 8, 9, 10, 12, 14, 15), 15, 150),
    3: ((12, 18, 20, 24, 28, 30, 36, 40, 42, 45, 48, 60), 8, 480),
}


def _tirer_fraction(rng: random.Random, facteurs_g: tuple[int, ...], max_q: int, plafond: int) -> tuple[int, int, int]:
    """Un couple (p, q) premiers entre eux et un facteur commun g, tel que g×max(p, q) <= plafond."""
    g = rng.choice(facteurs_g)
    q_max = max(2, min(max_q, plafond // g))
    p, q = couple_premiers_entre_eux(rng, 2, q_max)
    return g, p, q


# --- variante 1 : simplifier ------------------------------------------------------------------------


def _simplifier(rng: random.Random, difficulte: int) -> dict[str, Any]:
    facteurs_g, max_q, plafond = palier(_PALIERS_FACTEURS, difficulte)
    g, p, q = _tirer_fraction(rng, facteurs_g, max_q, plafond)
    a, b = g * p, g * q
    diviseur_partiel = decomposer(g)[0][0]  # un premier facteur de g : un diviseur commun, pas forcément g
    pieges = [
        piege_valeur(f"{q}/{p}", "Tu as échangé le numérateur et le dénominateur. Le numérateur reste en haut."),
    ]
    if diviseur_partiel < g:
        a_partiel, b_partiel = a // diviseur_partiel, b // diviseur_partiel
        pieges.append(
            piege_valeur(
                f"{a_partiel}/{b_partiel}",
                f"Tu as bien divisé par {diviseur_partiel}, mais {a_partiel} et {b_partiel} ont encore "
                "un diviseur commun : ce n'est pas fini, continue à simplifier.",
            )
        )
    pieges.append(
        piege_diagnostic(
            "non_irreductible",
            "Ta fraction est égale à celle de départ, mais on peut encore la simplifier : "
            "cherche un diviseur commun plus grand.",
        )
    )
    pieges.append(
        piege_diagnostic(
            "pas_une_fraction",
            "La valeur est bonne, mais on attend une fraction irréductible (numérateur/dénominateur), "
            "pas un nombre décimal.",
        )
    )
    pieges.append(
        piege_diagnostic(
            "valeur_fausse",
            "Ta fraction n'a plus la même valeur que celle de départ. On divise le numérateur ET le "
            "dénominateur par le même nombre.",
        )
    )
    return exercice_v2(
        id=f"simplifier-{a}-{b}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Simplifie la fraction {a}/{b} jusqu'à ce qu'elle soit irréductible.",
        reponse={"valeur": f"{p}/{q}", "forme": "fraction_irreductible"},
        indices={
            "relance": f"Cherche un nombre qui divise à la fois {a} et {b}.",
            "methode": "Divise le numérateur et le dénominateur par un même diviseur commun, puis recommence "
            "tant qu'il en existe un autre. La fraction est irréductible quand il n'en reste plus.",
            "etape": f"{diviseur_partiel} divise à la fois {a} et {b}. Divise les deux par {diviseur_partiel}, "
            "puis regarde si on peut continuer.",
        },
        pieges=pieges,
        solution=f"{a} et {b} ont pour plus grand diviseur commun {g}. {a}/{b} = ({p} × {g})/({q} × {g}) = {p}/{q}.",
        lieu=f"{NOTION}/simplifier/{a}-{b}",
    )


# --- variante 2 : irréductible ou non (choix) --------------------------------------------------------

_OPTIONS_IRREDUCTIBLE = (
    {"id": "oui", "texte": "Oui, elle est irréductible"},
    {"id": "non", "texte": "Non, on peut encore la simplifier"},
)


def _irreductible(rng: random.Random, difficulte: int) -> dict[str, Any]:
    facteurs_g, max_q, plafond = palier(_PALIERS_FACTEURS, difficulte)
    reductible = rng.choice((True, False))
    if reductible:
        g, p, q = _tirer_fraction(rng, facteurs_g, max_q, plafond)
    else:
        g = 1
        _, p, q = _tirer_fraction(rng, (1,), max_q, plafond)
    a, b = g * p, g * q
    bonnes = ["non"] if reductible else ["oui"]
    if reductible:
        diviseur_commun = decomposer(g)[0][0]
        pieges = [
            piege_contient(
                ["oui"],
                f"{a} et {b} sont pourtant tous les deux divisibles par {diviseur_commun} : ce n'est pas irréductible.",
            )
        ]
        solution = (
            f"{a} et {b} sont tous deux divisibles par {diviseur_commun} : la fraction n'est pas irréductible "
            f"(on peut la simplifier pour obtenir {p}/{q})."
        )
    else:
        pieges = [
            piege_contient(
                ["non"],
                f"Décompose {a} et {b} en facteurs premiers : ils n'ont aucun facteur premier en commun, "
                "donc la fraction est bien irréductible.",
            )
        ]
        solution = (
            f"{a} = {produit_developpe(a)} et {b} = {produit_developpe(b)} n'ont aucun facteur premier commun : "
            "la fraction est irréductible."
        )
    pieges.append(piege_diagnostic("incomplet", "Réponds par oui ou par non."))
    return exercice_v2(
        id=f"irreductible-{a}-{b}",
        type="choix",
        difficulte=difficulte,
        enonce=f"La fraction {a}/{b} est-elle irréductible ?",
        reponse={"options": list(_OPTIONS_IRREDUCTIBLE), "bonnes": bonnes},
        indices={
            "relance": f"Cherche un diviseur commun à {a} et {b}, autre que 1.",
            "methode": "Décompose le numérateur et le dénominateur en facteurs premiers : s'ils n'ont aucun "
            "facteur premier commun, la fraction est irréductible.",
            "etape": f"{a} = {produit_developpe(a)} et {b} = {produit_developpe(b)}. "
            "Un facteur apparaît-il dans les deux décompositions ?",
        },
        pieges=pieges,
        solution=solution,
        lieu=f"{NOTION}/irreductible/{a}-{b}",
    )


# --- variante 3 : PGCD (nombre entier) ----------------------------------------------------------------


def _pgcd(rng: random.Random, difficulte: int) -> dict[str, Any]:
    facteurs_g, max_q, plafond = palier(_PALIERS_PGCD, difficulte)

    def fabrique() -> tuple[int, int, int]:
        return _tirer_fraction(rng, facteurs_g, max_q, plafond)

    def acceptable(tire: tuple[int, int, int]) -> bool:
        g, p, q = tire
        a, b = g * p, g * q
        # le PGCD ne doit pas apparaître littéralement dans le développement de a et b (fuite de l'indice `etape`)
        return not collision(g, produit_developpe(a), produit_developpe(b))

    g, p, q = tirer(rng, fabrique, acceptable)
    a, b = g * p, g * q
    pieges: list[dict[str, Any]] = []
    diviseur_partiel = max((d for d in range(1, g) if g % d == 0), default=1)
    if diviseur_partiel > 1:
        pieges.append(
            piege_valeur(
                diviseur_partiel,
                f"{diviseur_partiel} divise bien {a} et {b}, mais ce n'est pas le plus grand diviseur commun. "
                "As-tu pris tous les facteurs premiers communs ?",
            )
        )
    pieges.append(
        piege_valeur(
            a * b,
            f"{a * b} est un multiple commun de {a} et {b} (leur produit), pas un diviseur commun. "
            "Le PGCD divise les deux nombres, il ne les multiplie pas.",
        )
    )
    pieges.append(
        piege_valeur(
            min(p, q),
            f"{min(p, q)} est ce qu'il resterait après avoir divisé par le PGCD, pas le PGCD lui-même. "
            f"Quel nombre divise à la fois {a} et {b} ?",
        )
    )
    pieges.append(
        piege_diagnostic(
            "valeur_fausse", f"Ce n'est pas le PGCD de {a} et {b}. Reprends les décompositions en facteurs premiers."
        )
    )
    return exercice_v2(
        id=f"pgcd-{a}-{b}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Quel est le PGCD de {a} et {b} ?",
        reponse={"valeur": g, "forme": "entier"},
        indices={
            "relance": f"Cherche les diviseurs communs à {a} et {b}.",
            "methode": "Décompose les deux nombres en facteurs premiers, puis multiplie les facteurs premiers "
            "communs, chacun avec le plus petit des deux exposants.",
            "etape": f"{a} = {produit_developpe(a)} et {b} = {produit_developpe(b)}. "
            "Quels facteurs premiers apparaissent dans les deux, et combien de fois ?",
        },
        pieges=pieges,
        solution=f"{a} = {joli_produit(decomposer(a))} et {b} = {joli_produit(decomposer(b))}. "
        f"Les facteurs communs donnent {joli_produit(decomposer(g))} = {g}. PGCD({a}, {b}) = {g}.",
        lieu=f"{NOTION}/pgcd/{a}-{b}",
    )


# --- point d'entrée -----------------------------------------------------------------------------------

_VARIANTES = {"simplifier": _simplifier, "irreductible": _irreductible, "pgcd": _pgcd}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
