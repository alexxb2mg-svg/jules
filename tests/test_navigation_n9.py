"""Navigation N9 : plus de `#rail` sur `/` (docs/spec/NAVIGATION.md, EX-216 (a), EX-209, EX-205, EX-210).

La colonne `#rail` d'`accueil.html` (« Notions avec une fiche ») et son bouton `#menu-rail` etaient une deuxieme
liste de notions a cote de la barre. Ils sont retires : la barre (etape 4 de Mes fiches) est le seul moyen
d'aller a une notion. Le fragment `#<id>` de notion ouvre toujours la fiche, sans le rail.

Mesures dans Chromium (banc de tests/nav_scenario.py, spec section 6) sur le jeu pire cas d'EX-212
(tests/test_navigation_n5.py : 16 matieres, 390 notions avec fiche), a 1280 x 800 et 390 x 844.
"""

from __future__ import annotations

import re
import shutil
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import STATIQUE, creer_app
from tests.conftest import regle_par_defaut
from tests.nav_scenario import banc_navigation
from tests.test_navigation import ATTENDRE_BARRE, RACINE
from tests.test_navigation_n5 import FICHES, generer_jeu

TAILLES = [(1280, 800), (390, 844)]
# Tout ce qui visait le rail : ids, selecteurs CSS, appels $("...") de accueil.js.
MOTIF_RAIL = re.compile(r'id="(menu-)?rail(-notions)?"|#(menu-)?rail\b|\.rail\b|\(\s*"(menu-)?rail(-notions)?"\s*\)')

# Releve avant la carte (base nav/integration-n3-n7 2a516f4, meme banc, meme jeu, chrome-headless-shell 1223,
# 27/09/2026) : plus grande hauteur de contenu (scrollHeight) d'un element hors barre sur /, fiche ouverte.
# C'etait la colonne #rail (390 boutons de notion + 16 intertitres).
HAUTEUR_AVANT = {1280: 52147, 390: 41239}


@pytest.fixture(scope="module")
def jeu(tmp_path_factory):
    projet = tmp_path_factory.mktemp("projet-n9")
    for dossier in ("persona", "consignes", "profils", "extensions"):
        shutil.copytree(RACINE / dossier, projet / dossier)
    generer_jeu(projet)
    brut = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))
    brut["llm"] = {"backend": "factice", "historique_max": 30}
    brut["modules"] = [
        {"id": "notions", "reglages": {"bibliotheques": ["ref-n5"], "detection": False}},
        {"id": "fiches_visuelles", "reglages": {"bibliotheques": ["fv-n5"]}},
        {"id": "cours", "reglages": {"bibliotheques": []}},
        {"id": "studio"},
    ]
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut, projet), llm=llm)
    try:
        yield tuteur
    finally:
        tuteur.fermer()


@pytest.fixture(scope="module")
def ids_notions(jeu) -> list[str]:
    reponse = TestClient(creer_app(jeu)).get(FICHES).json()
    return [n["id"] for m in reponse["matieres"] for n in m["notions"]]


@pytest.fixture(scope="module")
def banc_n9(jeu, tmp_path_factory):
    with banc_navigation(creer_app(jeu), tmp_path_factory.mktemp("chromium-n9")) as b:
        yield b


# Toute commande vers une notion : lien /#<id>, bouton ou element portant l'id de notion en data-*.
MESURER = r"""
  const ids = new Set(IDS);
  const barre = S.el("#barre-jules");
  const versNotion = (e) => {
    const href = e.getAttribute("href") || "";
    if (href.startsWith("/#") && ids.has(decodeURIComponent(href.slice(2)))) return true;
    return Object.values(e.dataset).some((v) => ids.has(v));
  };
  const visible = (e) => {
    const s = getComputedStyle(e);
    if (s.display === "none" || s.visibility === "hidden") return false;
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight;
  };
  const commandes = [...document.querySelectorAll("a, button, [data-id], [data-notion]")].filter(versNotion);
  let plusHaut = { hauteur: document.documentElement.scrollHeight, element: "html" };
  for (const e of document.body.querySelectorAll("*")) {
    if (barre.contains(e)) continue;
    if (e.scrollHeight > plusHaut.hauteur) {
      plusHaut = { hauteur: e.scrollHeight, element: e.id ? "#" + e.id : e.tagName.toLowerCase() + "." + e.className };
    }
  }
  return {
    rail: !!document.getElementById("rail"),
    menuRail: !!document.getElementById("menu-rail"),
    horsBarre: commandes.filter((e) => !barre.contains(e)).length,
    dansBarre: commandes.filter((e) => barre.contains(e)).length,
    // Boutons visibles dont le texte contient ☰ (« ☰ Notions » du rail compte, pas seulement un ☰ seul).
    hamburgers: [...document.querySelectorAll("button, a, [role=button]")].filter((e) => e.textContent.includes("☰")
      && visible(e)).map((e) => e.id || e.className),
    document: document.documentElement.scrollHeight,
    plusHaut,
    titre: S.el("#fiche-titre").textContent,
    api: S.api(),
  };
"""


def _mesurer(banc, ids: list[str], taille: tuple[int, int], fragment: str = "") -> dict[str, Any]:
    etapes = (
        ATTENDRE_BARRE
        + 'await S.attendre(() => !S.el("#fiche").classList.contains("cache"), 8000);'
        + "await S.pause(500);"
        + MESURER.replace("IDS", repr(ids).replace("'", '"'))
    )
    return banc.jouer("/" + fragment, etapes, taille=taille, budget_ms=10000)


def test_ex216a_temoin_mutation_une_liste_hors_barre_est_vue(banc_n9, ids_notions):
    """Mutation : accueil.js servi avec une 2e liste (boutons data-id hors barre) -> le scenario la compte."""
    texte = (STATIQUE / "accueil.js").read_text(encoding="utf-8")
    ajout = (
        '\nMS.api("/api/eleve/fiches_visuelles/notions").then((r) => { const z = document.createElement("div");'
        ' for (const m of r.matieres) for (const n of m.notions) { const b = document.createElement("button");'
        ' b.dataset.id = n.id; b.textContent = n.titre; z.appendChild(b); }'
        ' document.querySelector(".fiche-zone").appendChild(z); });\n'
    )
    etapes = (
        ATTENDRE_BARRE
        + 'await S.attendre(() => !S.el("#fiche").classList.contains("cache"), 8000);'
        + "await S.pause(500);"
        + MESURER.replace("IDS", repr(ids_notions).replace("'", '"'))
    )
    r = banc_n9.jouer("/", etapes, remplaces={"/static/accueil.js": texte + ajout}, budget_ms=10000)
    assert r["horsBarre"] == len(ids_notions), r["horsBarre"]


@pytest.mark.parametrize("taille", TAILLES, ids=lambda t: str(t[0]))
def test_ex216a_une_seule_liste_de_notions_sur_l_accueil(banc_n9, ids_notions, taille):
    """Sans fragment : premiere fiche ouverte, aucune commande vers une notion hors de la barre, plus de #rail,
    et l'element le plus haut hors barre est bien plus court que le releve d'avant la carte."""
    assert len(ids_notions) == 390  # le pire cas d'EX-212 est bien servi
    r = _mesurer(banc_n9, ids_notions, taille)
    print(f"\n{taille[0]} px : {r}")
    assert (r["rail"], r["menuRail"]) == (False, False), r
    assert r["horsBarre"] == 0, r
    assert r["titre"] == "Notion 1.1 de Allemand", r  # la premiere fiche s'ouvre toujours sans le rail
    # EX-207 / EX-216 (a) : un seul bouton ☰, celui du tiroir de la barre sous 900 px ; a 1280 la barre est
    # visible et son ☰ masque (test_ex207_un_seul_bouton_menu_par_page). Avant : « ☰ Notions » en plus a 390.
    assert r["hamburgers"] == (["barre-jules-bouton"] if taille[0] < 900 else []), r
    assert r["plusHaut"]["hauteur"] < HAUTEUR_AVANT[taille[0]], r
    # EX-210 : memes chemins qu'avant la carte (CHEMINS_AVANT de test_navigation.py, jeu n5)
    assert r["api"] == [
        "/api/session", "/api/infos", FICHES, FICHES + "/allemand-c1-n1",
    ], r  # fmt: skip


@pytest.mark.parametrize("taille", TAILLES, ids=lambda t: str(t[0]))
def test_ex209_fragment_de_notion_sans_rail(banc_n9, ids_notions, taille):
    """`/#<id>` ouvre la fiche et place la barre sur l'etape 4 de sa matiere : la barre est la seule liste."""
    cible = "francais-c7-n4"
    assert cible in ids_notions
    r = _mesurer(banc_n9, ids_notions, taille, fragment="#" + cible)
    print(f"\n{taille[0]} px #{cible} : {r}")
    assert (r["rail"], r["menuRail"], r["horsBarre"]) == (False, False, 0), r
    assert r["dansBarre"] == 10, r  # les 10 notions du chapitre 7 de Francais, dans la barre seulement
    assert r["titre"].startswith("Notion 7.4 Français"), r
    assert r["api"] == ["/api/session", "/api/infos", FICHES, FICHES + "/" + cible], r


def test_ex216a_plus_de_rail_dans_les_statiques():
    """Aucun id, selecteur ni appel vers #rail / #menu-rail / #rail-notions ne subsiste hors composant."""
    motif = MOTIF_RAIL
    for fichier in sorted([*STATIQUE.glob("*.html"), *STATIQUE.glob("*.css"), *STATIQUE.glob("*.js")]):
        trouve = [m.group(0) for m in motif.finditer(fichier.read_text(encoding="utf-8"))]
        assert not trouve, (fichier.name, trouve)


def test_ex216a_temoin_le_controle_statique_attrape_le_rail():
    motif = MOTIF_RAIL
    for texte in ('<aside id="rail">', ".rail { x }", '$("menu-rail")', "body.avec-barre .rail {", "#rail-notions"):
        assert motif.search(texte), texte
