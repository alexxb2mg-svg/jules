"""Accords selon le genre et variables du profil."""

from __future__ import annotations

import pytest

from jules.composition import charger_profil
from jules.texte import accorder, normaliser_genre, remplir


@pytest.mark.parametrize(
    ("genre", "attendu"),
    [("fille", "elle est prête"), ("garcon", "il est prêt"), ("neutre", "iel est prêt·e")],
)
def test_trois_formes(genre, attendu):
    assert accorder("{{elle|il|iel}} est {{prête|prêt|prêt·e}}", genre) == attendu


def test_deux_formes_donnent_une_forme_neutre_explicite():
    assert accorder("{{une collégienne|un collégien}}", "neutre") == "une collégienne ou un collégien"
    assert accorder("seul{{e|}}", "garcon") == "seul"


def test_accolades_ordinaires_intactes():
    texte = 'JSON : {"a": 1} et {inconnue}'
    assert remplir(texte, {"prenom": "Camille"}, "fille") == texte


def test_variables_et_accords_ensemble():
    assert remplir("{prenom} est {{contente|content}}", {"prenom": "Sam"}, "garcon") == "Sam est content"


@pytest.mark.parametrize(
    ("saisie", "attendu"), [("Fille", "fille"), ("garçon", "garcon"), ("", "neutre"), ("F", "fille")]
)
def test_normaliser_genre(saisie, attendu):
    assert normaliser_genre(saisie) == attendu


def test_genre_inconnu_refuse():
    with pytest.raises(ValueError):
        normaliser_genre("dragon")


def test_profil_exemple_valide():
    from pathlib import Path

    profil = charger_profil(Path(__file__).resolve().parents[1] / "profils" / "exemple.yaml")
    assert profil.genre in {"fille", "garcon", "neutre"}
    assert profil.prenom


@pytest.mark.parametrize("genre", ["fille", "garcon", "neutre"])
def test_prompt_complet_sans_balise_restante(tuteur, genre):
    """Quel que soit le genre, aucune balise {{...}} ou {variable} ne doit arriver au modele."""
    fichier = tuteur.config.fichier_profil
    fichier.write_text(
        fichier.read_text(encoding="utf-8").replace("genre: neutre", f"genre: {genre}"), encoding="utf-8"
    )
    systeme = tuteur.systeme(tuteur.stockage.creer_conversation("aide-devoirs"))
    assert "{{" not in systeme and "}}" not in systeme
    for variable in ("{prenom}", "{classe}", "{parent}"):
        assert variable not in systeme
    if genre == "garcon":
        assert "un collégien" in systeme and "une collégienne" not in systeme
    if genre == "fille":
        assert "une collégienne" in systeme


@pytest.mark.parametrize(("genre", "attendu"), [("fille", "une collégienne"), ("garcon", "un collégien")])
def test_consigne_du_rapport_accordee(genre, attendu):
    from jules.modules.rapport import CONSIGNE_SYNTHESE

    texte = remplir(CONSIGNE_SYNTHESE, {"prenom": "Sam"}, genre)
    assert attendu in texte
    assert "{{" not in texte and "{prenom}" not in texte
