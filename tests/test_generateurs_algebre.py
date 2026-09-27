"""Brique `algebre` des générateurs : écrire le calcul littéral comme en classe."""

from __future__ import annotations

from fractions import Fraction

import pytest

from jules.fiches.correction import lire_nombre
from jules.generateurs.briques.algebre import (
    affine_fr,
    entre_parentheses,
    facteur_fr,
    nombre_signe_fr,
    terme,
    valeur_machine,
)


@pytest.mark.parametrize(
    ("a", "b", "attendu"),
    [
        (3, -8, "3x − 8"),
        (-1, 5, "−x + 5"),
        (1, 0, "x"),
        (0, 4, "4"),
        (-7, -2, "−7x − 2"),
        (Fraction(1, 2), 3, "1/2x + 3"),
    ],
)
def test_affine_ecrit_comme_en_classe(a, b, attendu):
    assert affine_fr(a, b) == attendu


def test_facteur_et_terme():
    assert facteur_fr(2, -6) + facteur_fr(1, 4) == "(2x − 6)(x + 4)"
    assert terme(-3, premier=False) == " − 3x"
    assert terme(1, premier=False) == " + x"


def test_nombres_signes_et_parentheses():
    assert nombre_signe_fr(-5) == "−5"
    assert nombre_signe_fr(Fraction(-7, 3)) == "−7/3"
    assert nombre_signe_fr(12500) == "12 500"
    assert entre_parentheses(-5) == "(−5)"
    assert entre_parentheses(7) == "7"


@pytest.mark.parametrize("x", [Fraction(7, 3), Fraction(-17, 2), Fraction(5), Fraction(-4)])
def test_valeur_machine_exacte_et_lisible_par_le_correcteur(x):
    # nombre_machine écrirait 7/3 en décimal tronqué : valeur_machine le garde exact
    assert lire_nombre(valeur_machine(x)) == x
