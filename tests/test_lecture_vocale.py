"""Lecture vocale (spec ADAPTATIONS, EX-006 et EX-007) : voix locales uniquement.

Le comportement est verifie dans un vrai navigateur, avec `speechSynthesis` remplace par une synthese
simulee : le resultat ne depend donc pas des voix installees sur la machine qui lance les tests. Les noms
des voix simulees sont volontairement trompeurs, pour prouver que le filtre porte sur `localService` et
jamais sur le nom.
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
MODULE = STATIQUE / "lecture-vocale.js"

LOCALE_FR = {"name": "Voix en ligne (nom trompeur)", "lang": "fr-FR", "localService": True, "default": False}
LOCALE_EN = {"name": "English", "lang": "en-US", "localService": True, "default": True}
EN_LIGNE_FR = {"name": "Voix locale (nom trompeur)", "lang": "fr-FR", "localService": False, "default": False}
EN_LIGNE_EN = {"name": "Online English", "lang": "en-GB", "localService": False, "default": False}

# (voix au chargement, voix apres voiceschanged ou None si l'evenement n'arrive jamais)
CAS = {
    "locales": ([EN_LIGNE_FR, LOCALE_EN, LOCALE_FR], None),
    "en_ligne_seulement": ([EN_LIGNE_FR, EN_LIGNE_EN], None),
    "aucune": ([], None),
    "vide_puis_remplie": ([], [EN_LIGNE_FR, LOCALE_FR]),
}

# Synthese simulee, installee avant tout script de la page. Elle note les voix utilisees par speak().
SIMULATION = """
window.onerror = (message) => { document.body.setAttribute("data-erreur", String(message)); };
class EnonceSimule { constructor(texte) { this.text = texte; this.voice = null; this.lang = ""; } }
window.SpeechSynthesisUtterance = EnonceSimule;  // la vraie refuse une voix qui n'est pas une SpeechSynthesisVoice
class SyntheseSimulee extends EventTarget {
  constructor(voix) { super(); this.voix = voix; this.lues = []; }
  getVoices() { return this.voix.slice(); }
  cancel() {}
  speak(enonce) { this.lues.push({ texte: enonce.text, voix: enonce.voice && enonce.voice.name }); }
}
const CAS_VOIX = __CAS__;
const SIMULEE = new SyntheseSimulee(CAS_VOIX[0]);
Object.defineProperty(window, "speechSynthesis", { value: SIMULEE, configurable: true });
window.fetch = () => new Promise(() => {});  // page parent : aucun serveur, la porte attend en silence
"""

# Releve : etat avant (apres chargement) puis, si le cas le prevoit, apres voiceschanged.
RELEVE = """
const releve = { avant: __ETAT__ };
setTimeout(() => {
  if (CAS_VOIX[1]) { SIMULEE.voix = CAS_VOIX[1]; SIMULEE.dispatchEvent(new Event("voiceschanged")); }
  releve.apres = __ETAT__;
  __FIN__
  document.body.setAttribute("data-resultat", JSON.stringify(releve));
}, 50);
"""


def _navigateur() -> str:
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent (definir JULES_CHROMIUM)")
    return navigateur


def _executer(navigateur: str, page: Path) -> dict:
    options = ["--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files"]
    options += ["--virtual-time-budget=2000", "--dump-dom"]
    sortie = subprocess.run(  # noqa: S603 - navigateur local, arguments fixes
        [navigateur, *options, page.as_uri()], capture_output=True, text=True, timeout=120, check=True
    ).stdout
    erreur = re.search(r'data-erreur="([^"]*)"', sortie)
    assert not erreur, f"erreur JavaScript dans {page.name} : {erreur.group(1)}"
    brut = re.search(r'data-resultat="([^"]*)"', sortie)
    assert brut, sortie[-2000:]
    return json.loads(brut.group(1).replace("&quot;", '"').replace("&amp;", "&"))


def _simulation(cas: str) -> str:
    return SIMULATION.replace("__CAS__", json.dumps(list(CAS[cas]), ensure_ascii=False))


# --- EX-006 : le module, avec un bouton de lecture -----------------------------------------------------

ETAT_BOUTON = (
    '({ visible: !bouton.hidden && !bouton.classList.contains("cache"), '
    "locales: LectureVocale.voixLocales(speechSynthesis.getVoices()).map((v) => v.name), "
    "choisie: (LectureVocale.voixChoisie() || {}).name || null })"
)


FIN_BOUTON = 'bouton.click(); releve.lues = SIMULEE.lues.slice(); releve.lecture_directe = LectureVocale.lire("x");'


@pytest.fixture(scope="module")
def module_vocal(tmp_path_factory):
    navigateur = _navigateur()
    dossier = tmp_path_factory.mktemp("lecture_vocale")
    (dossier / "lecture-vocale.js").write_text(MODULE.read_text(encoding="utf-8"), encoding="utf-8")
    resultats = {}
    for cas in CAS:
        releve = RELEVE.replace("__ETAT__", ETAT_BOUTON).replace("__FIN__", FIN_BOUTON)
        page = dossier / f"{cas}.html"
        page.write_text(
            f'<!doctype html><meta charset="utf-8"><body><button id="lire">Lire</button>'
            f"<script>{_simulation(cas)}</script>"
            '<script src="lecture-vocale.js"></script>'
            '<script>const bouton = document.getElementById("lire");'
            'LectureVocale.initialiser(); LectureVocale.brancherBouton(bouton, "Bonjour");'
            f"{releve}</script></body>",
            encoding="utf-8",
        )
        resultats[cas] = _executer(navigateur, page)
    return resultats


def test_voix_locales_presentes_bouton_affiche_et_seule_une_voix_locale_lit(module_vocal):
    r = module_vocal["locales"]
    assert r["avant"]["visible"] is True
    assert r["avant"]["locales"] == [LOCALE_EN["name"], LOCALE_FR["name"]]  # filtre sur localService, pas le nom
    assert r["avant"]["choisie"] == LOCALE_FR["name"]  # francaise d'abord, choisie par la langue
    assert r["lues"] == [{"texte": "Bonjour", "voix": LOCALE_FR["name"]}]
    assert r["lecture_directe"] is True


def test_uniquement_des_voix_en_ligne_pas_de_bouton_et_rien_n_est_lu(module_vocal):
    r = module_vocal["en_ligne_seulement"]
    assert r["avant"] == {"visible": False, "locales": [], "choisie": None}
    assert r["apres"]["visible"] is False
    assert r["lues"] == [] and r["lecture_directe"] is False


def test_aucune_voix_pas_de_bouton(module_vocal):
    r = module_vocal["aucune"]
    assert r["avant"] == {"visible": False, "locales": [], "choisie": None}
    assert r["lues"] == [] and r["lecture_directe"] is False


def test_liste_vide_puis_remplie_le_bouton_apparait_apres_voiceschanged(module_vocal):
    r = module_vocal["vide_puis_remplie"]
    assert r["avant"]["visible"] is False
    assert r["apres"] == {"visible": True, "locales": [LOCALE_FR["name"]], "choisie": LOCALE_FR["name"]}
    assert r["lues"] == [{"texte": "Bonjour", "voix": LOCALE_FR["name"]}]


# --- EX-007 : la vraie page parent, avec le texte affiche --------------------------------------------

ETAT_PARENT = (
    '({ texte: document.getElementById("lecture-vocale-etat").textContent, '
    'disponible: document.getElementById("lecture-vocale-etat").dataset.disponible })'
)


@pytest.fixture(scope="module")
def page_parent(tmp_path_factory):
    navigateur = _navigateur()
    dossier = tmp_path_factory.mktemp("parent_vocal")
    for nom in ("symboles.js", "commun.js", "lecture-vocale.js", "parent.js"):
        (dossier / nom).write_text((STATIQUE / nom).read_text(encoding="utf-8"), encoding="utf-8")
    (dossier / "rappels.js").write_text("", encoding="utf-8")
    html = (STATIQUE / "parent.html").read_text(encoding="utf-8")
    html = html.replace('src="/static/', 'src="').replace('src="/rappels.js"', 'src="rappels.js"')
    resultats = {}
    for cas in CAS:
        releve = RELEVE.replace("__ETAT__", ETAT_PARENT).replace("__FIN__", "")
        page = html.replace("<body>", f"<body><script>{_simulation(cas)}</script>", 1)
        page = page.replace("</body>", f"<script>{releve}</script></body>")
        fichier = dossier / f"{cas}.html"
        fichier.write_text(page, encoding="utf-8")
        resultats[cas] = _executer(navigateur, fichier)
    return resultats


def _textes():
    js = MODULE.read_text(encoding="utf-8")
    disponible = re.search(r'TEXTE_DISPONIBLE = "([^"]+)"', js).group(1)
    indisponible = re.search(r'TEXTE_INDISPONIBLE = "([^"]+)"', js).group(1)
    return disponible, indisponible


@pytest.mark.parametrize(
    ("cas", "avant", "apres"),
    [
        ("locales", "oui", "oui"),
        ("en_ligne_seulement", "non", "non"),
        ("aucune", "non", "non"),
        ("vide_puis_remplie", "non", "oui"),
    ],
)
def test_la_page_parent_constate_la_disponibilite(page_parent, cas, avant, apres):
    disponible, indisponible = _textes()
    texte = {"oui": disponible, "non": indisponible}
    r = page_parent[cas]
    assert r["avant"] == {"texte": texte[avant], "disponible": avant}
    assert r["apres"] == {"texte": texte[apres], "disponible": apres}


def test_aucun_navigateur_nomme_et_aucun_filtre_sur_le_nom():
    marques = re.compile(r"\b(chrome|chromium|edge|firefox|safari|opera|brave|samsung|google|microsoft)\b", re.I)
    for fichier in (MODULE, STATIQUE / "parent.html"):
        assert not marques.search(fichier.read_text(encoding="utf-8")), fichier.name
    js = MODULE.read_text(encoding="utf-8")
    assert "localService === true" in js
    assert not re.search(r"\.name\b", js)  # le module ne lit jamais le nom d'une voix


def test_la_page_parent_charge_le_module_avant_son_script():
    html = (STATIQUE / "parent.html").read_text(encoding="utf-8")
    assert html.index("/static/lecture-vocale.js") < html.index("/static/parent.js")
    assert 'id="lecture-vocale-etat"' in html
