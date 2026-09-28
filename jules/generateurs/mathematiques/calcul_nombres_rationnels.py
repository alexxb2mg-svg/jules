"""Générateur déterministe pour la notion `calcul-nombres-rationnels` (mathématiques, 3e).

Quatre variantes, toutes de type `nombre` :

  - somme      : somme ou différence de deux fractions positives     (nombre, fraction_irreductible)
  - produit    : produit ou quotient de deux fractions positives     (nombre, fraction_irreductible)
  - priorites  : calcul avec relatifs et priorités opératoires       (nombre, entier)
  - relatifs   : somme et différence de nombres relatifs             (nombre, entier)

Tout est calculé en exact (`Fraction`, entiers), jamais en flottant. Les fractions de `somme` et
`produit` restent positives (le contrat des relatifs est couvert par `priorites` et `relatifs`) ;
les indices écrivent les fractions « a/b », comme en classe et comme le correcteur les lit.
Les nombres négatifs s'écrivent avec le signe moins typographique « − », comme dans les fiches
écrites à la main (voir `_ecrire_entier`) ; le champ machine (`nombre_machine`) reste du ressort
de la brique `format_fr`.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Any

from jules.generateurs.briques import exercice_v2, generer_notion, palier, piege_diagnostic, piege_valeur
from jules.generateurs.briques.format_fr import nombre_machine
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "calcul-nombres-rationnels"
VARIANTES = ("somme", "produit", "priorites", "relatifs")


def _ecrire_entier(n: int) -> str:
    """-3 -> « −3 » (signe moins typographique, comme dans les fiches écrites à la main)."""
    return f"−{-n}" if n < 0 else str(n)


def _facteur(n: int) -> str:
    """Un entier qui suit un opérateur : entre parenthèses s'il est négatif (« × (−2) »)."""
    return f"({_ecrire_entier(n)})" if n < 0 else str(n)


def _fraction_txt(num: int, den: int) -> str:
    return f"{num}/{den}"


def _valeur_fraction(x: Fraction) -> str:
    """La bonne réponse d'un exercice `fraction_irreductible` : « p/q » (jamais un décimal)."""
    return f"{x.numerator}/{x.denominator}" if x.denominator != 1 else str(x.numerator)


def _fuite_texte(reponse_num: int, reponse_den: int, *textes: str) -> bool:
    """Le vérificateur des fiches normalise un texte en jetons alphanumériques et refuse tout indice où
    la bonne réponse apparaît comme sous-suite contiguë (« 5 4 » pour −5/4). Un indice qui enchaîne deux
    fractions (« 5/4 = ... et .../4 ») peut ainsi faire fuir la réponse par la seule adjacence de deux
    nombres qui n'ont rien à voir entre eux. On reproduit ici la même normalisation pour filtrer le
    tirage, plutôt que de réécrire l'indice.

    Voir aussi : lecons.contient_la_reponse, fiches/schema._fuite, modules/studio._est_recopie ;
    duplication voulue (chaque brique reste autonome), reporter tout correctif dans les autres.
    """
    from jules.fiches.schema import cle_texte

    cle_rep = f" {reponse_num} {reponse_den} "
    return any(cle_rep in f" {cle_texte(texte)} " for texte in textes)


# --- variante 1 : somme ou différence de deux fractions -------------------------------------------

_PALIERS_SOMME = {
    # difficulté : (numérateur max, dénominateurs possibles)
    1: (8, (2, 3, 4, 5, 6)),
    2: (15, (2, 3, 4, 5, 6, 7, 8, 9, 10)),
    3: (20, (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)),
}


def _somme(rng: random.Random, difficulte: int) -> dict[str, Any]:
    num_max, denoms = palier(_PALIERS_SOMME, difficulte)

    def fabrique() -> tuple[int, int, int, int, bool]:
        b = rng.choice(denoms)
        d = rng.choice([x for x in denoms if x != b])
        a = rng.randint(1, num_max)
        c = rng.randint(1, num_max)
        addition = rng.random() < 0.5
        return a, b, c, d, addition

    def acceptable(t: tuple[int, int, int, int, bool]) -> bool:
        a, b, c, d, addition = t
        m = math.lcm(b, d)
        f1, f2 = Fraction(a, b), Fraction(c, d)
        if math.gcd(a, b) != 1 or math.gcd(c, d) != 1:  # un énoncé ne cite que des fractions irréductibles
            return False
        resultat = f1 + f2 if addition else f1 - f2
        if resultat == 0:  # une différence nulle n'apprend rien de nouveau ici
            return False
        a2, c2 = a * (m // b), c * (m // d)
        if resultat in (f1, f2, Fraction(a2, m), Fraction(c2, m)):  # une fraction citée vaut déjà le résultat
            return False
        cites = [a, b, c, d, m, a2, c2]
        if collision(resultat, *cites):
            return False
        num, den = abs(resultat.numerator), resultat.denominator
        etape = f"{a}/{b} = {a2}/{m} et {c}/{d} = {c2}/{m}. Calcule {a2}/{m} et {c2}/{m}."
        return not _fuite_texte(num, den, etape)

    a, b, c, d, addition = tirer(rng, fabrique, acceptable)
    m = math.lcm(b, d)
    mult_b, mult_d = m // b, m // d
    a2, c2 = a * mult_b, c * mult_d
    f1, f2 = Fraction(a, b), Fraction(c, d)
    resultat = f1 + f2 if addition else f1 - f2
    signe_txt = "+" if addition else "−"
    signe_mot = "additionne" if addition else "soustrais"
    # piège : additionner (ou soustraire) numérateurs et dénominateurs séparément, sans dénominateur commun
    piege_direct = Fraction(a + c, b + d) if addition else (Fraction(a - c, b - d) if b != d else None)
    # piège : oublier de réduire au même dénominateur (garder le premier dénominateur)
    piege_sans_commun = Fraction(a2 + c, b) if addition else Fraction(a2 - c, b)
    pieges = []
    if piege_direct is not None:
        pieges.append(
            piege_valeur(
                nombre_machine(piege_direct),
                "On n'additionne pas les numérateurs et les dénominateurs séparément. "
                "Il faut d'abord écrire les deux fractions avec le même dénominateur.",
            )
        )
    pieges.append(
        piege_valeur(
            nombre_machine(piege_sans_commun),
            f"Tu as gardé {b} comme dénominateur sans le mettre au même dénominateur que la deuxième fraction.",
        )
    )
    pieges.append(
        piege_diagnostic(
            "non_irreductible",
            "Ton résultat est juste, mais il n'est pas irréductible. Par quel nombre peux-tu diviser "
            "le numérateur et le dénominateur ?",
        )
    )
    pieges.append(
        piege_diagnostic(
            "pas_une_fraction", "La valeur est juste, mais on demande une fraction irréductible, pas un décimal."
        )
    )
    pieges.append(piege_diagnostic("valeur_fausse", "Mets les deux fractions au même dénominateur, puis calcule."))
    somme_num = a2 + c2 if addition else a2 - c2
    if math.gcd(somme_num, m) == 1 or somme_num == 0:  # déjà irréductible : rien à simplifier
        fin_solution = "."
    elif resultat.denominator != 1:
        fin_solution = f", que l'on simplifie = {resultat.numerator}/{resultat.denominator}."
    else:
        fin_solution = f", que l'on simplifie = {resultat.numerator}."
    return exercice_v2(
        id=f"somme-{a}-{b}-{'plus' if addition else 'moins'}-{c}-{d}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Calcule {_fraction_txt(a, b)} {signe_txt} {_fraction_txt(c, d)} et donne le résultat "
        "sous forme de fraction irréductible.",
        reponse={"valeur": _valeur_fraction(resultat), "forme": "fraction_irreductible"},
        indices={
            "relance": "Les deux fractions ont-elles le même dénominateur ? Peut-on les combiner directement ?",
            "methode": f"Trouve un dénominateur commun à {b} et {d} (par exemple leur produit, ou un multiple "
            f"plus petit), écris les deux fractions avec ce dénominateur, puis {signe_mot} les numérateurs.",
            "etape": f"{_fraction_txt(a, b)} = {_fraction_txt(a2, m)} et {_fraction_txt(c, d)} = "
            f"{_fraction_txt(c2, m)}. Calcule {_fraction_txt(a2, m)} {signe_txt} {_fraction_txt(c2, m)}.",
        },
        pieges=pieges,
        solution=f"{_fraction_txt(a, b)} = {_fraction_txt(a2, m)} et {_fraction_txt(c, d)} = {_fraction_txt(c2, m)}. "
        f"{_fraction_txt(a2, m)} {signe_txt} {_fraction_txt(c2, m)} = "
        f"{_fraction_txt(a2 + c2 if addition else a2 - c2, m)}" + fin_solution,
        lieu=f"{NOTION}/somme/{a}-{b}-{c}-{d}",
    )


# --- variante 2 : produit ou quotient de deux fractions --------------------------------------------

_PALIERS_PRODUIT = {
    1: (8, (2, 3, 4, 5, 6)),
    2: (12, (2, 3, 4, 5, 6, 7, 8)),
    3: (15, (2, 3, 4, 5, 6, 7, 8, 9, 10)),
}


def _produit(rng: random.Random, difficulte: int) -> dict[str, Any]:
    num_max, denoms = palier(_PALIERS_PRODUIT, difficulte)

    def fabrique() -> tuple[int, int, int, int, bool]:
        b = rng.choice(denoms)
        d = rng.choice([x for x in denoms if x != b])
        a = rng.randint(1, num_max)
        c = rng.randint(1, num_max)
        est_produit = rng.random() < 0.5
        return a, b, c, d, est_produit

    def acceptable(t: tuple[int, int, int, int, bool]) -> bool:
        a, b, c, d, est_produit = t
        f1, f2 = Fraction(a, b), Fraction(c, d)
        if math.gcd(a, b) != 1 or math.gcd(c, d) != 1:  # un énoncé ne cite que des fractions irréductibles
            return False
        resultat = f1 * f2 if est_produit else f1 / f2
        if resultat == 1:
            return False
        m = math.lcm(b, d)
        # les indices citent a, b, c, d et les produits a×c, b×d (ou a×d, b×c pour un quotient) : aucun
        # ne doit coïncider avec le résultat réduit, sous peine de fuite dans « etape »/« methode ».
        cites = [a, b, c, d, m, a * c, b * d] if est_produit else [a, b, c, d, m, a * d, b * c]
        if collision(resultat, *cites):
            return False
        num, den = resultat.numerator, resultat.denominator
        if est_produit:
            etape = f"{a}/{b} × {c}/{d} = {a}/{b} × {c}/{d}. {a} × {c} au numérateur, {b} × {d} au dénominateur."
        else:
            etape = f"{a}/{b} ÷ {c}/{d} = {a}/{b} × {d}/{c}. {a} × {d} au numérateur, {b} × {c} au dénominateur."
        return not _fuite_texte(num, den, etape)

    a, b, c, d, est_produit = tirer(rng, fabrique, acceptable)
    f1, f2 = Fraction(a, b), Fraction(c, d)
    resultat = f1 * f2 if est_produit else f1 / f2
    m = math.lcm(b, d)
    mult_b, mult_d = m // b, m // d
    a2, c2 = a * mult_b, c * mult_d
    signe_txt = "×" if est_produit else "÷"
    pieges = []
    if est_produit:
        # piège : mise au même dénominateur inutile, puis produit des seuls numérateurs (garde un dénominateur simple)
        piege_commun = Fraction(a2 * c2, m)
        pieges.append(
            piege_valeur(
                nombre_machine(piege_commun),
                "Pour multiplier des fractions, on ne les met pas au même dénominateur : on multiplie "
                "directement les numérateurs entre eux, et les dénominateurs entre eux.",
            )
        )
    else:
        # piège : oublier d'inverser, diviser comme on multiplie
        piege_sans_inverser = f1 * f2
        pieges.append(
            piege_valeur(
                nombre_machine(piege_sans_inverser),
                "Diviser par une fraction, c'est multiplier par son inverse. As-tu inversé la deuxième fraction ?",
            )
        )
        # piège : inverser la mauvaise fraction
        piege_mauvais_inverse = Fraction(b, a) * f2 if a != 0 else None
        if piege_mauvais_inverse is not None:
            pieges.append(
                piege_valeur(
                    nombre_machine(piege_mauvais_inverse),
                    "C'est la fraction par laquelle on divise qu'il faut inverser, pas la première.",
                )
            )
    pieges.append(
        piege_diagnostic(
            "non_irreductible",
            "Ton résultat est juste, mais il se simplifie encore. Cherche un diviseur commun au numérateur "
            "et au dénominateur.",
        )
    )
    pieges.append(
        piege_diagnostic("pas_une_fraction", "La valeur est juste, mais on demande une fraction irréductible.")
    )
    pieges.append(piege_diagnostic("valeur_fausse", "Recalcule en appliquant la bonne règle pour ce calcul."))
    if est_produit:
        methode = "Multiplie les numérateurs entre eux, et les dénominateurs entre eux, puis simplifie."
        etape = f"{a} × {c} au numérateur, {b} × {d} au dénominateur. Calcule ces deux produits."
        solution_calc = f"{_fraction_txt(a, b)} × {_fraction_txt(c, d)} = {a * c}/{b * d}"
    else:
        methode = (
            f"Diviser par {_fraction_txt(c, d)}, c'est multiplier par son inverse {_fraction_txt(d, c)}. "
            "Multiplie ensuite numérateurs et dénominateurs, puis simplifie."
        )
        etape = (
            f"{_fraction_txt(a, b)} ÷ {_fraction_txt(c, d)} = {_fraction_txt(a, b)} × {_fraction_txt(d, c)}. "
            "Calcule ce produit."
        )
        solution_calc = (
            f"{_fraction_txt(a, b)} ÷ {_fraction_txt(c, d)} = {_fraction_txt(a, b)} × {_fraction_txt(d, c)} "
            f"= {a * d}/{b * c}"
        )
    fin = (
        f" = {resultat.numerator}/{resultat.denominator}." if resultat.denominator != 1 else f" = {resultat.numerator}."
    )
    return exercice_v2(
        id=f"produit-{a}-{b}-{'fois' if est_produit else 'div'}-{c}-{d}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Calcule {_fraction_txt(a, b)} {signe_txt} {_fraction_txt(c, d)} et donne le résultat "
        "sous forme de fraction irréductible.",
        reponse={"valeur": _valeur_fraction(resultat), "forme": "fraction_irreductible"},
        indices={
            "relance": "Faut-il mettre les fractions au même dénominateur pour ce calcul ?"
            if est_produit
            else "Diviser par une fraction, à quoi cela revient-il ?",
            "methode": methode,
            "etape": etape,
        },
        pieges=pieges,
        solution=solution_calc + ", que l'on simplifie" + fin,
        lieu=f"{NOTION}/produit/{a}-{b}-{c}-{d}",
    )


# --- variante 3 : priorités opératoires avec des relatifs -------------------------------------------

_PALIERS_PRIORITES = {
    # difficulté : (plage des entiers, négatifs autorisés sur les facteurs, motif à deux produits)
    1: ((1, 9), False, False),
    2: ((1, 12), True, False),
    3: ((2, 12), True, True),
}


def _tirer_entier(rng: random.Random, plage: tuple[int, int], negatif: bool) -> int:
    bas, haut = plage
    n = rng.randint(bas, haut)
    return -n if negatif and rng.random() < 0.5 else n


def _priorites(rng: random.Random, difficulte: int) -> dict[str, Any]:
    plage, negatif, double = palier(_PALIERS_PRIORITES, difficulte)

    def fabrique() -> tuple[int, ...]:
        if double:
            return (
                _tirer_entier(rng, plage, True),
                _tirer_entier(rng, plage, negatif),
                rng.choice((1, -1)),
                _tirer_entier(rng, plage, negatif),
                _tirer_entier(rng, plage, negatif),
            )
        return (
            _tirer_entier(rng, plage, negatif),
            rng.choice((1, -1)),
            _tirer_entier(rng, plage, negatif),
            _tirer_entier(rng, plage, negatif),
        )

    if double:

        def acceptable(t: tuple[int, ...]) -> bool:
            a, b, signe, c, d = t
            produit1, produit2 = a * b, c * d
            valeur = produit1 + signe * produit2
            naif = ((a * b) + signe * c) * d
            if valeur == naif:
                return False
            return not collision(valeur, a, b, c, d, produit1, produit2)

        a, b, signe, c, d = tirer(rng, fabrique, acceptable)
        produit1, produit2 = a * b, c * d
        valeur = produit1 + signe * produit2
        naif = ((a * b) + signe * c) * d
        signe_txt = "+" if signe > 0 else "−"
        enonce_calc = f"{_ecrire_entier(a)} × {_facteur(b)} {signe_txt} {_facteur(c)} × {_facteur(d)}"
        etape = (
            f"{a} × {b} = {produit1} et {c} × {d} = {produit2}. Calcule {_ecrire_entier(produit1)} "
            f"{signe_txt} {_ecrire_entier(produit2) if signe > 0 else _facteur(produit2)}."
        )
        solution = (
            f"On calcule d'abord les deux produits : {a} × {b} = {produit1} et {c} × {d} = {produit2}. "
            f"Puis {_ecrire_entier(produit1)} {signe_txt} {_facteur(produit2)} = {_ecrire_entier(valeur)}."
        )
        cle_id = f"priorites-double-{a}-{b}-{signe}-{c}-{d}"
        lieu_id = f"{a}-{b}-{signe}-{c}-{d}"
    else:

        def acceptable(t: tuple[int, ...]) -> bool:
            a, signe, b, c = t
            produit = b * c
            valeur = a + signe * produit
            naif = (a + signe * b) * c
            if valeur == naif:
                return False
            return not collision(valeur, a, b, c, produit)

        a, signe, b, c = tirer(rng, fabrique, acceptable)
        produit = b * c
        valeur = a + signe * produit
        naif = (a + signe * b) * c
        signe_txt = "+" if signe > 0 else "−"
        enonce_calc = f"{_ecrire_entier(a)} {signe_txt} {_facteur(b)} × {_facteur(c)}"
        reste_signe = _facteur(produit) if signe < 0 else produit
        etape = f"{b} × {c} = {produit}. Calcule {_ecrire_entier(a)} {signe_txt} {reste_signe}."
        solution = (
            f"La multiplication est prioritaire : {b} × {c} = {produit}. Puis {_ecrire_entier(a)} "
            f"{signe_txt} {_facteur(produit)} = {_ecrire_entier(valeur)}."
        )
        cle_id = f"priorites-{a}-{signe}-{b}-{c}"
        lieu_id = f"{a}-{signe}-{b}-{c}"

    pieges = [
        piege_valeur(
            naif,
            "Tu as calculé de gauche à droite. La multiplication est prioritaire : il faut la faire avant "
            "l'addition ou la soustraction.",
        ),
        piege_diagnostic("valeur_fausse", "Repère l'opération prioritaire, calcule-la d'abord, puis termine."),
    ]
    return exercice_v2(
        id=cle_id,
        type="nombre",
        difficulte=difficulte,
        enonce=f"Calcule {enonce_calc}.",
        reponse={"valeur": nombre_machine(valeur), "forme": "entier"},
        indices={
            "relance": "Quelle opération doit-on effectuer en premier : l'addition/la soustraction, "
            "ou la multiplication ?",
            "methode": "La multiplication est prioritaire sur l'addition et la soustraction : on la calcule "
            "d'abord, en appliquant la règle des signes, puis on termine avec le reste du calcul.",
            "etape": etape,
        },
        pieges=pieges,
        solution=solution,
        lieu=f"{NOTION}/priorites/{lieu_id}",
    )


# --- variante 4 : somme et différence de relatifs ---------------------------------------------------

_PALIERS_RELATIFS = {
    # difficulté : (plage des entiers, nombre de termes)
    1: ((1, 15), 2),
    2: ((5, 40), 2),
    3: ((5, 50), 3),
}


def _relatifs(rng: random.Random, difficulte: int) -> dict[str, Any]:
    plage, nb_termes = palier(_PALIERS_RELATIFS, difficulte)

    def fabrique() -> tuple[int, ...]:
        premier = _tirer_entier(rng, plage, True)
        signes = tuple(rng.choice((1, -1)) for _ in range(nb_termes - 1))
        valeurs = tuple(_tirer_entier(rng, plage, True) for _ in range(nb_termes - 1))
        return (premier, *signes, *valeurs)

    def decouper(t: tuple[int, ...]) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
        premier = t[0]
        signes = t[1:nb_termes]
        valeurs = t[nb_termes:]
        return premier, signes, valeurs

    def acceptable(t: tuple[int, ...]) -> bool:
        premier, signes, valeurs = decouper(t)
        valeur = premier + sum(s * v for s, v in zip(signes, valeurs, strict=True))
        if valeur == 0:
            return False
        if valeur == -premier:  # rendrait le piège « erreur de signe » égal à la bonne réponse
            return False
        return not collision(valeur, premier, *valeurs)

    tirage = tirer(rng, fabrique, acceptable)
    premier, signes, valeurs = decouper(tirage)
    valeur = premier + sum(s * v for s, v in zip(signes, valeurs, strict=True))

    morceaux = [_ecrire_entier(premier)]
    for s, v in zip(signes, valeurs, strict=True):
        morceaux.append("+" if s > 0 else "−")
        morceaux.append(_facteur(v))
    enonce_calc = " ".join(morceaux)

    # piège : erreur de signe sur le résultat final
    # piège : additionner les valeurs absolues, en ignorant les signes intermédiaires
    naif_signes = premier + sum(v for v in valeurs)
    pieges = [
        piege_valeur(-valeur, "Le nombre est bon, mais pas le signe. Vérifie le signe du résultat."),
        piege_diagnostic("valeur_fausse", "Applique la règle des signes terme après terme."),
    ]
    if naif_signes != valeur:
        pieges.insert(
            1,
            piege_valeur(
                naif_signes,
                "Tu as additionné les nombres sans tenir compte de tous les signes. Reprends terme par terme.",
            ),
        )
    etapes_texte = []
    cumul = premier
    for s, v in zip(signes, valeurs, strict=True):
        precedent = cumul
        cumul = cumul + s * v
        op = "+" if s > 0 else "−"
        etapes_texte.append(f"{_ecrire_entier(precedent)} {op} {_facteur(v)} = {_ecrire_entier(cumul)}")
    return exercice_v2(
        id=f"relatifs-{premier}-{'-'.join(f'{s}{v}' for s, v in zip(signes, valeurs, strict=True))}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Calcule {enonce_calc}.",
        reponse={"valeur": nombre_machine(valeur), "forme": "entier"},
        indices={
            "relance": "Soustraire un nombre négatif revient-il à l'ajouter, ou à le soustraire encore plus ?",
            "methode": "Additionner un relatif, c'est avancer de sa valeur ; soustraire un relatif, c'est reculer "
            "de sa valeur (donc soustraire un négatif fait avancer). Calcule terme après terme, de gauche à droite.",
            "etape": f"Commence par {_ecrire_entier(premier)} {'+' if signes[0] > 0 else '−'} {_facteur(valeurs[0])}, "
            "puis continue avec le terme suivant.",
        },
        pieges=pieges,
        solution=" puis ".join(etapes_texte) + f". Le résultat est {_ecrire_entier(valeur)}.",
        lieu=f"{NOTION}/relatifs/{premier}",
    )


# --- point d'entrée ---------------------------------------------------------------------------------

_VARIANTES = {
    "somme": _somme,
    "produit": _produit,
    "priorites": _priorites,
    "relatifs": _relatifs,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
