"""Navigation N2 : barre laterale unique, etape 1 (docs/spec/NAVIGATION.md, EX-201 a EX-206, EX-208, EX-210 (a),
EX-211).

Tests statiques (HTML, JS, CSS de jules/web/static/) et scenarios Chromium sur le banc de tests/nav_scenario.py.
La reference `tests/navigation-reference.json` est une copie octet pour octet de
`docs/spec/navigation-reference.json` (branche spec/navigation), tenue par SPEC : elle n'est pas modifiee ici.
"""

from __future__ import annotations

import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

import pytest
import yaml

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import STATIQUE, creer_app
from tests.conftest import regle_par_defaut
from tests.nav_scenario import banc_navigation

RACINE = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((Path(__file__).parent / "navigation-reference.json").read_text(encoding="utf-8"))
PAGES_ELEVE = ("/", "/cours", "/studio", "/discuter")
COMPOSANT = ("navigation.js", "navigation.css")
EXEMPTIONS_EX205 = tuple(REFERENCE["exemptions_ex205"])
ROUTES_SECTION = ("/", "/cours", "/studio", "/discuter", "/parent")
LIBELLES = [e["libelle"] for r in REFERENCE["rubriques"] for e in r["entrees"]]
ACTIVE_PAR_CHEMIN = {e["page"]: e["libelle"] for r in REFERENCE["rubriques"] for e in r["entrees"]}
# EX-210 (N4) : liste blanche du cache de MS.api, seuls chemins que la barre lit.
CHEMINS_EN_CACHE = ("/api/eleve/fiches_visuelles/notions", "/api/eleve/cours/parcours", "/api/eleve/studio/notions")


# --- outils -------------------------------------------------------------------------------------------


def normaliser(texte: str) -> str:
    """Retire les emojis (symboles « So », selecteurs de variante, liant ZWJ) et normalise les espaces.
    Accents et casse sont gardes : la comparaison au JSON reste exacte."""
    sans = "".join(
        c for c in texte if unicodedata.category(c) != "So" and c not in "\ufe0e\ufe0f\u200d" and ord(c) < 0x1F000
    )
    return " ".join(sans.split())


def etape1_attendue() -> list[tuple[str, str, str, str]]:
    """(rubrique, libelle, 'href' ou 'sous_pages', valeur) dans l'ordre de la reference."""
    lignes = []
    for rubrique in REFERENCE["rubriques"]:
        for e in rubrique["entrees"]:
            genre = "sous_pages" if "sous_pages" in e else "href"
            lignes.append((rubrique["titre"], e["libelle"], genre, e[genre]))
    return lignes


def comparer_a_la_reference(rendu: list[list[str]]) -> None:
    """Comparaison exacte (EX-202) apres seulement retrait des emojis et normalisation des espaces."""
    obtenu = [(normaliser(r), normaliser(lib), genre, valeur) for r, lib, genre, valeur in rendu]
    assert obtenu == etape1_attendue()


def statiques(motif: str) -> list[Path]:
    return sorted(p for p in STATIQUE.glob(motif) if p.name not in COMPOSANT)


# --- EX-202 : le JSON de reference et le cas temoin --------------------------------------------------


def test_ex202_reference_contient_les_accents():
    assert "Mes leçons" in LIBELLES and "M'entraîner" in [r["titre"] for r in REFERENCE["rubriques"]]


def test_ex202_temoin_mes_lecons_sans_cedille_echoue():
    rendu = [[r, lib, genre, val] for r, lib, genre, val in etape1_attendue()]
    comparer_a_la_reference(rendu)  # la reference elle-meme passe
    for ligne in rendu:
        if ligne[1] == "Mes leçons":
            ligne[1] = "Mes lecons"
    with pytest.raises(AssertionError):
        comparer_a_la_reference(rendu)


def test_ex202_emojis_retires_et_espaces_normalises_seulement():
    assert normaliser("📘  Mes\u00a0leçons ") == "Mes leçons"
    assert normaliser("🛠️ M'entraîner") == "M'entraîner"
    assert normaliser("mes leçons") != "Mes leçons"  # la casse compte


# --- EX-201 : aucun libelle de la barre en dur hors composant ----------------------------------------

BALISES_A_NAV = re.compile(r"<(a|nav)\b[^>]*>(.*?)</\1>", re.S | re.I)


def _libelles_en_dur(html: str) -> list[str]:
    """Libelles de la barre trouves dans les <a> et <nav>. Les liens exemptes d'EX-205 (lien contextuel
    `#chat-flottant-lien` « Discuter avec Jules » de la fiche, `#retour-eleve`) sont hors du controle."""
    fautes = []
    for balise in BALISES_A_NAV.finditer(re.sub(r"<!--.*?-->", "", html, flags=re.S)):
        ouvrante = balise.group(0).split(">", 1)[0]
        if any(f'id="{ex}"' in ouvrante for ex in EXEMPTIONS_EX205):
            continue
        texte = normaliser(re.sub(r"<[^>]+>", " ", balise.group(2)))
        fautes += [lib for lib in LIBELLES if lib in texte]
    return fautes


def test_ex201_aucun_libelle_de_la_barre_dans_les_a_et_nav_des_html():
    for page in statiques("*.html"):
        assert not _libelles_en_dur(page.read_text(encoding="utf-8")), page.name


def test_ex201_temoin_le_controle_attrape_un_libelle_en_dur():
    assert _libelles_en_dur('<a class="x" href="/y">📘 Mes fiches</a>') == ["Mes fiches"]
    assert _libelles_en_dur("<nav><span>Discuter avec Jules</span></nav>") == ["Discuter avec Jules"]
    assert not _libelles_en_dur("<title>Jules - Mes fiches</title><!-- <a>Mes fiches</a> -->")
    assert not _libelles_en_dur('<a class="bouton" id="chat-flottant-lien" href="/discuter">Discuter avec Jules</a>')


def test_ex201_composant_charge_sur_les_4_pages_apres_commun_js():
    for nom in ("accueil.html", "cours.html", "studio.html", "eleve.html"):
        html = (STATIQUE / nom).read_text(encoding="utf-8")
        assert '<link rel="stylesheet" href="/static/navigation.css">' in html, nom
        assert html.index("/static/symboles.js") < html.index('"/rappels.js"') < html.index("/static/commun.js"), nom
        assert html.index("/static/commun.js") < html.index("/static/navigation.js"), nom
    parent = (STATIQUE / "parent.html").read_text(encoding="utf-8")
    assert "navigation.js" not in parent and "navigation.css" not in parent


# --- EX-205 : navigations concurrentes ---------------------------------------------------------------

ROUTE = r"/(?:cours|studio|discuter|parent)?(?:\?[^\"'`]*)?"
A_HREF = re.compile(r"<a\b[^>]*\bhref\s*=\s*\"(" + ROUTE + r")\"[^>]*>", re.I)
AFFECTATION_HREF = re.compile(r"\.href\s*=\s*[\"'`](" + ROUTE + r")(?:[\"'`]|\$\{)")
SET_ATTRIBUTE_HREF = re.compile(r"setAttribute\(\s*[\"']href[\"']")


def _navigations_concurrentes(nom: str, texte: str) -> list[str]:
    fautes = []
    for balise in A_HREF.finditer(texte):
        if not any(f'id="{ex}"' in balise.group(0) for ex in EXEMPTIONS_EX205):
            fautes.append(f"{nom}: {balise.group(0)}")
    for ligne in texte.splitlines():
        if (AFFECTATION_HREF.search(ligne) or SET_ATTRIBUTE_HREF.search(ligne)) and not any(
            ex in ligne for ex in EXEMPTIONS_EX205
        ):
            fautes.append(f"{nom}: {ligne.strip()}")
    return fautes


def test_ex205_aucun_lien_de_section_hors_composant_et_exemptions():
    fautes = []
    for fichier in statiques("*.html") + statiques("*.js"):
        fautes += _navigations_concurrentes(fichier.name, fichier.read_text(encoding="utf-8"))
    assert not fautes, "\n".join(fautes)


def test_ex205_temoins_le_controle_attrape_les_trois_ecritures():
    assert _navigations_concurrentes("t", '<a class="bouton" href="/">📘 Mes fiches</a>')
    assert _navigations_concurrentes("t", '<a href="/cours?matiere=x">x</a>')
    assert _navigations_concurrentes("t", '      lienCours.href = "/cours";')
    assert _navigations_concurrentes("t", "      lien.href = `/studio?notion=${n}`;")
    assert _navigations_concurrentes("t", '      lien.setAttribute("href", "/parent");')
    assert not _navigations_concurrentes("t", '<a class="bouton" id="chat-flottant-lien" href="/discuter">x</a>')
    assert not _navigations_concurrentes("t", '<a href="/api/parent/dossier/export">x</a>')


def test_ex205_elements_supprimes():
    tout = "\n".join(p.read_text(encoding="utf-8") for p in statiques("*.html") + statiques("*.js"))
    assert "chat-flottant-reglages" not in tout
    assert "Suivre un cours" not in tout and "Mon studio" not in tout
    assert "rail-lien" not in tout
    for nom in ("cours.html", "studio.html"):
        assert '<a class="cours-marque"' not in (STATIQUE / nom).read_text(encoding="utf-8")
        assert '<a class="studio-marque"' not in (STATIQUE / nom).read_text(encoding="utf-8")


# --- EX-206 : espace parent (statique) ---------------------------------------------------------------


def test_ex206_parent_sans_barre_eleve_avec_retour_eleve():
    html = (STATIQUE / "parent.html").read_text(encoding="utf-8")
    assert 'aria-label="Sections de Jules"' not in html
    retour = re.findall(r"<a\b[^>]*\bid=\"retour-eleve\"[^>]*>(.*?)</a>", html, re.S)
    assert retour == ["Retour à l'espace élève"]
    assert re.search(r"<a\b[^>]*id=\"retour-eleve\"[^>]*href=\"/\"", html)
    assert len(re.findall(r"<a\b[^>]*\bhref=\"/\"", html)) == 1  # son unique lien de retour


def test_ex206_plus_aucun_mon_suivi():
    for fichier in sorted(STATIQUE.glob("*.html")) + sorted(STATIQUE.glob("*.js")):
        assert "Mon suivi" not in fichier.read_text(encoding="utf-8"), fichier.name


def test_ex206_ms_porte_renvoie_l_etat_de_session():
    commun = (STATIQUE / "commun.js").read_text(encoding="utf-8")
    assert "if (etat[role]) return etat;" in commun
    assert "resoudre(nouvel);" in commun


# --- EX-208 et EX-210 : statiques du composant --------------------------------------------------------


def test_ex208_focus_visible_et_tailles_en_rem():
    css = (STATIQUE / "navigation.css").read_text(encoding="utf-8")
    regles = re.findall(r"([^{}]+)\{[^}]*\}", css)
    visibles = " ".join(sel for sel in regles if ":focus-visible" in sel)
    assert ".barre-entree:focus-visible" in visibles and ".barre-jules-bouton:focus-visible" in visibles
    assert not re.search(r"font-size\s*:\s*[\d.]+px", css)
    assert "min-height: 2.75rem" in css  # zones de clic >= 44 px


def test_ex210_le_composant_ne_lit_que_persona_et_prenom_et_n_appelle_rien():
    # N4 (EX-209/210, spec 8034799) : la barre lit ses listes par MS.api, sur les trois chemins de la liste blanche
    # du cache, et rien d'autre (ni fetch, ni /api/session, ni /api/infos).
    js = (STATIQUE / "navigation.js").read_text(encoding="utf-8")
    code = re.sub(r"^\s*//.*$", "", js, flags=re.M)  # les commentaires peuvent citer /api/session
    assert set(re.findall(r"\binfos\.(\w+)", code)) == {"persona", "prenom"}
    assert set(re.findall(r"\binfos\.persona\.(\w+)", code)) == {"nom"}
    assert "fetch(" not in code
    assert set(re.findall(r"[\"'`](/api/[^\"'`?]*)", code)) == set(CHEMINS_EN_CACHE)
    assert "innerHTML" not in code


def test_ex202_le_composant_recopie_la_reference():
    js = (STATIQUE / "navigation.js").read_text(encoding="utf-8")
    for rubrique in REFERENCE["rubriques"]:
        assert f'titre: "{rubrique["titre"]}"' in js
        for e in rubrique["entrees"]:
            assert f'libelle: "{e["libelle"]}"' in js and f'page: "{e["page"]}"' in js
    assert REFERENCE["nav_aria_label"] in js


# --- bancs Chromium -----------------------------------------------------------------------------------


def _tuteur(tmp_path_factory, acces: dict[str, str] | None) -> Tuteur:
    projet = tmp_path_factory.mktemp("projet-nav2")
    for dossier in ("persona", "consignes", "profils", "bibliotheque", "extensions"):
        shutil.copytree(RACINE / dossier, projet / dossier)
    brut = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))
    brut["llm"] = {"backend": "factice", "historique_max": 30}
    if acces:
        brut["acces"] = acces
    llm = Factice()
    llm.regle = regle_par_defaut
    return Tuteur(depuis_dict(brut, projet), llm=llm)


@pytest.fixture(scope="module")
def banc(tmp_path_factory):
    """Acces libre (config.yaml du depot : aucun code)."""
    tuteur = _tuteur(tmp_path_factory, None)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n2")) as b:
            yield b
    finally:
        tuteur.fermer()


CODE_ELEVE, CODE_PARENT = "k7m2q9", "r8t3w6p1"


@pytest.fixture(scope="module")
def banc_codes(tmp_path_factory):
    """Codes eleve et parent definis : la porte s'affiche (session vide a chaque scenario)."""
    tuteur = _tuteur(tmp_path_factory, {"code_eleve": empreinte(CODE_ELEVE), "code_parent": empreinte(CODE_PARENT)})
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n2-codes")) as b:
            yield b
    finally:
        tuteur.fermer()


# Lecture de l'etape 1 dans le DOM : nom accessible = texte hors aria-hidden.
LIRE_BARRE = r"""
  const nom = (e) => {
    let t = "";
    for (const n of e.childNodes) {
      if (n.nodeType === 3) t += n.textContent;
      else if (n.nodeType === 1 && n.getAttribute("aria-hidden") !== "true") t += nom(n);
    }
    return t;
  };
  const lireBarre = () => {
    const navs = [...document.querySelectorAll('nav[aria-label="Sections de Jules"]')];
    const barre = navs[0];
    const lignes = [];
    let rubrique = null;
    const entrees = [];
    for (const e of barre.querySelectorAll("h1,h2,h3,h4,h5,h6,a,button")) {
      if (/^H\d$/.test(e.tagName)) { rubrique = e.textContent; continue; }
      const sp = e.tagName === "BUTTON";
      lignes.push([rubrique, nom(e), sp ? "sous_pages" : "href", sp ? e.dataset.sousPages : e.getAttribute("href")]);
      const chevrons = [...e.querySelectorAll('[aria-hidden="true"]')].filter((s) => s.textContent.trim() === "›");
      const r = e.getBoundingClientRect();
      entrees.push({
        balise: e.tagName.toLowerCase(), libelle: nom(e).trim(), courant: e.getAttribute("aria-current"),
        expanded: e.getAttribute("aria-expanded"), chevron: chevrons.length, poids: getComputedStyle(e).fontWeight,
        haut: r.top, hauteur: r.height,
      });
    }
    const emojisVisibles = [];
    const marche = document.createTreeWalker(barre, NodeFilter.SHOW_TEXT);
    for (let n = marche.nextNode(); n; n = marche.nextNode()) {
      if (/\p{Extended_Pictographic}/u.test(n.textContent) && !n.parentElement.closest('[aria-hidden="true"]')) {
        emojisVisibles.push(n.textContent);
      }
    }
    const tag = document.getElementById("barre-etat-parent");
    return {
      navs: navs.length, lignes, entrees, emojisVisibles,
      pied: barre.querySelector(".barre-pied").textContent,
      titres: [...barre.querySelectorAll("h1,h2,h3,h4,h5,h6")].map((h) => h.textContent),
      parent: {
        cadenas: !!barre.querySelector(".barre-cadenas"),
        texte: tag ? tag.textContent : "",
        label: [...barre.querySelectorAll("[aria-label]")].map((x) => x.getAttribute("aria-label")).join(" "),
      },
    };
  };
"""

ATTENDRE_BARRE = 'await S.attendre(() => document.querySelector("nav[aria-label=\\"Sections de Jules\\"]"), 4000);'


def _barre(banc, chemin: str, **options: Any) -> dict[str, Any]:
    etapes = (
        LIRE_BARRE
        + ATTENDRE_BARRE
        + "await S.pause(300); return { barre: lireBarre(), titre: S.titre(), appels: S.appels() };"
    )
    return banc.jouer(chemin, etapes, budget_ms=8000, **options)


@pytest.fixture(scope="module")
def barres(banc) -> dict[str, dict[str, Any]]:
    return {page: _barre(banc, page) for page in PAGES_ELEVE}


# --- EX-201, EX-202 : meme barre sur les 4 pages, conforme au JSON -----------------------------------


def test_ex201_meme_barre_sur_les_4_pages(barres):
    lignes = {page: r["barre"]["lignes"] for page, r in barres.items()}
    assert all(len(r["barre"]["lignes"]) == len(LIBELLES) for r in barres.values())
    assert lignes["/cours"] == lignes["/"] == lignes["/studio"] == lignes["/discuter"]
    assert all(r["barre"]["navs"] == 1 for r in barres.values())


@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex202_etape1_exactement_la_reference(barres, page):
    comparer_a_la_reference(barres[page]["barre"]["lignes"])
    assert barres[page]["barre"]["titres"] == [r["titre"] for r in REFERENCE["rubriques"]]


# --- EX-203 : entree active --------------------------------------------------------------------------


@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex203_une_seule_entree_active_la_bonne(barres, page):
    actives = [e for e in barres[page]["barre"]["entrees"] if e["courant"] == "page"]
    assert [e["libelle"] for e in actives] == [ACTIVE_PAR_CHEMIN[page]]
    assert int(actives[0]["poids"]) >= 600
    autres = {int(e["poids"]) for e in barres[page]["barre"]["entrees"] if e["courant"] is None}
    assert autres and max(autres) < 600  # style distinct


@pytest.mark.parametrize(
    ("adresse", "attendu"),
    [
        ("/discuter?notion=x", "Discuter avec Jules"),
        ("/cours?matiere=m&notion=n", "Mes leçons"),
        ("/studio?matiere=m#nav=supports/m", "Exercices et supports"),
        ("/?x=1#nav=fiches/histoire", "Mes fiches"),
    ],
)
def test_ex203_parametres_et_fragment_ignores(banc, adresse, attendu):
    r = _barre(banc, adresse)
    assert [e["libelle"] for e in r["barre"]["entrees"] if e["courant"] == "page"] == [attendu]


# --- EX-204 : chaque entree atteignable a l'etape 1 -------------------------------------------------


@pytest.mark.parametrize("page", PAGES_ELEVE)
@pytest.mark.parametrize("entree", [e for r in REFERENCE["rubriques"] for e in r["entrees"]], ids=LIBELLES)
def test_ex204_couple_page_entree(barres, page, entree):
    trouvees = [e for e in barres[page]["barre"]["entrees"] if e["libelle"] == entree["libelle"]]
    assert len(trouvees) == 1
    e = trouvees[0]
    if "sous_pages" in entree:
        assert e["balise"] == "button" and e["expanded"] == "false" and e["chevron"] == 1
    else:
        assert e["balise"] == "a" and e["expanded"] is None and e["chevron"] == 0
    href = {tuple(ligne[1:]) for ligne in barres[page]["barre"]["lignes"]}
    genre = "sous_pages" if "sous_pages" in entree else "href"
    assert (entree["libelle"], genre, entree[genre]) in href


# --- EX-206 : etat de protection de l'espace parent -------------------------------------------------

SESSIONS = {
    "code_parent_non_saisi": {"role": None, "eleve": True, "parent": False},
    "aucun_code_parent": {"role": None, "eleve": True, "parent": True},
    "parent_connecte": {"role": "parent", "eleve": True, "parent": True},
}


@pytest.mark.parametrize("cas", list(SESSIONS))
def test_ex206_trois_reponses_de_session(banc, cas):
    r = _barre(banc, "/", simulees={"/api/session": SESSIONS[cas]})
    etat = r["barre"]["parent"]
    tout = etat["texte"] + " " + etat["label"]
    assert etat["cadenas"] is (cas == "code_parent_non_saisi")
    assert ("code parent" in tout) is (cas == "code_parent_non_saisi")
    assert ("non protégé" in tout) is (cas == "aucun_code_parent")
    if cas == "aucun_code_parent":
        assert "code" not in tout
    # un seul GET /api/session : la barre reutilise la reponse de MS.porte
    assert [a for a in r["appels"] if a["chemin"] == "/api/session"] == [{"methode": "GET", "chemin": "/api/session"}]


SAISIR = (
    r"""
  await S.attendre(() => !S.el("#porte").classList.contains("cache"));
  S.el("#porte-code").value = CODE;
  S.el("#porte-form").requestSubmit();
"""
    + ATTENDRE_BARRE
)


@pytest.mark.parametrize(("code", "cadenas"), [(CODE_ELEVE, True), (CODE_PARENT, False)])
def test_ex206_cas_porte(banc_codes, code, cadenas):
    etapes = (
        LIRE_BARRE
        + SAISIR.replace("CODE", json.dumps(code))
        + "await S.pause(200); return { barre: lireBarre(), appels: S.appels() };"
    )
    r = banc_codes.jouer("/", etapes, budget_ms=10000)
    assert r["barre"]["parent"]["cadenas"] is cadenas
    session = [a["methode"] for a in r["appels"] if a["chemin"] == "/api/session"]
    assert session == ["GET", "POST", "GET"]  # la sequence de la porte, sans appel de la barre


MS_PORTE = r"""
  // `const MS` est une liaison globale de script, pas une propriete de window.
  await S.attendre(() => typeof MS !== "undefined");
  const form = document.createElement("form");
  const champ = document.createElement("input");
  form.appendChild(champ);
  const porte = document.createElement("div");
  const contenu = document.createElement("div");
  const erreur = document.createElement("div");
  document.body.append(form, porte, contenu, erreur);
  const promesse = MS.porte("eleve", { porte, contenu, formulaire: form, champ, erreur });
  SAISIE
  return await promesse;
"""


def test_ex206_ms_porte_acces_deja_accorde_renvoie_etat(banc):
    simulee = {"role": "eleve", "eleve": True, "parent": False}
    r = banc.jouer("/", MS_PORTE.replace("SAISIE", ""), simulees={"/api/session": simulee})
    assert r == simulee


def test_ex206_ms_porte_apres_saisie_renvoie_le_nouvel_etat(banc_codes):
    saisie = (
        "await S.attendre(() => document.activeElement === champ); champ.value = "
        + json.dumps(CODE_ELEVE)
        + "; form.requestSubmit();"
    )
    r = banc_codes.jouer("/", MS_PORTE.replace("SAISIE", saisie), budget_ms=10000)
    assert r == {"role": "eleve", "eleve": True, "parent": False}


# --- EX-208 : accessibilite, controles explicites ---------------------------------------------------


@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex208_structure_emojis_ordre(barres, page):
    b = barres[page]["barre"]
    assert b["emojisVisibles"] == []
    hauts = [e["haut"] for e in b["entrees"]]
    assert hauts == sorted(hauts)  # l'ordre DOM suit l'ordre visuel
    assert all(e["hauteur"] >= 44 for e in b["entrees"])
    assert all(e["libelle"] for e in b["entrees"])


FOCUS = r"""
  const regles = [];
  for (const f of document.styleSheets) {
    for (const r of f.cssRules) {
      if (r.selectorText && r.selectorText.includes(":focus-visible")) regles.push(r.selectorText);
    }
  }
  const cible = (e) => regles.some((sel) => sel.split(",").some((s) => {
    const base = s.trim().replace(/:focus-visible/g, "");
    try { return base && e.matches(base); } catch (_) { return false; }
  }));
  const barre = document.querySelector('nav[aria-label="Sections de Jules"]');
  const entrees = [...barre.querySelectorAll("a,button")];
  const bouton = document.querySelector('button[aria-controls="' + barre.id + '"]');
  const avant = bouton.getAttribute("aria-expanded");
  // Sous 900 px le tiroir ferme est hors du parcours clavier (visibility: hidden) : on l'ouvre d'abord.
  const tiroir = getComputedStyle(bouton).display !== "none";
  if (tiroir) S.clic(bouton);
  const ouvert = bouton.getAttribute("aria-expanded");
  await S.pause(50);
  const resultats = entrees.map((e) => { e.focus(); return { focus: document.activeElement === e, regle: cible(e) }; });
  S.focus(entrees[0]);
  S.echap();
  return { resultats, bouton: cible(bouton), tiroir, avant, ouvert, apres: bouton.getAttribute("aria-expanded"),
           focusRendu: document.activeElement === bouton };
"""


@pytest.mark.parametrize("taille", [(768, 1024), (1280, 800)], ids=["768", "1280"])
@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex208_focus_et_bouton_aria_expanded(banc, page, taille):
    r = banc.jouer(page, ATTENDRE_BARRE + FOCUS, taille=taille, budget_ms=8000)
    assert r["resultats"] and all(x["focus"] and x["regle"] for x in r["resultats"])
    assert r["bouton"]
    if taille[0] < 900:
        assert r["tiroir"] is True
        assert (r["avant"], r["ouvert"], r["apres"]) == ("false", "true", "false")
        assert r["focusRendu"] is True
    else:
        assert r["tiroir"] is False  # barre visible, pas de tiroir a ouvrir


# --- Mise en page : la barre ne doit pas ecraser la zone centrale de /cours et /studio -------------
# Revue N2, tour 1 : sans correctif, a 1000 px, la zone centrale tombait a 132 px (380 px avant N2).
# Entre 900 et 1280 px, elle ne descend pas sous sa largeur d'avant N2 a 1000 px (380 px), et le
# panneau de Jules reste atteignable par son bouton.

ZONE_CENTRALE = {"/cours": ".lecon-zone", "/studio": ".support-zone"}
LARGEUR_MIN_ZONE = 380

MISE_EN_PAGE = r"""
  await S.pause(300);
  const zone = S.rect(ZONE).largeur;
  const bouton = S.el("#menu-jules");
  const panneau = S.el("#panneau-jules");
  const visible = getComputedStyle(bouton).display !== "none";
  const avant = panneau.getBoundingClientRect();
  const visibiliteAvant = getComputedStyle(panneau).visibility;
  // Le temps virtuel du banc (--dump-dom) ne fait pas avancer les transitions CSS : on mesure l'etat final.
  panneau.style.transition = "none";
  if (visible) S.clic(bouton);
  await S.pause(300);
  const apres = panneau.getBoundingClientRect();
  return { zone, visible, panneauAvant: [avant.left, avant.right], panneauApres: [apres.left, apres.right],
           largeurFenetre: innerWidth, ouvert: panneau.classList.contains("ouvert"), visibiliteAvant,
           visibiliteApres: getComputedStyle(panneau).visibility,
           expanded: bouton.getAttribute("aria-expanded"), transform: getComputedStyle(panneau).transform };
"""


@pytest.mark.parametrize("taille", [(960, 800), (1000, 800), (1100, 800), (1280, 800)], ids=lambda t: str(t[0]))
@pytest.mark.parametrize("page", list(ZONE_CENTRALE))
def test_mise_en_page_zone_centrale_avec_barre(banc, page, taille):
    etapes = ATTENDRE_BARRE + MISE_EN_PAGE.replace("ZONE", json.dumps(ZONE_CENTRALE[page]))
    r = banc.jouer(page, etapes, taille=taille, budget_ms=8000)
    assert r["largeurFenetre"] == taille[0]
    assert r["zone"] >= LARGEUR_MIN_ZONE, r
    # Panneau de Jules : soit en colonne visible, soit en tiroir ouvert par son bouton.
    gauche, droite = r["panneauApres"]
    assert 0 <= gauche < droite <= taille[0] + 1, repr(r)
    if r["visible"]:
        # Tiroir ferme : hors ecran a droite et hors du parcours clavier ; ouvert : visible, aria-expanded a jour.
        assert r["panneauAvant"][0] >= taille[0] - 1, repr(r)
        assert (r["visibiliteAvant"], r["visibiliteApres"], r["expanded"]) == ("hidden", "visible", "true"), repr(r)
    else:
        assert r["visibiliteAvant"] == "visible", repr(r)


# --- EX-210 : pied de barre et chemins appeles au chargement ----------------------------------------


@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex210_pied_de_barre_prenom_seul(barres, page):
    prenom = yaml.safe_load((RACINE / "profils" / "exemple.yaml").read_text(encoding="utf-8"))["prenom"]
    assert barres[page]["barre"]["pied"] == prenom


# Mesure sur la base 4bac7fc + N1 (avant cette carte), meme banc, meme jeu de donnees, 27/09/2026.
CHEMINS_AVANT = {
    "/": ["/api/session", "/api/infos", "/api/eleve/fiches_visuelles/notions",
          # premiere fiche de la premiere matiere : geographie depuis les fiches histoire-geo (#71)
          "/api/eleve/fiches_visuelles/notions/geographie-aires-urbaines"],
    "/cours": ["/api/session", "/api/infos", "/api/eleve/cours/parcours"],
    "/studio": ["/api/session", "/api/infos", "/api/eleve/studio/notions", "/api/eleve/studio/revisions"],
    "/discuter": ["/api/session", "/api/infos", "/api/eleve/epreuve/proposition", "/api/conversations"],
    "/parent": ["/api/session", "/api/infos", "/api/parent/modules", "/api/parent/evenements/vigilance",
                "/api/modules/memoire/notes", "/api/conversations", "/api/modules/rapport/jour",
                # ajouté par EX-108 (lot 2 adaptations), décision SPEC
                "/api/parent/adaptations"],
}  # fmt: skip


@pytest.mark.parametrize("page", list(CHEMINS_AVANT))
def test_ex210a_memes_chemins_au_chargement(banc, page):
    r = banc.jouer(page, "await S.pause(2500); return S.api();", budget_ms=8000)
    assert sorted(r) == sorted(CHEMINS_AVANT[page])


def test_ex210_routes_inchangees(banc):
    import urllib.request

    for route in ROUTES_SECTION:
        with urllib.request.urlopen(banc.url + route) as reponse:  # noqa: S310 - serveur local de test
            assert reponse.status == 200, route


# --- EX-211 : titre d'onglet -------------------------------------------------------------------------


@pytest.mark.parametrize("page", PAGES_ELEVE)
def test_ex211_titre_par_page(barres, page):
    assert barres[page]["titre"] == f"Jules - {ACTIVE_PAR_CHEMIN[page]}"


def test_ex211_titre_espace_parent(banc):
    r = banc.jouer("/parent", "await S.attendre(() => S.el('#jour').value); return S.titre();", budget_ms=8000)
    assert r == "Jules - Espace parent"


def test_ex211_mutation_eleve_js_fait_echouer_le_test(banc):
    source = (STATIQUE / "eleve.js").read_text(encoding="utf-8")
    ancre = "    MS.appliquerCouleurs(etat.infos.persona.couleurs);\n"
    assert source.count(ancre) == 1
    mutant = source.replace(ancre, ancre + "    document.title = etat.infos.persona.nom;\n")
    r = _barre(banc, "/discuter", remplaces={"/static/eleve.js": mutant})
    with pytest.raises(AssertionError):
        test_ex211_titre_par_page({"/discuter": r}, "/discuter")
