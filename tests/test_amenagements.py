"""Amenagements (docs/spec/ADAPTATIONS-LOT2.md, §3) : EX-103.

- chaque amenagement est un fichier sous adaptations/amenagements/ avec son identifiant, ses libelles par
  niveau (complets, avec la page) et les valeurs de leviers ;
- chaque libelle est compare caractere pour caractere a docs/spec/pap-libelles.txt (propriete SPEC,
  verifie contre le PDF officiel) ; seules les apostrophes et les suites d'espaces sont normalisees ;
- aucun terme de termes-interdits.txt : le test d'hygiene d'EX-008 (tests/test_adaptations.py) couvre
  adaptations/ ; on verifie ici que les fichiers d'amenagement sont bien dans son perimetre.

`temps-majore` est reporte au lot 3 (spec au tag spec-lot2-fige-2) : 7 amenagements. Ses lignes restent
dans pap-libelles.txt mais ne sont pas testees au lot 2.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from jules.amenagements import (
    DOSSIER_AMENAGEMENTS,
    MENTION_AUTRES,
    NIVEAUX,
    PAGES_RUBRIQUE_AUTRES,
    AmenagementInvalide,
    charger_amenagement,
    charger_amenagements,
)
from jules.leviers import charger_leviers
from tests.termes_interdits import termes_interdits, trouver_terme
from tests.test_adaptations import fichiers_ex008

RACINE = Path(__file__).resolve().parents[1]
PAP_LIBELLES = RACINE / "docs" / "spec" / "pap-libelles.txt"
EXCLUS_DU_LOT = {"temps-majore"}
APOSTROPHES = str.maketrans(dict.fromkeys("\u2019\u2018\u02bc", "'"))

# §3 de la spec : id -> leviers regles (colonne « Leviers réglés »).
LEVIERS_ATTENDUS: dict[str, set[str]] = {
    "supports-aeres-agrandis": {
        "espacement-lettres",
        "espacement-mots",
        "interligne",
        "taille-texte",
        "longueur-ligne",
    },
    "limiter-quantite-ecrit": {"densite"},
    "surligner-mots-cles": {"surlignage-mots-cles"},
    "lecture-oralisee": {"lecture-vocale"},
    "reformulation": {"phrases-courtes"},
    "consignes-decomposees": {"consignes-decoupees", "phrases-courtes"},
    "reperes-couleur-calcul": {"reperes-rang-chiffres"},
}
# Valeurs imposees en toutes lettres par le §3.
VALEURS_IMPOSEES = {
    ("limiter-quantite-ecrit", "densite"): "un-exercice",
    ("lecture-oralisee", "lecture-vocale"): "proposee",
}


def normaliser(texte: str) -> str:
    """Seule normalisation permise par EX-103 : apostrophes typographiques et suites d'espaces."""
    return re.sub(r"\s+", " ", texte.translate(APOSTROPHES)).strip()


def reference_pap() -> dict[str, dict[str, tuple[int, str]]]:
    """pap-libelles.txt : id -> niveau -> (page, libelle normalise)."""
    reference: dict[str, dict[str, tuple[int, str]]] = {}
    for brute in PAP_LIBELLES.read_text(encoding="utf-8").splitlines():
        if not brute.strip() or brute.lstrip().startswith("#"):
            continue
        ident, niveau, page, texte = (champ.strip() for champ in brute.split("|", 3))
        assert niveau not in reference.get(ident, {}), f"doublon dans pap-libelles.txt : {ident} {niveau}"
        reference.setdefault(ident, {})[niveau] = (int(page), normaliser(texte))
    return reference


@pytest.fixture(scope="module")
def amenagements():
    return charger_amenagements()


# --- chargement --------------------------------------------------------------------------------
def test_les_amenagements_du_lot_2_sont_tous_declares(amenagements):
    assert set(amenagements) == set(LEVIERS_ATTENDUS), "adaptations/amenagements/ = les 7 amenagements du §3"
    assert len(amenagements) == 7
    assert not EXCLUS_DU_LOT & set(amenagements), "temps-majore est reporte au lot 3"
    assert set(reference_pap()) - EXCLUS_DU_LOT == set(amenagements), "un amenagement par identifiant du PAP"


def test_un_fichier_par_amenagement_et_nom_egal_a_l_id():
    fichiers = sorted(DOSSIER_AMENAGEMENTS.glob("*.yaml"))
    assert len(fichiers) == len(LEVIERS_ATTENDUS)
    assert not list(DOSSIER_AMENAGEMENTS.glob("*.yml")), "une seule extension : .yaml"
    leviers = charger_leviers()
    for chemin in fichiers:
        assert charger_amenagement(chemin, leviers).id == chemin.stem


@pytest.mark.parametrize("ident", sorted(LEVIERS_ATTENDUS))
def test_leviers_regles_conformes_au_para_3(amenagements, ident):
    leviers = charger_leviers()
    amenagement = amenagements[ident]
    assert set(amenagement.leviers) == LEVIERS_ATTENDUS[ident]
    for nom, valeur in amenagement.leviers.items():
        assert leviers[nom].dans_la_plage(valeur) and valeur != leviers[nom].neutre, (nom, valeur)
        if (ident, nom) in VALEURS_IMPOSEES:
            assert valeur == VALEURS_IMPOSEES[ident, nom]


def test_aucun_amenagement_ne_regle_une_preference_du_parent(amenagements):
    # §3 : police, fond et lecture-vocale = automatique sont des preferences hors PAP ; §4 : jamais
    # d'automatique par un amenagement.
    for amenagement in amenagements.values():
        assert not {"police", "fond"} & set(amenagement.leviers), amenagement.id
        assert amenagement.leviers.get("lecture-vocale") != "automatique", amenagement.id


# --- libelles PAP ------------------------------------------------------------------------------
def test_normalisation_limitee_aux_apostrophes_et_aux_espaces():
    assert normaliser("l\u2019élève  a\tlu ") == "l'élève a lu"
    # les espaces irregulieres du PDF comptent : « (A 3) » n'est pas « (A3) »
    assert normaliser("(A 3)") != normaliser("(A3)")
    assert normaliser("mots clés /passages") != normaliser("mots clés / passages")
    assert normaliser("Élève") != normaliser("eleve"), "accents et casse ne sont pas normalises"


@pytest.mark.parametrize("ident", sorted(LEVIERS_ATTENDUS))
def test_libelles_identiques_a_pap_libelles(amenagements, ident):
    attendus = reference_pap()[ident]
    obtenus = {n: (lib.page, normaliser(lib.texte)) for n, lib in amenagements[ident].libelles.items()}
    assert obtenus == attendus  # memes niveaux, memes pages, memes libelles caractere pour caractere


def test_libelles_complets_jamais_tronques(amenagements):
    for amenagement in amenagements.values():
        for libelle in amenagement.libelles.values():
            assert not libelle.texte.rstrip().endswith(("…", "[...]")), (amenagement.id, libelle.niveau)
            assert libelle.texte == libelle.texte.strip()


# --- niveau sans libelle -----------------------------------------------------------------------
def test_niveau_sans_libelle_sous_la_rubrique_autres(amenagements):
    for amenagement in amenagements.values():
        for niveau in NIVEAUX:
            affichage = amenagement.affichage(niveau)
            libelle = amenagement.libelles.get(niveau)
            if libelle:
                assert affichage is not None and not affichage.rubrique_autres
                assert (affichage.texte, affichage.page) == (libelle.texte, libelle.page)
            elif niveau == "maternelle":
                assert affichage is None, "pas de rubrique « Autres » en maternelle : non affiche"
            else:
                assert affichage is not None and affichage.rubrique_autres and affichage.texte is None
                assert affichage.page == PAGES_RUBRIQUE_AUTRES[niveau]
                assert affichage.mention == MENTION_AUTRES


def test_cas_du_para_3(amenagements):
    # college sans item (§3) : rubrique « Autres » ; consignes-decomposees n'a qu'un libelle maternelle
    for ident in ("lecture-oralisee", "reformulation", "consignes-decomposees", "reperes-couleur-calcul"):
        assert amenagements[ident].affichage("college").rubrique_autres, ident  # type: ignore[union-attr]
    assert amenagements["consignes-decomposees"].affichage("elementaire").rubrique_autres  # type: ignore[union-attr]
    assert amenagements["consignes-decomposees"].affichage("maternelle").page == 2  # type: ignore[union-attr]
    assert amenagements["supports-aeres-agrandis"].affichage("maternelle") is None
    assert amenagements["surligner-mots-cles"].affichage("lycee").page == 11  # type: ignore[union-attr]
    with pytest.raises(ValueError, match="niveau"):
        amenagements["reformulation"].affichage("cp")


# --- EX-008 : hygiene --------------------------------------------------------------------------
def test_ex008_couvre_les_amenagements():
    perimetre = {p.relative_to(RACINE).as_posix() for p in fichiers_ex008()}
    fichiers = {p.relative_to(RACINE).as_posix() for p in DOSSIER_AMENAGEMENTS.glob("*.yaml")}
    assert fichiers and fichiers <= perimetre


def test_ex008_aucun_nom_de_trouble_dans_les_amenagements():
    termes = termes_interdits()
    fautifs = [
        f"{p.name}: {terme}"
        for p in DOSSIER_AMENAGEMENTS.glob("*")
        if p.is_file() and (terme := trouver_terme(p.read_text(encoding="utf-8"), termes))
    ]
    assert not fautifs


# --- validation du chargeur --------------------------------------------------------------------
BASE = """id: essai
libelles:
  college: {page: 7, texte: "Un libelle"}
leviers:
  densite: un-exercice
"""


@pytest.mark.parametrize(
    ("remplacement", "message"),
    [
        (("id: essai", "id: autre"), "nom du fichier"),
        (("college:", "cp:"), "niveau"),
        (("page: 7", "page: 0"), "page"),
        (('texte: "Un libelle"', 'texte: " "'), "vide"),
        (("densite: un-exercice", "inconnu-x: 1"), "inconnu"),
        (("densite: un-exercice", "densite: rien"), "hors de la plage"),
        (("densite: un-exercice", "densite: tout"), "neutre"),
        (("densite: un-exercice", "police: defaut"), "preference du parent"),
        (("densite: un-exercice", "fond: creme"), "preference du parent"),
        (("densite: un-exercice", "lecture-vocale: automatique"), "reservee"),
        (("densite: un-exercice", "taille-texte: 3"), "hors de la plage"),
        (("leviers:", "extra: 1\nleviers:"), "champs inconnus"),
    ],
)
def test_le_chargeur_refuse_une_declaration_incoherente(tmp_path, remplacement, message):
    chemin = tmp_path / "essai.yaml"
    chemin.write_text(BASE.replace(*remplacement), encoding="utf-8")
    with pytest.raises(AmenagementInvalide, match=message):
        charger_amenagement(chemin, charger_leviers())


@pytest.mark.parametrize("champ", ["id", "libelles", "leviers"])
def test_le_chargeur_refuse_un_champ_manquant(tmp_path, champ):
    lignes = BASE.split("\n")
    debut = next(i for i, ligne in enumerate(lignes) if ligne.startswith(f"{champ}:"))
    fin = next((i for i in range(debut + 1, len(lignes)) if lignes[i] and not lignes[i].startswith(" ")), len(lignes))
    chemin = tmp_path / "essai.yaml"
    chemin.write_text("\n".join(lignes[:debut] + lignes[fin:]), encoding="utf-8")
    with pytest.raises(AmenagementInvalide, match="manquants"):
        charger_amenagement(chemin, charger_leviers())


def test_la_declaration_de_base_est_valide(tmp_path):
    chemin = tmp_path / "essai.yaml"
    chemin.write_text(BASE, encoding="utf-8")
    assert charger_amenagement(chemin, charger_leviers()).leviers == {"densite": "un-exercice"}
