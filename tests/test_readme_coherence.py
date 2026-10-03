"""Coherence entre le README et config.yaml : la ligne "Modules" du tableau d'architecture.

Chaque id de module cite en `code` dans cette ligne a son fichier jules/modules/<id>.py et est actif
dans config.yaml ; chaque module actif dans config.yaml y est cite. Un module desactive (comme
modele_eleve) ne doit donc pas y figurer : la ligne decrit ce qui est en place.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from jules.config import RefBrique

RACINE = Path(__file__).resolve().parents[1]
README = (RACINE / "README.md").read_text(encoding="utf-8")
CONFIG = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))


def ligne_modules() -> str:
    """La ligne "Modules" du tableau de la section "Comment c'est construit"."""
    lignes = [ligne for ligne in README.splitlines() if ligne.startswith("| Modules |")]
    assert len(lignes) == 1, f"le README doit avoir une seule ligne '| Modules |', trouvees : {len(lignes)}"
    return lignes[0]


def ids_cites() -> set[str]:
    """Ids en `code` dans la ligne ; les chemins (`jules/modules/<id>.py`, `consignes/...`) sont ignores."""
    return {code for code in re.findall(r"`([^`]+)`", ligne_modules()) if re.fullmatch(r"[a-z_]+", code)}


def modules_actifs() -> set[str]:
    """Modules actifs de config.yaml, lus comme le fait jules/config.py (actif par defaut)."""
    return {ref.id for ref in map(RefBrique.depuis, CONFIG["modules"]) if ref.actif}


def test_chaque_module_cite_dans_le_readme_existe_et_est_actif():
    cites = ids_cites()
    assert cites, "aucun id de module en `code` dans la ligne Modules du README"
    sans_fichier = sorted(i for i in cites if not (RACINE / "jules" / "modules" / f"{i}.py").is_file())
    assert not sans_fichier, f"cites dans le README sans fichier jules/modules/<id>.py : {sans_fichier}"
    inactifs = sorted(cites - modules_actifs())
    assert not inactifs, f"cites dans le README mais pas actifs dans config.yaml : {inactifs}"


def test_chaque_module_actif_est_cite_dans_le_readme():
    actifs = modules_actifs()
    assert actifs, "aucun module actif lu dans config.yaml"
    absents = sorted(actifs - ids_cites())
    assert not absents, f"actifs dans config.yaml mais absents de la ligne Modules du README : {absents}"
