"""Relifting mobile (390 px) de l'interface React, mesure dans un vrai Chromium (tests/cdp.py).

Verifie : le theme sombre suit le reglage du telephone, se force depuis le tiroir et reste memorise apres
rechargement ; dans la discussion, Jules a son portrait une fois par groupe de bulles et les textes restent
lisibles (contraste texte/fond >= 4,5:1 en clair comme en sombre). Passe 3 : schemas SVG agrandissables et lisibles dans
les deux themes, figure interactive en tete de fiche, duree sur les cartes de lecon. Ignore si Chromium ou
l'interface construite (npm run build) est absent.
"""

# ruff: noqa: E501  (expressions JavaScript d'une ligne, plus lisibles ainsi)

from __future__ import annotations

import re
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


# --- passe 2 : blocs de lecon reconnaissables, en-tete collant, liste des lecons en cartes teintees ------------
TEINTES = "[...document.querySelectorAll('section[data-type]')].map((s) => s.dataset.type + '=' + getComputedStyle(s).backgroundColor)"


@pytest.mark.parametrize("sombre", [False, True], ids=["clair", "sombre"])
def test_lecon_blocs_types_et_entete_collant(serveur, tmp_path_factory, sombre):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-relift2"), (390, 844)) as page:
        _ouvrir(page, serveur, "#/lecon/thales-triangles-semblables-trigonometrie", sombre=sombre)
        page.attendre("document.querySelectorAll('section[data-type]').length > 3", delai=20)
        time.sleep(1)
        teintes = dict(t.split("=", 1) for t in page.evaluer(TEINTES))
        fond_page = page.evaluer(FOND)
        # chaque type a sa teinte, distincte des autres et du fond de page (2 niveaux en sombre)
        assert len({teintes[t] for t in ("objectifs", "retenir", "exemple", "exercice")}) == 4, teintes
        assert fond_page not in teintes.values(), (fond_page, teintes)
        # pastille pleine de l'icone du type, formule seule sur sa ligne
        assert (
            page.evaluer(
                "getComputedStyle(document.querySelector('section[data-type=exemple] [data-slot=pastille]')).backgroundColor"
            )
            != teintes["exemple"]
        )
        assert page.evaluer("!!document.querySelector('section[data-type=retenir] [data-formule]')")
        # en-tete collant, titre 20 px
        assert page.evaluer("getComputedStyle(document.querySelector('header')).position") == "sticky"
        assert page.evaluer("parseFloat(getComputedStyle(document.querySelector('header h1')).fontSize)") == 20
        assert page.evaluer(CONTRASTE) >= 4.5


def test_liste_des_lecons_matiere_en_grand_et_cartes_degradees(serveur, tmp_path_factory):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-relift2-liste"), (390, 844)) as page:
        _ouvrir(page, serveur, "#/lecons/mathematiques", sombre=False)
        page.attendre(
            "!!document.querySelector('[role=tablist] [aria-selected=true]') && !!document.querySelector('button [data-slot=progress]')",
            delai=20,
        )
        time.sleep(1)
        assert page.evaluer("parseFloat(getComputedStyle(document.querySelector('h1')).fontSize)") == 30
        assert "gradient" in page.evaluer(
            "getComputedStyle(document.querySelector('[data-slot=progress]').closest('button')).backgroundImage"
        )
        # la matiere active est pleine (accent), les autres en fond de matiere : jamais la meme couleur
        actif = page.evaluer(
            "getComputedStyle(document.querySelector('[role=tab][aria-selected=true]')).backgroundColor"
        )
        autre = page.evaluer(
            "getComputedStyle(document.querySelector('[role=tab][aria-selected=false]')).backgroundColor"
        )
        assert actif != autre
        assert page.evaluer(CONTRASTE) >= 4.5
        # passe 3 : la duree de la lecon sur chaque carte (« 30 min · a faire »), jamais « 0 min »
        metas = page.evaluer(
            "[...document.querySelectorAll('button [data-slot=progress]')].map((p) => p.closest('button').innerText)"
        )
        assert metas and all(re.search(r"\d+\s*min\b", m) for m in metas), metas
        assert not any(re.search(r"\b0\s*min", m) for m in metas), metas


# --- passe 3 : schemas SVG, figure interactive en tete -----------------------------------------------------------
# Contraste des textes d'un schema : fond = derniere forme pleine qui precede le texte et contient son centre, sinon la feuille.
CONTRASTE_SCHEMA = """(() => { const cv = document.createElement('canvas').getContext('2d', {willReadFrequently: true});
  const rgba = (s) => { cv.clearRect(0,0,1,1); cv.fillStyle = '#000'; cv.fillStyle = s; cv.fillRect(0,0,1,1); const d = cv.getImageData(0,0,1,1).data; return [d[0], d[1], d[2], d[3]/255]; };
  const lum = ([r,g,b]) => { const f = (c) => { c /= 255; return c <= .03928 ? c/12.92 : Math.pow((c+.055)/1.055, 2.4); }; return .2126*f(r)+.7152*f(g)+.0722*f(b); };
  const z = document.querySelector('article .bloc-schema'); const papier = rgba(getComputedStyle(z).backgroundColor); let min = 99;
  const formes = [...z.querySelectorAll('rect,circle,ellipse,path,polygon')].filter((f) => { const c = getComputedStyle(f); return c.fill !== 'none' && rgba(c.fill)[3] > .5 && parseFloat(c.fillOpacity) > .5; });
  for (const t of z.querySelectorAll('text')) { if (!t.textContent.trim()) continue; const b = t.getBoundingClientRect(), x = b.x + b.width/2, y = b.y + b.height/2; let fond = papier;
    for (const f of formes) { if (!(f.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_FOLLOWING)) continue; const q = f.getBoundingClientRect(); if (x >= q.left && x <= q.right && y >= q.top && y <= q.bottom) fond = rgba(getComputedStyle(f).fill); }
    const l1 = lum(rgba(getComputedStyle(t).fill)), l2 = lum(fond); min = Math.min(min, (Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05)); }
  return Math.round(min * 100) / 100; })()"""
AGRANDIR = "document.querySelector('[data-schema-agrandir]')"


@pytest.mark.parametrize("sombre", [False, True], ids=["clair", "sombre"])
def test_schema_agrandissable_et_lisible(serveur, tmp_path_factory, sombre):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-relift3-schema"), (390, 844)) as page:
        _ouvrir(page, serveur, "#/fiche/parallelisme-triangles-pythagore", sombre=sombre)
        page.attendre("!!document.querySelector('article .bloc-schema svg')", delai=20)
        page.evaluer(f"{AGRANDIR}.closest('section').scrollIntoView({{block: 'start'}})")
        time.sleep(1)
        assert page.evaluer(SOMBRE) is sombre
        # meme geste que la carte des notions : pastille de 48 px, en haut a droite du bloc
        assert page.evaluer(f"{AGRANDIR}.innerText.trim()") == "Agrandir le schéma"
        assert page.evaluer(f"{AGRANDIR}.getBoundingClientRect().height") >= 44
        # feuille du schema = variable du theme, distincte du fond de page ; textes lisibles (>= 4,5:1)
        papier = page.evaluer("getComputedStyle(document.querySelector('article .bloc-schema')).backgroundColor")
        assert papier != page.evaluer(FOND)
        assert papier == ("rgb(238, 235, 227)" if sombre else "rgb(255, 255, 255)")
        assert page.evaluer(CONTRASTE_SCHEMA) >= 4.5
        _cliquer(page, AGRANDIR)
        page.attendre("!!document.querySelector('[role=dialog] .bloc-schema svg')", delai=5)
        # le dialog a son propre exemplaire du SVG, a sa taille d'origine, et defile si l'ecran est plus etroit
        assert page.evaluer(
            "document.querySelector('[role=dialog] svg') !== document.querySelector('article .bloc-schema svg')"
        )
        assert page.evaluer("document.querySelector('[role=dialog] svg').getBoundingClientRect().width") >= 680
        assert page.evaluer(
            "(() => { const z = document.querySelector('[data-schema-defilement]'); return z.scrollWidth > z.clientWidth; })()"
        )
        page.commande("Input.dispatchKeyEvent", type="keyDown", key="Escape", code="Escape", windowsVirtualKeyCode=27)
        page.commande("Input.dispatchKeyEvent", type="keyUp", key="Escape", code="Escape", windowsVirtualKeyCode=27)
        page.attendre("!document.querySelector('[role=dialog]')", delai=3)
        page.attendre("document.activeElement.hasAttribute('data-schema-agrandir')", delai=3)


def test_figure_interactive_juste_apres_le_premier_bloc(serveur, tmp_path_factory):
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-relift3-graphe"), (390, 844)) as page:
        _ouvrir(page, serveur, "#/fiche/thales-triangles-semblables-trigonometrie", sombre=False)
        page.attendre("!!document.querySelector('article svg.figure')", delai=20)
        types = page.evaluer(
            "[...document.querySelectorAll('article > section')].map((s) => s.querySelector('svg.figure') ? 'graphe' : s.id)"
        )
        assert types.index("graphe") == 1 and types.count("graphe") == 1, types
        assert types[0] == "bloc-formule", types  # l'enonce reste premier
        # le sommaire (grand ecran) suit le meme ordre
        page.commande("Emulation.setDeviceMetricsOverride", width=1280, height=800, deviceScaleFactor=1, mobile=False)
        page.attendre("!!document.querySelector('nav[aria-label=\"Sommaire de la fiche\"] li')", delai=5)
        sommaire = page.evaluer(
            "[...document.querySelectorAll('nav[aria-label=\"Sommaire de la fiche\"] li')].map((l) => l.innerText.trim())"
        )
        assert sommaire[1] == "Vois la notion bouger", sommaire
