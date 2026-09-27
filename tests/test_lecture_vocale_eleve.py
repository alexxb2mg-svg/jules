"""EX-109 (docs/spec/ADAPTATIONS-LOT2.md) : bouton de lecture cote eleve et mode automatique.

Les vraies pages eleve (`eleve.html`, `cours.html`) et leurs vrais scripts tournent dans un navigateur
headless (EX-012) ; seuls l'API de Jules (`fetch`) et la synthese vocale (`speechSynthesis`,
`SpeechSynthesisUtterance`) sont simules. La synthese simulee tient un journal de ce qui est dit et
interrompu : les tests lisent ce journal, pas les voix de la machine.

Un scenario = une suite d'actions d'eleve (demarrer une discussion, taper, envoyer, cliquer un bouton de
lecture) ; apres chaque etape on releve le journal de la synthese et l'etat des boutons.

Valeur du levier : lue dans `/api/infos` sous `leviers["lecture-vocale"]` (LectureVocale.modeDepuis).
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from jules.chantier_visuel import _chromium

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"

VOIX_LOCALE = {"name": "Locale", "lang": "fr-FR", "localService": True, "default": True}
VOIX_EN_LIGNE = {"name": "En ligne", "lang": "fr-FR", "localService": False, "default": False}

ACCUEIL = "C'est parti, Alix ! Envoie-moi ton message ou une photo de ton exercice."
REPONSE_1 = "Qu'est-ce que tu as deja essaye ?"
REPONSE_2 = "Bien vu, continue."
HISTORIQUE_JULES = "Bonjour, on reprend les fractions."
HISTORIQUE_ELEVE = "Je bloque sur 1/2 + 1/3"
CONSIGNE_EXERCICE = "Calcule 3 x 4."
CONSIGNE_QUESTION = "Explique pourquoi on reduit au meme denominateur."
BULLE_COURS = "Je suis la si tu bloques."

# Simulation installee avant tout script de la page : API de Jules et synthese vocale.
# La reponse aux messages est retardee (40 ms) pour que la bulle d'attente soit visible entre-temps.
SIMULATION = """
window.onerror = (message) => { document.documentElement.setAttribute("data-erreur", String(message)); };
const CAS = __CAS__;
const JOURNAL = [];
class EnonceSimule extends EventTarget {
  constructor(texte) { super(); this.text = texte; this.voice = null; this.lang = ""; }
}
window.SpeechSynthesisUtterance = EnonceSimule;
class SyntheseSimulee extends EventTarget {
  constructor(voix) { super(); this.voix = voix; this.courant = null; }
  getVoices() { return this.voix.slice(); }
  get speaking() { return this.courant !== null; }
  cancel() {
    JOURNAL.push(["cancel"]);
    const e = this.courant; this.courant = null;
    if (e) e.dispatchEvent(new Event("error"));  // comme un vrai moteur : l'enonce interrompu echoue
  }
  speak(enonce) { JOURNAL.push(["speak", enonce.text, enonce.voice && enonce.voice.name]); this.courant = enonce; }
  finir() { const e = this.courant; this.courant = null; if (e) e.dispatchEvent(new Event("end")); }
}
const SIMULEE = new SyntheseSimulee(CAS.voix);
Object.defineProperty(window, "speechSynthesis", { value: SIMULEE, configurable: true });
const reponses = [__REPONSE_1__, __REPONSE_2__];
const API = {
  "GET /api/session": () => ({ eleve: true }),
  "GET /api/infos": () => ({ persona: { nom: "Jules", couleurs: {} }, prenom: "Alix",
    modes: [{ id: "aide-devoirs", nom: "Aide", icone: "A", description: "d", cache: false }],
    leviers: CAS.mode === null ? undefined : { "lecture-vocale": CAS.mode } }),
  "GET /api/conversations": () => [{ id: "c-ancienne", mode: "aide-devoirs", titre: "Fractions", nb: 2, debut: "" }],
  "POST /api/conversations": () => ({ id: "c1", mode: "aide-devoirs" }),
  "GET /api/conversations/c-ancienne": () => ({ id: "c-ancienne", mode: "aide-devoirs", titre: "Fractions",
    messages: [{ role: "eleve", texte: __HISTORIQUE_ELEVE__, images: [] },
      { role: "bot", texte: __HISTORIQUE_JULES__, images: [] }] }),
  "POST /api/conversations/c1/messages": () => ({ reponse: reponses.shift() }),
  "POST /api/conversations/cc/messages": () => ({ reponse: reponses.shift() }),
  "GET /api/conversations/cc": () => ({ id: "cc", messages: [{ role: "bot", texte: __BULLE_COURS__ }] }),
  "GET /api/eleve/cours/parcours": () => ({ matieres: [{ id: "maths", nom: "Maths" }], matiere: "maths", estimation: "",
    notions: [{ id: "n1", titre: "Multiplier", chapitre: "Calcul", etat: "en_cours", lecon: true }] }),
  "POST /api/eleve/cours/lecons/n1/ouvrir": () => ({ session: "s1", conversation: "cc",
    lecon: { titre: "Multiplier", notion: "n1", matiere: "Maths", niveau: "3e", blocs: [
      { index: 0, type: "exercice", forme: "nombre", enonce: __CONSIGNE_EXERCICE__, indices: [] },
      { index: 1, type: "question_ouverte", question: __CONSIGNE_QUESTION__, indices: [] }] },
    progression: { bloc_courant: 0, termine: false, blocs: [
      { index: 0, etat: "a_faire", tentatives: 0, indices_vus: 0 },
      { index: 1, etat: "a_faire", tentatives: 0, indices_vus: 0 }] } }),
};
window.fetch = async (chemin, options = {}) => {
  const cle = `${(options.method || "GET").toUpperCase()} ${String(chemin).split("?")[0]}`;
  const f = API[cle];
  if (cle.endsWith("/messages")) await new Promise((r) => setTimeout(r, 40));
  return { status: f ? 200 : 404, ok: Boolean(f), json: async () => (f ? f() : { detail: cle }) };
};
navigator.sendBeacon = () => true;
"""

# Outils du scenario, ajoutes en fin de page.
OUTILS = """
const pause = (ms) => new Promise((r) => setTimeout(r, ms));
const $ = (s) => document.querySelector(s);
const boutonsLecture = () => Array.from(document.querySelectorAll("button.lecture-vocale-bouton"));
const visible = (b) => !b.hidden && !b.classList.contains("cache");
function releve() {
  const bulles = Array.from(document.querySelectorAll(".ligne")).map((l) => {
    const b = l.querySelector("button.lecture-vocale-bouton");
    return { role: l.classList.contains("eleve") ? "eleve" : "bot", attente: l.classList.contains("attente"),
      bouton: b ? (visible(b) ? b.getAttribute("aria-pressed") : "cache") : null };
  });
  const consignes = Array.from(document.querySelectorAll(".bloc-enonce")).map((p) => {
    const b = p.querySelector("button.lecture-vocale-bouton");
    return b ? (visible(b) ? b.getAttribute("aria-pressed") : "cache") : null;
  });
  return { journal: JOURNAL.slice(), bulles, consignes, boutons: boutonsLecture().filter(visible).length };
}
async function taper(champ, texte) {
  champ.value = texte;
  champ.dispatchEvent(new Event("input", { bubbles: true }));
}
async function envoyer(texte) {
  await taper($("#texte"), texte);
  $("#formulaire").requestSubmit();
  await pause(15);
  const pendant = releve();
  await pause(120);
  return pendant;
}
const etapes = {};
(async () => {
  try {
    await pause(80);
    await __SCENARIO__;
  } catch (err) { etapes.erreur = String(err && err.stack || err); }
  document.documentElement.setAttribute("data-resultat", JSON.stringify(etapes));
})();
"""

# Scenarios sur la page de discussion (eleve.html).
SCENARIO_DISCUSSION = """(async () => {
  etapes.chargement = releve();
  $(".modes button").click();                       // nouvelle discussion : bulle d'accueil de Jules
  await pause(60);
  etapes.accueil = releve();
  await taper($("#texte"), "je");                   // l'eleve tape pendant la lecture
  etapes.frappe = releve();
  etapes.pendant_envoi = await envoyer("1/2 + 1/3 ?");  // bulle eleve + attente, puis reponse de Jules
  etapes.reponse_1 = releve();
  const bouton = boutonsLecture().filter(visible).pop();
  if (bouton) bouton.click();                       // « arreter » la bulle en cours
  etapes.arret = releve();
  etapes.apres_arret = await envoyer("d'accord");   // la suite de la seance est encore lue
  etapes.reponse_2 = releve();
  SIMULEE.finir();                                  // fin naturelle de la lecture
  etapes.fin_naturelle = releve();
  const premier = boutonsLecture().filter(visible)[0];
  if (premier) premier.click();                     // relire au clic une bulle deja lue
  etapes.relecture = releve();
  const second = boutonsLecture().filter(visible)[1];
  if (second) second.click();                       // un autre bouton interrompt le premier
  etapes.autre_bouton = releve();
  $("#historique button").click();                  // conversation passee : rien n'est lu d'office
  await pause(60);
  etapes.historique = releve();
})()"""

# Scenario sur la page de cours (consignes et bulle du panneau Jules).
SCENARIO_COURS = """(async () => {
  // Premiere visite (EX-209 j, navigation N4) : aucune matiere imposee, l'eleve la choisit d'abord.
  $(".choix-matiere-bouton").click();
  await pause(80);
  $(".notion-ligne").click();
  await pause(80);
  etapes.lecon = releve();
  const consigne = document.querySelector(".bloc-enonce button.lecture-vocale-bouton");
  if (consigne) consigne.click();
  etapes.clic_consigne = releve();
  await taper(document.querySelector(".bloc input[type=text]"), "12");  // taper une reponse d'exercice
  etapes.frappe_reponse = releve();
  await taper($("#jules-texte"), "Tu peux m'aider ?");
  $("#jules-formulaire").requestSubmit();
  await pause(150);
  etapes.bulle_cours = releve();
  const consigne2 = document.querySelectorAll(".bloc-enonce button.lecture-vocale-bouton")[1];
  if (consigne2) consigne2.click();                 // la question ouverte est lue au clic...
  etapes.consigne_lue = releve();
  $("#jules-texte").value = "Et apres ?";           // (valeur posee sans evenement input : pas de frappe)
  $("#jules-formulaire").requestSubmit();           // ...quand la reponse de Jules arrive
  await pause(150);
  etapes.interruption = releve();
})()"""


def _navigateur() -> str:
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent (definir JULES_CHROMIUM)")
    return navigateur


def _executer(navigateur: str, page: Path) -> dict:
    options = ["--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files"]
    options += ["--virtual-time-budget=5000", "--dump-dom"]
    sortie = subprocess.run(  # noqa: S603 - navigateur local, arguments fixes
        [navigateur, *options, page.as_uri()], capture_output=True, text=True, timeout=120, check=True
    ).stdout
    erreur = re.search(r'data-erreur="([^"]*)"', sortie)
    assert not erreur, f"erreur JavaScript dans {page.name} : {erreur.group(1)}"
    brut = re.search(r'data-resultat="([^"]*)"', sortie)
    assert brut, sortie[-2000:]
    resultat = json.loads(brut.group(1).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<"))
    assert "erreur" not in resultat, resultat["erreur"]
    return resultat


def _page(dossier: Path, gabarit: str, nom: str, mode: str | None, voix: list, scenario: str) -> Path:
    constantes = {
        "__REPONSE_1__": REPONSE_1,
        "__REPONSE_2__": REPONSE_2,
        "__HISTORIQUE_JULES__": HISTORIQUE_JULES,
        "__HISTORIQUE_ELEVE__": HISTORIQUE_ELEVE,
        "__BULLE_COURS__": BULLE_COURS,
        "__CONSIGNE_EXERCICE__": CONSIGNE_EXERCICE,
        "__CONSIGNE_QUESTION__": CONSIGNE_QUESTION,
    }
    simulation = SIMULATION.replace("__CAS__", json.dumps({"mode": mode, "voix": voix}))
    for cle, valeur in constantes.items():
        simulation = simulation.replace(cle, json.dumps(valeur))
    html = (STATIQUE / gabarit).read_text(encoding="utf-8")
    html = (
        html.replace('src="/static/', 'src="')
        .replace('href="/static/', 'href="')
        .replace('src="/rappels.js"', 'src="rappels.js"')
    )
    html = html.replace("<head>", f"<head><script>{simulation}</script>", 1)
    html = html.replace("</body>", f"<script>{OUTILS.replace('__SCENARIO__', scenario)}</script></body>")
    fichier = dossier / f"{nom}.html"
    fichier.write_text(html, encoding="utf-8")
    return fichier


def _preparer(dossier: Path) -> None:
    for fichier in STATIQUE.glob("*.js"):
        (dossier / fichier.name).write_text(fichier.read_text(encoding="utf-8"), encoding="utf-8")
    for fichier in STATIQUE.glob("*.css"):
        (dossier / fichier.name).write_text(fichier.read_text(encoding="utf-8"), encoding="utf-8")
    (dossier / "rappels.js").write_text("", encoding="utf-8")


# (page, mode du levier, voix) ; mode None = /api/infos sans `leviers`.
CAS = {
    "automatique": ("eleve.html", "automatique", [VOIX_EN_LIGNE, VOIX_LOCALE], SCENARIO_DISCUSSION),
    "proposee": ("eleve.html", "proposee", [VOIX_LOCALE], SCENARIO_DISCUSSION),
    "absente": ("eleve.html", "absente", [VOIX_LOCALE], SCENARIO_DISCUSSION),
    "sans_levier": ("eleve.html", None, [VOIX_LOCALE], SCENARIO_DISCUSSION),
    "automatique_sans_voix_locale": ("eleve.html", "automatique", [VOIX_EN_LIGNE], SCENARIO_DISCUSSION),
    "proposee_sans_voix": ("eleve.html", "proposee", [], SCENARIO_DISCUSSION),
    "cours_automatique": ("cours.html", "automatique", [VOIX_LOCALE], SCENARIO_COURS),
    "cours_proposee": ("cours.html", "proposee", [VOIX_LOCALE], SCENARIO_COURS),
    "cours_sans_voix_locale": ("cours.html", "automatique", [VOIX_EN_LIGNE], SCENARIO_COURS),
}


@pytest.fixture(scope="module")
def scenarios(tmp_path_factory):
    navigateur = _navigateur()
    dossier = tmp_path_factory.mktemp("lecture_eleve")
    _preparer(dossier)
    return {
        nom: _executer(navigateur, _page(dossier, gabarit, nom, mode, voix, scenario))
        for nom, (gabarit, mode, voix, scenario) in CAS.items()
    }


def _dits(etape: dict) -> list[str]:
    return [e[1] for e in etape["journal"] if e[0] == "speak"]


def _nouveaux(avant: dict, apres: dict) -> list[list]:
    return apres["journal"][len(avant["journal"]) :]


# --- visibilite du bouton ------------------------------------------------------------------------------


@pytest.mark.parametrize("cas", ["automatique", "proposee"])
def test_bouton_sur_chaque_bulle_de_jules_et_jamais_sur_l_eleve(scenarios, cas):
    r = scenarios[cas]["reponse_2"]
    jules = [b for b in r["bulles"] if b["role"] == "bot"]
    eleve = [b for b in r["bulles"] if b["role"] == "eleve"]
    assert len(jules) == 3 and all(b["bouton"] in ("true", "false") for b in jules), r["bulles"]
    assert len(eleve) == 2 and all(b["bouton"] is None for b in eleve), r["bulles"]


@pytest.mark.parametrize("cas", ["cours_automatique", "cours_proposee"])
def test_bouton_sur_chaque_consigne(scenarios, cas):
    r = scenarios[cas]["lecon"]
    assert r["consignes"] == ["false", "false"]  # exercice et question ouverte


@pytest.mark.parametrize(
    "cas", ["automatique_sans_voix_locale", "proposee_sans_voix", "cours_sans_voix_locale", "absente", "sans_levier"]
)
def test_aucune_voix_locale_ou_levier_absent_aucun_bouton_et_rien_n_est_lu(scenarios, cas):
    for nom, etape in scenarios[cas].items():
        assert etape["boutons"] == 0, (nom, etape)
        assert _dits(etape) == [], (nom, etape["journal"])


@pytest.mark.parametrize("cas", ["absente", "sans_levier"])
def test_levier_absent_aucun_bouton_cree_rendu_d_aujourd_hui(scenarios, cas):
    r = scenarios[cas]["reponse_2"]
    assert all(b["bouton"] is None for b in r["bulles"]), r["bulles"]


def test_mode_propose_rien_n_est_lu_sans_clic(scenarios):
    r = scenarios["proposee"]
    assert _dits(r["reponse_1"]) == []  # accueil et reponse affichees, rien de lu
    # Le seul clic du scenario avant la reponse 2 (bouton de la reponse 1) lit cette bulle, et la
    # reponse 2 arrivee ensuite n'est pas lue d'office.
    assert _nouveaux(r["reponse_1"], r["arret"]) == [["cancel"], ["speak", REPONSE_1, VOIX_LOCALE["name"]]]
    assert REPONSE_2 not in _dits(r["reponse_2"])


# --- mode automatique ---------------------------------------------------------------------------------


def test_automatique_la_nouvelle_bulle_de_jules_est_lue_une_fois_a_son_affichage_complet(scenarios):
    r = scenarios["automatique"]
    assert r["chargement"]["journal"] == []
    assert _dits(r["accueil"]) == [ACCUEIL]
    assert r["accueil"]["bulles"][-1]["bouton"] == "true"  # le bouton montre « arreter »
    # Voix locale uniquement (EX-006), meme si une voix en ligne vient en premier.
    assert all(e[2] == VOIX_LOCALE["name"] for e in r["accueil"]["journal"] if e[0] == "speak")
    # Une fois : la bulle d'accueil n'est plus jamais redite d'office ensuite.
    assert _dits(r["reponse_2"]).count(ACCUEIL) == 1
    assert _dits(r["reponse_1"]).count(REPONSE_1) == 1 and _dits(r["reponse_2"]).count(REPONSE_1) == 1


def test_automatique_la_bulle_d_attente_n_est_pas_lue_ni_equipee(scenarios):
    pendant = scenarios["automatique"]["pendant_envoi"]
    attente = [b for b in pendant["bulles"] if b["attente"]]
    assert len(attente) == 1 and attente[0]["bouton"] is None
    assert "Jules réfléchit…" not in _dits(pendant)


def test_automatique_les_messages_de_l_eleve_ne_sont_jamais_lus(scenarios):
    dits = _dits(scenarios["automatique"]["historique"])
    assert "1/2 + 1/3 ?" not in dits and "d'accord" not in dits and HISTORIQUE_ELEVE not in dits


def test_automatique_les_consignes_ne_sont_lues_qu_au_clic(scenarios):
    r = scenarios["cours_automatique"]
    assert CONSIGNE_EXERCICE not in _dits(r["lecon"]) and CONSIGNE_QUESTION not in _dits(r["lecon"])
    assert _nouveaux(r["lecon"], r["clic_consigne"]) == [["cancel"], ["speak", CONSIGNE_EXERCICE, VOIX_LOCALE["name"]]]
    assert r["clic_consigne"]["consignes"] == ["true", "false"]
    # Une nouvelle bulle de Jules dans le panneau du cours est lue, la question ouverte jamais.
    assert _dits(r["bulle_cours"])[-1] == REPONSE_1
    assert CONSIGNE_QUESTION not in _dits(r["bulle_cours"])


def test_un_bouton_de_lecture_interrompt_la_lecture_en_cours(scenarios):
    r = scenarios["automatique"]
    nouveaux = _nouveaux(r["relecture"], r["autre_bouton"])
    assert nouveaux == [["cancel"], ["speak", REPONSE_1, VOIX_LOCALE["name"]]]
    assert [b["bouton"] for b in r["autre_bouton"]["bulles"] if b["role"] == "bot"] == ["false", "true", "false"]


def test_automatique_nouvelle_bulle_pendant_une_lecture_l_interrompt(scenarios):
    r = scenarios["cours_automatique"]
    assert r["consigne_lue"]["journal"][-1] == ["speak", CONSIGNE_QUESTION, VOIX_LOCALE["name"]]
    assert r["consigne_lue"]["consignes"] == ["false", "true"]
    # La reponse de Jules arrive pendant la lecture de la consigne : cancel puis lecture de la bulle.
    assert _nouveaux(r["consigne_lue"], r["interruption"]) == [["cancel"], ["speak", REPONSE_2, VOIX_LOCALE["name"]]]
    assert r["interruption"]["consignes"] == ["false", "false"]
    jules = [b for b in r["interruption"]["bulles"] if b["role"] == "bot"]
    assert [b["bouton"] for b in jules][-2:] == ["false", "true"]


def test_automatique_nouvelle_bulle_du_panneau_de_cours_lue(scenarios):
    r = scenarios["cours_automatique"]
    assert _nouveaux(r["frappe_reponse"], r["bulle_cours"]) == [["cancel"], ["speak", REPONSE_1, VOIX_LOCALE["name"]]]
    # La bulle presente a l'ouverture de la lecon (historique de la conversation) n'a pas ete lue.
    assert BULLE_COURS not in _dits(r["bulle_cours"])


def test_automatique_taper_dans_le_champ_arrete_la_lecture(scenarios):
    r = scenarios["automatique"]
    assert _nouveaux(r["accueil"], r["frappe"]) == [["cancel"]]
    assert r["frappe"]["bulles"][-1]["bouton"] == "false"
    # Idem en cours : taper une reponse d'exercice arrete la consigne lue.
    c = scenarios["cours_automatique"]
    assert _nouveaux(c["clic_consigne"], c["frappe_reponse"]) == [["cancel"]]
    assert c["frappe_reponse"]["consignes"] == ["false", "false"]


def test_automatique_arreter_ne_vaut_que_pour_la_bulle_en_cours(scenarios):
    r = scenarios["automatique"]
    assert r["reponse_1"]["bulles"][-1]["bouton"] == "true"
    assert _nouveaux(r["reponse_1"], r["arret"]) == [["cancel"]]
    assert r["arret"]["bulles"][-1]["bouton"] == "false"
    # La bulle suivante de la seance est lue quand meme.
    assert _dits(r["reponse_2"])[-1] == REPONSE_2
    assert r["reponse_2"]["bulles"][-1]["bouton"] == "true"


def test_fin_naturelle_de_la_lecture_rend_le_bouton(scenarios):
    r = scenarios["automatique"]
    assert r["fin_naturelle"]["journal"] == r["reponse_2"]["journal"]
    assert all(b["bouton"] != "true" for b in r["fin_naturelle"]["bulles"])


def test_automatique_une_conversation_rouverte_n_est_pas_lue_d_office(scenarios):
    r = scenarios["automatique"]
    assert _nouveaux(r["autre_bouton"], r["historique"]) == []
    jules = [b for b in r["historique"]["bulles"] if b["role"] == "bot"]
    assert jules == [{"role": "bot", "attente": False, "bouton": "false"}]


# --- statique -----------------------------------------------------------------------------------------


@pytest.mark.parametrize(("page", "script"), [("eleve.html", "eleve.js"), ("cours.html", "cours.js")])
def test_les_pages_eleve_chargent_le_module_avant_leur_script(page, script):
    html = (STATIQUE / page).read_text(encoding="utf-8")
    assert html.index("/static/commun.js") < html.index("/static/lecture-vocale.js") < html.index(f"/static/{script}")
