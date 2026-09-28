"""Banc de test navigateur par scenario (tests/nav_scenario.py, docs/spec/NAVIGATION.md section 6).

Test temoin sur les pages actuelles, API simulee, et comportement sans Chromium
(JULES_CHROMIUM_OBLIGATOIRE=1 : echec, pas de skip).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
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
  // Fin du demarrage de / = premiere fiche affichee. Le titre et la barre sont poses des /api/infos, AVANT le
  // chargement des notions puis l'ouverture de la fiche (accueil.js, demarrage) : attendre seulement le titre
  // laissait le test lire S.api() avant l'appel /notions/<id> (course, echec intermittent sous Linux).
  await S.attendre(() => document.title === "Jules - Mes fiches" && document.getElementById("barre-jules-bouton")
    && !document.getElementById("fiche").classList.contains("cache"));
  const avant = { aria: S.aria("#barre-jules-bouton"), titre: S.titre() };
  S.focus("#barre-jules button");
  const actif = S.actif();
  S.clic("#avatar-jules");
  const chatOuvert = S.el("#chat-flottant").classList.contains("ouvert");
  S.echap();
  localStorage.setItem("essai-banc", "1");
  return {
    titre: avant.titre,
    aria: avant.aria,
    actif: actif,
    chatOuvert: chatOuvert,
    style: S.style("#chat-flottant", ["display"]),
    rect: S.rect("#chat-flottant"),
    stockage: S.stockage(),
    api: S.api(),
    appels: S.appels(),
    scriptsAvantLaPage: [...document.scripts].map((s) => s.getAttribute("src")).slice(0, 2),
  };
"""


# Carte N9 (EX-216) : le #rail de / est retire ; le temoin vise desormais le bouton ☰ de la barre, un bouton
# de rubrique de la barre et le bouton J (meme couverture du banc : aria, focus, clic, Echap, style, rect).
def test_nav_scenario_temoin_sur_la_page_d_accueil(banc):
    r = banc.jouer("/", TEMOIN, taille=(1280, 800))
    assert r["titre"] == "Jules - Mes fiches"
    assert r["aria"]["aria-controls"] == "barre-jules" and r["aria"]["aria-expanded"] == "false", r["aria"]
    assert r["actif"]["balise"] == "button" and r["actif"]["texte"]  # focus() sur un bouton de la barre
    assert r["chatOuvert"] is True  # element.click() declenche bien l'ecouteur de la page
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
    # Carte N9 (EX-216) : plus de #rail sur / ; le jeu simule se lit dans la barre (etape 4 de la matiere de la
    # notion du fragment), seule liste de notions de la page.
    etapes = """
      await S.attendre(() => document.querySelectorAll("#barre-jules a.barre-element").length === 4);
      return {
        titre: S.el("#barre-page-titre").textContent,
        liens: [...document.querySelectorAll("#barre-jules a.barre-element")].map((a) => a.getAttribute("href")),
        api: S.api(),
      };
    """
    r = banc.jouer("/#m2-n3", etapes, simulees={"/api/eleve/fiches_visuelles/notions": _notions_generees(3, 4)})
    assert r["liens"] == ["/#m2-n0", "/#m2-n1", "/#m2-n2", "/#m2-n3"], r
    assert "/api/eleve/fiches_visuelles/notions/m2-n3" in r["api"], r


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


NAVIGATEUR_BLOQUE = """
import subprocess, sys, time
enfant = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
open(sys.argv[1], "w").write(str(enfant.pid))
time.sleep(600)
"""


def _vivant(pid: int) -> bool:
    """Le processus `pid` tourne-t-il encore (un zombie compte comme mort) ?"""
    if sys.platform == "win32":
        import ctypes

        noyau = ctypes.windll.kernel32
        poignee = noyau.OpenProcess(0x00100000 | 0x1000, False, pid)  # SYNCHRONIZE | QUERY_LIMITED_INFORMATION
        if not poignee:
            return False
        try:
            return bool(noyau.WaitForSingleObject(poignee, 0) == 0x102)  # WAIT_TIMEOUT : toujours en vie
        finally:
            noyau.CloseHandle(poignee)
    etat = Path(f"/proc/{pid}/stat")
    if etat.exists():
        try:
            return etat.read_text().rsplit(")", 1)[1].split()[0] != "Z"
        except (ProcessLookupError, FileNotFoundError):
            return False  # le processus a disparu entre exists() et read_text() (course vue en CI)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_nav_scenario_page_qui_ne_repond_jamais_echoue_dans_le_delai_et_ferme_tout(tmp_path):
    """CI-3 : un « navigateur » qui ne rend jamais rien (et lance un enfant, comme le zygote de Chromium)
    est arrete au bout du delai, lui ET son enfant, au lieu de bloquer le job jusqu'a l'annulation."""
    script, fichier_pid = tmp_path / "bloque.py", tmp_path / "enfant.pid"
    script.write_text(NAVIGATEUR_BLOQUE, encoding="utf-8")
    debut = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        nav_scenario.executer_navigateur([sys.executable, str(script), str(fichier_pid)], 3)
    assert time.monotonic() - debut < 20
    enfant = int(fichier_pid.read_text())
    limite = time.monotonic() + 10
    while _vivant(enfant) and time.monotonic() < limite:
        time.sleep(0.1)
    assert not _vivant(enfant), "l'enfant du navigateur survit a l'echec : processus orphelin"


def test_nav_scenario_navigateur_bloque_echoue_vite_et_une_fois(monkeypatch, tmp_path):
    """Un navigateur qui ne rend rien (cas de /usr/bin/chromium en CI Linux) : le premier scenario echoue au
    bout du delai borne avec un message lisible, les suivants echouent sans relancer le navigateur."""
    appels = []
    reel = nav_scenario.executer_navigateur

    def bloque(commande, delai):
        appels.append(delai)
        return reel([sys.executable, "-c", "import time; time.sleep(600)"], 2)

    monkeypatch.setattr(nav_scenario, "executer_navigateur", bloque)
    b = nav_scenario.Banc(
        nav_scenario.EnveloppeTest(lambda *a: None), "http://127.0.0.1:1", "chromium-bloque", tmp_path
    )
    debut = time.monotonic()
    with pytest.raises(ErreurScenario, match=r"n'a rien rendu en 53 s sur /cours .*chrome-headless-shell"):
        b.jouer("/cours", "return 1;", budget_ms=8000)
    with pytest.raises(ErreurScenario, match="scenario non joue sur /studio"):
        b.jouer("/studio", "return 1;")
    assert appels == [nav_scenario.DELAI_FIXE_S + 8]
    assert time.monotonic() - debut < 20
