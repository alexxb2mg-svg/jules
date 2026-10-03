"""Prise de photo directe (brique front/src/composants/PriseDePhoto.tsx), dans « Ajouter mon cours » et le chat.

Chromium headless (tests/cdp.py) sur un vrai serveur, code eleve actif. Sur mobile (390 px) : deux inputs fichier
(`capture=environment` et sans `capture`), deux boutons de 44 px au moins, et un PNG injecte par
`DOM.setFileInputFiles` dans l'input galerie devient une vignette. Sur bureau : un seul input, sans `capture`.
Ignore si Chromium ou l'interface construite (jules/web/static/app) est absent.
"""

# ruff: noqa: E501  (expressions JavaScript d'une ligne, plus lisibles ainsi)

from __future__ import annotations

import base64
import json
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.cdp import navigateur, navigateur_cdp
from tests.conftest import regle_par_defaut

CODE = "1234"
INTERFACE = Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "app" / "index.html"

CODE = "1234"
INTERFACE = Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "app" / "index.html"


@pytest.fixture
def serveur(projet, brut_config):
    if not INTERFACE.is_file():
        pytest.skip("interface React non construite (npm run build dans front/)")
    brut_config["acces"] = {"code_eleve": empreinte(CODE), "code_parent": empreinte("parent67")}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    serveur = uvicorn.Server(uvicorn.Config(creer_app(tuteur), host="127.0.0.1", port=port, log_level="error"))
    fil = threading.Thread(target=serveur.run, daemon=True)
    fil.start()
    limite = time.monotonic() + 15
    while not serveur.started and time.monotonic() < limite:
        time.sleep(0.05)
    assert serveur.started, "serveur de test non demarre"
    yield f"http://127.0.0.1:{port}"
    serveur.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
ENTREES = (
    "JSON.stringify([...document.querySelectorAll('input[type=file]')]"
    ".map((i) => ({capture: i.getAttribute('capture'), accept: i.getAttribute('accept')})))"
)
BOUTONS = (
    "JSON.stringify([...document.querySelectorAll('button')].filter((b) => b.getBoundingClientRect().width > 0)"
    ".map((b) => ({t: (b.innerText || b.getAttribute('aria-label') || b.title || '').trim(),"
    " h: b.getBoundingClientRect().height, w: b.getBoundingClientRect().width})))"
)


def _centre(page, expression: str) -> tuple[float, float]:
    page.attendre(f"!!{expression}", delai=15)
    return tuple(
        page.evaluer(
            f"(() => {{ const r = {expression}.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }})()"
        )
    )


def _ouvrir(page, url: str, route: str) -> None:
    page.commande("Page.navigate", url=url + "/static/favicon.ico")
    time.sleep(0.5)
    page.evaluer(
        "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
    )
    time.sleep(0.5)
    page.commande("Page.navigate", url=url + "/app#/" + route)


def _injecter(page, chemin: Path) -> None:
    racine = page.commande("DOM.getDocument")["root"]["nodeId"]
    noeuds = page.commande("DOM.querySelectorAll", nodeId=racine, selector="input[type=file]")["nodeIds"]
    galerie = [n for n in noeuds if "capture" not in page.commande("DOM.getAttributes", nodeId=n)["attributes"]]
    assert len(galerie) == 1
    page.commande("DOM.setFileInputFiles", nodeId=galerie[0], files=[str(chemin)])


@pytest.mark.parametrize(("taille", "nom"), [((1280, 800), "bureau"), ((390, 844), "mobile")])
def test_prise_de_photo_ajouter(serveur, tmp_path_factory, taille, nom):
    dossier = tmp_path_factory.mktemp(f"chromium-photo-{nom}")
    image = dossier / "test.png"
    image.write_bytes(PNG)
    with navigateur_cdp(navigateur(), dossier, taille) as page:
        _ouvrir(page, serveur, "ajouter")
        page.cliquer(
            *_centre(page, "[...document.querySelectorAll('[role=tab]')].find((b) => /photo/i.test(b.innerText))")
        )
        page.attendre("document.querySelectorAll('input[type=file]').length > 0", delai=10)
        entrees = json.loads(page.evaluer(ENTREES))
        boutons = json.loads(page.evaluer(BOUTONS))
        assert all("heic" in e["accept"] for e in entrees)  # le HEIC reste accepte
        if nom == "mobile":
            assert sorted(str(e["capture"]) for e in entrees) == ["None", "environment"]
            for libelle in ("Prendre une photo", "Choisir une image"):
                (b,) = [b for b in boutons if b["t"] == libelle]
                assert b["h"] >= 44 and b["w"] >= 44
        else:
            assert [e["capture"] for e in entrees] == [None]  # bureau inchange : un seul input, sans capture
            assert not [b for b in boutons if b["t"] in ("Prendre une photo", "Choisir une image")]
        _injecter(page, image)
        page.attendre("document.querySelectorAll('ul img').length === 1", delai=10)


@pytest.mark.parametrize(("taille", "nom"), [((1280, 800), "bureau"), ((390, 844), "mobile")])
def test_prise_de_photo_chat(serveur, tmp_path_factory, taille, nom):
    dossier = tmp_path_factory.mktemp(f"chromium-photo-chat-{nom}")
    image = dossier / "test.png"
    image.write_bytes(PNG)
    with navigateur_cdp(navigateur(), dossier, taille) as page:
        _ouvrir(page, serveur, "discuter")
        page.cliquer(
            *_centre(page, "[...document.querySelectorAll('button')].find((b) => /Aide aux devoirs/.test(b.innerText))")
        )
        page.attendre("!!document.querySelector('textarea')", delai=15)
        entrees = json.loads(page.evaluer(ENTREES))
        boutons = json.loads(page.evaluer(BOUTONS))
        assert all(e["accept"] == "image/*" for e in entrees)
        if nom == "mobile":
            assert sorted(str(e["capture"]) for e in entrees) == ["None", "environment"]
            for libelle in ("Prendre une photo", "Choisir une image"):
                (b,) = [b for b in boutons if b["t"] == libelle]
                assert b["h"] >= 44 and b["w"] >= 44
        else:
            assert [e["capture"] for e in entrees] == [None]
        _injecter(page, image)
        page.attendre("document.querySelectorAll('img[alt=aperçu]').length === 1", delai=10)
