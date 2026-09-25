"""Tests du nettoyage SVG (jules/svg_sur.py) : voir docs/EXTENSIONS.md et jules_architecture_plugins.md."""

from __future__ import annotations

import pytest

from jules.svg_sur import ErreurSvg, nettoyer_svg

SVG_PROPRE = (
    '<svg viewBox="0 0 100 100"><g class="node c-purple"><rect x="0" y="0" width="10" height="10" rx="2"/>'
    '<text class="th" x="5" y="5" text-anchor="middle">Bonjour</text></g></svg>'
)


def test_svg_propre_conserve():
    resultat = nettoyer_svg(SVG_PROPRE)
    assert "<svg" in resultat
    assert "Bonjour" in resultat
    assert 'class="node c-purple"' in resultat
    assert 'xmlns="http://www.w3.org/2000/svg"' in resultat


def test_script_rejete():
    with pytest.raises(ErreurSvg, match="non autorise"):
        nettoyer_svg("<svg><script>alert(1)</script></svg>")


def test_foreignobject_rejete():
    with pytest.raises(ErreurSvg, match="non autorise"):
        nettoyer_svg("<svg><foreignObject><div>x</div></foreignObject></svg>")


def test_gestionnaire_onload_rejete():
    with pytest.raises(ErreurSvg, match="non autorise"):
        nettoyer_svg('<svg onload="alert(1)"><rect x="0" y="0" width="1" height="1"/></svg>')


def test_href_externe_rejete():
    with pytest.raises(ErreurSvg, match="externe"):
        nettoyer_svg('<svg><rect href="https://exemple.test" x="0" y="0" width="1" height="1"/></svg>')


def test_href_local_accepte():
    # <a> n'est pas dans la liste blanche des elements : on verifie via <use xlink:href="#x">,
    # mais <use> non plus n'est pas whiteliste ; on verifie donc marker-end local a la place.
    svg = '<svg><defs><marker id="fleche"/></defs><line x1="0" y1="0" x2="1" y2="1" marker-end="url(#fleche)"/></svg>'
    resultat = nettoyer_svg(svg)
    assert "url(#fleche)" in resultat


def test_marker_externe_rejete():
    with pytest.raises(ErreurSvg, match="ancre locale"):
        nettoyer_svg('<svg><line x1="0" y1="0" x2="1" y2="1" marker-end="url(https://exemple.test/x.svg#f)"/></svg>')


def test_style_avec_url_rejete():
    with pytest.raises(ErreurSvg, match="style"):
        nettoyer_svg('<svg><rect x="0" y="0" width="1" height="1" style="fill:url(https://exemple.test/x.png)"/></svg>')


def test_doctype_rejete():
    with pytest.raises(ErreurSvg, match="DOCTYPE"):
        nettoyer_svg('<!DOCTYPE svg><svg><rect x="0" y="0" width="1" height="1"/></svg>')


def test_entity_rejetee():
    with pytest.raises(ErreurSvg, match="interdit dans un SVG"):
        nettoyer_svg('<!DOCTYPE svg [<!ENTITY x "y">]><svg><rect x="0" y="0" width="1" height="1"/></svg>')


def test_entity_seule_rejetee():
    """Meme sans DOCTYPE visible avant, une ENTITY isolee est refusee."""
    with pytest.raises(ErreurSvg, match="ENTITY"):
        nettoyer_svg('<svg><!ENTITY x "y"><rect x="0" y="0" width="1" height="1"/></svg>')


def test_xml_illisible_rejete():
    with pytest.raises(ErreurSvg, match="illisible"):
        nettoyer_svg("<svg><rect></svg>")


def test_racine_doit_etre_svg():
    with pytest.raises(ErreurSvg, match="racine"):
        nettoyer_svg('<div><rect x="0" y="0" width="1" height="1"/></div>')


def test_attribut_inconnu_rejete():
    with pytest.raises(ErreurSvg, match="non autorise"):
        nettoyer_svg('<svg><rect x="0" y="0" width="1" height="1" data-espion="x"/></svg>')
