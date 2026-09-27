"""Générateur déterministe pour la notion `nombres-premiers-decomposition` (mathématiques, 3e).

Quatre variantes, de types de réponse différents :

  - decomposer   : décomposer un entier en produit de facteurs premiers   (nombre, produit_premiers)
  - reconnaitre  : repérer les nombres premiers dans une liste            (choix)
  - sachets      : plus grand partage possible de deux quantités (PGCD)   (nombre, entier)
  - fraction     : rendre une fraction irréductible par décomposition     (nombre, fraction_irreductible)

Tout est calculé : les valeurs sont tirées sous contraintes (graine + difficulté), la réponse vient du
solveur, les indices, les pièges et la solution sont rédigés à partir du calcul réel. Les fonctions
de calcul viennent du correcteur (jules/fiches/correction.py), les écritures et l'assemblage des
briques communes (jules/generateurs/briques/). Ce module ne contient que ce qui est propre à la notion.
"""

from __future__ import annotations

import random
from typing import Any

from jules.fiches.correction import decomposer, ecrire_produit, est_premier
from jules.generateurs.briques import (
    exercice_v2,
    generer_notion,
    palier,
    piege_contient,
    piege_diagnostic,
    piege_valeur,
)
from jules.generateurs.briques.format_fr import chaine_divisions, joli_produit, produit_developpe
from jules.generateurs.briques.habillage import lots, personnage
from jules.generateurs.briques.tirage import couple_premiers_entre_eux, entier_produit_de_premiers

NOTION = "nombres-premiers-decomposition"
VARIANTES = ("decomposer", "reconnaitre", "sachets", "fraction")


# --- variante 1 : décomposer ----------------------------------------------------------------------

_PALIERS_DECOMPOSER = {
    # difficulté : (nombre de facteurs premiers, nombres premiers permis, valeur maximale)
    1: (3, (2, 3, 5, 7), 100),
    2: (4, (2, 3, 5, 7, 11), 1000),
    3: (5, (2, 3, 5, 7, 11, 13), 5000),
}
_TOURNURES_DECOMPOSER = (
    "Décompose {n} en produit de facteurs premiers.",
    "Écris {n} sous la forme d'un produit de facteurs premiers.",
    "Donne la décomposition en facteurs premiers de {n}.",
)


def _decomposer(rng: random.Random, difficulte: int) -> dict[str, Any]:
    nb, premiers, maximum = palier(_PALIERS_DECOMPOSER, difficulte)
    n = entier_produit_de_premiers(rng, nb, premiers, maximum)
    facteurs = decomposer(n)
    plus_petit = facteurs[0][0]
    reste = n // plus_petit  # composé, puisque n a au moins trois facteurs premiers
    # erreur typique : un facteur oublié en route (on retire une occurrence d'un facteur au hasard)
    base_oubliee = rng.choice([b for b, _ in facteurs])
    oublie = [(b, e - 1 if b == base_oubliee else e) for b, e in facteurs]
    produit_oublie = ecrire_produit([(b, e) for b, e in oublie if e > 0])
    return exercice_v2(
        id=f"decomposer-{n}",
        type="nombre",
        difficulte=difficulte,
        enonce=rng.choice(_TOURNURES_DECOMPOSER).format(n=n),
        reponse={"valeur": n, "forme": "produit_premiers"},
        indices={
            "relance": f"Quel est le plus petit nombre premier qui divise {n} ?",
            "methode": "Divise par 2 tant que c'est possible, puis essaie 3, puis 5, puis 7… jusqu'à obtenir 1. "
            "Regroupe ensuite les facteurs égaux avec des puissances.",
            "etape": f"Première étape : {n} = {plus_petit} × {reste}. Continue avec {reste}.",
        },
        pieges=[
            piege_valeur(
                produit_oublie,
                f"Ton produit fait {n // base_oubliee}, pas {n} : il manque un facteur. "
                "Recompte combien de fois tu as divisé par chaque nombre premier.",
            ),
            piege_diagnostic(
                "facteur_non_premier",
                f"Ton produit fait bien {n}, mais un de tes facteurs n'est pas premier. "
                "Lequel peux-tu encore décomposer ?",
            ),
            piege_diagnostic("produit_faux", f"Recalcule ton produit : il ne donne pas {n}. As-tu oublié un facteur ?"),
        ],
        solution=f"{chaine_divisions(n)}, donc {n} = {joli_produit(facteurs)}. "
        f"Vérification : le produit fait bien {n}, et {', '.join(str(b) for b, _ in facteurs)} sont premiers.",
        lieu=f"{NOTION}/decomposer/{n}",
    )


# --- variante 2 : reconnaître les nombres premiers ---------------------------------------------------

_PALIERS_RECONNAITRE = {
    # difficulté : (nombres premiers candidats, faux amis impairs (composés), avec 1 et un pair ?)
    1: ((11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47), (21, 27, 33, 39, 45, 49, 51, 57), True),
    2: ((41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97), (51, 57, 63, 69, 77, 81, 87, 91, 93, 99), False),
    3: (
        (101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157),
        (111, 117, 119, 121, 123, 129, 133, 141, 143, 147, 153, 159),
        False,
    ),
}


def _pourquoi_compose(n: int) -> str:
    """La question qui fait trouver un diviseur de n (sans le donner tout cuit quand un critère existe)."""
    p = decomposer(n)[0][0]
    if p == 2:
        return f"{n} est pair. Est-il premier ?"
    if p == 3:
        return f"La somme des chiffres de {n} est {sum(map(int, str(n)))}. Que dit le critère de divisibilité par 3 ?"
    if p == 5:
        return f"{n} se termine par 5. Par quel nombre est-il divisible ?"
    return f"{n} est impair, mais est-il dans la table de {p} ?"


def _reconnaitre(rng: random.Random, difficulte: int) -> dict[str, Any]:
    premiers, composes, faciles = palier(_PALIERS_RECONNAITRE, difficulte)
    nb_premiers = rng.choice((2, 3))
    bons = rng.sample(premiers, nb_premiers)
    faux = rng.sample(composes, 5 - nb_premiers - (2 if faciles else 0))
    if faciles:
        faux += [1, rng.choice((12, 14, 16, 18, 20, 22, 24, 26, 28))]
    nombres = bons + faux
    rng.shuffle(nombres)
    options = [{"id": lettre, "texte": str(n)} for lettre, n in zip("abcde", nombres, strict=True)]
    bonnes = [o["id"] for o in options if est_premier(int(o["texte"]))]
    pieges: list[dict[str, Any]] = []
    for o in options:
        n = int(o["texte"])
        if n == 1:
            pieges.append(
                piege_contient([o["id"]], "1 n'a qu'un seul diviseur. Un nombre premier en a exactement deux.")
            )
        elif not est_premier(n):
            pieges.append(piege_contient([o["id"]], _pourquoi_compose(n)))
    pieges.append(
        piege_diagnostic(
            "incomplet", "Il y a au moins une autre bonne réponse. Teste chaque nombre qui reste avec 2, 3, 5, 7…"
        )
    )
    explications = []
    for n in sorted(nombres):
        if n == 1:
            explications.append("1 n'est pas premier (un seul diviseur)")
        elif est_premier(n):
            explications.append(f"{n} est premier")
        else:
            explications.append(f"{n} = {joli_produit(decomposer(n))} n'est pas premier")
    plus_grand = max(nombres)
    limite = next(p for p in (2, 3, 5, 7, 11, 13) if p * p > plus_grand)
    return exercice_v2(
        id="reconnaitre-" + "-".join(map(str, nombres)),
        type="choix",
        difficulte=difficulte,
        enonce="Parmi ces nombres, lesquels sont premiers ? (Il peut y en avoir plusieurs.)",
        reponse={"options": options, "bonnes": bonnes},
        indices={
            "relance": "Combien de diviseurs un nombre premier a-t-il exactement ?",
            "methode": f"Pour chaque nombre, teste la divisibilité par les nombres premiers 2, 3, 5, 7… "
            f"On peut s'arrêter à {limite} : {limite} × {limite} dépasse tous ces nombres. "
            "Un nombre plus grand que 1 qui n'est divisible par aucun d'eux est premier.",
            "etape": "Commence par éliminer les nombres pairs et ceux qui se terminent par 5. "
            "Pour les autres, additionne leurs chiffres (critère de 3), puis essaie les nombres premiers suivants.",
        },
        pieges=pieges,
        solution=" ; ".join(explications) + ".",
        lieu=f"{NOTION}/reconnaitre/{'-'.join(map(str, nombres))}",
    )


# --- variante 3 : partage maximal (PGCD par décomposition) ----------------------------------------------

_PALIERS_SACHETS = {
    # difficulté : (PGCD possibles, plus grand cofacteur)
    1: ((4, 6, 8, 9, 10, 12), 9),
    2: ((12, 15, 18, 20, 24, 28, 30, 36), 12),
    3: ((36, 42, 48, 54, 60, 72, 84, 90, 100), 15),
}


def _sachets(rng: random.Random, difficulte: int) -> dict[str, Any]:
    pgcds, cofacteur_max = palier(_PALIERS_SACHETS, difficulte)
    g = rng.choice(pgcds)
    x, y = couple_premiers_entre_eux(rng, 2, cofacteur_max)
    a, b = g * x, g * y
    qui = personnage(rng)
    objets = lots(rng)
    pieges: list[dict[str, Any]] = []
    diviseur = max(d for d in range(1, g) if g % d == 0)  # plus grand diviseur commun non maximal
    if diviseur > 1:  # 1 divise tout : ce n'est pas une erreur de raisonnement, juste pas une réponse
        pieges.append(
            piege_valeur(
                diviseur,
                f"{diviseur} divise bien {a} et {b}, mais ce n'est pas le plus grand diviseur commun. "
                "Compare les décompositions : as-tu pris tous les facteurs communs ?",
            )
        )
    pieges.append(
        piege_valeur(
            a * y,
            f"{a * y} est un multiple commun de {a} et {b}, pas un diviseur. "
            f"On cherche un nombre de {objets.lots} qui divise les deux quantités.",
        )
    )
    # selon le tirage, ce piège peut être la bonne réponse ou déjà intercepté : exercice_v2 l'écarte alors
    pieges.append(
        piege_valeur(
            min(x, y),
            f"Ce nombre, c'est ce qu'il y aurait dans chaque {objets.lot} pour une des deux sortes, "
            f"pas le nombre de {objets.lots}. Quel nombre divise à la fois {a} et {b} ?",
        )
    )
    return exercice_v2(
        id=f"sachets-{a}-{b}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"{qui.prenom} a {a} {objets.objets_a} et {b} {objets.objets_b}. {qui.Pronom} veut faire des "
        f"{objets.lots} tous identiques, en utilisant tout. Quel est le plus grand nombre de {objets.lots} possible ?",
        reponse={"valeur": g, "forme": "entier"},
        indices={
            "relance": f"Le nombre de {objets.lots} doit diviser à la fois {a} et {b}. "
            "Quels nombres divisent les deux ?",
            "methode": "Décompose les deux nombres en facteurs premiers, puis garde les facteurs communs, "
            "chacun avec le plus petit exposant : leur produit est le plus grand diviseur commun.",
            "etape": f"{a} = {produit_developpe(a)} et {b} = {produit_developpe(b)}. "
            "Quels facteurs premiers apparaissent dans les deux, et combien de fois ?",
        },
        pieges=pieges,
        solution=f"{a} = {joli_produit(decomposer(a))} et {b} = {joli_produit(decomposer(b))}. "
        f"Les facteurs communs donnent {joli_produit(decomposer(g))} = {g}. "
        f"On peut faire {g} {objets.lots}, avec {x} {objets.objets_a} et {y} {objets.objets_b} dans chacun.",
        lieu=f"{NOTION}/sachets/{a}-{b}",
    )


# --- variante 4 : fraction irréductible ------------------------------------------------------------------

_PALIERS_FRACTION = {
    # difficulté : (facteurs communs possibles, plus grand numérateur/dénominateur réduit)
    1: ((2, 3, 4, 5, 6), 9),
    2: ((6, 8, 9, 10, 12, 14, 15), 12),
    3: ((12, 18, 20, 24, 28, 30, 36, 42), 15),
}


def _fraction(rng: random.Random, difficulte: int) -> dict[str, Any]:
    communs, maximum = palier(_PALIERS_FRACTION, difficulte)
    g = rng.choice(communs)
    p, q = couple_premiers_entre_eux(rng, 2, maximum)
    a, b = g * p, g * q
    premier_commun = decomposer(g)[0][0]
    return exercice_v2(
        id=f"fraction-{a}-{b}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Rends la fraction {a}/{b} irréductible en utilisant les décompositions en facteurs premiers.",
        reponse={"valeur": f"{p}/{q}", "forme": "fraction_irreductible"},
        indices={
            "relance": f"Quel nombre premier divise à la fois {a} et {b} ?",
            "methode": "Décompose le numérateur et le dénominateur en facteurs premiers, puis barre les facteurs "
            "qui apparaissent dans les deux. Ce qui reste en haut et en bas donne la fraction irréductible.",
            "etape": f"{premier_commun} divise {a} et {b}. Divise les deux par {premier_commun}, "
            "puis regarde si on peut continuer.",
        },
        pieges=[
            piege_valeur(f"{q}/{p}", "Tu as échangé le numérateur et le dénominateur. Le numérateur reste en haut."),
            piege_diagnostic(
                "non_irreductible",
                "Ta fraction est égale à celle de départ, mais on peut encore la simplifier : "
                "le numérateur et le dénominateur ont encore un facteur premier commun.",
            ),
            piege_diagnostic(
                "pas_une_fraction",
                "La valeur est bonne, mais on attend une fraction irréductible, pas un nombre décimal.",
            ),
            piege_diagnostic(
                "valeur_fausse",
                "Ta fraction n'est pas égale à celle de départ. On divise le numérateur ET le dénominateur "
                "par le même nombre.",
            ),
        ],
        solution=f"{a} = {joli_produit(decomposer(a))} et {b} = {joli_produit(decomposer(b))}. "
        f"Les facteurs communs font {g}. Donc {a}/{b} = ({p} × {g})/({q} × {g}) = {p}/{q}.",
        lieu=f"{NOTION}/fraction/{a}-{b}",
    )


# --- point d'entrée -----------------------------------------------------------------------------------

_VARIANTES = {"decomposer": _decomposer, "reconnaitre": _reconnaitre, "sachets": _sachets, "fraction": _fraction}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
