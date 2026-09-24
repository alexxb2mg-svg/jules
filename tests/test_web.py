"""Tests de l'application web : acces par code, API eleve et parent."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from jules.acces import Acces, empreinte
from jules.config import depuis_dict
from jules.moteur import Tuteur
from jules.web.app import creer_app

PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def client_protege(projet, brut_config):
    from jules.llm.factice import Brique as Factice
    from tests.conftest import regle_par_defaut

    brut_config["acces"] = {"code_eleve": empreinte("1234"), "code_parent": empreinte("parent67")}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as client:
        yield client
    tuteur.fermer()


def test_jeton_signe_et_falsification(tmp_path):
    acces = Acces({"code_parent": empreinte("x")}, tmp_path / "s.key")
    jeton = acces.jeton("eleve")
    assert acces.lire_jeton(jeton) == "eleve"
    assert acces.lire_jeton(jeton.replace("eleve", "parent", 1)) is None
    assert acces.lire_jeton(acces.jeton("eleve", maintenant=0)) is None  # expire


def test_sans_code_tout_est_bloque(client_protege):
    assert client_protege.get("/api/infos").status_code == 401
    assert client_protege.get("/api/modules/memoire/notes").status_code == 401
    assert client_protege.get("/").status_code == 200  # la page s'affiche (ecran de code)


def test_code_eleve_ne_donne_pas_acces_parent(client_protege):
    assert client_protege.post("/api/session", json={"code": "faux"}).status_code == 401
    assert client_protege.post("/api/session", json={"code": "1234"}).json() == {"role": "eleve"}
    assert client_protege.get("/api/infos").status_code == 200
    assert client_protege.get("/api/modules/memoire/notes").status_code == 401
    assert client_protege.get("/api/parent/evenements/vigilance").status_code == 401


def test_parent_voit_tout(client_protege):
    client_protege.post("/api/session", json={"code": "parent67"})
    assert client_protege.get("/api/infos").status_code == 200
    note = client_protege.post("/api/modules/memoire/notes", json={"texte": "Contrôle vendredi"}).json()
    assert client_protege.get("/api/modules/memoire/notes").json()[0]["texte"] == "Contrôle vendredi"
    assert client_protege.delete(f"/api/modules/memoire/notes/{note['id']}").json() == {"ok": True}
    assert client_protege.get("/api/modules/rapport/jour").status_code == 200


def test_trop_d_essais(client_protege):
    for _ in range(8):
        client_protege.post("/api/session", json={"code": "faux"})
    assert client_protege.post("/api/session", json={"code": "1234"}).status_code == 429


def test_conversation_avec_photo(client_protege):
    client_protege.post("/api/session", json={"code": "1234"})
    conv = client_protege.post("/api/conversations", json={"mode": "aide-devoirs"}).json()
    r = client_protege.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"texte": "Voilà mon exo"},
        files=[("photos", ("exo.png", io.BytesIO(PNG_1PX), "image/png"))],
    )
    assert r.status_code == 200, r.text
    assert r.json()["reponse"] == "Qu'est-ce que tu as déjà essayé ?"
    lue = client_protege.get(f"/api/conversations/{conv['id']}").json()
    nom = lue["messages"][0]["images"][0]
    assert client_protege.get(f"/api/images/{nom}").content == PNG_1PX
    assert client_protege.get("/api/images/..%2Fjules.db").status_code == 404


def test_refus_fichier_non_image(client_protege):
    client_protege.post("/api/session", json={"code": "1234"})
    conv = client_protege.post("/api/conversations", json={}).json()
    r = client_protege.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"texte": "x"},
        files=[("photos", ("virus.exe", io.BytesIO(b"MZ"), "application/octet-stream"))],
    )
    assert r.status_code == 400


def test_message_vide_refuse(client_protege):
    client_protege.post("/api/session", json={"code": "1234"})
    conv = client_protege.post("/api/conversations", json={}).json()
    assert client_protege.post(f"/api/conversations/{conv['id']}/messages", data={"texte": "  "}).status_code == 400


def test_entetes_de_securite(client_protege):
    r = client_protege.get("/")
    csp = r.headers["content-security-policy"]
    assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp
    assert r.headers["x-content-type-options"] == "nosniff"
    assert client_protege.get("/api/infos").headers["cache-control"] == "no-store"


def test_pages_sans_style_ni_script_en_ligne():
    """La politique de securite interdit le code en ligne : aucune page ne doit en contenir."""
    import re
    from pathlib import Path

    statique = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"
    for page in statique.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert not re.search(r"<script(?![^>]*\bsrc=)", html), page.name
        assert not re.search(r"\son[a-z]+\s*=", html), page.name
        assert "style=" not in html, page.name


def test_faux_png_refuse(client_protege):
    """Le type annonce ne suffit pas : le contenu doit vraiment etre une image."""
    client_protege.post("/api/session", json={"code": "1234"})
    conv = client_protege.post("/api/conversations", json={}).json()
    r = client_protege.post(
        f"/api/conversations/{conv['id']}/messages",
        data={"texte": "x"},
        files=[("photos", ("exo.png", io.BytesIO(b"<script>alert(1)</script>"), "image/png"))],
    )
    assert r.status_code == 400
