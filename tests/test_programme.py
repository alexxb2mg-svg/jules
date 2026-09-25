"""Referentiel du programme officiel : plusieurs niveaux (5e, 4e, 3e) dans la meme bibliotheque."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from jules.bibliotheques import charger_catalogue, lire_identite

BIBLIOTHEQUES = Path(__file__).resolve().parents[1] / "bibliotheque"
PROGRAMME = BIBLIOTHEQUES / "programme"
NIVEAUX = ("5e", "4e", "3e")


def fichiers_du_niveau(niveau: str) -> list[Path]:
    return sorted(f for f in (PROGRAMME / niveau).glob("*.yaml") if not f.name.startswith("_"))


def test_les_trois_niveaux_sont_declares():
    assert set(NIVEAUX) <= set(lire_identite(PROGRAMME).niveaux)


def test_la_3e_ne_change_pas():
    """Rien ne change pour un eleve de 3e : les memes 252 notions qu'avant l'ajout de la 4e et de la 5e."""
    cat = charger_catalogue(BIBLIOTHEQUES, ["programme"], "3e")
    assert len(cat.notions) == 252
    assert {n.niveau for n in cat.notions.values()} == {"3e"}


@pytest.mark.parametrize("niveau", NIVEAUX)
def test_un_niveau_ne_charge_que_ses_notions(niveau):
    cat = charger_catalogue(BIBLIOTHEQUES, ["programme"], niveau)
    attendu = sum(
        len(chapitre["notions"])
        for f in fichiers_du_niveau(niveau)
        for theme in yaml.safe_load(f.read_text(encoding="utf-8"))["themes"]
        for chapitre in theme["chapitres"]
    )
    assert len(cat.notions) == attendu > 0
    assert {n.niveau for n in cat.notions.values()} == {niveau}


def test_les_trois_niveaux_ensemble_sans_doublon():
    """Profil sans classe : tout est charge. Un identifiant en double entre deux niveaux ferait echouer."""
    cat = charger_catalogue(BIBLIOTHEQUES, ["programme"], None)
    declares = lire_identite(PROGRAMME).niveaux  # tous les niveaux declares (CM1 compris), pas seulement le cycle 4
    assert set(NIVEAUX) <= set(declares)
    par_niveau = [len(charger_catalogue(BIBLIOTHEQUES, ["programme"], n).notions) for n in declares]
    assert len(cat.notions) == sum(par_niveau)


@pytest.mark.parametrize("niveau", ("5e", "4e"))
def test_fichiers_4e_5e_au_format(niveau):
    """Meme format que la 3e (SCHEMA.md) : niveau, textes officiels avec lien, attendus et source par notion."""
    fichiers = fichiers_du_niveau(niveau)
    assert {f.stem for f in fichiers} == {f.stem for f in fichiers_du_niveau("3e")}
    for f in fichiers:
        brut = yaml.safe_load(f.read_text(encoding="utf-8"))
        assert brut["id"] == f.stem and str(brut["niveau"]) == niveau, f.name
        assert brut["textes_officiels"], f.name
        for texte in brut["textes_officiels"]:
            assert str(texte["url"]).startswith("https://"), f.name
        for theme in brut["themes"]:
            for chapitre in theme["chapitres"]:
                for n in chapitre["notions"]:
                    assert n["attendus"] and n["source"], f"{f.name} : {n['id']}"
                    assert n["niveau_programme"] in (niveau, "cycle 4"), f"{f.name} : {n['id']}"
