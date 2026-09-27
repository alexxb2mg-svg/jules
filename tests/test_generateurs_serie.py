"""Brique `serie` des générateurs : écriture d'une série et indicateurs calculés en exact."""

from __future__ import annotations

import random
from fractions import Fraction

from jules.generateurs.briques.serie import (
    CONTEXTES_SERIE,
    arrondi_dixieme,
    contexte_serie,
    decimal_exact,
    etendue,
    mediane,
    moyenne,
    moyenne_ponderee,
    serie_fr,
    tirer_valeurs,
    total,
)


def test_serie_fr_separe_par_des_points_virgules() -> None:
    assert serie_fr([12, 7, 15]) == "12 ; 7 ; 15"
    assert serie_fr([Fraction(5, 2), 3]) == "2,5 ; 3"


def test_moyenne_et_total_exacts() -> None:
    assert total([12, 7, 15, 9, 11, 8, 14]) == 76
    assert moyenne([12, 7, 15, 9, 11, 8, 14]) == Fraction(76, 7)
    assert moyenne([4, 6]) == 5


def test_mediane_impair_pair_et_non_rangee() -> None:
    assert mediane([12, 7, 15, 9, 11, 8, 14]) == 11  # exemple de la fiche : rangée 7 8 9 11 12 14 15
    assert mediane([4, 18, 6, 10, 8, 12]) == 9  # effectif pair : (8 + 10) / 2
    assert mediane([3, 1, 2]) == 2
    assert mediane([5, 5, 5, 6]) == 5


def test_etendue() -> None:
    assert etendue([12, 7, 15]) == 8


def test_moyenne_ponderee_exemple_de_la_fiche() -> None:
    # 1 élève en a 2, 4 en ont 3, 3 en ont 5, 2 en ont 4 : 37/10
    assert moyenne_ponderee([2, 3, 5, 4], [1, 4, 3, 2]) == Fraction(37, 10)


def test_decimal_exact() -> None:
    assert decimal_exact(Fraction(29, 4))  # 7,25
    assert not decimal_exact(Fraction(29, 8))  # 3,625 : trois chiffres
    assert decimal_exact(Fraction(29, 8), 3)
    assert not decimal_exact(Fraction(1, 3), 12)


def test_arrondi_dixieme() -> None:
    assert arrondi_dixieme(Fraction(76, 7)) == Fraction(109, 10)  # 10,857... -> 10,9
    assert arrondi_dixieme(Fraction(21, 20)) == Fraction(11, 10)  # 1,05 -> 1,1 (demi vers le haut)
    assert arrondi_dixieme(Fraction(-76, 7)) == Fraction(-109, 10)


def test_tirage_deterministe_et_dans_la_plage() -> None:
    rng, rejoue = random.Random(3), random.Random(3)  # noqa: S311 - un tirage rejouable, pas de cryptographie
    a = tirer_valeurs(rng, 12, 4, 20)
    assert a == tirer_valeurs(rejoue, 12, 4, 20)
    assert len(a) == 12 and all(4 <= v <= 20 for v in a)


def test_contextes_coherents() -> None:
    rng = random.Random(1)  # noqa: S311 - un tirage rejouable, pas de cryptographie
    assert contexte_serie(rng) in CONTEXTES_SERIE
    for contexte in CONTEXTES_SERIE:
        assert contexte.bas < contexte.haut
    assert CONTEXTES_SERIE[1].valeur(18) == "18 °C"
    assert CONTEXTES_SERIE[0].valeur(Fraction(25, 2)) == "12,5"
