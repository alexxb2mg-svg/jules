"""Navigation N3 : tiroir sous 900 px et barre repliable au-dessus (docs/spec/NAVIGATION.md, EX-207, EX-208).

Scenarios Chromium sur le banc de tests/nav_scenario.py, sur les 4 pages eleve :
- 390 x 844 (carte N3) et 768 x 1024 (spec EX-207) : ouverture par ☰, fermeture par Echap, par clic en dehors
  et par choix d'une entree feuille, focus rendu au bouton ☰ ; une rubrique a sous-pages ne ferme pas le tiroir ;
- 1280 x 800 : repli de la barre, rechargement, la barre reste repliee ; seule la cle `jules.nav.repliee`
  (booleen) est ecrite.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from jules.web.app import STATIQUE, creer_app
from tests.nav_scenario import banc_navigation
from tests.test_navigation import (
    ATTENDRE_BARRE,
    LIRE_BARRE,
    PAGES_ELEVE,
    _tuteur,
    comparer_a_la_reference,
)

CLE = "jules.nav.repliee"
TAILLES_TIROIR = [(390, 844), (768, 1024)]


@pytest.fixture(scope="module")
def banc(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory, None)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n3")) as b:
            yield b
    finally:
        tuteur.fermer()


# --- statiques ---------------------------------------------------------------------------------------


def test_ex207_une_seule_cle_localstorage_booleenne():
    js = (STATIQUE / "navigation.js").read_text(encoding="utf-8")
    code = re.sub(r"^\s*//.*$", "", js, flags=re.M)
    assert re.findall(r"localStorage\.(\w+)\(", code) == ["getItem", "setItem"]
    assert 'const CLE_REPLI = "jules.nav.repliee";' in code
    assert "localStorage.setItem(CLE_REPLI, String(repliee))" in code
    assert code.count("jules.nav") == 1


def test_ex207_ex208_regles_css_du_tiroir_et_du_repli():
    css = (STATIQUE / "navigation.css").read_text(encoding="utf-8")
    assert ".barre-replier:focus-visible" in css
    assert not re.search(r"font-size\s*:\s*[\d.]+px", css)


def test_ex207_un_seul_bouton_barre_dans_les_pages():
    """Le bouton ☰ de la barre n'existe que dans le composant : aucune page ne le declare."""
    for nom in ("accueil.html", "cours.html", "studio.html", "eleve.html"):
        html = (STATIQUE / nom).read_text(encoding="utf-8")
        assert "barre-jules" not in html, nom


# --- tiroir sous 900 px ------------------------------------------------------------------------------

TIROIR = r"""
  const barre = S.el("#barre-jules");
  const bouton = S.el("#barre-jules-bouton");
  // Le temps virtuel du banc ne fait pas avancer les transitions CSS : on mesure l'etat final.
  barre.style.transition = "none";
  const etat = () => {
    const r = barre.getBoundingClientRect();
    return {
      expanded: bouton.getAttribute("aria-expanded"), classe: barre.classList.contains("ouverte"),
      visibilite: getComputedStyle(barre).visibility, gauche: r.left, droite: r.right,
      focusBouton: document.activeElement === bouton,
    };
  };
  const ouvrir = async () => { S.clic(bouton); await S.pause(50); return etat(); };
  const b = bouton.getBoundingClientRect();
  const r = {
    controls: bouton.getAttribute("aria-controls"), idBarre: barre.id, boutonVisible: getComputedStyle(bouton).display,
    boutonPos: [b.left, b.top, b.width, b.height], nom: bouton.textContent.replace("☰", "").trim(),
    replier: getComputedStyle(S.el("#barre-jules-replier")).display,
  };
  r.initial = etat();

  // 1. Echap (focus dans le tiroir)
  r.ouvert1 = await ouvrir();
  barre.querySelector("a,button").focus();
  r.focusDansTiroir = barre.contains(document.activeElement);
  S.echap();
  await S.pause(50);
  r.apresEchap = etat();

  // 2. Clic en dehors : ce qui est sous le point (droite de l'ecran) doit etre le voile, pas la page
  r.ouvert2 = await ouvrir();
  const dehors = document.elementFromPoint(innerWidth - 8, Math.round(innerHeight / 2));
  r.dehors = dehors ? dehors.className : null;
  r.dehorsDansBarre = !!dehors && barre.contains(dehors);
  dehors.click();
  await S.pause(50);
  r.apresDehors = etat();

  // 3. Rubrique a sous-pages : le tiroir reste ouvert (elle ouvre une petite page, EX-207)
  await ouvrir();
  S.clic('#barre-jules button[data-sous-pages="fiches"]');
  await S.pause(50);
  r.apresRubrique = etat();

  // 4. Entree feuille (lien) : le tiroir se ferme ; la navigation est empechee pour rester sur la page
  window.addEventListener("click", (ev) => ev.preventDefault());
  S.clic('#barre-jules a[href="/discuter"]');
  await S.pause(50);
  r.apresFeuille = etat();
  r.chemin = location.pathname;

  // 5. Re-clic sur ☰ : ferme aussi
  await ouvrir();
  S.clic(bouton);
  await S.pause(50);
  r.apresBouton = etat();
  return r;
"""


def _tiroir(banc, page: str, taille: tuple[int, int], avant: str = "") -> dict[str, Any]:
    return banc.jouer(page, ATTENDRE_BARRE + TIROIR, taille=taille, budget_ms=8000, avant=avant)


@pytest.fixture(scope="module")
def tiroirs(banc) -> dict[tuple[str, tuple[int, int]], dict[str, Any]]:
    return {(page, taille): _tiroir(banc, page, taille) for page in PAGES_ELEVE for taille in TAILLES_TIROIR}


def _ferme(e: dict[str, Any]) -> None:
    assert e["expanded"] == "false" and e["classe"] is False and e["visibilite"] == "hidden", e
    assert e["droite"] <= 0.5, e  # hors ecran a gauche


def _ouvert(e: dict[str, Any], largeur: int) -> None:
    assert e["expanded"] == "true" and e["classe"] is True and e["visibilite"] == "visible", e
    assert 0 <= e["gauche"] < e["droite"] <= largeur, e


@pytest.mark.parametrize("taille", TAILLES_TIROIR, ids=lambda t: f"{t[0]}x{t[1]}")
@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex207_tiroir_ouverture_et_trois_fermetures(tiroirs, page, taille):
    r = tiroirs[(page, taille)]
    largeur = taille[0]
    assert r["boutonVisible"] != "none" and r["replier"] == "none"
    assert r["controls"] == r["idBarre"] == "barre-jules"
    assert r["nom"] == "Menu"
    _ferme(r["initial"])
    for cle in ("ouvert1", "ouvert2"):
        _ouvert(r[cle], largeur)
    assert r["focusDansTiroir"] is True
    # Echap, clic en dehors, entree feuille, re-clic : ferme et focus rendu au bouton ☰
    for cle in ("apresEchap", "apresDehors", "apresFeuille", "apresBouton"):
        _ferme(r[cle])
        assert r[cle]["focusBouton"] is True, (cle, r[cle])
    assert r["dehors"] == "barre-voile" and r["dehorsDansBarre"] is False
    _ouvert(r["apresRubrique"], largeur)  # une rubrique a sous-pages ne ferme pas
    assert r["chemin"] == page


@pytest.mark.parametrize("taille", TAILLES_TIROIR, ids=lambda t: f"{t[0]}x{t[1]}")
def test_ex207_bouton_au_meme_endroit_sur_les_4_pages(tiroirs, taille):
    positions = {page: tiroirs[(page, taille)]["boutonPos"] for page in PAGES_ELEVE}
    assert len({json.dumps(p) for p in positions.values()}) == 1, positions
    assert positions["/"][2] >= 44 and positions["/"][3] >= 44  # zone de clic >= 44 px


def test_ex207_etat_replie_memorise_sans_effet_sur_le_tiroir(banc):
    """Barre repliee memorisee sur grand ecran : sous 900 px, le tiroir s'ouvre deplie (libelles visibles)."""
    avant = f"localStorage.setItem({json.dumps(CLE)}, 'true');"
    etapes = (
        ATTENDRE_BARRE
        + r"""
  S.el("#barre-jules").style.transition = "none";
  S.clic("#barre-jules-bouton");
  await S.pause(50);
  const lib = S.el("#barre-jules .barre-libelle").getBoundingClientRect();
  return { largeurLibelle: lib.width, icone: getComputedStyle(S.el("#barre-jules .barre-icone")).display,
           largeurBarre: S.rect("#barre-jules").largeur };
"""
    )
    r = banc.jouer("/", etapes, taille=(390, 844), budget_ms=8000, avant=avant)
    assert r["largeurLibelle"] > 40 and r["icone"] == "none" and r["largeurBarre"] > 200, r


# --- barre repliable a partir de 900 px ---------------------------------------------------------------

REPLI = (
    LIRE_BARRE
    + r"""
  const mesure = () => {
    const barre = S.el("#barre-jules");
    const replier = S.el("#barre-jules-replier");
    const lib = barre.querySelector(".barre-libelle").getBoundingClientRect();
    const rr = replier.getBoundingClientRect();
    const icones = [...barre.querySelectorAll(".barre-icone")].map((i) => getComputedStyle(i).display);
    return {
      repliee: document.body.classList.contains("barre-repliee"),
      expanded: replier.getAttribute("aria-expanded"), controls: replier.getAttribute("aria-controls"),
      nomReplier: replier.getAttribute("aria-label"),
      largeurBarre: barre.getBoundingClientRect().width, largeurLibelle: lib.width,
      paddingBody: parseFloat(getComputedStyle(document.body).paddingLeft), icones,
      replierRect: [rr.left, rr.right, rr.width, rr.height],
      boutonTiroir: getComputedStyle(S.el("#barre-jules-bouton")).display,
      stockage: S.stockage(), lecture: lireBarre(),
    };
  };
  const phase = sessionStorage.getItem("scenario-phase");
  if (!phase) {
    const r = { avant: mesure() };
    S.clic("#barre-jules-replier");
    await S.pause(50);
    r.apresClic = mesure();
    sessionStorage.setItem("scenario-phase", JSON.stringify(r));
    location.reload();
    await new Promise(() => {}); // la page se recharge : la suite se joue au chargement suivant
  }
  const r = JSON.parse(phase);
  r.apresRechargement = mesure();
  S.focus("#barre-jules-replier");
  S.clic("#barre-jules-replier");
  await S.pause(50);
  r.deplie = mesure();
  r.focusReplier = document.activeElement === S.el("#barre-jules-replier");
  return r;
"""
)


@pytest.fixture(scope="module")
def replis(banc) -> dict[str, dict[str, Any]]:
    return {page: banc.jouer(page, ATTENDRE_BARRE + REPLI, taille=(1280, 800), budget_ms=15000) for page in PAGES_ELEVE}


def _cles_nav(stockage: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in stockage.items() if "nav" in k.lower() or "barre" in k.lower() or "repli" in k.lower()}


@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex207_repli_puis_rechargement_reste_repliee(replis, page):
    r = replis[page]
    avant, clic, recharge, deplie = r["avant"], r["apresClic"], r["apresRechargement"], r["deplie"]
    # Etat initial : depliee, aucune cle ecrite
    assert avant["repliee"] is False and avant["expanded"] == "true" and CLE not in avant["stockage"]
    assert avant["controls"] == "barre-jules" and avant["nomReplier"]
    assert avant["boutonTiroir"] == "none"
    assert avant["largeurLibelle"] > 40 and set(avant["icones"]) == {"none"}
    # Repli : barre etroite, icones visibles, libelles masques visuellement
    for e in (clic, recharge):
        assert e["repliee"] is True and e["expanded"] == "false", e
        assert e["largeurBarre"] < 80 and e["paddingBody"] == pytest.approx(e["largeurBarre"], abs=1), e
        assert e["largeurLibelle"] <= 1 and set(e["icones"]) == {"flex"}, (
            e
        )  # inline-flex d un element de flex calcule en flex
        assert _cles_nav(e["stockage"]) == {CLE: "true"}, e["stockage"]
    # Deplier de nouveau : le booleen passe a false, rien d'autre
    assert deplie["repliee"] is False and deplie["expanded"] == "true" and deplie["largeurBarre"] > 200
    assert _cles_nav(deplie["stockage"]) == {CLE: "false"}
    assert r["focusReplier"] is True


@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex207_ex202_ex208_barre_repliee_garde_noms_et_ordre(replis, page):
    """Repliee, la barre garde exactement l'etape 1 de la reference (noms accessibles), les zones de clic
    >= 44 px, aucune emoji visible et l'entree active."""
    b = replis[page]["apresRechargement"]["lecture"]
    comparer_a_la_reference(b["lignes"])
    assert b["emojisVisibles"] == []
    assert all(e["hauteur"] >= 44 for e in b["entrees"])
    hauts = [e["haut"] for e in b["entrees"]]
    assert hauts == sorted(hauts)
    assert len([e for e in b["entrees"] if e["courant"] == "page"]) == 1


@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex208_bouton_replier_cible_44px(replis, page):
    for e in (replis[page]["avant"], replis[page]["apresRechargement"]):
        gauche, droite, largeur, hauteur = e["replierRect"]
        assert largeur >= 44 and hauteur >= 44
        assert gauche >= 0 and droite <= e["largeurBarre"] + 1, e["replierRect"]  # dans la barre


# --- EX-207 (spec c552b31) : un seul bouton ☰ par page ------------------------------------------------

UN_SEUL_MENU = r"""
  await S.pause(300);
  const visible = (e) => {
    const s = getComputedStyle(e);
    if (s.display === "none" || s.visibility === "hidden") return false;
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight;
  };
  const seuls = [...document.body.querySelectorAll("*")].filter((e) => e.textContent.trim() === "☰" && visible(e));
  // Un element et son parent au texte identique ne comptent qu'une fois : on garde les plus profonds.
  const feuilles = seuls.filter((e) => !seuls.some((f) => f !== e && e.contains(f)));
  const bouton = (e) => e.closest("button,a,[role=button]");
  const cote = document.getElementById("menu-cote");
  return {
    seuls: feuilles.map((e) => (bouton(e) || e).id || (bouton(e) || e).className),
    menuCote: cote ? { nom: cote.getAttribute("aria-label") || cote.textContent.trim(),
                       expanded: cote.getAttribute("aria-expanded") } : null,
  };
"""


@pytest.mark.parametrize("taille", [(768, 1024), (390, 844), (1280, 800)], ids=lambda t: f"{t[0]}x{t[1]}")
@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex207_un_seul_bouton_menu_par_page(banc, page, taille):
    r = banc.jouer(page, ATTENDRE_BARRE + UN_SEUL_MENU, taille=taille, budget_ms=8000)
    if taille[0] < 900:
        assert r["seuls"] == ["barre-jules-bouton"], r
    else:
        # A partir de 900 px le bouton ☰ du tiroir est masque : aucun autre ☰ seul ne le remplace.
        assert r["seuls"] == [], r
    if page == "/discuter":
        assert r["menuCote"] == {"nom": "Discussions", "expanded": None}, r


def test_ex207_menu_cote_statique():
    html = (STATIQUE / "eleve.html").read_text(encoding="utf-8")
    bouton = re.findall(r"<button\b[^>]*\bid=\"menu-cote\"[^>]*>(.*?)</button>", html, re.S)
    assert bouton == ["Discussions"]
    assert 'aria-label="Menu"' not in html


def test_ex207_valeur_invalide_en_stockage_barre_depliee(banc):
    avant = f"localStorage.setItem({json.dumps(CLE)}, '{{\"x\":1}}');"
    etapes = ATTENDRE_BARRE + 'return document.body.classList.contains("barre-repliee");'
    assert banc.jouer("/cours", etapes, taille=(1280, 800), avant=avant) is False
