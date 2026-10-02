"""Tests du module 'retours' (bouton « Un souci, une idée ? » sur chaque page) : aucune IA."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import regle_par_defaut


@pytest.fixture
def tuteur(projet: Path, brut_config: dict):
    autres = [m for m in brut_config["modules"] if not (isinstance(m, dict) and m.get("id") == "retours")]
    brut_config["modules"] = [*autres, {"id": "retours", "reglages": {"par_jour": 3}}]
    llm = Factice()
    llm.regle = regle_par_defaut
    t = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    yield t
    t.fermer()


@pytest.fixture
def client(tuteur):
    with TestClient(creer_app(tuteur)) as c:
        yield c


def test_deposer_garde_l_adresse_et_le_parent_le_lit(client, tuteur):
    r = client.post("/api/eleve/retours/deposer", json={
        "type": "bug", "texte": "Le bouton indice ne fait rien",
        "adresse": "http://127.0.0.1:8799/app/#/fiche/actions-et-forces", "titre_page": "Jules", "ecran": "390x844",
    })  # fmt: skip
    assert r.status_code == 200 and r.json()["ok"]
    liste = client.get("/api/modules/retours/liste").json()
    assert len(liste) == 1
    assert liste[0]["adresse"] == "/app/#/fiche/actions-et-forces"  # ni hote ni port gardes
    assert liste[0]["type"] == "bug" and liste[0]["traite"] is False and liste[0]["ecran"] == "390x844"
    # marquer traite, filtrer, supprimer
    rid = liste[0]["id"]
    assert client.patch(f"/api/modules/retours/{rid}", json={"traite": True}).json()["traite"] is True
    assert client.get("/api/modules/retours/liste?traite=false").json() == []
    assert client.delete(f"/api/modules/retours/{rid}").status_code == 200
    assert client.get("/api/modules/retours/liste").json() == []
    assert client.delete(f"/api/modules/retours/{rid}").status_code == 404


def test_entrees_invalides_et_limite_du_jour(client):
    assert client.post("/api/eleve/retours/deposer", json={"type": "autre", "texte": "abc"}).status_code == 422
    assert client.post("/api/eleve/retours/deposer", json={"type": "suggestion", "texte": "  "}).status_code in (
        400,
        422,
    )
    assert (
        client.post("/api/eleve/retours/deposer", json={"type": "suggestion", "texte": "x" * 3000}).status_code == 422
    )
    for i in range(3):
        assert (
            client.post("/api/eleve/retours/deposer", json={"type": "suggestion", "texte": f"idée {i}"}).status_code
            == 200
        )
    assert (
        client.post("/api/eleve/retours/deposer", json={"type": "suggestion", "texte": "une de trop"}).status_code
        == 429
    )


def test_un_retour_n_entre_ni_dans_une_conversation_ni_dans_le_suivi(client, tuteur):
    avant = tuteur.stockage._cx.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    client.post("/api/eleve/retours/deposer", json={"type": "amelioration", "texte": "Plus de couleurs"})
    assert tuteur.stockage.evenements("suivi") == []
    assert tuteur.stockage._cx.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == avant


# --- profil de test : les retours sont signes par un des testeurs declares ----------------------


def test_testeurs_du_profil_signent_leurs_retours(projet, brut_config):
    (projet / "profils" / "essai-testeurs.yaml").write_text(
        "prenom: Testeurs\nclasse: 3e\ntesteurs: [Amélie, Thibault]\n", encoding="utf-8"
    )
    brut_config["profil"] = "essai-testeurs"
    autres = [m for m in brut_config["modules"] if not (isinstance(m, dict) and m.get("id") == "retours")]
    brut_config["modules"] = [*autres, {"id": "retours"}]
    llm = Factice()
    llm.regle = regle_par_defaut
    t = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    try:
        with TestClient(creer_app(t)) as c:
            assert c.get("/api/infos").json()["retours"]["testeurs"] == ["Amélie", "Thibault"]
            depot = {"type": "suggestion", "texte": "Frise trop petite"}
            assert c.post("/api/eleve/retours/deposer", json=depot).status_code == 400  # qui ecrit ?
            assert c.post("/api/eleve/retours/deposer", json={**depot, "auteur": "Inconnu"}).status_code == 400
            assert c.post("/api/eleve/retours/deposer", json={**depot, "auteur": "Thibault"}).status_code == 200
            liste = c.get("/api/modules/retours/liste?auteur=Thibault").json()
            assert [r["auteur"] for r in liste] == ["Thibault"]
            assert c.get("/api/modules/retours/liste?auteur=Amélie").json() == []
        # les testeurs ne partent jamais dans le prompt
        assert "Thibault" not in t.profil().texte()
    finally:
        t.fermer()


def test_sans_testeurs_le_retour_est_signe_par_l_eleve(client, tuteur):
    assert client.post("/api/eleve/retours/deposer", json={"type": "bug", "texte": "rien ne marche"}).status_code == 200
    assert client.get("/api/modules/retours/liste").json()[0]["auteur"] == tuteur.profil().prenom
