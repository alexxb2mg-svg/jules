"""Messages d'erreur de configuration : yaml casse, profil absent (voir jules/config.py)."""

from __future__ import annotations

import pytest

from jules.config import ErreurConfig, charger_config


def test_yaml_mal_indente_message_clair(tmp_path):
    fichier = tmp_path / "config.yaml"
    fichier.write_text(
        "serveur:\n  hote: 127.0.0.1\n    port: 8797\n",  # sur-indentation : ParserError
        encoding="utf-8",
    )
    with pytest.raises(ErreurConfig, match=r"config\.yaml a une erreur d'indentation vers la ligne \d+"):
        charger_config(fichier)


def test_profil_absent_liste_les_disponibles(tmp_path):
    (tmp_path / "profils").mkdir()
    (tmp_path / "profils" / "camille.yaml").write_text("prenom: Camille\n", encoding="utf-8")
    fichier = tmp_path / "config.yaml"
    fichier.write_text("persona: jules\nprofil: nexistepas\n", encoding="utf-8")
    with pytest.raises(ErreurConfig, match=r"Profil « nexistepas » introuvable.*camille"):
        charger_config(fichier)
