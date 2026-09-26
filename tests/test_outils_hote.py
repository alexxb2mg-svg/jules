"""EX-009 : la page hote cree l'iframe d'outil et filtre ce qu'elle recoit (docs/OUTILS-CONTRAT.md,
§2 « Origine opaque » et §3 « Isolement technique »), code dans jules/web/static/outils-hote.js.

Deux niveaux :
- statique : l'iframe est creee en sandbox="allow-scripts" sans allow-same-origin, la page de cours
  charge outils-hote.js, les en-tetes servis sont ceux ecrits dans le contrat ;
- navigateur reel : un vrai serveur Jules (uvicorn, pas file://) sert une page d'essai qui monte
  un outil sonde avec le vrai outils-hote.js ; un Chromium headless relit ce que l'hote a laisse
  passer. Ignore si Chromium est absent (definir JULES_CHROMIUM), comme tests/test_symboles.py.
"""

from __future__ import annotations

import json
import re
import socket
import subprocess
import threading
import time
from pathlib import Path

import pytest
from fastapi.responses import HTMLResponse, Response
from fastapi.testclient import TestClient

from jules.chantier_visuel import _chromium
from jules.config import depuis_dict
from jules.modules.outils import ENTETES_OUTIL
from jules.moteur import Tuteur
from jules.web.app import creer_app

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"
HOTE_JS = (STATIQUE / "outils-hote.js").read_text(encoding="utf-8")


# --- statique -------------------------------------------------------------------------------


def _code_sans_commentaires(js: str) -> str:
    return "\n".join(ligne.split("//")[0] for ligne in js.splitlines())


def test_iframe_sandbox_allow_scripts_sans_allow_same_origin():
    code = _code_sans_commentaires(HOTE_JS)
    assert 'const SANDBOX = "allow-scripts";' in code
    assert 'setAttribute("sandbox", SANDBOX)' in code
    # Aucun fichier de la page ne donne jamais l'origine du site a une iframe.
    for fichier in STATIQUE.glob("*.js"):
        assert "allow-same-origin" not in _code_sans_commentaires(fichier.read_text(encoding="utf-8")), fichier.name


def test_hote_verifie_la_source_et_jamais_l_origine():
    code = _code_sans_commentaires(HOTE_JS)
    assert "event.source !== iframe.contentWindow" in code
    assert "event.origin" not in code


def test_page_de_cours_charge_l_hote_avant_cours_js():
    html = (STATIQUE / "cours.html").read_text(encoding="utf-8")
    assert html.index('"/static/commun.js"') < html.index('"/static/outils-hote.js"') < html.index('"/static/cours.js"')
    cours = (STATIQUE / "cours.js").read_text(encoding="utf-8")
    assert "OutilsHote.monter(" in cours
    assert "iframe" not in _code_sans_commentaires(cours)  # seule outils-hote.js cree l'iframe


def test_csp_des_outils_identique_a_celle_du_contrat():
    contrat = (RACINE / "docs" / "OUTILS-CONTRAT.md").read_text(encoding="utf-8")
    section = contrat.split("## 3. Isolement technique")[1].split("### Premier filtre")[0]
    trouve_csp = re.search(r"`(default-src 'none';[^`]*)`", section, re.S)
    assert trouve_csp
    csp_contrat = " ".join(trouve_csp.group(1).split())
    assert ENTETES_OUTIL["Content-Security-Policy"] == csp_contrat
    section5 = " ".join(contrat.split("## 5. Comment un outil est servi")[1].split())
    for entete in ("X-Frame-Options: SAMEORIGIN", "X-Content-Type-Options: nosniff", "Referrer-Policy: no-referrer"):
        nom, valeur = entete.split(": ")
        assert f"`{entete}`" in section5
        assert ENTETES_OUTIL[nom] == valeur
    assert ENTETES_OUTIL["Cache-Control"] == "no-store"


# --- serveur Jules reel + navigateur ------------------------------------------------------

SONDE_YAML = """id: sonde
titre: "Sonde"
entree: index.html
actions: [demander]
evenements: [bonjour, echo]
permissions: []
licence: MIT
"""

# La sonde envoie, au chargement, un evenement valide puis des messages hors contrat ; elle repond
# a l'action « demander » par l'evenement « echo ».
SONDE_JS = """"use strict";
(function () {
  var p = window.parent;
  p.postMessage({ type: "evenement", evenement: "bonjour", donnees: { de: "sonde" } }, "*");
  p.postMessage({ type: "evenement", evenement: "non_declare", donnees: {} }, "*");
  p.postMessage({ type: "autre", evenement: "bonjour", donnees: {} }, "*");
  p.postMessage("chaine", "*");
  p.postMessage({ type: "evenement", evenement: "bonjour", donnees: "pas un objet" }, "*");
  window.addEventListener("message", function (e) {
    if (e.source !== window.parent) return;
    var m = e.data;
    if (m && m.type === "action" && m.action === "demander") {
      p.postMessage({ type: "evenement", evenement: "echo", donnees: { recu: m.donnees } }, "*");
    }
  });
})();
"""

INTRUS_YAML = SONDE_YAML.replace("id: sonde", "id: intrus").replace('"Sonde"', '"Intrus"')
# Un autre outil de la meme page tente de se faire passer pour la sonde.
INTRUS_JS = """"use strict";
window.parent.postMessage({ type: "evenement", evenement: "bonjour", donnees: { de: "intrus" } }, "*");
"""

INDEX = '<!doctype html><meta charset="utf-8"><title>{t}</title><body><script src="outil.js"></script></body>'

ESSAI_HTML = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>essai</title></head>
<body><div id="zone"></div><script src="/static/outils-hote.js"></script>
<script src="/essai-hote.js"></script></body></html>"""

ESSAI_JS = """"use strict";
(function () {
  var r = { recus: [], erreurs: [] };
  window.addEventListener("error", function (e) { r.erreurs.push(String(e.message)); });
  var outil = { id: "sonde", titre: "Sonde", actions: ["demander"], evenements: ["bonjour", "echo"] };
  var m = OutilsHote.monter(document.getElementById("zone"), outil, {
    action: "demander", donnees: { x: 1 },
    surEvenement: function (ev, d) { r.recus.push({ ev: ev, d: d }); }
  });
  // Message bien forme mais venu de la page elle-meme : pas de l'iframe de la sonde.
  window.postMessage({ type: "evenement", evenement: "bonjour", donnees: { de: "page" } }, "*");
  var intrus = document.createElement("iframe");
  intrus.setAttribute("sandbox", "allow-scripts");
  intrus.src = "/api/eleve/outils/intrus/";
  document.body.appendChild(intrus);
  setTimeout(function () {
    r.sandbox = m.iframe.getAttribute("sandbox");
    r.documentInaccessible = m.iframe.contentDocument === null;
    r.actionNonDeclareeEnvoyee = m.envoyer("inconnue", {});
    m.demonter();
    r.iframeRetiree = !document.body.contains(m.iframe);
    document.body.setAttribute("data-resultat", JSON.stringify(r));
  }, 1500);
})();
"""


def _port_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def serveur(projet, brut_config):
    """Un vrai serveur Jules (acces libre, 127.0.0.1) avec les outils sonde et intrus."""
    import uvicorn

    for ident, yaml_, js in (("sonde", SONDE_YAML, SONDE_JS), ("intrus", INTRUS_YAML, INTRUS_JS)):
        dossier = projet / "outils" / ident
        dossier.mkdir(parents=True)
        (dossier / "outil.yaml").write_text(yaml_, encoding="utf-8")
        (dossier / "index.html").write_text(INDEX.format(t=ident), encoding="utf-8")
        (dossier / "outil.js").write_text(js, encoding="utf-8")
    brut_config["modules"] = [*brut_config["modules"], {"id": "outils"}]
    from jules.llm.factice import Brique as Factice

    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    app = creer_app(tuteur)

    @app.get("/essai-hote", response_class=HTMLResponse)
    def essai() -> HTMLResponse:
        return HTMLResponse(ESSAI_HTML)

    @app.get("/essai-hote.js")
    def essai_js() -> Response:
        return Response(ESSAI_JS, media_type="text/javascript; charset=utf-8")

    port = _port_libre()
    serveur_uv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    fil = threading.Thread(target=serveur_uv.run, daemon=True)
    fil.start()
    limite = time.time() + 20
    while not serveur_uv.started and time.time() < limite:
        time.sleep(0.05)
    assert serveur_uv.started, "serveur Jules non demarre"
    yield f"http://127.0.0.1:{port}", app
    serveur_uv.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


def test_en_tetes_servis_aux_outils_et_a_la_page(serveur):
    _, app = serveur
    client = TestClient(app)
    for chemin in ("/api/eleve/outils/sonde/", "/api/eleve/outils/sonde/outil.js"):
        r = client.get(chemin)
        assert r.status_code == 200, chemin
        for nom, valeur in ENTETES_OUTIL.items():
            assert r.headers[nom] == valeur, (chemin, nom)
    cours = client.get("/cours")
    # La page de cours reste non encadrable par un autre site ; ses cadres restent same-origin.
    assert cours.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in cours.headers["content-security-policy"]
    assert "default-src 'self'" in cours.headers["content-security-policy"]


def test_hote_dans_un_vrai_navigateur(serveur, tmp_path):
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent (definir JULES_CHROMIUM)")
    url, _ = serveur
    options = ["--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={tmp_path / 'profil'}"]
    options += ["--virtual-time-budget=5000", "--dump-dom"]
    sortie = subprocess.run(  # noqa: S603 - navigateur local, arguments fixes
        [navigateur, *options, f"{url}/essai-hote"], capture_output=True, text=True, timeout=120, check=True
    ).stdout
    trouve = re.search(r'data-resultat="([^"]*)"', sortie)
    assert trouve, sortie[-2000:]
    r = json.loads(trouve.group(1).replace("&quot;", '"').replace("&amp;", "&"))
    assert r["erreurs"] == []
    assert r["sandbox"] == "allow-scripts"
    assert r["documentInaccessible"] is True
    # Seuls passent : l'evenement declare de la sonde (donnees non objet ramenees a {}) et l'echo
    # de l'action envoyee au chargement. Rien de la page, rien de l'intrus, rien d'hors contrat.
    assert r["recus"] == [
        {"ev": "bonjour", "d": {"de": "sonde"}},
        {"ev": "bonjour", "d": {}},
        {"ev": "echo", "d": {"recu": {"x": 1}}},
    ]
    assert r["actionNonDeclareeEnvoyee"] is False
    assert r["iframeRetiree"] is True
