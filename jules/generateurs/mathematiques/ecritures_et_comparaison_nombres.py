"""Générateur déterministe pour la notion `ecritures-et-comparaison-nombres` (mathématiques, 3e).

  - ranger           : ranger cinq nombres (décimaux, fractions, négatifs)                  (ordre)
  - fraction_decimal : écriture décimale d'une fraction ; au palier 3, décimal -> fraction
                       irréductible                                                         (nombre)
  - encadrer         : quels nombres sont compris entre deux bornes ?                      (choix multiple)
  - abscisse         : abscisse d'un point sur une droite graduée partagée en b parts      (nombre, fraction)

Pièges de la fiche v2 : comparer les parties décimales comme des entiers (1,58 > 1,6), ranger des
négatifs par leur distance à zéro, 7/8 lu « 7,8 », fraction à l'envers, signe oublié, fraction non
simplifiée. Les indices écrivent une division « 7 ÷ 8 », jamais « 7/8 » : le vérificateur lirait
la réponse elle-même.
"""

from __future__ import annotations

import math
import random
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
from jules.generateurs.briques.algebre import nombre_signe_fr, valeur_machine
from jules.generateurs.briques.format_fr import nombre_fr, nombre_machine
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "ecritures-et-comparaison-nombres"
VARIANTES = ("ranger", "fraction_decimal", "encadrer", "abscisse")

_LETTRES = "abcdefg"
_DENOMINATEURS_DECIMAUX = (2, 4, 5, 8, 20, 25)


def _ecrire(x: Fraction, en_fraction: bool) -> str:
    """Un nombre tel que l'élève le lit : « 1,65 », « −1,4 » ou « 5/3 », « −3/2 »."""
    if en_fraction and x.denominator != 1:
        return nombre_signe_fr(x)
    texte = nombre_fr(abs(x))
    return ("−" if x < 0 else "") + texte


def _decimal_court(rng: random.Random, bas: int, haut: int, chiffres: int) -> Fraction:
    """Un décimal avec 1 à `chiffres` chiffres après la virgule, entre bas et haut."""
    n = rng.randint(1, chiffres)
    return Fraction(rng.randint(bas * 10**n, haut * 10**n), 10**n)


# --- variante 1 : ranger ------------------------------------------------------------------------------


def _relance_ordre_faux(en_fraction: list[bool], valeurs: list[Fraction]) -> str:
    """La relance d'un ordre faux, écrite d'après la liste réellement tirée (fractions ? négatifs ?)."""
    etapes = []
    if any(en_fraction):
        etapes.append("écris chaque fraction en écriture décimale")
    if any(v < 0 for v in valeurs):
        etapes.append("place les négatifs avant les positifs")
    comparer = "compare les parties entières, puis les dixièmes, puis les centièmes"
    if not etapes:
        return f"Reprends pas à pas : {comparer}."
    return "D'abord, " + " ; ensuite, ".join(etapes) + f" ; enfin, {comparer}."


_PALIERS_RANGER = {
    # difficulté : (fractions ?, négatifs ?)
    1: (False, False),
    2: (True, False),
    3: (True, True),
}


def _ranger(rng: random.Random, difficulte: int) -> dict[str, Any]:
    fractions, negatifs = palier(_PALIERS_RANGER, difficulte)
    base = rng.randint(0, 3)

    def tirage() -> list[tuple[Fraction, bool]]:
        nombres: list[tuple[Fraction, bool]] = []
        # deux décimaux de même partie entière, l'un plus long mais plus petit : le piège « 1,58 > 1,6 »
        court = Fraction(rng.randint(base * 10 + 2, base * 10 + 9), 10)
        long_ = court - Fraction(rng.randint(1, 9), 100)
        nombres += [(court, False), (long_, False)]
        while len(nombres) < 5:
            if fractions and rng.random() < 0.5:
                den = rng.choice((3, 4, 6, 7, 8))
                x = Fraction(rng.randint(den * base, den * (base + 2)), den)
                en_fraction = x.denominator != 1
            else:
                x, en_fraction = _decimal_court(rng, base, base + 2, 2), False
            if negatifs and rng.random() < 0.4:
                x = -x
            nombres.append((x, en_fraction))
        return nombres

    def accepte(nombres: list[tuple[Fraction, bool]]) -> bool:
        valeurs = [x for x, _ in nombres]
        textes = [_ecrire(x, f) for x, f in nombres]
        if len(set(valeurs)) != 5 or len(set(textes)) != 5:
            return False
        return not negatifs or sum(v < 0 for v in valeurs) >= 2  # au palier 3, au moins deux négatifs à ordonner

    nombres = tirer(rng, tirage, accepte)
    croissant = difficulte < 3 or rng.random() < 0.5
    lettres = rng.sample(_LETTRES[:5], 5)
    ids = {x: lettre for (x, _), lettre in zip(nombres, lettres, strict=True)}
    textes = {x: _ecrire(x, f) for x, f in nombres}
    ordre = sorted(ids, reverse=not croissant)
    elements = [{"id": ids[x], "texte": textes[x]} for x in ordre]

    def comme_reponse(suite: list[Fraction]) -> str:
        return ", ".join(ids[x] for x in suite)

    # erreur « longueur » : partie entière, puis partie décimale lue comme un entier (1,58 > 1,6)
    def cle_longueur(x: Fraction) -> tuple[int, int, int]:
        texte = nombre_fr(abs(x)) if x.denominator in (1, 2, 4, 5, 10, 20, 25, 50, 100) else ""
        entier, _, decimales = texte.partition(",")
        signe = -1 if x < 0 else 1
        return (signe, signe * int(entier or 0), signe * int(decimales or 0)) if texte else (signe, 0, 0)

    pieges = [
        piege_valeur(
            comme_reponse(sorted(ids, key=cle_longueur, reverse=not croissant)),
            "Compare les chiffres rang par rang : les dixièmes d'abord, puis les centièmes. "
            "Un nombre qui a plus de chiffres après la virgule n'est pas forcément plus grand.",
        ),
        piege_valeur(
            comme_reponse(sorted(ids, key=abs, reverse=not croissant)),
            "Pour deux nombres négatifs, le plus petit est celui qui est le plus LOIN de zéro.",
        ),
        piege_valeur(
            comme_reponse(list(reversed(ordre))),
            f"Relis la consigne : on range dans l'ordre {'croissant' if croissant else 'décroissant'}.",
        ),
        piege_diagnostic(
            "inversion_voisine", "Presque : deux nombres voisins sont inversés. Compare-les chiffre par chiffre."
        ),
        piege_diagnostic("ordre_faux", _relance_ordre_faux([f for _, f in nombres], [x for x, _ in nombres])),
    ]
    sens = "croissant (du plus petit au plus grand)" if croissant else "décroissant (du plus grand au plus petit)"
    return exercice_v2(
        id=f"ranger-{'-'.join(valeur_machine(x) for x in ordre).replace('/', 'sur')}",
        type="ordre",
        difficulte=difficulte,
        enonce=f"Range ces nombres dans l'ordre {sens}.",
        reponse={"elements": elements},
        indices={
            "relance": "Lesquels de ces nombres sont négatifs ? Et y a-t-il des fractions à écrire autrement ?"
            if fractions
            else "Ces nombres ont-ils la même partie entière ? Que compares-tu ensuite ?",
            "methode": "Écris tous les nombres en écriture décimale, place les négatifs avant les positifs, "
            "puis compare les parties entières, les dixièmes, les centièmes.",
            "etape": "Pour chaque nombre, écris le chiffre des unités, puis celui des dixièmes, puis celui des "
            "centièmes (ajoute un 0 si besoin) : tu compares alors des nombres qui ont autant de chiffres.",
        },
        pieges=pieges,
        solution="Dans l'ordre "
        + ("croissant" if croissant else "décroissant")
        + " : "
        + (" < " if croissant else " > ").join(textes[x] for x in ordre)
        + ".",
        lieu=f"{NOTION}/ranger/{difficulte}",
    )


# --- variante 2 : écriture décimale <-> fraction -----------------------------------------------------------


def _fraction_decimal(rng: random.Random, difficulte: int) -> dict[str, Any]:
    den = rng.choice(_DENOMINATEURS_DECIMAUX if difficulte > 1 else (2, 4, 5, 10))
    num = tirer(rng, lambda: rng.randint(1, (5 if difficulte == 1 else 3) * den), lambda n: math.gcd(n, den) == 1)
    x = Fraction(num, den)
    if difficulte < 3:  # fraction -> décimal
        pieges = [
            piege_valeur(
                f"{num}.{den}", "La barre de fraction ne remplace pas la virgule : elle veut dire « divisé par »."
            ),
            piege_valeur(
                valeur_machine(Fraction(den, num)),
                "Tu as divisé dans le mauvais sens : le numérateur par le dénominateur, pas l'inverse.",
            ),
            piege_diagnostic(
                "valeur_fausse", f"Pose la division de {num} par {den}, en ajoutant des zéros après la virgule."
            ),
        ]
        return exercice_v2(
            id=f"fraction_decimal-{num}-{den}",
            type="nombre",
            difficulte=difficulte,
            enonce=f"Donne l'écriture décimale de la fraction {num}/{den}.",
            reponse={"valeur": nombre_machine(x), "forme": "libre"},
            indices={
                "relance": "Que veut dire la barre de fraction ? Quelle opération représente-t-elle ?",
                "methode": "Une fraction, c'est une division : le numérateur divisé par le dénominateur.",
                "etape": f"Calcule {num} ÷ {den} (pose la division, ou passe par un dénominateur 10, 100 ou 1 000).",
            },
            pieges=pieges,
            solution=f"{num}/{den} = {num} ÷ {den} = {nombre_fr(x)}.",
            lieu=f"{NOTION}/fraction_decimal/{num}-{den}",
        )
    # palier 3 : décimal -> fraction irréductible
    puissance = 10 ** len(nombre_fr(x).partition(",")[2])
    brute = x * puissance
    pieges = [
        piege_valeur(
            f"{puissance}/{int(brute)}",
            "Ta fraction est à l'envers : le nombre de départ est-il plus petit ou plus grand que 1 ?",
        ),
        piege_diagnostic(
            "non_irreductible",
            "C'est la bonne valeur, mais la fraction se simplifie encore : divise le "
            "numérateur et le dénominateur par un diviseur commun.",
        ),
        piege_diagnostic("pas_une_fraction", "On attend une fraction : un numérateur, une barre, un dénominateur."),
        piege_diagnostic(
            "valeur_fausse",
            "Écris le nombre comme un nombre de dixièmes, de centièmes ou de millièmes, puis simplifie.",
        ),
    ]
    return exercice_v2(
        id=f"fraction_decimal-inverse-{num}-{den}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Écris le nombre {nombre_fr(x)} sous la forme d'une fraction irréductible.",
        reponse={"valeur": valeur_machine(x), "forme": "fraction_irreductible"},
        indices={
            "relance": "Combien y a-t-il de chiffres après la virgule ? Que te dit le dernier chiffre (dixièmes, "
            "centièmes, millièmes) ?",
            "methode": "Écris le nombre sur 10, 100 ou 1 000, puis simplifie la fraction jusqu'à ce qu'elle soit "
            "irréductible.",
            "etape": f"Le nombre s'écrit {int(brute)} sur {puissance}. Cherche le plus grand diviseur commun de "
            "ces deux nombres.",
        },
        pieges=pieges,
        solution=f"{nombre_fr(x)} = {int(brute)}/{puissance} = {num}/{den} (on divise en haut et en bas par "
        f"{int(brute) // num}).",
        lieu=f"{NOTION}/fraction_decimal/inverse-{num}-{den}",
    )


# --- variante 3 : encadrer ---------------------------------------------------------------------------------

_PALIERS_ENCADRER = {
    # difficulté : (bornes en fraction ?, négatifs ?)
    1: (False, False),
    2: (True, False),
    3: (True, True),
}


def _encadrer(rng: random.Random, difficulte: int) -> dict[str, Any]:
    fractions, negatifs = palier(_PALIERS_ENCADRER, difficulte)
    signe = -1 if negatifs and rng.random() < 0.6 else 1

    def bornes() -> tuple[Fraction, Fraction]:
        if fractions:
            den = rng.choice((3, 4, 5, 6, 8))
            n = rng.randint(1, 2 * den)
            return Fraction(n, den), Fraction(n + rng.randint(1, 2), den)
        a = Fraction(rng.randint(10, 60), 10)
        return a, a + Fraction(rng.randint(2, 8), 10)

    bas, haut = tirer(rng, bornes, lambda b: (b[0] != b[1] and b[0].denominator != 1) or not fractions)
    if signe < 0:
        bas, haut = -haut, -bas
    largeur = haut - bas

    def candidat(dedans: bool) -> Fraction:
        if dedans:
            return bas + largeur * Fraction(rng.randint(1, 9), 10)
        cote = rng.choice((-1, 1))
        return (bas if cote < 0 else haut) + cote * largeur * Fraction(rng.randint(1, 8), 10)

    def tirage() -> list[tuple[Fraction, bool]]:
        dedans = [True, True, False, False]
        if rng.random() < 0.5:
            dedans[1] = False
        return [(candidat(d), d) for d in dedans]

    def accepte(liste: list[tuple[Fraction, bool]]) -> bool:
        valeurs = [x for x, _ in liste]
        textes = [_ecrire(x, False) for x in valeurs]
        ok_decimal = all(x.denominator in (1, 2, 4, 5, 8, 10, 20, 25, 40, 50, 100, 1000) for x in valeurs)
        if not ok_decimal or len(set(textes)) != 4 or any(x in (bas, haut) for x in valeurs):
            return False
        # une bonne réponse ne doit pas se lire dans un autre nombre cité par une relance (« 5 » dans « 4,5 »)
        return all(not collision(x, *(y for y in valeurs if y != x)) for x, dedans in liste if dedans)

    choix = tirer(rng, tirage, accepte)
    # une réponse écrite en fraction, pour mélanger les écritures (quand elle est simple)
    rng.shuffle(choix)
    options = []
    bonnes = []
    relances = {}
    for lettre, (x, dedans) in zip(_LETTRES, choix, strict=False):
        en_fraction = fractions and x.denominator in (4, 5, 8) and rng.random() < 0.4
        texte = _ecrire(x, en_fraction)
        options.append({"id": lettre, "texte": texte})
        if dedans:
            bonnes.append(lettre)
        else:
            relances[lettre] = (
                f"{texte} est {'plus petit que la plus petite' if x < bas else 'plus grand que la plus grande'} "
                "des deux bornes : il n'est pas entre elles."
            )
    bornes_texte = f"{_ecrire(bas, fractions)} et {_ecrire(haut, fractions)}"
    return exercice_v2(
        id=f"encadrer-{valeur_machine(bas)}-{valeur_machine(haut)}-{'-'.join(o['texte'] for o in options)}".replace(
            "/", "sur"
        ),
        type="choix",
        difficulte=difficulte,
        enonce=f"Quels nombres sont compris entre {bornes_texte} ? (Il peut y en avoir plusieurs.)",
        reponse={"options": options, "bonnes": bonnes},
        indices={
            "relance": "Quelles sont les écritures décimales des deux bornes ?"
            if fractions
            else "Quelle est la plus petite borne ? La plus grande ?",
            "methode": "Écris les bornes et chaque nombre en écriture décimale, puis compare chaque nombre aux "
            "deux bornes : il doit être plus grand que la première ET plus petit que la seconde.",
            "etape": "Écris les deux bornes en écriture décimale, puis compare chaque nombre à la plus petite, "
            "puis à la plus grande.",
        },
        pieges=[
            *(piege_contient([i], r) for i, r in relances.items()),
            piege_diagnostic("incomplet", "Il en manque : vérifie chaque nombre, un par un."),
        ],
        solution=(
            f"{_ecrire(bas, fractions)} = {_ecrire(bas, False)} et "
            f"{_ecrire(haut, fractions)} = {_ecrire(haut, False)}. "
            if fractions
            else ""
        )
        + "Les nombres compris entre les deux bornes sont : "
        + ", ".join(o["texte"] for o in options if o["id"] in bonnes)
        + ".",
        lieu=f"{NOTION}/encadrer/{valeur_machine(bas)}-{valeur_machine(haut)}",
    )


# --- variante 4 : abscisse sur une droite graduée ---------------------------------------------------------

_PALIERS_ABSCISSE = {
    # difficulté : (parts possibles, négatif possible ?, fraction à simplifier ?, graduations max en unités)
    1: ((2, 3, 4, 5, 6, 8, 10), False, False, 3),
    2: ((3, 4, 5, 6, 8), True, False, 2),
    3: ((4, 6, 8, 9, 10, 12), True, True, 2),
}


def _abscisse(rng: random.Random, difficulte: int) -> dict[str, Any]:
    parts_possibles, negatif, simplifier, unites = palier(_PALIERS_ABSCISSE, difficulte)

    def fabrique() -> tuple[int, int, int]:
        b = rng.choice(parts_possibles)
        k = rng.randint(2, unites * b)  # à 1 graduation, « une graduation vaut 1 ÷ b » serait la réponse
        s = rng.choice((1, -1)) if negatif else 1
        return b, k, s

    def accepte(t: tuple[int, int, int]) -> bool:
        b, k, s = t
        x = Fraction(s * k, b)
        if x.denominator == 1:
            return False
        if simplifier != (math.gcd(k, b) > 1):  # palier 3 : toujours à simplifier ; avant : jamais
            return False
        return not collision(x, b, k)

    b, k, s = tirer(rng, fabrique, accepte)
    x = Fraction(s * k, b)
    cote = "à droite" if s > 0 else "à gauche"
    pieges = [
        piege_valeur(str(s * k), f"{k}, c'est le nombre de graduations. Chaque graduation vaut une part de l'unité."),
        piege_valeur(
            valeur_machine(Fraction(s * b, k)),
            "Ta fraction est à l'envers : combien de parts dans une unité, et combien de parts compte-t-on ?",
        ),
        piege_valeur(valeur_machine(-x), f"Le point est {cote} de 0 : quel est le signe de son abscisse ?"),
        piege_diagnostic("non_irreductible", "C'est la bonne valeur, mais la fraction se simplifie encore."),
        piege_diagnostic(
            "valeur_fausse", "Compte les graduations depuis 0, et rappelle-toi combien de parts fait une unité."
        ),
    ]
    return exercice_v2(
        id=f"abscisse-{b}-{s * k}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Sur une droite graduée, l'unité (de 0 à 1) est partagée en {b} parts égales. Le point A est "
        f"{cote} de 0, à {k} graduations de 0. Quelle est l'abscisse de A ? Donne-la sous forme de fraction "
        "irréductible.",
        reponse={"valeur": valeur_machine(x), "forme": "fraction_irreductible"},
        indices={
            "relance": "Que vaut une seule graduation, si l'unité est partagée en parts égales ?",
            "methode": "Une graduation vaut une part de l'unité. Multiplie par le nombre de graduations, "
            "mets le bon signe, puis simplifie.",
            "etape": f"Une graduation vaut 1 ÷ {b}. Le point est à {k} graduations, {cote} de 0.",
        },
        pieges=pieges,
        solution=f"Une graduation vaut 1/{b}. A est à {k} graduations {cote} de 0 : son abscisse est "
        + (
            f"{'−' if s < 0 else ''}{k}/{b} = {nombre_signe_fr(x)}." if math.gcd(k, b) > 1 else f"{nombre_signe_fr(x)}."
        ),
        lieu=f"{NOTION}/abscisse/{b}-{s * k}",
    )


_VARIANTES = {
    "ranger": _ranger,
    "fraction_decimal": _fraction_decimal,
    "encadrer": _encadrer,
    "abscisse": _abscisse,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
