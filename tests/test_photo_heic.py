"""Aide aux devoirs : une photo HEIC (iPhone) est acceptee et convertie en JPEG avant stockage."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app, extension_reelle
from tests.conftest import regle_par_defaut


def _heic(couleur=(30, 30, 200)) -> bytes:
    pillow_heif = pytest.importorskip("pillow_heif")
    from PIL import Image

    pillow_heif.register_heif_opener()
    b = io.BytesIO()
    Image.new("RGB", (64, 48), couleur).save(b, "HEIF")
    return b.getvalue()


def test_extension_reelle_reconnait_heic():
    assert extension_reelle(_heic()) == "heic"


@pytest.mark.parametrize("type_annonce", ["image/heic", "image/heif", "application/octet-stream"])
def test_message_avec_photo_heic(projet, brut_config, type_annonce):
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    try:
        with TestClient(creer_app(tuteur)) as client:
            conv = client.post("/api/conversations", json={"mode": "aide-devoirs"}).json()
            r = client.post(
                f"/api/conversations/{conv['id']}/messages",
                data={"texte": "Je dois le 29 et le 30"},
                files=[("photos", ("IMG_0001.HEIC", io.BytesIO(_heic()), type_annonce))],
            )
            assert r.status_code == 200, r.text
            lu = client.get(f"/api/conversations/{conv['id']}").json()
            images = [i for m in lu["messages"] for i in (m.get("images") or [])]
            assert len(images) == 1 and images[0].endswith(".jpg"), images
            chemin = tuteur.stockage.chemin_image(images[0])
            assert chemin is not None and chemin.read_bytes()[:3] == b"\xff\xd8\xff"
    finally:
        tuteur.fermer()


def test_message_faux_heic_refuse(projet, brut_config):
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    try:
        with TestClient(creer_app(tuteur)) as client:
            conv = client.post("/api/conversations", json={"mode": "aide-devoirs"}).json()
            r = client.post(
                f"/api/conversations/{conv['id']}/messages",
                data={"texte": "?"},
                files=[("photos", ("x.heic", io.BytesIO(b"pas une image du tout"), "image/heic"))],
            )
            assert r.status_code == 400
    finally:
        tuteur.fermer()
