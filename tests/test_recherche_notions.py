"""Tests de l'index de recherche des notions (GET /api/eleve/notions/index), barre laterale du front."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import regle_par_defaut

CHAMPS = {"id", "titre", "chapitre", "matiere", "nom_matiere", "niveau", "fiche", "lecon", "mots_cles"}


@pytest.fixture
def client(projet, brut_config):
    brut_config["acces"] = {"code_eleve": empreinte("1234")}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as c:
        c.post("/api/session", json={"code": "1234"})
        yield c, tuteur
    tuteur.fermer()


def test_forme_de_l_index(client):
    c, tuteur = client
    r = c.get("/api/eleve/notions/index")
    assert r.status_code == 200
    notions = r.json()["notions"]
    catalogue = tuteur.module("notions").catalogue
    # toutes les notions du referentiel charge, une seule fois chacune
    assert [n["id"] for n in notions] == list(catalogue.notions)
    for n in notions:
        assert set(n) == CHAMPS
        assert isinstance(n["fiche"], bool) and isinstance(n["lecon"], bool)
        assert isinstance(n["mots_cles"], list) and all(isinstance(m, str) for m in n["mots_cles"])
        assert n["titre"] and n["matiere"] and n["nom_matiere"]
    # plusieurs matieres (pas seulement celles qui ont une fiche)
    assert len({n["matiere"] for n in notions}) > 3


def test_drapeaux_alignes_sur_les_modules(client):
    c, tuteur = client
    notions = {n["id"]: n for n in c.get("/api/eleve/notions/index").json()["notions"]}
    # fiche = meme ensemble que l'index de « Mes fiches »
    fv = c.get("/api/eleve/fiches_visuelles/notions").json()
    avec_fiche = {n["id"] for m in fv["matieres"] for n in m["notions"]}
    assert avec_fiche, "le profil d'exemple doit avoir des fiches visuelles"
    assert {i for i, n in notions.items() if n["fiche"]} == avec_fiche
    # lecon = meme critere que le parcours du module 'cours'
    lecons = set(tuteur.module("cours").lecons)
    assert lecons, "le profil d'exemple doit avoir des lecons"
    assert {i for i, n in notions.items() if n["lecon"]} == lecons & set(notions)
    # une notion sans fiche ni lecon reste listee
    assert any(not n["fiche"] and not n["lecon"] for n in notions.values())


def test_mots_cles_repris_du_referentiel(client):
    c, tuteur = client
    catalogue = tuteur.module("notions").catalogue
    for n in c.get("/api/eleve/notions/index").json()["notions"]:
        notion = catalogue.notion(n["id"])
        attendus = list(dict.fromkeys([*notion.mots_cles, *catalogue.declencheurs(n["id"])]))
        assert n["mots_cles"] == attendus


def test_index_protege_par_code(projet, brut_config):
    brut_config["acces"] = {"code_eleve": empreinte("1234")}
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    with TestClient(creer_app(tuteur)) as c:
        assert c.get("/api/eleve/notions/index").status_code in (401, 403)
    tuteur.fermer()
