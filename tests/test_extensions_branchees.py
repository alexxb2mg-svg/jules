"""Etape 2 des extensions : les figures et les outils du coeur viennent des extensions actives
(voir docs/EXTENSIONS.md, jules/extensions.py `code_des_figures` et `dossiers_outils`)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.extensions import (
    ErreurExtension,
    charger_extensions,
    dossiers_outils,
    figures_fournies,
    lire_extension,
)
from jules.moteur import Tuteur
from jules.outils import charger_outils
from jules.web.app import creer_app

RACINE = Path(__file__).resolve().parents[1]
FIGURES = {"droite-affine", "triangle-thales", "triangle-rectangle", "equation-solutions", "probabilites-frequences"}
OUTILS = {"calculatrice", "frise-chronologique", "lexique"}
RAPPELS = {"rappels-sciences", "rappels-histoire", "rappels-francais"}

MANIFESTE = """\
id: {id}
titre: "Essai"
version: "1.0.0"
licence: MIT
fournit:
  {famille}: [{fourni}]
"""


def creer(
    racine: Path, identifiant: str, famille: str = "figures", fourni: str = "", gabarit: str | None = None
) -> Path:
    dossier = racine / identifiant
    dossier.mkdir(parents=True)
    (dossier / "extension.yaml").write_text(
        MANIFESTE.format(id=identifiant, famille=famille, fourni=fourni or identifiant), encoding="utf-8"
    )
    if gabarit is not None:
        (dossier / "gabarit.js").write_text(gabarit, encoding="utf-8")
    return dossier


# --- les extensions du depot, telles qu'activees dans config.yaml --------------------


def test_config_active_les_cinq_figures_les_trois_outils_et_les_rappels():
    ids = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))["extensions"]
    extensions = charger_extensions(RACINE / "extensions", ids)
    assert set(extensions) == FIGURES | OUTILS | RAPPELS  # aucune ecartee
    assert {e.id for e in extensions.values() if e.fournit_liste("rappels")} == RAPPELS
    assert set(figures_fournies(extensions)) == FIGURES
    dossiers = dossiers_outils(extensions)
    assert {d.name for d in dossiers} == OUTILS
    assert all((d / "outil.yaml").is_file() for d in dossiers)


# --- figures : controle du code -----------------------------------------------------


def test_figure_sans_gabarit_js_refusee(tmp_path):
    with pytest.raises(ErreurExtension, match=r"gabarit\.js"):
        lire_extension(creer(tmp_path, "sans-code"))


@pytest.mark.parametrize(
    ("code", "motif"),
    [
        ("eval('1');", "eval"),
        ("new Function('return 1');", "Function"),
        ("fetch('/api/eleve/infos');", "fetch"),
        ('const u = "https://exemple.org/x.js";', "adresse externe"),
    ],
)
def test_figure_avec_motif_interdit_refusee(tmp_path, code, motif):
    with pytest.raises(ErreurExtension, match=motif):
        lire_extension(creer(tmp_path, "suspecte", gabarit=code))


def test_espace_de_noms_svg_admis(tmp_path):
    code = 'const NS = "http://www.w3.org/2000/svg"; window.GABARITS["ok"] = {};'
    assert lire_extension(creer(tmp_path, "ok", gabarit=code)).fournit_liste("figures") == ["ok"]


# --- outils : ou vit le code ----------------------------------------------------------


def test_dossiers_outils_extension_ou_sous_dossier(tmp_path):
    seul = creer(tmp_path, "mon-outil", famille="outils")
    pack = creer(tmp_path, "pack", famille="outils", fourni="autre-outil")
    extensions = charger_extensions(tmp_path, ["mon-outil", "pack"])
    assert dossiers_outils(extensions) == [seul, pack / "autre-outil"]


def test_charger_outils_depuis_outils_et_extensions_sans_doublon(tmp_path):
    source = RACINE / "extensions" / "lexique"
    ancien = tmp_path / "outils" / "lexique"
    ancien.mkdir(parents=True)
    for fichier in source.iterdir():
        if fichier.name != "extension.yaml":
            (ancien / fichier.name).write_bytes(fichier.read_bytes())
    outils = charger_outils(tmp_path / "outils", [RACINE / "extensions" / "calculatrice", source])
    assert set(outils) == {"lexique", "calculatrice"}
    assert outils["lexique"].dossier == ancien  # outils/ (retrocompatibilite) passe en premier


# --- branchement web ------------------------------------------------------------------


def client_pour(projet: Path, brut_config: dict, extensions: list[str]):
    from jules.llm.factice import Brique as Factice
    from tests.conftest import regle_par_defaut

    brut_config["acces"] = {"code_eleve": empreinte("1234")}
    brut_config["extensions"] = extensions
    brut_config["modules"] = [*brut_config["modules"], {"id": "outils"}]
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    client = TestClient(creer_app(tuteur))
    client.post("/api/session", json={"code": "1234"})
    return tuteur, client


def test_sixieme_figure_ajoutee_par_extension_sans_toucher_l_accueil(projet, brut_config):
    creer(projet / "extensions", "ma-sixieme", gabarit='window.GABARITS["ma-sixieme"] = {};')
    tuteur, client = client_pour(projet, brut_config, [*brut_config["extensions"], "ma-sixieme"])
    try:
        code = client.get("/gabarits.js").text
        assert 'window.GABARITS["ma-sixieme"]' in code
        assert 'window.GABARITS["droite-affine"]' in code
    finally:
        tuteur.fermer()


def test_sans_extension_de_figures_aucune_fiche_a_graphe_acceptee(projet, brut_config):
    """Preuve que le coeur ne connait plus les gabarits par leur nom : sans extension, les 5 fiches
    (qui ont toutes une figure) sont ecartees, et /gabarits.js est vide."""
    tuteur, client = client_pour(projet, brut_config, [])
    try:
        assert client.get("/gabarits.js").text == ""
        assert tuteur.module("fiches_visuelles").fiches == {}
        assert client.get("/api/eleve/outils/catalogue").json() == []
    finally:
        tuteur.fermer()


def test_outil_fourni_par_extension_servi_sans_son_manifeste(projet, brut_config):
    tuteur, client = client_pour(projet, brut_config, ["lexique"])
    try:
        assert {o["id"] for o in client.get("/api/eleve/outils/catalogue").json()} == {"lexique"}
        assert client.get("/api/eleve/outils/lexique/").status_code == 200
        assert client.get("/api/eleve/outils/lexique/extension.yaml").status_code == 404
        assert client.get("/api/eleve/outils/calculatrice/").status_code == 404  # non activee
    finally:
        tuteur.fermer()
