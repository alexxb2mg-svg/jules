"""Générateur déterministe pour la notion `probabilites-deux-epreuves` (mathématiques, 3e).

  - deux_des   : deux dés équilibrés, tableau à double entrée : somme, double, « au moins un »   (nombre)
  - enchainees : deux épreuves différentes (pièce, dé, roue, sac) : P(A puis B) = P(A) × P(B)     (nombre)
  - remise     : deux tirages dans un sac, avec ou sans remise                                   (nombre)
  - associer   : relier des événements de deux dés à leur probabilité                            (association)

Pièges de la fiche v2 : croire que toutes les sommes de deux dés sont aussi probables, compter (1 ; 2)
et (2 ; 1) comme une seule issue, confondre tirage avec remise et sans remise. S'y ajoutent : additionner
les probabilités d'une branche au lieu de les multiplier, compter 6 + 6 issues au lieu de 6 × 6.

Réponses exactes (« 1/6 ») ; au palier 3, la fraction irréductible est exigée.
"""

from __future__ import annotations

import random
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from jules.generateurs.briques import (
    exercice_v2,
    generer_notion,
    palier,
    piege_diagnostic,
    piege_valeur,
)
from jules.generateurs.briques.algebre import valeur_machine
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "probabilites-deux-epreuves"
VARIANTES = ("deux_des", "enchainees", "remise", "associer")

# (singulier, pluriel), noms féminins : « une boule verte », « 3 boules vertes »
_COULEURS = (
    ("rouge", "rouges"),
    ("verte", "vertes"),
    ("bleue", "bleues"),
    ("jaune", "jaunes"),
    ("noire", "noires"),
    ("blanche", "blanches"),
)

Couple = tuple[int, int]


def _fraction(x: Fraction) -> str:
    return f"{x.numerator}/{x.denominator}"


def _brute(favorables: int, total: int) -> str:
    """« 6/36 = 1/6 » : la fraction telle qu'on la compte, puis simplifiée si elle se simplifie."""
    p = Fraction(favorables, total)
    brute = f"{favorables}/{total}"
    return brute if p.denominator == total else f"{brute} = {_fraction(p)}"


def _reponse(p: Fraction, irreductible: bool) -> dict[str, Any]:
    return {"valeur": valeur_machine(p), "forme": "fraction_irreductible" if irreductible else "libre"}


def _pieges_fin(irreductible: bool, relance: str) -> list[dict[str, Any]]:
    pieges = []
    if irreductible:
        pieges.append(
            piege_diagnostic(
                "non_irreductible",
                "C'est la bonne probabilité, mais la fraction se simplifie encore : divise en haut et en bas "
                "par un diviseur commun.",
            )
        )
    pieges.append(piege_diagnostic("valeur_fausse", relance))
    return pieges


def _couples(n1: int, n2: int) -> list[Couple]:
    return [(a, b) for a in range(1, n1 + 1) for b in range(1, n2 + 1)]


def _non_ordonnes(couples: list[Couple]) -> int:
    """Nombre de paires si l'on confond (1 ; 2) et (2 ; 1) : l'erreur de la fiche."""
    return len({tuple(sorted(c)) for c in couples})


def _slug(texte: str) -> str:
    """« une somme égale à 7 » -> « une_somme_egale_a_7 » : un identifiant sans accent ni espace."""
    ascii_ = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_.lower()).strip("_")


def _pluriel(n: int, mot: str) -> str:
    return f"{n} {mot}{'s' if n > 1 else ''}"


def _liste(couples: list[Couple]) -> str:
    return ", ".join(f"({a} ; {b})" for a, b in couples)


# --- variante 1 : deux dés -------------------------------------------------------------------------------


@dataclass(frozen=True)
class _EvenementDes:
    nom: str  # complète « Quelle est la probabilité d'obtenir ... ? »
    test: Callable[[int, int], bool]
    # erreurs propres à l'événement : (nombre de cases favorables compté par l'élève, relance)
    erreurs: tuple[tuple[int, str], ...] = ()


def _evenements_des(rng: random.Random, n1: int, n2: int, difficulte: int) -> list[_EvenementDes]:
    s = rng.randint(3, n1 + n2 - 1)
    k = rng.randint(1, min(n1, n2))
    evenements = [_EvenementDes(f"une somme égale à {s}", lambda a, b: a + b == s)]
    if n1 == n2:
        evenements.append(
            _EvenementDes(
                "un double (deux fois le même nombre)",
                lambda a, b: a == b,
                ((1, "Il y a plusieurs doubles possibles : (1 ; 1), (2 ; 2)... Compte-les tous."),),
            )
        )
    seuil = rng.randint(4, n1 + n2 - 2)
    evenements += [
        _EvenementDes(
            f"une somme supérieure ou égale à {seuil}",
            lambda a, b: a + b >= seuil,
            (
                (
                    sum(a + b > seuil for a, b in _couples(n1, n2)),
                    f"« Supérieure ou égale à {seuil} » : la somme {seuil} elle-même convient aussi.",
                ),
            ),
        ),
        _EvenementDes(
            f"une somme strictement inférieure à {seuil}",
            lambda a, b: a + b < seuil,
            (
                (
                    sum(a + b <= seuil for a, b in _couples(n1, n2)),
                    f"« Strictement inférieure à {seuil} » : la somme {seuil} elle-même ne convient pas.",
                ),
            ),
        ),
    ]
    if difficulte > 1:
        evenements.append(
            _EvenementDes(
                f"au moins un {k}",
                lambda a, b: k in (a, b),
                (
                    (
                        n1 + n2,
                        f"La case ({k} ; {k}) contient deux fois le {k}, mais c'est une seule case : "
                        "ne la compte qu'une fois.",
                    ),
                ),
            )
        )
    if difficulte > 2:
        evenements.append(
            _EvenementDes(
                "un produit pair",
                lambda a, b: a * b % 2 == 0,
                ((n1 * n2 // 2, "Il suffit qu'UN des deux nombres soit pair pour que le produit soit pair."),),
            )
        )
    return evenements


_PALIERS_DEUX_DES = {
    # difficulté : (faces des deux dés possibles, irréductible ?)
    1: (((6, 6), (4, 4), (8, 8)), False),
    2: (((6, 6), (4, 6), (8, 8)), False),
    3: (((6, 6), (4, 6), (6, 8), (8, 8)), True),
}


def _deux_des(rng: random.Random, difficulte: int) -> dict[str, Any]:
    paires_de_des, irreductible = palier(_PALIERS_DEUX_DES, difficulte)

    def fabrique() -> tuple[int, int, _EvenementDes]:
        n1, n2 = rng.choice(paires_de_des)
        return n1, n2, rng.choice(_evenements_des(rng, n1, n2, difficulte))

    def etape(n1: int, n2: int) -> str:
        return (
            f"Fais un tableau à double entrée : le premier dé en ligne ({n1} valeurs), le second en colonne "
            f"({n2} valeurs), soit {n1 * n2} cases. Colorie celles qui conviennent."
        )

    def accepte(t: tuple[int, int, _EvenementDes]) -> bool:
        n1, n2, ev = t
        favorables = [c for c in _couples(n1, n2) if ev.test(*c)]
        if not 0 < len(favorables) < n1 * n2:
            return False
        p = Fraction(len(favorables), n1 * n2)
        if irreductible and p.denominator == n1 * n2:  # au palier 3, une fraction à simplifier
            return False
        return not collision(p, etape(n1, n2))

    n1, n2, ev = tirer(rng, fabrique, accepte)
    total = n1 * n2
    favorables = [c for c in _couples(n1, n2) if ev.test(*c)]
    f = len(favorables)
    p = Fraction(f, total)
    pieges = [piege_valeur(valeur_machine(Fraction(e, total)), r) for e, r in ev.erreurs if 0 < e < total]
    if _non_ordonnes(favorables) != f:
        pieges.append(
            piege_valeur(
                valeur_machine(Fraction(_non_ordonnes(favorables), total)),
                "(1 ; 2) et (2 ; 1) sont deux issues différentes : le premier dé et le second ne sont pas les "
                "mêmes. Compte les deux.",
            )
        )
    if ev.nom.startswith("une somme égale"):
        pieges.append(
            piege_valeur(
                valeur_machine(Fraction(1, n1 + n2 - 1)),
                "Les sommes n'ont pas toutes la même chance : une somme du milieu s'obtient de plus de façons "
                "qu'une somme extrême.",
            )
        )
    pieges += [
        piege_valeur(
            valeur_machine(Fraction(f, n1 + n2)),
            f"Le nombre total d'issues est {n1} × {n2} (une case par couple), pas {n1} + {n2}.",
        ),
        piege_valeur(
            valeur_machine(Fraction(total, f)),
            "Une probabilité est toujours comprise entre 0 et 1 : ta fraction est à l'envers.",
        ),
        *_pieges_fin(irreductible, "Reprends le tableau et compte les cases favorables une par une."),
    ]
    des = (
        "deux dés équilibrés à 6 faces"
        if (n1, n2) == (6, 6)
        else (
            f"deux dés équilibrés à {n1} faces"
            if n1 == n2
            else f"un dé équilibré à {n1} faces et un dé équilibré à {n2} faces"
        )
    )
    detail = f" : {_liste(favorables)}" if f <= 12 else ""
    return exercice_v2(
        id=f"deux_des-{n1}-{n2}-{_slug(ev.nom)}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"On lance {des}. Quelle est la probabilité d'obtenir {ev.nom} ?"
        + (" Donne-la sous forme de fraction irréductible." if irreductible else ""),
        reponse=_reponse(p, irreductible),
        indices={
            "relance": "Quelles sont les issues de cette expérience ? Un seul nombre, ou un couple de nombres ?",
            "methode": "Chaque couple (premier dé ; second dé) a la même chance. P = nombre de cases "
            "favorables ÷ nombre total de cases du tableau.",
            "etape": etape(n1, n2),
        },
        pieges=pieges,
        solution=f"Le tableau compte {n1} × {n2} = {total} cases équiprobables. {f} cases conviennent{detail}. "
        f"P = {_brute(f, total)}.",
        lieu=f"{NOTION}/deux_des/{n1}-{n2}-{ev.nom}",
    )


# --- variante 2 : deux épreuves différentes enchaînées ---------------------------------------------------


@dataclass(frozen=True)
class _Epreuve:
    description: str  # « une pièce équilibrée »
    total: int
    evenements: tuple[tuple[str, int], ...]  # (événement, issues favorables)


def _epreuves(rng: random.Random, difficulte: int) -> list[_Epreuve]:
    faces = rng.choice((4, 6, 8))
    k = rng.randint(2, faces - 1)
    secteurs = rng.choice((5, 8, 10))
    rouges = rng.randint(1, secteurs - 2)
    bleus = rng.randint(1, secteurs - rouges - 1)
    boules = rng.randint(4, 10)
    vertes = rng.randint(1, boules - 1)
    epreuves = [
        _Epreuve("une pièce équilibrée", 2, (("« pile »", 1), ("« face »", 1))),
        _Epreuve(
            f"un dé équilibré à {faces} faces",
            faces,
            (
                ("un nombre pair", faces // 2),
                (f"un {k}", 1),
                (f"un nombre supérieur ou égal à {k}", faces - k + 1),
            ),
        ),
        _Epreuve(
            f"une roue partagée en {secteurs} secteurs égaux ({_pluriel(rouges, 'rouge')}, "
            f"{_pluriel(bleus, 'bleu')}, {_pluriel(secteurs - rouges - bleus, 'jaune')})",
            secteurs,
            (
                ("un secteur rouge", rouges),
                ("un secteur bleu", bleus),
                ("un secteur qui n'est pas jaune", rouges + bleus),
            ),
        ),
        _Epreuve(
            f"un sac de {boules} boules ({_pluriel(vertes, 'verte')}, les autres blanches) dans lequel on tire "
            "une boule",
            boules,
            (("une boule verte", vertes), ("une boule blanche", boules - vertes)),
        ),
    ]
    if difficulte == 1:  # d'abord une pièce, puis autre chose
        return epreuves
    return epreuves[1:]


def _enchainees(rng: random.Random, difficulte: int) -> dict[str, Any]:
    irreductible = difficulte == 3

    def fabrique() -> tuple[_Epreuve, tuple[str, int], _Epreuve, tuple[str, int]]:
        epreuves = _epreuves(rng, difficulte)
        premiere = epreuves[0] if difficulte == 1 else rng.choice(epreuves)
        seconde = rng.choice([e for e in epreuves if e is not premiere])
        return premiere, rng.choice(premiere.evenements), seconde, rng.choice(seconde.evenements)

    def probas(t: tuple[_Epreuve, tuple[str, int], _Epreuve, tuple[str, int]]) -> tuple[Fraction, Fraction]:
        e1, (_, f1), e2, (_, f2) = t
        return Fraction(f1, e1.total), Fraction(f2, e2.total)

    def etape(pa: Fraction, pb: Fraction) -> str:
        return (
            f"La probabilité de la première issue est {_fraction(pa)}, celle de la seconde est {_fraction(pb)}. "
            "Suis la branche de l'arbre qui correspond aux deux."
        )

    def accepte(t: tuple[_Epreuve, tuple[str, int], _Epreuve, tuple[str, int]]) -> bool:
        pa, pb = probas(t)
        p = pa * pb
        if pa == 1 or pb == 1:
            return False
        if irreductible and p.denominator == t[0].total * t[2].total:  # au palier 3, un produit à simplifier
            return False
        return not collision(p, etape(pa, pb))

    tirage = tirer(rng, fabrique, accepte)
    e1, (a, _), e2, (b, _) = tirage
    pa, pb = probas(tirage)
    p = pa * pb
    pieges = [
        piege_valeur(
            valeur_machine(pa + pb),
            "Le long d'une branche de l'arbre, on MULTIPLIE les probabilités, on ne les additionne pas.",
        ),
        piege_valeur(valeur_machine(pa), "Tu n'as tenu compte que de la première épreuve : il en faut deux."),
        piege_valeur(valeur_machine(pb), "Tu n'as tenu compte que de la seconde épreuve : il en faut deux."),
        *_pieges_fin(irreductible, "Calcule chaque probabilité séparément, puis multiplie-les."),
    ]
    return exercice_v2(
        id=f"enchainees-{e1.total}-{_slug(a)}-{e2.total}-{_slug(b)}-{_slug(e2.description)}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"On utilise d'abord {e1.description}, puis {e2.description}. Quelle est la probabilité "
        f"d'obtenir {a} à la première épreuve, puis {b} à la seconde ?"
        + (" Donne-la sous forme de fraction irréductible." if irreductible else ""),
        reponse=_reponse(p, irreductible),
        indices={
            "relance": "Le résultat de la première épreuve change-t-il les chances de la seconde ?",
            "methode": "Dessine un arbre : une branche par issue. La probabilité d'un chemin est le produit des "
            "probabilités lues sur ses branches.",
            "etape": etape(pa, pb),
        },
        pieges=pieges,
        solution=f"P({a}) = {_fraction(pa)} et P({b}) = {_fraction(pb)}. Sur l'arbre, on multiplie le long "
        f"du chemin : P = {_fraction(pa)} × {_fraction(pb)} = {_fraction(p)}.",
        lieu=f"{NOTION}/enchainees/{e1.description}-{a}-{e2.description}-{b}",
    )


# --- variante 3 : deux tirages, avec ou sans remise ------------------------------------------------------

_PALIERS_REMISE = {
    # difficulté : (remise ?, événement)
    1: (True, "deux_a"),
    2: (False, "deux_a"),
    3: (False, "melange"),
}


def _compte(n: int, couleur: tuple[str, str]) -> str:
    return f"{n} boule{'s' if n > 1 else ''} {couleur[1] if n > 1 else couleur[0]}"


def _remise(rng: random.Random, difficulte: int) -> dict[str, Any]:
    avec, evenement = palier(_PALIERS_REMISE, difficulte)
    couleur_a, couleur_b = rng.sample(_COULEURS, 2)
    irreductible = difficulte == 3
    differentes = evenement == "melange" and rng.random() < 0.5

    def probabilites(r: int, v: int) -> tuple[Fraction, Fraction]:
        """(probabilité demandée, la même dans l'autre mode de tirage)."""
        n = r + v
        if evenement == "deux_a":
            avec_remise, sans_remise = Fraction(r * r, n * n), Fraction(r * (r - 1), n * (n - 1))
        elif differentes:
            avec_remise, sans_remise = Fraction(2 * r * v, n * n), Fraction(2 * r * v, n * (n - 1))
        else:
            avec_remise = Fraction(r * r + v * v, n * n)
            sans_remise = Fraction(r * (r - 1) + v * (v - 1), n * (n - 1))
        return (avec_remise, sans_remise) if avec else (sans_remise, avec_remise)

    def etape(r: int, v: int) -> str:
        n = r + v
        if avec:
            return (
                f"Au premier tirage, il y a {r} {couleur_a[1]} sur {n} boules. La boule est remise : au second "
                "tirage, rien n'a changé. Multiplie les deux probabilités."
            )
        return (
            f"Au premier tirage, il y a {n} boules. La boule n'est pas remise : au second tirage, il n'en reste "
            f"que {n - 1}. Fais un arbre et multiplie le long de chaque chemin."
        )

    def accepte(t: tuple[int, int]) -> bool:
        r, v = t
        p, autre = probabilites(r, v)
        if p == autre or p == 0:
            return False
        return not collision(p, etape(r, v))

    r, v = tirer(rng, lambda: (rng.randint(2, 7), rng.randint(1, 7)), accepte)
    n = r + v
    p, autre = probabilites(r, v)
    mode = "la remet dans le sac" if avec else "ne la remet pas"
    pieges = [
        piege_valeur(
            valeur_machine(autre),
            "Relis l'énoncé : la première boule est remise dans le sac, le second tirage se fait avec toutes "
            "les boules."
            if avec
            else "Relis l'énoncé : la première boule n'est pas remise, il reste une boule de moins au second tirage.",
        )
    ]
    if evenement == "deux_a":
        question = f"deux boules {couleur_a[1]}"
        pieges += [
            piege_valeur(
                valeur_machine(Fraction(r, n)), "Il y a deux tirages : il faut deux boules de cette couleur, pas une."
            ),
            piege_valeur(
                valeur_machine(Fraction(2 * r, n)),
                "Le long d'un chemin de l'arbre, on multiplie les probabilités, on ne les additionne pas.",
            ),
        ]
        if not avec:
            pieges.append(
                piege_valeur(
                    valeur_machine(Fraction(r * (r - 1), n * n)),
                    f"Au second tirage, il ne reste que {n - 1} boules en tout : le dénominateur change aussi.",
                )
            )
        chemins = f"{_fraction(Fraction(r, n))} × " + (_fraction(Fraction(r, n)) if avec else f"{r - 1}/{n - 1}")
    elif differentes:
        question = "deux boules de couleurs différentes"
        pieges.append(
            piege_valeur(
                valeur_machine(Fraction(r * v, n * (n - 1))),
                f"« Couleurs différentes », c'est {couleur_a[0]} puis {couleur_b[0]}, OU {couleur_b[0]} puis "
                f"{couleur_a[0]} : deux chemins de l'arbre.",
            )
        )
        chemins = f"{r}/{n} × {v}/{n - 1} + {v}/{n} × {r}/{n - 1}"
    else:
        question = "deux boules de la même couleur"
        pieges += [
            piege_valeur(
                valeur_machine(Fraction(r * (r - 1), n * (n - 1))),
                f"« De la même couleur », c'est deux {couleur_a[1]} OU deux {couleur_b[1]} : deux chemins.",
            ),
            piege_valeur(
                valeur_machine(Fraction(v * (v - 1), n * (n - 1))),
                f"« De la même couleur », c'est deux {couleur_a[1]} OU deux {couleur_b[1]} : deux chemins.",
            ),
        ]
        chemins = f"{r}/{n} × {r - 1}/{n - 1} + {v}/{n} × " + (f"{v - 1}/{n - 1}" if v > 1 else "0")
    pieges += _pieges_fin(irreductible, "Fais l'arbre des deux tirages, puis multiplie le long de chaque chemin.")
    return exercice_v2(
        id=f"remise-{'avec' if avec else 'sans'}-{r}-{v}-{'differentes' if differentes else evenement}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Un sac contient {_compte(r, couleur_a)} et {_compte(v, couleur_b)}. On tire une boule au hasard, "
        f"on {mode}, puis on tire une seconde boule. Quelle est la probabilité d'obtenir {question} ?"
        + (" Donne-la sous forme de fraction irréductible." if irreductible else ""),
        reponse=_reponse(p, irreductible),
        indices={
            "relance": "Après le premier tirage, combien reste-t-il de boules dans le sac ?",
            "methode": "Fais un arbre à deux niveaux. Sur chaque branche, écris la probabilité ; on multiplie le "
            "long d'un chemin, puis on additionne les chemins qui conviennent.",
            "etape": etape(r, v),
        },
        pieges=pieges,
        solution=f"Il y a {n} boules. P = {chemins} = {_fraction(p)}.",
        lieu=f"{NOTION}/remise/{'avec' if avec else 'sans'}-{r}-{v}-{evenement}",
    )


# --- variante 4 : associer des événements à leur probabilité --------------------------------------------


def _pool_associer(rng: random.Random, difficulte: int) -> list[tuple[str, int]]:
    """(événement, cases favorables sur 36) pour deux dés à 6 faces."""
    couples = _couples(6, 6)

    def compte(test: Callable[[int, int], bool]) -> int:
        return sum(test(a, b) for a, b in couples)

    pool = [(f"une somme égale à {s}", sum(a + b == s for a, b in couples)) for s in range(2, 13)]
    if difficulte > 1:
        k = rng.randint(1, 6)
        p = rng.choice((4, 6, 12))
        pool += [
            ("un double", compte(lambda a, b: a == b)),
            ("une somme paire", compte(lambda a, b: (a + b) % 2 == 0)),
            (f"au moins un {k}", compte(lambda a, b: k in (a, b))),
            ("deux nombres pairs", compte(lambda a, b: a % 2 == 0 and b % 2 == 0)),
            (f"un produit égal à {p}", compte(lambda a, b: a * b == p)),
        ]
    return pool


_PALIERS_ASSOCIER = {1: (3, False), 2: (4, False), 3: (4, True)}  # difficulté : (événements, leurre ?)
_DROITE = "vwxyz"


def _associer(rng: random.Random, difficulte: int) -> dict[str, Any]:
    nombre, leurre = palier(_PALIERS_ASSOCIER, difficulte)

    def fabrique() -> list[tuple[str, int]]:
        return rng.sample(_pool_associer(rng, difficulte), nombre)

    def accepte(choisis: list[tuple[str, int]]) -> bool:
        probas = [Fraction(f, 36) for _, f in choisis]
        if len(set(probas)) != nombre:  # une probabilité par événement, sans doublon à droite
            return False
        # le leurre (sommes crues équiprobables : 1/11) ne doit être la probabilité d'aucun événement
        return not leurre or Fraction(1, 11) not in probas

    choisis = tirer(rng, fabrique, accepte)
    probas = [Fraction(f, 36) for _, f in choisis]
    droite_valeurs = probas + ([Fraction(1, 11)] if leurre else [])
    rng.shuffle(droite_valeurs)
    ids_droite = {p: _DROITE[i] for i, p in enumerate(droite_valeurs)}
    gauche = [{"id": "abcd"[i], "texte": nom} for i, (nom, _) in enumerate(choisis)]
    droite = [{"id": ids_droite[p], "texte": _fraction(p)} for p in droite_valeurs]
    paires = {"abcd"[i]: ids_droite[p] for i, p in enumerate(probas)}
    details = " ; ".join(f"{nom} : {_pluriel(f, 'case')}, {_brute(f, 36)}" for nom, f in choisis)
    return exercice_v2(
        id=f"associer-{'-'.join(str(f) for _, f in choisis)}-{''.join(paires.values())}",
        type="association",
        difficulte=difficulte,
        enonce="On lance deux dés équilibrés à 6 faces. Relie chaque événement à sa probabilité."
        + (" Une des probabilités proposées ne correspond à aucun événement." if leurre else ""),
        reponse={"gauche": gauche, "droite": droite, "paires": paires},
        indices={
            "relance": "Combien y a-t-il d'issues quand on lance deux dés ? Ont-elles toutes la même chance ?",
            "methode": "Fais le tableau à double entrée des 36 couples équiprobables. Pour chaque événement, "
            "compte ses cases et divise par 36.",
            "etape": "Pour une somme, lis les diagonales du tableau : la somme 7 occupe la plus longue, les "
            "sommes 2 et 12 une seule case chacune.",
        },
        pieges=[
            piege_diagnostic(
                "une_erreur", "Une seule association est fausse : recompte les cases des événements dans le tableau."
            ),
            piege_diagnostic(
                "associations_fausses",
                "Les sommes de deux dés ne sont pas équiprobables : fais le tableau des 36 couples et compte les "
                "cases de chaque événement.",
            ),
        ],
        solution=f"Sur 36 cases équiprobables : {details}."
        + (" La probabilité 1/11 ne correspond à rien : elle suppose les 11 sommes équiprobables." if leurre else ""),
        lieu=f"{NOTION}/associer/{'-'.join(nom for nom, _ in choisis)}",
    )


_VARIANTES = {
    "deux_des": _deux_des,
    "enchainees": _enchainees,
    "remise": _remise,
    "associer": _associer,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
