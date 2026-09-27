"""Générateur déterministe pour la notion `equations-premier-degre-et-produits` (mathématiques, 3e).

  - premier_degre : résoudre ax + b = c                                      (nombre)
  - deux_membres  : résoudre ax + b = cx + d (des x des deux côtés)          (nombre)
  - produit_nul   : solutions de (ax + b)(cx + d) = 0                        (choix)
  - carre         : solutions de x² = a (a carré parfait, nul, négatif, quelconque) (choix)

Paliers : 1 = coefficients et solution entiers positifs ; 2 = nombres relatifs ; 3 = solution
fractionnaire (premier degré, produit) ou a qui n'est pas un carré parfait (x² = a).

Les pièges sont les erreurs de la fiche v2 : soustraire le coefficient au lieu de diviser (3x = 27
donne 24), déplacer un nombre sans changer son signe, regrouper les x en ajoutant, ne donner qu'une
solution d'une équation produit, oublier la division (2x − 6 = 0 donne 6), oublier −√a, croire que
x² = −9 donne −3. Toutes les valeurs sont exactes (Fraction) ; une réponse fractionnaire est écrite
« 7/3 » (valeur_machine), jamais en décimal tronqué.
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
from jules.generateurs.briques.algebre import (
    MOINS,
    affine_fr,
    entre_parentheses,
    facteur_fr,
    nombre_signe_fr,
    terme,
    valeur_machine,
)
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "equations-premier-degre-et-produits"
VARIANTES = ("premier_degre", "deux_membres", "produit_nul", "carre")

_PALIERS_PREMIER = {
    # difficulté : (coefficients de x possibles, constantes possibles, solution entière ?, relatifs ?)
    1: (range(2, 10), range(1, 21), True, False),
    2: (range(2, 10), range(1, 31), True, True),
    3: (range(2, 10), range(1, 31), False, True),
}


def _signe(rng: random.Random, relatifs: bool) -> int:
    return rng.choice((1, -1)) if relatifs else 1


def _solution(rng: random.Random, a: int, entiere: bool, relatifs: bool) -> Fraction:
    """x = entier (difficultés 1-2) ou fraction de dénominateur a, non entière (difficulté 3)."""
    if entiere:
        bas = 1 if not relatifs else -12
        return Fraction(tirer(rng, lambda: rng.randint(bas, 12), lambda v: v != 0))
    num = tirer(rng, lambda: rng.randint(-40, 40), lambda n: n % a != 0)
    return Fraction(num, a)


def _verification(a: int, x: Fraction, b: int) -> str:
    """« 3 × 9 − 8 » (sans le résultat), pour la solution rédigée."""
    return f"{abs(a) if a > 0 else nombre_signe_fr(a)} × {entre_parentheses(x)}{_plus_moins(b)}"


def _plus_moins(b: int | Fraction) -> str:
    return f" {MOINS} {nombre_signe_fr(-b)}" if b < 0 else f" + {nombre_signe_fr(b)}"


# --- variante 1 : ax + b = c ---------------------------------------------------------------------------


def _premier_degre(rng: random.Random, difficulte: int) -> dict[str, Any]:
    coefs, constantes, entiere, relatifs = palier(_PALIERS_PREMIER, difficulte)

    def fabrique() -> tuple[int, int, Fraction]:
        a = rng.choice(coefs) * _signe(rng, relatifs)
        b = rng.choice(constantes) * rng.choice((1, -1))
        return a, b, _solution(rng, abs(a), entiere, relatifs)

    def accepte(t: tuple[int, int, Fraction]) -> bool:
        a, b, x = t
        c = a * x + b
        # c entier, et la réponse n'apparaît dans aucun nombre cité par les indices et les relances
        return c.denominator == 1 and c != 0 and not collision(x, a, abs(a), abs(b), c, c - b, abs(c - b))

    a, b, x = tirer(rng, fabrique, accepte)
    c = a * x + b
    ax = c - b  # ce que vaut ax une fois b passé de l'autre côté
    equation = f"{affine_fr(a, b)} = {nombre_signe_fr(c)}"
    operation = f"{'Ajoute' if b < 0 else 'Soustrais'} {nombre_signe_fr(abs(b))} aux deux membres"
    pieges = [
        piege_valeur(
            valeur_machine(ax - a),
            f"{terme(a)} veut dire {nombre_signe_fr(a)} fois x : pour trouver x, on DIVISE par "
            f"{nombre_signe_fr(a)}, on ne le soustrait pas.",
        ),
        piege_valeur(
            valeur_machine((c + b) / a),
            f"Pour faire disparaître le « {nombre_signe_fr(b)} », on fait l'opération contraire aux deux membres. "
            "As-tu ajouté ou soustrait ?",
        ),
        piege_valeur(
            valeur_machine(Fraction(a) / ax),
            f"Tu as divisé dans le mauvais sens : on divise le nombre du second membre par {nombre_signe_fr(a)}.",
        ),
    ]
    if a < 0:
        pieges.append(
            piege_valeur(
                valeur_machine(-x),
                f"Attention au signe : on divise par {nombre_signe_fr(a)}, un nombre négatif.",
            )
        )
    pieges.append(
        piege_diagnostic("valeur_fausse", "Remplace x par ta valeur dans l'équation : l'égalité est-elle vraie ?")
    )
    return exercice_v2(
        id=f"premier_degre-{a}-{b}-{c}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Résous l'équation {equation}. Donne la valeur de x"
        + (" sous la forme d'une fraction." if not entiere else "."),
        reponse={"valeur": valeur_machine(x), "forme": "libre"},
        indices={
            "relance": f"Que faut-il faire aux deux membres pour faire disparaître le « {nombre_signe_fr(b)} » ?",
            "methode": f"{operation}, puis divise les deux membres par {nombre_signe_fr(a)}.",
            "etape": f"On obtient {terme(a)} = {nombre_signe_fr(ax)}. Termine.",
        },
        pieges=pieges,
        solution=f"{equation}, donc {terme(a)} = {nombre_signe_fr(ax)}, donc x = {nombre_signe_fr(ax)} ÷ "
        f"{entre_parentheses(a)} = {nombre_signe_fr(x)}."
        + (f" Vérification : {_verification(a, x, b)} = {nombre_signe_fr(c)}." if x.denominator == 1 else ""),
        lieu=f"{NOTION}/premier_degre/{a}-{b}-{c}",
    )


# --- variante 2 : ax + b = cx + d ------------------------------------------------------------------------


def _deux_membres(rng: random.Random, difficulte: int) -> dict[str, Any]:
    coefs, constantes, entiere, relatifs = palier(_PALIERS_PREMIER, difficulte)

    def fabrique() -> tuple[int, int, int, Fraction]:
        a = rng.choice(coefs) * _signe(rng, relatifs)
        c = rng.choice(coefs) * _signe(rng, relatifs)
        b = rng.choice(constantes) * _signe(rng, relatifs)
        k = a - c
        # une solution fractionnaire demande |a − c| ≥ 2 ; sinon x = 0, écarté par `accepte`
        x = _solution(rng, abs(k), entiere, relatifs) if (abs(k) >= 2 or (entiere and k)) else Fraction(0)
        return a, b, c, x

    def accepte(t: tuple[int, int, int, Fraction]) -> bool:
        a, b, c, x = t
        k = a - c
        if k == 0 or x == 0 or (not relatifs and k < 0):
            return False
        d = k * x + b
        if d.denominator != 1 or d == 0 or (not relatifs and d < 0):
            return False
        return not collision(x, a, abs(a), c, abs(c), abs(b), d, abs(d), k, abs(k), d - b, abs(d - b))

    a, b, c, x = tirer(rng, fabrique, accepte)
    k = a - c
    d = k * x + b
    equation = f"{affine_fr(a, b)} = {affine_fr(c, d)}"
    enlever_x = f"{'Soustrais' if c > 0 else 'Ajoute'} {terme(abs(c))} aux deux membres"
    pieges = []
    if a + c:  # regrouper les x en ajoutant cx au lieu de le soustraire (a + c = 0 : pas de valeur à piéger)
        pieges.append(
            piege_valeur(
                valeur_machine((d - b) / (a + c)),
                f"Pour enlever {terme(c)} du second membre, on fait l'opération contraire des deux côtés. "
                "Combien de x reste-t-il alors dans le premier membre ?",
            )
        )
    pieges += [
        piege_valeur(
            valeur_machine((d + b) / k),
            f"Pour faire disparaître le « {nombre_signe_fr(b)} », on fait l'opération contraire aux deux membres. "
            "Vérifie ce calcul.",
        ),
        piege_valeur(
            valeur_machine((d - b) - k),
            "Quand il reste un nombre fois x, on DIVISE par ce nombre, on ne le soustrait pas.",
        ),
        piege_valeur(
            valeur_machine(-x),
            "Vérifie le signe : remplace x par ta valeur dans les deux membres, obtiens-tu la même chose ?",
        ),
        piege_diagnostic("valeur_fausse", "Regroupe d'abord les x dans un seul membre, puis les nombres dans l'autre."),
    ]
    return exercice_v2(
        id=f"deux_membres-{a}-{b}-{c}-{d}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Résous l'équation {equation}. Donne la valeur de x"
        + (" sous la forme d'une fraction." if not entiere else "."),
        reponse={"valeur": valeur_machine(x), "forme": "libre"},
        indices={
            "relance": "Comment faire pour qu'il n'y ait des x que dans un seul membre ?",
            "methode": f"{enlever_x}, puis regroupe les nombres dans l'autre membre, puis divise.",
            "etape": f"On obtient {affine_fr(k, b)} = {nombre_signe_fr(d)}. Continue.",
        },
        pieges=pieges,
        solution=f"{equation}, donc {affine_fr(k, b)} = {nombre_signe_fr(d)}, donc {terme(k)} = "
        f"{nombre_signe_fr(d - b)}, donc x = {nombre_signe_fr(d - b)} ÷ {entre_parentheses(k)} = "
        f"{nombre_signe_fr(x)}.",
        lieu=f"{NOTION}/deux_membres/{a}-{b}-{c}-{d}",
    )


# --- variante 3 : équation produit ------------------------------------------------------------------------

_PALIERS_PRODUIT = {
    # difficulté : (coefficient du 1er facteur, coefficient du 2d facteur, solutions entières ?)
    1: ((1,), (1,), True),
    2: ((2, 3, 4, 5), (1,), True),
    3: ((2, 3, 4, 5), (2, 3, 5), False),
}

_LETTRES = "abcde"


def _solutions_texte(sols: list[Fraction]) -> str:
    return " ou ".join(f"x = {nombre_signe_fr(s)}" for s in sols)


def _options_choix(
    rng: random.Random, bonne: str, distracteurs: list[tuple[str, str]]
) -> tuple[list[dict[str, str]], str, dict[str, str]]:
    """Options mélangées : (options, id de la bonne, {id: relance} des distracteurs gardés)."""
    vus = {bonne}
    gardes: list[tuple[str, str]] = []
    for texte, relance in distracteurs:
        if texte not in vus:
            vus.add(texte)
            gardes.append((texte, relance))
    gardes = gardes[:3]
    textes = [bonne] + [t for t, _ in gardes]
    rng.shuffle(textes)
    ids = {texte: _LETTRES[i] for i, texte in enumerate(textes)}
    options = [{"id": ids[t], "texte": t} for t in textes]
    return options, ids[bonne], {ids[t]: r for t, r in gardes}


def _produit_nul(rng: random.Random, difficulte: int) -> dict[str, Any]:
    coefs1, coefs2, entiere = palier(_PALIERS_PRODUIT, difficulte)

    def facteur(coefs: tuple[int, ...]) -> tuple[int, int]:
        p = rng.choice(coefs)
        if entiere:
            s = tirer(rng, lambda: rng.randint(-9, 9), lambda v: v != 0)
            return p, -p * s  # px + q = 0 donne x = s, entier
        q = tirer(rng, lambda: rng.randint(-12, 12), lambda v: v != 0 and v % p != 0)
        return p, q

    def fabrique() -> tuple[tuple[int, int], tuple[int, int]]:
        return facteur(coefs1), facteur(coefs2)

    def accepte(f: tuple[tuple[int, int], tuple[int, int]]) -> bool:
        (p, q), (r, s) = f
        x1, x2 = Fraction(-q, p), Fraction(-s, r)
        return x1 != x2 and x1 != -x2  # deux solutions distinctes, et pas opposées (options ambiguës)

    (p, q), (r, s) = tirer(rng, fabrique, accepte)
    if rng.random() < 0.5:
        (p, q), (r, s) = (r, s), (p, q)
    x1, x2 = Fraction(-q, p), Fraction(-s, r)
    equation = f"{facteur_fr(p, q)}{facteur_fr(r, s)} = 0"
    bonne = _solutions_texte([x1, x2])
    distracteurs = [
        (
            _solutions_texte([Fraction(-q), Fraction(-s)]),
            f"{affine_fr(p, q) if p != 1 else affine_fr(r, s)} = 0 ne donne pas directement x : "
            "il reste une division à faire.",
        ),
        (
            _solutions_texte([-x1, -x2]),
            "Vérifie les signes : remplace x par tes valeurs dans chaque facteur. Obtiens-tu 0 ?",
        ),
        (
            f"x = {nombre_signe_fr(x1)} seulement",
            "Un produit est nul si l'un OU l'autre facteur est nul. As-tu regardé le second facteur ?",
        ),
        (
            f"x = {nombre_signe_fr(x2)} seulement",
            "Un produit est nul si l'un OU l'autre facteur est nul. As-tu regardé le premier facteur ?",
        ),
    ]
    options, id_bonne, relances = _options_choix(rng, bonne, distracteurs)
    return exercice_v2(
        id=f"produit_nul-{p}-{q}-{r}-{s}",
        type="choix",
        difficulte=difficulte,
        enonce=f"Quelles sont les solutions de l'équation {equation} ?",
        reponse={"options": options, "bonnes": [id_bonne]},
        indices={
            "relance": "Quand un produit de deux facteurs est-il égal à 0 ?",
            "methode": f"Écris que {affine_fr(p, q)} = 0 ou que {affine_fr(r, s)} = 0, "
            "et résous chacune de ces deux équations.",
            "etape": f"{affine_fr(p, q)} = 0 donne {terme(p)} = {nombre_signe_fr(-q)}. "
            "Termine, puis résous l'autre équation.",
        },
        pieges=[piege_contient([i], relance) for i, relance in relances.items()],
        solution=f"Un produit est nul si l'un de ses facteurs est nul : {affine_fr(p, q)} = 0, soit "
        f"x = {nombre_signe_fr(x1)} ; ou {affine_fr(r, s)} = 0, soit x = {nombre_signe_fr(x2)}. "
        f"Les solutions sont {nombre_signe_fr(x1)} et {nombre_signe_fr(x2)}.",
        lieu=f"{NOTION}/produit_nul/{p}-{q}-{r}-{s}",
    )


# --- variante 4 : x² = a ---------------------------------------------------------------------------------

_PALIERS_CARRE = {
    # difficulté : cas possibles
    1: ("carre",),
    2: ("carre", "nul", "negatif"),
    3: ("irrationnel", "irrationnel", "negatif"),
}


def _au_carre(racine: str) -> str:
    """« 5² », « (−5)² », « (√15)² » : parenthèses dès que le nombre n'est pas un entier positif."""
    return f"{racine}²" if racine.isdigit() else f"({racine})²"


def _carre(rng: random.Random, difficulte: int) -> dict[str, Any]:
    cas_possibles: tuple[str, ...] = palier(_PALIERS_CARRE, difficulte)
    cas = rng.choice(cas_possibles)
    k = rng.randint(2, 12)
    if cas == "carre":
        a = k * k
    elif cas == "nul":
        a = 0
    elif cas == "negatif":
        a = -k * k if difficulte < 3 else -tirer(rng, lambda: rng.randint(2, 50), lambda n: math.isqrt(n) ** 2 != n)
    else:
        a = tirer(rng, lambda: rng.randint(2, 60), lambda n: math.isqrt(n) ** 2 != n)
    racine = f"√{a}" if cas == "irrationnel" else nombre_signe_fr(k)
    pas_de_solution = "pas de solution"
    moitie = [
        (
            f"x = {nombre_signe_fr(Fraction(a, 2))} ou x = {nombre_signe_fr(Fraction(-a, 2))}",
            f"x² veut dire x × x, pas 2 × x. Calcule le carré de {nombre_signe_fr(Fraction(a, 2))}.",
        )
    ]
    if cas in ("carre", "irrationnel"):
        bonne = f"x = {racine} ou x = {MOINS}{racine}"
        distracteurs = [
            (f"x = {racine} seulement", f"Calcule {_au_carre(MOINS + racine)}. Obtiens-tu aussi {a} ?"),
            *(moitie if a % 2 == 0 else []),
            (
                pas_de_solution,
                f"{a} est positif : un nombre au carré peut-il valoir {a} ?"
                + (f" (Même si {a} n'est pas un carré parfait, √{a} existe.)" if cas == "irrationnel" else ""),
            ),
            (f"x = {MOINS}{racine} seulement", f"Calcule {_au_carre(racine)}. Obtiens-tu aussi {a} ?"),
        ]
        explication = f"{_au_carre(racine)} = {a} et {_au_carre(MOINS + racine)} = {a}."
    elif cas == "nul":
        bonne = "x = 0 seulement"
        distracteurs = [
            (pas_de_solution, "Cherche un nombre dont le carré vaut 0 : essaie 0 lui-même."),
            ("x = 1 ou x = −1".replace("−", MOINS), "Calcule 1² : obtiens-tu 0 ?"),
        ]
        explication = "0² = 0, et le carré de tout autre nombre est strictement positif."
    else:  # a < 0
        r = abs(a)
        racine_r = nombre_signe_fr(k) if math.isqrt(r) ** 2 == r else f"√{r}"
        bonne = pas_de_solution
        distracteurs = [
            (
                f"x = {MOINS}{racine_r} seulement",
                f"Calcule {_au_carre(MOINS + racine_r)} : le carré d'un nombre négatif est-il négatif ?",
            ),
            (
                f"x = {racine_r} ou x = {MOINS}{racine_r}",
                f"Teste : {_au_carre(MOINS + racine_r)} vaut-il {nombre_signe_fr(a)} ?",
            ),
            (f"x = {racine_r} seulement", f"Calcule {_au_carre(racine_r)} : obtiens-tu {nombre_signe_fr(a)} ?"),
        ]
        explication = "Un carré n'est jamais négatif."
    options, id_bonne, relances = _options_choix(rng, bonne, distracteurs)
    return exercice_v2(
        id=f"carre-{cas}-{a}",
        type="choix",
        difficulte=difficulte,
        enonce=f"Quelles sont les solutions de l'équation x² = {nombre_signe_fr(a)} ?",
        reponse={"options": options, "bonnes": [id_bonne]},
        indices={
            "relance": f"Le nombre {nombre_signe_fr(a)} est-il positif, nul ou négatif ?",
            "methode": "x² = a : si a est positif, deux solutions, √a et son opposé ; si a est nul, une seule, 0 ; "
            "si a est négatif, aucune (un carré n'est jamais négatif).",
            "etape": "Regarde le signe du second membre, puis cherche combien de nombres ont ce carré.",
        },
        pieges=[piege_contient([i], relance) for i, relance in relances.items()],
        solution=f"{explication} "
        + (
            "L'équation n'a pas de solution."
            if bonne == pas_de_solution
            else "La seule solution est 0."
            if cas == "nul"
            else f"Les solutions de x² = {a} sont {racine} et {MOINS}{racine}."
        ),
        lieu=f"{NOTION}/carre/{cas}-{a}",
    )


_VARIANTES = {
    "premier_degre": _premier_degre,
    "deux_membres": _deux_membres,
    "produit_nul": _produit_nul,
    "carre": _carre,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
