"""Tests du module 'synchro' : l'etat de l'interface suit l'eleve d'un appareil a l'autre."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.modules.synchro import fusionner_etapes
from jules.moteur import Tuteur
from jules.web.app import creer_app


@pytest.fixture
def client(projet, brut_config):
    from jules.llm.factice import Brique as Factice
    from tests.conftest import regle_par_defaut

    brut_config["acces"] = {"code_eleve": empreinte("1234"), "code_parent": empreinte("parent67")}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as c:
        c.post("/api/session", json={"code": "1234"})
        yield c
    tuteur.fermer()


def test_sans_code_rien_ne_sort(client):
    anonyme = TestClient(client.app)
    assert anonyme.get("/api/eleve/synchro/etat").status_code == 401
    assert anonyme.put("/api/eleve/synchro/matiere", json={"valeur": "histoire"}).status_code == 401


def test_etat_vide_puis_ecriture_relue(client):
    assert client.get("/api/eleve/synchro/etat").json() == {}  # rien d'ecrit : le client pousse son etat local
    assert client.put("/api/eleve/synchro/matiere", json={"valeur": "francais"}).json() == {"valeur": "francais"}
    assert client.put("/api/eleve/synchro/filtre_fiches", json={"valeur": "perso"}).status_code == 200
    etat = client.get("/api/eleve/synchro/etat").json()
    assert etat["matiere"] == "francais"
    assert etat["filtre_fiches"] == "perso"
    assert "etapes" not in etat


def test_choix_explicite_de_toutes_les_matieres_est_conserve(client):
    client.put("/api/eleve/synchro/matiere", json={"valeur": "histoire"})
    client.put("/api/eleve/synchro/matiere", json={"valeur": None})
    assert client.get("/api/eleve/synchro/etat").json() == {"matiere": None}


def test_etapes_se_fusionnent_entre_appareils(client):
    # telephone : a lu la fiche ; PC : a fait l'entrainement, sans connaitre l'etape du telephone
    client.put("/api/eleve/synchro/etapes", json={"valeur": {"pythagore": ["fiche"]}})
    r = client.put("/api/eleve/synchro/etapes", json={"valeur": {"pythagore": ["exercices"], "thales": ["lecon"]}})
    assert r.json()["valeur"] == {"pythagore": ["fiche", "exercices"], "thales": ["lecon"]}
    assert client.get("/api/eleve/synchro/etat").json()["etapes"] == r.json()["valeur"]


def test_fusion_pure_et_ordre():
    assert fusionner_etapes({"a": ["exercices"]}, {"a": ["fiche", "lecon"]}) == {"a": ["fiche", "lecon", "exercices"]}


def test_recentes_valides(client):
    rec = [{"genre": "perso", "id": "x1", "titre": "Mon cours", "matiere": "francais"}]
    assert client.put("/api/eleve/synchro/fiches_recentes", json={"valeur": rec}).json() == {"valeur": rec}


@pytest.mark.parametrize(
    ("cle", "valeur"),
    [
        ("matiere", 12),
        ("filtre_fiches", "tout-et-n-importe-quoi"),
        ("etapes", ["pas", "un", "objet"]),
        ("etapes", {"n": "pas une liste"}),
        ("fiches_recentes", [{"genre": "inconnu", "id": "a", "titre": "b", "matiere": "c"}]),
        ("fiches_recentes", [{"genre": "perso", "id": "a", "titre": "b", "matiere": "c"}] * 7),
    ],
)
def test_formes_invalides_refusees(client, cle, valeur):
    assert client.put(f"/api/eleve/synchro/{cle}", json={"valeur": valeur}).status_code == 422


def test_cle_inconnue_refusee(client):
    assert client.put("/api/eleve/synchro/n_importe_quoi", json={"valeur": 1}).status_code == 404


def test_etapes_inconnues_ecartees(client):
    r = client.put("/api/eleve/synchro/etapes", json={"valeur": {"n": ["fiche", "piratage"]}})
    assert r.json()["valeur"] == {"n": ["fiche"]}
