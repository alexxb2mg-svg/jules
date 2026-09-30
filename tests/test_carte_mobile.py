"""Carte des notions d'une fiche visuelle sur telephone : reduite a l'ecran + bouton « Agrandir » (Dialog Radix).

Pilote Chromium headless (tests/cdp.py) sur un serveur reel, fiche thales-triangles-semblables-trigonometrie.
Verifie : le SVG tient dans l'ecran (390 px), plus de defilement parasite, bouton de 44 px, dialog ouvert avec une
carte lisible (>= 11 px reels) defilable, Echap qui ferme et rend le focus au bouton.
Ignore si le navigateur ou l'interface construite (jules/web/static/app) est absent.
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
FICHE = "thales-triangles-semblables-trigonometrie"
SVG = 'svg[aria-label="Carte des notions"]'
MESURE = f"""(() => {{ const s = document.querySelector('{SVG}'); s.scrollIntoView({{block: 'center'}});
  const r = s.getBoundingClientRect(); const vb = s.viewBox.baseVal; const t = s.querySelector('text.carte-titre');
  const b = document.querySelector('[data-carte-agrandir]').getBoundingClientRect();
  return JSON.stringify({{svg: r.width, doc: document.documentElement.clientWidth, defile: s.parentElement.scrollWidth - s.parentElement.clientWidth,
    police: parseFloat(getComputedStyle(t).fontSize) * r.width / vb.width, bouton: b.height, libelle: document.querySelector('[data-carte-agrandir]').innerText}}); }})()"""
DIALOG = f"""(() => {{ const d = document.querySelector('[role=dialog]'); if (!d) return null;
  const s = d.querySelector('{SVG}'); const r = s.getBoundingClientRect(); const vb = s.viewBox.baseVal; const t = s.querySelector('text.carte-titre');
  return JSON.stringify({{police: parseFloat(getComputedStyle(t).fontSize) * r.width / vb.width, focus: d.contains(document.activeElement),
    noeuds: d.querySelectorAll('[data-adresse^="carte/"]').length}}); }})()"""


@pytest.fixture
def serveur(projet, brut_config):
    if not INTERFACE.is_file():
        pytest.skip("interface React non construite (npm run build dans front/)")
    brut_config["acces"] = {"code_eleve": empreinte(CODE)}
    brut_config["modules"] = [
        *(brut_config.get("modules") or []),
        {"id": "fiches_visuelles", "reglages": {"bibliotheques": ["fiches-visuelles-3e-experimentales"]}},
    ]
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


def _ouvrir_fiche(page, url: str) -> None:
    page.commande("Page.navigate", url=url + "/static/favicon.ico")
    time.sleep(0.5)
    page.evaluer(
        "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
    )
    time.sleep(0.5)
    page.commande("Page.navigate", url=f"{url}/app#/fiche/{FICHE}")
    page.attendre(f"!!document.querySelector('{SVG}')", delai=20)
    time.sleep(1.5)


def test_carte_reduite_a_l_ecran_et_agrandissable_sur_telephone(serveur, tmp_path_factory):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-carte-mobile"), (390, 844)) as page:
        page.commande("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
        _ouvrir_fiche(page, serveur)
        m = json.loads(page.evaluer(MESURE))
        assert m["svg"] <= 390, m
        assert m["defile"] <= 4, m
        assert m["bouton"] >= 44, m
        assert "Agrandir" in m["libelle"], m
        assert page.evaluer("!document.querySelector('[role=dialog]')")

        page.cliquer(
            *page.evaluer(
                "(() => { const r = document.querySelector('[data-carte-agrandir]').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()"
            )
        )
        page.attendre("!!document.querySelector('[role=dialog]')", delai=8)
        time.sleep(0.6)
        d = json.loads(page.evaluer(DIALOG))
        assert d["police"] >= 11, d
        assert d["focus"], d
        assert d["noeuds"] >= 3, d

        page.touche("Escape", "Escape", 27)
        page.attendre("!document.querySelector('[role=dialog]')", delai=8)
        assert page.evaluer("document.activeElement.hasAttribute('data-carte-agrandir')")
