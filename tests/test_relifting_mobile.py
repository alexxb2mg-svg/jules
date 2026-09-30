"""Relifting mobile (390 px) de l'interface React, mesure dans un vrai Chromium (tests/cdp.py).

Verifie : le theme sombre suit le reglage du telephone, se force depuis le tiroir et reste memorise apres
rechargement ; dans la discussion, Jules a son portrait une fois par groupe de bulles et les textes restent
lisibles (contraste texte/fond >= 4,5:1 en clair comme en sombre). Ignore si Chromium ou l'interface construite
(npm run build) est absent.
"""

# ruff: noqa: E501  (expressions JavaScript d'une ligne, plus lisibles ainsi)

from __future__ import annotations

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

SOMBRE = "document.documentElement.classList.contains('dark')"
FOND = "getComputedStyle(document.body).backgroundColor"
CENTRE = "(() => {{ const e = {}; if (!e) return null; const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }})()"
BOUTON_THEME = "document.querySelector('[data-mobile=\"true\"] button[aria-pressed]')"
# Contraste minimal (WCAG) des textes HTML visibles, fond reconstitue en remontant les parents.
CONTRASTE = """(() => { const cv = document.createElement('canvas').getContext('2d', {willReadFrequently: true});
  const rgba = (s) => { cv.clearRect(0,0,1,1); cv.fillStyle = '#000'; cv.fillStyle = s; cv.fillRect(0,0,1,1); const d = cv.getImageData(0,0,1,1).data; return [d[0], d[1], d[2], d[3]/255]; };
  const lum = ([r,g,b]) => { const f = (c) => { c /= 255; return c <= .03928 ? c/12.92 : Math.pow((c+.055)/1.055, 2.4); }; return .2126*f(r)+.7152*f(g)+.0722*f(b); };
  const fond = (e) => { const pile = []; for (let x = e; x; x = x.parentElement) { const v = rgba(getComputedStyle(x).backgroundColor); if (v[3] > 0) { pile.push(v); if (v[3] >= .99) break; } }
    let res = [255,255,255,1]; for (const v of pile.reverse()) res = [0,1,2].map(i => v[i]*v[3] + res[i]*(1-v[3])).concat(1); return res; };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n, min = 99; const vus = new Set();
  while ((n = w.nextNode())) { if (!n.textContent.trim()) continue; const e = n.parentElement; if (!e || vus.has(e) || e.closest('svg,.sr-only')) continue; vus.add(e);
    const cs = getComputedStyle(e); const b = e.getBoundingClientRect(); if (cs.visibility === 'hidden' || !b.width || b.bottom < 0 || b.top > innerHeight) continue;
    let op = 1; for (let x = e; x; x = x.parentElement) op *= parseFloat(getComputedStyle(x).opacity); if (op < .05) continue;
    const t = rgba(cs.color), f = fond(e), tc = [0,1,2].map(i => t[i]*t[3]*op + f[i]*(1-t[3]*op));
    const l1 = lum(tc), l2 = lum(f); min = Math.min(min, (Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05)); }
  return Math.round(min * 100) / 100; })()"""


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


def _ouvrir(page, url: str, route: str, sombre: bool) -> None:
    page.commande("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
    page.commande(
        "Emulation.setEmulatedMedia",
        features=[{"name": "prefers-color-scheme", "value": "dark" if sombre else "light"}],
    )
    page.commande("Page.navigate", url=url + "/static/favicon.ico")
    time.sleep(0.5)
    page.evaluer(
        "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
    )
    time.sleep(0.5)
    page.commande("Page.navigate", url=url + "/app" + route)


def _cliquer(page, js: str) -> None:
    point = page.evaluer(CENTRE.format(js))
    assert point, js
    page.cliquer(*point)


def test_theme_sombre_suit_le_telephone_et_se_force_depuis_le_tiroir(serveur, tmp_path_factory):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-theme"), (390, 844)) as page:
        _ouvrir(page, serveur, "#/lecons", sombre=True)
        page.attendre("!!document.querySelector('[role=tablist]')", delai=20)
        assert page.evaluer(SOMBRE) is True
        assert page.evaluer(FOND) == "rgb(20, 17, 31)"
        _cliquer(page, "document.querySelector('[data-sidebar=\"trigger\"]')")
        page.attendre(f"!!{BOUTON_THEME}", delai=8)
        time.sleep(0.5)
        _cliquer(page, BOUTON_THEME)
        page.attendre(f"!{SOMBRE}", delai=5)
        assert page.evaluer("localStorage.getItem('jules-theme')") == "clair"
        page.commande("Page.reload")
        page.attendre("!!document.querySelector('[role=tablist]')", delai=20)
        assert page.evaluer(SOMBRE) is False  # le choix de l'eleve l'emporte sur le reglage du telephone


@pytest.mark.parametrize("sombre", [False, True], ids=["clair", "sombre"])
def test_discussion_jules_en_personnage_et_lisible(serveur, tmp_path_factory, sombre):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-chat"), (390, 844)) as page:
        _ouvrir(page, serveur, "#/discuter", sombre=sombre)
        page.attendre("!!document.body && document.body.innerText.includes('Aide aux devoirs')", delai=20)
        time.sleep(0.8)
        _cliquer(page, "[...document.querySelectorAll('button')].find((b) => /Aide aux devoirs/.test(b.innerText))")
        page.attendre("!!document.querySelector('textarea')", delai=10)
        page.evaluer(
            "(() => { const t = document.querySelector('textarea'); Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')"
            ".set.call(t, 'Comment on calcule une longueur ?'); t.dispatchEvent(new Event('input', {bubbles: true})); return 1 })()"
        )
        time.sleep(0.3)
        _cliquer(page, "document.querySelector('button[aria-label=Envoyer]')")
        page.attendre("document.querySelectorAll('.bulle-jules').length === 2", delai=15)
        time.sleep(0.5)
        # Jules, eleve, Jules : deux groupes de bulles de Jules, donc deux portraits dans le fil (40 px).
        portraits = page.evaluer(
            "[...document.querySelectorAll('.bulle-jules')].map((b) => { const a = b.parentElement.querySelector('[data-slot=avatar-jules]'); return a ? Math.round(a.getBoundingClientRect().width) : 0; })"
        )
        assert portraits == [40, 40]
        assert page.evaluer("parseFloat(getComputedStyle(document.querySelector('.bulle-jules')).fontSize)") >= 16
        assert page.evaluer("parseFloat(getComputedStyle(document.querySelector('h1')).fontSize)") >= 28
        assert page.evaluer(SOMBRE) is sombre
        assert page.evaluer(CONTRASTE) >= 4.5
