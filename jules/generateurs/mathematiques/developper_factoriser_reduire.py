"""Générateur déterministe pour la notion `developper-factoriser-reduire` (mathématiques, 3e).

  - simple     : développer et réduire k(ax + b) (+ cx + d, − m(cx + d))      (expression développée)
  - double     : développer et réduire (ax + b)(cx + d)                        (expression développée)
  - difference : développer (ax + b)(ax − b), l'égalité (a + b)(a − b) = a² − b²  (expression développée)
  - factoriser : facteur commun (nombre, x), puis différence de deux carrés    (expression factorisée)

Le programme de 3e demande l'égalité (a + b)(a − b) = a² − b² dans les deux sens, pas les carrés
(a + b)² : ils n'apparaissent ici que comme pièges ((x − 7)² au lieu de (x − 7)(x + 7)).

Limite connue du correcteur : la forme `developpee` vérifie l'absence de parenthèses, pas la
réduction (« 6x − 15 + 4x » serait accepté). Les exercices demandent « développe et réduis » et la
solution réduit ; une forme `reduite` du correcteur est proposée à part (docs/GENERATEURS-COUVERTURE.md).

Pièges de la fiche v2 : oublier de multiplier le second terme, erreur de signe, deux produits sur
quatre, (x − 7)² pour x² − 49, facteur commun non divisé dans le second terme.
"""

from __future__ import annotations

import math
import random
from typing import Any

from jules.generateurs.briques import exercice_v2, generer_notion, palier, piege_diagnostic, piege_valeur
from jules.generateurs.briques.algebre import (
    constante,
    en_machine,
    entre_parentheses,
    facteur_fr,
    nombre_signe_fr,
    polynome_fr,
    polynome_machine,
    terme,
)
from jules.generateurs.briques.tirage import tirer

NOTION = "developper-factoriser-reduire"
VARIANTES = ("simple", "double", "difference", "factoriser")


def _non_nul(rng: random.Random, bas: int, haut: int, relatifs: bool) -> int:
    v = rng.randint(bas, haut)
    return v * rng.choice((1, -1)) if relatifs else v


def _terme_facteur(a: int) -> str:
    """« 3x », « (−6x) » : un terme en x dans un produit, entre parenthèses s'il est négatif."""
    return f"({terme(a)})" if a < 0 else terme(a)


def _produit_fr(k: int, a: int, b: int) -> str:
    """« 3(2x − 5) », « −(x + 4) », « −2(3x + 1) »."""
    if k == 1:
        return facteur_fr(a, b)
    if k == -1:
        return "−" + facteur_fr(a, b)
    return f"{nombre_signe_fr(k)}{facteur_fr(a, b)}"


# --- variante 1 : simple distributivité ---------------------------------------------------------------

_PALIERS_SIMPLE = {
    # difficulté : (relatifs ?, forme)
    1: (False, "seul"),  # k(ax + b)
    2: (True, "plus_terme"),  # k(ax + b) + cx + d
    3: (True, "deux_produits"),  # k(ax + b) + m(cx + d)
}


def _simple(rng: random.Random, difficulte: int) -> dict[str, Any]:
    relatifs, forme = palier(_PALIERS_SIMPLE, difficulte)
    k = tirer(rng, lambda: _non_nul(rng, 2, 9, relatifs), lambda v: v != 0)
    a, b = _non_nul(rng, 1, 7, relatifs), rng.randint(1, 9) * rng.choice((1, -1))
    c = d = m = 0
    if forme == "plus_terme":
        c, d = _non_nul(rng, 1, 9, True), rng.randint(0, 9) * rng.choice((1, -1))
    elif forme == "deux_produits":
        m = tirer(rng, lambda: _non_nul(rng, 2, 6, True), lambda v: v != k)
        c, d = _non_nul(rng, 1, 5, True), rng.randint(1, 9) * rng.choice((1, -1))
    x1 = k * a + (m * c if forme == "deux_produits" else c)
    x0 = k * b + (m * d if forme == "deux_produits" else d)
    if x1 == 0 or x0 == 0:  # réponse réduite à un nombre, ou à « 3x » que l'indice citerait : on retire ce tirage
        return _simple(rng, difficulte)
    if forme == "seul":
        expression = _produit_fr(k, a, b)
    elif forme == "plus_terme":
        expression = (
            _produit_fr(k, a, b) + terme(c, premier=False) + (f" {'+' if d > 0 else '−'} {abs(d)}" if d else "")
        )
    else:
        expression = _produit_fr(k, a, b) + (" + " if m > 0 else " − ") + _produit_fr(abs(m), c, d)
    reponse = [x0, x1]
    oubli_second = [(b + (m * d if forme == "deux_produits" else d)), x1]  # k(ax + b) -> kax + b
    signe_faux = [(-k * b + (m * d if forme == "deux_produits" else d)), x1]
    pieges = [
        piege_valeur(
            polynome_machine(oubli_second),
            f"Le nombre devant la parenthèse multiplie CHAQUE terme de la parenthèse : "
            f"{nombre_signe_fr(k)} × {entre_parentheses(b)} aussi.",
        ),
    ]
    if k < 0 or b < 0:
        pieges.append(
            piege_valeur(
                polynome_machine(signe_faux),
                f"Attention au signe : que vaut {entre_parentheses(k)} × {entre_parentheses(b)} ?",
            )
        )
    if forme == "deux_produits" and m < 0:  # − 3(2x + 5) devient −6x + 5 × 3 : le signe oublié sur le second terme
        pieges.append(
            piege_valeur(
                polynome_machine([k * b - m * d, x1]),
                "Le signe « − » devant la seconde parenthèse s'applique à TOUS ses termes.",
            )
        )
    pieges.append(piege_diagnostic("pas_developpee", "Il reste une parenthèse : développe-la aussi."))
    pieges.append(
        piege_diagnostic(
            "non_equivalente",
            "Remplace x par 1 dans l'expression de départ et dans la tienne : obtiens-tu le même nombre ?",
        )
    )
    premier_produit = f"{nombre_signe_fr(k)} × {_terme_facteur(a)} et {nombre_signe_fr(k)} × {entre_parentheses(b)}"
    return exercice_v2(
        id=f"simple-{k}-{a}-{b}-{c}-{d}-{m}",
        type="expression",
        difficulte=difficulte,
        enonce=f"Développe et réduis A = {expression}.",
        reponse={"valeur": polynome_machine(reponse), "forme": "developpee", "variables": ["x"]},
        indices={
            "relance": "Le nombre devant la parenthèse multiplie-t-il un seul terme, ou tous les termes ?",
            "methode": "k(a + b) = ka + kb : multiplie chaque terme de la parenthèse par le nombre devant, "
            "puis regroupe les x ensemble et les nombres ensemble.",
            "etape": f"Commence par calculer {premier_produit}.",
        },
        pieges=pieges,
        solution=f"A = {expression} = {polynome_fr(reponse)}.",
        lieu=f"{NOTION}/simple/{k}-{a}-{b}-{c}-{d}-{m}",
    )


# --- variante 2 : double distributivité ---------------------------------------------------------------

_PALIERS_DOUBLE = {
    # difficulté : (coefficients de x possibles, relatifs ?)
    1: ((1,), False),
    2: ((1, 2, 3), True),
    3: ((2, 3, 4, 5), True),
}


def _double(rng: random.Random, difficulte: int) -> dict[str, Any]:
    coefs, relatifs = palier(_PALIERS_DOUBLE, difficulte)

    def fabrique() -> tuple[int, int, int, int]:
        a, c = rng.choice(coefs), rng.choice(coefs)
        b, d = _non_nul(rng, 1, 9, relatifs), _non_nul(rng, 1, 9, relatifs)
        return a, b, c, d

    def accepte(t: tuple[int, int, int, int]) -> bool:
        a, b, c, d = t
        return a * d + b * c != 0 and (a, b) != (c, d)  # un terme en x ; pas un carré

    a, b, c, d = tirer(rng, fabrique, accepte)
    reponse = [b * d, a * d + b * c, a * c]
    expression = f"{facteur_fr(a, b)}{facteur_fr(c, d)}"
    pieges = [
        piege_valeur(
            polynome_machine([b * d, 0, a * c]),
            "Tu n'as fait que deux produits sur quatre : chaque terme de la première parenthèse multiplie "
            "chaque terme de la seconde.",
        ),
        piege_valeur(
            polynome_machine([-b * d, a * d + b * c, a * c]),
            f"Vérifie le signe du produit {entre_parentheses(b)} × {entre_parentheses(d)}.",
        ),
        piege_valeur(
            polynome_machine([b * d, a * d - b * c, a * c]),
            "Vérifie les deux produits qui donnent des x, et leurs signes, avant de les additionner.",
        ),
        piege_diagnostic("pas_developpee", "Il reste une parenthèse : développe complètement."),
        piege_diagnostic(
            "non_equivalente",
            "Remplace x par 1 dans l'expression de départ et dans la tienne : obtiens-tu le même nombre ?",
        ),
    ]
    produits = (
        f"{terme(a)} × {terme(c)}, {terme(a)} × {entre_parentheses(d)}, "
        f"{entre_parentheses(b)} × {terme(c)} et {entre_parentheses(b)} × {entre_parentheses(d)}"
    )
    return exercice_v2(
        id=f"double-{a}-{b}-{c}-{d}",
        type="expression",
        difficulte=difficulte,
        enonce=f"Développe et réduis B = {expression}.",
        reponse={"valeur": polynome_machine(reponse), "forme": "developpee", "variables": ["x"]},
        indices={
            "relance": "Combien de produits faut-il faire en tout pour développer ce produit de deux parenthèses ?",
            "methode": "(a + b)(c + d) = ac + ad + bc + bd : chaque terme de la première parenthèse multiplie "
            "chaque terme de la seconde. Ensuite, regroupe les termes en x.",
            "etape": f"Les quatre produits sont {produits}. Calcule-les un par un.",
        },
        pieges=pieges,
        solution=f"B = {expression} = {polynome_fr([0, 0, a * c])}"
        f"{terme(a * d, premier=False)}{terme(b * c, premier=False)}{constante(b * d)} = {polynome_fr(reponse)}.",
        lieu=f"{NOTION}/double/{a}-{b}-{c}-{d}",
    )


# --- variante 3 : (ax + b)(ax − b) = a²x² − b² ------------------------------------------------------------

_PALIERS_DIFFERENCE = {
    # difficulté : (a possibles, b possibles)
    1: ((1,), range(1, 11)),
    2: ((2, 3, 4, 5), range(1, 10)),
    3: ((2, 3, 4, 5, 6, 7), range(2, 13)),
}


def _difference(rng: random.Random, difficulte: int) -> dict[str, Any]:
    coefs, valeurs_b = palier(_PALIERS_DIFFERENCE, difficulte)
    a, b = rng.choice(coefs), rng.choice(valeurs_b)
    if difficulte == 3 and rng.random() < 0.5:
        expression = f"({b} − {terme(a)})({b} + {terme(a)})"  # (b − ax)(b + ax) = b² − a²x²
        reponse = [b * b, 0, -a * a]
    else:
        premier, second = (
            (facteur_fr(a, b), facteur_fr(a, -b)) if rng.random() < 0.5 else (facteur_fr(a, -b), facteur_fr(a, b))
        )
        expression = premier + second
        reponse = [-b * b, 0, a * a]
    signe_carre = 1 if reponse[2] > 0 else -1
    pieges = [
        piege_valeur(
            polynome_machine([-reponse[0], 0, reponse[2]]),
            "Regarde le signe du produit des deux nombres : l'un est positif, l'autre négatif.",
        ),
        piege_valeur(
            polynome_machine([reponse[0], 0, signe_carre * a]),
            f"Le terme {terme(a)} est lui aussi élevé au carré : que vaut {terme(a)} × {terme(a)} ?"
            if a != 1
            else "Élève chaque terme au carré.",
        ),
        piege_valeur(
            polynome_machine([reponse[0], 2 * a * b, reponse[2]]),
            "Les deux produits en x s'annulent : l'un vaut +, l'autre −. Refais-les.",
        ),
        piege_valeur(
            polynome_machine([b if reponse[0] > 0 else -b, 0, reponse[2]]),
            f"Le nombre {b} est lui aussi au carré : {b} × {b}.",
        ),
        piege_diagnostic("pas_developpee", "Il reste une parenthèse : développe complètement."),
        piege_diagnostic("non_equivalente", "Utilise (a + b)(a − b) = a² − b², ou fais les quatre produits."),
    ]
    return exercice_v2(
        id=f"difference-{a}-{b}-{reponse[0]}",
        type="expression",
        difficulte=difficulte,
        enonce=f"Développe et réduis C = {expression}.",
        reponse={"valeur": polynome_machine(reponse), "forme": "developpee", "variables": ["x"]},
        indices={
            "relance": "Les deux parenthèses se ressemblent : qu'est-ce qui change de l'une à l'autre ?",
            "methode": "(a + b)(a − b) = a² − b² : le carré du premier terme moins le carré du second. "
            "Tu peux aussi faire les quatre produits : ceux en x s'annulent.",
            "etape": f"Ici, un des termes est {terme(a)} et l'autre est {b}. Élève chacun au carré.",
        },
        pieges=pieges,
        # « 49 − 9x² » plutôt que « −9x² + 49 » : l'ordre de l'énoncé, et un signe « − » en tête de réponse
        # échappe au repérage des calculs dans la solution
        solution=f"C = {expression} = "
        + (polynome_fr(reponse) if reponse[2] > 0 else f"{b * b} − {polynome_fr([0, 0, a * a])}")
        + ", d'après (a + b)(a − b) = a² − b².",
        lieu=f"{NOTION}/difference/{a}-{b}",
    )


# --- variante 4 : factoriser -----------------------------------------------------------------------

_PALIERS_FACTORISER = {
    # difficulté : cas possibles
    1: ("nombre",),
    2: ("nombre", "x", "difference"),
    3: ("x_et_nombre", "difference", "parenthese"),
}
_PREMIERS = (2, 3, 5, 7)


def _factoriser(rng: random.Random, difficulte: int) -> dict[str, Any]:
    cas_possibles: tuple[str, ...] = palier(_PALIERS_FACTORISER, difficulte)
    cas = rng.choice(cas_possibles)
    diag_incomplet: str | None = None
    if cas == "nombre":  # kax + kb -> k(ax + b), k premier : une seule factorisation entière possible
        k = rng.choice(_PREMIERS)
        a, b = tirer(
            rng,
            lambda: (rng.randint(1, 9), rng.randint(1, 9) * rng.choice((1, -1))),
            lambda t: math.gcd(t[0], abs(t[1])) == 1 and t[0] % k != 0 and t[1] % k != 0,
        )
        depart = polynome_fr([k * b, k * a])
        reponse = f"{k}{facteur_fr(a, b)}"
        pieges = [
            piege_valeur(
                en_machine(f"{k}{facteur_fr(a, k * b)}"),
                f"Le facteur commun {k} sort de TOUS les termes : divise aussi le second terme par {k}.",
            ),
            piege_valeur(
                en_machine(f"{k}{facteur_fr(k * a, b)}"),
                f"Le facteur commun {k} sort de TOUS les termes : divise aussi le premier terme par {k}.",
            ),
        ]
        etape = f"{polynome_fr([0, k * a])} = {k} × {terme(a)}. Écris de même le second terme comme {k} fois un nombre."
        facteur_commun = "un nombre"
    elif cas in ("x", "x_et_nombre"):  # ux² + vx -> x(ux + v), ou kx(ux + v)
        k = 1 if cas == "x" else rng.choice((2, 3, 5))
        u, v = tirer(
            rng,
            lambda: (rng.randint(1, 9), rng.randint(1, 9) * rng.choice((1, -1))),
            lambda t: math.gcd(t[0], abs(t[1])) == 1 and (k == 1 or (t[0] % k != 0 and t[1] % k != 0)),
        )
        depart = polynome_fr([0, k * v, k * u])
        facteur = "x" if k == 1 else f"{k}x"
        reponse = f"{facteur}{facteur_fr(u, v)}"
        pieges = [
            piege_valeur(
                en_machine(f"{facteur}({polynome_fr([v, 0, u])})"),
                "En sortant x, il faut diviser CHAQUE terme par x : x² ÷ x = x.",
            ),
            piege_valeur(
                polynome_machine([0, 0, k * (u + v)]),
                "On ne peut pas additionner des x² et des x : ce ne sont pas des termes de même nature.",
            ),
        ]
        if k > 1:
            diag_incomplet = (
                f"Tu as trouvé un facteur commun, mais il en reste : {k} et x sont communs aux deux termes."
            )
        etape = (
            f"x² = x × x. Quel facteur retrouves-tu dans {polynome_fr([0, 0, k * u])} "
            f"et dans {polynome_fr([0, k * v])} ?"
        )
        facteur_commun = "x" if k == 1 else "un nombre et x"
    elif cas == "difference":  # a²x² − b² -> (ax − b)(ax + b)
        a = 1 if difficulte == 2 else rng.choice((2, 3, 4, 5))
        b = rng.randint(2, 12)
        depart = polynome_fr([-b * b, 0, a * a])
        reponse = f"{facteur_fr(a, -b)}{facteur_fr(a, b)}"
        pieges = [
            piege_valeur(
                en_machine(f"{facteur_fr(a, -b)}²"),
                f"{facteur_fr(a, -b)}² se développe avec un terme en x. "
                "Ici, c'est une différence de deux carrés : a² − b² = (a − b)(a + b).",
            ),
            piege_valeur(
                en_machine(f"{facteur_fr(a, -b * b)}{facteur_fr(a, b * b)}"),
                f"Dans a² − b², b est le nombre dont le carré vaut {b * b}, pas {b * b} lui-même.",
            ),
        ]
        etape = f"Écris {polynome_fr([-b * b, 0, a * a])} sous la forme a² − b² : que valent a et b ?"
        facteur_commun = ""
    else:  # (x + p)(qx + r) + (x + p)(sx + t) -> (x + p)((q + s)x + r + t)
        p = rng.randint(1, 9) * rng.choice((1, -1))
        q, s = rng.randint(1, 5), rng.randint(1, 5)
        r, t = rng.randint(1, 9) * rng.choice((1, -1)), rng.randint(1, 9) * rng.choice((1, -1))
        if r + t == 0:
            t += 1 if t > 0 else -1
        depart = f"{facteur_fr(1, p)}{facteur_fr(q, r)} + {facteur_fr(1, p)}{facteur_fr(s, t)}"
        reponse = f"{facteur_fr(1, p)}{facteur_fr(q + s, r + t)}"
        pieges = [
            piege_valeur(
                en_machine(f"{facteur_fr(1, p)}{facteur_fr(q * s, r * t)}"),
                "Le facteur commun est sorti : il reste à ADDITIONNER ce qu'il y a dans les autres parenthèses.",
            ),
            piege_valeur(
                en_machine(f"{facteur_fr(1, 2 * p)}{facteur_fr(q + s, r + t)}"),
                f"Le facteur commun {facteur_fr(1, p)} ne s'écrit qu'une fois.",
            ),
        ]
        etape = f"Le facteur commun est {facteur_fr(1, p)}. Qu'est-ce qui le multiplie dans chacun des deux termes ?"
        facteur_commun = "une parenthèse entière"
    pieges.append(
        piege_diagnostic(
            "pas_factorisee", "Une expression factorisée est un PRODUIT : écris-la sous la forme « facteur × (…) »."
        )
    )
    if diag_incomplet:
        pieges.append(piege_diagnostic("factorisation_incomplete", diag_incomplet))
    pieges.append(piege_diagnostic("non_equivalente", "Redéveloppe ta réponse : retrouves-tu l'expression de départ ?"))
    methode = (
        "Si l'expression est de la forme a² − b², écris (a − b)(a + b)."
        if cas == "difference"
        else f"Cherche le facteur commun à tous les termes (ici, {facteur_commun}) et écris-le devant une parenthèse : "
        "ka + kb = k(a + b)."
    )
    return exercice_v2(
        id=f"factoriser-{cas}-{en_machine(reponse).replace(' ', '')}",
        type="expression",
        difficulte=difficulte,
        enonce=f"Factorise D = {depart}.",
        reponse={"valeur": en_machine(reponse), "forme": "factorisee", "variables": ["x"]},
        indices={
            "relance": "Factoriser, c'est écrire l'expression comme un produit. Que retrouves-tu dans chaque terme ?"
            if cas != "difference"
            else "Reconnais-tu deux carrés séparés par un signe moins ?",
            "methode": methode,
            "etape": etape,
        },
        pieges=pieges,
        solution=f"D = {depart} = {reponse}. Vérification : en redéveloppant, on retrouve l'expression de départ.",
        lieu=f"{NOTION}/factoriser/{cas}",
    )


_VARIANTES = {"simple": _simple, "double": _double, "difference": _difference, "factoriser": _factoriser}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
