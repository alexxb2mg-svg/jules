"""EX-106 (docs/spec/ADAPTATIONS-LOT2.md) : robustesse. Aucun contenu n'est coupe ni ne se superpose,
ni aux valeurs du test WCAG 1.4.12, ni aux valeurs maximales des plages du §2.

Deux conditions, dans un vrai Chromium servi par un vrai serveur Jules :

- « wcag » : tous les leviers au neutre, et une feuille de style « utilisateur » chargee en dernier,
  celle du test WCAG 1.4.12 (interligne 1,5 ; paragraphes 2 fois la taille ; lettres 0,12em ; mots
  0,16em). La sonde verifie aussi que ces valeurs sont bien celles qui s'appliquent : aucune regle de
  Jules (le `!important` du levier interligne compris) ne les ecrase ;
- « maxima » : les leviers regles aux maxima des plages du §2 (lettres 0,18em, mots 0,5em,
  interligne 2,0, taille 1,5 fois la neutre, lignes de 80ch), avec Verdana, la police la plus large
  de la liste fermee.

Pages : accueil, une fiche (lien direct), cours (liste des notions, puis une lecon ouverte), studio
(choix de la matiere, puis la liste des notions d'EMC aux titres longs), et les trois outils
(calculatrice, frise en affichage et en exercice, lexique) dans des cadres de meme origine a la largeur
d'un cadre de lecon, qui recoivent les leviers par le message `adaptations` puis un contenu aux
libelles longs. Largeurs : 1280 px (ordinateur) et 390 px (telephone).

Detection (tests/sonde_robustesse.js) : chaque ligne de texte visible reste dans la page et dans la
boite de tout ancetre qui coupe (overflow hidden/clip) ; le bloc qui porte un texte ne deborde pas
(scrollWidth > clientWidth), pas plus qu'un ancetre a defilement horizontal ni la page ; deux lignes
de texte de noeuds differents ne se recouvrent pas (tiroirs fermes et textes masques pour les
lecteurs d'ecran exclus).

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

from jules.chantier_visuel import _chromium
from jules.leviers import charger_leviers
from tests.test_outils_hote import _port_libre, temps_virtuel_hors_ci_linux

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"
SONDE = Path(__file__).with_name("sonde_robustesse.js")
# cadre -> dossier de l'outil (la frise deux fois : affichage d'une periode, exercice de rangement)
CADRES = {
    "calculatrice": "calculatrice",
    "frise-chronologique": "frise-chronologique",
    "frise-exercice": "frise-chronologique",
    "lexique": "lexique",
}

# cas -> (page html, fragment d'URL)
CAS_PAGES = {
    "accueil": ("accueil.html", ""),
    "fiche": ("accueil.html", "#fonctions-lineaires-affines"),
    "cours": ("cours.html", "?matiere=mathematiques"),  # liste des notions au centre (EX-209)
    "cours-lecon": ("cours.html", "?matiere=mathematiques"),  # puis une lecon ouverte (action de la sonde)
    "studio": ("studio.html", ""),  # premiere visite : « Choisis une matière »
    "studio-notions": ("studio.html", "?matiere=emc"),  # titres de notions longs
}
LARGEURS = (1280, 390)

# Valeurs maximales des plages du §2 (verifiees contre les YAML par test_les_maxima_sont_ceux_des_plages).
MAXIMA: dict[str, Any] = {
    "espacement-lettres": 0.18,
    "espacement-mots": 0.5,
    "interligne": 2.0,
    "taille-texte": 1.6875,
    "longueur-ligne": 80,
    "police": "verdana",
}

# Test WCAG 1.4.12 (https://www.w3.org/WAI/WCAG22/Understanding/text-spacing) : la feuille que
# l'utilisateur ajoute. Chargee apres toutes les feuilles de la page.
FEUILLE_WCAG = """/* WCAG 2.2, critere 1.4.12 : feuille de l'utilisateur */
* { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; }
p { margin-bottom: 2em !important; }
"""

PAGE_OUTILS = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>essai</title>
<link rel="stylesheet" href="/essai-outils.css"></head>
<body>__CADRES__
<script src="/sonde-robustesse.js" data-cas="outils" data-wcag="__WCAG__" data-leviers="__LEVIERS__"></script>
<script src="/essai-poignee.js"></script></body></html>"""

# Largeur des cadres : celle de .outil-cadre dans une lecon de /cours (colonne de 760 px au plus, marges
# de .lecon-zone et du bloc), soit 716 px a 1280 px et 316 px a 390 px. En fichier : la CSP de la page
# (style-src 'self') refuse l'attribut style, un cadre sans feuille resterait a 300 px par defaut.
FEUILLE_OUTILS = """body { margin: 0; }
iframe[data-outil] { display: block; width: min(100vw - 74px, 716px); height: 1400px; border: 0; }
"""

# Contenu envoye aux outils apres la poignee de main (sans lui, frise et lexique sont vides) : des
# libelles longs, comme ceux d'une vraie lecon d'histoire ou de sciences.
EVENEMENTS = [
    {"id": "e1", "annee": 1789, "titre": "Prise de la Bastille et Déclaration des droits de l'homme et du citoyen"},
    {"id": "e2", "annee": 1848, "titre": "Abolition définitive de l'esclavage dans les colonies françaises"},
    {"id": "e3", "annee": 1905, "titre": "Loi de séparation des Églises et de l'État"},
    {"id": "e4", "annee": 1944, "titre": "Droit de vote des femmes (ordonnance du 21 avril)"},
]
TERMES = [
    {
        "terme": "photosynthèse",
        "definition": "Production de matière organique par les végétaux chlorophylliens, "
        "à partir d'eau et de dioxyde de carbone, grâce à l'énergie lumineuse.",
    },
    {"terme": "anticonstitutionnellement", "definition": "D'une manière contraire à la Constitution."},
    {"terme": "hypoténuse", "definition": "Dans un triangle rectangle, côté opposé à l'angle droit."},
]
ACTIONS_OUTILS = {
    "frise-chronologique": [
        {"action": "afficher_periode", "donnees": {"evenements": EVENEMENTS}},
    ],
    "frise-exercice": [
        {
            "action": "exercice_remettre_dans_l_ordre",
            "donnees": {"evenements": [{"id": e["id"], "titre": e["titre"]} for e in EVENEMENTS]},
        },
    ],
    "lexique": [{"action": "afficher_termes", "donnees": {"termes": TERMES}}],
}

# Poignee de main des outils (comme outils-hote.js) : leviers de /api/infos a chaque « pret », puis
# les actions de contenu de l'outil (ACTIONS_OUTILS).
POIGNEE_JS = """"use strict";
(function () {
  var ACTIONS = __ACTIONS__;
  var leviers = null, enAttente = [];
  function repondre(source) {
    source.postMessage({ type: "adaptations", leviers: leviers }, "*");
    var cadre = Array.prototype.find.call(document.querySelectorAll("iframe[data-outil]"), function (c) {
      return c.contentWindow === source;
    });
    (ACTIONS[cadre && cadre.getAttribute("data-outil")] || []).forEach(function (a) {
      source.postMessage({ type: "action", action: a.action, donnees: a.donnees }, "*");
    });
  }
  window.addEventListener("message", function (e) {
    if (!e.data || e.data.type !== "pret") return;
    if (leviers === null) enAttente.push(e.source); else repondre(e.source);
  });
  fetch("/api/infos").then(function (r) { return r.json(); }).then(function (infos) {
    leviers = infos.leviers || {};
    enAttente.forEach(repondre);
  });
})();
"""

ENTETES_CADRE = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; base-uri 'self'; frame-ancestors 'self'"
    ),
    "X-Frame-Options": "SAMEORIGIN",
}


def _balise_sonde(cas: str, wcag: bool, leviers: bool) -> str:
    return (
        f'<script src="/sonde-robustesse.js" data-cas="{cas}" data-wcag="{int(wcag)}" '
        f'data-leviers="{int(leviers)}"></script>'
    )


def _avec_feuille_wcag(html: str) -> str:
    return html.replace("</head>", '<link rel="stylesheet" href="/wcag-1412.css">\n</head>', 1)


def _serveur(projet: Path, brut_config: dict, valeurs: dict[str, Any], wcag: bool):
    import uvicorn

    from jules.config import depuis_dict
    from jules.llm.factice import Brique as Factice
    from jules.moteur import Tuteur
    from jules.web.app import creer_app

    brut_config["modules"] = [*brut_config["modules"], {"id": "outils"}]
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    tuteur.valeurs_leviers = lambda: dict(valeurs)  # type: ignore[method-assign]
    app = creer_app(tuteur)
    leviers = bool(valeurs)

    pages = {}
    for cas, (html, _) in CAS_PAGES.items():
        texte = (STATIQUE / html).read_text(encoding="utf-8")
        texte = texte.replace("</body>", _balise_sonde(cas, wcag, leviers) + "\n</body>", 1)
        pages[cas] = _avec_feuille_wcag(texte) if wcag else texte
    cadres = {}
    for cadre, dossier in CADRES.items():
        html = (projet / "extensions" / dossier / "index.html").read_text(encoding="utf-8")
        html = html.replace("<head>", f'<head><base href="/api/eleve/outils/{dossier}/">', 1)
        cadres[cadre] = _avec_feuille_wcag(html) if wcag else html
    balises = "\n".join(f'<iframe data-outil="{o}" src="/essai-cadre/{o}"></iframe>' for o in CADRES)
    page_outils = (
        PAGE_OUTILS.replace("__CADRES__", balises)
        .replace("__WCAG__", str(int(wcag)))
        .replace("__LEVIERS__", str(int(leviers)))
    )
    scripts = {
        "sonde-robustesse.js": SONDE.read_text(encoding="utf-8"),
        "essai-poignee.js": POIGNEE_JS.replace("__ACTIONS__", json.dumps(ACTIONS_OUTILS, ensure_ascii=False)),
    }

    @app.get("/essai-page/{cas}", response_class=HTMLResponse)
    def essai_page(cas: str) -> HTMLResponse:
        if cas not in pages:
            raise HTTPException(status_code=404)
        return HTMLResponse(pages[cas])

    @app.get("/essai-outils", response_class=HTMLResponse)
    def essai_outils() -> HTMLResponse:
        return HTMLResponse(page_outils, headers=ENTETES_CADRE)

    @app.get("/essai-cadre/{outil_id}", response_class=HTMLResponse)
    def essai_cadre(outil_id: str) -> HTMLResponse:
        if outil_id not in cadres:
            raise HTTPException(status_code=404)
        return HTMLResponse(cadres[outil_id], headers=ENTETES_CADRE)

    @app.get("/essai-outils.css")
    def feuille_outils() -> Response:
        return Response(FEUILLE_OUTILS, media_type="text/css; charset=utf-8")

    @app.get("/wcag-1412.css")
    def feuille_wcag() -> Response:
        return Response(FEUILLE_WCAG, media_type="text/css; charset=utf-8")

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


@pytest.fixture(params=["wcag", "maxima"])
def serveur(request, projet, brut_config):
    condition = request.param
    valeurs = MAXIMA if condition == "maxima" else {}
    base, uv, fil, tuteur = _serveur(projet, brut_config, valeurs, wcag=condition == "wcag")
    yield condition, base
    uv.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


def _resultat(url: str, profil: Path, largeur: int) -> Any:
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent (definir JULES_CHROMIUM)")
    options = ["--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={profil}"]
    options += [f"--window-size={largeur},900", "--hide-scrollbars", "--virtual-time-budget=20000", "--dump-dom"]
    fini = subprocess.run(  # noqa: S603 - navigateur local, arguments fixes
        [navigateur, *options, url], capture_output=True, text=True, encoding="utf-8", timeout=180, check=False
    )
    sortie = fini.stdout
    trouve = re.search(r'data-resultat="([^"]*)"', sortie)
    assert trouve, f"code {fini.returncode}\n{fini.stderr[-2000:]}\n{sortie[-2000:]}"
    return json.loads(
        trouve.group(1).replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    )


def _rapport(r: dict) -> str:
    lignes = []
    for doc in r["resultats"]:
        for f in doc["fautes"]:
            lignes.append(f"[{doc['doc']}] {f['type']} {f['element']} « {f['texte']} » {f['detail']}")
    return "\n".join(lignes)


def test_les_maxima_sont_ceux_des_plages():
    leviers = charger_leviers()
    for ident, valeur in MAXIMA.items():
        levier = leviers[ident]
        assert levier.dans_la_plage(valeur), ident
        if ident == "police":
            assert valeur in levier.valeurs, ident
        else:
            assert levier.maximum == pytest.approx(valeur), ident


def test_la_feuille_wcag_porte_les_valeurs_du_critere():
    assert "line-height: 1.5 !important" in FEUILLE_WCAG
    assert "letter-spacing: 0.12em !important" in FEUILLE_WCAG
    assert "word-spacing: 0.16em !important" in FEUILLE_WCAG
    assert "margin-bottom: 2em !important" in FEUILLE_WCAG


@temps_virtuel_hors_ci_linux
@pytest.mark.parametrize("largeur", LARGEURS)
@pytest.mark.parametrize("cas", [*CAS_PAGES, "outils"])
def test_rien_n_est_coupe_ni_superpose(serveur, tmp_path, cas, largeur):
    condition, base = serveur
    url = f"{base}/essai-outils" if cas == "outils" else f"{base}/essai-page/{cas}{CAS_PAGES[cas][1]}"
    r = _resultat(url, tmp_path / "profil", largeur)
    assert "erreur" not in r, r.get("erreur")
    assert r["largeur"] == largeur
    attendus = {f"data-adapt-{i}" for i in MAXIMA} if condition == "maxima" else set()
    for doc in r["resultats"]:
        assert doc["textes"] > 5, (doc["doc"], "page vide : la sonde n'a rien mesure")
        assert set(doc["attributs"]) == attendus, doc["doc"]
    assert not _rapport(r), f"{condition} / {cas} / {largeur} px :\n{_rapport(r)}"
