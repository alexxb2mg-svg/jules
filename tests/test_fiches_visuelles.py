"""Tests du validateur de fiches visuelles (jules/fiches_visuelles.py)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from jules.bibliotheques import Notion, charger_catalogue, lire_identite
from jules.extensions import charger_extensions, figures_fournies
from jules.fiches_visuelles import (
    ErreurFicheVisuelle,
    analyser_condition,
    charger_fiches_visuelles,
    evaluer_condition,
    lire_fiche_visuelle,
    texte_sans_accents,
)

RACINE = Path(__file__).resolve().parents[1]
BIBLIOTHEQUES = RACINE / "bibliotheque"
BIBLIO_ID = "fiches-visuelles-3e-experimentales"
# Gabarits acceptes : ceux des extensions de figures activees dans config.yaml (docs/EXTENSIONS.md).
GABARITS = frozenset(
    figures_fournies(
        charger_extensions(
            RACINE / "extensions", yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))["extensions"]
        )
    )
)

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
    fiche = lire_fiche_visuelle(chemin, notions, biblio, GABARITS)
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
    """Les 5 fiches livrees existent, sont valides, et couvrent au moins les 7 types de base.

    La fiche Pythagore porte en plus un bloc `schema` (premier schema reel, voir docs/EXTENSIONS.md
    et jules_architecture_plugins.md) : elle a donc un type de plus que les quatre autres.
    """
    chemin = BIBLIOTHEQUES / BIBLIO_ID / "fiches" / "mathematiques" / f"{notion_id}.yaml"
    assert chemin.is_file(), f"fiche manquante : {chemin}"
    fiche = lire_fiche_visuelle(chemin, notions, biblio, GABARITS)
    assert fiche.notion == notion_id
    types = {b.type for b in fiche.blocs}
    types_attendus = {"formule", "carte", "graphe", "methode", "piege", "exemple", "renfort"}
    if notion_id == "parallelisme-triangles-pythagore":
        types_attendus = types_attendus | {"schema"}
    assert types == types_attendus
    for bloc in fiche.blocs:
        assert bloc.jules, f"{notion_id}, bloc {bloc.id} : commentaire 'jules' manquant"


def test_charger_fiches_visuelles_les_cinq(notions):
    fiches = charger_fiches_visuelles(BIBLIOTHEQUES, [BIBLIO_ID], notions, GABARITS)
    assert set(fiches) == set(NOTIONS_ATTENDUES)


# --- cas invalides refuses ----------------------------------------------------------


def test_notion_inconnue_du_referentiel_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["notion"] = "notion-qui-n-existe-pas"
    with pytest.raises(ErreurFicheVisuelle, match="inconnue"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_id_de_bloc_invalide_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["id"] = "ID Invalide !"
    with pytest.raises(ErreurFicheVisuelle, match="invalide"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_ids_de_blocs_en_double_refuses(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][1]["id"] = brut["blocs"][0]["id"]
    with pytest.raises(ErreurFicheVisuelle, match="double"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_id_reserve_attendus_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["id"] = "attendus"
    with pytest.raises(ErreurFicheVisuelle, match="reserve"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_type_de_bloc_inconnu_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["type"] = "video"
    with pytest.raises(ErreurFicheVisuelle, match="inconnu"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_gabarit_inconnu_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    graphe = next(b for b in brut["blocs"] if b["type"] == "graphe")
    graphe["gabarit"] = "gabarit-invente"
    with pytest.raises(ErreurFicheVisuelle, match="gabarit"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_condition_de_lecture_malveillante_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    graphe = next(b for b in brut["blocs"] if b["type"] == "graphe")
    graphe["lectures"] = [{"si": "__import__('os').system('x')", "texte": "..."}]
    with pytest.raises(ErreurFicheVisuelle):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_variable_de_lecture_hors_curseurs_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    graphe = next(b for b in brut["blocs"] if b["type"] == "graphe")
    graphe["lectures"] = [{"si": "c > 0", "texte": "..."}]  # 'c' n'est pas un curseur declare
    with pytest.raises(ErreurFicheVisuelle, match="inconnue"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_commentaire_jules_trop_long_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["jules"] = "Une phrase. " * 40
    with pytest.raises(ErreurFicheVisuelle, match="jules"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_commentaire_jules_trop_de_phrases_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"][0]["jules"] = "Un. Deux. Trois. Quatre."
    with pytest.raises(ErreurFicheVisuelle, match="1 a 3 phrases"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def _bloc(brut: dict, type_: str) -> dict:
    return next(b for b in brut["blocs"] if b["type"] == type_)


def test_notions_cles_acceptees_et_comptees_sans_marques(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    methode = _bloc(brut, "methode")
    methode["etapes"][0] = "Repérer le **coefficient directeur** a, puis l'**ordonnée à l'origine** b dans f(x)."
    # 260 caracteres lisibles : les marques ** ne comptent pas dans la limite.
    methode["etapes"][1] = "Le **" + "x" * 30 + "** " + "y" * 226
    _bloc(brut, "piege")["bonne_idee"] = "Une **fonction affine** s'écrit f(x) = ax + b."
    brut["blocs"][0]["jules"] = "Regarde d'abord le **signe** de a."
    fiche = lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)
    etapes = next(b for b in fiche.blocs if b.type == "methode").donnees["etapes"]
    assert etapes[0].count("**") == 4  # le texte garde ses marques : l'affichage les met en valeur
    assert len(texte_sans_accents(etapes[1])) == 260


@pytest.mark.parametrize(
    "texte, motif",
    [
        ("Une **notion non fermée.", "non fermee"),
        ("**un** **deux** **trois** **quatre** **cinq** et la suite du texte bien longue ici.", "notions cles"),
        ("Une ** notion** avec un espace.", "notion cle"),
        ("Une **" + "n" * 41 + "** trop longue, suivie d'assez de texte pour le reste de la phrase ici.", "notion cle"),
        ("**Presque tout est en gras ici** ou pas.", "60 %"),
    ],
)
def test_notions_cles_mal_marquees_refusees(tmp_path, notions, biblio, texte, motif):
    brut = copy.deepcopy(fiche_valide())
    _bloc(brut, "methode")["etapes"][0] = texte
    with pytest.raises(ErreurFicheVisuelle, match=motif):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_notion_cle_refusee_hors_texte_courant(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    _bloc(brut, "carte")["noeuds"][0]["titre"] = "**Fonction**"  # dessine en SVG : la marque resterait visible
    with pytest.raises(ErreurFicheVisuelle, match="pas de mise en valeur"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_variables_declarees_servies_telles_quelles(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["variables"] = {"a": "le coefficient directeur", "b": "l'ordonnée à l'origine", "V₁": "un volume"}
    fiche = lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)
    assert fiche.toutes_les_variables() == brut["variables"]
    assert fiche.publique([])["variables"] == brut["variables"]
    # Sans champ : aucune lettre rappelee (jamais un symbole chimique ou une unite par deduction).
    assert lire_fiche_visuelle(ecrire(tmp_path, fiche_valide()), notions, biblio, GABARITS).variables == {}


@pytest.mark.parametrize("variables", [{"2 H₂O": "eau"}, {"vitesse": "trop long comme nom"}, {"v": ""}, ["v"]])
def test_variables_mal_formees_refusees(tmp_path, notions, biblio, variables):
    brut = copy.deepcopy(fiche_valide())
    brut["variables"] = variables
    with pytest.raises(ErreurFicheVisuelle):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


@pytest.mark.parametrize(
    "champ, texte",
    [("titre", "La masse volumique : ρ = m / V"), ("etape", "Calculer a = (yB − yA) / (xB − xA).")],
)
def test_division_s_ecrit_avec_le_signe_de_l_eleve(tmp_path, notions, biblio, champ, texte):
    brut = copy.deepcopy(fiche_valide())
    if champ == "titre":
        brut["titre"] = texte
    else:
        _bloc(brut, "methode")["etapes"][0] = texte
    with pytest.raises(ErreurFicheVisuelle, match="÷"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)
    # Les unites gardent leur barre collee.
    _bloc(brut, "methode")["etapes"][0] = "Convertir 36 km/h en m/s : 36 ÷ 3,6 = 10 m/s."
    brut["titre"] = "Fonctions"
    lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_source_sans_licence_libre_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["sources"] = [{"titre": "x", "url": "https://exemple.fr", "licence": "tous-droits-reserves"}]
    with pytest.raises(ErreurFicheVisuelle, match="licence"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_aucune_source_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["sources"] = []
    with pytest.raises(ErreurFicheVisuelle, match="source"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_relecture_absente_refusee(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["relecture"] = {"statut": "publiee"}
    with pytest.raises(ErreurFicheVisuelle, match="relecture"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_trop_peu_de_blocs_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    brut["blocs"] = brut["blocs"][:1]
    with pytest.raises(ErreurFicheVisuelle, match="blocs"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_curseur_depart_hors_bornes_refuse(tmp_path, notions, biblio):
    brut = copy.deepcopy(fiche_valide())
    graphe = next(b for b in brut["blocs"] if b["type"] == "graphe")
    graphe["curseurs"][0]["depart"] = 999
    with pytest.raises(ErreurFicheVisuelle, match="depart"):
        lire_fiche_visuelle(ecrire(tmp_path, brut), notions, biblio, GABARITS)


def test_bibliotheque_absente_est_ignoree_sans_lever(notions):
    """Une bibliotheque de fiches visuelles introuvable : Jules demarre sans elle, sans lever."""
    fiches = charger_fiches_visuelles(BIBLIOTHEQUES, ["bibliotheque-qui-n-existe-pas"], notions, GABARITS)
    assert fiches == {}
