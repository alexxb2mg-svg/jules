"""Messages d'erreur au demarrage (`jules serveur`), rotation des logs et verification des
dependances entre modules (voir jules/cli.py, jules/moteur.py)."""

from __future__ import annotations

import logging
import logging.handlers
import socket
import sys

import pytest

from jules import cli
from jules.config import Config
from jules.moteur import ErreurDependance, Tuteur


def _config_minimale(tmp_path, port: int) -> Config:
    return Config(
        racine=tmp_path,
        donnees=tmp_path / "donnees",
        hote="127.0.0.1",
        port=port,
        persona="jules",
        profil="exemple",
        llm={"backend": "demo"},
        acces={},
        modules=[],
        notifieurs=[],
    )


def test_port_deja_pris_message_clair(monkeypatch, tmp_path):
    """Un autre Jules (ou n'importe quel programme) ecoute deja sur le port : message clair, pas
    de traceback, et rien n'est imprime comme si le serveur avait demarre."""
    occupe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupe.bind(("127.0.0.1", 0))
    occupe.listen(1)
    port = occupe.getsockname()[1]
    try:
        config = _config_minimale(tmp_path, port)
        monkeypatch.setattr(cli, "charger_config", lambda _chemin: config)
        with pytest.raises(SystemExit) as exc:
            cli.servir()
        message = str(exc.value)
        assert str(port) in message
        assert "déjà pris" in message
        assert "config.local.yaml" in message
    finally:
        occupe.close()


def test_journaliser_installe_une_rotation(tmp_path):
    """Le fichier de log tourne (jamais d'ecriture illimitee) : RotatingFileHandler, pas FileHandler simple."""
    logger_racine = logging.getLogger()
    handlers_avant = list(logger_racine.handlers)
    try:
        cli.journaliser(tmp_path / "donnees")
        fichiers = [h for h in logger_racine.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert fichiers, "aucun RotatingFileHandler installe"
        assert fichiers[0].maxBytes > 0 and fichiers[0].backupCount >= 1
    finally:
        logger_racine.handlers = handlers_avant


def test_module_verifier_python_minimum():
    """`requires-python` du projet (pyproject.toml) et lancer.py/__main__.py doivent s'accorder :
    ce test lit le seuil reel plutot que de le recopier en dur."""
    import re
    from pathlib import Path

    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    seuil = re.search(r'requires-python\s*=\s*">=(\d+)\.(\d+)"', pyproject)
    assert seuil is not None
    assert (int(seuil.group(1)), int(seuil.group(2))) == (3, 10)
    for fichier in ("lancer.py", "jules/__main__.py"):
        texte = (Path(__file__).resolve().parents[1] / fichier).read_text(encoding="utf-8")
        assert "sys.version_info < (3, 10)" in texte
        assert "Python 3.10 ou plus" in texte


def test_version_python_trop_ancienne_message_clair(monkeypatch, capsys):
    """La verification de version, executee dans lancer.py/__main__.py avant tout import de jules,
    n'est pas testable directement en subprocess sans installer un vieux Python : on isole ici la
    meme logique et verifie le message."""
    import collections

    def verification(version_info):
        if version_info < (3, 10):
            sys.exit(
                f"Jules a besoin de Python 3.10 ou plus (vous avez {version_info.major}.{version_info.minor}). "
                "Installez-le depuis python.org puis relancez."
            )

    Version = collections.namedtuple("Version", "major minor micro releaselevel serial")
    ancienne = Version(3, 9, 0, "final", 0)
    with pytest.raises(SystemExit) as exc:
        verification(ancienne)
    assert "Python 3.10 ou plus" in str(exc.value)
    assert "3.9" in str(exc.value)


def test_dependance_manquante_message_nomme_les_deux_modules(tmp_path):
    """`cours` sans `notions` actif : le moteur refuse de demarrer avec un message nommant les deux
    modules (et non un RuntimeError brut au premier acces a la @property)."""
    config = _config_minimale(tmp_path, 8797)
    config.donnees.mkdir(parents=True, exist_ok=True)
    (tmp_path / "profils").mkdir()
    (tmp_path / "profils" / "exemple.yaml").write_text("prenom: Test\n", encoding="utf-8")
    (tmp_path / "persona" / "jules").mkdir(parents=True)
    (tmp_path / "persona" / "jules" / "persona.yaml").write_text("nom: Jules\n", encoding="utf-8")
    (tmp_path / "consignes").mkdir()
    from jules.config import RefBrique

    config.modules = [RefBrique(id="cours")]
    with pytest.raises(ErreurDependance, match=r"« cours ».*« notions »"):
        Tuteur(config)
