"""Tiroir de navigation sur telephone (front/src/composants/Nav.tsx) : un choix referme le tiroir.

Pilote Chromium headless (tests/cdp.py) en 390 x 844 avec de vrais appuis : rubrique, fiche recente, « Ajouter mon
cours », choix de matiere. Apres chacun, le tiroir (Sheet mobile) doit avoir disparu ET la page avoir change.
Sur bureau (1280 x 800) la barre reste en place. Ignore si Chromium ou l'interface construite est absent.
"""

# ruff: noqa: E501  (expressions JavaScript d'une ligne, plus lisibles ainsi)

from __future__ import annotations

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
LARGEUR_TIROIR = """(() => { const e = document.querySelector('[data-sidebar="sidebar"][data-mobile="true"]'); return e ? Math.round(e.getBoundingClientRect().width) : 0; })()"""
RECENTE = {
    "genre": "native",
    "id": "fonctions-lineaires-affines",
    "titre": "Fonctions lineaires",
    "matiere": "mathematiques",
}


@pytest.fixture
def serveur(projet, brut_config):
    if not INTERFACE.is_file():
        pytest.skip("interface React non construite (npm run build dans front/)")
    brut_config["acces"] = {"code_eleve": empreinte(CODE)}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(creer_app(tuteur), host="127.0.0.1", port=port, log_level="error"))
    fil = threading.Thread(target=srv.run, daemon=True)
    fil.start()
    limite = time.monotonic() + 15
    while not srv.started and time.monotonic() < limite:
        time.sleep(0.05)
    assert srv.started, "serveur de test non demarre"
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


def _centre(page, selecteur_js: str) -> tuple[float, float]:
    c = page.evaluer(
        f"(() => {{ const e = {selecteur_js}; if (!e) return null; const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }})()"
    )
    assert c, f"element introuvable : {selecteur_js}"
    return c[0], c[1]


def _dans_tiroir(texte: str) -> str:
    return f'[...document.querySelectorAll(\'[data-mobile="true"] a, [data-mobile="true"] button\')].find((b) => b.innerText.trim().startsWith({json.dumps(texte)}))'


def _ouvrir_tiroir(page) -> None:
    page.cliquer(*_centre(page, "document.querySelector('[data-sidebar=\"trigger\"]')"))
    page.attendre(f"({LARGEUR_TIROIR}) > 200", delai=8)
    time.sleep(0.4)


def _aller(page, url: str, hash_: str) -> None:
    page.commande("Page.navigate", url=url + "/app" + hash_)
    page.attendre(
        "!!document.querySelector('[data-sidebar=\"trigger\"]') || !!document.querySelector('[data-sidebar=\"sidebar\"]')",
        delai=15,
    )
    time.sleep(0.6)


def _ferme_et_route(page, route: str) -> None:
    page.attendre(f"({LARGEUR_TIROIR}) === 0 && location.hash.startsWith({json.dumps(route)})", delai=8)


def test_tiroir_mobile_se_ferme_apres_chaque_choix(serveur, tmp_path):
    with navigateur_cdp(navigateur(), tmp_path / "profil", (390, 844)) as page:
        page.commande("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
        page.commande("Page.navigate", url=serveur + "/static/favicon.ico")
        time.sleep(0.5)
        page.evaluer(
            "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
            f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
        )
        page.evaluer(f"localStorage.setItem('jules.fiches-recentes', {json.dumps(json.dumps([RECENTE]))})")
        time.sleep(0.4)

        # fiche recente
        _aller(page, serveur, "#/fiches")
        _ouvrir_tiroir(page)
        page.cliquer(*_centre(page, _dans_tiroir("Fonctions lineaires")))
        _ferme_et_route(page, "#/fiche/fonctions-lineaires-affines")

        # « Ajouter mon cours »
        _aller(page, serveur, "#/fiches")
        _ouvrir_tiroir(page)
        page.cliquer(*_centre(page, _dans_tiroir("Ajouter mon cours")))
        _ferme_et_route(page, "#/ajouter")

        # rubrique « Mes leçons »
        _ouvrir_tiroir(page)
        page.cliquer(*_centre(page, _dans_tiroir("Mes leçons")))
        _ferme_et_route(page, "#/lecons")

        # le bouton d'ouverture reste utilisable : le tiroir se rouvre
        _ouvrir_tiroir(page)
        assert page.evaluer(LARGEUR_TIROIR) > 200


def test_barre_bureau_inchangee(serveur, tmp_path):
    with navigateur_cdp(navigateur(), tmp_path / "profil", (1280, 800)) as page:
        page.commande("Emulation.setDeviceMetricsOverride", width=1280, height=800, deviceScaleFactor=1, mobile=False)
        page.commande("Page.navigate", url=serveur + "/static/favicon.ico")
        time.sleep(0.5)
        page.evaluer(
            "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
            f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
        )
        time.sleep(0.4)
        _aller(page, serveur, "#/fiches")
        page.cliquer(
            *_centre(
                page,
                "[...document.querySelectorAll('[data-sidebar=\"menu-button\"]')].find((b) => b.innerText.trim().startsWith('Mes leçons'))",
            )
        )
        page.attendre("location.hash.startsWith('#/lecons')", delai=8)
        assert (
            page.evaluer(
                "Math.round(document.querySelector('[data-sidebar=\"sidebar\"]').getBoundingClientRect().width)"
            )
            > 200
        )
        assert page.evaluer(LARGEUR_TIROIR) == 0
