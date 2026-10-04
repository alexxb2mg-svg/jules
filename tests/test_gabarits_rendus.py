"""Rendu reel de gabarits dans Chromium headless : textes ecrits par la figure pour des valeurs donnees.

Les autres tests lisent les declarations (extension.yaml) ; ici on execute gabarit.js et on lit le SVG produit,
pour les decisions qui portent sur ce que la figure ECRIT : seuil de la dose de jauge-decibels (85 dB(A) sur 8 h,
Code du travail art. R4431-2, regle des 3 dB) et absence de verdict en mots dans urne-tirage.

JULES_CAPTURES_GABARITS=<dossier> : enregistre en plus une capture PNG de chaque rendu (preuve visuelle).
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import pytest

from tests.cdp import Page, navigateur, navigateur_cdp

EXTENSIONS = Path(__file__).resolve().parents[1] / "extensions"


@pytest.fixture(scope="module")
def page(tmp_path_factory: pytest.TempPathFactory):
    chromium = navigateur()
    with navigateur_cdp(chromium, tmp_path_factory.mktemp("profil-gabarits"), (420, 420)) as p:
        p.evaluer("document.body.style.margin = '0'; document.body.style.background = '#FFFFFF'; true")
        for gabarit in ("jauge-decibels", "urne-tirage"):
            p.evaluer((EXTENSIONS / gabarit / "gabarit.js").read_text(encoding="utf-8") + "\ntrue")
        yield p


def _rendre(page: Page, gabarit: str, valeurs: dict[str, float]) -> list[str]:
    """Dessine le gabarit dans un SVG neuf de 420 px et rend ses textes, dans l'ordre du document."""
    script = f"""(() => {{
        document.body.replaceChildren();
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "420"); svg.setAttribute("height", "420");
        document.body.appendChild(svg);
        window.GABARITS[{json.dumps(gabarit)}].dessiner(svg, {json.dumps(valeurs)});
        return [...svg.querySelectorAll("text")].map((t) => t.textContent);
    }})()"""
    textes = page.evaluer(script)
    dossier = os.environ.get("JULES_CAPTURES_GABARITS")
    if dossier:
        nom = gabarit + "".join(f"_{k}-{v}" for k, v in valeurs.items()) + ".png"
        png = page.commande("Page.captureScreenshot", format="png")["data"]
        Path(dossier).mkdir(parents=True, exist_ok=True)
        (Path(dossier) / nom).write_bytes(base64.b64decode(png))
    return list(textes)


@pytest.mark.parametrize(
    ("niveau", "duree", "verdict"),
    [
        (85, 8, "juste à la limite"),
        (91, 2, "juste à la limite"),
        (94, 1, "juste à la limite"),
        (88, 4.5, "limite dépassée"),
        (88, 4, "juste à la limite"),
        (82, 8, "sous la limite"),
    ],
)
def test_jauge_dose_sur_85_db_pendant_8_h(page, niveau, duree, verdict):
    """Meme reference que la fiche 3e physiologie-audition : 8 h a 85 dB, duree divisee par 2 tous les 3 dB."""
    textes = _rendre(page, "jauge-decibels", {"niveau": niveau, "duree": duree})
    assert textes[-1] == verdict, textes


@pytest.mark.parametrize(
    ("niveau", "titre"),
    [(80, "80 dB : sans danger"), (85, "85 dB : danger si ça dure"), (120, "120 dB : danger immédiat")],
)
def test_jauge_zone_orange_a_partir_de_85(page, niveau, titre):
    textes = _rendre(page, "jauge-decibels", {"niveau": niveau, "duree": 1})
    assert textes[0] == titre
    assert {"20", "85", "120"} <= set(textes) and "80" not in textes  # graduations de la jauge


@pytest.mark.parametrize("rouges", range(11))
def test_urne_sans_verdict_en_mots(page, rouges):
    """L'eleve qualifie l'evenement a partir de la fleche : la figure n'ecrit ni « peu probable » ni « probable »,
    seulement la composition du sac et les trois reperes de l'echelle."""
    textes = _rendre(page, "urne-tirage", {"rouges": rouges})
    bleues = 10 - rouges
    assert textes == [
        f"{rouges} {'rouges' if rouges > 1 else 'rouge'}",
        f"{bleues} {'bleues' if bleues > 1 else 'bleue'}",
        "impossible",
        "une chance",
        "sur deux",
        "certain",
    ]
    assert not any("probable" in t or "Tirer" in t for t in textes)
