"""Bouton « Calculatrice » a cote de l'entree vers Jules (docs/spec/NAVIGATION.md, EX-217).

Banc de tests/nav_scenario.py (spec section 6) sur les 4 pages eleve :

- (a) un vrai `<button type="button" aria-label="Calculatrice">`, juste a cote du bouton qui ouvre Jules, zone de
  toucher mesuree >= 44 x 44 px, taille de texte suivant `--adapt-echelle-texte` ;
- (b) ouverture dans la page, par `OutilsHote.monter` : iframe `sandbox="allow-scripts"` sans
  `allow-same-origin`, jamais `window.open` ; bascule `aria-expanded`, une seule calculatrice a la fois ;
- (c) fermeture par « × » et par Echap, focus rendu au bouton ;
- (d) module `outils` retire de la config : pas de bouton ;
- (e) a 390 x 844 et 768 x 1024 : bouton ferme sans chevauchement avec la fiche ni la bande de Jules (EX-213),
  calculatrice ouverte entierement visible, aucune touche hors de son cadre ;
- (f) memes chemins d'API au chargement (`CHEMINS_AVANT`), fichiers de l'outil demandes seulement au clic.

Le calcul 7 x 6 = 42 « par clics » se fait DANS l'iframe isolee (origine opaque : la page ne peut pas y
toucher). Le test sert, a la place de `outil.js`, le vrai `outil.js` suivi d'une petite sonde, uniquement en
test : a la reception des leviers (poignee de main EX-001 a 003, donc apres l'affichage de l'outil), la sonde
clique 7, ×, 6, = sur les vraies touches, lit l'ecran, mesure chaque touche dans la fenetre de l'iframe, puis
renvoie le releve a la page par postMessage. La page (scenario) n'accepte ce releve que venu de
`iframe.contentWindow`.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import regle_par_defaut
from tests.nav_scenario import banc_navigation
from tests.test_navigation import ATTENDRE_BARRE, CHEMINS_AVANT

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"
OUTIL_JS = RACINE / "extensions" / "calculatrice" / "outil.js"
CHEMIN_OUTIL_JS = "/api/eleve/outils/calculatrice/outil.js"
PAGES = ("/", "/cours", "/studio", "/discuter")
# Element qui ouvre Jules, voisin immediat du bouton ; /discuter : la page de Jules, bouton dans l'en-tete.
VOISIN = {"/": "#avatar-jules", "/cours": "#menu-jules", "/studio": "#menu-jules", "/discuter": None}
NOTION = "parallelisme-triangles-pythagore"  # fiche avec schema, deja utilisee par EX-213
TELEPHONE, TABLETTE, BUREAU = (390, 844), (768, 1024), (1280, 800)

SONDE_OUTIL = r"""
;(function () {
  // Sonde de test (tests/test_navigation_calculatrice.py) : jamais servie en production.
  window.addEventListener("message", function (ev) {
    if (ev.source !== window.parent || !ev.data || ev.data.type !== "adaptations") return;
    var touches = Array.prototype.slice.call(document.querySelectorAll("#pave button"));
    function touche(t) {
      for (var i = 0; i < touches.length; i++) if (touches[i].textContent === t) return touches[i];
      throw new Error("touche absente : " + t);
    }
    ["7", "×", "6", "="].forEach(function (t) { touche(t).click(); });
    var hors = touches.filter(function (b) {
      var r = b.getBoundingClientRect();
      return r.width === 0 || r.top < -0.5 || r.left < -0.5
        || r.bottom > innerHeight + 0.5 || r.right > innerWidth + 0.5;
    }).map(function (b) { return b.textContent; });
    window.parent.postMessage({
      type: "sonde-calculatrice", ecran: document.getElementById("ecran").textContent, touches: touches.length,
      hors: hors, affiche: !document.body.hidden, defile: document.scrollingElement.scrollHeight > innerHeight + 0.5,
      hauteurContenu: document.scrollingElement.scrollHeight, fenetre: [innerWidth, innerHeight]
    }, "*");
  });
})();
"""

# Avant les scripts de la page : trace des window.open (aucun ne doit partir).
AVANT = r"""
  window.__ouvertures = [];
  var ouvrirOrigine = window.open;
  window.open = function () {
    window.__ouvertures.push(String(arguments[0]));
    return ouvrirOrigine.apply(window, arguments);
  };
"""

LIRE = r"""
  const inter = (a, b) => {
    const g = Math.max(a.left, b.left), d = Math.min(a.right, b.right);
    const h = Math.max(a.top, b.top), bas = Math.min(a.bottom, b.bottom);
    return d > g + 0.5 && bas > h + 0.5 ? { g, d, h, bas } : null;
  };
  const boite = (e) => {
    const r = e.getBoundingClientRect();
    return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, largeur: r.width, hauteur: r.height };
  };
  const dansFenetre = (r) =>
    r.left >= -0.5 && r.top >= -0.5 && r.right <= innerWidth + 0.5 && r.bottom <= innerHeight + 0.5;
  const ressourcesOutil = () => performance.getEntriesByType("resource").map((e) => new URL(e.name).pathname)
    .filter((p) => p.indexOf("/api/eleve/outils/") === 0);
  // Blocs visibles de la fiche (/) : meme definition qu'EX-213 (tests/test_navigation_n6.py).
  const blocsFiche = () => {
    const fiche = document.querySelector("#fiche");
    if (!fiche || fiche.classList.contains("cache")) return [];
    const zone = document.querySelector(".fiche-zone").getBoundingClientRect();
    const liste = [];
    for (const e of fiche.children) {
      if (e.id === "fiche-blocs") liste.push(...e.querySelectorAll(":scope > .fiche-bloc"));
      else liste.push(e);
    }
    return liste.filter((e) => getComputedStyle(e).display !== "none" && e.getBoundingClientRect().height > 0)
      .map((e) => ({ nom: e.id || e.dataset.adresse || e.className, r: inter(e.getBoundingClientRect(), zone) }))
      .filter((b) => b.r);
  };
  const chevauchements = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return [];
    const r = e.getBoundingClientRect();
    const zoneBloc = (b) => ({ left: b.r.g, right: b.r.d, top: b.r.h, bottom: b.r.bas });
    return blocsFiche().filter((b) => inter(zoneBloc(b), r)).map((b) => b.nom);
  };
  const releveSonde = () => new Promise((resoudre) => {
    const ecoute = (ev) => {
      const cadre = document.querySelector("#calculatrice-panneau iframe");
      if (!cadre || ev.source !== cadre.contentWindow || !ev.data || ev.data.type !== "sonde-calculatrice") return;
      removeEventListener("message", ecoute);
      resoudre(ev.data);
    };
    addEventListener("message", ecoute);
  });
"""

SCENARIO = (
    ATTENDRE_BARRE
    + LIRE
    + r"""
  await S.pause(1500);
  const r = { erreurs: [], ouvertures: null };
  r.apiAvant = S.api();
  r.ressourcesAvantClic = ressourcesOutil();
  r.iframesAvantClic = document.querySelectorAll("iframe").length;
  const b = document.querySelector("#bouton-calculatrice");
  r.present = !!b;
  r.nbBoutons = document.querySelectorAll("#bouton-calculatrice, button[aria-label='Calculatrice']").length;
  if (!b) { r.erreurs = S.erreurs(); r.ouvertures = window.__ouvertures; return r; }
  r.balise = b.tagName.toLowerCase();
  r.type = b.getAttribute("type");
  r.ariaLabel = b.getAttribute("aria-label");
  r.suivant = b.nextElementSibling ? "#" + b.nextElementSibling.id : null;
  r.precedent = b.previousElementSibling ? "#" + b.previousElementSibling.id : null;
  r.parent = b.parentElement.className;
  r.bouton = boite(b);
  r.visible = getComputedStyle(b).display !== "none" && getComputedStyle(b).visibility !== "hidden";
  r.boutonDansFenetre = dansFenetre(b.getBoundingClientRect());
  r.expandedFerme = b.getAttribute("aria-expanded");
  r.controls = b.getAttribute("aria-controls");
  r.chevauchementBoutonFerme = chevauchements("#bouton-calculatrice");
  r.chevauchementJFerme = chevauchements("#avatar-jules");
  const bande = document.querySelector("#jules-bulles");
  const bulles = document.querySelector("#bulles");
  const bulleVisible = bulles && bulles.getBoundingClientRect().height > 0;
  r.boutonSurBulles = bulleVisible ? !!inter(b.getBoundingClientRect(), bulles.getBoundingClientRect()) : false;
  const zone = document.querySelector(".fiche-zone");
  r.zoneBas = zone ? zone.getBoundingClientRect().bottom : null;
  r.bandeHaut = bande ? bande.getBoundingClientRect().top : null;
  r.focusableBouton = (() => { b.focus(); return document.activeElement === b; })();

  // (b) ouverture par clic
  const sonde = releveSonde();
  S.clic("#bouton-calculatrice");
  const ouvert = await S.attendre("#calculatrice-panneau iframe", 3000).catch(() => null);
  r.expandedOuvert = b.getAttribute("aria-expanded");
  r.iframes = document.querySelectorAll("iframe").length;
  if (!ouvert) { r.erreurs = S.erreurs(); r.ouvertures = window.__ouvertures; return r; }  // releve partiel
  const panneau = S.el("#calculatrice-panneau");
  const cadre = panneau.querySelector("iframe");
  r.sandbox = cadre.getAttribute("sandbox");
  r.classeCadre = cadre.className;
  r.srcCadre = new URL(cadre.src).pathname;
  r.panneauVisible = !panneau.hidden && getComputedStyle(panneau).display !== "none";
  r.panneau = boite(panneau);
  r.cadre = boite(cadre);
  r.panneauDansFenetre = dansFenetre(panneau.getBoundingClientRect());
  r.panneauSurBande = bande && innerWidth < 600
    ? !!inter(panneau.getBoundingClientRect(), bande.getBoundingClientRect()) : null;
  r.panneauSurBouton = !!inter(panneau.getBoundingClientRect(), b.getBoundingClientRect());
  const f = panneau.querySelector(".calculatrice-fermer");
  const rf = f ? f.getBoundingClientRect() : null;
  r.fermer = f ? { texte: f.textContent, visible: rf.height > 0, hauteur: rf.height } : null;
  r.sonde = await Promise.race([sonde, S.pause(4000).then(() => null)]);
  r.ressourcesApresClic = ressourcesOutil();

  // (c) Echap : ferme, focus rendu au bouton
  S.echap();
  await S.pause(50);
  r.apresEchap = { iframes: document.querySelectorAll("iframe").length, expanded: b.getAttribute("aria-expanded"),
                   panneauCache: panneau.hidden, focus: document.activeElement === b };

  // second clic = fermeture (bascule) ; puis « × »
  S.clic("#bouton-calculatrice");
  await S.attendre("#calculatrice-panneau iframe", 3000);
  S.clic("#bouton-calculatrice");
  await S.pause(50);
  r.apresSecondClic = { iframes: document.querySelectorAll("iframe").length,
                        expanded: b.getAttribute("aria-expanded") };
  S.clic("#bouton-calculatrice");
  await S.attendre("#calculatrice-panneau iframe", 3000);
  S.clic("#bouton-calculatrice");
  S.clic("#bouton-calculatrice");
  await S.pause(50);
  r.uneSeuleOuverte = document.querySelectorAll("iframe").length;
  S.clic("#calculatrice-panneau .calculatrice-fermer");
  await S.pause(50);
  r.apresCroix = { iframes: document.querySelectorAll("iframe").length, expanded: b.getAttribute("aria-expanded"),
                   focus: document.activeElement === b };
  r.echelle = getComputedStyle(b).fontSize;
  r.erreurs = S.erreurs();
  r.ouvertures = window.__ouvertures;
  return r;
"""
)

# Meme scenario avec l'echelle de texte doublee : la taille du bouton doit suivre (EX-105).
ECHELLE = (
    ATTENDRE_BARRE
    + r"""
  await S.attendre("#bouton-calculatrice", 4000);
  const b = S.el("#bouton-calculatrice");
  const avant = parseFloat(getComputedStyle(b).fontSize);
  document.body.style.setProperty("--adapt-echelle-texte", "2");
  const apres = parseFloat(getComputedStyle(b).fontSize);
  return { avant, apres };
"""
)


def _tuteur(tmp_path_factory, avec_outils: bool = True) -> Tuteur:
    projet = tmp_path_factory.mktemp("projet-calculatrice")
    for dossier in ("persona", "consignes", "profils", "bibliotheque", "extensions"):
        shutil.copytree(RACINE / dossier, projet / dossier)
    brut = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))
    brut["llm"] = {"backend": "factice", "historique_max": 30}
    if not avec_outils:
        brut["modules"] = [m for m in brut["modules"] if m.get("id") != "outils"]
    llm = Factice()
    llm.regle = regle_par_defaut
    return Tuteur(depuis_dict(brut, projet), llm=llm)


@pytest.fixture(scope="module")
def banc(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-calc")) as b:
            yield b
    finally:
        tuteur.fermer()


@pytest.fixture(scope="module")
def banc_sans_outils(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory, avec_outils=False)
    assert "outils" not in [m.id for m in tuteur.modules]
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-calc-sans")) as b:
            yield b
    finally:
        tuteur.fermer()


def _sonde() -> dict[str, str]:
    return {CHEMIN_OUTIL_JS: OUTIL_JS.read_text(encoding="utf-8") + SONDE_OUTIL}


def _jouer(banc, page: str, taille=BUREAU, remplaces: dict[str, str] | None = None) -> dict[str, Any]:
    chemin = f"/#{NOTION}" if page == "/" else page
    return banc.jouer(
        chemin, SCENARIO, taille=taille, avant=AVANT, remplaces={**_sonde(), **(remplaces or {})}, budget_ms=20000
    )


@pytest.fixture(scope="module")
def releves(banc) -> dict[tuple[str, tuple[int, int]], dict[str, Any]]:
    r = {}
    for page in PAGES:
        r[(page, BUREAU)] = _jouer(banc, page)
    for taille in (TELEPHONE, TABLETTE):
        for page in PAGES:
            r[(page, taille)] = _jouer(banc, page, taille)
    cles = ("bouton", "panneau", "cadre", "sonde", "chevauchementBoutonFerme", "chevauchementJFerme")
    for (page, taille), v in r.items():  # lisible avec `pytest -s` (a coller dans la revue)
        print(f"\nEX-217 {page} {taille}", {k: v.get(k) for k in cles})
    return r


CAS = [(p, t) for t in (BUREAU, TABLETTE, TELEPHONE) for p in PAGES]


def _id(cas) -> str:
    return f"{cas[0]}-{cas[1][0]}"


# --- (a) element ------------------------------------------------------------------------------------------


def verifier_element(r: dict[str, Any], page: str) -> None:
    assert r["present"] and r["nbBoutons"] == 1, r
    assert r["balise"] == "button" and r["type"] == "button", r
    assert r["ariaLabel"] == "Calculatrice", r
    assert r["visible"] and r["boutonDansFenetre"], r
    assert r["bouton"]["largeur"] >= 44 and r["bouton"]["hauteur"] >= 44, r["bouton"]
    assert r["focusableBouton"], r
    assert r["expandedFerme"] == "false" and r["controls"] == "calculatrice-panneau", r
    if VOISIN[page]:
        assert r["suivant"] == VOISIN[page], r  # juste avant l'entree vers Jules
    else:
        assert r["parent"] == "entete", r  # en-tete de /discuter


@pytest.mark.parametrize("cas", CAS, ids=_id)
def test_ex217a_bouton_a_cote_de_jules(releves, cas):
    verifier_element(releves[cas], cas[0])


def test_ex217a_taille_suit_l_echelle_du_texte(banc):
    r = banc.jouer("/cours", ECHELLE, budget_ms=10000)
    assert r["apres"] == pytest.approx(2 * r["avant"]), r


def test_ex217a_css_en_rem_et_echelle():
    css = (STATIQUE / "calculatrice.css").read_text(encoding="utf-8")
    assert "min-width: 2.75rem; min-height: 2.75rem" in css
    assert "font-size: calc(1.25rem * var(--adapt-echelle-texte, 1))" in css


# --- (b) ouverture dans la page, par l'hote ---------------------------------------------------------------


def verifier_ouverture(r: dict[str, Any]) -> None:
    assert r["ouvertures"] == [], r["ouvertures"]  # jamais window.open
    assert r["expandedOuvert"] == "true", r
    assert r["iframes"] == 1 and r["panneauVisible"], r
    assert r["panneauSurBouton"] is False, r  # le bouton reste visible et cliquable pour refermer
    assert r["sandbox"] == "allow-scripts", r["sandbox"]  # pas d'allow-same-origin
    assert r["classeCadre"] == "outil-cadre", r  # cadre cree par OutilsHote.monter
    assert r["srcCadre"] == "/api/eleve/outils/calculatrice/", r
    sonde = r["sonde"]
    assert sonde and sonde["affiche"], r  # poignee de main faite : les leviers sont arrives, l'outil s'affiche
    assert sonde["ecran"] == "42", sonde  # 7 x 6 par clics sur les vraies touches


@pytest.mark.parametrize("cas", CAS, ids=_id)
def test_ex217b_ouverture_iframe_isolee_et_calcul(releves, cas):
    verifier_ouverture(releves[cas])


@pytest.mark.parametrize("cas", CAS, ids=_id)
def test_ex217b_bascule_une_seule_a_la_fois(releves, cas):
    r = releves[cas]
    assert r["apresSecondClic"] == {"iframes": 0, "expanded": "false"}, r
    # trois clics de suite : ouvert, ferme, ouvert -> une seule calculatrice
    assert r["uneSeuleOuverte"] == 1, r


# --- (c) fermeture ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("cas", CAS, ids=_id)
def test_ex217c_echap_et_croix_rendent_le_focus(releves, cas):
    r = releves[cas]
    assert r["fermer"] and r["fermer"]["texte"] == "×" and r["fermer"]["visible"], r
    assert r["fermer"]["hauteur"] >= 44, r
    assert r["apresEchap"] == {"iframes": 0, "expanded": "false", "panneauCache": True, "focus": True}, r
    assert r["apresCroix"] == {"iframes": 0, "expanded": "false", "focus": True}, r


# --- (d) absence propre ------------------------------------------------------------------------------------


@pytest.mark.parametrize("page", PAGES)
def test_ex217d_sans_module_outils_pas_de_bouton(banc_sans_outils, page):
    r = _jouer(banc_sans_outils, page)
    assert r["present"] is False and r["nbBoutons"] == 0, r
    assert r["erreurs"] == [], r["erreurs"]


# --- (e) telephone et tablette ----------------------------------------------------------------------------


def verifier_petit_ecran(r: dict[str, Any], page: str, taille: tuple[int, int]) -> None:
    # Bouton ferme : aucun chevauchement avec les blocs visibles de la fiche, ni avec la bulle de Jules.
    assert r["chevauchementBoutonFerme"] == [], r["chevauchementBoutonFerme"]
    assert r["boutonSurBulles"] is False, r
    if page == "/" and taille[0] < 600:
        # EX-213 : la zone de lecture s'arrete au-dessus de la bande de Jules, qui contient le bouton.
        assert r["zoneBas"] <= r["bandeHaut"] + 0.5, r
        assert r["bouton"]["top"] >= r["bandeHaut"] - 0.5, r
        assert r["chevauchementJFerme"] == [], r
        assert r["panneauSurBande"] is False, r
    # Ouvert : panneau entierement dans l'ecran, toutes les touches dans le cadre (pas de defilement).
    assert r["panneauDansFenetre"], r["panneau"]
    sonde = r["sonde"]
    assert sonde and sonde["touches"] >= 24 and sonde["hors"] == [] and not sonde["defile"], sonde


@pytest.mark.parametrize("cas", [c for c in CAS if c[1] != BUREAU], ids=_id)
def test_ex217e_petits_ecrans(releves, cas):
    verifier_petit_ecran(releves[cas], *cas)


@pytest.mark.parametrize("cas", CAS, ids=_id)
def test_ex217e_calculatrice_entiere_a_toutes_les_tailles(releves, cas):
    r = releves[cas]
    assert r["panneauDansFenetre"] and r["sonde"]["hors"] == [] and not r["sonde"]["defile"], (r["panneau"], r["sonde"])


# --- (f) appels -------------------------------------------------------------------------------------------


@pytest.mark.parametrize("page", PAGES)
def test_ex217f_memes_chemins_au_chargement(banc, page):
    # Meme mesure que test_ex210a (test_navigation.py) : CHEMINS_AVANT n'est pas modifie par cette carte.
    r = banc.jouer(page, "await S.pause(2500); return S.api();", budget_ms=8000)
    assert sorted(r) == sorted(CHEMINS_AVANT[page])


@pytest.mark.parametrize("cas", CAS, ids=_id)
def test_ex217f_fichiers_de_l_outil_charges_au_clic_seulement(releves, cas):
    r = releves[cas]
    assert r["iframesAvantClic"] == 0 and r["ressourcesAvantClic"] == [], r
    assert not any(c.startswith("/api/eleve/outils") for c in r["apiAvant"]), r["apiAvant"]
    assert "/api/eleve/outils/calculatrice/" in r["ressourcesApresClic"], r["ressourcesApresClic"]


@pytest.mark.parametrize("cas", CAS, ids=_id)
def test_ex217_scenario_sans_erreur(releves, cas):
    assert releves[cas]["erreurs"] == [], releves[cas]["erreurs"]


# --- statique ----------------------------------------------------------------------------------------------


def test_ex217_pages_chargent_hote_puis_bouton():
    for nom in ("accueil.html", "cours.html", "studio.html", "eleve.html"):
        html = (STATIQUE / nom).read_text(encoding="utf-8")
        assert html.index("/static/outils-hote.js") < html.index("/static/calculatrice.js"), nom
        assert '<link rel="stylesheet" href="/static/calculatrice.css">' in html, nom
    parent = (STATIQUE / "parent.html").read_text(encoding="utf-8")
    assert "calculatrice" not in parent


def test_ex217_ouverture_seulement_par_l_hote():
    js = (STATIQUE / "calculatrice.js").read_text(encoding="utf-8")
    assert "OutilsHote.monter(" in js
    for interdit in ("window.open", 'createElement("iframe")', "target=", "location.href", "MS.api(", "fetch("):
        assert interdit not in js, interdit


# --- mutations : chaque mutation fait echouer le test vise -------------------------------------------------


def _mutant(ancre: str, remplacement: str) -> str:
    source = (STATIQUE / "calculatrice.js").read_text(encoding="utf-8")
    assert source.count(ancre) == 1, ancre
    return source.replace(ancre, remplacement)


def test_mutation_sans_aria_label_fait_echouer_ex217a(banc):
    mutant = _mutant('    bouton.setAttribute("aria-label", "Calculatrice");\n', "")
    r = _jouer(banc, "/cours", remplaces={"/static/calculatrice.js": mutant})
    with pytest.raises(AssertionError):
        verifier_element(r, "/cours")


def test_mutation_window_open_fait_echouer_ex217b(banc):
    mutant = _mutant(
        "      monte = OutilsHote.monter(zone, outil, { leviers: options.leviers || {} });\n",
        '      window.open("/api/eleve/outils/calculatrice/", "_blank");\n      monte = { demonter() {} };\n',
    )
    r = _jouer(banc, "/cours", remplaces={"/static/calculatrice.js": mutant})
    assert r["ouvertures"] == ["/api/eleve/outils/calculatrice/"]  # la mutation a bien joue
    with pytest.raises(AssertionError):
        verifier_ouverture(r)


def test_mutation_bouton_sans_catalogue_fait_echouer_ex217d(banc_sans_outils):
    mutant = _mutant(
        "    const outil = outilDuCatalogue(infos);\n",
        '    const outil = outilDuCatalogue(infos) || { id: "calculatrice", titre: "Calculatrice" };\n',
    )
    r = _jouer(banc_sans_outils, "/cours", remplaces={"/static/calculatrice.js": mutant})
    with pytest.raises(AssertionError):
        assert r["present"] is False and r["nbBoutons"] == 0, r
