"""Assistant d'installation et commande `code` : fichiers produits, rien de secret en clair."""

from __future__ import annotations

import yaml

from jules.acces import code_correct
from jules.cli import enregistrer_code
from jules.installation import MOTEURS, config_locale, identifiant, lancer, ligne_env, profil_yaml


def test_identifiant_de_fichier():
    assert identifiant("Élise-Marie") == "elise-marie"
    assert identifiant("../../etc") == "etc"
    assert identifiant("!!!") == "eleve"


def test_profil_yaml_relu():
    donnees = yaml.safe_load(profil_yaml("Sam", "garcon", "4e", "son oncle"))
    assert donnees["prenom"] == "Sam" and donnees["genre"] == "garcon" and donnees["parent"] == "son oncle"


def test_config_locale_garde_les_codes():
    ollama = next(m for m in MOTEURS if m.id == "ollama")
    resultat = config_locale({"acces": {"code_parent": "x"}}, "sam", ollama)
    assert resultat["acces"] == {"code_parent": "x"}
    assert resultat["llm"]["backend"] == "openai_compatible" and resultat["profil"] == "sam"


def test_ligne_env_sans_doublon():
    assert ligne_env("", "CLE") == "CLE=\n"
    assert ligne_env("CLE=abc\n", "CLE") == "CLE=abc\n"
    assert ligne_env("AUTRE=1", "CLE") == "AUTRE=1\nCLE=\n"


def test_assistant_complet(tmp_path):
    (tmp_path / "profils").mkdir()
    reponses = iter(["Léa", "fille", "3e", "sa maman", "3"])  # 3 = Anthropic
    lancer(tmp_path, demander=lambda _q: next(reponses), afficher=lambda _t: None)
    profil = yaml.safe_load((tmp_path / "profils" / "lea.yaml").read_text(encoding="utf-8"))
    assert profil["genre"] == "fille" and profil["classe"] == "3e"
    local = yaml.safe_load((tmp_path / "config.local.yaml").read_text(encoding="utf-8"))
    assert local["profil"] == "lea" and local["llm"]["backend"] == "anthropic"
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "ANTHROPIC_API_KEY=\n"


def test_assistant_albert_pour_enseignants(tmp_path):
    (tmp_path / "profils").mkdir()
    numero = str([m.id for m in MOTEURS].index("albert") + 1)
    reponses = iter(["Noé", "garcon", "4e", "son professeur", numero])
    lancer(tmp_path, demander=lambda _q: next(reponses), afficher=lambda _t: None)
    local = yaml.safe_load((tmp_path / "config.local.yaml").read_text(encoding="utf-8"))
    assert local["llm"]["url"] == "https://albert.api.etalab.gouv.fr/v1"
    assert local["llm"]["cle_env"] == "ALBERT_API_KEY"
    assert local["llm"]["modeles"] == {"principal": "openweight-medium", "rapide": "openweight-small"}
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "ALBERT_API_KEY=\n"


def test_code_enregistre_en_empreinte_seulement(tmp_path):
    fichier = tmp_path / "config.local.yaml"
    fichier.write_text("profil: sam\n", encoding="utf-8")
    enregistrer_code(fichier, "parent", "secret-parent")
    texte = fichier.read_text(encoding="utf-8")
    assert "secret-parent" not in texte
    donnees = yaml.safe_load(texte)
    assert donnees["profil"] == "sam"
    assert code_correct("secret-parent", donnees["acces"]["code_parent"])


def test_verifier_ne_plante_pas_sur_une_console_cp1252():
    """Regression : sur Windows, la console en cp1252 ne sait pas afficher certains symboles du prompt."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    resultat = subprocess.run(
        [sys.executable, "-m", "jules", "verifier"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        env=env,
        check=False,
    )
    assert resultat.returncode == 0, resultat.stderr.decode("utf-8", "replace")[-800:]
