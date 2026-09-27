"""Générateurs d'exercices déterministes : chaque exercice généré passe le contrat fiches v2 tel quel.

La première partie est GÉNÉRIQUE : elle s'applique à toute notion enregistrée dans `jules.generateurs.MODULES`.
Une nouvelle notion (copiée depuis jules/generateurs/GABARIT.py) est couverte dès son enregistrement, sans
écrire un test. La seconde partie porte sur des cas précis d'une notion (erreurs classiques, parcours).
"""

from __future__ import annotations

import copy
import itertools
import random
from fractions import Fraction

import pytest

from jules.fiches.correction import ILLISIBLE, corriger, piege_declenche, reponse_de_reference
from jules.fiches.parcours import Etat, repondre
from jules.fiches.schema import _verifier_exercice
from jules.generateurs import GABARIT, GENERATEURS, MODULES, generer, serie_generee
from jules.generateurs.briques import ErreurGeneration, ErreurParametre, exercice_v2
from jules.generateurs.briques.format_fr import nombre_fr, nombre_machine, pourcentage_fr, prix_fr
from jules.generateurs.briques.pieges import filtrer_pieges, piege_valeur
from jules.generateurs.briques.tirage import couple_premiers_entre_eux, entier_multiple, tirer
from jules.generateurs.commande import apercu, eprouver, lister
from jules.generateurs.mathematiques import nombres_premiers_decomposition as npd

GRAINES = range(60)
CAS = [
    (notion, variante, difficulte, graine)
    for notion, module in sorted(MODULES.items())
    for variante, difficulte, graine in itertools.product(module.VARIANTES, (1, 2, 3), GRAINES)
]
NOTIONS = sorted(MODULES)


def _fiche_autour(notion: str, ex: dict) -> dict:
    """Une fiche minimale, juste pour donner un contexte au parcours."""
    return {"notion": notion, "prerequis": [], "exercices": [ex]}


# --- générique : toute notion enregistrée ------------------------------------------------------------


@pytest.mark.parametrize(("notion", "variante", "difficulte", "graine"), CAS)
def test_contrat_v2(notion: str, variante: str, difficulte: int, graine: int) -> None:
    ex = generer(notion, graine, difficulte, variante)
    erreurs: list[str] = []
    _verifier_exercice(ex, f"{notion}/{variante}/{graine}", erreurs)
    assert erreurs == []
    assert ex["difficulte"] == difficulte
    assert corriger(ex, reponse_de_reference(ex)).juste


@pytest.mark.parametrize(("notion", "variante", "difficulte", "graine"), CAS)
def test_chaque_piege_se_declenche(notion: str, variante: str, difficulte: int, graine: int) -> None:
    """Un piège à `valeur` est reconnu comme tel ; un piège à `contient` aussi."""
    ex = generer(notion, graine, difficulte, variante)
    for piege in ex["pieges"]:
        condition = piege["si"]
        if "valeur" in condition:
            verdict = corriger(ex, condition["valeur"])
            assert not verdict.juste and verdict.diagnostic != ILLISIBLE
            assert piege_declenche(ex, condition["valeur"], verdict) == piege
        if "contient" in condition:
            verdict = corriger(ex, condition["contient"])
            assert not verdict.juste
            assert piege_declenche(ex, condition["contient"], verdict) == piege


@pytest.mark.parametrize("notion", NOTIONS)
def test_meme_graine_meme_exercice(notion: str) -> None:
    module = MODULES[notion]
    for variante in module.VARIANTES:
        assert module.generer(7, 2, variante) == module.generer(7, 2, variante)
        assert generer(notion, 7, 2, variante) == module.generer(7, 2, variante)


@pytest.mark.parametrize("notion", NOTIONS)
def test_les_graines_donnent_des_variantes(notion: str) -> None:
    module = MODULES[notion]
    for variante in module.VARIANTES:
        enonces = {
            module.generer(g, 2, variante)["enonce"] + str(module.generer(g, 2, variante)["reponse"]) for g in GRAINES
        }
        assert len(enonces) >= len(GRAINES) // 2, f"{notion}/{variante} : trop peu de variété"


@pytest.mark.parametrize("notion", NOTIONS)
def test_sans_variante_le_tirage_choisit(notion: str) -> None:
    module = MODULES[notion]
    vues = {module.generer(g)["id"].split("-")[0] for g in range(60)}
    assert vues == set(module.VARIANTES)


@pytest.mark.parametrize("notion", NOTIONS)
def test_un_piege_au_moins_par_exercice(notion: str) -> None:
    """Un exercice généré sans aucun piège n'aide pas l'élève : le générateur en prévoit toujours."""
    module = MODULES[notion]
    for variante, difficulte, graine in itertools.product(module.VARIANTES, (1, 2, 3), range(20)):
        assert module.generer(graine, difficulte, variante)["pieges"], f"{notion}/{variante}/{difficulte}/{graine}"


@pytest.mark.parametrize("notion", NOTIONS)
def test_serie_generee(notion: str) -> None:
    fiche = serie_generee(notion, 5)
    ids = [ex["id"] for ex in fiche["exercices"]]
    assert len(ids) == len(set(ids)) == len(MODULES[notion].VARIANTES)
    assert fiche["generee"] and fiche["notion"] == notion


@pytest.mark.parametrize("notion", NOTIONS)
def test_parametres_invalides(notion: str) -> None:
    module = MODULES[notion]
    with pytest.raises(ErreurParametre, match="difficulte"):
        module.generer(1, 4)
    with pytest.raises(ErreurParametre, match="variante"):
        module.generer(1, 1, "inconnue")
    assert notion in GENERATEURS


def test_notion_inconnue() -> None:
    with pytest.raises(KeyError):
        generer("notion-inexistante", 1)


def test_gabarit_est_un_generateur_valide() -> None:
    """Le fichier à copier fabrique bien des exercices conformes (sinon il n'apprend rien de bon)."""
    for graine in range(30):
        ex = GABARIT.generer(graine, graine % 3 + 1)
        erreurs: list[str] = []
        _verifier_exercice(ex, f"gabarit/{graine}", erreurs)
        assert erreurs == []


# --- briques ---------------------------------------------------------------------------------------------


def test_filtrer_pieges_ecarte_les_pieges_inutiles() -> None:
    ex = {"type": "nombre", "reponse": {"valeur": 12, "forme": "entier"}}
    pieges = [
        piege_valeur(12, "bonne réponse : écarté"),
        piege_valeur(6, "gardé"),
        piege_valeur("6", "même valeur que le précédent : écarté"),
        piege_valeur("???", "illisible : écarté"),
        piege_valeur(24, "gardé"),
    ]
    assert [p["relance"] for p in filtrer_pieges(ex, pieges)] == ["gardé", "gardé"]


def test_exercice_v2_refuse_un_exercice_non_conforme() -> None:
    with pytest.raises(ErreurGeneration, match="contient la reponse"):
        exercice_v2(
            id="x-1",
            type="nombre",
            difficulte=1,
            enonce="Calcule 3 × 4.",
            reponse={"valeur": 12, "forme": "entier"},
            indices={"relance": "C'est 12.", "methode": "m", "etape": "e"},
            pieges=[],
            solution="3 × 4 = 12.",
        )


def test_tirage_borne() -> None:
    rng = random.Random(1)  # noqa: S311 - un tirage rejouable, pas de cryptographie
    with pytest.raises(ValueError, match="trop stricte"):
        tirer(rng, lambda: 1, lambda v: v == 2, essais=50)
    x, y = couple_premiers_entre_eux(rng, 2, 9)
    assert x != y and 2 <= x <= 9 and 2 <= y <= 9
    assert entier_multiple(rng, 5, 12, 40) % 5 == 0
    with pytest.raises(ValueError, match="multiple"):
        entier_multiple(rng, 50, 12, 40)


def test_format_fr() -> None:
    assert nombre_fr(1234.5) == "1\u202f234,5"
    assert nombre_fr(Fraction(23, 20)) == "1,15"
    assert nombre_fr(80) == "80"
    assert nombre_fr(Fraction(23, 4), 2) == "5,75"
    assert nombre_machine(Fraction(23, 20)) == "1.15"
    assert nombre_machine(1234) == "1234"
    assert pourcentage_fr(Fraction(25, 2)) == "12,5 %"
    assert prix_fr(80) == "80 €"
    assert prix_fr(Fraction(23, 4)) == "5,75 €"


def test_commande_generateurs() -> None:
    assert npd.NOTION in lister()
    texte = apercu(npd.NOTION, 3, 2, "sachets", 2)
    assert "graine 3" in texte and "graine 4" in texte and "Solution" in texte
    assert eprouver([npd.NOTION], graines=10) == []


# --- nombres-premiers-decomposition : cas précis --------------------------------------------------------


def test_decomposer_erreurs_classiques() -> None:
    ex = npd.generer(3, 1, "decomposer")
    n = ex["reponse"]["valeur"]
    # un facteur non premier laissé : partiel, piège dédié
    verdict = corriger(ex, f"{n} = {n // 2} × 2" if n % 2 == 0 else f"{n} = {n // 3} × 3")
    assert verdict.diagnostic == "facteur_non_premier"
    assert "pas premier" in piege_declenche(ex, "x", verdict)["relance"]


def test_parcours_complet_sans_ia() -> None:
    """Le parcours (jules/fiches/parcours.py) sert l'exercice généré : relance de piège, indices, correction."""
    ex = npd.generer(11, 2, "sachets")
    fiche = _fiche_autour(npd.NOTION, copy.deepcopy(ex))
    etat = Etat(ex["id"])
    retour = repondre(fiche, etat, str(ex["pieges"][0]["si"]["valeur"]))
    assert retour.message == ex["pieges"][0]["relance"]
    retour = repondre(fiche, etat, "0")
    assert retour.message == ex["indices"]["relance"]
    retour = repondre(fiche, etat, str(ex["reponse"]["valeur"]))
    assert retour.termine and etat.reussi
