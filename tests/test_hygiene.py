"""Hygiene du depot : ce qui est publie reste generique.

Ces tests protegent les contributeurs : ils echouent si des donnees personnelles, des chemins
propres a une machine ou des secrets se glissent dans les fichiers publies.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
EXTENSIONS = {".py", ".md", ".yaml", ".yml", ".toml", ".js", ".html", ".css", ".svg", ".txt", ".cfg", ".json"}
MOTIFS_INTERDITS = {
    "chemin Windows personnel": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?!OWNER|<)\w+", re.IGNORECASE),
    "chemin Linux/macOS personnel": re.compile(r"/(?:home|Users)/(?!runner\b|OWNER\b|<)[a-z][\w.-]+/", re.IGNORECASE),
    "adresse IP du reseau local": re.compile(r"\b(?:192\.168|10\.\d{1,3})\.\d{1,3}\.\d{1,3}\b"),
    "adresse e-mail": re.compile(r"[\w.+-]+@(?!users\.noreply\.github\.com)[\w-]+\.[\w.]+"),
    "cle API": re.compile(r"\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,})\b"),
    "jeton Telegram": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
}


def fichiers_publies() -> list[Path]:
    """Fichiers que git publierait (suivis ou nouveaux non ignores) ; repli sur le disque hors git."""
    try:
        sortie = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
            cwd=RACINE,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        chemins = [RACINE / ligne for ligne in sortie.splitlines() if ligne]
    except (OSError, subprocess.CalledProcessError):
        chemins = [p for p in RACINE.rglob("*") if ".git" not in p.parts]
    return [p for p in chemins if p.is_file() and p.suffix in EXTENSIONS and p.name != Path(__file__).name]


def test_il_y_a_des_fichiers_a_verifier():
    assert len(fichiers_publies()) > 20


@pytest.mark.parametrize("nom", sorted(MOTIFS_INTERDITS))
def test_rien_de_personnel_dans_les_fichiers_publies(nom):
    motif = MOTIFS_INTERDITS[nom]
    fautifs = [
        f"{p.relative_to(RACINE)}: {m.group(0)}"
        for p in fichiers_publies()
        for m in [motif.search(p.read_text(encoding="utf-8", errors="replace"))]
        if m
    ]
    assert not fautifs, f"{nom} trouve(e) dans : {fautifs}"


def test_fichiers_prives_ignores_par_git():
    ignores = (RACINE / ".gitignore").read_text(encoding="utf-8")
    for motif in ("donnees/", "config.local.yaml", ".env", "profils/*", "*.key"):
        assert motif in ignores.splitlines(), motif


def test_seul_le_profil_exemple_est_publie():
    profils = [p.name for p in fichiers_publies() if p.parent.name == "profils"]
    assert profils == ["exemple.yaml"]


def test_config_publiee_sure_par_defaut():
    import yaml

    config = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))
    assert config["serveur"]["hote"] == "127.0.0.1"
    assert config["llm"]["backend"] == "demo"
    assert not any(config["acces"].values())
    assert config["profil"] == "exemple"
