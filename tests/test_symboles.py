"""Nom des symboles au survol : un module commun, charge par toutes les pages (jules/web/static/symboles.*)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

STATIQUE = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"
PAGES = sorted(STATIQUE.glob("*.html"))


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_chaque_page_charge_le_module_des_symboles(page):
    html = page.read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/static/symboles.css">' in html
    # Avant les scripts de la page : le module observe tout ce qu'ils afficheront.
    assert html.index("/static/symboles.js") < html.index("/static/commun.js")


def test_chaque_page_rappelle_les_lettres_de_sa_notion():
    for page, appel in [
        ("accueil.js", "Symboles.variables("),
        ("eleve.js", "Symboles.notion("),
        ("studio.js", "Symboles.notion("),
        ("cours.js", "Symboles.notion("),
    ]:
        assert appel in (STATIQUE / page).read_text(encoding="utf-8"), page


def test_le_module_n_utilise_jamais_innerhtml():
    code = (STATIQUE / "symboles.js").read_text(encoding="utf-8")
    assert "innerHTML" not in code.replace("Jamais d'innerHTML", "")
    noms = re.findall(r'^\s+"(.+?)": "(.+?)",$', code, flags=re.M)
    assert len(noms) >= 30 and len({s for s, _ in noms}) == len(noms)
    assert {"<", ">", "≤", "≥", "≠", "≈", "√", "π", "Ω"} <= {s for s, _ in noms}
    # Les operations evidentes n'ont pas de bulle : ce sont les lettres des formules qu'on rappelle.
    assert not {"×", "÷", "+", "="} & {s for s, _ in noms}
