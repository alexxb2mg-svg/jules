"""Générateur déterministe pour la notion `problemes-mise-en-equation` (mathématiques, 3e).

  - nombre_pense     : « je pense à un nombre, je le multiplie par… »          (nombre)
  - ages             : âges de deux personnes, somme dans n ans                (nombre)
  - perimetre        : rectangle, longueur = largeur + d, périmètre connu      (nombre)
  - tarifs           : deux formules de prix, pour combien de séances égales   (nombre entier)
  - choisir_equation : quelle(s) équation(s) traduisent l'énoncé ?             (choix multiple)

Pièges de la fiche v2 : répondre à une autre question que celle posée (l'autre personne, la
longueur, le prix au lieu du nombre de séances), faire vieillir une seule personne, ne compter
qu'une longueur et une largeur dans un périmètre, défaire les opérations dans le mauvais ordre.
Les nombres sont tirés pour que la solution soit un entier positif qui a du sens.
"""

from __future__ import annotations

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
from jules.generateurs.briques.algebre import affine_fr, valeur_machine
from jules.generateurs.briques.format_fr import nombre_fr
from jules.generateurs.briques.habillage import PERSONNAGES, personnage
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "problemes-mise-en-equation"
VARIANTES = ("nombre_pense", "ages", "perimetre", "tarifs", "choisir_equation")

_LETTRES = "abcdef"
_FOIS = {2: "le double", 3: "le triple", 4: "le quadruple"}
_FOIS_AGE = {2: "deux fois", 3: "trois fois", 4: "quatre fois", 5: "cinq fois"}

_PALIERS = {
    # difficulté : (plus grand nombre pensé, plus grand âge, plus grande largeur)
    1: (15, 14, 20),
    2: (30, 14, 40),
    3: (30, 14, 40),
}

_METHODE = (
    "Appelle x le nombre cherché, écris chaque quantité de l'énoncé en fonction de x, repère la phrase qui "
    "donne l'égalité, puis résous l'équation et vérifie dans l'énoncé."
)


def _deux_personnages(rng: random.Random) -> tuple[Any, Any]:
    a, b = rng.sample(PERSONNAGES, 2)
    return a, b


# --- variante 1 : je pense à un nombre ------------------------------------------------------------------


def _nombre_pense(rng: random.Random, difficulte: int) -> dict[str, Any]:
    p = personnage(rng)

    def fabrique() -> tuple[int, int, int, int]:
        """(x, a, b signé, c) ; au palier 3, c est le second coefficient et d se déduit."""
        x = rng.randint(2, palier(_PALIERS, difficulte)[0])
        a = rng.randint(2, 9)
        b = rng.randint(1, 20) * (1 if difficulte == 1 else rng.choice((1, -1)))
        c = rng.randint(2, 5) if difficulte == 3 else 0
        if difficulte == 3:
            b = abs(b)
        return x, a, b, c

    def accepte(t: tuple[int, int, int, int]) -> bool:
        x, a, b, c = t
        resultat = a * x + b
        if difficulte == 3:
            d = resultat - c * x
            return a > c and d > 0 and not collision(x, a, b, c, d, d - b, a - c, resultat)
        return resultat > 0 and not collision(x, a, abs(b), resultat, resultat - b)

    x, a, b, c = tirer(rng, fabrique, accepte)
    if difficulte < 3:
        b_signe = b
        resultat = a * x + b_signe
        operation = f"ajoute {b}" if b > 0 else f"retire {-b}"
        enonce = (
            f"{p.prenom} pense à un nombre. {p.Pronom} le multiplie par {a}, puis {operation} au résultat. "
            f"{p.Pronom} obtient {resultat}. À quel nombre {p.prenom} a-t-{p.pronom} pensé ?"
        )
        equation = f"{affine_fr(a, b_signe)} = {resultat}"
        pieges = [
            piege_valeur(
                valeur_machine(Fraction(resultat, a) - b_signe),
                "Tu as défait les opérations dans le mauvais ordre : on défait d'abord la DERNIÈRE opération faite.",
            ),
            piege_valeur(
                str(resultat - b_signe),
                f"Il reste à défaire la multiplication : ce nombre est le résultat de la multiplication par {a}.",
            ),
            piege_valeur(
                valeur_machine(Fraction(resultat + b_signe, a)),
                "Pour défaire un ajout, on retire ; pour défaire un retrait, on ajoute.",
            ),
        ]
        etape = f"Écris l'équation {affine_fr(a, b_signe)} = {resultat}, puis défais d'abord l'ajout ou le retrait."
        solution = (
            f"Si x est le nombre pensé : {equation}, donc {a}x = {resultat - b_signe}, donc x = "
            f"{resultat - b_signe} ÷ {a} = {x}. Vérification : {a} × {x} {'+' if b_signe > 0 else '−'} {abs(b_signe)} "
            f"= {resultat}. {p.prenom} a pensé à {x}."
        )
    else:  # le même nombre des deux côtés : « a fois x plus b » = « c fois x plus d »
        d = a * x + b - c * x  # positif : vérifié au tirage
        si = "s'il" if p.pronom == "il" else "si elle"
        enonce = (
            f"{p.prenom} pense à un nombre. {si.capitalize()} le multiplie par {a} et ajoute {b}, {p.pronom} obtient "
            f"le même résultat que {si} le multiplie par {c} et ajoute {d}. Quel est ce nombre ?"
        )
        equation = f"{affine_fr(a, b)} = {affine_fr(c, d)}"
        pieges = [
            piege_valeur(
                valeur_machine(Fraction(d - b, a + c)),
                "Pour regrouper les x, on retire le même nombre de x des deux côtés : on ne les additionne pas.",
            ),
            piege_valeur(str(d - b), "Il reste un nombre de x : divise par ce nombre."),
        ]
        etape = f"Écris l'équation {equation}, puis regroupe les x dans un seul membre."
        solution = (
            f"Si x est le nombre pensé : {equation}, donc {affine_fr(a - c, 0)} = {d - b}, donc x = {x}. "
            f"Vérification : {a} × {x} + {b} = {a * x + b} et {c} × {x} + {d} = {c * x + d}. Le nombre est {x}."
        )
    pieges.append(
        piege_diagnostic("valeur_fausse", "Remplace ta réponse dans l'énoncé : obtiens-tu bien le résultat annoncé ?")
    )
    return exercice_v2(
        id=f"nombre_pense-{a}-{b}-{c}-{x}",
        type="nombre",
        difficulte=difficulte,
        enonce=enonce,
        reponse={"valeur": x, "forme": "entier"},
        indices={
            "relance": "Appelle x le nombre pensé. Qu'est-ce qu'on fait à x, dans l'ordre ?",
            "methode": _METHODE,
            "etape": etape,
        },
        pieges=pieges,
        solution=solution,
        lieu=f"{NOTION}/nombre_pense/{a}-{b}-{c}-{x}",
    )


# --- variante 2 : âges --------------------------------------------------------------------------------------


def _ages(rng: random.Random, difficulte: int) -> dict[str, Any]:
    grand, petit = _deux_personnages(rng)

    def fabrique() -> tuple[int, int, int]:
        x = rng.randint(3, palier(_PALIERS, difficulte)[1])
        k = rng.randint(2, 5) if difficulte > 1 else rng.randint(3, 12)  # palier 1 : écart d'âge ; sinon : facteur
        n = rng.randint(2, 10) if difficulte == 3 else 0
        return x, k, n

    def total(t: tuple[int, int, int]) -> int:
        x, k, n = t
        return (x + (x + k) if difficulte == 1 else x + k * x) + 2 * n

    def accepte(t: tuple[int, int, int]) -> bool:
        x, k, n = t
        return not collision(x, k, n, total(t), total(t) - 2 * n, k + 1)

    x, k, n = tirer(rng, fabrique, accepte)
    s = total((x, k, n))
    if difficulte == 1:
        relation = f"{grand.prenom} a {k} ans de plus que {petit.prenom}"
        age_grand = x + k
        equation = f"x + (x + {k}) = {s}"
        resolution = f"2x + {k} = {s}, donc 2x = {s - k}, donc x = {x}"
    else:
        relation = f"{grand.prenom} a {_FOIS_AGE[k]} l'âge de {petit.prenom}"
        age_grand = k * x
        if n:
            equation = f"(x + {n}) + ({k}x + {n}) = {s}"
            resolution = f"{k + 1}x + {2 * n} = {s}, donc {k + 1}x = {s - 2 * n}, donc x = {x}"
        else:
            equation = f"x + {k}x = {s}"
            resolution = f"{k + 1}x = {s}, donc x = {x}"
    quand = f"Dans {n} ans, la somme de leurs âges sera {s} ans." if n else f"La somme de leurs âges est {s} ans."
    pieges = [
        piege_valeur(str(age_grand), f"C'est l'âge de {grand.prenom}. On demande celui de {petit.prenom}."),
    ]
    if n:
        pieges.append(
            piege_valeur(
                valeur_machine(Fraction(s - n, k + 1)), f"Dans {n} ans, les DEUX personnes auront vieilli de {n} ans."
            )
        )
        pieges.append(piege_valeur(valeur_machine(Fraction(s, k + 1)), f"Tu as oublié les {n} ans qui passent."))
        pieges.append(
            piege_valeur(str(x + n), f"C'est l'âge de {petit.prenom} dans {n} ans. On demande son âge aujourd'hui.")
        )
    else:
        pieges.append(
            piege_valeur(
                valeur_machine(Fraction(s, k if difficulte > 1 else 2)),
                f"Compte bien tous les x : l'âge de {petit.prenom} est compté aussi.",
            )
        )
    pieges.append(
        piege_diagnostic(
            "valeur_fausse", "Vérifie : avec ta réponse, la somme des âges donne-t-elle bien le total annoncé ?"
        )
    )
    return exercice_v2(
        id=f"ages-{difficulte}-{x}-{k}-{n}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"{relation}. {quand} Quel âge a {petit.prenom} aujourd'hui ?",
        reponse={"valeur": x, "forme": "entier"},
        indices={
            "relance": f"Appelle x l'âge de {petit.prenom}. Comment s'écrit l'âge de {grand.prenom} ?",
            "methode": _METHODE,
            "etape": "Écris l'âge de chacun en fonction de x"
            + (f", puis ajoute {n} ans à CHACUN" if n else "")
            + ", et écris que la somme vaut le total.",
        },
        pieges=pieges,
        solution=f"Soit x l'âge de {petit.prenom}. {equation}, donc {resolution}. {petit.prenom} a {x} ans "
        f"(et {grand.prenom} {age_grand} ans).",
        lieu=f"{NOTION}/ages/{x}-{k}-{n}",
    )


# --- variante 3 : périmètre d'un rectangle ------------------------------------------------------------------


def _perimetre(rng: random.Random, difficulte: int) -> dict[str, Any]:
    demande_longueur = difficulte == 3 and rng.random() < 0.5
    unite = rng.choice(("cm", "m"))

    def fabrique() -> tuple[int, int]:
        return rng.randint(3, palier(_PALIERS, difficulte)[2]), rng.randint(2, 15)

    def accepte(t: tuple[int, int]) -> bool:
        largeur, d = t
        reponse = largeur + d if demande_longueur else largeur
        return not collision(reponse, d, 2 * (2 * largeur + d), 4 * largeur + 2 * d - 2 * d, 2 * largeur + d)

    largeur, d = tirer(rng, fabrique, accepte)
    longueur = largeur + d
    p = 2 * (largeur + longueur)
    reponse = longueur if demande_longueur else largeur
    autre = largeur if demande_longueur else longueur
    pieges = [
        piege_valeur(
            str(autre),
            f"C'est la {'largeur' if demande_longueur else 'longueur'}. On demande la "
            f"{'longueur' if demande_longueur else 'largeur'}.",
        ),
        piege_valeur(
            valeur_machine(Fraction(p - d, 2)),
            "Un rectangle a DEUX longueurs et DEUX largeurs : le périmètre les compte toutes les quatre.",
        ),
        piege_valeur(
            valeur_machine(Fraction(p, 4)),
            f"Si tous les côtés étaient égaux, ce serait un carré. Ici, la longueur dépasse la largeur de {d} {unite}.",
        ),
        piege_diagnostic(
            "valeur_fausse", "Vérifie : avec ta réponse, le périmètre donne-t-il bien la valeur annoncée ?"
        ),
    ]
    return exercice_v2(
        id=f"perimetre-{largeur}-{d}-{'longueur' if demande_longueur else 'largeur'}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Un rectangle a une longueur qui dépasse sa largeur de {d} {unite}. Son périmètre est {p} {unite}. "
        f"Quelle est sa {'longueur' if demande_longueur else 'largeur'}, en {unite} ?",
        reponse={"valeur": reponse, "forme": "entier"},
        indices={
            "relance": "Appelle x la largeur. Comment s'écrit la longueur ? Et le périmètre ?",
            "methode": _METHODE,
            "etape": "Le périmètre d'un rectangle vaut 2 × (longueur + largeur). Écris-le avec x, puis écris qu'il "
            "vaut le périmètre annoncé.",
        },
        pieges=pieges,
        solution=f"Soit x la largeur : la longueur vaut x + {d}. 2 × (x + x + {d}) = {p}, donc 4x + {2 * d} = {p}, "
        f"donc 4x = {p - 2 * d}, donc x = {largeur}. La largeur est {largeur} {unite} et la longueur "
        f"{longueur} {unite}.",
        lieu=f"{NOTION}/perimetre/{largeur}-{d}",
    )


# --- variante 4 : deux tarifs ---------------------------------------------------------------------------------

_ACTIVITES = (
    ("Au cinéma", "séance", "séances"),
    ("À la piscine", "entrée", "entrées"),
    ("À la salle d'escalade", "séance", "séances"),
)


def _tarifs(rng: random.Random, difficulte: int) -> dict[str, Any]:
    lieu_, unite, unites = rng.choice(_ACTIVITES)
    de = "d'" if unites[0] in "aeiouéè" else "de "

    def fabrique() -> tuple[int, int, int]:
        prix = rng.randint(5, 12)
        reduit = rng.randint(2, prix - 2)
        n = rng.randint(3, 15)
        return prix, reduit, n

    def accepte(t: tuple[int, int, int]) -> bool:
        prix, reduit, n = t
        abonnement = (prix - reduit) * n
        return not collision(n, prix, reduit, abonnement, prix - reduit, prix * n)

    prix, reduit, n = tirer(rng, fabrique, accepte)
    abonnement = (prix - reduit) * n
    pieges = [
        piege_valeur(
            str(prix * n), f"C'est le prix payé pour ce nombre {de}{unites}. On demande le nombre {de}{unites}."
        ),
        piege_valeur(
            valeur_machine(Fraction(abonnement, prix)),
            f"Avec l'abonnement, chaque {unite} coûte aussi {reduit} € : écris le prix total des deux formules.",
        ),
        piege_valeur(
            valeur_machine(Fraction(abonnement, prix + reduit)),
            "Quand on regroupe les x, on soustrait : on n'additionne pas les deux prix.",
        ),
        piege_diagnostic("valeur_fausse", "Calcule le prix des deux formules pour ta réponse : sont-ils égaux ?"),
    ]
    return exercice_v2(
        id=f"tarifs-{prix}-{reduit}-{abonnement}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"{lieu_}, deux formules : sans abonnement, chaque {unite} coûte {prix} € ; avec abonnement, on "
        f"paie {abonnement} € pour l'année, puis {reduit} € par {unite}. Pour combien {de}{unites} les deux formules "
        "coûtent-elles le même prix ?",
        reponse={"valeur": n, "forme": "entier"},
        indices={
            "relance": f"Appelle x le nombre {de}{unites}. Combien coûte chaque formule pour x {unites} ?",
            "methode": _METHODE,
            "etape": f"Sans abonnement : {prix}x. Avec abonnement : {abonnement} + {reduit}x. Écris que les deux "
            "prix sont égaux.",
        },
        pieges=pieges,
        solution=f"Soit x le nombre {de}{unites}. {prix}x = {abonnement} + {reduit}x, donc {prix - reduit}x = "
        f"{abonnement}, donc x = {n}. Pour {n} {unites}, les deux formules coûtent {nombre_fr(prix * n)} €.",
        lieu=f"{NOTION}/tarifs/{prix}-{reduit}-{abonnement}",
    )


# --- variante 5 : choisir l'équation --------------------------------------------------------------------------


def _choisir_equation(rng: random.Random, difficulte: int) -> dict[str, Any]:
    grand, petit = _deux_personnages(rng)
    k = rng.randint(2, 5)
    n = rng.randint(2, 10)
    x = rng.randint(3, 12)
    s = x + k * x + 2 * n
    justes = [f"(x + {n}) + ({k}x + {n}) = {s}", f"{affine_fr(k + 1, 2 * n)} = {s}"]
    fausses = [
        (f"x + {k}x = {s}", f"Dans {n} ans, les deux personnes auront vieilli : il faut ajouter {n} ans à chacune."),
        (f"x + {n} + {k}x = {s}", f"{grand.prenom} aussi aura {n} ans de plus."),
        (
            f"(x + {n}) + {k}(x + {n}) = {s}",
            f"C'est aujourd'hui que {grand.prenom} a {_FOIS_AGE[k]} l'âge de {petit.prenom}, pas dans {n} ans.",
        ),
    ]
    if difficulte == 1:  # une seule bonne équation, deux distracteurs
        justes = justes[:1]
        fausses = fausses[:2]
    textes = [(t, True, "") for t in justes] + [(t, False, r) for t, r in fausses]
    rng.shuffle(textes)
    options = [{"id": _LETTRES[i], "texte": t} for i, (t, _, _) in enumerate(textes)]
    bonnes = [_LETTRES[i] for i, (_, j, _) in enumerate(textes) if j]
    pieges = [piege_contient([_LETTRES[i]], r) for i, (_, j, r) in enumerate(textes) if not j]
    if len(bonnes) > 1:
        pieges.append(
            piege_diagnostic(
                "incomplet",
                "Il en manque : deux écritures différentes peuvent traduire le "
                "même énoncé. Développe et réduis pour comparer.",
            )
        )
    return exercice_v2(
        id=f"choisir_equation-{k}-{n}-{s}-{len(bonnes)}",
        type="choix",
        difficulte=difficulte,
        enonce=f"{grand.prenom} a {_FOIS_AGE[k]} l'âge de {petit.prenom}. Dans {n} ans, la somme de leurs âges sera "
        f"{s} ans. On note x l'âge actuel de {petit.prenom}. Quelle(s) équation(s) traduisent l'énoncé ?"
        + (" (Il peut y en avoir plusieurs.)" if difficulte > 1 else ""),
        reponse={"options": options, "bonnes": bonnes},
        indices={
            "relance": f"Comment s'écrit l'âge actuel de {grand.prenom} avec x ? Et les deux âges dans {n} ans ?",
            "methode": "Écris chaque âge dans le futur en fonction de x, puis la somme. Deux équations qui se "
            "développent et se réduisent de la même façon traduisent le même énoncé.",
            "etape": f"Aujourd'hui : x et {k}x. Dans {n} ans : ajoute {n} à CHACUN des deux âges.",
        },
        pieges=pieges,
        solution=f"Dans {n} ans, {petit.prenom} aura x + {n} ans et {grand.prenom} {k}x + {n} ans : "
        f"(x + {n}) + ({k}x + {n}) = {s}, qui se réduit en {affine_fr(k + 1, 2 * n)} = {s}. "
        + ("Les deux écritures conviennent." if len(bonnes) > 1 else ""),
        lieu=f"{NOTION}/choisir_equation/{k}-{n}-{s}",
    )


_VARIANTES = {
    "nombre_pense": _nombre_pense,
    "ages": _ages,
    "perimetre": _perimetre,
    "tarifs": _tarifs,
    "choisir_equation": _choisir_equation,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
