"""Nettoyage d'un SVG avant de le servir au bloc de fiche `schema` (voir jules_architecture_plugins.md).

Un fichier .svg n'est jamais servi tel quel : ce module le relit avec `xml.etree` (stdlib, pas
d'entites externes) et ne garde que les elements et attributs d'une liste blanche. Tout le reste
fait echouer `nettoyer_svg` avec `ErreurSvg` : pas de degrade silencieux, pas de bloc affiche a
moitie nettoye.

Refuse d'office :
  - `<!DOCTYPE ...>` ou `<!ENTITY ...>` (attaque XXE / bombe d'entites) ;
  - `<script>`, `<foreignObject>` (code libre) ;
  - les attributs `on*` (gestionnaires d'evenements) ;
  - `href` / `xlink:href` vers autre chose qu'une ancre locale (`#id`) ;
  - tout attribut `style` contenant `url(` (peut charger une ressource externe).

Ce nettoyage est la seule protection : le SVG vient d'un fichier du depot (relu par un adulte),
mais on le traite comme une entree non fiable, comme pour le code d'un outil (jules/outils.py).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

NS_SVG = "http://www.w3.org/2000/svg"

# Elements autorises (sans le namespace : ElementTree les rend sous la forme "{ns}nom").
ELEMENTS_AUTORISES = frozenset(
    {
        "svg",
        "g",
        "defs",
        "marker",
        "path",
        "line",
        "polyline",
        "polygon",
        "rect",
        "circle",
        "ellipse",
        "text",
        "tspan",
        "title",
        "desc",
    }
)

# Attributs autorises sur n'importe quel element de la liste ci-dessus.
ATTRIBUTS_AUTORISES = frozenset(
    {
        "class",
        "transform",
        "fill",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-dasharray",
        "marker-end",
        "marker-start",
        "text-anchor",
        "dominant-baseline",
        "font-size",
        "font-weight",
        "font-family",
        "font-style",
        "viewBox",
        "width",
        "height",
        "id",
        "x",
        "y",
        "x1",
        "y1",
        "x2",
        "y2",
        "cx",
        "cy",
        "r",
        "rx",
        "ry",
        "points",
        "d",
        "refX",
        "refY",
        "markerWidth",
        "markerHeight",
        "orient",
        "preserveAspectRatio",
        "role",
        "aria-label",
        "aria-hidden",
    }
)

_ATTRIBUT_INTERDIT_PREFIXE = "on"  # onload, onclick... jamais autorises, quel que soit l'element
_URL_LOCALE = re.compile(r"^url\(#[A-Za-z0-9_-]+\)$")
_MARQUEURS_DANGEREUX = ("<!DOCTYPE", "<!ENTITY")


class ErreurSvg(ValueError):
    """SVG refuse : le message dit pourquoi, en francais."""


def _nom_local(balise: str) -> str:
    """'{http://www.w3.org/2000/svg}rect' -> 'rect' ; 'rect' -> 'rect'."""
    return balise.rsplit("}", 1)[-1]


def _controler_valeur_attribut(nom: str, valeur: str, ou: str) -> None:
    if nom.lower().startswith(_ATTRIBUT_INTERDIT_PREFIXE):
        raise ErreurSvg(f"{ou} : attribut interdit {nom!r} (gestionnaire d'evenement)")
    if nom in ("href", "xlink:href") and not valeur.startswith("#"):
        raise ErreurSvg(f"{ou} : lien externe interdit ({nom}={valeur!r})")
    if nom == "style" and "url(" in valeur:
        raise ErreurSvg(f"{ou} : attribut style avec url() interdit")
    if nom in ("marker-end", "marker-start") and valeur and not _URL_LOCALE.match(valeur):
        raise ErreurSvg(f"{ou} : {nom} doit pointer vers une ancre locale (url(#id)), recu {valeur!r}")


def _nettoyer_element(element: ET.Element, ou: str) -> ET.Element:
    nom = _nom_local(element.tag)
    if nom not in ELEMENTS_AUTORISES:
        raise ErreurSvg(f"{ou} : element {nom!r} non autorise")
    propre = ET.Element(nom)
    for cle, valeur in element.attrib.items():
        nom_attr = _nom_local(cle)
        if nom_attr not in ATTRIBUTS_AUTORISES and cle not in ("href", "xlink:href"):
            raise ErreurSvg(f"{ou}, element {nom!r} : attribut {cle!r} non autorise")
        _controler_valeur_attribut(nom_attr, valeur, f"{ou}, element {nom!r}")
        propre.set(nom_attr, valeur)
    if element.text:
        propre.text = element.text
    for enfant in element:
        propre.append(_nettoyer_element(enfant, f"{ou} > {nom}"))
        # tail du dernier enfant ajoute conserve pour un rendu texte correct (ex. <text>a<tspan/>b</text>)
    for enfant_source, enfant_propre in zip(element, propre, strict=True):
        if enfant_source.tail:
            enfant_propre.tail = enfant_source.tail
    return propre


def nettoyer_svg(brut: str, ou: str = "svg") -> str:
    """Nettoie un SVG par liste blanche. Leve `ErreurSvg` si un element ou attribut est refuse.

    Rejette d'abord le fichier s'il contient un DOCTYPE ou une ENTITY (avant meme le parsing XML :
    la simple presence de ces mots dans le texte suffit a refuser, sans essayer de les interpreter).
    """
    for marqueur in _MARQUEURS_DANGEREUX:
        if marqueur in brut:
            raise ErreurSvg(f"{ou} : {marqueur} interdit dans un SVG")
    try:
        racine = ET.fromstring(brut)  # noqa: S314 - pas de resolveur d'entites externes dans ElementTree
    except ET.ParseError as err:
        raise ErreurSvg(f"{ou} : XML illisible ({err})") from err
    if _nom_local(racine.tag) != "svg":
        raise ErreurSvg(f"{ou} : la racine doit etre <svg>")
    propre = _nettoyer_element(racine, ou)
    # Le xmlns est indispensable au rendu cote navigateur (DOMParser en mode "image/svg+xml" a
    # besoin de cet espace de noms sur la racine, sinon les enfants ne sont pas reconnus comme des
    # elements SVG et le dessin ne s'affiche pas). ElementTree ne l'ecrit jamais lui-meme.
    propre.set("xmlns", NS_SVG)
    return ET.tostring(propre, encoding="unicode")
