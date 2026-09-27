"""Leviers d'adaptation (docs/spec/ADAPTATIONS-LOT2.md, §2) : EX-101 et EX-107.

- EX-101 : chaque levier est declare une seule fois sous adaptations/leviers/, avec les champs du §2 ;
  la valeur neutre est dans la plage et la regle de combinaison est connue.
- EX-107 : la liste fermee du levier `police` ne contient aucune police presentee comme « speciale ».

La table attendue ci-dessous recopie le §2 de la spec (canal, neutre, combinaison) : si la spec change,
ce test doit changer avec elle. `temps-majore` est reporte au lot 3 (spec au tag spec-lot2-fige-2) : 13 leviers.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest

from jules.leviers import (
    CHAMPS,
    COMBINAISONS,
    DOSSIER_LEVIERS,
    Levier,
    LevierInvalide,
    charger_levier,
    charger_leviers,
)
from tests.test_hygiene import fichiers_publies

RACINE = Path(__file__).resolve().parents[1]

# §2 de la spec : id -> (canaux, neutre, combinaison). Neutre None = « valeur actuelle / aucune limite ».
ATTENDUS: dict[str, tuple[set[str], object, str]] = {
    "espacement-lettres": ({"css"}, 0, "max"),
    "espacement-mots": ({"css"}, 0, "max"),
    "interligne": ({"css"}, None, "max"),
    "longueur-ligne": ({"css"}, None, "min"),
    "taille-texte": ({"css"}, 1.125, "max"),
    "police": ({"css"}, "defaut", "arbitrage-parent"),
    "fond": ({"css"}, "blanc", "arbitrage-parent"),
    "densite": ({"js"}, "tout", "plus-restrictif"),
    "lecture-vocale": ({"js"}, "absente", "max"),
    "consignes-decoupees": ({"consigne", "js"}, False, "ou"),
    "phrases-courtes": ({"consigne"}, False, "ou"),
    "reperes-rang-chiffres": ({"css", "outils"}, False, "ou"),
    "surlignage-mots-cles": ({"consigne", "css"}, False, "ou"),
}
EXCLUS_DU_LOT = {"temps-majore"}

# EX-107 : polices presentees comme concues pour une difficulte de lecture. Comparaison sans casse,
# sans accents, sans espaces ni tirets (« Open-Dyslexic », « lexie readable »...).
POLICES_EXCLUES = (
    "OpenDyslexic",
    "Open Dyslexic",
    "Dyslexie",
    "Dyslexic",
    "Lexie Readable",
    "Read Regular",
    "Sylexiad",
    "EasyReading",
    "Easy Reading",
    "Dyslexia Font",
)


def compacter(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte.casefold())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in decompose if not unicodedata.combining(c)))


@pytest.fixture(scope="module")
def leviers() -> dict[str, Levier]:
    return charger_leviers()


# --- EX-101 ------------------------------------------------------------------------------------
def test_les_leviers_du_lot_2_sont_tous_declares(leviers):
    assert set(leviers) == set(ATTENDUS), "adaptations/leviers/ doit contenir exactement les leviers du §2"
    assert len(leviers) == 13, "EX-101 : 13 fichiers de leviers"
    assert not EXCLUS_DU_LOT & set(leviers), "temps-majore est reporte au lot 3"


def test_un_fichier_par_levier_et_nom_egal_a_l_id():
    fichiers = sorted(DOSSIER_LEVIERS.glob("*.yaml"))
    assert len(fichiers) == len(ATTENDUS)
    assert not list(DOSSIER_LEVIERS.glob("*.yml")), "une seule extension : .yaml"
    for chemin in fichiers:
        assert charger_levier(chemin).id == chemin.stem


def test_chaque_levier_n_est_declare_qu_une_fois():
    # aucun autre fichier de donnees du depot ne redeclare un levier (id: <levier> au premier niveau)
    doublons = []
    for chemin in fichiers_publies():
        if chemin.suffix not in {".yaml", ".yml"} or chemin.parent == DOSSIER_LEVIERS:
            continue
        texte = chemin.read_text(encoding="utf-8", errors="replace")
        rel = chemin.relative_to(RACINE)
        doublons += [f"{rel}:{i}" for i in ATTENDUS if re.search(rf"(?m)^id:\s*{re.escape(i)}\s*$", texte)]
    assert not doublons


@pytest.mark.parametrize("ident", sorted(ATTENDUS))
def test_champs_neutre_et_combinaison_conformes_au_para_2(leviers, ident):
    levier = leviers[ident]
    canaux, neutre, combinaison = ATTENDUS[ident]
    assert set(levier.canal) == canaux
    assert levier.neutre == neutre and type(levier.neutre) is type(neutre)
    assert levier.combinaison == combinaison and levier.combinaison in COMBINAISONS
    assert levier.dans_la_plage(levier.neutre), "valeur neutre hors de la plage"
    assert levier.source["nature"] and levier.source["reference"]
    if "css" in levier.canal:
        assert str(levier.details.get("variable_css", "")).startswith("--adapt-"), "variable CSS dediee"


def test_plages_numeriques_du_para_2(leviers):
    plages = {i: (leviers[i].minimum, leviers[i].maximum, leviers[i].unite) for i in leviers if leviers[i].unite}
    assert plages["espacement-lettres"] == (0, 0.18, "em")
    assert plages["espacement-mots"] == (0, 0.5, "em")
    assert plages["interligne"] == (1.55, 2.0, "multiplicateur")  # jamais sous la valeur actuelle
    assert plages["longueur-ligne"] == (None, 80, "ch")  # aucune borne basse sourcee
    assert plages["taille-texte"] == (1.125, 1.125 * 1.5, "rem")  # 1 a 1,5 x la neutre


def test_longueur_ligne_refuse_une_valeur_nulle_ou_negative(leviers):
    # Revue tour 1 : sans borne basse, 0 et -10 etaient acceptes (max-width invalide, ignore en silence).
    levier = leviers["longueur-ligne"]
    assert [v for v in (-10, -0.5, 0, 0.0) if levier.dans_la_plage(v)] == []
    assert all(levier.dans_la_plage(v) for v in (1, 45, 80, None))
    assert not levier.dans_la_plage(81)


def test_plages_des_choix_du_para_2(leviers):
    assert leviers["densite"].valeurs == ("tout", "un-exercice")
    assert leviers["lecture-vocale"].valeurs == ("absente", "proposee", "automatique")
    assert leviers["fond"].valeurs == ("blanc", "creme", "bleu-pale")
    for ident, (_, neutre, _) in ATTENDUS.items():
        if isinstance(neutre, bool):
            assert leviers[ident].valeurs == (False, True)


def luminance(couleur: str) -> float:
    canaux = [int(couleur[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lineaires = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canaux]
    return 0.2126 * lineaires[0] + 0.7152 * lineaires[1] + 0.0722 * lineaires[2]


def contraste(a: str, b: str) -> float:
    clair, fonce = sorted((luminance(a), luminance(b)), reverse=True)
    return (clair + 0.05) / (fonce + 0.05)


def test_chaque_fond_garde_un_contraste_de_4_5(leviers):
    fond = leviers["fond"]
    couleurs = fond.details["couleurs"]
    assert set(couleurs) == set(fond.valeurs)
    assert couleurs["blanc"].upper() == "#FFFFFF", "neutre = fond actuel"
    css = (RACINE / "jules" / "web" / "static" / "style.css").read_text(encoding="utf-8")
    textes = [re.search(rf"--{nom}:\s*(#[0-9A-Fa-f]{{6}})", css).group(1) for nom in ("texte", "gris", "p-principale")]  # type: ignore[union-attr]
    for nom, couleur in couleurs.items():
        for texte in textes:
            assert contraste(couleur, texte) >= fond.details["contraste_minimum"] >= 4.5, (nom, texte)


# --- validation du chargeur --------------------------------------------------------------------
BASE = """id: essai
canal: css
type: nombre
unite: em
neutre: 0
plage: {min: 0, max: 1}
combinaison: max
source: {nature: usage, reference: essai}
"""


@pytest.mark.parametrize(
    ("remplacement", "message"),
    [
        (("combinaison: max", "combinaison: moyenne"), "combinaison"),
        (("neutre: 0", "neutre: 2"), "hors de la plage"),
        (("canal: css", "canal: magie"), "canal"),
        (("source: {nature: usage, reference: essai}", "source: {nature: rumeur, reference: x}"), "source"),
        (("unite: em\n", ""), "unite"),
        (("plage: {min: 0, max: 1}", "plage: {min: 2, max: 1}"), "inversee"),
        (("id: essai", "id: autre"), "nom du fichier"),
    ],
)
def test_le_chargeur_refuse_une_declaration_incoherente(tmp_path, remplacement, message):
    chemin = tmp_path / "essai.yaml"
    chemin.write_text(BASE.replace(*remplacement), encoding="utf-8")
    with pytest.raises(LevierInvalide, match=message):
        charger_levier(chemin)


@pytest.mark.parametrize("champ", CHAMPS)
def test_le_chargeur_refuse_un_champ_manquant(tmp_path, champ):
    lignes = [ligne for ligne in BASE.splitlines() if not ligne.startswith(f"{champ}:")]
    chemin = tmp_path / "essai.yaml"
    chemin.write_text("\n".join(lignes), encoding="utf-8")
    with pytest.raises(LevierInvalide, match="manquants"):
        charger_levier(chemin)


def test_le_chargeur_refuse_un_choix_hors_liste(tmp_path):
    chemin = tmp_path / "essai.yaml"
    texte = BASE.replace(
        "type: nombre\nunite: em\nneutre: 0\nplage: {min: 0, max: 1}", "type: choix\nneutre: c\nplage: [a, b]"
    )
    chemin.write_text(texte, encoding="utf-8")
    with pytest.raises(LevierInvalide, match="hors de la plage"):
        charger_levier(chemin)


# --- EX-107 ------------------------------------------------------------------------------------
def test_cas_temoin_de_la_liste_d_exclusion():
    exclues = {compacter(p) for p in POLICES_EXCLUES}
    for ecrite in ("OpenDyslexic", "open-dyslexic", "Lexie  Readable", "DYSLEXIE"):
        assert any(e in compacter(ecrite) for e in exclues), ecrite


def test_aucune_police_speciale_dans_la_liste_fermee(leviers):
    police = leviers["police"]
    assert police.type == "choix" and len(police.valeurs) >= 2, "liste fermee"
    familles = police.details["familles"]
    assert set(familles) == set(police.valeurs), "chaque valeur a sa pile de polices, et rien d'autre"
    assert familles["defaut"] == "var(--police-texte)", "neutre = police actuelle"
    exclues = [compacter(p) for p in POLICES_EXCLUES]
    textes = [*map(str, police.valeurs), *map(str, familles.values())]
    trouvees = [t for t in textes for e in exclues if e in compacter(t)]
    assert not trouvees, f"police exclue proposee : {trouvees}"


def test_aucune_police_speciale_dans_les_css_ni_les_polices_livrees():
    statique = RACINE / "jules" / "web" / "static"
    exclues = [compacter(p) for p in POLICES_EXCLUES]
    fichiers = [*statique.glob("*.css"), *statique.glob("polices/*")]
    trouvees = [f.name for f in fichiers for e in exclues if e in compacter(f.name)]
    for css in statique.glob("*.css"):
        texte = compacter(css.read_text(encoding="utf-8"))
        trouvees += [f"{css.name}:{e}" for e in exclues if e in texte]
    assert not trouvees
