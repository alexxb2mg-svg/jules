"""Navigation N7 : habillage « Cahier » de la barre (docs/spec/NAVIGATION.md, EX-214, tag spec-nav-fige-2),
branche sur les couleurs par matiere de N7b (EX-215, matieres-couleurs.css).

Tests statiques (CSS, HTML) et scenarios Chromium sur le banc de tests/nav_scenario.py (spec section 6), a
1280 x 800 et, pour le tiroir, a 390 x 844. Les couleurs attendues sont relues dans la table de SPEC
(`docs/spec/matieres-couleurs.json`) ou dans la spec (valeurs de EX-214), jamais recalculees depuis le CSS teste.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from jules.web.app import STATIQUE, creer_app
from tests.nav_scenario import banc_navigation
from tests.test_navigation import RACINE, _tuteur
from tests.test_navigation_n4 import DEBUT, FICHES, memoire

TABLE = json.loads((RACINE / "docs" / "spec" / "matieres-couleurs.json").read_text(encoding="utf-8"))
PAGES_ELEVE = ("accueil.html", "cours.html", "studio.html", "eleve.html")
NAVIGATION_CSS = STATIQUE / "navigation.css"

# Valeurs de EX-214 (spec-nav-fige-2), en hexadecimal.
PAPIER = "#FBF8F1"
BORDURE = "#E9E2D0"
TRAIT_MARGE = "#E7A3AE"
RUBRIQUE = "#6E6A58"
POINTILLE = "#E4DCC6"
CHEVRON = "#7A7562"
ETIQUETTE_FOND, ETIQUETTE_TEXTE = "#FFE3E7", "#8A0F22"
P_PRINCIPALE, P_SECONDAIRE = "#1F4E8C", "#C8102E"


def rgb(hexa: str) -> str:
    """#RRGGBB -> la forme que renvoie getComputedStyle (« rgb(r, g, b) »)."""
    r, g, b = (int(hexa[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgb({r}, {g}, {b})"


def _sans_commentaires(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _regles(css: str) -> list[tuple[str, str]]:
    """(selecteur, corps) de chaque regle, @media aplatis (les blocs imbriques sont relus un a un)."""
    return [(s.strip(), c) for s, c in re.findall(r"([^{}]+)\{([^{}]*)\}", _sans_commentaires(css))]


def _corps(selecteur: str) -> str:
    corps = [c for s, c in _regles(NAVIGATION_CSS.read_text(encoding="utf-8")) if selecteur in s.split(",")]
    assert corps, f"regle introuvable dans navigation.css : {selecteur}"
    return " ".join(corps)


# --- statique : EX-214 -----------------------------------------------------------------------------------


def test_ex214_polices_de_jules():
    style = (STATIQUE / "style.css").read_text(encoding="utf-8")
    assert re.search(r"--police-titre:\s*\"Outfit\"", style)
    assert re.search(r"--police-texte:\s*\"Work Sans\"", style)
    for sel in (".barre-marque", ".barre-rubrique", ".barre-page-titre", ".barre-retour", ".barre-intertitre"):
        assert "font-family: var(--police-titre)" in _corps(sel), sel
    assert "font-family: var(--police-texte)" in _corps(".barre-entree")
    assert re.search(r"font-weight:\s*800", _corps(".barre-marque"))
    assert re.search(r"font-weight:\s*800", _corps(".barre-page-titre"))


def test_ex214_couleurs_de_l_habillage_presentes():
    css = _sans_commentaires(NAVIGATION_CSS.read_text(encoding="utf-8")).upper()
    for couleur in (PAPIER, BORDURE, TRAIT_MARGE, RUBRIQUE, POINTILLE, CHEVRON, ETIQUETTE_FOND, ETIQUETTE_TEXTE):
        assert couleur in css, couleur
    assert f"1PX DASHED {POINTILLE}" in css  # entrees separees par un pointille


def test_ex214_zones_de_clic_et_tailles_en_rem():
    assert re.search(r"min-height:\s*2\.75rem", _corps(".barre-entree"))  # 2.75rem = 44 px
    css = _sans_commentaires(NAVIGATION_CSS.read_text(encoding="utf-8"))
    assert not re.search(r"font-size\s*:[^;]*\d+(?:\.\d+)?px", css)


def test_ex214_trait_de_marge_purement_decoratif():
    corps = _corps(".barre-jules::before")
    assert re.search(r"content:\s*\"\"", corps)  # aucun contenu textuel
    assert "width: 2px" in corps and TRAIT_MARGE in corps.upper()


def test_ex214_aucun_style_en_ligne_dans_les_pages():
    for nom in (*PAGES_ELEVE, "parent.html"):
        assert "style=" not in (STATIQUE / nom).read_text(encoding="utf-8"), nom


# --- statique : branchement de EX-215 ---------------------------------------------------------------------


def test_ex215_couleurs_chargees_avant_la_feuille_de_la_barre():
    lien_couleurs = '<link rel="stylesheet" href="/static/matieres-couleurs.css">'
    lien_barre = '<link rel="stylesheet" href="/static/navigation.css">'
    for nom in PAGES_ELEVE:
        html = (STATIQUE / nom).read_text(encoding="utf-8")
        assert html.count(lien_couleurs) == 1, nom
        assert html.index("/static/style.css") < html.index(lien_couleurs) < html.index(lien_barre), nom
    assert "matieres-couleurs.css" not in (STATIQUE / "parent.html").read_text(encoding="utf-8")


def test_ex215_navigation_css_utilise_les_variables_sans_en_definir():
    css = _sans_commentaires(NAVIGATION_CSS.read_text(encoding="utf-8"))
    assert not re.search(r"--matiere-[\w-]+\s*:", css), "navigation.css ne definit aucune variable --matiere-*"
    en_dur = {c[k].upper() for c in TABLE["matieres"].values() for k in ("fond", "texte", "accent")}
    trouvees = set(re.findall(r"#[0-9A-Fa-f]{6}", css.upper()))
    assert not (en_dur & trouvees), f"couleur de matiere ecrite en dur : {sorted(en_dur & trouvees)}"


def test_ex215_chaque_matiere_de_la_table_a_sa_pastille():
    css = _sans_commentaires(NAVIGATION_CSS.read_text(encoding="utf-8"))
    for mid in TABLE["matieres"]:
        if mid == "_neutre":
            assert "var(--matiere-_neutre-accent)" in _corps(".barre-pastille")
            continue
        motif = rf'\[data-matiere="{re.escape(mid)}"\]\s*\{{[^}}]*var\(--matiere-{re.escape(mid)}-accent\)'
        assert re.search(motif, css), mid


# --- scenarios Chromium ------------------------------------------------------------------------------------

# Reponse simulee de la liste des fiches : 4 matieres de la table, 1 inconnue (couleurs _neutre attendues).
MATIERE_INCONNUE = "astronomie"
FICHES_N7 = {
    "matieres": [
        {
            "id": "mathematiques",
            "nom": "Mathématiques",
            "notions": [
                {"id": "thales", "titre": "Théorème de Thalès", "chapitre": "Géométrie"},
                {"id": "pythagore", "titre": "Théorème de Pythagore", "chapitre": "Géométrie"},
                {"id": "fonctions", "titre": "Fonctions affines", "chapitre": "Fonctions"},
            ],
        },
        {"id": "francais", "nom": "Français", "notions": [{"id": "fr1", "titre": "Le récit", "chapitre": "Lire"}]},
        {"id": "histoire", "nom": "Histoire", "notions": [{"id": "h1", "titre": "La guerre froide", "chapitre": "XXe"}]},
        {"id": "arts-plastiques", "nom": "Arts plastiques", "notions": [{"id": "ap1", "titre": "La couleur"}]},
        {"id": MATIERE_INCONNUE, "nom": "Astronomie", "notions": [{"id": "as1", "titre": "Les planètes"}]},
    ]
}


@pytest.fixture(scope="module")
def banc(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory, None)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n7")) as b:
            yield b
    finally:
        tuteur.fermer()


# Releve de chaque element cliquable visible de la barre (a, button) : hauteur, chevron, aria-current,
# graisse, police, et quelques couleurs.
RELEVE = r"""
  await document.fonts.ready;
  const barre = S.el("#barre-jules");
  const visible = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0
    && getComputedStyle(e).visibility !== "hidden"; };
  const cliquables = () => [...barre.querySelectorAll("a, button")].filter(visible).map((e) => {
    const s = getComputedStyle(e);
    const chev = e.querySelector(".barre-chevron");
    return {
      texte: (e.querySelector(".barre-libelle") || e).textContent.trim(),
      classes: e.className, hauteur: e.getBoundingClientRect().height,
      sousPages: e.dataset.sousPages || null, matiere: e.dataset.matiere || null, chapitre: e.dataset.chapitre || null,
      element: e.classList.contains("barre-element"), retour: e.classList.contains("barre-retour"),
      chevron: chev && visible(chev) ? { texte: chev.textContent, couleur: getComputedStyle(chev).color } : null,
      courant: e.getAttribute("aria-current"), expanded: e.getAttribute("aria-expanded"),
      graisse: Number(s.fontWeight), police: s.fontFamily, couleur: s.color,
    };
  });
  const page = () => { const p = barre.querySelector(".barre-sous-page:not([hidden]) .barre-page");
    return p ? Number(p.dataset.etape) : 1; };
  const titre = () => { const t = barre.querySelector("#barre-page-titre"); if (!t) return null;
    const s = getComputedStyle(t); return { texte: t.textContent, police: s.fontFamily, graisse: Number(s.fontWeight) }; };
  const fil = () => { const f = barre.querySelector(".barre-sous-page:not([hidden]) .barre-fil");
    return f ? f.textContent : null; };
  const pastilles = () => [...barre.querySelectorAll(".barre-matiere")].map((b) => {
    const s = getComputedStyle(b.querySelector(".barre-pastille"));
    return { matiere: b.dataset.matiere, fond: s.backgroundColor, rayon: s.borderTopLeftRadius,
      largeur: s.width, hauteur: s.height };
  });
  const releve = () => ({ etape: page(), cliquables: cliquables(), titre: titre(), fil: fil() });
"""


def jouer(banc, chemin: str, etapes: str, **options: Any) -> Any:
    options.setdefault("budget_ms", 10000)
    options.setdefault("avant", memoire(None))
    options.setdefault("simulees", {FICHES: FICHES_N7})
    return banc.jouer(chemin, DEBUT + RELEVE + etapes, **options)


PARCOURS_FICHES = r"""
  const r = {};
  r.etape1 = releve();
  rubrique("fiches").click(); await attendreEtape(2);
  r.etape2 = releve(); r.pastilles = pastilles();
  matiere("mathematiques").click(); await attendreEtape(3);
  r.etape3 = releve();
  S.clic('#barre-jules [data-chapitre="Géométrie"]'); await attendreEtape(4);
  r.etape4 = releve();
  return r;
"""


def _verifier_cliquables(releve: dict[str, Any]) -> None:
    trop_petits = [(c["texte"], c["hauteur"]) for c in releve["cliquables"] if c["hauteur"] < 44]
    assert not trop_petits, f"etape {releve['etape']} : zones de clic < 44 px : {trop_petits}"
    for c in releve["cliquables"]:
        # Chevron exactement sur ce qui ouvre une petite page : rubrique a sous-pages, matiere, chapitre.
        ouvre = bool(c["sousPages"] or c["matiere"] or c["chapitre"])
        assert (c["chevron"] is not None) is ouvre, (releve["etape"], c["texte"], c["chevron"])
        if c["chevron"]:
            assert c["chevron"]["texte"] == "›"
            assert c["chevron"]["couleur"] == rgb(CHEVRON)


@pytest.mark.parametrize("chemin", ["/", "/cours", "/studio", "/discuter"])
def test_ex214_etape1_cliquables_chevrons_et_entree_active(banc, chemin):
    r = jouer(banc, chemin, "return releve();")
    assert r["etape"] == 1
    _verifier_cliquables(r)
    entrees = [c for c in r["cliquables"] if "barre-entree" in c["classes"]]
    assert [c["texte"] for c in entrees] == [
        "Mes fiches", "Mes leçons", "Exercices et supports", "Discuter avec Jules", "Espace parent",
    ]
    actives = [c for c in entrees if c["courant"] == "page"]
    assert len(actives) == 1
    assert actives[0]["graisse"] >= 600 and actives[0]["couleur"] == rgb(P_PRINCIPALE)
    for c in entrees:
        assert "Work Sans" in c["police"], c
        if c["courant"] != "page":
            assert c["graisse"] < 600, c


def test_ex214_parcours_des_4_etapes_a_1280(banc):
    r = jouer(banc, "/cours", PARCOURS_FICHES)
    for etape in ("etape1", "etape2", "etape3", "etape4"):
        _verifier_cliquables(r[etape])
    # etape 2 : une matiere par ligne, pastille carree, bouton retour Outfit marine
    assert [c["matiere"] for c in r["etape2"]["cliquables"] if c["matiere"]] == [m["id"] for m in FICHES_N7["matieres"]]
    retours = [c for c in r["etape2"]["cliquables"] if c["retour"]]
    assert [c["texte"] for c in retours] == ["← Menu"]
    assert "Outfit" in retours[0]["police"] and retours[0]["couleur"] == rgb(P_PRINCIPALE)
    # etapes 2 a 4 : titre Outfit 800 ; fil d'Ariane textuel aux etapes 3 et 4
    for etape in ("etape2", "etape3", "etape4"):
        assert "Outfit" in r[etape]["titre"]["police"] and r[etape]["titre"]["graisse"] == 800, etape
    assert r["etape3"]["titre"]["texte"] == "Mathématiques" and r["etape3"]["fil"] == "Mes fiches"
    assert r["etape4"]["titre"]["texte"] == "Géométrie" and r["etape4"]["fil"] == "Mes fiches › Mathématiques"
    assert [c["texte"] for c in r["etape3"]["cliquables"] if c["retour"]] == ["← Matières"]
    assert [c["texte"] for c in r["etape4"]["cliquables"] if c["retour"]] == ["← Chapitres"]
    # etape 4 : les fiches sont des liens, sans chevron
    elements = [c for c in r["etape4"]["cliquables"] if c["element"]]
    assert [c["texte"] for c in elements] == ["Théorème de Thalès", "Théorème de Pythagore"]


def test_ex215_pastille_de_la_couleur_accent_et_neutre_pour_une_matiere_inconnue(banc):
    r = jouer(banc, "/cours", PARCOURS_FICHES)
    assert MATIERE_INCONNUE not in TABLE["matieres"]
    for p in r["pastilles"]:
        cle = p["matiere"] if p["matiere"] in TABLE["matieres"] else "_neutre"
        assert p["fond"] == rgb(TABLE["matieres"][cle]["accent"]), p
        assert p["largeur"] == p["hauteur"] == "10px", p  # 0.625rem
        assert p["rayon"] not in ("50%", "0px"), p  # carre aux coins arrondis, pas un rond
    fonds = {p["matiere"]: p["fond"] for p in r["pastilles"]}
    assert fonds[MATIERE_INCONNUE] == rgb(TABLE["matieres"]["_neutre"]["accent"])
    assert len(set(fonds.values())) == len(fonds)  # chaque matiere a sa teinte


def test_ex214_identite_cahier_mesuree(banc):
    r = jouer(
        banc,
        "/cours",
        r"""
        const s = (e, p) => getComputedStyle(e, p || null);
        const marque = S.el("#barre-jules .barre-marque");
        const point = S.el("#barre-jules .barre-marque-point");
        const rub = S.el("#barre-jules .barre-rubrique");
        const ligne = S.el("#barre-jules .barre-ligne");
        const active = S.el('#barre-jules [aria-current="page"]');
        return {
          fond: s(barre).backgroundColor, bord: s(barre).borderRightColor,
          trait: { contenu: s(barre, "::before").content, fond: s(barre, "::before").backgroundColor,
                   largeur: s(barre, "::before").width },
          marque: { police: s(marque).fontFamily, graisse: Number(s(marque).fontWeight), couleur: s(marque).color },
          point: { texte: point.textContent, couleur: s(point).color },
          rubrique: { police: s(rub).fontFamily, casse: s(rub).textTransform, couleur: s(rub).color,
                      espacement: s(rub).letterSpacing },
          ligne: { style: s(ligne).borderBottomStyle, couleur: s(ligne).borderBottomColor },
          pastilleActive: { fond: s(active, "::before").backgroundColor, rayon: s(active, "::before").borderTopLeftRadius },
          polices: { outfit: document.fonts.check("800 16px Outfit"), work: document.fonts.check("400 16px 'Work Sans'") },
        };
        """,
    )
    assert r["fond"] == rgb(PAPIER) and r["bord"] == rgb(BORDURE)
    assert r["trait"] == {"contenu": '""', "fond": rgb(TRAIT_MARGE), "largeur": "2px"}
    assert "Outfit" in r["marque"]["police"] and r["marque"]["graisse"] == 800
    assert r["marque"]["couleur"] == rgb(P_PRINCIPALE)
    assert r["point"] == {"texte": ".", "couleur": rgb(P_SECONDAIRE)}
    assert "Outfit" in r["rubrique"]["police"] and r["rubrique"]["casse"] == "uppercase"
    assert r["rubrique"]["couleur"] == rgb(RUBRIQUE) and r["rubrique"]["espacement"] != "normal"
    assert r["ligne"] == {"style": "dashed", "couleur": rgb(POINTILLE)}
    assert r["pastilleActive"] == {"fond": rgb(P_SECONDAIRE), "rayon": "50%"}
    assert r["polices"] == {"outfit": True, "work": True}  # polices de Jules chargees, pas celles de secours


def test_ex214_sans_le_trait_de_marge_l_etat_des_entrees_est_identique(banc):
    """Le trait de marge ne porte aucune information : on retire sa regle (CSSOM, feuille chargee) et l'etat
    de chaque entree (aria-*, graisse, chevron) reste le meme, aux etapes 1 et 2."""
    r = jouer(
        banc,
        "/cours",
        r"""
        const etat = () => cliquables().map((c) => [c.texte, c.courant, c.expanded, c.graisse, !!c.chevron]);
        const retirer = () => {
          let n = 0;
          for (const f of document.styleSheets) {
            if (!(f.href || "").endsWith("/static/navigation.css")) continue;
            for (let i = f.cssRules.length - 1; i >= 0; i--) {
              if (f.cssRules[i].selectorText === ".barre-jules::before") { f.deleteRule(i); n++; }
            }
          }
          return n;
        };
        const largeurTrait = () => getComputedStyle(barre, "::before").width;
        const avant1 = etat();
        rubrique("fiches").click(); await attendreEtape(2);
        matiere("histoire").click(); await attendreEtape(3);
        retour().click(); await attendreEtape(2);
        const avant2 = etat(), traitAvant = largeurTrait();
        const retirees = retirer();
        const apres2 = etat(), traitApres = getComputedStyle(barre, "::before").content;
        retour().click(); await attendreEtape(1);
        return { avant1, apres1: etat(), avant2, apres2, retirees, traitAvant, traitApres };
        """,
    )
    assert r["retirees"] == 1
    assert r["traitAvant"] == "2px" and r["traitApres"] == "none"
    assert r["apres2"] == r["avant2"]
    assert any(e[1] == "true" for e in r["avant2"])  # matiere selectionnee (histoire) : l'etat est bien releve
    # etape 1 : avant (trait present) et apres (trait retire), meme rubrique fermee
    assert [e for e in r["apres1"] if e[0] != "Mes fiches"] == [e for e in r["avant1"] if e[0] != "Mes fiches"]
    assert [e[:2] + e[3:] for e in r["apres1"]] == [e[:2] + e[3:] for e in r["avant1"]]


def test_ex214_tiroir_a_390_zones_de_clic_et_chevrons(banc):
    r = jouer(
        banc,
        "/cours",
        r"""
        barre.style.transition = "none";
        S.clic("#barre-jules-bouton"); await S.pause(50);
        const bouton = S.el("#barre-jules-bouton").getBoundingClientRect().height;
        const r = { bouton, etape1: releve() };
        rubrique("fiches").click(); await attendreEtape(2);
        r.etape2 = releve();
        return r;
        """,
        taille=(390, 844),
    )
    assert r["bouton"] >= 44
    _verifier_cliquables(r["etape1"])
    _verifier_cliquables(r["etape2"])
    assert len([c for c in r["etape2"]["cliquables"] if c["matiere"]]) == len(FICHES_N7["matieres"])
