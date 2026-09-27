"""Générateur déterministe pour la notion `racine-carree` (mathématiques, 3e).

  - calculer        : √n pour un carré parfait ; √(a + b) ; √ d'un décimal ou d'un produit   (nombre)
  - aire_cote       : côté d'un carré dont on connaît l'aire                              (nombre)
  - carres_parfaits : lesquels sont des carrés parfaits (de 1 à 144) ?                    (choix multiple)
  - encadrer        : √n entre deux entiers consécutifs : le plus petit, ou le plus grand (nombre entier)

Pièges de la fiche v2 : diviser par 2 au lieu de prendre la racine (√64 n'est pas 32), donner une
racine négative, √(9 + 16) = √9 + √16, élever au carré au lieu de prendre la racine ; pour l'aire,
diviser par 4 (confusion avec le périmètre).
"""

from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Any

from jules.generateurs.briques import (
    exercice_v2,
    generer_notion,
    piege_contient,
    piege_diagnostic,
    piege_valeur,
)
from jules.generateurs.briques.format_fr import nombre_fr, nombre_machine
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "racine-carree"
VARIANTES = ("calculer", "aire_cote", "carres_parfaits", "encadrer")

_LETTRES = "abcdef"
_TRIPLETS = ((3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17), (12, 16, 20))


def _est_carre(n: int) -> bool:
    return n >= 0 and math.isqrt(n) ** 2 == n


# --- variante 1 : calculer une racine carrée ------------------------------------------------------------


def _calculer(rng: random.Random, difficulte: int) -> dict[str, Any]:
    if difficulte == 1:
        k = rng.randint(2, 12)
        sous, affiche, reponse = k * k, f"√{k * k}", Fraction(k)
        etape = f"Récite les carrés des nombres entiers, dans l'ordre, jusqu'à retrouver {k * k}."
        pieges = [
            piege_valeur(
                nombre_machine(Fraction(k * k, 2)),
                f"On ne divise pas par deux : on cherche le nombre qui, multiplié par LUI-MÊME, donne {k * k}.",
            ),
            piege_valeur(str(k**4), "Tu as calculé le carré. La racine carrée, c'est l'opération inverse."),
        ]
        solution_calcul = f"√{k * k} = {k}, car {k} × {k} = {k * k} et {k} est positif."
    elif difficulte == 2:  # √(a + b) avec un triplet : on calcule d'abord sous la racine
        if rng.random() < 0.5:  # deux carrés dont la somme est un carré (triplet, multiplié par 1 à 4)
            base = rng.choice(_TRIPLETS)
            m = rng.randint(1, 20 // base[2])  # la réponse reste au plus 20
            a, b, c = (m * t for t in base)
            gauche, droite = a * a, b * b
        else:  # une somme quelconque qui tombe sur un carré parfait
            c = rng.randint(4, 12)
            # aucun des deux termes ne doit s'écrire comme la réponse (√(7 + 42) : l'indice citerait 7)
            gauche = tirer(rng, lambda: rng.randint(3, c * c - 3), lambda g: not collision(c, g, c * c - g))
            droite = c * c - gauche
        sous, affiche, reponse = c * c, f"√({gauche} + {droite})", Fraction(c)
        etape = f"Calcule d'abord {gauche} + {droite}, puis cherche le nombre positif dont c'est le carré."
        racines_separees = (
            [
                piege_valeur(
                    str(math.isqrt(gauche) + math.isqrt(droite)),
                    f"√({gauche} + {droite}) n'est pas √{gauche} + √{droite} : on calcule d'abord ce qu'il y a "
                    "sous la racine.",
                )
            ]
            if _est_carre(gauche) and _est_carre(droite)
            else []
        )
        pieges = [
            *racines_separees,
            piege_valeur(
                nombre_machine(Fraction(c * c, 2)),
                "On ne divise pas par deux : on cherche le nombre qui, "
                "multiplié par lui-même, donne le nombre sous la racine.",
            ),
            piege_valeur(str(c * c), "Tu as fait la somme sous la racine : il reste à prendre la racine carrée."),
        ]
        solution_calcul = f"{gauche} + {droite} = {c * c}, et √{c * c} = {c}, car {c} × {c} = {c * c}."
    else:  # √ d'un décimal (√0,49 = 0,7) ou d'un produit de deux carrés (√(4 × 49) = 14)
        if rng.random() < 0.5:
            k = rng.choice((2, 3, 4, 5, 6, 7, 8, 9, 11, 12))  # pas 10 : ce serait √1
            reponse = Fraction(k, 10)
            sous_d = reponse * reponse
            affiche = f"√{nombre_fr(sous_d)}"
            sous = 0
            etape = f"{nombre_fr(sous_d)} = {k * k} ÷ 100. Cherche la racine de {k * k}, puis celle de 100, et divise."
            pieges = [
                piege_valeur(
                    nombre_machine(sous_d / 2),
                    "On ne divise pas par deux : on cherche le nombre qui, multiplié par lui-même, donne ce nombre.",
                ),
                piege_valeur(
                    nombre_machine(Fraction(k, 100)),
                    f"Vérifie en multipliant ta réponse par elle-même : obtiens-tu {nombre_fr(sous_d)} ?",
                ),
            ]
            solution_calcul = (
                f"{nombre_fr(reponse)} × {nombre_fr(reponse)} = {nombre_fr(sous_d)}, "
                f"donc {affiche} = {nombre_fr(reponse)}."
            )
        else:
            p, q = tirer(rng, lambda: (rng.randint(2, 5), rng.randint(3, 12)), lambda t: t[0] != t[1])
            sous, affiche, reponse = p * p * q * q, f"√({p * p} × {q * q})", Fraction(p * q)
            etape = f"La racine d'un produit est le produit des racines : cherche √{p * p}, puis √{q * q}."
            pieges = [
                piege_valeur(
                    str(p * p * q * q // 2) if (p * q) % 2 == 0 else "0.5",
                    "On ne divise pas par deux : on cherche la racine carrée.",
                ),
                piege_valeur(str(p + q), f"√{p * p} × √{q * q}, c'est une multiplication : pas une addition."),
            ]
            solution_calcul = f"{affiche} = √{p * p} × √{q * q} = {p} × {q} = {p * q}."
    pieges.append(piege_valeur(nombre_machine(-reponse), "Une racine carrée est toujours positive."))
    pieges.append(
        piege_diagnostic(
            "valeur_fausse", "Vérifie : multiplie ta réponse par elle-même, retrouves-tu le nombre sous la racine ?"
        )
    )
    return exercice_v2(
        id=f"calculer-{difficulte}-{affiche}".replace("√", "r").replace(" ", ""),
        type="nombre",
        difficulte=difficulte,
        enonce=f"Calcule {affiche}.",
        reponse={"valeur": nombre_machine(reponse), "forme": "libre"},
        indices={
            "relance": "Quel nombre positif, multiplié par lui-même, donne le nombre sous la racine ?",
            "methode": "La racine carrée d'un nombre positif a est le nombre positif dont le carré vaut a. "
            "Connaître les carrés parfaits de 1 à 144 aide beaucoup.",
            "etape": etape,
        },
        pieges=pieges,
        solution=solution_calcul,
        lieu=f"{NOTION}/calculer/{affiche}-{sous}",
    )


# --- variante 2 : côté d'un carré d'aire donnée ---------------------------------------------------------

_OBJETS = ("un carré", "une dalle carrée", "un jardin carré", "une nappe carrée", "un tapis carré")


def _aire_cote(rng: random.Random, difficulte: int) -> dict[str, Any]:
    unite = rng.choice(("cm", "m"))
    if difficulte == 3:
        cote = Fraction(rng.randint(11, 29), 10)
        if cote.denominator == 1:
            cote += Fraction(1, 2)
    else:
        cote = Fraction(rng.randint(2, 12) if difficulte == 1 else rng.choice((13, 14, 15, 20, 25, 30, 40, 50)))
    aire = cote * cote
    objet = rng.choice(_OBJETS)
    pieges = [
        piege_valeur(nombre_machine(aire / 2), "Le côté n'est pas la moitié de l'aire : l'aire, c'est côté × côté."),
        piege_valeur(
            nombre_machine(aire / 4), "Diviser par 4, c'est pour passer du périmètre au côté. Ici, on connaît l'AIRE."
        ),
        piege_valeur(
            nombre_machine(aire * aire), "Tu as élevé l'aire au carré. On cherche le nombre dont le carré vaut l'aire."
        ),
        piege_diagnostic("valeur_fausse", f"Vérifie : ton côté multiplié par lui-même donne-t-il {nombre_fr(aire)} ?"),
    ]
    return exercice_v2(
        id=f"aire_cote-{nombre_machine(aire)}-{unite}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"{objet[0].upper() + objet[1:]} a une aire de {nombre_fr(aire)} {unite}². "
        f"Quelle est la longueur de son côté, en {unite} ?",
        reponse={"valeur": nombre_machine(cote), "forme": "libre"},
        indices={
            "relance": "Comment calcule-t-on l'aire d'un carré à partir de son côté ?",
            "methode": "Aire du carré = côté × côté. Le côté est donc le nombre positif dont le carré vaut l'aire : "
            "c'est la racine carrée de l'aire.",
            "etape": f"Cherche le nombre positif qui, multiplié par lui-même, donne {nombre_fr(aire)}.",
        },
        pieges=pieges,
        solution=f"Côté × côté = {nombre_fr(aire)}, donc côté = √{nombre_fr(aire)} = {nombre_fr(cote)} {unite} "
        f"(vérification : {nombre_fr(cote)} × {nombre_fr(cote)} = {nombre_fr(aire)}).",
        lieu=f"{NOTION}/aire_cote/{nombre_machine(aire)}",
    )


# --- variante 3 : reconnaître les carrés parfaits ------------------------------------------------------------


def _carres_parfaits(rng: random.Random, difficulte: int) -> dict[str, Any]:
    nb_bons = rng.choice((1, 2)) if difficulte == 1 else rng.choice((2, 3))

    def tirage() -> list[tuple[int, str]]:
        """(nombre, raison du piège ; « » pour un vrai carré parfait)."""
        bons = rng.sample(range(2, 13), nb_bons)
        liste = [(k * k, "") for k in bons]
        pieges_possibles = []
        for k in rng.sample(range(3, 13), 4):
            pieges_possibles += [
                (
                    2 * k * k if difficulte > 1 else 2 * k,
                    "C'est le double d'un nombre, pas un carré : cherche un entier qui, "
                    "multiplié par lui-même, le donne.",
                ),
                (
                    k * k + rng.choice((-1, 1)),
                    "Il est juste à côté d'un carré parfait, mais ce n'en est pas un : aucun entier "
                    "multiplié par lui-même ne le donne.",
                ),
                (10 * k, "C'est 10 fois un autre nombre : pour un carré parfait, il faut deux facteurs ÉGAUX."),
            ]
        rng.shuffle(pieges_possibles)
        liste += pieges_possibles[: 5 - nb_bons]
        return liste

    def accepte(liste: list[tuple[int, str]]) -> bool:
        nombres = [n for n, _ in liste]
        return len(set(nombres)) == 5 and all((r == "") == _est_carre(n) for n, r in liste) and max(nombres) <= 300

    liste = tirer(rng, tirage, accepte)
    rng.shuffle(liste)
    options = [{"id": _LETTRES[i], "texte": str(n)} for i, (n, _) in enumerate(liste)]
    bonnes = [_LETTRES[i] for i, (_, r) in enumerate(liste) if not r]
    return exercice_v2(
        id=f"carres_parfaits-{'-'.join(str(n) for n, _ in liste)}",
        type="choix",
        difficulte=difficulte,
        enonce="Parmi ces nombres, lesquels sont des carrés parfaits ? (Il peut y en avoir plusieurs.)",
        reponse={"options": options, "bonnes": bonnes},
        indices={
            "relance": "Un carré parfait, c'est le carré d'un nombre entier. Connais-tu les carrés de 1 à 12 ?",
            "methode": "Pour chaque nombre, cherche un entier qui, multiplié par lui-même, le donne. "
            "S'il n'y en a pas, "
            "ce n'est pas un carré parfait.",
            "etape": "Écris la liste des carrés des entiers de 1 à 12, puis compare-la aux nombres proposés.",
        },
        pieges=[
            *(piege_contient([_LETTRES[i]], r) for i, (_, r) in enumerate(liste) if r),
            piege_diagnostic("incomplet", "Il en manque : teste chaque nombre, un par un."),
        ],
        solution="Les carrés parfaits sont : "
        + ", ".join(f"{n} = {math.isqrt(n)} × {math.isqrt(n)}" for n, r in liste if not r)
        + ". Les autres ne sont le carré d'aucun entier.",
        lieu=f"{NOTION}/carres_parfaits/{difficulte}",
    )


# --- variante 4 : encadrer une racine entre deux entiers consécutifs ----------------------------------------


def _encadrer(rng: random.Random, difficulte: int) -> dict[str, Any]:
    haut_k = {1: 9, 2: 12, 3: 20}[difficulte]
    k = rng.randint(2, haut_k - 1)
    n = tirer(
        rng, lambda: rng.randint(k * k + 1, (k + 1) ** 2 - 1), lambda v: not collision(k, v) and not collision(k + 1, v)
    )
    petit = rng.random() < 0.5 if difficulte > 1 else True
    reponse = k if petit else k + 1
    autre = k + 1 if petit else k
    pieges = [
        piege_valeur(
            str(reponse * reponse),
            f"{reponse * reponse} est un carré parfait, pas sa racine. On cherche le "
            "nombre entier dont c'est le carré.",
        ),
        piege_valeur(str(autre), f"C'est l'autre entier. On demande le plus {'petit' if petit else 'grand'} des deux."),
        piege_valeur(
            nombre_machine(Fraction(n, 2)),
            f"On ne divise pas par deux : on cherche les carrés parfaits qui entourent {n}.",
        ),
        piege_diagnostic(
            "valeur_fausse",
            f"Cherche le plus grand carré parfait inférieur à {n}, et le plus petit qui lui est supérieur.",
        ),
    ]
    return exercice_v2(
        id=f"encadrer-{n}-{'petit' if petit else 'grand'}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"√{n} est compris entre deux nombres entiers consécutifs. Quel est le plus "
        f"{'petit' if petit else 'grand'} des deux ?",
        reponse={"valeur": reponse, "forme": "entier"},
        indices={
            "relance": f"Quels sont les carrés parfaits qui entourent {n} ?",
            "methode": f"Trouve deux carrés parfaits consécutifs, l'un plus petit que {n}, l'autre plus grand. "
            f"√{n} est entre leurs racines.",
            "etape": f"Cherche le plus grand carré parfait inférieur à {n}, puis le suivant dans la liste.",
        },
        pieges=pieges,
        solution=f"{k * k} < {n} < {(k + 1) ** 2}, donc √{k * k} < √{n} < √{(k + 1) ** 2}, soit {k} < √{n} < {k + 1}. "
        f"Le plus {'petit' if petit else 'grand'} des deux entiers est {reponse}.",
        lieu=f"{NOTION}/encadrer/{n}",
    )


_VARIANTES = {
    "calculer": _calculer,
    "aire_cote": _aire_cote,
    "carres_parfaits": _carres_parfaits,
    "encadrer": _encadrer,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
