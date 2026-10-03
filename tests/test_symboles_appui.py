"""Bulles de rappel au doigt : sur telephone/tablette, un appui ouvre la bulle, un autre la ferme.

Vrais evenements d'entree (CDP Input.dispatchTouchEvent / dispatchMouseEvent) dans Chromium headless
en mode tactile emule : on teste la brique commune symboles.js, pas une page en particulier.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jules.chantier_visuel import _chromium
from tests.cdp import navigateur_cdp

STATIQUE = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"

PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<style>{css} body{{font-size:24px;padding:80px 20px}}</style>
<body><div id="z"><p>On lit P = m × g, avec 10 kg.</p><p id="ailleurs">Un autre paragraphe.</p></div>
<script>{js}</script>
<script>setTimeout(() => Symboles.contexte(document.getElementById("z"),
  {{matiere: "physique-chimie",
  variables: {{P: "le poids", m: "la masse", g: "l'intensité de la pesanteur"}}}}), 0)</script>
</body>"""

VISIBLE = "!!document.querySelector('.symboles-bulle.visible')"
TEXTE = "document.querySelector('.symboles-bulle') && document.querySelector('.symboles-bulle').textContent"


def _centre(page, selecteur):
    return page.evaluer(
        f"(() => {{ const r = document.querySelector({selecteur!r}).getBoundingClientRect();"
        " return [r.left + r.width / 2, r.top + r.height / 2]; })()"
    )


def _appui(page, x, y):
    page.commande("Input.dispatchTouchEvent", type="touchStart", touchPoints=[{"x": x, "y": y}])
    page.commande("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])


@pytest.fixture
def page(tmp_path):
    chromium = _chromium()
    if not chromium:
        pytest.skip("Chromium absent")
    html = tmp_path / "page.html"
    html.write_text(
        PAGE.format(
            css=(STATIQUE / "symboles.css").read_text(encoding="utf-8"),
            js=(STATIQUE / "symboles.js").read_text(encoding="utf-8"),
        ),
        encoding="utf-8",
    )
    with navigateur_cdp(chromium, tmp_path / "profil", (400, 800)) as p:
        yield p, html


def _ouvrir(p, html, tactile):
    if tactile:
        p.commande("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
        p.commande("Emulation.setEmitTouchEventsForMouse", enabled=True, configuration="mobile")
    p.commande("Page.navigate", url=html.as_uri())
    p.attendre("document.querySelectorAll('abbr.symbole').length >= 3")


def test_un_appui_ouvre_la_bulle_un_autre_la_ferme(page):
    p, html = page
    _ouvrir(p, html, tactile=True)
    x, y = _centre(p, "abbr.symbole")
    _appui(p, x, y)
    p.attendre(VISIBLE)
    assert p.evaluer(TEXTE) == p.evaluer("document.querySelector('abbr.symbole').dataset.nom")
    # La bulle reste ouverte (pas de survol au doigt qui la referme aussitot).
    assert p.evaluer(VISIBLE)
    # Appui ailleurs : fermee.
    x2, y2 = _centre(p, "#ailleurs")
    _appui(p, x2, y2)
    p.attendre("!" + VISIBLE)


def test_appui_sur_une_autre_bulle_change_de_definition(page):
    p, html = page
    _ouvrir(p, html, tactile=True)
    x, y = _centre(p, "abbr.symbole")
    _appui(p, x, y)
    p.attendre(VISIBLE)
    premiere = p.evaluer(TEXTE)
    x2, y2 = _centre(p, "abbr.symbole:nth-of-type(2)")
    _appui(p, x2, y2)
    p.attendre(f"{VISIBLE} && ({TEXTE}) !== {premiere!r}")
    # Re-appui sur la meme : fermee.
    _appui(p, x2, y2)
    p.attendre("!" + VISIBLE)


def test_la_souris_garde_le_survol(page):
    p, html = page
    _ouvrir(p, html, tactile=False)
    x, y = _centre(p, "abbr.symbole")
    p.commande("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    p.attendre(VISIBLE)
    p.commande("Input.dispatchMouseEvent", type="mouseMoved", x=5, y=5)
    p.attendre("!" + VISIBLE)
