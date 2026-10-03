"""Le README ne doit pas decrocher du code : ce que le README affirme est mesure ici.

Premier signal de fiabilite pour un contributeur ou un enseignant : si le README annonce 13 leviers,
il y en a 13 ; si un module est actif dans config.yaml, le README le nomme ; si la description du paquet
dit « du CM1 a la 3e », le README dit la meme chose.

La ligne "Modules" du tableau d'architecture : chaque id de module cite en `code` dans cette ligne a son
fichier jules/modules/<id>.py et est actif dans config.yaml ; chaque module actif dans config.yaml y est
cite. Un module desactive (comme modele_eleve) n'y figure pas : la ligne decrit ce qui est en place (il
a sa propre ligne dans le tableau).
"""

from __future__ import annotations

import re

import yaml

from jules.config import RACINE, RefBrique

README = (RACINE / "README.md").read_text(encoding="utf-8")
CONFIG = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))


def _nombres(motif: str) -> set[int]:
    """Tous les nombres N qui precedent `motif` dans le README (« 13 leviers » -> 13)."""
    return {int(n) for n in re.findall(rf"(\d+)\s+{motif}", README)}


def _yaml_hors_readme(dossier: str) -> int:
    return len(list((RACINE / dossier).glob("*.yaml")))


def test_chaque_module_de_config_est_nomme_dans_le_readme():
    absents = [m["id"] for m in CONFIG["modules"] if f"`{m['id']}`" not in README]
    assert not absents, f"modules de config.yaml absents du README : {absents}"


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
    # Depuis l'audit externe (#85), le paquet est un harnais « fourni avec les bibliotheques du programme
    # officiel de CM1, 5e, 4e et 3e » : le README doit citer les memes niveaux, dans le meme ordre.
    niveaux = re.findall(r"\b(CP|CE[12]|CM[12]|[3-6]e)\b", description)
    assert niveaux, "la description du paquet doit annoncer ses niveaux (« de CM1, 5e, 4e et 3e »)"
    assert f"({', '.join(niveaux)}" in README, (
        f"le README n'annonce pas les mêmes niveaux que pyproject.toml ({', '.join(niveaux)})"
    )


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
