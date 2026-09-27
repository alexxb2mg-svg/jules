"""EX-105 (docs/spec/ADAPTATIONS-LOT2.md) : les leviers CSS s'appliquent par variables CSS sur <body>
dans les pages de l'eleve et, dans les outils, par le message `{type: "adaptations", leviers}` de la
poignee de main (lot 1, EX-001 a 003). Chaque outil applique les leviers qu'il connait et ignore les
autres.

- `jules.leviers.leviers_resolus` et `leviers_css` : valeurs -> leviers retenus (valeurs brutes) et
  variables CSS derivees (tests unitaires) ;
- `/api/infos` expose `leviers` et `leviers_css` (vides tant que tout est neutre, EX-102), et plus
  aucune cle `adaptations` (decision SPEC du 27/09) ;
- vrai Chromium, vrai serveur Jules : les vraies pages (accueil, cours, studio, discuter), servies avec
  une sonde qui relit les styles calcules (getComputedStyle), une fois avec des valeurs non neutres
  et une fois au neutre ; les trois vrais outils, dans un cadre de meme origine, avec les leviers
  lus dans /api/infos, des leviers hors plage, et sans levier.

Le retour au neutre « identique a origin/main » est aussi mesure sur tout le DOM, hors test
(releve des styles calcules avant/apres, voir le commentaire de la carte EX-105).

EX-012 : les tests navigateur ne comptent que s'ils ont tourne (JULES_CHROMIUM defini, `pytest -rs`).
"""

from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.testclient import TestClient

from jules.chantier_visuel import _chromium
from jules.leviers import VARIABLE_ECHELLE, charger_leviers, leviers_css, leviers_resolus
from tests.test_outils_hote import _port_libre, temps_virtuel_hors_ci_linux

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"
OUTILS_REELS = ("calculatrice", "frise-chronologique", "lexique")
PAGES = {"accueil": "accueil.html", "cours": "cours.html", "studio": "studio.html", "discuter": "eleve.html"}

# Valeurs non neutres : les maxima des plages du §2 pour les nombres, un choix non neutre sinon.
REGLAGES: dict[str, Any] = {
    "espacement-lettres": 0.12,
    "espacement-mots": 0.16,
    "interligne": 2.0,
    "longueur-ligne": 60,
    "taille-texte": 1.6875,
    "police": "verdana",
    "fond": "creme",
    "surlignage-mots-cles": True,
    "reperes-rang-chiffres": True,
}
CREME = "rgb(251, 245, 230)"


# --- leviers_resolus et leviers_css ------------------------------------------------------------------------
@pytest.fixture(scope="module")
def leviers():
    return charger_leviers()


def test_tout_neutre_ne_pose_rien(leviers):
    neutres = {i: levier.neutre for i, levier in leviers.items()}
    for valeurs in (neutres, {}):
        assert leviers_resolus(leviers, valeurs) == {}
        assert leviers_css(leviers, valeurs) == {}


def test_valeurs_non_neutres_donnent_leurs_variables(leviers):
    assert leviers_resolus(leviers, REGLAGES) == REGLAGES
    assert leviers_css(leviers, REGLAGES) == {
        "--adapt-espacement-lettres": "0.12em",
        "--adapt-espacement-mots": "0.16em",
        "--adapt-interligne": "2",
        "--adapt-longueur-ligne": "60ch",
        "--adapt-taille-texte": "1.6875rem",
        VARIABLE_ECHELLE: "1.5",
        "--adapt-police": 'Verdana, "DejaVu Sans", sans-serif',
        "--adapt-fond": "#FBF5E6",
        "--adapt-surlignage-mots-cles": "1",
        "--adapt-reperes-rang-chiffres": "1",
    }


def test_valeurs_refusees(leviers):
    refusees = {
        "espacement-lettres": 0.5,  # hors plage
        "interligne": 1.2,  # sous le plancher
        "longueur-ligne": 0,  # nulle
        "taille-texte": "grande",  # mauvais type
        "police": "opendyslexic",  # hors liste fermee (EX-107)
        "fond": "noir",
        "surlignage-mots-cles": "oui",  # booleen attendu
        "reperes-rang-chiffres": False,  # neutre
        "levier-inconnu": 1,
    }
    assert leviers_resolus(leviers, refusees) == {}
    assert leviers_css(leviers, refusees) == {}


def test_leviers_sans_canal_css_restent_dans_leviers_sans_variable(leviers):
    # `infos.leviers` porte tous les leviers regles (EX-109 y lit lecture-vocale) ; `leviers_css`
    # n'en derive que les variables des leviers du canal css.
    valeurs = {"densite": "un-exercice", "lecture-vocale": "proposee", "phrases-courtes": True}
    assert leviers_resolus(leviers, valeurs) == valeurs
    assert leviers_css(leviers, valeurs) == {}


def test_api_infos_expose_les_adaptations(tuteur, monkeypatch):
    from jules.web.app import creer_app

    client = TestClient(creer_app(tuteur))
    infos = client.get("/api/infos").json()
    assert (infos["leviers"], infos["leviers_css"]) == ({}, {})
    assert "adaptations" not in infos
    monkeypatch.setattr(type(tuteur), "valeurs_leviers", lambda self: {"espacement-mots": 0.5, "police": "defaut"})
    infos = client.get("/api/infos").json()
    assert infos["leviers"] == {"espacement-mots": 0.5}  # police au neutre : absente
    assert infos["leviers_css"] == {"--adapt-espacement-mots": "0.5em"}


def test_les_pages_eleve_chargent_adaptations_css_et_l_appliquent():
    for nom, html in PAGES.items():
        texte = (STATIQUE / html).read_text(encoding="utf-8")
        assert '<link rel="stylesheet" href="/static/adaptations.css">' in texte, nom
        feuilles = re.findall(r'href="/static/([a-z-]+\.css)"', texte)
        assert feuilles[-1] == "adaptations.css", f"{nom} : adaptations.css doit etre la derniere feuille"
    for js in ("accueil.js", "cours.js", "studio.js", "eleve.js"):
        assert "MS.appliquerLeviers(etat.infos)" in (STATIQUE / js).read_text(encoding="utf-8"), js
    # la page de cours transmet aux outils les valeurs retenues
    assert "leviers: etat.leviers || {}" in (STATIQUE / "cours.js").read_text(encoding="utf-8")


def test_toutes_les_tailles_de_police_suivent_l_echelle():
    fautes = []
    for css in sorted(STATIQUE.glob("*.css")):
        for n, ligne in enumerate(css.read_text(encoding="utf-8").splitlines(), 1):
            for m in re.finditer(r"font(?:-size)?\s*:([^;{}]*)", ligne):
                if re.search(r"\d(?:\.\d+)?rem", m.group(1)) and "var(--adapt-echelle-texte, 1)" not in m.group(1):
                    fautes.append(f"{css.name}:{n}: {ligne.strip()}")
    assert not fautes, "taille en rem sans l'echelle du levier taille-texte :\n" + "\n".join(fautes)


# --- navigateur --------------------------------------------------------------------------------
# Sonde ajoutee a la fin des vraies pages : releve les styles calcules une fois la page demarree.
SONDE_PAGE_JS = """"use strict";
(function () {
  function mesure(el) {
    if (!el) return null;
    var cs = getComputedStyle(el);
    return {
      fontSize: parseFloat(cs.fontSize), letterSpacing: cs.letterSpacing, wordSpacing: cs.wordSpacing,
      lineHeight: cs.lineHeight, fontFamily: cs.fontFamily, backgroundColor: cs.backgroundColor,
      maxWidth: cs.maxWidth
    };
  }
  setTimeout(function () {
    var corps = document.body;
    var bulle = document.createElement("div");
    bulle.className = "bulle";
    bulle.innerHTML = "<p>Un <strong>mot</strong></p>";
    corps.appendChild(bulle);
    var attributs = corps.getAttributeNames().filter(function (n) { return n.indexOf("data-adapt-") === 0; });
    var r = {
      attributs: attributs.sort(),
      racine: parseFloat(getComputedStyle(document.documentElement).fontSize),
      body: mesure(corps),
      titre: mesure(document.querySelector(".marque, h1, h2")),
      paragraphe: mesure(bulle.querySelector("p")),
      fort: mesure(bulle.querySelector("strong")),
      echelle: getComputedStyle(corps).getPropertyValue("--adapt-echelle-texte").trim()
    };
    corps.removeChild(bulle);
    document.documentElement.setAttribute("data-resultat", JSON.stringify(r));
  }, 4000);
})();
"""

# Page d'essai des outils : chaque outil reel dans un cadre de meme origine (pour relire son DOM),
# trois cas par outil : leviers de /api/infos, leviers hors plage, aucun levier.
SONDE_OUTILS_JS = """"use strict";
(function () {
  var OUTILS = __OUTILS__;
  var HORS_PLAGE = { "espacement-lettres": 5, "interligne": 1, "taille-texte": 9, "police": "comic",
    "fond": "noir", "reperes-rang-chiffres": "oui", "levier-inconnu": 1 };
  var cadres = [];
  // Fond reellement peint derriere un element : on remonte jusqu'au premier ancetre qui porte une
  // couleur de fond non transparente ou une image de fond (degrade) ; on rend toutes ses couleurs.
  function fondsPeints(doc, el) {
    for (var n = el; n && n.nodeType === 1; n = n.parentElement) {
      var cs = doc.defaultView.getComputedStyle(n);
      var couleurs = [];
      if (cs.backgroundImage && cs.backgroundImage !== "none") {
        couleurs = cs.backgroundImage.match(/rgba?\\([^)]*\\)/g) || [];
      }
      if (!/^rgba\\(.*,\\s*0\\)$/.test(cs.backgroundColor) && cs.backgroundColor !== "transparent") {
        couleurs.push(cs.backgroundColor);
      }
      if (couleurs.length) return couleurs;
    }
    return [];
  }
  function mesure(doc) {
    // calculatrice : saisir 456 pour avoir un chiffre de chaque rang a l'ecran
    var touches = Array.prototype.slice.call(doc.querySelectorAll("#pave button"));
    ["4", "5", "6"].forEach(function (chiffreSaisi) {
      touches.forEach(function (b) { if (b.textContent === chiffreSaisi) b.click(); });
    });
    var corps = doc.body, cs = doc.defaultView.getComputedStyle(corps);
    var chiffre = doc.querySelector("#ecran span");
    return {
      cache: corps.hidden,
      adaptations: doc.documentElement.getAttribute("data-adaptations"),
      attributs: corps.getAttributeNames().filter(function (n) { return n.indexOf("data-adapt-") === 0; }).sort(),
      racine: parseFloat(doc.defaultView.getComputedStyle(doc.documentElement).fontSize),
      fontSize: parseFloat(cs.fontSize), letterSpacing: cs.letterSpacing, wordSpacing: cs.wordSpacing,
      lineHeight: cs.lineHeight, fontFamily: cs.fontFamily, backgroundColor: cs.backgroundColor,
      titreEspacement: doc.defaultView.getComputedStyle(doc.querySelector("h1")).letterSpacing,
      chiffres: Array.prototype.map.call(doc.querySelectorAll("#ecran span"), function (s) {
        return { classe: s.className, couleur: doc.defaultView.getComputedStyle(s).color,
          fonds: fondsPeints(doc, s) };
      }),
      chiffre: chiffre ? { classe: chiffre.className, couleur: doc.defaultView.getComputedStyle(chiffre).color } : null,
      ecran: doc.getElementById("ecran") ? doc.defaultView.getComputedStyle(doc.getElementById("ecran")).color : null,
      touchePolice: touches.length ? doc.defaultView.getComputedStyle(touches[0]).fontFamily : null
    };
  }
  window.addEventListener("message", function (e) {
    for (var i = 0; i < cadres.length; i++) {
      var c = cadres[i];
      if (c.iframe.contentWindow !== e.source || !e.data || e.data.type !== "pret") continue;
      c.iframe.contentWindow.postMessage({ type: "adaptations", leviers: c.leviers }, "*");
    }
  });
  fetch("/api/infos").then(function (r) { return r.json(); }).then(function (infos) {
    var cas = { reglages: infos.leviers, "hors-plage": HORS_PLAGE, neutre: {} };
    OUTILS.forEach(function (outil) {
      Object.keys(cas).forEach(function (nom) {
        var c = { outil: outil, cas: nom, leviers: cas[nom] };
        c.iframe = document.createElement("iframe");
        c.iframe.src = "/essai-cadre/" + outil;
        cadres.push(c);
        document.getElementById("zone").appendChild(c.iframe);
      });
    });
    setTimeout(function () {
      var r = cadres.map(function (c) {
        return { outil: c.outil, cas: c.cas, mesure: mesure(c.iframe.contentDocument) };
      });
      document.body.setAttribute("data-resultat", JSON.stringify(r));
    }, 2500);
  });
})();
""".replace("__OUTILS__", json.dumps(list(OUTILS_REELS)))

PAGE_OUTILS = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>essai</title></head>
<body><div id="zone"></div><script src="/sonde-outils.js"></script></body></html>"""

ENTETES_CADRE = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; base-uri 'self'; frame-ancestors 'self'"
    ),
    "X-Frame-Options": "SAMEORIGIN",
}


def _serveur(projet: Path, brut_config: dict, valeurs: dict[str, Any]):
    import uvicorn

    from jules.config import depuis_dict
    from jules.llm.factice import Brique as Factice
    from jules.moteur import Tuteur
    from jules.web.app import creer_app

    brut_config["modules"] = [*brut_config["modules"], {"id": "outils"}]
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    tuteur.valeurs_leviers = lambda: dict(valeurs)  # type: ignore[method-assign]
    app = creer_app(tuteur)

    pages = {}
    for nom, html in PAGES.items():
        texte = (STATIQUE / html).read_text(encoding="utf-8")
        pages[nom] = texte.replace("</body>", '<script src="/sonde-page.js"></script>\n</body>', 1)
    cadres = {}
    for ident in OUTILS_REELS:
        html = (projet / "extensions" / ident / "index.html").read_text(encoding="utf-8")
        cadres[ident] = html.replace("<head>", f'<head><base href="/api/eleve/outils/{ident}/">', 1)
    scripts = {"sonde-page.js": SONDE_PAGE_JS, "sonde-outils.js": SONDE_OUTILS_JS}

    @app.get("/essai-page/{nom}", response_class=HTMLResponse)
    def essai_page(nom: str) -> HTMLResponse:
        if nom not in pages:
            raise HTTPException(status_code=404)
        return HTMLResponse(pages[nom])

    @app.get("/essai-outils", response_class=HTMLResponse)
    def essai_outils() -> HTMLResponse:
        return HTMLResponse(PAGE_OUTILS, headers=ENTETES_CADRE)

    @app.get("/essai-cadre/{outil_id}", response_class=HTMLResponse)
    def essai_cadre(outil_id: str) -> HTMLResponse:
        if outil_id not in cadres:
            raise HTTPException(status_code=404)
        return HTMLResponse(cadres[outil_id], headers=ENTETES_CADRE)

    @app.get("/{nom}.js")
    def essai_js(nom: str) -> Response:
        script = scripts.get(f"{nom}.js")
        if script is None:
            raise HTTPException(status_code=404)
        return Response(script, media_type="text/javascript; charset=utf-8")

    port = _port_libre()
    serveur_uv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    fil = threading.Thread(target=serveur_uv.run, daemon=True)
    fil.start()
    limite = time.time() + 20
    while not serveur_uv.started and time.time() < limite:
        time.sleep(0.05)
    assert serveur_uv.started, "serveur Jules non demarre"
    return f"http://127.0.0.1:{port}", serveur_uv, fil, tuteur


@pytest.fixture
def serveur_regle(projet, brut_config):
    base, uv, fil, tuteur = _serveur(projet, brut_config, REGLAGES)
    yield base
    uv.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


@pytest.fixture
def serveur_neutre(projet, brut_config):
    base, uv, fil, tuteur = _serveur(projet, brut_config, {})
    yield base
    uv.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


def _resultat(url: str, profil: Path) -> Any:
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent (definir JULES_CHROMIUM)")
    options = ["--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={profil}"]
    options += ["--window-size=1280,900", "--virtual-time-budget=15000", "--dump-dom"]
    fini = subprocess.run(  # noqa: S603 - navigateur local, arguments fixes
        [navigateur, *options, url], capture_output=True, text=True, encoding="utf-8", timeout=180, check=False
    )
    sortie = fini.stdout
    trouve = re.search(r'data-resultat="([^"]*)"', sortie)
    assert trouve, f"code {fini.returncode}\n{fini.stderr[-2000:]}\n{sortie[-2000:]}"
    return json.loads(trouve.group(1).replace("&quot;", '"').replace("&amp;", "&"))


def _contraste(couleur: str, fond: str) -> float:
    """Rapport de contraste WCAG 2.2 entre deux couleurs CSS calculees « rgb(r, g, b) »."""

    def luminance(css: str) -> float:
        r, g, b = (int(x) / 255 for x in re.findall(r"\d+", css)[:3])
        lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    claire, sombre = sorted((luminance(couleur), luminance(fond)), reverse=True)
    return (claire + 0.05) / (sombre + 0.05)


def test_contraste_mesure_comme_le_wcag():
    assert _contraste("rgb(0, 0, 0)", "rgb(255, 255, 255)") == pytest.approx(21)
    assert _contraste("rgb(118, 118, 118)", "rgb(255, 255, 255)") == pytest.approx(4.54, abs=0.01)


def _pire_contraste(couleur: str, fonds: list[str]) -> float:
    """Pire contraste d'une couleur contre toutes les couleurs du fond peint derriere elle (une
    couleur unie ou chaque arret d'un degrade). Un fond absent ou transparent n'est jamais mesure :
    le test echoue au lieu de passer en silence contre rgba(0, 0, 0, 0)."""
    assert fonds, f"aucun fond peint derriere {couleur}"
    for fond in fonds:
        valeurs = re.findall(r"[\d.]+", fond)
        assert len(valeurs) == 3 or float(valeurs[3]) == 1, f"fond non opaque, contraste non mesurable : {fond}"
    return min(_contraste(couleur, fond) for fond in fonds)


def test_pire_contraste_mesure_chaque_couleur_du_degrade():
    # ecran sombre de la calculatrice : degrade #1e293b -> #0f172a
    degrade = ["rgb(30, 41, 59)", "rgb(15, 23, 42)"]
    assert _pire_contraste("rgb(39, 103, 73)", degrade) < 4.5  # ancien vert #276749 : illisible
    assert _pire_contraste("rgb(39, 103, 73)", degrade) == pytest.approx(
        _contraste("rgb(39, 103, 73)", "rgb(30, 41, 59)")
    )
    for fond in ([], ["rgba(0, 0, 0, 0)"]):
        with pytest.raises(AssertionError):
            _pire_contraste("rgb(255, 255, 255)", fond)


def _px(valeur: str) -> float:
    assert valeur.endswith("px"), valeur
    return float(valeur[:-2])


ATTRIBUTS_PAGE = sorted(f"data-adapt-{i}" for i in REGLAGES)


@temps_virtuel_hors_ci_linux
@pytest.mark.parametrize("page", sorted(PAGES))
def test_page_avec_leviers_regles(serveur_regle, tmp_path, page):
    r = _resultat(f"{serveur_regle}/essai-page/{page}", tmp_path / "profil")
    assert r["attributs"] == ATTRIBUTS_PAGE
    assert r["echelle"] == "1.5"
    assert r["racine"] == 16  # la racine ne bouge pas : l'echelle passe par les tailles des feuilles
    corps = r["body"]
    assert corps["fontSize"] == pytest.approx(18 * 1.5)  # taille-texte 1,6875rem = 1,5 x 1,125rem
    assert _px(corps["letterSpacing"]) == pytest.approx(0.12 * corps["fontSize"], abs=0.01)
    assert _px(corps["wordSpacing"]) == pytest.approx(0.16 * corps["fontSize"], abs=0.01)
    assert _px(corps["lineHeight"]) == pytest.approx(2.0 * corps["fontSize"], abs=0.01)
    assert corps["fontFamily"].startswith("Verdana")
    assert corps["backgroundColor"] == CREME
    # les titres, qui fixent leur propre espacement, suivent aussi le levier ; ils gardent leur police
    titre = r["titre"]
    assert _px(titre["letterSpacing"]) == pytest.approx(0.12 * titre["fontSize"], abs=0.01)
    assert _px(titre["lineHeight"]) == pytest.approx(2.0 * titre["fontSize"], abs=0.01)
    assert titre["fontFamily"].startswith('"Outfit"') or titre["fontFamily"].startswith("Outfit")
    # longueur de ligne sur les paragraphes ; surligneur sur le gras des bulles
    paragraphe = r["paragraphe"]
    assert _px(paragraphe["maxWidth"]) > 0 and paragraphe["maxWidth"] != "none"
    assert r["fort"]["backgroundColor"] == "rgba(255, 214, 102, 0.45)"


@temps_virtuel_hors_ci_linux
@pytest.mark.parametrize("page", sorted(PAGES))
def test_page_au_neutre(serveur_neutre, tmp_path, page):
    r = _resultat(f"{serveur_neutre}/essai-page/{page}", tmp_path / "profil")
    assert r["attributs"] == []
    assert r["echelle"] == ""
    corps = r["body"]
    assert r["racine"] == 16 and corps["fontSize"] == 18
    assert corps["letterSpacing"] == "normal" and corps["wordSpacing"] == "0px"
    assert _px(corps["lineHeight"]) == pytest.approx(1.55 * 18, abs=0.01)
    assert corps["fontFamily"].startswith('"Work Sans"')
    assert corps["backgroundColor"] == "rgb(255, 255, 255)"
    assert r["paragraphe"]["maxWidth"] == "none"
    assert r["fort"]["backgroundColor"] == "rgba(0, 0, 0, 0)"


@temps_virtuel_hors_ci_linux
def test_les_outils_appliquent_les_leviers_qu_ils_connaissent(serveur_regle, tmp_path):
    resultats = _resultat(f"{serveur_regle}/essai-outils", tmp_path / "profil")
    assert {(r["outil"], r["cas"]) for r in resultats} == {
        (o, c) for o in OUTILS_REELS for c in ("reglages", "hors-plage", "neutre")
    }
    for r in resultats:
        m, cas = r["mesure"], (r["outil"], r["cas"])
        assert m["cache"] is False and m["adaptations"] == "appliquees", cas
        if r["cas"] == "reglages":
            attendus = {f"data-adapt-{i}" for i in REGLAGES if i != "surlignage-mots-cles"}
            if r["outil"] != "calculatrice":
                attendus.discard("data-adapt-reperes-rang-chiffres")  # levier inconnu de cet outil
            assert set(m["attributs"]) == attendus, cas
            assert m["racine"] == 24, cas  # 16 px x 1,5
            assert m["fontSize"] == 24, cas
            assert _px(m["letterSpacing"]) == pytest.approx(0.12 * 24, abs=0.01), cas
            assert _px(m["wordSpacing"]) == pytest.approx(0.16 * 24, abs=0.01), cas
            assert _px(m["lineHeight"]) == pytest.approx(2.0 * 24, abs=0.01), cas
            assert m["fontFamily"].startswith("Verdana"), cas
            assert m["backgroundColor"] == CREME, cas
            assert _px(m["titreEspacement"]) > 0, cas
            if r["outil"] == "calculatrice":
                # 456 : centaines, dizaines, unites ; chaque couleur >= 4,5:1 sur tout le fond de
                # l'ecran (chaque couleur du degrade, le pire compte)
                assert [c["classe"] for c in m["chiffres"]] == ["rang-centaines", "rang-dizaines", "rang-unites"], cas
                for c in m["chiffres"]:
                    assert _pire_contraste(c["couleur"], c["fonds"]) >= 4.5, (cas, c)
                # trois teintes distinctes entre elles et du texte normal de l'ecran
                couleurs = {c["couleur"] for c in m["chiffres"]}
                assert len(couleurs) == 3 and m["ecran"] not in couleurs, (cas, couleurs, m["ecran"])
                # les touches suivent le levier police (l'ecran garde sa chasse fixe, renvoye au lot 3)
                assert m["touchePolice"].startswith("Verdana"), (cas, m["touchePolice"])
        else:
            # hors plage : ignore comme un levier inconnu ; neutre : rien. Le rendu est celui d'avant.
            assert m["attributs"] == [], cas
            assert m["racine"] == 16 and m["fontSize"] == 16, cas
            assert m["letterSpacing"] == "normal" and m["wordSpacing"] == "0px", cas
            if r["outil"] == "calculatrice":
                # la calculatrice de main ne fixe pas d'interligne : le rendu d'avant est « normal »
                assert m["lineHeight"] == "normal", cas
            else:
                assert _px(m["lineHeight"]) == pytest.approx(1.4 * 16, abs=0.01), cas
            assert m["backgroundColor"] == "rgb(255, 255, 255)", cas
            assert m["chiffre"] is None and m["chiffres"] == [], cas
            if r["outil"] == "calculatrice":
                assert m["touchePolice"].startswith('"Segoe UI"'), (cas, m["touchePolice"])
