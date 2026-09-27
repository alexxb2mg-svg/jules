"""Banc de test navigateur par scenario (tests/nav_scenario.py, docs/spec/NAVIGATION.md section 6).

Test temoin sur les pages actuelles, API simulee, et comportement sans Chromium
(JULES_CHROMIUM_OBLIGATOIRE=1 : echec, pas de skip).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import STATIQUE, creer_app
from tests import nav_scenario
from tests.conftest import regle_par_defaut
from tests.nav_scenario import BALISE_SCENARIO, ErreurScenario, banc_navigation


@pytest.fixture(scope="module")
def banc(tmp_path_factory):
    """Un tuteur sans code d'acces (moteur factice), servi une fois pour tout le module."""
    import shutil

    import yaml

    racine = Path(__file__).resolve().parents[1]
    projet = tmp_path_factory.mktemp("projet-nav")
    for dossier in ("persona", "consignes", "profils", "bibliotheque", "extensions"):
        shutil.copytree(racine / dossier, projet / dossier)
    brut = yaml.safe_load((racine / "config.yaml").read_text(encoding="utf-8"))
    brut["llm"] = {"backend": "factice", "historique_max": 30}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut, projet), llm=llm)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium")) as b:
            yield b
    finally:
        tuteur.fermer()


# --- test temoin : la page / telle qu'elle est ----------------------------------------------------

TEMOIN = """
  await S.attendre(() => document.title === "Jules - Mes fiches" && document.querySelector("#rail-notions button"));
  const avant = { aria: S.aria("#menu-rail"), titre: S.titre() };
  S.focus("#rail-notions button");
  const actif = S.actif();
  S.clic("#menu-rail");
  const railOuvert = S.el("#rail").classList.contains("ouvert");
  S.echap();
  localStorage.setItem("essai-banc", "1");
  return {
    titre: avant.titre,
    aria: avant.aria,
    actif: actif,
    railOuvert: railOuvert,
    style: S.style("#rail", ["display"]),
    rect: S.rect("#rail"),
    stockage: S.stockage(),
    api: S.api(),
    appels: S.appels(),
    scriptsAvantLaPage: [...document.scripts].map((s) => s.getAttribute("src")).slice(0, 2),
  };
"""


def test_nav_scenario_temoin_sur_la_page_d_accueil(banc):
    r = banc.jouer("/", TEMOIN, taille=(1280, 800))
    assert r["titre"] == "Jules - Mes fiches"
    assert r["aria"] == {"aria-label": "Ouvrir la liste des notions", "aria-expanded": "false", "aria-controls": "rail"}
    assert r["actif"]["balise"] == "button" and r["actif"]["texte"]  # focus() sur un bouton de notion du rail
    assert r["railOuvert"] is True  # element.click() declenche bien l'ecouteur de la page
    assert r["style"]["display"] not in ("", None)
    assert r["rect"]["largeur"] > 0 and r["rect"]["hauteur"] > 0
    assert r["stockage"] == {"essai-banc": "1"}
    # fetch enveloppe avant les scripts de la page : les premiers appels du demarrage sont vus, dans l'ordre
    assert r["api"][:3] == ["/api/session", "/api/infos", "/api/eleve/fiches_visuelles/notions"]
    assert any(p.startswith("/api/eleve/fiches_visuelles/notions/") for p in r["api"])  # premiere fiche ouverte
    assert {"methode": "GET", "chemin": "/api/session"} in r["appels"]
    assert r["scriptsAvantLaPage"][0] == nav_scenario.CHEMIN_SCENARIO


def test_nav_scenario_taille_de_fenetre_reglable(banc):
    etapes = "return { largeur: innerWidth, hauteur: innerHeight };"
    assert banc.jouer("/", etapes, taille=(390, 844)) == {"largeur": 390, "hauteur": 844}
    assert banc.jouer("/", etapes, taille=(1024, 700)) == {"largeur": 1024, "hauteur": 700}


# --- API simulee par le test -----------------------------------------------------------------------


def _notions_generees(n_matieres: int, n_notions: int) -> dict:
    return {
        "matieres": [
            {
                "id": f"matiere-{m}",
                "nom": f"Matiere {m}",
                "notions": [
                    {"id": f"m{m}-n{k}", "titre": f"Notion {m}.{k}", "chapitre": "c"} for k in range(n_notions)
                ],
            }
            for m in range(n_matieres)
        ]
    }


def test_nav_scenario_session_simulee_ferme_la_porte(banc):
    etapes = """
      await S.attendre(() => !S.el("#porte").classList.contains("cache"));
      return { porte: !S.el("#porte").classList.contains("cache"), actif: S.actif().id, api: S.api() };
    """
    r = banc.jouer("/", etapes, simulees={"/api/session": {"role": None, "eleve": False, "parent": False}})
    assert r == {"porte": True, "actif": "porte-code", "api": ["/api/session"]}


def test_nav_scenario_jeu_de_notions_genere_par_le_test(banc):
    etapes = """
      await S.attendre(() => document.querySelectorAll("#rail-notions button").length === 12);
      return {
        matieres: [...document.querySelectorAll("#rail-notions h4")].map((h) => h.textContent),
        boutons: document.querySelectorAll("#rail-notions button").length,
      };
    """
    r = banc.jouer("/", etapes, simulees={"/api/eleve/fiches_visuelles/notions": _notions_generees(3, 4)})
    assert r == {"matieres": ["Matiere 0", "Matiere 1", "Matiere 2"], "boutons": 12}


def test_nav_scenario_avant_s_execute_avant_la_page(banc):
    r = banc.jouer("/", "return S.stockage();", avant='localStorage.setItem("pose-avant", "oui");')
    assert r == {"pose-avant": "oui"}


def test_nav_scenario_une_erreur_js_est_remontee(banc):
    with pytest.raises(ErreurScenario, match="element introuvable : #n-existe-pas"):
        banc.jouer("/", 'S.clic("#n-existe-pas");')


# --- le HTML de production n'est pas modifie --------------------------------------------------------


def test_nav_scenario_rien_dans_le_html_de_production():
    for page in STATIQUE.glob("*.html"):
        texte = page.read_text(encoding="utf-8")
        assert "_test" not in texte and "resultat-scenario" not in texte, page.name
    assert BALISE_SCENARIO.startswith('<script src="/_test/')


# --- sans Chromium ------------------------------------------------------------------------------------


def test_nav_scenario_sans_chromium_echoue_si_obligatoire(monkeypatch):
    monkeypatch.setattr(nav_scenario, "_chromium", lambda: None)
    monkeypatch.setenv(nav_scenario.VARIABLE_OBLIGATOIRE, "1")
    with pytest.raises(pytest.fail.Exception, match="ne peut pas etre ignore"):
        nav_scenario.navigateur()


def test_nav_scenario_sans_chromium_saute_sinon(monkeypatch):
    monkeypatch.setattr(nav_scenario, "_chromium", lambda: None)
    monkeypatch.delenv(nav_scenario.VARIABLE_OBLIGATOIRE, raising=False)
    with pytest.raises(pytest.skip.Exception, match="Chromium absent"):
        nav_scenario.navigateur()
