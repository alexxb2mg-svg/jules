"""Acces a distance (tunnel Cloudflare) : l'administration ne s'ouvre que sur l'ordinateur ou tourne Jules.

Une requete « distante » porte les en-tetes du relais (cf-connecting-ip...) ou ne vient pas de 127.0.0.1.
A distance : seul un vrai code eleve fait entrer (un code vide n'y vaut jamais acces libre), les routes
parent repondent 403 quel que soit le cookie, et le code parent n'ouvre que l'espace eleve.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from jules.acces import empreinte, requete_distante
from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import regle_par_defaut

CODE_ELEVE = "velo-bleu-42"
CODE_PARENT = "phare-du-nord-77"
TUNNEL = {"cf-connecting-ip": "203.0.113.9", "cf-ray": "8a1b2c3d4e5f-CDG"}


def _app(projet: Path, brut_config: dict, codes: dict[str, str]) -> tuple[Tuteur, TestClient]:
    brut_config["acces"] = codes
    llm = Factice()
    llm.regle = regle_par_defaut
    t = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    return t, TestClient(creer_app(t), client=("127.0.0.1", 50000))


@pytest.fixture
def avec_code_eleve(projet: Path, brut_config: dict):
    t, c = _app(projet, brut_config, {"code_eleve": empreinte(CODE_ELEVE), "code_parent": ""})
    with c:
        yield c
    t.fermer()


@pytest.fixture
def sans_codes(projet: Path, brut_config: dict):
    t, c = _app(projet, brut_config, {"code_eleve": "", "code_parent": ""})
    with c:
        yield c
    t.fermer()


@pytest.fixture
def deux_codes(projet: Path, brut_config: dict):
    t, c = _app(projet, brut_config, {"code_eleve": empreinte(CODE_ELEVE), "code_parent": empreinte(CODE_PARENT)})
    with c:
        yield c
    t.fermer()


def test_detection_distante():
    assert requete_distante({}, "127.0.0.1") is False
    assert requete_distante({}, "::1") is False
    assert requete_distante({"cf-connecting-ip": "1.2.3.4"}, "127.0.0.1") is True  # tunnel sur la meme machine
    assert requete_distante({"x-forwarded-for": "1.2.3.4"}, "127.0.0.1") is True
    assert requete_distante({}, "203.0.113.20") is True  # adresse de documentation (RFC 5737)
    assert requete_distante({}, "testclient") is False  # client en memoire des tests
    assert requete_distante({"cf-ray": "x"}, "testclient") is True


def test_sur_l_ordinateur_tout_reste_comme_avant(avec_code_eleve):
    # code parent vide : l'administrateur, sur son ordinateur, entre sans code
    assert avec_code_eleve.get("/parent").status_code == 200
    assert avec_code_eleve.get("/api/modules/retours/liste").status_code == 200
    assert avec_code_eleve.get("/api/infos").status_code == 401  # l'eleve a un code : il faut le donner
    assert avec_code_eleve.post("/api/session", json={"code": CODE_ELEVE}).status_code == 200
    assert avec_code_eleve.get("/api/infos").status_code == 200


def test_a_distance_l_administration_est_fermee(avec_code_eleve):
    c = avec_code_eleve
    assert c.get("/parent", headers=TUNNEL).status_code == 403
    assert c.get("/api/modules/retours/liste", headers=TUNNEL).status_code == 403
    assert c.get("/api/conversations", headers=TUNNEL).status_code in (401, 403)
    assert c.get("/api/parent/modules", headers=TUNNEL).status_code == 403
    # meme connecte comme eleve
    assert c.post("/api/session", json={"code": CODE_ELEVE}, headers=TUNNEL).json()["role"] == "eleve"
    assert c.get("/api/infos", headers=TUNNEL).status_code == 200
    assert c.get("/api/modules/retours/liste", headers=TUNNEL).status_code == 403
    etat = c.get("/api/session", headers=TUNNEL).json()
    assert etat["distant"] is True and etat["eleve"] is True and etat["parent"] is False


def test_a_distance_un_code_vide_ne_donne_jamais_acces(sans_codes):
    assert sans_codes.get("/api/infos").status_code == 200  # sur l'ordinateur : acces libre, comme avant
    assert sans_codes.get("/api/infos", headers=TUNNEL).status_code == 401
    assert sans_codes.get("/parent", headers=TUNNEL).status_code == 403
    assert sans_codes.get("/api/session", headers=TUNNEL).json()["eleve"] is False


def test_a_distance_le_code_parent_n_ouvre_que_l_espace_eleve(deux_codes):
    c = deux_codes
    assert c.post("/api/session", json={"code": CODE_PARENT}, headers=TUNNEL).json()["role"] == "eleve"
    assert c.get("/api/infos", headers=TUNNEL).status_code == 200
    assert c.get("/api/modules/retours/liste", headers=TUNNEL).status_code == 403


def test_a_distance_l_eleve_peut_envoyer_un_retour(avec_code_eleve):
    c = avec_code_eleve
    c.post("/api/session", json={"code": CODE_ELEVE}, headers=TUNNEL)
    r = c.post("/api/eleve/retours/deposer", json={"type": "bug", "texte": "La frise déborde"}, headers=TUNNEL)
    assert r.status_code == 200
    # l'administrateur le lit sur son ordinateur
    assert [x["texte"] for x in c.get("/api/modules/retours/liste").json()] == ["La frise déborde"]
