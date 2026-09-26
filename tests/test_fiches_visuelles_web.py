"""Tests du module 'fiches_visuelles' et de la page d'accueil « Mes fiches » (/)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.moteur import Tuteur
from jules.web.app import creer_app

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"


@pytest.fixture
def client_fiches(projet, brut_config):
    from jules.llm.factice import Brique as Factice
    from tests.conftest import regle_par_defaut

    brut_config["acces"] = {"code_eleve": empreinte("1234")}
    brut_config["modules"] = [
        *(brut_config.get("modules") or []),
        {"id": "fiches_visuelles", "reglages": {"bibliotheques": ["fiches-visuelles-3e-experimentales"]}},
    ]
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as client:
        client.post("/api/session", json={"code": "1234"})
        yield client
    tuteur.fermer()


def test_liste_notions_fiches_visuelles(client_fiches):
    r = client_fiches.get("/api/eleve/fiches_visuelles/notions")
    assert r.status_code == 200
    matieres = r.json()["matieres"]
    assert len(matieres) == 1
    maths = matieres[0]
    assert maths["id"] == "mathematiques"
    ids = {n["id"] for n in maths["notions"]}
    assert ids == {
        "fonctions-lineaires-affines",
        "thales-triangles-semblables-trigonometrie",
        "parallelisme-triangles-pythagore",
        "equations-premier-degre-et-produits",
        "probabilites-experiences-simples",
    }


def test_une_fiche_par_notion(client_fiches):
    r = client_fiches.get("/api/eleve/fiches_visuelles/notions/fonctions-lineaires-affines")
    assert r.status_code == 200
    fiche = r.json()
    assert fiche["titre"]
    assert fiche["relecture_a_relire"] is True
    assert fiche["blocs"][0]["type"] == "attendus"
    assert len(fiche["blocs"][0]["attendus"]) >= 1
    types = {b["type"] for b in fiche["blocs"][1:]}
    assert types == {"formule", "carte", "graphe", "methode", "piege", "exemple", "renfort"}


def test_fiche_inconnue_404(client_fiches):
    r = client_fiches.get("/api/eleve/fiches_visuelles/notions/notion-inconnue")
    assert r.status_code == 404


def test_routes_fiches_visuelles_protegees_par_code(projet, brut_config):
    """Sans code eleve, les routes de fiches visuelles sont bloquees comme le reste (/api/eleve/*)."""
    from jules.llm.factice import Brique as Factice
    from tests.conftest import regle_par_defaut

    llm = Factice()
    llm.regle = regle_par_defaut
    brut_config2 = dict(brut_config)
    brut_config2["acces"] = {"code_eleve": empreinte("1234")}
    tuteur = Tuteur(depuis_dict(brut_config2, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as client_sans_code:
        assert client_sans_code.get("/api/eleve/fiches_visuelles/notions").status_code == 401
    tuteur.fermer()


def test_page_accueil_sert_mes_fiches(client_fiches):
    r = client_fiches.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "accueil.js" in r.text
    assert "Mes fiches" in r.text


def test_page_discuter_sert_l_ancien_chat(client_fiches):
    r = client_fiches.get("/discuter")
    assert r.status_code == 200
    assert "eleve.js" in r.text


def test_gabarits_javascript_servis(client_fiches):
    """Les 5 figures livrees comme extensions (config.yaml, extensions:) sont servies par /gabarits.js."""
    r = client_fiches.get("/gabarits.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    for gabarit in (
        "droite-affine",
        "triangle-thales",
        "triangle-rectangle",
        "equation-solutions",
        "probabilites-frequences",
    ):
        assert f'window.GABARITS["{gabarit}"]' in r.text, gabarit
    # une extension presente dans le depot mais non activee n'est pas servie
    assert "exemple-cercle" not in r.text


def test_accueil_charge_les_gabarits_par_les_extensions():
    html = (STATIQUE / "accueil.html").read_text(encoding="utf-8")
    assert '<script src="/gabarits.js"></script>' in html
    assert "/static/gabarits/" not in html


def test_accueil_html_couvert_par_verification_style_script():
    pages = {p.name for p in STATIQUE.glob("*.html")}
    assert "accueil.html" in pages


def test_accueil_js_echappe_tout_texte_serveur_avant_innerhtml():
    """Le titre, les attendus, les textes de blocs viennent du serveur : jamais concatenes bruts."""
    js = (STATIQUE / "accueil.js").read_text(encoding="utf-8")
    assert "MS.echapper(" in js or "textContent" in js
    # aucun `.innerHTML = ...donnee_serveur...` direct : soit un vidage "", soit un gabarit dont
    # la seule interpolation passe par MS.echapper(...)
    import re

    for match in re.findall(r"\.innerHTML\s*=\s*([^;]+);", js):
        match = match.strip()
        if match == '""':
            continue
        interpolations = re.findall(r"\$\{([^}]*)\}", match)
        assert interpolations, f"affectation innerHTML suspecte : {match}"
        for interpolation in interpolations:
            assert interpolation.strip().startswith("MS.echapper("), f"non echappe : {interpolation}"


def test_gabarits_ne_font_jamais_appel_a_eval():
    import re

    fichiers = list((RACINE / "extensions").glob("*/gabarit.js"))
    assert len(fichiers) >= 5
    for fichier in fichiers:
        lignes_code = [
            ligne for ligne in fichier.read_text(encoding="utf-8").splitlines() if not ligne.strip().startswith("//")
        ]
        js = "\n".join(lignes_code)
        assert not re.search(r"\beval\s*\(", js), fichier.name


def test_rappels_d_une_notion_pour_toutes_les_pages(client_fiches):
    r = client_fiches.get("/api/eleve/fiches_visuelles/notions/fonctions-lineaires-affines/rappels")
    assert r.status_code == 200 and set(r.json()) == {"variables", "abreviations"}
    # Une notion sans fiche visuelle : rien a rappeler, pas d'erreur (la page ne sait pas d'avance).
    r = client_fiches.get("/api/eleve/fiches_visuelles/notions/racine-carree/rappels")
    assert r.status_code == 200 and r.json() == {"variables": {}, "abreviations": {}}
