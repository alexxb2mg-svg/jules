"""EX-001 a EX-003 (docs/spec/ADAPTATIONS.md) : poignee de main des adaptations entre la page hote
(jules/web/static/outils-hote.js) et les outils (extensions/<outil>/outil.js), decrite dans
docs/OUTILS-CONTRAT.md, §2 « Adaptations ».

Tout se passe dans un vrai Chromium servi par un vrai serveur Jules (pas file://), comme
tests/test_outils_hote.py. Trois pages d'essai :

- cote outil : chacun des trois outils de reference est charge dans un cadre de meme origine (non
  sandboxe, pour pouvoir relire son DOM) sous une page hote factice qui joue un scenario : reponse
  immediate avec un levier inconnu, aucune reponse (delai depasse), reponse apres le delai (appliquee),
  message d'adaptations venu d'une autre fenetre que le parent (ignore) ;
- cote hote : le vrai OutilsHote avec un outil sonde en iframe sandboxee, qui se recharge une fois
  (deuxieme « pret » -> deuxieme reponse) ; des « pret » venus de la page elle-meme et d'une autre
  iframe restent sans reponse ;
- bout en bout : les trois vrais outils en iframe sandboxee, avec et sans page hote qui repond.

EX-012 : ces tests ne comptent que s'ils ont tourne (JULES_CHROMIUM defini, `pytest -rs`).
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from fastapi.responses import HTMLResponse, Response

from jules.chantier_visuel import _chromium
from tests.test_outils_hote import INDEX, _port_libre

RACINE = Path(__file__).resolve().parents[1]
OUTILS_REELS = ("calculatrice", "frise-chronologique", "lexique")
SCENARIOS = ("reponse", "delai", "tardif", "autre-source")

# En-tetes des pages d'essai encadrees par la page d'essai (meme origine) : l'en-tete par defaut de
# Jules (X-Frame-Options: DENY) les rendrait inaffichables dans un cadre.
ENTETES_CADRE = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; base-uri 'self'; frame-ancestors 'self'"
    ),
    "X-Frame-Options": "SAMEORIGIN",
}

# --- page d'essai cote outil -----------------------------------------------------------------

PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>essai</title></head>
<body><div id="zone"></div>{scripts}</body></html>"""

ESSAI_OUTIL_JS = """"use strict";
(function () {
  var OUTILS = __OUTILS__;
  var SCENARIOS = __SCENARIOS__;
  var REPONSE = { type: "adaptations", leviers: { levier_inconnu: 42, autre: { x: [1, 2] } } };
  var cadres = [];

  function parSource(source) {
    for (var i = 0; i < cadres.length; i++) if (cadres[i].iframe.contentWindow === source) return cadres[i];
    return null;
  }
  function etatDe(c) {
    var d = c.iframe.contentDocument;
    return { cache: d.body.hidden, adaptations: d.documentElement.getAttribute("data-adaptations") };
  }

  window.addEventListener("message", function (e) {
    var m = e.data;
    if (m && m.type === "intrus-envoye") {
      cadres[m.cible].intrusApres = Math.round(performance.now() - cadres[m.cible].tPret);
      return;
    }
    var c = parSource(e.source);
    if (!c) return;
    c.journal.push(m && m.type);
    if (!m || m.type !== "pret") return;
    c.tPret = performance.now();
    c.cacheAuPret = c.iframe.contentDocument.body.hidden;
    c.iframe.contentWindow.addEventListener("error", function (err) { c.erreurs.push(String(err.message)); });
    if (c.scenario === "reponse") c.iframe.contentWindow.postMessage(REPONSE, "*");
    if (c.scenario === "tardif") setTimeout(function () { c.iframe.contentWindow.postMessage(REPONSE, "*"); }, 800);
    if (c.scenario === "autre-source") {
      var intrus = document.createElement("iframe");
      intrus.src = "/essai-intrus?cible=" + c.index;
      document.body.appendChild(intrus);
    }
    setTimeout(function () { c.a300 = etatDe(c); }, 300);
    setTimeout(function () { c.a700 = etatDe(c); }, 700);
  });

  OUTILS.forEach(function (outil) {
    SCENARIOS.forEach(function (scenario) {
      var c = { index: cadres.length, outil: outil, scenario: scenario, journal: [], erreurs: [] };
      c.iframe = document.createElement("iframe");
      c.iframe.id = "cadre-" + c.index;
      c.iframe.src = "/essai-cadre/" + outil;
      cadres.push(c);
      document.getElementById("zone").appendChild(c.iframe);
    });
  });

  setTimeout(function () {
    var r = cadres.map(function (c) {
      return {
        outil: c.outil, scenario: c.scenario, journal: c.journal, erreurs: c.erreurs,
        cacheAuPret: c.cacheAuPret, a300: c.a300, a700: c.a700, fin: etatDe(c), intrusApres: c.intrusApres
      };
    });
    document.body.setAttribute("data-resultat", JSON.stringify(r));
  }, 2500);
})();
""".replace("__OUTILS__", json.dumps(list(OUTILS_REELS))).replace("__SCENARIOS__", json.dumps(list(SCENARIOS)))

# Autre fenetre de la meme page (pas le parent de l'outil) : envoie des adaptations a l'outil cible.
ESSAI_INTRUS_JS = """"use strict";
(function () {
  var cible = Number(new URLSearchParams(location.search).get("cible"));
  var fenetre = parent.document.getElementById("cadre-" + cible).contentWindow;
  fenetre.postMessage({ type: "adaptations", leviers: {} }, "*");
  parent.postMessage({ type: "intrus-envoye", cible: cible }, "*");
})();
"""

# --- page d'essai cote hote ------------------------------------------------------------------

POLI_YAML = """id: poli
titre: "Poli"
entree: index.html
actions: []
evenements: [adaptations_recues]
permissions: []
licence: MIT
"""

# Outil sonde : fait la poignee de main, rapporte chaque « adaptations » recu, se recharge une fois
# (meme contentWindow, nouvelle poignee de main). Une fois recharge, il envoie aussi
# « adaptations-absentes » pour verifier que l'hote le transmet (une seule fois).
POLI_JS = """"use strict";
(function () {
  var p = window.parent;
  var page = location.search.indexOf("recharge") === -1 ? "premiere" : "rechargee";
  window.addEventListener("message", function (e) {
    if (e.source !== p) return;
    var m = e.data;
    if (!m || m.type !== "adaptations") return;
    var d = { page: page, leviers: m.leviers };
    p.postMessage({ type: "evenement", evenement: "adaptations_recues", donnees: d }, "*");
    if (page === "premiere") setTimeout(function () { location.href = "index.html?recharge=1"; }, 600);
    else p.postMessage({ type: "adaptations-absentes" }, "*");
  });
  p.postMessage({ type: "pret" }, "*");
})();
"""

FAUX_POLI_YAML = POLI_YAML.replace("id: poli", "id: faux-poli").replace('"Poli"', '"Faux"')
# Une autre iframe de la page tente la poignee de main a la place de la sonde.
FAUX_POLI_JS = """"use strict";
window.parent.postMessage({ type: "pret" }, "*");
window.parent.postMessage({ type: "adaptations-absentes" }, "*");
"""

ESSAI_HOTE_JS = """"use strict";
(function () {
  var r = { recus: [], absentes: 0, erreurs: [] };
  window.addEventListener("error", function (e) { r.erreurs.push(String(e.message)); });
  var outil = { id: "poli", titre: "Poli", actions: [], evenements: ["adaptations_recues"] };
  var leviers = { taille_texte: "grande", levier_inconnu: 1 };
  function faussesPoignees() {
    window.postMessage({ type: "pret" }, "*");
    window.postMessage({ type: "adaptations-absentes" }, "*");
    var faux = document.createElement("iframe");
    faux.setAttribute("sandbox", "allow-scripts");
    faux.src = "/api/eleve/outils/faux-poli/";
    document.body.appendChild(faux);
  }
  var m = OutilsHote.monter(document.getElementById("zone"), outil, {
    leviers: leviers,
    surEvenement: function (ev, d) { r.recus.push(d); if (r.recus.length === 1) faussesPoignees(); },
    surAdaptationsAbsentes: function () { r.absentes += 1; }
  });
  setTimeout(function () {
    m.demonter();
    document.body.setAttribute("data-resultat", JSON.stringify(r));
  }, 3000);
})();
"""

# --- bout en bout : vrais outils en iframe sandboxee -----------------------------------------

ESSAI_REELS_JS = """"use strict";
(function () {
  var OUTILS = __OUTILS__;
  var suivis = [];
  window.addEventListener("message", function (e) {
    for (var i = 0; i < suivis.length; i++) {
      if (suivis[i].iframe.contentWindow === e.source) suivis[i].journal.push(e.data && e.data.type);
    }
  });
  OUTILS.forEach(function (id) {
    var avecHote = { outil: id, hote: true, journal: [], absentes: 0 };
    var monte = OutilsHote.monter(document.getElementById("zone"), { id: id, titre: id, actions: [], evenements: [] }, {
      leviers: { levier_inconnu: 1 },
      surAdaptationsAbsentes: function () { avecHote.absentes += 1; }
    });
    avecHote.iframe = monte.iframe;
    suivis.push(avecHote);
    // Meme outil, meme sandbox, mais personne ne repond : l'outil doit s'afficher seul et le dire.
    var seul = { outil: id, hote: false, journal: [], absentes: 0 };
    seul.iframe = document.createElement("iframe");
    seul.iframe.setAttribute("sandbox", "allow-scripts");
    seul.iframe.src = "/api/eleve/outils/" + id + "/";
    document.getElementById("zone").appendChild(seul.iframe);
    suivis.push(seul);
  });
  setTimeout(function () {
    var r = suivis.map(function (s) {
      return { outil: s.outil, hote: s.hote, journal: s.journal, absentes: s.absentes };
    });
    document.body.setAttribute("data-resultat", JSON.stringify(r));
  }, 2500);
})();
""".replace("__OUTILS__", json.dumps(list(OUTILS_REELS)))


@pytest.fixture
def serveur(projet, brut_config):
    """Un vrai serveur Jules (127.0.0.1) : outils de reference (extensions), sondes, pages d'essai."""
    import threading
    import time

    import uvicorn

    for ident, yaml_, js in (("poli", POLI_YAML, POLI_JS), ("faux-poli", FAUX_POLI_YAML, FAUX_POLI_JS)):
        dossier = projet / "outils" / ident
        dossier.mkdir(parents=True)
        (dossier / "outil.yaml").write_text(yaml_, encoding="utf-8")
        (dossier / "index.html").write_text(INDEX.format(t=ident), encoding="utf-8")
        (dossier / "outil.js").write_text(js, encoding="utf-8")
    brut_config["modules"] = [*brut_config["modules"], {"id": "outils"}]
    from jules.config import depuis_dict
    from jules.llm.factice import Brique as Factice
    from jules.moteur import Tuteur
    from jules.web.app import creer_app

    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    app = creer_app(tuteur)
    scripts_js = {"essai-outil.js": ESSAI_OUTIL_JS, "essai-intrus.js": ESSAI_INTRUS_JS}
    scripts_js |= {"essai-hote.js": ESSAI_HOTE_JS, "essai-reels.js": ESSAI_REELS_JS}

    def page(*scripts: str) -> HTMLResponse:
        balises = "".join(f'<script src="{s}"></script>' for s in scripts)
        return HTMLResponse(PAGE.format(scripts=balises), headers=ENTETES_CADRE)

    @app.get("/essai-outil", response_class=HTMLResponse)
    def essai_outil() -> HTMLResponse:
        return page("/essai-outil.js")

    @app.get("/essai-hote", response_class=HTMLResponse)
    def essai_hote() -> HTMLResponse:
        return page("/static/outils-hote.js", "/essai-hote.js")

    @app.get("/essai-reels", response_class=HTMLResponse)
    def essai_reels() -> HTMLResponse:
        return page("/static/outils-hote.js", "/essai-reels.js")

    @app.get("/essai-intrus", response_class=HTMLResponse)
    def essai_intrus() -> HTMLResponse:
        return page("/essai-intrus.js")

    @app.get("/essai-cadre/{outil_id}", response_class=HTMLResponse)
    def essai_cadre(outil_id: str) -> HTMLResponse:
        # L'index.html reel de l'outil, dont les fichiers relatifs pointent vers la route de l'outil.
        assert outil_id in OUTILS_REELS
        html = (projet / "extensions" / outil_id / "index.html").read_text(encoding="utf-8")
        html = html.replace("<head>", f'<head><base href="/api/eleve/outils/{outil_id}/">', 1)
        return HTMLResponse(html, headers=ENTETES_CADRE)

    @app.get("/{nom}.js")
    def essai_js(nom: str) -> Response:
        return Response(scripts_js[f"{nom}.js"], media_type="text/javascript; charset=utf-8")

    port = _port_libre()
    serveur_uv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    fil = threading.Thread(target=serveur_uv.run, daemon=True)
    fil.start()
    limite = time.time() + 20
    while not serveur_uv.started and time.time() < limite:
        time.sleep(0.05)
    assert serveur_uv.started, "serveur Jules non demarre"
    yield f"http://127.0.0.1:{port}"
    serveur_uv.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


def _resultat(url: str, profil: Path) -> object:
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent (definir JULES_CHROMIUM)")
    options = ["--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={profil}"]
    # Les iframes sandboxees (origine opaque) tournent par defaut dans un processus a part, dont les
    # minuteries n'avancent pas avec le temps virtuel : sans ce drapeau, le delai de 500 ms d'un
    # outil sandboxe ne s'ecoule jamais pendant l'essai. L'isolement teste reste celui du sandbox.
    options += ["--disable-features=IsolateSandboxedIframes"]
    options += ["--virtual-time-budget=10000", "--dump-dom"]
    sortie = subprocess.run(  # noqa: S603 - navigateur local, arguments fixes
        [navigateur, *options, url], capture_output=True, text=True, timeout=120, check=True
    ).stdout
    trouve = re.search(r'data-resultat="([^"]*)"', sortie)
    assert trouve, sortie[-2000:]
    return json.loads(trouve.group(1).replace("&quot;", '"').replace("&amp;", "&"))


def test_les_trois_outils_suivent_la_poignee_de_main(serveur, tmp_path):
    """Cote outil (EX-001, EX-002, EX-003) pour calculatrice, frise-chronologique et lexique."""
    resultats = _resultat(f"{serveur}/essai-outil", tmp_path / "profil")
    assert isinstance(resultats, list)
    assert {(r["outil"], r["scenario"]) for r in resultats} == {(o, s) for o in OUTILS_REELS for s in SCENARIOS}
    for r in resultats:
        cas = (r["outil"], r["scenario"])
        # Contenu masque au chargement, jusqu'a l'envoi de « pret » ; aucune erreur de script.
        assert r["cacheAuPret"] is True, cas
        assert r["erreurs"] == [], cas
        assert r["journal"][0] == "pret", cas
        if r["scenario"] == "reponse":
            # Reponse recue (avec leviers inconnus, ignores sans erreur) : affiche, rien a signaler.
            assert r["journal"] == ["pret"], cas
            assert r["a300"] == {"cache": False, "adaptations": "appliquees"}, cas
            assert r["fin"] == {"cache": False, "adaptations": "appliquees"}, cas
        elif r["scenario"] == "delai":
            # Pas de reponse : masque avant 500 ms, puis affiche avec les valeurs neutres, et signale.
            assert r["a300"] == {"cache": True, "adaptations": None}, cas
            assert r["a700"] == {"cache": False, "adaptations": "neutres"}, cas
            assert r["journal"] == ["pret", "adaptations-absentes"], cas
            assert r["fin"] == {"cache": False, "adaptations": "neutres"}, cas
        elif r["scenario"] == "tardif":
            # Reponse apres le delai : l'outil s'est deja affiche en neutre, la reponse est appliquee.
            assert r["a700"] == {"cache": False, "adaptations": "neutres"}, cas
            assert r["journal"] == ["pret", "adaptations-absentes"], cas
            assert r["fin"] == {"cache": False, "adaptations": "appliquees"}, cas
        else:
            # Adaptations envoyees par une autre fenetre que le parent, avant la fin du delai : ignorees.
            assert r["intrusApres"] is not None and r["intrusApres"] < 450, cas
            assert r["a300"] == {"cache": True, "adaptations": None}, cas
            assert r["journal"] == ["pret", "adaptations-absentes"], cas
            assert r["fin"] == {"cache": False, "adaptations": "neutres"}, cas


def test_hote_repond_a_chaque_pret_de_son_iframe_et_seulement_a_elle(serveur, tmp_path):
    """Cote hote (EX-001, EX-003) : reponse a chaque « pret » de l'iframe, y compris apres
    rechargement ; « pret » et « adaptations-absentes » d'une autre source ignores."""
    r = _resultat(f"{serveur}/essai-hote", tmp_path / "profil")
    assert isinstance(r, dict)
    assert r["erreurs"] == []
    leviers = {"taille_texte": "grande", "levier_inconnu": 1}
    # Exactement deux reponses : une par poignee de main de la sonde (avant et apres rechargement).
    # Une reponse aux « pret » de la page ou de l'autre iframe arriverait aussi a la sonde (l'hote
    # ecrit toujours a SON iframe) et ferait une troisieme entree.
    assert r["recus"] == [{"page": "premiere", "leviers": leviers}, {"page": "rechargee", "leviers": leviers}]
    # Seul le « adaptations-absentes » de la sonde est remonte, pas ceux de la page ni de l'intrus.
    assert r["absentes"] == 1


def test_vrais_outils_sandboxes_avec_et_sans_hote(serveur, tmp_path):
    """Bout en bout, iframes sandboxees reelles : avec OutilsHote, l'outil ne signale jamais
    d'adaptations absentes ; sans page qui repond, il le signale au bout du delai."""
    resultats = _resultat(f"{serveur}/essai-reels", tmp_path / "profil")
    assert isinstance(resultats, list)
    assert len(resultats) == 2 * len(OUTILS_REELS)
    for r in resultats:
        if r["hote"]:
            assert r["journal"] == ["pret"], r
            assert r["absentes"] == 0, r
        else:
            assert r["journal"] == ["pret", "adaptations-absentes"], r
