"""Générateur déterministe pour la notion `probabilites-experiences-simples` (mathématiques, 3e).

  - urne      : tirer une boule dans un sac : P(une couleur), puis P(une couleur ou une autre)   (nombre)
  - de_roue   : dé ou roue équilibrés, numérotés : P(pair, multiple, premier, supérieur à...)    (nombre)
  - contraire : probabilité de l'événement contraire (décimal, fraction, « ni A ni B »)          (nombre)
  - hasard    : raisonner : la pièce sans mémoire, fréquence et probabilité, issues non
                équiprobables                                                                  (choix)

Pièges de la fiche v2 : une probabilité plus grande que 1 ou négative, « favorables / total » appliqué à
des issues qui n'ont pas la même chance, croire qu'après plusieurs « pile » le « face » devient plus
probable, confondre fréquence observée et probabilité.

Réponses exactes : « 3/10 » (forme libre : 6/20 ou 0,3 sont justes aussi) ; au palier 3, la fraction
irréductible est exigée.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable
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
from jules.generateurs.briques.algebre import valeur_machine
from jules.generateurs.briques.format_fr import nombre_fr, nombre_machine
from jules.generateurs.briques.habillage import personnage
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "probabilites-experiences-simples"
VARIANTES = ("urne", "de_roue", "contraire", "hasard")

_LETTRES = "abcdef"


def _fraction(x: Fraction) -> str:
    """Une probabilité écrite en fraction, même quand elle se simplifie en entier : « 3/10 »."""
    return f"{x.numerator}/{x.denominator}"


def _brute(favorables: int, total: int) -> str:
    """« 6/20 », puis « = 3/10 » si la fraction se simplifie : le calcul tel qu'on l'écrit."""
    p = Fraction(favorables, total)
    brute = f"{favorables}/{total}"
    return brute if p.denominator == total else f"{brute} = {_fraction(p)}"


def _reponse(p: Fraction, irreductible: bool) -> dict[str, Any]:
    return {"valeur": valeur_machine(p), "forme": "fraction_irreductible" if irreductible else "libre"}


def _pieges_communs(favorables: int, total: int, irreductible: bool) -> list[dict[str, Any]]:
    """Les erreurs de toute probabilité « favorables / total »."""
    pieges = []
    if total - favorables > 0:
        pieges.append(
            piege_valeur(
                valeur_machine(Fraction(favorables, total - favorables)),
                "Tu as divisé par le nombre d'issues qui ne conviennent pas : divise par le nombre TOTAL d'issues.",
            )
        )
    pieges += [
        piege_valeur(
            valeur_machine(Fraction(total, favorables)),
            "Une probabilité est toujours comprise entre 0 et 1 : ta fraction est à l'envers.",
        ),
        piege_valeur(
            str(favorables),
            "Une probabilité est un nombre entre 0 et 1 : écris le nombre d'issues favorables sur le nombre "
            "total d'issues.",
        ),
    ]
    if irreductible:
        pieges.append(
            piege_diagnostic(
                "non_irreductible",
                "C'est la bonne probabilité, mais la fraction se simplifie encore : divise en haut et en bas "
                "par un diviseur commun.",
            )
        )
    pieges.append(
        piege_diagnostic("valeur_fausse", "Recompte les issues favorables une par une, puis le nombre total d'issues.")
    )
    return pieges


# --- variante 1 : tirage dans une urne ------------------------------------------------------------------

_COULEURS = (  # (singulier, pluriel), noms féminins : « une boule verte », « 3 boules vertes »
    ("rouge", "rouges"),
    ("verte", "vertes"),
    ("bleue", "bleues"),
    ("jaune", "jaunes"),
    ("noire", "noires"),
    ("blanche", "blanches"),
    ("violette", "violettes"),
)
_OBJETS = (("boule", "boules"), ("bille", "billes"), ("perle", "perles"))  # féminins, comme les couleurs

_PALIERS_URNE = {
    # difficulté : (nombre de couleurs, effectif max par couleur, deux couleurs demandées ?, irréductible ?)
    1: (2, 9, False, False),
    2: (3, 9, True, False),
    3: (4, 12, True, True),
}


def _compte(n: int, objet: tuple[str, str], couleur: tuple[str, str]) -> str:
    return f"{n} {objet[0] if n == 1 else objet[1]} {couleur[0] if n == 1 else couleur[1]}"


def _urne(rng: random.Random, difficulte: int) -> dict[str, Any]:
    nb_couleurs, maximum, deux, irreductible = palier(_PALIERS_URNE, difficulte)
    objet = rng.choice(_OBJETS)
    couleurs = rng.sample(_COULEURS, nb_couleurs)

    def fabrique() -> list[int]:
        return [rng.randint(1, maximum) for _ in couleurs]

    def accepte(effectifs: list[int]) -> bool:
        total = sum(effectifs)
        favorables = effectifs[0] + (effectifs[1] if deux else 0)
        p = Fraction(favorables, total)
        if len(set(effectifs)) == 1:  # toutes les couleurs à égalité : « 1 / nombre de couleurs » serait juste
            return False
        if irreductible and p.denominator == total:  # au palier 3, une fraction à simplifier
            return False
        # l'étape cite le nombre total d'objets
        return not collision(p, total)

    effectifs = tirer(rng, fabrique, accepte)
    total = sum(effectifs)
    favorables = effectifs[0] + (effectifs[1] if deux else 0)
    p = Fraction(favorables, total)
    contenu = ", ".join(_compte(n, objet, c) for n, c in zip(effectifs[:-1], couleurs[:-1], strict=True))
    contenu += f" et {_compte(effectifs[-1], objet, couleurs[-1])}"
    evenement = couleurs[0][0] + (f" ou {couleurs[1][0]}" if deux else "")
    pieges = _pieges_communs(favorables, total, irreductible)
    pieges.insert(
        0,
        piege_valeur(
            valeur_machine(Fraction(2 if deux else 1, nb_couleurs)),
            f"Les couleurs n'ont pas toutes le même nombre de {objet[1]} : ce sont les {objet[1]} qu'on "
            "compte, pas les couleurs.",
        ),
    )
    if deux:
        pieges[1:1] = [
            piege_valeur(
                valeur_machine(Fraction(effectifs[i], total)),
                f"« {couleurs[0][0].capitalize()} ou {couleurs[1][0]} » : compte les {objet[1]} des deux couleurs.",
            )
            for i in (0, 1)
        ]
    return exercice_v2(
        id=f"urne-{'-'.join(map(str, effectifs))}-{'ou' if deux else 'une'}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Un sac contient {contenu}, indiscernables au toucher. On tire une {objet[0]} au hasard. "
        f"Quelle est la probabilité qu'elle soit {evenement} ?"
        + (" Donne-la sous forme de fraction irréductible." if irreductible else ""),
        reponse=_reponse(p, irreductible),
        indices={
            "relance": f"Combien y a-t-il de {objet[1]} en tout ? Et combien conviennent ?",
            "methode": "Chaque objet a la même chance d'être tiré : P = nombre d'issues favorables ÷ nombre "
            "total d'issues.",
            "etape": f"Il y a {total} {objet[1]} en tout. Compte celles qui sont "
            + couleurs[0][1]
            + (f" ou {couleurs[1][1]}" if deux else "")
            + (" (additionne les deux couleurs)." if deux else "."),
        },
        pieges=pieges,
        solution=f"Il y a {' + '.join(map(str, effectifs))} = {total} {objet[1]}, toutes avec la même chance. "
        + (f"{effectifs[0]} + {effectifs[1]} = {favorables} conviennent" if deux else f"{favorables} conviennent")
        + f" : P = {_brute(favorables, total)}.",
        lieu=f"{NOTION}/urne/{'-'.join(map(str, effectifs))}",
    )


# --- variante 2 : dé ou roue équilibrés ------------------------------------------------------------------


def _est_premier(n: int) -> bool:
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


# un événement : (nom, test, (valeur de l'erreur typique en issues favorables, relance) ou None)
_Evenement = tuple[str, Callable[[int], bool], tuple[int, str] | None]


def _evenements(rng: random.Random, n: int, difficulte: int) -> list[_Evenement]:
    k = rng.randint(2, n - 2)
    m = rng.choice([x for x in (12, 18, 20, 24, 30, 36) if x >= n // 2])
    evenements: list[_Evenement] = [
        ("un nombre pair", lambda x: x % 2 == 0, None),
        ("un nombre impair", lambda x: x % 2 == 1, None),
        (
            f"un nombre strictement supérieur à {k}",
            lambda x: x > k,
            (1, f"« Strictement supérieur à {k} » : le nombre {k} lui-même ne convient pas."),
        ),
        (
            f"un nombre inférieur ou égal à {k}",
            lambda x: x <= k,
            (-1, f"« Inférieur ou égal à {k} » : le nombre {k} lui-même convient aussi."),
        ),
    ]
    d = rng.choice((3, 4, 5))
    evenements.append((f"un multiple de {d}", lambda x: x % d == 0, None))
    if difficulte > 1:
        evenements += [
            (
                "un nombre premier",
                _est_premier,
                (1, "Le nombre 1 n'est pas un nombre premier : il n'a qu'un diviseur."),
            ),
        ]
    if difficulte > 2:
        evenements.append(
            (
                f"un diviseur de {m}",
                lambda x: m % x == 0,
                (
                    -1,
                    f"As-tu pensé à 1 et à {m} lui-même ?"
                    if m <= n
                    else "As-tu pensé à 1 ? Il divise tous les nombres.",
                ),
            )
        )
    return evenements


_DES = (6, 8, 10, 12, 20)  # les dés équilibrés courants

_PALIERS_DE_ROUE = {
    # difficulté : (nombres d'issues possibles, irréductible ?)
    1: ((6, 8, 10), False),
    2: ((8, 10, 12, 20), False),
    3: ((12, 15, 16, 18, 20, 24), True),
}


def _de_roue(rng: random.Random, difficulte: int) -> dict[str, Any]:
    tailles, irreductible = palier(_PALIERS_DE_ROUE, difficulte)

    def fabrique() -> tuple[int, _Evenement]:
        n = rng.choice(tailles)
        return n, rng.choice(_evenements(rng, n, difficulte))

    def accepte(tirage: tuple[int, _Evenement]) -> bool:
        n, (_, test, _) = tirage
        favorables = sum(test(x) for x in range(1, n + 1))
        if not 0 < favorables < n:
            return False
        p = Fraction(favorables, n)
        if irreductible and p.denominator == n:
            return False
        return not collision(p, n)

    n, (nom, test, erreur) = tirer(rng, fabrique, accepte)
    # pas de dé à 15, 16, 18 ou 24 faces : ce sera une roue ; sinon, dé ou roue au hasard
    en_roue = n not in _DES or rng.random() < 0.5
    issues = [x for x in range(1, n + 1) if test(x)]
    favorables = len(issues)
    p = Fraction(favorables, n)
    pieges = _pieges_communs(favorables, n, irreductible)
    if erreur is not None and 0 < favorables + erreur[0] <= n:
        pieges.insert(0, piege_valeur(valeur_machine(Fraction(favorables + erreur[0], n)), erreur[1]))
    if en_roue:
        situation = (
            f"Une roue est partagée en {n} secteurs de même taille, numérotés de 1 à {n}. On la fait tourner : "
            f"quelle est la probabilité que la flèche s'arrête sur {nom} ?"
        )
    else:
        situation = (
            f"On lance un dé équilibré à {n} faces, numérotées de 1 à {n}. Quelle est la probabilité d'obtenir {nom} ?"
        )
    return exercice_v2(
        id=f"de_roue-{'roue' if en_roue else 'de'}-{n}-{'-'.join(map(str, issues))}",
        type="nombre",
        difficulte=difficulte,
        enonce=situation + (" Donne-la sous forme de fraction irréductible." if irreductible else ""),
        reponse=_reponse(p, irreductible),
        indices={
            "relance": "Combien y a-t-il d'issues possibles ? Ont-elles toutes la même chance ?",
            "methode": "Les issues sont équiprobables : P = nombre d'issues favorables ÷ nombre total d'issues. "
            "Écris la liste des issues favorables pour ne pas en oublier.",
            "etape": f"Il y a {n} issues possibles, de 1 à {n}. Parmi elles, écris la liste de celles qui "
            f"donnent {nom}, puis compte-les.",
        },
        pieges=pieges,
        solution=f"Issues favorables : {', '.join(map(str, issues))}. Il y en a {favorables} sur {n} issues "
        f"équiprobables, donc P = {_brute(favorables, n)}.",
        lieu=f"{NOTION}/de_roue/{n}-{nom}",
    )


# --- variante 3 : événement contraire --------------------------------------------------------------------

_CONTRAIRES = (  # (événement, événement contraire)
    ("qu'il pleuve demain", "qu'il ne pleuve pas demain"),
    ("qu'un joueur réussisse son tir au but", "qu'il le rate"),
    ("qu'une ampoule prise au hasard soit défectueuse", "qu'elle fonctionne"),
    ("qu'un ticket de tombola soit gagnant", "qu'il soit perdant"),
    ("que le bus arrive en retard", "qu'il ne soit pas en retard"),
    ("qu'une graine plantée germe", "qu'elle ne germe pas"),
)

_PALIERS_CONTRAIRE = {1: "decimal", 2: "fraction", 3: "ni_ni"}


def _contraire(rng: random.Random, difficulte: int) -> dict[str, Any]:
    forme = palier(_PALIERS_CONTRAIRE, difficulte)
    if forme == "ni_ni":
        return _ni_ni(rng, difficulte)
    evenement, contraire = rng.choice(_CONTRAIRES)

    def fabrique() -> Fraction:
        if forme == "decimal":
            return Fraction(rng.randint(1, 19) * 5, 100)
        den = rng.randint(3, 12)
        return Fraction(rng.randint(1, den - 1), den)

    def ecrit(p: Fraction) -> str:
        return nombre_fr(p) if forme == "decimal" else _fraction(p)

    def etape(p: Fraction) -> str:
        if forme == "decimal":
            return f"Calcule 1 − {ecrit(p)}."
        return f"Écris 1 sous la forme {p.denominator}/{p.denominator}, puis soustrais {ecrit(p)}."

    def accepte(p: Fraction) -> bool:
        if forme == "fraction" and p.denominator == 1:
            return False
        return p != Fraction(1, 2) and not collision(1 - p, etape(p), ecrit(p))

    p = tirer(rng, fabrique, accepte)
    q = 1 - p
    ecrit_q = nombre_fr(q) if forme == "decimal" else _fraction(q)
    machine = nombre_machine if forme == "decimal" else valeur_machine
    pieges = [
        piege_valeur(machine(p), "C'est la probabilité de l'événement lui-même, pas celle de son contraire."),
        piege_valeur(machine(1 + p), "Une probabilité ne dépasse jamais 1 : on retire P(A) de 1, on ne l'ajoute pas."),
    ]
    if forme == "fraction":
        pieges.append(
            piege_valeur(
                valeur_machine(Fraction(1 - p.numerator, p.denominator)),
                f"On ne soustrait pas seulement les numérateurs : 1, c'est {p.denominator}/{p.denominator}.",
            )
        )
    pieges.append(piege_diagnostic("valeur_fausse", "Un événement et son contraire ont des probabilités de somme 1."))
    enonce_p = ecrit(p)
    return exercice_v2(
        id=f"contraire-{forme}-{valeur_machine(p).replace('/', 'sur')}-{_CONTRAIRES.index((evenement, contraire))}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"La probabilité {evenement} est {enonce_p}. Quelle est la probabilité {contraire} ?",
        reponse={"valeur": machine(q), "forme": "libre"},
        indices={
            "relance": "Les deux événements peuvent-ils arriver en même temps ? L'un des deux arrive-t-il forcément ?",
            "methode": "Pour un événement A et son contraire « non A » : P(non A) = 1 − P(A).",
            "etape": etape(p),
        },
        pieges=pieges,
        solution=f"L'événement demandé est le contraire du premier : P = 1 − {enonce_p} = {ecrit_q}.",
        lieu=f"{NOTION}/contraire/{forme}-{valeur_machine(p)}",
    )


def _ni_ni(rng: random.Random, difficulte: int) -> dict[str, Any]:
    """Palier 3 : deux probabilités de dénominateurs différents, P(ni A ni B) = 1 − P(A) − P(B)."""
    objet = rng.choice(_OBJETS)
    couleur_a, couleur_b = rng.sample(_COULEURS, 2)

    def fabrique() -> tuple[Fraction, Fraction]:
        return (
            Fraction(rng.randint(1, 5), rng.choice((4, 6, 8, 10, 12))),
            Fraction(rng.randint(1, 5), rng.choice((3, 4, 5, 6, 8))),
        )

    def accepte(t: tuple[Fraction, Fraction]) -> bool:
        pa, pb = t
        q = 1 - pa - pb
        if pa.denominator == pb.denominator or q <= 0 or pa == pb:
            return False
        commun = math.lcm(pa.denominator, pb.denominator)  # cité par l'étape
        return not collision(q, _fraction(pa), _fraction(pb), commun, f"{commun}/{commun}")

    pa, pb = tirer(rng, fabrique, accepte)
    q = 1 - pa - pb
    pieges = [
        piege_valeur(
            valeur_machine(1 - pa),
            f"Tu n'as retiré que les {objet[1]} {couleur_a[1]} : retire aussi les {couleur_b[1]}.",
        ),
        piege_valeur(
            valeur_machine(1 - pb),
            f"Tu n'as retiré que les {objet[1]} {couleur_b[1]} : retire aussi les {couleur_a[1]}.",
        ),
        piege_valeur(
            valeur_machine(pa + pb),
            f"C'est la probabilité d'obtenir une {objet[0]} {couleur_a[0]} ou {couleur_b[0]}. On demande le contraire.",
        ),
        piege_diagnostic("non_irreductible", "C'est la bonne probabilité, mais la fraction se simplifie encore."),
        piege_diagnostic(
            "valeur_fausse", "Mets les fractions au même dénominateur avant de les additionner ou de les soustraire."
        ),
    ]
    commun = math.lcm(pa.denominator, pb.denominator)
    return exercice_v2(
        id=f"contraire-ni_ni-{valeur_machine(pa).replace('/', 'sur')}-{valeur_machine(pb).replace('/', 'sur')}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Dans un sac, on tire une {objet[0]} au hasard. La probabilité qu'elle soit {couleur_a[0]} est "
        f"{_fraction(pa)} ; la probabilité qu'elle soit {couleur_b[0]} est {_fraction(pb)}. Quelle est la "
        f"probabilité qu'elle ne soit ni {couleur_a[0]} ni {couleur_b[0]} ? Donne-la sous forme de fraction "
        "irréductible.",
        reponse=_reponse(q, irreductible=True),
        indices={
            "relance": f"« Ni {couleur_a[0]} ni {couleur_b[0]} » : c'est le contraire de quel événement ?",
            "methode": f"P(ni {couleur_a[0]} ni {couleur_b[0]}) = 1 − P({couleur_a[0]}) − P({couleur_b[0]}), "
            "car les deux couleurs ne peuvent pas sortir en même temps.",
            "etape": f"Mets les deux fractions au même dénominateur, par exemple {commun}, et écris 1 sous la "
            f"forme {commun}/{commun}.",
        },
        pieges=pieges,
        solution=f"P = 1 − {_fraction(pa)} − {_fraction(pb)} = {commun}/{commun} − "
        f"{pa.numerator * commun // pa.denominator}/{commun} − {pb.numerator * commun // pb.denominator}/{commun}"
        f" = {_fraction(q)}.",
        lieu=f"{NOTION}/contraire/ni_ni-{valeur_machine(pa)}-{valeur_machine(pb)}",
    )


# --- variante 4 : raisonner sur le hasard ----------------------------------------------------------------


def _options(
    rng: random.Random, bonne: str, fausses: list[tuple[str, str]]
) -> tuple[list[dict[str, str]], str, dict[str, str]]:
    """Options mélangées : (options, id de la bonne, {id: relance} des fausses)."""
    textes = [bonne] + [t for t, _ in fausses]
    rng.shuffle(textes)
    ids = {t: _LETTRES[i] for i, t in enumerate(textes)}
    return [{"id": ids[t], "texte": t} for t in textes], ids[bonne], {ids[t]: r for t, r in fausses}


def _hasard(rng: random.Random, difficulte: int) -> dict[str, Any]:
    qui = personnage(rng)
    if difficulte == 1:  # la pièce n'a pas de mémoire
        k = rng.randint(3, 9)
        cote, autre = rng.choice((("pile", "face"), ("face", "pile")))
        enonce = (
            f"{qui.prenom} lance une pièce bien équilibrée. Elle est tombée {k} fois de suite sur « {cote} ». "
            "Que peut-on dire du lancer suivant ?"
        )
        bonne = f"« {cote.capitalize()} » et « {autre} » ont toujours la même probabilité : 1/2."
        fausses = [
            (
                f"« {autre.capitalize()} » est plus probable, pour rattraper la série.",
                "La pièce n'a pas de mémoire : les lancers précédents ne changent rien au suivant.",
            ),
            (
                f"« {cote.capitalize()} » est plus probable, car il sort souvent.",
                "La pièce est bien équilibrée : une série, même longue, arrive par hasard.",
            ),
            (
                f"« {autre.capitalize()} » est certain.",
                "Rien n'est certain au lancer suivant : chaque face a une chance sur deux.",
            ),
        ]
        relance, methode = (
            "Les lancers précédents changent-ils la pièce elle-même ?",
            "Pour une pièce équilibrée, chaque lancer est une nouvelle expérience : les deux faces ont la même "
            "probabilité, quels que soient les résultats précédents.",
        )
        etape = (
            f"Les {k} lancers déjà faits ne modifient pas la pièce. Combien de faces possibles, et "
            "sont-elles équiprobables ?"
        )
        resume = f"{k}-{cote}"
        solution = (
            f"La pièce n'a pas de mémoire : au lancer suivant, « {cote} » et « {autre} » ont chacun une "
            "probabilité de 1/2."
        )
    elif difficulte == 2:  # fréquence observée et probabilité
        faces, face = rng.choice(((6, 6), (6, 1), (4, 4), (8, 8)))
        lancers = rng.choice((60, 120, 300, 600, 1200))
        attendu = lancers // faces
        sorties = attendu + rng.choice((-1, 1)) * rng.randint(1, max(2, attendu // 8))
        enonce = (
            f"{qui.prenom} a lancé {lancers} fois un dé équilibré à {faces} faces. Le {face} est sorti "
            f"{sorties} fois. Quelle affirmation est juste ?"
        )
        bonne = (
            f"La fréquence du {face} est {sorties}/{lancers} ; elle est proche de la probabilité 1/{faces}, "
            "sans lui être forcément égale."
        )
        fausses = [
            (
                f"Le dé est truqué, car la fréquence du {face} n'est pas exactement 1/{faces}.",
                "Un petit écart entre fréquence et probabilité est normal : il ne prouve pas que le dé est truqué.",
            ),
            (
                f"La probabilité d'obtenir le {face} est {sorties}/{lancers}.",
                "La fréquence est observée pendant l'expérience ; la probabilité se calcule avec les issues "
                "équiprobables du dé.",
            ),
            (
                f"Au lancer suivant, le {face} a moins de chances de sortir, car il est déjà sorti souvent.",
                "Le dé n'a pas de mémoire : chaque lancer a les mêmes probabilités.",
            ),
        ]
        relance, methode = (
            "Quelle différence fais-tu entre la fréquence observée et la probabilité ?",
            "La fréquence = nombre d'apparitions ÷ nombre de lancers. Quand on répète l'expérience un grand "
            "nombre de fois, elle se rapproche de la probabilité, sans lui être forcément égale.",
        )
        etape = (
            f"Pour un dé équilibré à {faces} faces, chaque face a une probabilité de 1 sur {faces}. "
            "Compare avec la fréquence observée."
        )
        resume = f"{faces}-{face}-{lancers}-{sorties}"
        solution = (
            f"La fréquence observée, {sorties}/{lancers}, est proche de 1/{faces} : c'est normal, la fréquence se "
            "stabilise autour de la probabilité sans lui être égale, et le dé n'a pas de mémoire."
        )
    else:  # issues non équiprobables : on compte les objets, pas les couleurs
        a, b = rng.sample(range(1, 10), 2)
        objet = rng.choice(_OBJETS)
        couleur_a, couleur_b = rng.sample(_COULEURS, 2)
        enonce = (
            f"Un sac contient {_compte(a, objet, couleur_a)} et {_compte(b, objet, couleur_b)}. {qui.prenom} "
            f"dit : « Il y a deux couleurs, donc la probabilité de tirer une {objet[0]} {couleur_a[0]} est 1/2. » "
            "Quelle affirmation est juste ?"
        )
        p = Fraction(a, a + b)
        bonne = f"{qui.Pronom} se trompe : les deux couleurs n'ont pas la même chance ; la probabilité est {a}/{a + b}."
        fausses = [
            (
                f"{qui.Pronom} a raison, car il y a deux issues : {couleur_a[0]} ou {couleur_b[0]}.",
                "Les deux couleurs ne sont pas équiprobables : ce sont les objets qui ont tous la même chance.",
            ),
            (
                f"{qui.Pronom} se trompe : la probabilité est {a}/{b}.",
                "On divise par le nombre TOTAL d'objets, pas par le nombre d'objets de l'autre couleur.",
            ),
            (
                f"{qui.Pronom} se trompe : la probabilité est {b}/{a + b}.",
                f"Cette fraction compte les {objet[1]} {couleur_b[1]}, pas les {couleur_a[1]}.",
            ),
        ]
        relance, methode = (
            f"Chaque couleur a-t-elle autant de chances que l'autre ? Et chaque {objet[0]} ?",
            "« Favorables ÷ total » ne marche que pour des issues équiprobables : ici, ce sont les objets qui "
            "ont tous la même chance, pas les couleurs.",
        )
        etape = f"Compte toutes les {objet[1]} du sac, puis celles qui sont {couleur_a[1]}."
        resume = f"{a}-{b}"
        solution = (
            f"Les {a + b} {objet[1]} ont la même chance, pas les deux couleurs : P = {a}/{a + b}"
            + (f" = {_fraction(p)}" if p.denominator != a + b else "")
            + f", et non 1/2. {qui.Pronom} se trompe."
        )
    options, id_bonne, relances = _options(rng, bonne, fausses)
    return exercice_v2(
        id=f"hasard-{difficulte}-{resume}-{qui.prenom}",
        type="choix",
        difficulte=difficulte,
        enonce=enonce,
        reponse={"options": options, "bonnes": [id_bonne]},
        indices={"relance": relance, "methode": methode, "etape": etape},
        pieges=[piege_contient([i], r) for i, r in relances.items()]
        + [
            piege_diagnostic(
                "mauvais_choix", "Relis chaque affirmation et demande-toi si elle dépend du hasard ou d'un calcul."
            )
        ],
        solution=solution,
        lieu=f"{NOTION}/hasard/{difficulte}-{resume}",
    )


_VARIANTES = {
    "urne": _urne,
    "de_roue": _de_roue,
    "contraire": _contraire,
    "hasard": _hasard,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
