"""Route /app : la nouvelle interface (front/) est servie a cote des pages existantes, sans les remplacer."""

from __future__ import annotations

from fastapi.testclient import TestClient

from jules.config import depuis_dict
from jules.moteur import Tuteur
from jules.web import app as module_app


def _client(projet, brut_config, monkeypatch, statique=None):
    from jules.llm.factice import Brique as Factice
    from tests.conftest import regle_par_defaut

    if statique is not None:
        monkeypatch.setattr(module_app, "STATIQUE", statique)
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    return tuteur, TestClient(module_app.creer_app(tuteur))


def test_app_sans_build_repond_404_explicite(projet, brut_config, monkeypatch, tmp_path):
    tuteur, client = _client(projet, brut_config, monkeypatch, tmp_path)
    try:
        r = client.get("/app")
        assert r.status_code == 404 and "npm run build" in r.text
    finally:
        tuteur.fermer()


def test_app_sert_le_build_avec_les_entetes_de_securite(projet, brut_config, monkeypatch, tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "index.html").write_text('<!doctype html><div id="root"></div>', encoding="utf-8")
    tuteur, client = _client(projet, brut_config, monkeypatch, tmp_path)
    try:
        r = client.get("/app")
        assert r.status_code == 200 and 'id="root"' in r.text
        assert "script-src 'self'" in r.headers["content-security-policy"]
    finally:
        tuteur.fermer()


def test_les_anciennes_pages_redirigent_vers_l_interface(projet, brut_config, monkeypatch):
    """Depuis la bascule sur l'interface React, chaque ancienne adresse (favoris, ecran d'accueil du telephone)
    mene a l'ecran correspondant de /app, sans jamais servir l'ancienne page."""
    tuteur, client = _client(projet, brut_config, monkeypatch)
    try:
        for ancienne, cible in [
            ("/", "/app#/fiches"),
            ("/discuter", "/app#/discuter"),
            ("/cours", "/app#/lecons"),
            ("/studio", "/app#/supports"),
            ("/parent", "/app#/parent"),
        ]:
            r = client.get(ancienne, follow_redirects=False)
            assert r.status_code == 302 and r.headers["location"] == cible, ancienne
    finally:
        tuteur.fermer()
