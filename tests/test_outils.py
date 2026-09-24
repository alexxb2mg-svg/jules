"""Tests du chargeur d'outils (jules/outils.py) : voir docs/OUTILS-CONTRAT.md."""

from __future__ import annotations

from pathlib import Path

import pytest

from jules.outils import ErreurOutil, charger_outils, lire_outil

FICHE_VALIDE = """\
id: {id}
titre: "Un outil"
matieres: [mathematiques]
niveaux: [6e]
entree: index.html
actions: [afficher]
evenements: [chose_faite]
permissions: []
auteurs: ["quelqu'un"]
licence: MIT
"""


def creer_outil(racine: Path, identifiant: str, fiche: str | None = None, js: str = "") -> Path:
    dossier = racine / identifiant
    dossier.mkdir(parents=True)
    (dossier / "outil.yaml").write_text(
        fiche if fiche is not None else FICHE_VALIDE.format(id=identifiant), encoding="utf-8"
    )
    (dossier / "index.html").write_text("<!doctype html><title>t</title>", encoding="utf-8")
    if js:
        (dossier / "outil.js").write_text(js, encoding="utf-8")
    return dossier


def test_outil_valide_est_charge(tmp_path):
    dossier = creer_outil(tmp_path, "mon-outil")
    outil = lire_outil(dossier)
    assert outil.id == "mon-outil"
    assert outil.actions == ["afficher"]
    assert outil.evenements == ["chose_faite"]
    assert outil.publique()["id"] == "mon-outil"
    assert "dossier" not in outil.publique()  # jamais le chemin disque cote client


def test_id_doit_correspondre_au_dossier(tmp_path):
    dossier = creer_outil(tmp_path, "mon-outil", fiche=FICHE_VALIDE.format(id="autre-id"))
    with pytest.raises(ErreurOutil, match="doit être le nom du dossier"):
        lire_outil(dossier)


def test_fiche_manquante(tmp_path):
    dossier = tmp_path / "vide"
    dossier.mkdir()
    with pytest.raises(ErreurOutil, match="manquant"):
        lire_outil(dossier)


def test_entree_hors_du_dossier_refusee(tmp_path):
    fiche = FICHE_VALIDE.format(id="mechant").replace("entree: index.html", "entree: ../../secret.html")
    dossier = creer_outil(tmp_path, "mechant", fiche=fiche)
    with pytest.raises(ErreurOutil, match="entree invalide"):
        lire_outil(dossier)


def test_entree_doit_etre_html(tmp_path):
    fiche = FICHE_VALIDE.format(id="mauvais").replace("entree: index.html", "entree: outil.js")
    dossier = creer_outil(tmp_path, "mauvais", fiche=fiche)
    (dossier / "outil.js").write_text("", encoding="utf-8")
    with pytest.raises(ErreurOutil, match=r"page \.html"):
        lire_outil(dossier)


def test_entree_introuvable(tmp_path):
    fiche = FICHE_VALIDE.format(id="fantome").replace("entree: index.html", "entree: absent.html")
    dossier = tmp_path / "fantome"
    dossier.mkdir()
    (dossier / "outil.yaml").write_text(fiche, encoding="utf-8")
    with pytest.raises(ErreurOutil, match="introuvable"):
        lire_outil(dossier)


def test_permission_non_validee_refusee(tmp_path):
    fiche = FICHE_VALIDE.format(id="gourmand").replace("permissions: []", "permissions: [microphone]")
    dossier = creer_outil(tmp_path, "gourmand", fiche=fiche)
    with pytest.raises(ErreurOutil, match="non validée"):
        lire_outil(dossier)


def test_action_mal_formee_refusee(tmp_path):
    fiche = FICHE_VALIDE.format(id="casse").replace("actions: [afficher]", "actions: [Afficher-La-Chose]")
    dossier = creer_outil(tmp_path, "casse", fiche=fiche)
    with pytest.raises(ErreurOutil, match="identifiant invalide"):
        lire_outil(dossier)


def test_licence_manquante_refusee(tmp_path):
    fiche = FICHE_VALIDE.format(id="sanslicence").replace("licence: MIT", "licence: ")
    dossier = creer_outil(tmp_path, "sanslicence", fiche=fiche)
    with pytest.raises(ErreurOutil, match="licence manquante"):
        lire_outil(dossier)


@pytest.mark.parametrize(
    "extrait",
    [
        'fetch("/api/infos")',
        "new XMLHttpRequest()",
        "new WebSocket('wss://x')",
        "eval('1+1')",
        "new Function('return 1')",
        "import('./x.js')",
        "new Worker('w.js')",
        "navigator.sendBeacon('/x', {})",
        "document.cookie",
        "http://exemple.test/donnees.json",
    ],
)
def test_code_avec_motif_interdit_refuse(tmp_path, extrait):
    dossier = creer_outil(tmp_path, "suspect", js=extrait)
    with pytest.raises(ErreurOutil, match=r"motif interdit|adresse externe"):
        lire_outil(dossier)


def test_charger_outils_ecarte_les_invalides_sans_planter(tmp_path):
    creer_outil(tmp_path, "bon")
    dossier_invalide = tmp_path / "invalide"
    dossier_invalide.mkdir()
    (dossier_invalide / "outil.yaml").write_text("id: invalide\n", encoding="utf-8")  # pas de titre, pas d'entree
    outils = charger_outils(tmp_path)
    assert set(outils) == {"bon"}


def test_charger_outils_racine_absente(tmp_path):
    assert charger_outils(tmp_path / "n_existe_pas") == {}


def test_les_trois_outils_de_reference_sont_valides():
    """Les outils livrés avec cette étape doivent tous se charger sans erreur."""
    racine = Path(__file__).resolve().parents[1] / "outils"
    outils = charger_outils(racine)
    assert set(outils) == {"frise-chronologique", "calculatrice", "lexique"}
    for outil in outils.values():
        assert outil.licence == "MIT"
        assert outil.permissions == []
