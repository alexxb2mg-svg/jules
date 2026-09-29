"""Page parent : amenagements, preferences hors PAP et conflits (docs/spec/ADAPTATIONS-LOT2.md, EX-108).

- navigateur reel (EX-012) : un vrai serveur Jules sert la vraie page parent avec le profil fictif
  profils/test-cumul.yaml (classe 4e, donc college). On verifie les libelles college, la rubrique
  « Autres amenagements et adaptations » avec sa mention pour les amenagements sans libelle college,
  les conflits du §4 visibles, le texte de la page passe au crible de docs/spec/termes-interdits.txt,
  puis l'enregistrement : le YAML ne contient que des identifiants ;
- API : toute preference hors §3 ou hors liste fermee (y compris une valeur non hachable) est refusee
  avec un message et n'arrive jamais a `resoudre` (demande SPEC sur la carte EX-108).
"""

from __future__ import annotations

import asyncio
import json
import re
import socket
import subprocess
import threading
from pathlib import Path

import pytest
import yaml
from fastapi.responses import HTMLResponse, Response
from fastapi.testclient import TestClient

from jules import page_adaptations
from jules.amenagements import MENTION_AUTRES, RUBRIQUE_AUTRES, charger_amenagements
from jules.chantier_visuel import _chromium
from jules.combinaison import CONFLIT_LECTURE_AUTOMATIQUE, CONFLIT_SURLIGNAGE_DENSITE, CONFLIT_TAILLE_DENSITE
from jules.composition import MOTIF_ID_AMENAGEMENT, charger_profil
from jules.config import depuis_dict
from jules.web.app import creer_app
from tests.termes_interdits import termes_interdits, trouver_terme

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"
PROFIL = "test-cumul"
# test-cumul.yaml (classe 4e) : amenagements du lot 2 coches et place attendue a l'affichage college.
COCHES_LOT2 = {"supports-aeres-agrandis", "limiter-quantite-ecrit", "surligner-mots-cles", "lecture-oralisee"}
COCHES_LOT2 |= {"consignes-decomposees"}
AVEC_LIBELLE_COLLEGE = {"supports-aeres-agrandis", "limiter-quantite-ecrit", "surligner-mots-cles"}
SANS_LIBELLE_COLLEGE = {"lecture-oralisee", "reformulation", "consignes-decomposees", "reperes-couleur-calcul"}
IDS_LOT1 = ["amenagement-test-a", "amenagement-test-b", "amenagement-inexistant"]

# Script de l'essai, servi par le serveur (la CSP de Jules refuse les scripts en ligne). Il attend que
# la carte soit remplie, releve l'etat, change le choix (lecture automatique, un amenagement decoche),
# enregistre, puis releve a nouveau.
ESSAI_JS = r"""
"use strict";
window.addEventListener("error", (e) => { document.body.setAttribute("data-erreur", String(e.message)); });
const attendre = (test) => new Promise((ok) => {
  const t = setInterval(() => { if (test()) { clearInterval(t); ok(); } }, 20);
});
const ligne = (li) => ({
  id: li.dataset.amenagement,
  coche: li.querySelector("input").checked,
  texte: li.querySelector(".adaptation-libelle").textContent,
  mention: (li.querySelector(".adaptation-mention") || {}).textContent || null,
});
const releve = () => ({
  pap: [...document.querySelectorAll("#adaptations-pap li")].map(ligne),
  autres: [...document.querySelectorAll("#adaptations-autres li")].map(ligne),
  autresTitre: document.getElementById("adaptations-autres-titre").textContent,
  autresVisible: !document.getElementById("adaptations-autres-groupe").classList.contains("cache"),
  niveau: document.getElementById("adaptations-niveau").textContent,
  conflits: [...document.querySelectorAll("#adaptations-conflits li.conflit")]
    .map((li) => ({ id: li.dataset.conflit, texte: li.textContent })),
  police: [...document.querySelectorAll("#pref-police option")].map((o) => o.value),
  fond: [...document.querySelectorAll("#pref-fond option")].map((o) => o.value),
  lectureAuto: document.getElementById("pref-lecture-automatique").checked,
  etat: document.getElementById("adaptations-etat").textContent,
});
(async () => {
  const etape = (nom) => document.body.setAttribute("data-etape", nom);
  etape("chargement");
  await attendre(() => document.querySelectorAll("#adaptations-pap li").length > 0);
  const resultat = { avant: releve() };
  const options = [...document.querySelectorAll("option")].map((o) => o.textContent).join("\n");
  resultat.texte = document.body.innerText + "\n" + options + "\n" + document.title;
  etape("apercu");
  document.getElementById("pref-lecture-automatique").click();
  await attendre(() => document.querySelector('#adaptations-conflits li[data-conflit="lecture-vocale-automatique"]'));
  resultat.apercu = releve();
  etape("enregistrement");
  document.querySelector('input[data-amenagement="consignes-decomposees"]').click();
  document.getElementById("pref-fond").value = "creme";
  document.getElementById("adaptations-enregistrer").click();
  await attendre(() => document.getElementById("adaptations-etat").textContent === "Enregistré.");
  resultat.apres = releve();
  document.body.setAttribute("data-resultat", JSON.stringify(resultat));
})().catch((e) => document.body.setAttribute("data-erreur", String(e && e.message)));
"""

# EX-110 : meme etape d'enregistrement que ESSAI_JS, avec un apercu perime en vol. Le parent coche la lecture
# automatique (apercu A, retenu par le serveur de test), la decoche (apercu B, retour a l'etat de depart),
# puis enregistre. Le serveur ne livre A qu'une fois la reponse du PUT envoyee : A arrive toujours apres.
# Aucune instrumentation du navigateur : l'etat final est lu dans le DOM rendu par --dump-dom.
ESSAI_EX110_JS = r"""
"use strict";
window.addEventListener("error", (e) => { document.body.setAttribute("data-erreur", String(e.message)); });
const attendre = (test) => new Promise((ok) => {
  const t = setInterval(() => { if (test()) { clearInterval(t); ok(); } }, 20);
});
(async () => {
  const etape = (nom) => document.body.setAttribute("data-etape", nom);
  etape("chargement");
  await attendre(() => document.querySelectorAll("#adaptations-pap li").length > 0);
  etape("enregistrement");
  const lecture = document.getElementById("pref-lecture-automatique");
  lecture.click();  // apercu A : retenu jusqu'a l'envoi de la reponse du PUT
  lecture.click();  // apercu B : choix de depart, celui qui est enregistre
  document.getElementById("adaptations-enregistrer").click();
  await attendre(() => document.getElementById("adaptations-etat").textContent === "Enregistré.");
  document.body.setAttribute("data-resultat", JSON.stringify({ enregistre: true }));
})().catch((e) => document.body.setAttribute("data-erreur", String(e && e.message)));
"""
CHEMIN_APERCU = "/api/parent/adaptations/apercu"
CHEMIN_ENREGISTRER = "/api/parent/adaptations"


class _RetenueApercu:
    """Middleware ASGI pur du serveur de test (EX-110). Tant que RETENUE est armee, la reponse du POST
    d'apercu qui demande la lecture automatique (apercu A) est calculee tout de suite, puis retenue
    jusqu'a ce que la reponse du PUT d'enregistrement soit entierement envoyee (threading.Event, pas de
    sleep). Desarmee, elle laisse tout passer sans rien toucher."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or not RETENUE.active:
            await self.app(scope, receive, send)
            return
        chemin, methode = scope["path"], scope["method"]
        if methode == "PUT" and chemin == CHEMIN_ENREGISTRER:

            async def envoyer(message) -> None:
                await send(message)
                if message["type"] == "http.response.body" and not message.get("more_body", False):
                    RETENUE.put_envoye.set()

            await self.app(scope, receive, envoyer)
            return
        if methode != "POST" or chemin != CHEMIN_APERCU:
            await self.app(scope, receive, send)
            return
        messages = [await receive()]
        while messages[-1].get("more_body", False):
            messages.append(await receive())
        corps = b"".join(m.get("body", b"") for m in messages)
        restants = list(messages)

        async def rejouer():
            return restants.pop(0) if restants else await receive()

        if b'"automatique"' not in corps or not RETENUE.prendre():
            await self.app(scope, rejouer, send)
            return
        tampon: list = []

        async def retenir(message) -> None:
            tampon.append(message)

        await self.app(scope, rejouer, retenir)  # calculee maintenant, livree apres le PUT
        RETENUE.libere_apres_put = await asyncio.to_thread(RETENUE.put_envoye.wait, 60)
        for message in tampon:
            await send(message)
        RETENUE.active = False


class _Retenue:
    def __init__(self) -> None:
        self._verrou = threading.Lock()
        self.active = False  # armee jusqu'a la livraison de l'apercu retenu
        self._a_prendre = False
        self.put_envoye = threading.Event()
        self.libere_apres_put = False

    def armer(self) -> None:
        with self._verrou:
            self.put_envoye.clear()
            self.libere_apres_put = False
            self._a_prendre = self.active = True

    def prendre(self) -> bool:
        with self._verrou:
            pris, self._a_prendre = self._a_prendre, False
            return pris

    def desarmer(self) -> None:
        with self._verrou:
            self._a_prendre = self.active = False
            self.put_envoye.set()  # ne jamais laisser une requete retenue apres le deroulement


RETENUE = _Retenue()


def _port_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def config_cumul(projet, brut_config):
    brut_config["profil"] = PROFIL
    brut_config["acces"] = {}  # 127.0.0.1 : acces libre admis (jules/acces.py)
    return depuis_dict(brut_config, projet)


@pytest.fixture(scope="module")
def serveur(tmp_path_factory):
    """Serveur et projet partages par les tests navigateur du module : un seul lancement de Chromium
    (chaque lancement coute 5 a 15 s sous Windows et multiplie les occasions d'aleas)."""
    import shutil
    import threading
    import time

    import uvicorn

    from jules.llm.factice import Brique as Factice
    from jules.moteur import Tuteur

    projet = tmp_path_factory.mktemp("projet-page-parent")
    for dossier in ("persona", "consignes", "profils", "bibliotheque", "extensions"):
        shutil.copytree(RACINE / dossier, projet / dossier)
    brut = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))
    brut["llm"] = {"backend": "factice", "historique_max": 30}
    brut["profil"] = PROFIL
    brut["acces"] = {}  # 127.0.0.1 : acces libre admis (jules/acces.py)
    config = depuis_dict(brut, projet)
    tuteur = Tuteur(config, llm=Factice())
    app = creer_app(tuteur)
    html = (STATIQUE / "parent.html").read_text(encoding="utf-8")

    @app.get("/essai-parent", response_class=HTMLResponse)
    def essai_parent() -> HTMLResponse:
        return HTMLResponse(html.replace("</body>", '<script src="/essai-parent.js"></script></body>'))

    @app.get("/essai-parent.js")
    def essai_js() -> Response:
        return Response(ESSAI_JS, media_type="text/javascript; charset=utf-8")

    @app.get("/essai-ex110", response_class=HTMLResponse)
    def essai_ex110() -> HTMLResponse:
        return HTMLResponse(html.replace("</body>", '<script src="/essai-ex110.js"></script></body>'))

    @app.get("/essai-ex110.js")
    def essai_ex110_js() -> Response:
        return Response(ESSAI_EX110_JS, media_type="text/javascript; charset=utf-8")

    app.add_middleware(_RetenueApercu)  # inerte tant que RETENUE n'est pas armee (fixture page_ex110)

    port = _port_libre()
    serveur_uv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    fil = threading.Thread(target=serveur_uv.run, daemon=True)
    fil.start()
    limite = time.time() + 20
    while not serveur_uv.started and time.time() < limite:
        time.sleep(0.05)
    assert serveur_uv.started, "serveur Jules non demarre"
    # Echauffement : les premieres requetes chargent bibliotheques et referentiel (plusieurs secondes sous
    # charge). Faites ici, elles ne mangent pas le budget de temps virtuel de Chromium.
    import urllib.request

    for chemin in ("/api/infos", "/api/parent/adaptations", "/api/parent/modules", "/essai-parent"):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{chemin}", timeout=60) as reponse:
            assert reponse.status == 200, chemin
    yield f"http://127.0.0.1:{port}", config.fichier_profil
    serveur_uv.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


@pytest.fixture(scope="module")
def page(serveur):
    url, fichier_profil = serveur
    sortie, diagnostic = _ouvrir(f"{url}/essai-parent")
    trouve = re.search(r'data-resultat="([^"]*)"', sortie)
    assert trouve, diagnostic
    brut = trouve.group(1).replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return json.loads(brut), fichier_profil


def _ouvrir(adresse: str) -> tuple[str, str]:
    """DOM final de `adresse` rendu par Chromium headless, et le diagnostic a joindre aux assertions."""
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent (definir JULES_CHROMIUM)")
    # Sans --user-data-dir (profil temporaire du mode headless, comme test_lecture_vocale) : sous Windows,
    # un dossier de profil neuf bloque Chromium plus d'une minute au premier lancement. Acces libre en
    # 127.0.0.1 : aucun cookie de session n'est necessaire.
    options = ["--headless=new", "--no-sandbox", "--disable-gpu"]
    options += ["--virtual-time-budget=15000", "--dump-dom"]
    fini = subprocess.run(  # noqa: S603 - navigateur local, arguments fixes
        [navigateur, *options, adresse], capture_output=True, text=True, timeout=180, check=False
    )
    sortie = fini.stdout
    erreur = re.search(r'data-erreur="([^"]*)"', sortie)
    assert not erreur, f"erreur JavaScript : {erreur.group(1)}"
    etape = re.search(r'data-etape="([^"]*)"', sortie)
    etat = re.search(r'id="adaptations-etat"[^>]*>([^<]*)<', sortie)
    diagnostic = (
        f"code {fini.returncode}, etape {etape and etape.group(1)!r}, "
        f"{sortie.count('data-amenagement=')} attributs data-amenagement, etat {etat and etat.group(1)!r}"
    )
    return sortie, f"{diagnostic}\n{fini.stderr[-2000:]}"


@pytest.fixture(scope="module")
def page_ex110(serveur):
    """EX-110 : l'apercu A est retenu par le serveur jusqu'a l'envoi de la reponse du PUT. Le profil part de
    celui du depot (lecture automatique decochee), quel que soit l'ordre des tests : l'essai `page` enregistre
    la lecture automatique dans le profil partage du module. Il est remis tel quel ensuite."""
    url, fichier_profil = serveur
    avant = fichier_profil.read_bytes()
    fichier_profil.write_bytes((RACINE / "profils" / f"{PROFIL}.yaml").read_bytes())
    RETENUE.armer()
    try:
        sortie, diagnostic = _ouvrir(f"{url}/essai-ex110")
        return sortie, diagnostic, RETENUE.libere_apres_put
    finally:
        RETENUE.desarmer()
        fichier_profil.write_bytes(avant)


# --- navigateur (EX-012) -------------------------------------------------------------------------------


def test_libelles_college_et_rubrique_autres(page):
    r, _ = page
    avant = r["avant"]
    catalogue = charger_amenagements()
    assert avant["niveau"] == "collège"
    assert {li["id"] for li in avant["pap"]} == AVEC_LIBELLE_COLLEGE
    for li in avant["pap"]:
        libelle = catalogue[li["id"]].libelles["college"]
        assert li["texte"] == f"{libelle.texte} (p. {libelle.page})", li  # libelle entier, jamais tronque
        assert li["mention"] is None
    assert avant["autresVisible"] is True
    assert avant["autresTitre"] == f"{RUBRIQUE_AUTRES} (p. 8)"
    assert {li["id"] for li in avant["autres"]} == SANS_LIBELLE_COLLEGE
    for li in avant["autres"]:
        assert li["mention"] == f" : {MENTION_AUTRES}", li
    coches = {li["id"] for li in avant["pap"] + avant["autres"] if li["coche"]}
    assert coches == COCHES_LOT2


def test_preferences_hors_pap_affichees(page):
    r, _ = page
    assert r["avant"]["police"] == ["defaut", "arial", "verdana"]
    assert r["avant"]["fond"] == ["blanc", "creme", "bleu-pale"]
    assert r["avant"]["lectureAuto"] is False


def test_conflits_visibles_sans_etre_tranches(page):
    r, _ = page
    assert [c["id"] for c in r["avant"]["conflits"]] == [CONFLIT_TAILLE_DENSITE, CONFLIT_SURLIGNAGE_DENSITE]
    assert all(c["texte"] for c in r["avant"]["conflits"])
    # La lecture automatique cochee fait apparaitre son avertissement ; les cases restent cochees.
    apercu = r["apercu"]
    assert CONFLIT_LECTURE_AUTOMATIQUE in [c["id"] for c in apercu["conflits"]]
    assert apercu["lectureAuto"] is True
    assert {li["id"] for li in apercu["pap"] + apercu["autres"] if li["coche"]} == COCHES_LOT2


def test_aucun_terme_interdit_dans_la_page(page):
    r, _ = page
    assert "Aménagements du PAP" in r["texte"]  # le releve porte bien sur la page remplie
    assert trouver_terme(r["texte"], termes_interdits()) is None


def test_enregistrement_ne_contient_que_des_identifiants(page):
    r, fichier_profil = page
    assert r["apres"]["etat"] == "Enregistré."
    brut = yaml.safe_load(fichier_profil.read_text(encoding="utf-8"))
    attendus = sorted(COCHES_LOT2 - {"consignes-decomposees"})
    assert brut["amenagements"][:3] == IDS_LOT1  # lot 1 garde en tete, dans son ordre
    assert sorted(brut["amenagements"][3:]) == attendus
    assert all(isinstance(i, str) and MOTIF_ID_AMENAGEMENT.match(i) for i in brut["amenagements"])
    assert brut["preferences"] == {"fond": "creme", "lecture-vocale": "automatique"}
    # Aucun libelle ni message dans le fichier : que des identifiants.
    texte = fichier_profil.read_text(encoding="utf-8")
    for amenagement in charger_amenagements().values():
        for libelle in amenagement.libelles.values():
            assert libelle.texte not in texte
    assert RUBRIQUE_AUTRES not in texte and MENTION_AUTRES not in texte
    # Le reste du profil est intact et la relecture de la page reprend le choix enregistre.
    assert brut["prenom"] == "Alix" and brut["classe"] == "4e"
    assert brut["remarques"] == "Suivi amenagement-test-a depuis la rentrée ; aime les exemples concrets."
    assert r["apres"]["lectureAuto"] is True
    assert CONFLIT_LECTURE_AUTOMATIQUE in [c["id"] for c in r["apres"]["conflits"]]


def test_ex110_apercu_perime_ignore_apres_enregistrement(page_ex110):
    """EX-110 : la reponse d'un apercu anterieur a l'enregistrement, arrivee apres celle du PUT (ordre
    force par le serveur de test), ne change ni le message « Enregistré. » ni les conflits affiches."""
    sortie, diagnostic, libere_apres_put = page_ex110
    assert libere_apres_put, "mise en place : l'apercu retenu n'a pas attendu la reponse du PUT"
    termine = re.search(r'data-resultat="([^"]*)"', sortie)
    etat = re.search(r'id="adaptations-etat"[^>]*>([^<]*)<', sortie)
    assert termine and etat and etat.group(1) == "Enregistré.", diagnostic
    # Conflits de l'etat enregistre (lecture automatique decochee) : pas celui de l'apercu perime.
    conflits = re.findall(r'<li class="conflit" data-conflit="([^"]*)"', sortie)
    assert conflits == [CONFLIT_TAILLE_DENSITE, CONFLIT_SURLIGNAGE_DENSITE], diagnostic


# --- API : validation avant resoudre() ------------------------------------------------------------------


@pytest.fixture
def client(config_cumul):
    from jules.llm.factice import Brique as Factice
    from jules.moteur import Tuteur

    tuteur = Tuteur(config_cumul, llm=Factice())
    with TestClient(creer_app(tuteur)) as c:
        yield c, config_cumul.fichier_profil
    tuteur.fermer()


@pytest.mark.parametrize(
    "preferences",
    [
        {"lecture-vocale": ["automatique"]},  # non hachable : plantait resoudre() (TypeError)
        {"fond": {"x": 1}},
        {"lecture-vocale": "proposee"},  # reservee aux amenagements
        {"police": "comic-sans"},
        {"densite": "un-exercice"},  # levier hors §3
        {"inconnu": "x"},
        ["police"],
        "police",
        {"police": None},
    ],
)
def test_preference_invalide_refusee_avant_resoudre(client, monkeypatch, preferences):
    c, fichier_profil = client
    avant = fichier_profil.read_bytes()
    appels = []
    monkeypatch.setattr(page_adaptations, "resoudre", lambda *a, **k: appels.append(a))
    for methode, chemin in (("put", "/api/parent/adaptations"), ("post", "/api/parent/adaptations/apercu")):
        r = getattr(c, methode)(chemin, json={"amenagements": [], "preferences": preferences})
        assert r.status_code == 400, r.text
        assert r.json()["detail"]
    assert appels == []
    assert fichier_profil.read_bytes() == avant


@pytest.mark.parametrize("amenagements", [["inexistant"], [["supports-aeres-agrandis"]], "supports-aeres-agrandis"])
def test_amenagement_invalide_refuse(client, amenagements):
    c, fichier_profil = client
    avant = fichier_profil.read_bytes()
    r = c.put("/api/parent/adaptations", json={"amenagements": amenagements, "preferences": {}})
    assert r.status_code == 400 and r.json()["detail"]
    assert fichier_profil.read_bytes() == avant


def test_preference_neutre_non_enregistree(client):
    c, fichier_profil = client
    r = c.put("/api/parent/adaptations", json={"amenagements": [], "preferences": {"police": "defaut"}})
    assert r.status_code == 200
    brut = yaml.safe_load(fichier_profil.read_text(encoding="utf-8"))
    assert "preferences" not in brut
    assert brut["amenagements"] == IDS_LOT1


def test_preferences_jamais_dans_le_prompt(client):
    c, fichier_profil = client
    c.put("/api/parent/adaptations", json={"amenagements": [], "preferences": {"fond": "creme"}})
    profil = charger_profil(fichier_profil)
    assert "preferences" not in profil.details and "creme" not in profil.texte()


def _profil_copie(tmp_path: Path) -> Path:
    cible = tmp_path / f"{PROFIL}.yaml"
    cible.write_bytes((RACINE / "profils" / f"{PROFIL}.yaml").read_bytes())
    return cible


def _remplacement_refuse(monkeypatch, refus: int) -> list[int]:
    """Path.replace leve PermissionError les `refus` premieres fois, comme sous Windows quand un lecteur
    tient le profil ouvert (echec constate dans la suite ciblee : WinError 5 a l'enregistrement)."""
    appels = [0]
    vrai = Path.replace

    def remplacer(self, cible):
        appels[0] += 1
        if appels[0] <= refus:
            raise PermissionError(13, "Acces refuse (fichier ouvert par un lecteur)")
        return vrai(self, cible)

    monkeypatch.setattr(Path, "replace", remplacer)
    monkeypatch.setattr(page_adaptations.time, "sleep", lambda _s: None)
    return appels


def test_enregistrement_resiste_a_un_lecteur_windows(tmp_path, monkeypatch):
    fichier_profil = _profil_copie(tmp_path)
    appels = _remplacement_refuse(monkeypatch, refus=3)
    choix = page_adaptations.choix_depuis_entree(["surligner-mots-cles"], {"fond": "creme"})
    page_adaptations.enregistrer(fichier_profil, choix)
    brut = yaml.safe_load(fichier_profil.read_text(encoding="utf-8"))
    assert appels[0] == 4
    assert "surligner-mots-cles" in brut["amenagements"] and brut["preferences"] == {"fond": "creme"}
    assert list(tmp_path.glob(".profil-*")) == []


def test_enregistrement_abandonne_si_le_profil_reste_verrouille(tmp_path, monkeypatch):
    fichier_profil = _profil_copie(tmp_path)
    avant = fichier_profil.read_bytes()
    _remplacement_refuse(monkeypatch, refus=10_000)
    choix = page_adaptations.choix_depuis_entree(["surligner-mots-cles"], {})
    with pytest.raises(PermissionError):
        page_adaptations.enregistrer(fichier_profil, choix)
    assert fichier_profil.read_bytes() == avant
    assert list(tmp_path.glob(".profil-*")) == []


def test_page_adaptations_reservee_au_parent(projet, brut_config):
    from jules.acces import empreinte
    from jules.llm.factice import Brique as Factice
    from jules.moteur import Tuteur

    brut_config["profil"] = PROFIL
    brut_config["acces"] = {"code_eleve": empreinte("1234"), "code_parent": empreinte("parent67")}
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    with TestClient(creer_app(tuteur)) as c:
        assert c.get("/api/parent/adaptations").status_code == 401
        c.post("/api/session", json={"code": "1234"})
        assert c.get("/api/parent/adaptations").status_code == 401
        assert c.put("/api/parent/adaptations", json={"amenagements": []}).status_code == 401
    tuteur.fermer()


@pytest.mark.parametrize(
    ("classe", "niveau"),
    [
        ("4e", "college"),
        ("6ème", "college"),
        ("CM1", "elementaire"),
        ("CE 2", "elementaire"),
        ("2nde", "lycee"),
        ("Terminale", "lycee"),
        ("GS", "maternelle"),
        ("", None),
        ("inconnue", None),
    ],
)
def test_niveau_de_classe(classe, niveau):
    assert page_adaptations.niveau_de_classe(classe) == niveau
