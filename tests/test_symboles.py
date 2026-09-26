"""Bulles de rappel au survol : un coeur commun a toutes les pages (jules/web/static/symboles.*) et des
regles par matiere fournies par les extensions de la famille `rappels` (servies par /rappels.js)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from jules.chantier_visuel import _chromium
from jules.extensions import ErreurExtension, charger_extensions, code_des_rappels, lire_extension

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"
PAGES = sorted(STATIQUE.glob("*.html"))
ACTIVES = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))["extensions"]


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_chaque_page_charge_le_coeur_puis_les_extensions(page):
    html = page.read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/static/symboles.css">' in html
    # Coeur, puis regles des extensions, puis les scripts de la page : tout ce qu'ils affichent est observe.
    assert html.index("/static/symboles.js") < html.index('"/rappels.js"') < html.index("/static/commun.js")


def test_chaque_page_donne_le_contexte_de_sa_notion():
    for page, appel in [
        ("accueil.js", "Symboles.contexte("),
        ("eleve.js", "Symboles.notion("),
        ("studio.js", "Symboles.notion("),
        ("cours.js", "Symboles.notion("),
    ]:
        assert appel in (STATIQUE / page).read_text(encoding="utf-8"), page


def test_le_coeur_ne_connait_aucune_regle_de_matiere():
    coeur = (STATIQUE / "symboles.js").read_text(encoding="utf-8")
    assert "innerHTML" not in coeur.replace("Jamais d'innerHTML", "")
    assert "kilogrammes" not in coeur and "dioxyde" not in coeur and "siècle :" not in coeur
    symboles = dict(
        re.findall(r'^\s+"(.+?)": "(.+?)",$', coeur.split("const SYMBOLES = {")[1].split("};")[0], flags=re.M)
    )
    assert {"<", ">", "≤", "≥", "≠", "≈", "√", "π", "→"} <= set(symboles)
    assert not {"×", "÷", "+", "="} & set(symboles)  # les operations evidentes n'ont pas de bulle


def test_les_extensions_de_rappels_actives():
    extensions = charger_extensions(RACINE / "extensions", ACTIVES)
    code = code_des_rappels(extensions)
    for identifiant in ("rappels-sciences", "rappels-histoire", "rappels-francais"):
        assert f"// --- extension {identifiant} ---" in code
    elements = re.findall(r"\b([A-Z][a-z]?): \"", code.split("elements: {")[1].split("},")[0])
    assert len(elements) == len(set(elements)) == 118


def _extension(dossier: Path, code: str | None) -> Path:
    dossier = dossier / "rappels-essai"
    dossier.mkdir(parents=True)
    (dossier / "extension.yaml").write_text(
        "id: rappels-essai\ntitre: essai\nversion: '1'\nlicence: MIT\nfournit:\n  rappels: [essai]\n",
        encoding="utf-8",
    )
    if code is not None:
        (dossier / "rappels.js").write_text(code, encoding="utf-8")
    return dossier


def test_une_extension_de_rappels_est_controlee_comme_une_figure(tmp_path):
    with pytest.raises(ErreurExtension, match=r"rappels\.js est absent"):
        lire_extension(_extension(tmp_path / "a", None))
    with pytest.raises(ErreurExtension, match="motif interdit"):
        lire_extension(_extension(tmp_path / "b", 'fetch("/api/eleve/notes");'))
    valide = lire_extension(_extension(tmp_path / "c", 'Symboles.dictionnaire({id: "x", entrees: {}});'))
    assert valide.fournit["rappels"] == ["essai"]


# --- comportement, dans un vrai navigateur (saute si Chromium est absent) ---------------------------

PHYSIQUE = {
    "matiere": "physique-chimie",
    "variables": {"P": "le poids", "m": "la masse", "g": "la pesanteur"},
    "abreviations": {"ua": "unité astronomique"},
}
TEXTES = [
    ("formule", PHYSIQUE, "Pour un poids : écrire P = m × g, puis m = P ÷ g."),
    ("unites", PHYSIQUE, "Un sac de 10 kg pèse 98 N ; il tombe en 2 s, à 5 m/s."),
    ("chimie", PHYSIQUE, "La combustion rejette du CO₂ et de l'eau H₂O ; l'ion Cu²⁺ est bleu."),
    ("elements", PHYSIQUE, "Au début, les éléments légers : H, He. Le fer (Fe) et l'or (Au)."),
    ("prose", PHYSIQUE, "Si tu as une masse, il a raison : c'est la vitesse d'un objet."),
    ("abreviation", PHYSIQUE, "La Terre est à 1 ua du Soleil."),
    ("parentheses", PHYSIQUE, "La puissance en watts (W), la tension en volts (V) ; l'azote (N). Source : BO n° 31."),
    ("equation", PHYSIQUE, "Combustion : C + O₂ → CO₂, et on convertit km/h → m/s."),
    ("mg", PHYSIQUE, "Le poids : P = mg, soit 2 mg de poudre."),
    ("negatif", PHYSIQUE, "Variation : (190 − 250) ÷ 250 × 100 = −60 ÷ 250 × 100 = −24."),
    ("unite_en", PHYSIQUE, "La distance en m, la masse en g."),
    ("phrase", PHYSIQUE, "Vérifie que m est en kg et que la vitesse est en m/s : il y a une erreur, il a oublié g."),
    (
        "histoire",
        {"matiere": "histoire"},
        "Au XIXe siècle, Louis XIV est déjà loin ; la Ve République date de 1958. "
        "Rome au Ier siècle av. J.-C. ; l'URSS et l'ONU.",
    ),
    ("histoire_sans_chimie", {"matiere": "histoire"}, "Le CO₂ et 10 kg : pas de sciences ici."),
    (
        "francais",
        {"matiere": "francais"},
        "Dans « il mange une pomme », le GN « une pomme » est COD ; adj. qualificatif.",
    ),
    ("sans_matiere", {}, "Sans notion : 10 kg de CO₂ au XIXe siècle."),
    ("svt", {"matiere": "svt"}, "L'ADN du VIH ; 10 g de glucose C₆H₁₂O₆ ; il faut une IST au XIXe siècle."),
]


@pytest.fixture(scope="module")
def annotations(tmp_path_factory):
    navigateur = _chromium()
    if not navigateur:
        pytest.skip("Chromium absent")
    dossier = tmp_path_factory.mktemp("symboles")
    (dossier / "symboles.js").write_text((STATIQUE / "symboles.js").read_text(encoding="utf-8"), encoding="utf-8")
    (dossier / "rappels.js").write_text(
        code_des_rappels(charger_extensions(RACINE / "extensions", ACTIVES)), encoding="utf-8"
    )
    zones = "\n".join(f'<div id="{i}"><p>{t}</p></div>' for i, _, t in TEXTES)
    contextes = json.dumps({i: c for i, c, _ in TEXTES}, ensure_ascii=False)
    script = f"""
      const CONTEXTES = {contextes};
      setTimeout(() => {{
        for (const [id, c] of Object.entries(CONTEXTES)) Symboles.contexte(document.getElementById(id), c);
        const r = {{}};
        for (const id of Object.keys(CONTEXTES)) {{
          const z = document.getElementById(id);
          r[id] = {{
            formules: [...z.querySelectorAll(".formule-texte")].map((e) => e.textContent),
            bulles: [...z.querySelectorAll("abbr.symbole")].map((e) => e.dataset.nom),
          }};
        }}
        document.body.setAttribute("data-resultat", JSON.stringify(r));
      }}, 50);
    """
    page = dossier / "page.html"
    page.write_text(
        f'<!doctype html><meta charset="utf-8"><body>{zones}<script src="symboles.js"></script>'
        f'<script src="rappels.js"></script><script>{script}</script></body>',
        encoding="utf-8",
    )
    options = ["--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files"]
    options += ["--virtual-time-budget=2000", "--dump-dom"]
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


def test_histoire_siecles_regnes_ere_et_sigles(annotations):
    bulles = _bulles(annotations, "histoire")
    assert "XIXe : le 19e siècle : de 1801 à 1900" in bulles
    assert "XIV : 14 (chiffres romains)" in bulles and "Ve : 5e (chiffres romains)" in bulles
    assert "Ier : le 1er siècle avant J.-C. : de 100 à 1 av. J.-C. (on compte à rebours)" in bulles
    assert any(b.startswith("av. J.-C. : avant Jésus-Christ") for b in bulles)
    assert any(b.startswith("URSS : Union des républiques") for b in bulles)
    assert any(b.startswith("ONU : Organisation des Nations unies") for b in bulles)  # « l'ONU » compte


def test_chaque_matiere_ses_regles(annotations):
    assert _bulles(annotations, "histoire_sans_chimie") == []  # ni chimie ni unites en histoire
    francais = _bulles(annotations, "francais")
    assert any(b.startswith("GN : groupe nominal") for b in francais) and any(b.startswith("COD :") for b in francais)
    assert "adj. : adjectif" in francais


def test_sans_matiere_toutes_les_regles(annotations):
    bulles = _bulles(annotations, "sans_matiere")
    assert "kg : kilogrammes" in bulles and any(b.startswith("CO₂ :") for b in bulles)
    assert "XIXe : le 19e siècle : de 1801 à 1900" in bulles


def test_svt_sigles_et_chimie_sans_histoire(annotations):
    bulles = _bulles(annotations, "svt")
    assert any(b.startswith("ADN : acide désoxyribonucléique") for b in bulles)
    assert any(b.startswith("VIH :") for b in bulles) and any(b.startswith("IST :") for b in bulles)
    assert any(b.startswith("C₆H₁₂O₆ : glucose : 6 atomes de carbone") for b in bulles) and "g : grammes" in bulles
    assert not any(b.startswith("XIXe") for b in bulles)  # les siecles sont une regle d'histoire


def test_formule_avec_un_nombre_negatif(annotations):
    assert annotations["negatif"]["formules"] == ["(190 − 250) ÷ 250 × 100 = −60 ÷ 250 × 100 = −24"]
