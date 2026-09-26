"""Le patron des fiches visuelles : paquet de generation, controle et apercu (jules/chantier_visuel.py)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from jules.chantier_visuel import construire_apercu, controler, paquet, version_paquet

RACINE = Path(__file__).resolve().parents[1]
BIBLIOTHEQUES = RACINE / "bibliotheque"
EXPERIMENTALE = BIBLIOTHEQUES / "fiches-visuelles-3e-experimentales"


def test_paquet_contient_charte_format_modele_et_notions():
    texte = paquet([BIBLIOTHEQUES], ["racine-carree"], par="camille", jour="2026-09-26")
    assert "fiche de RÉVISION" in texte and version_paquet() in texte
    assert "## La charte" in texte and "complément d'explication" in texte and "÷" in texte
    assert "## Le format" in texte and "`variables:`" in texte
    # Une fiche visuelle existante sert de modele, avec son schema, jamais celle d'une notion demandee.
    assert "## Une fiche conforme" in texte and "```svg" in texte
    assert "`fiches/mathematiques/racine-carree.yaml`" in texte and "Attendus officiels" in texte
    assert 'par: "camille"' in texte and 'le: "2026-09-26"' in texte


def test_paquet_ne_prend_jamais_pour_modele_une_notion_demandee():
    texte = paquet([BIBLIOTHEQUES], ["parallelisme-triangles-pythagore"])
    modele = texte.split("## Une fiche conforme")[1].split("## Les notions")[0]
    assert "notion: parallelisme-triangles-pythagore" not in modele


def test_paquet_refuse_une_notion_inconnue():
    with pytest.raises(ValueError, match="inconnue"):
        paquet([BIBLIOTHEQUES], ["pas-une-notion"])


def test_controler_donne_le_motif_des_fiches_ecartees(tmp_path):
    copie = tmp_path / "fiches-visuelles-3e-experimentales"
    shutil.copytree(EXPERIMENTALE, copie)
    chemin = copie / "fiches" / "mathematiques" / "fonctions-lineaires-affines.yaml"
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    brut["titre"] = "Pente : a = Δy / Δx"
    chemin.write_text(yaml.safe_dump(brut, allow_unicode=True), encoding="utf-8")
    fiches, ecartees = controler([BIBLIOTHEQUES], copie)
    assert len(fiches) == 4
    assert len(ecartees) == 1 and "fonctions-lineaires-affines.yaml" in ecartees[0] and "÷" in ecartees[0]


def test_apercu_hors_ligne_avec_api_simulee(tmp_path):
    fiches, ecartees = controler([BIBLIOTHEQUES], EXPERIMENTALE)
    assert not ecartees
    index = construire_apercu([BIBLIOTHEQUES], fiches, tmp_path / "apercu")
    html = index.read_text(encoding="utf-8")
    assert "/static/" not in html and "/api/" not in html
    assert html.index("simulation.js") < html.index("static/commun.js")
    simulation = (tmp_path / "apercu" / "simulation.js").read_text(encoding="utf-8")
    donnees = json.loads(simulation.split("const DONNEES = ", 1)[1].split(";\n", 1)[0])
    assert {n["id"] for m in donnees["/api/eleve/fiches_visuelles/notions"]["matieres"] for n in m["notions"]} == set(
        fiches
    )
    assert (tmp_path / "apercu" / "static" / "symboles.js").is_file()
