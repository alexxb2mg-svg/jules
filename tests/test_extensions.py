"""Tests du chargeur d'extensions (jules/extensions.py, voir docs/EXTENSIONS.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from jules.extensions import (
    CLES_FOURNIT,
    CLES_PERMISSIONS,
    ErreurExtension,
    charger_extensions,
    decouvrir_extensions,
    figures_fournies,
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


def test_extension_exemple_du_depot_est_valide():
    """L'extension livree avec cette etape (preuve du contrat) doit se charger sans erreur."""
    racine = Path(__file__).resolve().parents[1] / "extensions"
    extensions = decouvrir_extensions(racine)
    assert "exemple-figure" in extensions
    exemple = extensions["exemple-figure"]
    assert exemple.fournit_liste("figures") == ["exemple-cercle"]
    assert exemple.licence == "MIT"
