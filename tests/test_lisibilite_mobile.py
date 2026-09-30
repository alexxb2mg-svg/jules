"""Lisibilite sur telephone (390 px) de l'interface React, mesuree dans un vrai Chromium (tests/cdp.py).

Verifie : aucun texte sous 14 px sur l'ecran de discussion ; aucun paragraphe du cadre « A retenir » de plus de
5 lignes visuelles (lecon Thales) ; bouton « Demander a Jules » reduit en pastille pendant le defilement puis
redevenu complet a l'arret ; degrade (masque) sur le bandeau des matieres ; bureau inchange (paragraphe d'origine
d'un seul tenant, pas de masque). Ignore si Chromium ou l'interface construite (npm run build) est absent.
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
LECON = "#/lecon/thales-triangles-semblables-trigonometrie"

PETITS_TEXTES = """(() => { const r = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n; const vus = new Set();
  while ((n = w.nextNode())) { if (!n.textContent.trim()) continue; const e = n.parentElement; if (!e || vus.has(e)) continue; vus.add(e);
    const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const b = e.getBoundingClientRect(); if (!b.width || !b.height) continue;
    if (parseFloat(cs.fontSize) < 14) r.push(e.tagName + ':' + cs.fontSize + ':' + n.textContent.trim().slice(0, 30)); }
  return r; })()"""
LIGNES_RETENIR = """(() => { const out = []; for (const s of document.querySelectorAll('section')) {
  if (!/À retenir/i.test(s.innerText.slice(0, 40))) continue;
  for (const p of s.querySelectorAll('p')) { const cs = getComputedStyle(p); let lh = parseFloat(cs.lineHeight); if (isNaN(lh)) lh = parseFloat(cs.fontSize) * 1.2;
    out.push(Math.round(p.getBoundingClientRect().height / lh)); } } return out; })()"""
BOUTON = "(() => { const b = document.querySelector('button[aria-label=\"Demander à Jules\"]'); if (!b) return null; const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })()"
MASQUE = (
    "(() => { const t = document.querySelector('[role=tablist]'); return t ? getComputedStyle(t).maskImage : null; })()"
)


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


def _ouvrir(page, url: str, largeur: int, hauteur: int, route: str) -> None:
    page.commande(
        "Emulation.setDeviceMetricsOverride",
        width=largeur,
        height=hauteur,
        deviceScaleFactor=2,
        mobile=largeur < 768,
    )
    page.commande("Page.navigate", url=url + "/static/favicon.ico")
    time.sleep(0.5)
    page.evaluer(
        "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
    )
    time.sleep(0.5)
    page.commande("Page.navigate", url=url + "/app" + route)


def test_discussion_aucun_texte_sous_14_px(serveur, tmp_path_factory):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-lisi-chat"), (390, 844)) as page:
        _ouvrir(page, serveur, 390, 844, "#/discuter")
        page.attendre("!!document.body && document.body.innerText.includes('Aide aux devoirs')", delai=20)
        time.sleep(1)
        assert page.evaluer(PETITS_TEXTES) == []


def test_a_retenir_aere_sur_mobile_et_intact_sur_bureau(serveur, tmp_path_factory):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-lisi-mob"), (390, 844)) as page:
        _ouvrir(page, serveur, 390, 844, LECON)
        page.attendre("!!document.body && document.body.innerText.toLowerCase().includes('à retenir')", delai=20)
        time.sleep(1)
        lignes = page.evaluer(LIGNES_RETENIR)
        assert lignes and max(lignes) <= 5, lignes
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-lisi-bur"), (1280, 800)) as page:
        _ouvrir(page, serveur, 1280, 800, LECON)
        page.attendre("!!document.body && document.body.innerText.toLowerCase().includes('à retenir')", delai=20)
        time.sleep(1)
        lignes = page.evaluer(LIGNES_RETENIR)
        assert len(lignes) == 4, lignes  # bureau : un paragraphe par bloc, comme avant


def test_bouton_jules_se_reduit_au_defilement(serveur, tmp_path_factory):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-lisi-btn"), (390, 844)) as page:
        _ouvrir(page, serveur, 390, 844, LECON)
        page.attendre(f"!!({BOUTON})", delai=20)
        time.sleep(1)
        assert page.evaluer(BOUTON)[0] > 100  # complet au repos
        for _ in range(3):
            page.commande("Input.dispatchMouseEvent", type="mouseWheel", x=200, y=400, deltaX=0, deltaY=300)
            time.sleep(0.15)
        assert page.evaluer(BOUTON) == [48, 48]  # pastille ronde pendant le defilement vers le bas
        page.attendre(f"({BOUTON})[0] > 100", delai=5)  # complet de nouveau a l'arret


def test_bandeau_matieres_a_un_degrade_sur_mobile_seulement(serveur, tmp_path_factory):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-lisi-fondu"), (390, 844)) as page:
        _ouvrir(page, serveur, 390, 844, "#/lecons")
        page.attendre("!!document.querySelector('[role=tablist]')", delai=20)
        time.sleep(1)
        assert "linear-gradient" in page.evaluer(MASQUE)
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-lisi-fondu-b"), (1280, 800)) as page:
        _ouvrir(page, serveur, 1280, 800, "#/lecons")
        page.attendre("!!document.querySelector('[role=tablist]')", delai=20)
        time.sleep(1)
        assert page.evaluer(MASQUE) == "none"
