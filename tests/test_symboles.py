"""Bulles de rappel au survol : un module commun a toutes les pages (jules/web/static/rappels.js et symboles.*)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from jules.chantier_visuel import _chromium

STATIQUE = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"
PAGES = sorted(STATIQUE.glob("*.html"))
RAPPELS = (STATIQUE / "rappels.js").read_text(encoding="utf-8")


def _section(nom: str) -> str:
    return RAPPELS.split(f"  {nom}: {{", 1)[1].split("\n  },", 1)[0]


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_chaque_page_charge_le_module(page):
    html = page.read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/static/symboles.css">' in html
    # Dictionnaires, puis moteur, puis les scripts de la page : tout ce qu'ils affichent est observe.
    assert html.index("/static/rappels.js") < html.index("/static/symboles.js") < html.index("/static/commun.js")


def test_chaque_page_rappelle_ce_qui_est_propre_a_sa_notion():
    for page, appel in [
        ("accueil.js", "Symboles.contexte("),
        ("eleve.js", "Symboles.notion("),
        ("studio.js", "Symboles.notion("),
        ("cours.js", "Symboles.notion("),
    ]:
        assert appel in (STATIQUE / page).read_text(encoding="utf-8"), page


def test_dictionnaires():
    symboles = dict(re.findall(r'^\s+"(.+?)": "(.+?)",$', _section("symboles"), flags=re.M))
    assert {"<", ">", "≤", "≥", "≠", "≈", "√", "π", "→"} <= set(symboles)
    # Les operations evidentes n'ont pas de bulle : ce sont les lettres des formules qu'on rappelle.
    assert not {"×", "÷", "+", "="} & set(symboles)
    unites = dict(re.findall(r'^\s+"(.+?)": "(.+?)",$', _section("unites"), flags=re.M))
    assert unites["s"] == "secondes" and unites["kg"] == "kilogrammes" and unites["m"] == "mètres"
    assert {"N", "J", "W", "V", "A", "Ω", "Hz", "m/s", "km/h", "g/cm³", "°C"} <= set(unites)
    elements = re.findall(r"\b([A-Z][a-z]?): \"", _section("elements"))
    assert len(elements) == len(set(elements)) == 118
    assert "innerHTML" not in (STATIQUE / "symboles.js").read_text(encoding="utf-8").replace("Jamais d'innerHTML", "")


# --- comportement, dans un vrai navigateur (saute si Chromium est absent) ---------------------------

TEXTES = [
    ("formule", "Pour un poids : écrire P = m × g, puis m = P ÷ g."),
    ("unites", "Un sac de 10 kg pèse 98 N ; il tombe en 2 s, à 5 m/s."),
    ("chimie", "La combustion rejette du CO₂ et de l'eau H₂O ; l'ion Cu²⁺ est bleu."),
    ("elements", "Au début, les éléments légers : H, He. Le fer (Fe) et l'or (Au)."),
    ("prose", "Si tu as une masse, il a raison : c'est la vitesse d'un objet."),
    ("abreviation", "La Terre est à 1 ua du Soleil."),
    ("parentheses", "La puissance en watts (W), la tension en volts (V) ; l'azote (N). Source : BO n° 31."),
    ("equation", "Combustion : C + O₂ → CO₂, et on convertit km/h → m/s."),
    ("mg", "Le poids : P = mg, soit 2 mg de poudre."),
    ("unite_en", "La distance en m, la masse en g."),
    ("phrase", "Vérifie que m est en kg et que la vitesse est en m/s : il y a une erreur, il a oublié g."),
]


@pytest.fixture(scope="module")
def annotations(tmp_path_factory):
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent")
    dossier = tmp_path_factory.mktemp("symboles")
    for f in ("rappels.js", "symboles.js"):
        shutil.copy(STATIQUE / f, dossier / f)
    paragraphes = "\n".join(f'<p id="{i}">{t}</p>' for i, t in TEXTES)
    script = """
      Symboles.contexte(document.body, {variables: {P: "le poids", m: "la masse", g: "la pesanteur"},
                                        abreviations: {ua: "unité astronomique"}});
      const r = {};
      for (const p of document.querySelectorAll("p")) r[p.id] = {
        formules: [...p.querySelectorAll(".formule-texte")].map((e) => e.textContent),
        bulles: [...p.querySelectorAll("abbr.symbole")].map((e) => e.dataset.nom),
      };
      document.body.setAttribute("data-resultat", JSON.stringify(r));
    """
    page = dossier / "page.html"
    page.write_text(
        f'<!doctype html><meta charset="utf-8"><body>{paragraphes}<script src="rappels.js"></script>'
        f'<script src="symboles.js"></script><script>{script}</script></body>',
        encoding="utf-8",
    )
    options = ["--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files", "--dump-dom"]
    sortie = subprocess.run(  # noqa: S603 - navigateur local, arguments fixes
        [navigateur, *options, page.as_uri()], capture_output=True, text=True, timeout=120, check=True
    ).stdout
    brut = re.search(r'data-resultat="([^"]*)"', sortie).group(1)
    return json.loads(brut.replace("&quot;", '"').replace("&amp;", "&"))


def _bulles(annotations, cle):
    return annotations[cle]["bulles"]


def test_une_formule_du_texte_passe_en_gras_et_ses_lettres_ont_leur_bulle(annotations):
    assert annotations["formule"]["formules"] == ["P = m × g", "m = P ÷ g"]
    assert "P : le poids" in _bulles(annotations, "formule") and "g : la pesanteur" in _bulles(annotations, "formule")


def test_les_unites_apres_un_nombre(annotations):
    bulles = _bulles(annotations, "unites")
    assert {"kg : kilogrammes", "N : newtons (unité de force et de poids)", "s : secondes"} <= set(bulles)
    assert "m/s : mètres par seconde" in bulles


def test_especes_et_ions_avec_leur_composition(annotations):
    bulles = _bulles(annotations, "chimie")
    assert "CO₂ : dioxyde de carbone : 1 atome de carbone, 2 atomes d'oxygène" in bulles
    assert any(b.startswith("H₂O : eau : 2 atomes d'hydrogène, 1 atome d'oxygène") for b in bulles)
    assert any(b.startswith("Cu²⁺ : ion cuivre II") and "2 charges positives" in b for b in bulles)


def test_elements_hors_des_phrases_seulement(annotations):
    bulles = _bulles(annotations, "elements")
    assert "Fe : fer (élément chimique)" in bulles and "Au : or (élément chimique)" in bulles
    assert "H : hydrogène (élément chimique)" in bulles and "He : hélium (élément chimique)" in bulles
    assert sum(b.startswith("Au :") for b in bulles) == 1  # « Au début » n'est pas de l'or


def test_la_prose_reste_tranquille(annotations):
    assert annotations["prose"] == {"formules": [], "bulles": []}


def test_abreviation_propre_a_la_notion(annotations):
    assert _bulles(annotations, "abreviation") == ["ua : unité astronomique"]


def test_le_mot_devant_la_parenthese_decide(annotations):
    bulles = _bulles(annotations, "parentheses")
    assert "W : watts (unité de puissance)" in bulles and "V : volts (unité de tension)" in bulles
    assert "N : azote (élément chimique)" in bulles
    assert not any(b.startswith("° ") for b in bulles)  # « n° 31 » n'est pas un degre


def test_equation_chimique_et_conversion_d_unites(annotations):
    assert annotations["equation"]["formules"] == ["C + O₂ → CO₂", "km/h → m/s"]
    assert "C : carbone (élément chimique)" in _bulles(annotations, "equation")


def test_une_unite_faite_des_lettres_de_la_formule_n_en_est_pas_une(annotations):
    bulles = _bulles(annotations, "mg")
    assert bulles.count("mg : milligrammes") == 1  # « 2 mg » oui, « P = mg » non


def test_les_lettres_de_la_notion_aussi_dans_les_phrases(annotations):
    bulles = _bulles(annotations, "phrase")
    assert "m : la masse" in bulles and "g : la pesanteur" in bulles
    assert "kg : kilogrammes" in bulles and "m/s : mètres par seconde" in bulles  # « m/s » l'emporte sur « m »


def test_apres_en_c_est_une_unite(annotations):
    assert _bulles(annotations, "unite_en") == ["m : mètres", "g : grammes"]
