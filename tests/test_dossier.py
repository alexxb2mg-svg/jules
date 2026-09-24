"""Tests du dossier de l'eleve : export complet et effacement par le parent.

Tout se passe dans un dossier donnees/ temporaire (fixture `projet`) : aucun vrai dossier n'est touche.
"""

from __future__ import annotations

import io
import json
import sqlite3
import zipfile

import pytest
from fastapi.testclient import TestClient

from jules import dossier
from jules.acces import empreinte
from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import regle_par_defaut
from tests.test_web import PNG_1PX


@pytest.fixture
def famille(projet, brut_config):
    """Un tuteur protege par codes, avec un peu de vie : conversation, photo, note, bilan envoye."""
    brut_config["acces"] = {"code_eleve": empreinte("1234"), "code_parent": empreinte("parent67")}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as client:
        client.post("/api/session", json={"code": "parent67"})
        conv = client.post("/api/conversations", json={"mode": "aide-devoirs"}).json()
        r = client.post(
            f"/api/conversations/{conv['id']}/messages",
            data={"texte": "Camille : 1/2 + 1/3 ?"},
            files=[("photos", ("exo.png", io.BytesIO(PNG_1PX), "image/png"))],
        )
        assert r.status_code == 200, r.text
        client.post("/api/modules/memoire/notes", json={"texte": "Contrôle de maths vendredi"})
        tuteur.attendre_fond()
        tuteur.module("rapport").envoyer()
        tuteur.stockage.ecrire_etat("planificateur", "rapport_quotidien", "2026-09-23")
        yield tuteur, client, conv["id"]
    tuteur.fermer()


def lire_zip(contenu: bytes) -> tuple[list[str], dict]:
    with zipfile.ZipFile(io.BytesIO(contenu)) as zf:
        return zf.namelist(), json.loads(zf.read("dossier.json"))


def test_export_contient_tout_le_dossier(famille):
    _, client, conv_id = famille
    r = client.get("/api/parent/dossier/export")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert "jules-dossier-" in r.headers["content-disposition"]
    noms, contenu = lire_zip(r.content)
    assert "LISEZMOI.txt" in noms and "profil.yaml" in noms
    assert sum(n.startswith("images/") for n in noms) == 1
    assert any(n.startswith("notifications/") for n in noms)
    assert contenu["format"] == "jules-dossier" and contenu["version"] == 1
    conv = contenu["conversations"][0]
    assert conv["id"] == conv_id
    assert conv["messages"][0]["texte"] == "Camille : 1/2 + 1/3 ?"
    assert conv["messages"][0]["images"][0] in {n.removeprefix("images/") for n in noms}
    assert "suivi" in {e["type"] for e in contenu["evenements"]}
    assert contenu["etat"]["memoire"]["notes"][0]["texte"] == "Contrôle de maths vendredi"
    assert "planificateur" not in contenu["etat"]  # technique, rien sur l'eleve


def test_export_et_effacement_reserves_au_parent(famille):
    _, client, conv_id = famille
    client.delete("/api/session")
    client.post("/api/session", json={"code": "1234"})  # code eleve
    assert client.get("/api/parent/dossier/export").status_code == 401
    assert client.post("/api/parent/dossier/effacer", json={"confirmation": "EFFACER"}).status_code == 401
    assert client.delete(f"/api/parent/conversations/{conv_id}").status_code == 401


def test_effacement_refuse_sans_le_mot_de_confirmation(famille):
    tuteur, client, _ = famille
    for mot in ("", "oui", "effacer tout"):
        r = client.post("/api/parent/dossier/effacer", json={"confirmation": mot})
        assert r.status_code == 400 and "EFFACER" in r.json()["detail"]
    assert client.post("/api/parent/dossier/effacer", json={}).status_code == 400
    assert len(tuteur.stockage.lister_conversations()) == 1  # rien n'a bouge


def test_tout_effacer(famille):
    tuteur, client, _ = famille
    donnees = tuteur.config.donnees
    r = client.post("/api/parent/dossier/effacer", json={"confirmation": " effacer "})
    assert r.status_code == 200, r.text
    efface = r.json()["efface"]
    assert efface["conversations"] == 1 and efface["evenements"] >= 1 and efface["bilans"] == 1
    # plus rien dans la base, ni sur le disque
    assert tuteur.stockage.lister_conversations() == []
    assert tuteur.stockage.evenements("suivi") == [] and tuteur.stockage.evenements("vigilance") == []
    assert client.get("/api/modules/memoire/notes").json() == []
    assert list((donnees / "images").iterdir()) == []
    assert list((donnees / "notifications").glob("*.log")) == []
    # le texte efface n'est plus lisible dans le fichier de la base (VACUUM)
    assert b"1/2 + 1/3" not in (donnees / "jules.db").read_bytes()
    assert "Contrôle de maths".encode() not in (donnees / "jules.db").read_bytes()
    # restent : le profil, et la date du dernier bilan (pour ne pas le renvoyer)
    assert tuteur.config.fichier_profil.is_file()
    assert tuteur.stockage.lire_etat("planificateur", "rapport_quotidien") == "2026-09-23"
    # Jules marche encore apres l'effacement
    assert "n'a pas utilisé Jules" in client.get("/api/modules/rapport/jour").json()["texte"]
    client.post("/api/session", json={"code": "1234"})
    conv = client.post("/api/conversations", json={"mode": "aide-devoirs"}).json()
    assert client.post(f"/api/conversations/{conv['id']}/messages", data={"texte": "re"}).status_code == 200


def test_effacer_une_conversation(famille):
    tuteur, client, conv_id = famille
    autre = tuteur.stockage.creer_conversation("quiz")
    tuteur.echanger(autre.id, "Interroge-moi sur Thalès")
    tuteur.attendre_fond()
    photo = tuteur.stockage.conversation(conv_id).messages[0].images[0]
    assert client.delete(f"/api/parent/conversations/{conv_id}").json() == {"ok": True}
    assert client.delete(f"/api/parent/conversations/{conv_id}").status_code == 404
    assert [c["id"] for c in tuteur.stockage.lister_conversations()] == [autre.id]
    assert tuteur.stockage.chemin_image(photo) is None
    assert all(e["conversation"] == autre.id for e in tuteur.stockage.evenements("suivi"))
    assert tuteur.stockage.evenements("suivi")  # les analyses de l'autre conversation restent
    assert client.get("/api/modules/memoire/notes").json()  # les notes du parent aussi


def test_la_base_reste_saine_apres_effacement(famille):
    tuteur, client, _ = famille
    client.post("/api/parent/dossier/effacer", json={"confirmation": "EFFACER"})
    tuteur.stockage.fermer()
    cx = sqlite3.connect(tuteur.config.donnees / "jules.db")
    assert cx.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    cx.close()
    tuteur.stockage = type(tuteur.stockage)(tuteur.config.donnees)  # rouvre pour la fermeture de la fixture


def test_mot_de_confirmation_identique_dans_la_page():
    """La page parent et le serveur doivent demander le meme mot."""
    from pathlib import Path

    statique = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"
    assert f'"{dossier.MOT_DE_CONFIRMATION}"' in (statique / "parent.js").read_text(encoding="utf-8")
    assert f"<b>{dossier.MOT_DE_CONFIRMATION}</b>" in (statique / "parent.html").read_text(encoding="utf-8")
