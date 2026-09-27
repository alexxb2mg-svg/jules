"""Écrire les nombres et les calculs comme en classe.

Le correcteur (jules/fiches/correction.py) sait LIRE ces écritures ; cette brique sait les ÉCRIRE.
Les fonctions de calcul (décomposer, est_premier...) restent dans le correcteur : on les importe,
on ne les recopie pas.

Règle apprise sur le premier générateur : un indice qui cite la réponse sous une autre écriture
(2² × 3 pour « 2 × 2 × 3 ») est refusé par le vérificateur. Dans un indice, écrire le produit
DÉVELOPPÉ (`produit_developpe`) ; la forme avec puissances (`joli_produit`) est pour la solution.
"""

from __future__ import annotations

from fractions import Fraction

from jules.fiches.correction import decomposer

_EXPOSANTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def exposant(e: int) -> str:
    """3 -> « ³ »."""
    return str(e).translate(_EXPOSANTS)


def joli_produit(facteurs: list[tuple[int, int]]) -> str:
    """[(2, 2), (3, 1), (5, 1)] -> « 2² × 3 × 5 » (lisible par l'élève et par le correcteur)."""
    return " × ".join(f"{b}{exposant(e)}" if e > 1 else str(b) for b, e in facteurs)


def produit_developpe(n: int) -> str:
    """60 -> « 2 × 2 × 3 × 5 » : sans puissances, pour un indice où un exposant trahirait la réponse."""
    return " × ".join(str(b) for b, e in decomposer(n) for _ in range(e))


def chaine_divisions(n: int) -> str:
    """« 60 = 2 × 30 = 2 × 2 × 15 = 2 × 2 × 3 × 5 » : les divisions successives, telles qu'on les écrit."""
    faits: list[int] = []
    reste = n
    etapes = []
    for base, e in decomposer(n):
        for _ in range(e):
            faits.append(base)
            reste //= base
            etapes.append(" × ".join(map(str, [*faits, reste] if reste > 1 else faits)))
    return f"{n} = " + " = ".join(etapes)


def nombre_fr(x: Fraction | int | float | str, decimales: int | None = None) -> str:
    """Écriture française d'un nombre : virgule décimale, espace fine tous les trois chiffres.

    1234.5 -> « 1 234,5 » ; Fraction(23, 20) -> « 1,15 » ; 80 -> « 80 ».
    `decimales` force un nombre de chiffres après la virgule (prix : 2). Un nombre qui ne tombe pas
    juste est arrondi : le générateur doit avoir tiré des valeurs exactes avant d'en arriver là.
    """
    valeur = Fraction(str(x)) if not isinstance(x, Fraction) else x
    signe = "-" if valeur < 0 else ""
    valeur = abs(valeur)
    if decimales is None:
        entier, reste = divmod(valeur.numerator, valeur.denominator)
        chiffres = ""
        while reste and len(chiffres) < 12:
            reste *= 10
            chiffre, reste = divmod(reste, valeur.denominator)
            chiffres += str(chiffre)
    else:
        arrondi = round(valeur * 10**decimales)
        entier, frac = divmod(arrondi, 10**decimales)
        chiffres = str(frac).rjust(decimales, "0") if decimales else ""
    partie_entiere = f"{entier:,}".replace(",", "\u202f")
    return f"{signe}{partie_entiere},{chiffres}" if chiffres else f"{signe}{partie_entiere}"


def nombre_machine(x: Fraction | int | float | str) -> str:
    """Écriture pour le champ `reponse.valeur` : point décimal, sans espace (« 1234.5 »), lisible par lire_nombre."""
    valeur = Fraction(str(x)) if not isinstance(x, Fraction) else x
    if valeur.denominator == 1:
        return str(valeur.numerator)
    texte = nombre_fr(valeur)
    return texte.replace("\u202f", "").replace(",", ".")


def pourcentage_fr(taux: Fraction | int) -> str:
    """15 -> « 15 % » ; Fraction(25, 2) -> « 12,5 % »."""
    return f"{nombre_fr(taux)} %"


def prix_fr(x: Fraction | int) -> str:
    """80 -> « 80 € » ; Fraction(23, 4) -> « 5,75 € » (toujours deux décimales dès qu'il y en a)."""
    valeur = Fraction(x)
    return f"{nombre_fr(valeur, 2 if valeur.denominator != 1 else None)} €"
