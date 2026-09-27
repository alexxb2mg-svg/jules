"""Écrire le calcul littéral comme en classe : « 3x − 8 », « −x + 5 », « (2x − 6)(x + 4) », « −7/3 ».

Née avec `equations-premier-degre-et-produits` ; sert à toute notion qui écrit une expression en x
(développer, factoriser, fonctions affines, mise en équation).

Deux écritures d'un même nombre :
  - `nombre_signe_fr` pour l'élève : signe moins typographique « − », fraction « 7/3 » (jamais un
    décimal tronqué), espace fine des milliers ;
  - `valeur_machine` pour `reponse.valeur` et les pièges : « -7/3 », lu exactement par le correcteur.
    (`nombre_machine` écrit un décimal : parfait pour 2,5, faux pour 7/3, qui deviendrait 2.333...)
"""

from __future__ import annotations

from fractions import Fraction

from jules.generateurs.briques.format_fr import nombre_fr

MOINS = "−"  # le signe moins de l'écrit, pas le trait d'union


def nombre_signe_fr(x: Fraction | int) -> str:
    """-5 -> « −5 » ; Fraction(-7, 3) -> « −7/3 » ; 1234 -> « 1 234 »."""
    valeur = Fraction(x)
    signe = MOINS if valeur < 0 else ""
    valeur = abs(valeur)
    if valeur.denominator == 1:
        return signe + nombre_fr(valeur)
    return f"{signe}{valeur.numerator}/{valeur.denominator}"


def entre_parentheses(x: Fraction | int) -> str:
    """Un nombre négatif (ou une fraction) dans un produit : 3 × (−5), 3 × (7/3)."""
    texte = nombre_signe_fr(x)
    return f"({texte})" if Fraction(x) < 0 or Fraction(x).denominator != 1 else texte


def valeur_machine(x: Fraction | int) -> str:
    """Pour `reponse.valeur` et les pièges : « -5 », « 7/3 », « -7/3 » (exact, lisible par lire_nombre)."""
    valeur = Fraction(x)
    if valeur.denominator == 1:
        return str(valeur.numerator)
    return f"{valeur.numerator}/{valeur.denominator}"


def terme(coef: Fraction | int, variable: str = "x", premier: bool = True) -> str:
    """Un terme en x : premier terme « 3x », « −x », « x » ; terme suivant « + 3x », « − x »."""
    c = Fraction(coef)
    if c == 0:
        return ""
    corps = variable if abs(c) == 1 else f"{nombre_signe_fr(abs(c))}{variable}"
    if premier:
        return f"{MOINS}{corps}" if c < 0 else corps
    return f" {MOINS} {corps}" if c < 0 else f" + {corps}"


def constante(b: Fraction | int, premier: bool = False) -> str:
    """Une constante après un terme : « + 5 », « − 8 » ; seule : « 5 », « −8 »."""
    v = Fraction(b)
    if premier:
        return nombre_signe_fr(v)
    if v == 0:
        return ""
    return f" {MOINS} {nombre_signe_fr(-v)}" if v < 0 else f" + {nombre_signe_fr(v)}"


def affine_fr(a: Fraction | int, b: Fraction | int, variable: str = "x") -> str:
    """ax + b écrit comme en classe : (3, −8) -> « 3x − 8 », (−1, 5) -> « −x + 5 », (0, 4) -> « 4 »."""
    if Fraction(a) == 0:
        return constante(b, premier=True)
    return terme(a, variable) + constante(b)


def facteur_fr(a: Fraction | int, b: Fraction | int, variable: str = "x") -> str:
    """Un facteur d'un produit, entre parenthèses : « (2x − 6) », « (x + 4) »."""
    return f"({affine_fr(a, b, variable)})"
