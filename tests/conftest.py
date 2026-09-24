"""Fixtures communes : un tuteur complet branche sur le moteur factice, dans un dossier temporaire."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from jules.config import depuis_dict  # noqa: E402
from jules.llm.factice import Brique as Factice  # noqa: E402
from jules.moteur import Tuteur  # noqa: E402


def regle_par_defaut(systeme: str, tours, modele: str) -> str:
    if "suivi scolaire" in systeme:
        return (
            '{"matiere": "Mathématiques", "notion": "fractions : addition", "statut": "bloque", '
            '"resume": "Addition de fractions.", "titre": "Fractions"}'
        )
    if "Tu protèges un élève" in systeme:
        return '{"niveau": "aucun", "motif": ""}'
    if "résumé de sa séance" in systeme:
        return "Belle séance sur les fractions."
    return "Qu'est-ce que tu as déjà essayé ?"


@pytest.fixture
def projet(tmp_path: Path) -> Path:
    """Copie des fichiers de contenu (persona, consignes, profils) dans un dossier jetable."""
    for dossier in ("persona", "consignes", "profils"):
        shutil.copytree(RACINE / dossier, tmp_path / dossier)
    return tmp_path


@pytest.fixture
def brut_config() -> dict:
    brut = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))
    brut["llm"] = {"backend": "factice", "historique_max": 30}
    return brut


@pytest.fixture
def tuteur(projet: Path, brut_config: dict):
    config = depuis_dict(brut_config, projet)
    llm = Factice()
    llm.regle = regle_par_defaut
    t = Tuteur(config, llm=llm)
    yield t
    t.fermer()
