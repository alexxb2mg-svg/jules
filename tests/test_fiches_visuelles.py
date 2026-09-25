"""Tests du validateur de fiches visuelles (jules/fiches_visuelles.py)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from jules.bibliotheques import Notion, charger_catalogue, lire_identite
from jules.fiches_visuelles import (
    ErreurFicheVisuelle,
    analyser_condition,
    charger_fiches_visuelles,
    evaluer_condition,
    lire_fiche_visuelle,
)

RACINE = Path(__file__).resolve().parents[1]
BIBLIOTHEQUES = RACINE / "bibliotheque"
BIBLIO_ID = "fiches-visuelles-3e-experimentales"

NOTIONS_ATTENDUES = [
    "fonctions-lineaires-affines",
    "thales-triangles-semblables-trigonometrie",
    "parallelisme-triangles-pythagore",
    "equations-premier-degre-et-produits",
    "probabilites-experiences-simples",
]


@pytest.fixture(scope="module")
def notions() -> dict[str, Notion]:
    return charger_catalogue(BIBLIOTHEQUES, ["programme"], None).notions


@pytest.fixture(scope="module")
def biblio():
    return lire_identite(BIBLIOTHEQUES / BIBLIO_ID)


def fiche_valide() -> dict:
    chemin = BIBLIOTHEQUES / BIBLIO_ID / "fiches" / "mathematiques" / "fonctions-lineaires-affines.yaml"
    return yaml.safe_load(chemin.read_text(encoding="utf-8"))


def ecrire(tmp_path: Path, brut: dict) -> Path:
    chemin = tmp_path / "fiche.yaml"
    chemin.write_text(yaml.safe_dump(brut, allow_unicode=True), encoding="utf-8")
    return chemin


# --- analyseur de conditions : jamais d'eval() -----------------------------------------


def test_analyser_condition_simple():
    assert analyser_condition("a > 0") == [("a", ">", 0.0)]
    assert analyser_condition("b == 0") == [("b", "==", 0.0)]


def test_analyser_condition_avec_et():
    assert analyser_condition("a > 0 && b < 5") == [("a", ">", 0.0), ("b", "<", 5.0)]


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "a > 0 or b < 1",
        "eval('1')",
        "a + b > 0",
        "a > b",  # comparaison a une autre variable, pas a un nombre litteral
        "",
        "a >",
        "a ? 1 : 0",
    ],
)
def test_conditions_malveillantes_ou_illisibles_refusees(expression):
    with pytest.raises(ErreurFicheVisuelle):
        analyser_condition(expression)


def test_evaluer_condition():
    assert evaluer_condition("a > 0 && b == 1", {"a": 2, "b": 1}) is True
    assert evaluer_condition("a > 0", {"a": -1}) is False
    assert evaluer_condition("a > 0", {}) is False  # variable absente : jamais vraie


# --- lecture d'une fiche valide -----------------------------------------------------


def test_fiche_valide_se_lit(notions, biblio):
    chemin = BIBLIOTHEQUES / BIBLIO_ID / "fiches" / "mathematiques" / "fonctions-lineaires-affines.yaml"
    fiche = lire_fiche_visuelle(chemin, notions, biblio)
    assert fiche.notion == "fonctions-lineaires-affines"
    assert fiche.relecture == "a_relire"
    assert {b.type for b in fiche.blocs} == {
        "formule",
        "carte",
        "graphe",
        "methode",
        "piege",
        "exemple",
        "renfort",
    }
    ids = [b.id for b in fiche.blocs]
    assert len(ids) == len(set(ids))
    publique = fiche.publique(["Un attendu officiel."])
    assert publique["blocs"][0]["type"] == "attendus"
    assert publique["blocs"][0]["attendus"] == ["Un attendu officiel."]
    # chaque bloc a une adresse fiche/<id>
    for bloc in publique["blocs"]:
        assert bloc["adresse"].startswith("fiche/")


@pytest.mark.parametrize("notion_id", NOTIONS_ATTENDUES)
def test_les_cinq_fiches_publiees_sont_valides(notions, biblio, notion_id):
    """Les 5 fiches livrees existent, sont valides, et couvrent les 8 types de blocs."""
    chemin = BIBLIOTHEQUES / BIBLIO_ID / "fiches" / "mathematiques" / f"{notion_id}.yaml"
    assert chemin.is_file(), f"fiche manquante : {chemin}"
    fiche = lire_fiche_visuelle(chemin, notions, biblio)
    assert fiche.notion == notion_id
    types = {b.type for b in fiche.blocs}
    assert types == {"formule", "carte", "graphe", "methode", "piege", "exemple", "renfort"}
    for bloc in fiche.blocs:
        assert bloc.jules, f"{notion_id}, bloc {bloc.id} : commentaire 'jules' manquant"


def test_charger_fiches_visuelles_les_cinq(notions):
    fiches = charger_fiches_visuelles(BIBLIOTHEQUES, [BIBLIO_ID], notions)
    assert set(fiches) == set(NOTIONS_ATTENDUES)


# --- cas invalides refuses ----------------------------------------------------------


def test_notion_inconnue_du_referentiel_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["notion"] = "notion-qui-n-existe-pas"
    with pytest.raises(ErreurFicheVisuelle, match="inconnue"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_id_de_bloc_invalide_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["id"] = "ID Invalide !"
    with pytest.raises(ErreurFicheVisuelle, match="invalide"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_ids_de_blocs_en_double_refuses(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][1]["id"] = brut["blocs"][0]["id"]
    with pytest.raises(ErreurFicheVisuelle, match="double"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_id_reserve_attendus_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["id"] = "attendus"
    with pytest.raises(ErreurFicheVisuelle, match="reserve"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_type_de_bloc_inconnu_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["type"] = "video"
    with pytest.raises(ErreurFicheVisuelle, match="inconnu"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_gabarit_inconnu_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    graphe = next(b for b in brut["blocs"] if b["type"] == "graphe")
    graphe["gabarit"] = "gabarit-invente"
    with pytest.raises(ErreurFicheVisuelle, match="gabarit"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_condition_de_lecture_malveillante_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    graphe = next(b for b in brut["blocs"] if b["type"] == "graphe")
    graphe["lectures"] = [{"si": "__import__('os').system('x')", "texte": "..."}]
    with pytest.raises(ErreurFicheVisuelle):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_variable_de_lecture_hors_curseurs_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    graphe = next(b for b in brut["blocs"] if b["type"] == "graphe")
    graphe["lectures"] = [{"si": "c > 0", "texte": "..."}]  # 'c' n'est pas un curseur declare
    with pytest.raises(ErreurFicheVisuelle, match="inconnue"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_commentaire_jules_trop_long_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["jules"] = "Une phrase. " * 40
    with pytest.raises(ErreurFicheVisuelle, match="jules"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_commentaire_jules_trop_de_phrases_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["jules"] = "Un. Deux. Trois. Quatre."
    with pytest.raises(ErreurFicheVisuelle, match="1 a 3 phrases"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_source_sans_licence_libre_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["sources"] = [{"titre": "x", "url": "https://exemple.fr", "licence": "tous-droits-reserves"}]
    with pytest.raises(ErreurFicheVisuelle, match="licence"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_aucune_source_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["sources"] = []
    with pytest.raises(ErreurFicheVisuelle, match="source"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_relecture_absente_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["relecture"] = {"statut": "publiee"}
    with pytest.raises(ErreurFicheVisuelle, match="relecture"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_trop_peu_de_blocs_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"] = brut["blocs"][:1]
    with pytest.raises(ErreurFicheVisuelle, match="blocs"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_curseur_depart_hors_bornes_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    graphe = next(b for b in brut["blocs"] if b["type"] == "graphe")
    graphe["curseurs"][0]["depart"] = 999
    with pytest.raises(ErreurFicheVisuelle, match="depart"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio)


def test_bibliotheque_absente_est_ignoree_sans_lever(notions):
    """Une bibliotheque de fiches visuelles introuvable : Jules demarre sans elle, sans lever."""
    fiches = charger_fiches_visuelles(BIBLIOTHEQUES, ["bibliotheque-qui-n-existe-pas"], notions)
    assert fiches == {}
