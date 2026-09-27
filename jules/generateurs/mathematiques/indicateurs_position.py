"""Générateur déterministe pour la notion `indicateurs-position` (mathématiques, 3e).

  - moyenne  : moyenne d'une série de valeurs (entière, décimale, puis arrondie au dixième)   (nombre)
  - mediane  : médiane d'une série non rangée (effectif impair, pair, puis avec répétitions)   (nombre)
  - ponderee : moyenne d'une série donnée par valeurs et effectifs                             (nombre)
  - comparer : deux séries, affirmations sur leurs moyennes et leurs médianes                (choix multiple)

Pièges de la fiche v2 : chercher la médiane sans avoir rangé la série, se tromper de rang (n/2 pour un
effectif impair, une seule valeur centrale pour un effectif pair), diviser par le nombre de valeurs
différentes au lieu de l'effectif total, confondre médiane et milieu de l'étendue.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from jules.generateurs.briques import (
    exercice_v2,
    generer_notion,
    palier,
    piege_contient,
    piege_diagnostic,
    piege_valeur,
)
from jules.generateurs.briques.format_fr import nombre_fr, nombre_machine
from jules.generateurs.briques.habillage import PERSONNAGES
from jules.generateurs.briques.serie import (
    arrondi_dixieme,
    contexte_serie,
    decimal_exact,
    mediane,
    moyenne,
    moyenne_ponderee,
    serie_fr,
    tirer_valeurs,
    total,
)
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "indicateurs-position"
VARIANTES = ("moyenne", "mediane", "ponderee", "comparer")

_LETTRES = "abcdef"
_TOLERANCE_DIXIEME = "0.05"  # « arrondie au dixième » : 10,86 et 10,9 sont justes pour 76/7


def _ecrit(x: Fraction, arrondir: bool) -> str | None:
    """Une valeur telle que l'élève l'écrirait : arrondie au dixième, ou exacte si elle tombe juste.

    None quand l'élève ne pourrait pas l'écrire exactement (piège impossible à reconnaître).
    """
    if arrondir:
        return nombre_machine(arrondi_dixieme(x))
    return nombre_machine(x) if decimal_exact(x) else None


def _pieges_valeurs(candidats: list[tuple[Fraction, str]], arrondir: bool) -> list[dict[str, Any]]:
    """Pièges « valeur » pour les erreurs que l'élève peut écrire (les autres sont écartées)."""
    pieges = []
    for valeur, relance in candidats:
        ecrit = _ecrit(valeur, arrondir)
        if ecrit is not None:
            pieges.append(piege_valeur(ecrit, relance))
    return pieges


def _rang(r: int) -> str:
    return "1re" if r == 1 else f"{r}e"


# --- variante 1 : moyenne d'une série --------------------------------------------------------------------

_PALIERS_MOYENNE = {
    # difficulté : (effectifs possibles, résultat attendu)
    1: ((5,), "entiere"),
    2: ((4, 5, 8, 10), "decimale"),
    3: ((6, 7, 9, 11, 12), "arrondie"),
}


def _moyenne(rng: random.Random, difficulte: int) -> dict[str, Any]:
    effectifs, attendu = palier(_PALIERS_MOYENNE, difficulte)
    contexte = contexte_serie(rng)
    arrondir = attendu == "arrondie"

    def fabrique() -> list[int]:
        return tirer_valeurs(rng, rng.choice(effectifs), contexte.bas, contexte.haut)

    def accepte(valeurs: list[int]) -> bool:
        m = moyenne(valeurs)
        if attendu == "entiere" and m.denominator != 1:
            return False
        if attendu == "decimale" and (m.denominator == 1 or not decimal_exact(m)):
            return False
        if arrondir and decimal_exact(m, 1):
            return False
        if difficulte > 1 and len(set(valeurs)) == len(
            valeurs
        ):  # une répétition : le piège des « valeurs différentes »
            return False
        # l'étape cite l'effectif : il ne doit pas s'écrire comme la réponse
        return not collision(arrondi_dixieme(m) if arrondir else m, len(valeurs))

    valeurs = tirer(rng, fabrique, accepte)
    n, somme, m = len(valeurs), total(valeurs), moyenne(valeurs)
    reponse = arrondi_dixieme(m) if arrondir else m
    pieges = _pieges_valeurs(
        [
            (somme, "Tu as calculé le total des valeurs : il reste à le diviser par l'effectif total."),
            (
                somme / len(set(valeurs)),
                "Divise par l'effectif total : une valeur qui revient plusieurs fois compte autant de fois "
                "qu'elle apparaît.",
            ),
            (somme / (n - 1), "Recompte les valeurs de la série : tu n'as pas divisé par le bon effectif."),
            (somme / (n + 1), "Recompte les valeurs de la série : tu n'as pas divisé par le bon effectif."),
            (
                mediane(valeurs),
                "C'est la médiane, la valeur du milieu de la série rangée. La moyenne se calcule avec toutes "
                "les valeurs.",
            ),
            (
                Fraction(min(valeurs) + max(valeurs), 2),
                "Tu as pris le milieu entre la plus petite et la plus grande valeur : pour la moyenne, "
                "toutes les valeurs comptent.",
            ),
        ],
        arrondir,
    )
    pieges.append(
        piege_diagnostic("valeur_fausse", "Refais l'addition des valeurs, par exemple deux par deux, puis la division.")
    )
    consigne = "Calcule la moyenne de cette série" + (", arrondie au dixième." if arrondir else ".")
    fin = f"≈ {nombre_fr(reponse)} (arrondi au dixième)" if arrondir else f"= {nombre_fr(m)}"
    return exercice_v2(
        id=f"moyenne-{'-'.join(map(str, valeurs))}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Voici {contexte.quoi} : {serie_fr(valeurs)}. {consigne}",
        reponse={"valeur": nombre_machine(reponse), "forme": "libre"}
        | ({"tolerance": _TOLERANCE_DIXIEME} if arrondir else {}),
        indices={
            "relance": "Pour calculer une moyenne, que fais-tu de toutes les valeurs ? Et par quoi divises-tu ?",
            "methode": "Moyenne = total des valeurs ÷ effectif total. L'effectif total, c'est le nombre de "
            "valeurs, répétitions comprises." + (" N'arrondis qu'à la fin." if arrondir else ""),
            "etape": f"La série compte {n} valeurs. Calcule leur total, puis divise-le par {n}.",
        },
        pieges=pieges,
        solution=f"Total : {' + '.join(map(str, valeurs))} = {nombre_fr(somme)}. Il y a {n} valeurs, donc la "
        f"moyenne vaut {nombre_fr(somme)} ÷ {n} {fin}.",
        lieu=f"{NOTION}/moyenne/{'-'.join(map(str, valeurs))}",
    )


# --- variante 2 : médiane d'une série non rangée ---------------------------------------------------------

_PALIERS_MEDIANE = {
    # difficulté : (effectifs possibles, répétitions ?)
    1: ((5, 7), False),
    2: ((6, 8), False),
    3: ((9, 10, 11, 12), True),
}


def _milieu_non_range(valeurs: list[int]) -> Fraction:
    """La « médiane » de l'élève qui n'a pas rangé la série : le milieu dans l'ordre de l'énoncé."""
    n = len(valeurs)
    if n % 2:
        return Fraction(valeurs[n // 2])
    return Fraction(valeurs[n // 2 - 1] + valeurs[n // 2], 2)


def _mediane(rng: random.Random, difficulte: int) -> dict[str, Any]:
    effectifs, repetitions = palier(_PALIERS_MEDIANE, difficulte)
    contexte = contexte_serie(rng)

    def fabrique() -> list[int]:
        return tirer_valeurs(rng, rng.choice(effectifs), contexte.bas, contexte.haut)

    def accepte(valeurs: list[int]) -> bool:
        n = len(valeurs)
        if (len(set(valeurs)) < n) != repetitions:
            return False
        if _milieu_non_range(valeurs) == mediane(valeurs):  # sans rangement, l'élève tomberait juste
            return False
        # l'étape cite l'effectif et les rangs du milieu
        return not collision(mediane(valeurs), n, n // 2, n // 2 + 1, (n + 1) // 2)

    valeurs = tirer(rng, fabrique, accepte)
    n, rangees, med = len(valeurs), sorted(valeurs), mediane(valeurs)
    candidats = [
        (
            _milieu_non_range(valeurs),
            "As-tu rangé la série dans l'ordre croissant avant de chercher la valeur du milieu ?",
        )
    ]
    if n % 2:
        r = (n + 1) // 2
        candidats += [
            (
                Fraction(rangees[r - 2]),
                "Vérifie le rang du milieu : il doit rester autant de valeurs avant la médiane qu'après.",
            ),
            (
                Fraction(rangees[r]),
                "Vérifie le rang du milieu : il doit rester autant de valeurs avant la médiane qu'après.",
            ),
        ]
        etape = (
            f"La série compte {n} valeurs, un nombre impair. Une fois la série rangée, la médiane est la "
            f"{_rang(r)} valeur."
        )
        detail = f"L'effectif {n} est impair : la médiane est la {_rang(r)} valeur, soit {nombre_fr(med)}."
    else:
        r1, r2 = n // 2, n // 2 + 1
        a, b = rangees[r1 - 1], rangees[r2 - 1]
        candidats += [
            (
                Fraction(a),
                "Avec un effectif pair, il y a deux valeurs centrales : la médiane est leur moyenne.",
            ),
            (
                Fraction(b),
                "Avec un effectif pair, il y a deux valeurs centrales : la médiane est leur moyenne.",
            ),
        ]
        etape = (
            f"La série compte {n} valeurs, un nombre pair. Une fois la série rangée, la médiane est la moyenne "
            f"de la {_rang(r1)} et de la {_rang(r2)} valeur."
        )
        detail = (
            f"L'effectif {n} est pair : la médiane est la moyenne des {_rang(r1)} et {_rang(r2)} valeurs, "
            f"({a} + {b}) ÷ 2 = {nombre_fr(med)}."
        )
    candidats += [
        (
            moyenne(valeurs),
            "Tu as calculé la moyenne. La médiane, c'est la valeur du milieu de la série rangée.",
        ),
        (
            Fraction(min(valeurs) + max(valeurs), 2),
            "La médiane n'est pas le milieu entre la plus petite et la plus grande valeur : c'est la valeur "
            "du milieu de la série rangée.",
        ),
    ]
    pieges = _pieges_valeurs(candidats, arrondir=False)
    pieges.append(
        piege_diagnostic("valeur_fausse", "Range la série, puis compte les valeurs une à une jusqu'au milieu.")
    )
    return exercice_v2(
        id=f"mediane-{'-'.join(map(str, valeurs))}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Voici {contexte.quoi} : {serie_fr(valeurs)}. Détermine la médiane de cette série.",
        reponse={"valeur": nombre_machine(med), "forme": "libre"},
        indices={
            "relance": "Que dois-tu faire à la série avant de chercher sa valeur du milieu ?",
            "methode": "Range les valeurs dans l'ordre croissant. Avec un effectif impair, la médiane est la "
            "valeur du milieu ; avec un effectif pair, c'est la moyenne des deux valeurs centrales.",
            "etape": etape,
        },
        pieges=pieges,
        solution=f"Série rangée : {serie_fr(rangees)}. {detail}",
        lieu=f"{NOTION}/mediane/{'-'.join(map(str, valeurs))}",
    )


# --- variante 3 : moyenne pondérée par les effectifs -----------------------------------------------------


@dataclass(frozen=True)
class _Enquete:
    intro: str
    bas: int
    haut: int
    ligne: Callable[[int, int], str]  # (effectif, valeur) -> « 4 élèves en ont 3 »
    question: str


def _s(e: int) -> str:
    return "s" if e > 1 else ""


_ENQUETES = (
    _Enquete(
        "On a demandé à des élèves combien ils ont de frères et sœurs :",
        0,
        5,
        lambda e, v: f"{e} élève{_s(e)} en {'a' if e == 1 else 'ont'} {v}",
        "Calcule le nombre moyen de frères et sœurs par élève.",
    ),
    _Enquete(
        "Un magasin a noté la pointure des paires de chaussures vendues dans la journée :",
        35,
        45,
        lambda e, v: f"{e} paire{_s(e)} en {v}",
        "Calcule la pointure moyenne des paires vendues.",
    ),
    _Enquete(
        "Voici les résultats d'une classe à un contrôle noté sur 20 :",
        5,
        19,
        lambda e, v: f"{e} élève{_s(e)} {'a' if e == 1 else 'ont'} eu {v}",
        "Calcule la note moyenne de la classe.",
    ),
    _Enquete(
        "Une équipe de football a compté les buts marqués à chaque match de la saison :",
        0,
        5,
        lambda e, v: f"{e} match{'s' if e > 1 else ''} avec {v} but{_s(v)}",
        "Calcule le nombre moyen de buts marqués par match.",
    ),
    _Enquete(
        "Au tir à l'arc, on a relevé les points obtenus à chaque flèche :",
        3,
        10,
        lambda e, v: f"{e} flèche{_s(e)} à {v} point{_s(v)}",
        "Calcule le nombre moyen de points par flèche.",
    ),
)


def _produits(valeurs: list[int], effectifs: list[int]) -> str:
    return " + ".join(f"{v} × {e}" for v, e in zip(valeurs, effectifs, strict=True))


_PALIERS_PONDEREE = {
    # difficulté : (nombre de valeurs, effectifs totaux possibles (None : libre), arrondir ?)
    1: (3, (10,), False),
    2: (4, (20, 25), False),
    3: (5, None, True),
}


def _ponderee(rng: random.Random, difficulte: int) -> dict[str, Any]:
    k, totaux, arrondir = palier(_PALIERS_PONDEREE, difficulte)
    enquete = rng.choice(_ENQUETES)

    def fabrique() -> tuple[list[int], list[int]]:
        valeurs = sorted(rng.sample(range(enquete.bas, enquete.haut + 1), k))
        if totaux is None:
            return valeurs, [rng.randint(1, 9) for _ in range(k)]
        effectif_total = rng.choice(totaux)
        coupures = sorted(rng.sample(range(1, effectif_total), k - 1))
        bornes = [0, *coupures, effectif_total]
        return valeurs, [bornes[i + 1] - bornes[i] for i in range(k)]

    def accepte(tirage: tuple[list[int], list[int]]) -> bool:
        valeurs, effectifs = tirage
        m = moyenne_ponderee(valeurs, effectifs)
        if arrondir and decimal_exact(m, 1):
            return False
        if len(set(effectifs)) == 1:  # effectifs tous égaux : la moyenne simple tomberait juste
            return False
        # l'étape cite l'effectif total et les produits : « 5 × 2 » se lit comme la réponse 5,2
        return not collision(arrondi_dixieme(m) if arrondir else m, sum(effectifs), _produits(valeurs, effectifs))

    valeurs, effectifs = tirer(rng, fabrique, accepte)
    effectif_total = sum(effectifs)
    somme = sum(v * e for v, e in zip(valeurs, effectifs, strict=True))
    m = moyenne_ponderee(valeurs, effectifs)
    reponse = arrondi_dixieme(m) if arrondir else m
    pieges = _pieges_valeurs(
        [
            (
                Fraction(sum(valeurs), k),
                "Chaque valeur ne compte pas une seule fois : multiplie-la par son effectif.",
            ),
            (
                Fraction(somme, k),
                "Divise par l'effectif total, pas par le nombre de valeurs différentes.",
            ),
            (Fraction(somme), "Tu as le total : il reste à le diviser par l'effectif total."),
        ],
        arrondir,
    )
    pieges.append(
        piege_diagnostic(
            "valeur_fausse",
            "Vérifie chaque produit valeur × effectif, leur somme, puis la division par l'effectif total.",
        )
    )
    lignes = [enquete.ligne(e, v) for v, e in zip(valeurs, effectifs, strict=True)]
    produits = _produits(valeurs, effectifs)
    fin = f"≈ {nombre_fr(reponse)} (arrondi au dixième)" if arrondir else f"= {nombre_fr(m)}"
    return exercice_v2(
        id=f"ponderee-{'-'.join(f'{v}x{e}' for v, e in zip(valeurs, effectifs, strict=True))}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"{enquete.intro} {' ; '.join(lignes)}. {enquete.question}"
        + (" Arrondis au dixième." if arrondir else ""),
        reponse={"valeur": nombre_machine(reponse), "forme": "libre"}
        | ({"tolerance": _TOLERANCE_DIXIEME} if arrondir else {}),
        indices={
            "relance": "Chaque valeur compte-t-elle une seule fois dans cette série ?",
            "methode": "Multiplie chaque valeur par son effectif, additionne ces produits, puis divise par "
            "l'effectif total.",
            "etape": f"L'effectif total est {effectif_total}. Calcule d'abord {produits}.",
        },
        pieges=pieges,
        solution=f"Effectif total : {' + '.join(map(str, effectifs))} = {effectif_total}. Total : {produits} = "
        f"{somme}. Moyenne : {somme} ÷ {effectif_total} {fin}.",
        lieu=f"{NOTION}/ponderee/{'-'.join(f'{v}x{e}' for v, e in zip(valeurs, effectifs, strict=True))}",
    )


# --- variante 4 : comparer deux séries -------------------------------------------------------------------

_PALIERS_COMPARER = {
    # difficulté : (effectif de la première série, effectif de la seconde)
    1: (5, 5),
    2: (5, 6),
    3: (7, 8),
}


def _environ(x: Fraction) -> str:
    return nombre_fr(x) if decimal_exact(x) else f"environ {nombre_fr(arrondi_dixieme(x))}"


def _comparer(rng: random.Random, difficulte: int) -> dict[str, Any]:
    n_a, n_b = palier(_PALIERS_COMPARER, difficulte)
    eleve_a, eleve_b = rng.sample(PERSONNAGES, 2)
    a, b = eleve_a.prenom, eleve_b.prenom

    def fabrique() -> tuple[list[int], list[int]]:
        return tirer_valeurs(rng, n_a, 4, 20), tirer_valeurs(rng, n_b, 4, 20)

    def accepte(series: tuple[list[int], list[int]]) -> bool:
        sa, sb = series
        ma, mb, meda, medb = moyenne(sa), moyenne(sb), mediane(sa), mediane(sb)
        if ma in (mb, meda) or medb in (meda, mb):  # des comparaisons strictes, sans égalité
            return False
        verites = [ma > mb, meda > medb, ma > meda, mb > medb]
        return any(verites) and not all(verites)

    sa, sb = tirer(rng, fabrique, accepte)
    ma, mb, meda, medb = moyenne(sa), moyenne(sb), mediane(sa), mediane(sb)
    affirmations = [
        (
            f"La moyenne des notes de {a} est plus grande que celle de {b}.",
            ma > mb,
            "Calcule la moyenne de chaque série (total ÷ effectif) avant de comparer"
            + (f" : {a} et {b} n'ont pas le même nombre de notes." if n_a != n_b else "."),
        ),
        (
            f"La médiane des notes de {a} est plus grande que celle de {b}.",
            meda > medb,
            "Range chaque série avant de chercher sa médiane, puis compare les deux médianes.",
        ),
        (
            f"Pour {a}, la moyenne est plus grande que la médiane.",
            ma > meda,
            f"Pour {a}, calcule séparément la moyenne et la médiane avant de les comparer.",
        ),
        (
            f"Pour {b}, la moyenne est plus grande que la médiane.",
            mb > medb,
            f"Pour {b}, calcule séparément la moyenne et la médiane avant de les comparer.",
        ),
    ]
    rng.shuffle(affirmations)
    options = [{"id": _LETTRES[i], "texte": texte} for i, (texte, _, _) in enumerate(affirmations)]
    bonnes = [_LETTRES[i] for i, (_, vrai, _) in enumerate(affirmations) if vrai]
    pieges = [piege_contient([_LETTRES[i]], relance) for i, (_, vrai, relance) in enumerate(affirmations) if not vrai]
    pieges.append(piege_diagnostic("incomplet", "Il manque une affirmation vraie : vérifie-les toutes, une par une."))
    vraies = " ; ".join(texte.rstrip(".") for texte, vrai, _ in affirmations if vrai)
    return exercice_v2(
        id=f"comparer-{'-'.join(map(str, sa))}-{'-'.join(map(str, sb))}",
        type="choix",
        difficulte=difficulte,
        enonce=f"Voici les notes sur 20 de {a} et de {b} ce trimestre. {a} : {serie_fr(sa)}. "
        f"{b} : {serie_fr(sb)}. Quelles affirmations sont vraies ?",
        reponse={"options": options, "bonnes": bonnes},
        indices={
            "relance": "Quels nombres dois-tu calculer pour chaque série avant de pouvoir juger ces affirmations ?",
            "methode": "Pour chaque série : moyenne = total ÷ effectif ; médiane = valeur du milieu de la série "
            "rangée. Compare ensuite les nombres obtenus.",
            "etape": (f"{a} et {b} ont chacun {n_a} notes." if n_a == n_b else f"{a} a {n_a} notes et {b} en a {n_b}.")
            + " Range chaque série, puis calcule sa moyenne et sa médiane.",
        },
        pieges=pieges,
        solution=f"{a} : moyenne {_environ(ma)}, médiane {nombre_fr(meda)}. {b} : moyenne {_environ(mb)}, "
        f"médiane {nombre_fr(medb)}. Affirmations vraies : {vraies}.",
        lieu=f"{NOTION}/comparer/{'-'.join(map(str, sa))}/{'-'.join(map(str, sb))}",
    )


_VARIANTES = {
    "moyenne": _moyenne,
    "mediane": _mediane,
    "ponderee": _ponderee,
    "comparer": _comparer,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
