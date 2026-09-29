"""Calculatrice de la nouvelle interface React (front/, composant Calculatrice.tsx) : test de bout en bout.

Pilote Chromium headless par le protocole de debogage (tests/cdp.py) sur un serveur reel de l'application,
code d'acces eleve actif. Verifie ce que l'eleve vit : bouton present seulement si l'outil est au catalogue,
contenu de l'outil visible (l'iframe a origine opaque n'envoie pas de cookie : ses fichiers sont servis sans),
touches de 44 px au moins, contenu de la page non recouvert sur grand ecran, Echap qui ferme et rend le focus.
Ignore si le navigateur ou l'interface construite (jules/web/static/app) est absent.
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
from tests.cdp import ErreurCdp, navigateur, navigateur_cdp
from tests.conftest import regle_par_defaut

CODE = "1234"
INTERFACE = Path(__file__).resolve().parents[1] / "jules" / "web" / "static" / "app" / "index.html"

BOUTON = "document.querySelector('button[aria-label=Calculatrice]')"
PANNEAU = "document.querySelector('[data-slot=popover-content],[data-slot=sheet-content]')"
CENTRE_BOUTON = f"(() => {{ const r = {BOUTON}.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }})()"
RECOUVERTS = f"""(() => {{
  const c = {PANNEAU}.getBoundingClientRect();
  const hors = (e) => !e.closest('[data-slot=popover-content],[data-slot=sheet-content]') && !e.closest('[aria-label=Calculatrice]')
    && !e.closest('[data-sidebar]');
  return [...document.querySelectorAll('h1,h2,h3,p,button,a,span')].filter(hors)
    .filter((e) => e.children.length === 0 && e.textContent.trim())
    .filter((e) => {{ const b = e.getBoundingClientRect();
      return b.width > 0 && b.height > 0 && b.right > c.left + 1 && b.left < c.right && b.bottom > c.top && b.top < c.bottom; }}).length;
}})()"""
TOUCHES = ("JSON.stringify({n: document.querySelectorAll('#pave button').length, "
           "min: Math.min(...[...document.querySelectorAll('#pave button')].map((b) => b.getBoundingClientRect().height))})")


@pytest.fixture
def serveur(projet, brut_config):
    if not INTERFACE.is_file():
        pytest.skip("interface React non construite (npm run build dans front/)")
    brut_config["acces"] = {"code_eleve": empreinte(CODE), "code_parent": empreinte("parent67")}
    brut_config["modules"] = [*brut_config["modules"], {"id": "outils", "actif": True}]
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    serveur = uvicorn.Server(uvicorn.Config(creer_app(tuteur), host="127.0.0.1", port=port, log_level="error"))
    fil = threading.Thread(target=serveur.run, daemon=True)
    fil.start()
    limite = time.monotonic() + 15
    while not serveur.started and time.monotonic() < limite:
        time.sleep(0.05)
    assert serveur.started, "serveur de test non demarre"
    yield f"http://127.0.0.1:{port}"
    serveur.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


def _ouvrir(page, url: str) -> None:
    page.commande("Page.navigate", url=url + "/static/favicon.ico")
    time.sleep(0.5)
    page.evaluer(
        "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
    )
    time.sleep(0.5)
    page.commande("Page.navigate", url=url + "/app#/lecons")
    page.attendre(f"!!{BOUTON}", delai=15)
    page.cliquer(*page.evaluer(CENTRE_BOUTON))
    page.attendre(f"!!{PANNEAU}", delai=10)


CLAVIER = "!document.body.hidden && document.querySelectorAll('#pave button').length > 0"


def _candidats(page) -> list[tuple[str | None, int | None]]:
    """Ou peut se trouver le document de l'outil : une session d'iframe hors processus (Chrome en cree une selon son
    isolation de sites), ou un contexte d'execution dans la page. On les essaie tous : lequel existe varie d'un lancement."""
    sessions = [(ss, None) for ss in page.sessions_iframes()]
    # Le contexte de l'outil est le contexte par defaut de SON cadre : on ecarte ceux du cadre principal (page), pas
    # tous les contextes « default » (Chrome marque aussi ainsi celui de l'iframe).
    tous = page.contextes()
    principal = page.commande("Page.getFrameTree")["frameTree"]["frame"]["id"]
    contextes = [(None, int(c["id"])) for c in tous if c.get("auxData", {}).get("frameId") != principal]
    return sessions + contextes


def _pret_outil(page) -> tuple[str | None, int | None]:
    limite = time.monotonic() + 15
    while time.monotonic() < limite:
        page.evaluer("1")  # le pilote ne recoit les evenements de Chrome (sessions, contextes) qu'en envoyant une commande
        for session, contexte in _candidats(page):
            try:
                if page.evaluer(CLAVIER, session=session, contexte=contexte):
                    return session, contexte
            except ErreurCdp:
                continue
        time.sleep(0.1)
    raise AssertionError(f"outil calculatrice non affiche (candidats : {_candidats(page)})")


@pytest.mark.parametrize(("taille", "nom"), [((1280, 800), "bureau"), ((390, 800), "mobile")])
def test_calculatrice_react(serveur, tmp_path_factory, taille, nom):
    dossier = tmp_path_factory.mktemp(f"chromium-calc-react-{nom}")
    with navigateur_cdp(navigateur(), dossier, taille) as page:
        _ouvrir(page, serveur)
        session, contexte = _pret_outil(page)
        import json

        touches = json.loads(page.evaluer(TOUCHES, session=session, contexte=contexte))
        assert touches["n"] == 32  # le clavier est bien la, pas un panneau vide
        assert touches["min"] >= 44  # cible tactile
        assert page.evaluer(f"{PANNEAU}.querySelector('iframe').sandbox + ''") == "allow-scripts"  # jamais allow-same-origin
        if nom == "bureau":  # panneau flottant : la page pousse son contenu (animation) puis rien n'est recouvert
            page.attendre(f"({RECOUVERTS}) === 0", delai=5)
        page.touche("Escape", "Escape", 27)
        page.attendre(f"!{PANNEAU}", delai=5)
        # focus rendu au bouton (Radix le rend apres la fin de l'animation de fermeture)
        page.attendre("document.activeElement.getAttribute('aria-label') === 'Calculatrice'", delai=5)
