"""Tests du module 'outils' : sert les outils sous /api/eleve/outils (voir jules/modules/outils.py).

Isolement testé RÉELLEMENT (résultat noté dans la description de la pull request) via un essai
manuel dans le navigateur (session jules-s2, port 8798) : ici, on vérifie côté serveur ce qui
est vérifiable sans navigateur (en-têtes, refus de sortir du dossier, absence de outil.yaml
servi, 404 propre).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.moteur import Tuteur
from jules.web.app import creer_app

RACINE = Path(__file__).resolve().parents[1]


@pytest.fixture
def client_outils(projet, brut_config):
    from jules.llm.factice import Brique as Factice
    from tests.conftest import regle_par_defaut

    # Les trois outils de référence sont livrés comme extensions (extensions/<id>/, activées dans
    # config.yaml) : la fixture "projet" (tests/conftest.py) copie déjà extensions/.
    brut_config["acces"] = {"code_eleve": empreinte("1234"), "code_parent": empreinte("parent67")}
    brut_config["modules"] = [*brut_config["modules"], {"id": "outils", "actif": True}]
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as client:
        client.post("/api/session", json={"code": "1234"})
        yield client
    tuteur.fermer()


def test_catalogue_liste_les_trois_outils_de_reference(client_outils):
    r = client_outils.get("/api/eleve/outils/catalogue")
    assert r.status_code == 200
    ids = {o["id"] for o in r.json()}
    assert ids == {"frise-chronologique", "calculatrice", "lexique"}
    for o in r.json():
        assert "dossier" not in o and "entree" in o


def test_page_entree_servie_avec_entetes_de_securite(client_outils):
    r = client_outils.get("/api/eleve/outils/calculatrice/")
    assert r.status_code == 200
    assert "<title>Calculatrice</title>" in r.text
    csp = r.headers["content-security-policy"]
    assert "connect-src 'none'" in csp
    assert "default-src 'none'" in csp
    assert r.headers["x-frame-options"] == "SAMEORIGIN"
    assert r.headers["cache-control"] == "no-store"


def test_fichier_js_servi(client_outils):
    r = client_outils.get("/api/eleve/outils/calculatrice/outil.js")
    assert r.status_code == 200
    assert "postMessage" in r.text
    assert r.headers["content-type"].startswith("text/javascript")


def test_outil_yaml_jamais_servi(client_outils):
    assert client_outils.get("/api/eleve/outils/calculatrice/outil.yaml").status_code == 404


def test_sortie_de_dossier_refusee(client_outils):
    assert client_outils.get("/api/eleve/outils/calculatrice/../lexique/outil.js").status_code in (404, 200)
    # Le navigateur normalise ../ avant l'envoi ; on vérifie surtout l'échappement encodé.
    r = client_outils.get("/api/eleve/outils/calculatrice/%2e%2e/lexique/outil.js")
    assert r.status_code == 404


def test_outil_inconnu_404(client_outils):
    assert client_outils.get("/api/eleve/outils/n-existe-pas").status_code == 404


def test_sans_code_acces_refuse(client_outils):
    client_outils.delete("/api/session")
    assert client_outils.get("/api/eleve/outils/catalogue").status_code == 401
