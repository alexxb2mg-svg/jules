"""Le README ne doit pas decrocher du code : ce que le README affirme est mesure ici.

Premier signal de fiabilite pour un contributeur ou un enseignant : si le README annonce 13 leviers,
il y en a 13 ; si un module est actif dans config.yaml, le README le nomme ; si la description du paquet
dit « du CM1 a la 3e », le README dit la meme chose.
"""

from __future__ import annotations

import re

import yaml

from jules.config import RACINE

README = (RACINE / "README.md").read_text(encoding="utf-8")
CONFIG = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))


def _nombres(motif: str) -> set[int]:
    """Tous les nombres N qui precedent `motif` dans le README (« 13 leviers » -> 13)."""
    return {int(n) for n in re.findall(rf"(\d+)\s+{motif}", README)}


def _yaml_hors_readme(dossier: str) -> int:
    return len(list((RACINE / dossier).glob("*.yaml")))


def test_chaque_module_de_config_est_nomme_dans_le_readme():
    absents = [m["id"] for m in CONFIG["modules"] if f"`{m['id']}`" not in README]
    assert not absents, f"modules de config.yaml absents de la ligne « Modules » du README : {absents}"


def test_leviers_et_amenagements_annonces_sont_les_vrais():
    assert _nombres("leviers") == {_yaml_hors_readme("adaptations/leviers")}
    assert _nombres(r"am[ée]nagements") == {_yaml_hors_readme("adaptations/amenagements")}


def test_extensions_annoncees_sont_les_vraies():
    assert _nombres(r"extensions activ[ée]es") == {len(CONFIG["extensions"])}
    dossiers = [d for d in (RACINE / "extensions").iterdir() if d.is_dir()]
    assert _nombres(r"dossiers dans `extensions/`") == {len(dossiers)}


def test_generateurs_annonces_sont_les_vrais():
    reels = [f for f in (RACINE / "jules" / "generateurs" / "mathematiques").glob("*.py") if not f.name.startswith("_")]
    assert _nombres(r"notions de math[ée]matiques 3e") == {len(reels)}


def test_niveaux_du_paquet_et_du_readme_concordent():
    pyproject = (RACINE / "pyproject.toml").read_text(encoding="utf-8")
    description = re.search(r'^description\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)[1]  # type: ignore[index]
    niveaux = re.search(r"du (\w+) [àa] la (\w+)", description)
    assert niveaux, "la description du paquet doit annoncer ses niveaux (« du CM1 a la 3e »)"
    assert re.search(rf"du {niveaux[1]} à la {niveaux[2]}", README), (
        "le README n'annonce pas les mêmes niveaux que pyproject.toml"
    )
