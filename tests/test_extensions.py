"""Tests du chargeur d'extensions (jules/extensions.py, voir docs/EXTENSIONS.md)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from jules.extensions import (
    CLES_FOURNIT,
    CLES_PERMISSIONS,
    ErreurExtension,
    charger_extensions,
    decouvrir_extensions,
    figures_fournies,
    figures_pour_discussion,
    lire_extension,
)

MANIFESTE_VALIDE = """\
id: {id}
titre: "Une extension"
version: "1.0.0"
licence: MIT
auteurs: ["quelqu'un"]
fournit:
  figures: [ma-figure]
permissions:
  reseau: false
"""


def creer_extension(racine: Path, identifiant: str, manifeste: str | None = None) -> Path:
    dossier = racine / identifiant
    dossier.mkdir(parents=True)
    (dossier / "extension.yaml").write_text(
        manifeste if manifeste is not None else MANIFESTE_VALIDE.format(id=identifiant), encoding="utf-8"
    )
    # le manifeste valide fournit une figure : son code est attendu dans gabarit.js
    (dossier / "gabarit.js").write_text('window.GABARITS["ma-figure"] = {};\n', encoding="utf-8")
    return dossier


# --- manifeste valide ---------------------------------------------------------------


def test_extension_valide_est_chargee(tmp_path):
    dossier = creer_extension(tmp_path, "mon-extension")
    extension = lire_extension(dossier)
    assert extension.id == "mon-extension"
    assert extension.titre == "Une extension"
    assert extension.version == "1.0.0"
    assert extension.licence == "MIT"
    assert extension.fournit_liste("figures") == ["ma-figure"]
    assert extension.fournit_liste("modules") == []
    assert extension.a_permission("reseau") is False
    assert extension.a_permission("appel_ia") is False  # absente du manifeste : vaut False


def test_extension_sans_fournit_ni_permissions_est_valide(tmp_path):
    manifeste = 'id: minimal\ntitre: "Minimal"\nversion: "1.0.0"\nlicence: MIT\n'
    dossier = creer_extension(tmp_path, "minimal", manifeste=manifeste)
    extension = lire_extension(dossier)
    assert extension.fournit == {}
    assert extension.permissions == {}


# --- manifeste invalide ---------------------------------------------------------------


def test_manifeste_manquant_refuse(tmp_path):
    dossier = tmp_path / "vide"
    dossier.mkdir()
    with pytest.raises(ErreurExtension, match="manquant"):
        lire_extension(dossier)


def test_id_doit_correspondre_au_dossier(tmp_path):
    dossier = creer_extension(tmp_path, "mon-extension", manifeste=MANIFESTE_VALIDE.format(id="autre-id"))
    with pytest.raises(ErreurExtension, match="doit etre le nom du dossier"):
        lire_extension(dossier)


def test_id_invalide_refuse(tmp_path):
    manifeste = MANIFESTE_VALIDE.format(id="Mon_Extension")
    dossier = tmp_path / "Mon_Extension"
    dossier.mkdir()
    (dossier / "extension.yaml").write_text(manifeste, encoding="utf-8")
    with pytest.raises(ErreurExtension, match="invalide"):
        lire_extension(dossier)


@pytest.mark.parametrize("champ", ["titre", "version", "licence"])
def test_champ_obligatoire_manquant_refuse(tmp_path, champ):
    manifeste = MANIFESTE_VALIDE.format(id="incomplet")
    lignes = [ligne for ligne in manifeste.splitlines() if not ligne.startswith(f"{champ}:")]
    dossier = creer_extension(tmp_path, "incomplet", manifeste="\n".join(lignes) + "\n")
    with pytest.raises(ErreurExtension, match=champ):
        lire_extension(dossier)


def test_cle_fournit_inconnue_refusee(tmp_path):
    manifeste = MANIFESTE_VALIDE.format(id="mauvais").replace(
        "figures: [ma-figure]", "figures: [ma-figure]\n  video: [x]"
    )
    dossier = creer_extension(tmp_path, "mauvais", manifeste=manifeste)
    with pytest.raises(ErreurExtension, match="fournit"):
        lire_extension(dossier)


def test_cle_permission_inconnue_refusee(tmp_path):
    manifeste = MANIFESTE_VALIDE.format(id="gourmand").replace("reseau: false", "reseau: false\n  camera: true")
    dossier = creer_extension(tmp_path, "gourmand", manifeste=manifeste)
    with pytest.raises(ErreurExtension, match="permissions"):
        lire_extension(dossier)


def test_permission_non_booleenne_refusee(tmp_path):
    manifeste = MANIFESTE_VALIDE.format(id="etrange").replace("reseau: false", "reseau: peut-etre")
    dossier = creer_extension(tmp_path, "etrange", manifeste=manifeste)
    with pytest.raises(ErreurExtension, match="booleen"):
        lire_extension(dossier)


def test_toutes_les_cles_du_contrat_sont_couvertes():
    """Documente le contrat : ces ensembles sont ceux de docs/EXTENSIONS.md."""
    attendu_fournit = {
        "modules",
        "moteurs",
        "notifieurs",
        "outils",
        "figures",
        "rappels",
        "types_de_blocs",
        "bibliotheques",
    }
    attendu_permissions = {"reseau", "appel_ia", "ecriture_dossier_eleve", "notification_parent"}
    assert attendu_fournit == CLES_FOURNIT
    assert attendu_permissions == CLES_PERMISSIONS


# --- activation : seule une extension citee dans config.yaml est chargee -----------------


def test_extension_non_activee_non_chargee(tmp_path):
    creer_extension(tmp_path, "presente")
    chargees = charger_extensions(tmp_path, ids_actives=[])
    assert chargees == {}


def test_extension_activee_est_chargee(tmp_path):
    creer_extension(tmp_path, "presente")
    chargees = charger_extensions(tmp_path, ids_actives=["presente"])
    assert set(chargees) == {"presente"}


def test_extension_activee_mais_introuvable_ignoree_sans_lever(tmp_path):
    chargees = charger_extensions(tmp_path, ids_actives=["fantome"])
    assert chargees == {}


def test_extension_invalide_ecartee_sans_planter(tmp_path):
    creer_extension(tmp_path, "bonne")
    dossier_invalide = tmp_path / "invalide"
    dossier_invalide.mkdir()
    (dossier_invalide / "extension.yaml").write_text("id: invalide\n", encoding="utf-8")  # titre manquant
    trouvees = decouvrir_extensions(tmp_path)
    assert set(trouvees) == {"bonne"}


def test_decouvrir_racine_absente(tmp_path):
    assert decouvrir_extensions(tmp_path / "n_existe_pas") == {}


# --- ce que fournit une extension est utilisable : preuve du contrat ------------------------


def test_figure_fournie_par_extension_utilisable(tmp_path):
    creer_extension(tmp_path, "pack-figures")
    chargees = charger_extensions(tmp_path, ids_actives=["pack-figures"])
    assert figures_fournies(chargees) == {"ma-figure": "pack-figures"}


# --- figures proposees dans la discussion (cle `discussion`, jules/modules/figures.py) ---------------

DISCUSSION_VALIDE = (
    '  ma-figure:\n    quand: "Pour voir."\n    valeurs:\n      a: {min: -3, max: 3, pas: 0.5, defaut: 1}\n'
)


def _avec_discussion(tmp_path: Path, declaration: str) -> Path:
    return creer_extension(tmp_path, "pack", MANIFESTE_VALIDE.format(id="pack") + "discussion:\n" + declaration)


def test_discussion_valide_exposee(tmp_path):
    _avec_discussion(tmp_path, DISCUSSION_VALIDE)
    bornes = {"min": -3.0, "max": 3.0, "pas": 0.5, "defaut": 1.0}
    assert figures_pour_discussion(charger_extensions(tmp_path, ["pack"])) == {
        "ma-figure": {"quand": "Pour voir.", "valeurs": {"a": bornes}, "revele": False}
    }


def test_discussion_revele_lu(tmp_path):
    """`revele: true` est lu tel quel ; absent, il vaut false (test precedent)."""
    _avec_discussion(tmp_path, DISCUSSION_VALIDE.replace("    valeurs:", "    revele: true\n    valeurs:"))
    assert figures_pour_discussion(charger_extensions(tmp_path, ["pack"]))["ma-figure"]["revele"] is True


@pytest.mark.parametrize(
    ("declaration", "message"),
    [
        (DISCUSSION_VALIDE.replace("ma-figure", "autre-figure"), "fournit.figures"),
        (DISCUSSION_VALIDE.replace("defaut: 1", "defaut: 9"), "defaut doit etre compris"),
        (DISCUSSION_VALIDE.replace("pas: 0.5", "pas: 0"), "pas doit etre strictement positif"),
        (DISCUSSION_VALIDE.replace("min: -3", "min: 4"), "min doit etre inferieur"),
        (DISCUSSION_VALIDE.replace(", defaut: 1", ""), "attendu exactement"),
        (DISCUSSION_VALIDE.replace("pas: 0.5", "pas: .nan"), "des nombres"),
        (DISCUSSION_VALIDE.replace("max: 3", "max: true"), "des nombres"),
        (DISCUSSION_VALIDE.replace('"Pour voir."', '""'), "'quand'"),
        (DISCUSSION_VALIDE.replace("      a:", "      A b:"), "nom invalide"),
        ("  ma-figure: {quand: x, valeurs: {}}\n", "au moins une valeur"),
        ("  ma-figure: {quand: x, valeurs: {a: {min: 0, max: 1, pas: 1, defaut: 0}}, svg: x}\n", "{quand, valeurs}"),
        (DISCUSSION_VALIDE.replace("    valeurs:", "    revele: oui-non\n    valeurs:"), "'revele'"),
    ],
)
def test_discussion_invalide_refusee(tmp_path, declaration, message):
    dossier = _avec_discussion(tmp_path, declaration)
    with pytest.raises(ErreurExtension, match=re.escape(message)):
        lire_extension(dossier)


# Figures declarees pour la discussion par les extensions du depot : id -> (revele attendu, bornes reprises
# des curseurs des fiches visuelles 3e, voir le commentaire de chaque extension.yaml).
DECLARATIONS_DU_DEPOT = {
    "droite-affine": (False, {"a": (-3, 3, 0.5, 1), "b": (-4, 4, 1, 0)}),
    "triangle-thales": (False, {"t": (0.1, 0.9, 0.1, 0.5)}),
    # triangle-rectangle 2.0 : carres sur les cotes, la longueur AB n'est plus ecrite -> revele false.
    "triangle-rectangle": (False, {"ac": (1, 12, 1, 6), "bc": (1, 12, 1, 8)}),
    "equation-solutions": (True, {"a": (-25, 81, 1, 49)}),
    "probabilites-frequences": (False, {"n": (10, 500, 10, 50)}),
    "engrenages": (
        False,
        {"dents_a": (6, 60, 1, 12), "dents_b": (6, 60, 1, 18), "avance": (0, 360, 1, 0), "courroie": (0, 1, 1, 0)},
    ),
    "horloge": (False, {"h": (0, 23, 1, 9), "m": (0, 55, 5, 15), "duree": (0, 180, 5, 0)}),
    "urne-tirage": (False, {"rouges": (0, 10, 1, 3)}),
    "paquets-proportionnels": (False, {"a": (1, 10, 1, 4), "b": (50, 500, 50, 250), "fois": (0.25, 4, 0.25, 1)}),
}


def test_toutes_les_declarations_du_depot_se_chargent():
    """Chaque extension du depot qui a une cle `discussion` passe le controle, et les bornes sont celles prevues."""
    racine = Path(__file__).resolve().parents[1] / "extensions"
    ids = [d.name for d in sorted(racine.iterdir()) if (d / "extension.yaml").is_file()]
    declarations = figures_pour_discussion(charger_extensions(racine, ids))
    assert set(declarations) == set(DECLARATIONS_DU_DEPOT)
    for gabarit, (revele, valeurs) in DECLARATIONS_DU_DEPOT.items():
        assert declarations[gabarit]["revele"] is revele, gabarit
        lues = {
            nom: tuple(b[c] for c in ("min", "max", "pas", "defaut"))
            for nom, b in declarations[gabarit]["valeurs"].items()
        }
        assert lues == valeurs, gabarit


@pytest.mark.parametrize("gabarit", sorted(DECLARATIONS_DU_DEPOT))
def test_valeurs_declarees_lues_par_le_gabarit(gabarit):
    """Les noms de valeurs declares sont ceux que gabarit.js lit vraiment (`valeurs.<nom>`), ni plus ni moins."""
    code = (Path(__file__).resolve().parents[1] / "extensions" / gabarit / "gabarit.js").read_text(encoding="utf-8")
    assert set(re.findall(r"valeurs\.(\w+)", code)) == set(DECLARATIONS_DU_DEPOT[gabarit][1])


def test_droite_affine_du_depot_declaree_pour_la_discussion():
    racine = Path(__file__).resolve().parents[1] / "extensions"
    declaration = figures_pour_discussion(charger_extensions(racine, ["droite-affine"]))["droite-affine"]
    assert declaration["valeurs"]["a"] == {"min": -3.0, "max": 3.0, "pas": 0.5, "defaut": 1.0}


def test_extension_exemple_du_depot_est_valide():
    """L'extension livree avec cette etape (preuve du contrat) doit se charger sans erreur."""
    racine = Path(__file__).resolve().parents[1] / "extensions"
    extensions = decouvrir_extensions(racine)
    assert "exemple-figure" in extensions
    exemple = extensions["exemple-figure"]
    assert exemple.fournit_liste("figures") == ["exemple-cercle"]
    assert exemple.licence == "MIT"
