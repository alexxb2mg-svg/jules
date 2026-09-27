"""Navigation N8 : plus aucune navigation en double (docs/spec/NAVIGATION.md, EX-216).

- (a) sur /, plus de `#rail` ni de `#menu-rail` : la liste des notions est celle de la barre (Mes fiches) ;
- (b) (c) sur /cours et /studio, la barre et la zone centrale affichent toujours la meme matiere, sans rechargement
  et sans appel de plus (cache EX-210), l'adresse passe a `?matiere=<id>` ;
- (d) les intertitres de chapitre de la barre (etape 4 de Mes lecons et d'Exercices) ne sont pas tronques (ni
  `line-clamp`, ni ellipse).
La verification (e) (budget EX-212) est celle de tests/test_navigation_n5.py, relancee telle quelle.

Scenarios Chromium sur le banc de tests/nav_scenario.py (spec section 6), a 1280 x 800 et 390 x 844, donnees du
depot (`bibliotheque/`).
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from jules.web.app import STATIQUE, creer_app
from tests.nav_scenario import banc_navigation
from tests.test_navigation import _tuteur
from tests.test_navigation_n4 import DEBUT, PARCOURS, STUDIO, memoire
from tests.test_navigation_n7 import _regles

TAILLES = [(1280, 800), (390, 844)]
IDS_TAILLES = [f"{t[0]}x{t[1]}" for t in TAILLES]
NAVIGATION_CSS = STATIQUE / "navigation.css"


@pytest.fixture(scope="module")
def tuteur_n8(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory, None)
    yield tuteur
    tuteur.fermer()


@pytest.fixture(scope="module")
def banc(tuteur_n8, tmp_path_factory):
    with banc_navigation(creer_app(tuteur_n8), tmp_path_factory.mktemp("chromium-n8")) as b:
        yield b


@pytest.fixture(scope="module")
def noms(tuteur_n8) -> dict[str, dict[str, Any]]:
    """Faits du jeu du depot relus dans l'API : noms des matieres et titres des notions par matiere."""
    from fastapi.testclient import TestClient

    client = TestClient(creer_app(tuteur_n8))
    faits: dict[str, dict[str, Any]] = {}
    for chemin in (PARCOURS, STUDIO):
        base = client.get(chemin).json()
        par = {m["id"]: client.get(chemin, params={"matiere": m["id"]}).json() for m in base["matieres"]}
        faits[chemin] = {
            "noms": {m["id"]: m["nom"] for m in base["matieres"]},
            "notions": {mid: [n["id"] for n in r["notions"]] for mid, r in par.items()},
        }
    for chemin in (PARCOURS, STUDIO):
        assert {"histoire", "mathematiques"} <= set(faits[chemin]["noms"])
        assert faits[chemin]["notions"]["histoire"] and faits[chemin]["notions"]["mathematiques"]
        assert set(faits[chemin]["notions"]["histoire"]).isdisjoint(faits[chemin]["notions"]["mathematiques"])
    return faits


def jouer(banc, chemin: str, etapes: str, **options: Any) -> Any:
    options.setdefault("budget_ms", 12000)
    return banc.jouer(chemin, DEBUT + etapes, **options)


# Sous 900 px la barre est un tiroir : on l'ouvre par son bouton avant d'y cliquer.
OUVRIR_TIROIR = r"""
  const ouvrirTiroir = async () => {
    const b = document.getElementById("barre-jules-bouton");
    if (b && getComputedStyle(b).display !== "none" && b.getAttribute("aria-expanded") !== "true") {
      b.click();
      await S.pause(250);
    }
  };
"""


# --- (a) : / sans rail ni second bouton de menu -----------------------------------------------------------

UN_SEUL_MENU = r"""
  await S.attendre(() => !S.el("#fiche").classList.contains("cache"), 8000);
  await S.pause(200);
  const visible = (e) => {
    const s = getComputedStyle(e);
    if (s.display === "none" || s.visibility === "hidden") return false;
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight;
  };
  const avecMenu = [...document.body.querySelectorAll("button, a, [role=button]")]
    .filter((e) => e.textContent.includes("☰"));
  return {
    rail: !!document.getElementById("rail"), menuRail: !!document.getElementById("menu-rail"),
    railNotions: !!document.getElementById("rail-notions"),
    boutonsMenu: avecMenu.map((e) => e.id), visibles: avecMenu.filter(visible).map((e) => e.id),
    aside: [...document.querySelectorAll("aside")].map((a) => a.getAttribute("aria-label")),
    fiche: S.el("#fiche-titre").textContent, api: S.api(), erreurs: S.erreurs(),
  };
"""


@pytest.mark.parametrize("taille", TAILLES, ids=IDS_TAILLES)
def test_ex216a_accueil_sans_rail_ni_second_menu(banc, taille):
    r = jouer(banc, "/", UN_SEUL_MENU, taille=taille, avant=memoire(None))
    assert (r["rail"], r["menuRail"], r["railNotions"]) == (False, False, False)
    assert "Notions avec une fiche" not in r["aside"]
    assert r["boutonsMenu"] == ["barre-jules-bouton"], r  # exactement un ☰ dans le DOM : celui de la barre
    # visible en tiroir seulement (EX-207 : a partir de 900 px la barre est toujours la, sans bouton)
    assert r["visibles"] == (["barre-jules-bouton"] if taille[0] < 900 else [])
    # la page ouvre toujours une fiche (la premiere), avec la meme liste que la barre (un seul appel)
    assert r["fiche"]
    assert r["api"].count("/api/eleve/fiches_visuelles/notions") == 1
    assert r["erreurs"] == []


def test_ex216a_accueil_html_sans_rail():
    texte = (STATIQUE / "accueil.html").read_text(encoding="utf-8")
    assert 'id="rail"' not in texte and 'id="menu-rail"' not in texte and "rail-notions" not in texte
    js = (STATIQUE / "accueil.js").read_text(encoding="utf-8")
    assert '"rail' not in js and '"menu-rail"' not in js
    css = (STATIQUE / "accueil.css").read_text(encoding="utf-8")
    assert not re.search(r"\.rail\b|#rail\b|\.bouton-panneau", re.sub(r"/\*.*?\*/", "", css, flags=re.S))


def test_ex216a_lien_de_la_barre_ouvre_la_fiche_sans_rail(banc):
    """Le rail retire, c'est l'etape 4 de Mes fiches qui ouvre une autre fiche (lien /#<id>, sans rechargement)."""
    r = jouer(
        banc,
        "/",
        r"""
        await S.attendre(() => !S.el("#fiche").classList.contains("cache"), 8000);
        const premiere = S.el("#fiche-titre").textContent;
        rubrique("fiches").click();
        await S.attendre(() => lirePage().etape >= 2, 5000);
        if (lirePage().etape === 2) {
          matiere("mathematiques").click();
          await S.attendre(() => lirePage().etape >= 3, 5000);
        }
        if (lirePage().etape === 3) {
          // le chapitre qui a le plus de fiches : il en faut une autre que celle deja ouverte
          const chapitres = [...document.querySelectorAll("#barre-jules [data-chapitre]")];
          const effectif = (b) => Number(b.querySelector(".barre-effectif").textContent);
          chapitres.sort((a, b) => effectif(b) - effectif(a))[0].click();
          await attendreEtape(4);
        }
        const liens = [...document.querySelectorAll("#barre-jules a.barre-element")];
        const cible = liens.find((a) => a.getAttribute("aria-current") !== "true") || liens[0];
        const href = cible.getAttribute("href");
        cible.click();
        await S.attendre(() => location.hash === href.slice(1) && S.el("#fiche-titre").textContent !== "", 5000);
        await S.pause(300);
        return { premiere, href, hash: location.hash, titre: S.el("#fiche-titre").textContent,
                 api: S.api(), nbLiens: liens.length };
        """,
        avant=memoire(None),
    )
    assert r["nbLiens"] >= 2, r
    assert r["hash"] == r["href"][1:]
    assert r["titre"] != r["premiere"]
    assert r["api"].count("/api/session") == 1  # pas de rechargement


# --- (b) : choix dans la barre -> la zone centrale suit ---------------------------------------------------

BARRE_VERS_CENTRE = (
    OUVRIR_TIROIR
    + r"""
  await S.attendre(() => !S.el("#choix-matiere").classList.contains("cache"), 8000);
  const sessions = () => S.api().filter((c) => c === "/api/session").length;
  await ouvrirTiroir();
  rubrique(RUBRIQUE).click();
  await attendreEtape(2);
  matiere("histoire").click();
  await attendreEtape(4);
  await S.attendre(() => S.el("#catalogue-titre").textContent.includes(":"), 5000);
  await S.pause(300);
  return {
    titre: S.el("#catalogue-titre").textContent,
    ids: [...document.querySelectorAll(ELEMENTS)].map((e) => e.dataset.id),
    choixCache: S.el("#choix-matiere").classList.contains("cache"),
    search: location.search, hash: location.hash, barre: lirePage(),
    requetes: S.requetes(), sessions: sessions(), stockage: S.stockage(), erreurs: S.erreurs(),
  };
"""
)


@pytest.mark.parametrize("taille", TAILLES, ids=IDS_TAILLES)
@pytest.mark.parametrize(
    ("page", "chemin", "rubrique", "elements"),
    [
        ("/cours", PARCOURS, "lecons", "#parcours-liste .notion-ligne"),
        ("/studio", STUDIO, "supports", "#notions-liste .notion-bloc"),
    ],
)
def test_ex216b_matiere_choisie_dans_la_barre_la_zone_centrale_suit(
    banc, noms, page, chemin, rubrique, elements, taille
):
    etapes = BARRE_VERS_CENTRE.replace("RUBRIQUE", json.dumps(rubrique)).replace("ELEMENTS", json.dumps(elements))
    r = jouer(banc, page, etapes, taille=taille, avant=memoire(None))
    nom = noms[chemin]["noms"]["histoire"]
    assert r["titre"].endswith(": " + nom), r["titre"]
    assert r["choixCache"] is True
    attendues = noms[chemin]["notions"]["histoire"]
    if chemin == STUDIO:  # le studio ne liste que les notions qui ont une lecon
        assert r["ids"] and set(r["ids"]) <= set(attendues)
    else:
        assert r["ids"] == attendues
    assert r["search"] == "?matiere=histoire"
    assert r["hash"] == f"#nav={rubrique}/histoire"
    assert (r["barre"]["etape"], r["barre"]["titre"]) == (4, nom)
    assert r["requetes"].count(chemin + "?matiere=histoire") == 1  # barre et page : un seul appel (EX-210)
    assert [q for q in r["requetes"] if q.startswith(chemin)] == [chemin, chemin + "?matiere=histoire"]
    assert r["sessions"] == 1  # sans rechargement
    assert r["stockage"] == {"jules.matiere": "histoire"}
    assert r["erreurs"] == []


def test_ex216b_changer_de_matiere_dans_la_barre_ferme_la_lecon_ouverte(banc, noms):
    """Lecon de Mathematiques ouverte, Histoire choisie dans la barre : la lecon se ferme, le centre liste
    Histoire. Jamais deux matieres differentes a l'ecran."""
    r = jouer(
        banc,
        "/cours?matiere=mathematiques&notion=thales-triangles-semblables-trigonometrie",
        r"""
        await S.attendre(() => !S.el("#lecon").classList.contains("cache"), 8000);
        const lecon = S.el("#lecon-titre").textContent;
        rubrique("lecons").click();
        await attendreEtape(4);
        retour().click();
        await attendreEtape(2);
        matiere("histoire").click();
        await attendreEtape(4);
        await S.attendre(() => S.el("#catalogue-titre").textContent.includes("Histoire"), 5000);
        await S.pause(200);
        return { lecon, leconCachee: S.el("#lecon").classList.contains("cache"),
                 catalogueVisible: !S.el("#catalogue").classList.contains("cache"),
                 titre: S.el("#catalogue-titre").textContent, search: location.search, barre: lirePage(),
                 erreurs: S.erreurs() };
        """,
        avant=memoire(None),
    )
    assert r["lecon"]
    assert r["leconCachee"] is True and r["catalogueVisible"] is True
    assert r["titre"].endswith(": " + noms[PARCOURS]["noms"]["histoire"])
    assert r["search"] == "?matiere=histoire"  # la notion de l'ancienne matiere ne reste pas dans l'adresse
    assert r["barre"]["titre"] == noms[PARCOURS]["noms"]["histoire"]
    assert r["erreurs"] == []


def test_ex216b_rubrique_d_une_autre_page_ne_touche_pas_la_zone_centrale(banc):
    """Sur /cours, choisir une matiere dans Exercices et supports ne change ni l'adresse ni la liste des lecons."""
    r = jouer(
        banc,
        "/cours",
        r"""
        await S.attendre(() => S.el("#catalogue-titre").textContent.includes(":"), 8000);
        const avant = S.el("#catalogue-titre").textContent;
        rubrique("supports").click();
        await attendreEtape(4);
        retour().click();
        await attendreEtape(2);
        matiere("histoire").click();
        await attendreEtape(4);
        await S.pause(300);
        return { avant, apres: S.el("#catalogue-titre").textContent, search: location.search,
                 requetes: S.requetes() };
        """,
        avant=memoire("mathematiques"),
    )
    assert r["apres"] == r["avant"]
    assert r["search"] == ""
    assert PARCOURS + "?matiere=histoire" not in r["requetes"]


# --- (c) : choix au centre -> la barre suit ---------------------------------------------------------------

CENTRE_VERS_BARRE = (
    OUVRIR_TIROIR
    + r"""
  await S.attendre(() => !S.el("#choix-matiere").classList.contains("cache"), 8000);
  S.el('.choix-matiere-bouton[data-matiere="mathematiques"]').click();
  await S.attendre(() => lirePage().etape === 4 && S.el("#catalogue-titre").textContent.includes(":"), 5000);
  await S.pause(300);
  const apresCentre = { barre: lirePage(), titre: S.el("#catalogue-titre").textContent, search: location.search,
                        hash: location.hash, actif: S.actif().id };
  // Puis un choix dans la barre : le centre suit a son tour (symetrie) ; jamais deux matieres a l'ecran.
  await ouvrirTiroir();
  retour().click();
  await attendreEtape(2);
  matiere("histoire").click();
  await S.attendre(() => lirePage().titre !== apresCentre.barre.titre && lirePage().etape === 4, 5000);
  await S.attendre(() => S.el("#catalogue-titre").textContent !== apresCentre.titre, 5000);
  await S.pause(200);
  return { apresCentre, apresBarre: { barre: lirePage(), titre: S.el("#catalogue-titre").textContent,
                                      search: location.search },
           requetes: S.requetes(), erreurs: S.erreurs() };
"""
)


@pytest.mark.parametrize("taille", TAILLES, ids=IDS_TAILLES)
@pytest.mark.parametrize(
    ("page", "chemin", "rubrique"), [("/cours", PARCOURS, "lecons"), ("/studio", STUDIO, "supports")]
)
def test_ex216c_matiere_choisie_au_centre_la_barre_suit(banc, noms, page, chemin, rubrique, taille):
    r = jouer(banc, page, CENTRE_VERS_BARRE, taille=taille, avant=memoire(None))
    maths, histoire = noms[chemin]["noms"]["mathematiques"], noms[chemin]["noms"]["histoire"]
    c = r["apresCentre"]
    assert (c["barre"]["etape"], c["barre"]["rubrique"], c["barre"]["titre"]) == (4, rubrique, maths)
    assert c["titre"].endswith(": " + maths)
    assert c["search"] == "?matiere=mathematiques"
    assert c["hash"] == f"#nav={rubrique}/mathematiques"
    assert c["actif"] == "catalogue-titre"  # le focus reste dans la page (EX-209 j)
    b = r["apresBarre"]
    assert b["barre"]["titre"] == histoire and b["titre"].endswith(": " + histoire)
    assert b["search"] == "?matiere=histoire"
    assert r["requetes"].count(chemin + "?matiere=mathematiques") == 1
    assert r["requetes"].count(chemin + "?matiere=histoire") == 1
    assert r["erreurs"] == []


# --- (d) : intertitres de chapitre complets ---------------------------------------------------------------

TRONQUE = re.compile(r"line-clamp|text-overflow\s*:\s*ellipsis")


def _vise_un_intertitre(selecteur: str) -> bool:
    """Le selecteur atteint le libelle d'un intertitre : il le nomme, ou vise `.barre-libelle` a travers les seuls
    conteneurs de la petite page (ex. `.barre-page .barre-libelle`), sans preciser le type d'entree."""
    s = re.sub(r"\s+", " ", selecteur.strip())
    conteneurs = r"(body|\.barre-jules|#barre-jules|\.barre-sous-page|\.barre-page|\.barre-liste|\.barre-groupe)"
    return "barre-intertitre" in s or re.fullmatch(rf"({conteneurs} )*\.barre-libelle", s) is not None


def test_ex216d_aucune_troncature_sur_les_intertitres_de_chapitre():
    regles = _regles(NAVIGATION_CSS.read_text(encoding="utf-8"))
    fautives = [s for s, corps in regles if TRONQUE.search(corps) and any(_vise_un_intertitre(x) for x in s.split(","))]
    assert fautives == [], fautives
    # le detecteur lui-meme : l'ancienne regle (N7) et une regle generique seraient reperees
    assert _vise_un_intertitre(".barre-intertitre .barre-libelle")
    assert _vise_un_intertitre(".barre-page .barre-libelle")
    assert not _vise_un_intertitre(".barre-page .barre-entree .barre-libelle")


def test_ex216d_intertitres_affiches_en_entier_dans_le_navigateur(banc):
    """Mes lecons, Francais (chapitres longs du depot) : aucun libelle de chapitre coupe a l'affichage."""
    r = jouer(
        banc,
        "/cours",
        r"""
        rubrique("lecons").click();
        await attendreEtape(4);
        await S.pause(200);
        const libelles = [...document.querySelectorAll("#barre-jules .barre-intertitre .barre-libelle")];
        return libelles.map((e) => ({ texte: e.textContent, clamp: getComputedStyle(e).webkitLineClamp,
                                      ellipse: getComputedStyle(e).textOverflow,
                                      coupe: e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1,
                                      lignes: Math.round(e.getBoundingClientRect().height /
                                                         parseFloat(getComputedStyle(e).lineHeight || "16")) }));
        """,
        avant=memoire("francais"),
    )
    assert r, "aucun intertitre"
    assert max(len(x["texte"]) for x in r) > 60  # des titres assez longs pour avoir ete coupes avant N8
    for x in r:
        assert x["clamp"] in ("none", "", None), x
        assert x["ellipse"] != "ellipsis", x
        assert x["coupe"] is False, x
