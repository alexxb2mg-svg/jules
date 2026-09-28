"""Permet `python -m jules [commande]`."""

import sys

if sys.version_info < (3, 10):  # noqa: UP036 - verifie l'interpreteur qui EXECUTE ce fichier, pas la cible ruff
    sys.exit(
        f"Jules a besoin de Python 3.10 ou plus (vous avez {sys.version_info.major}.{sys.version_info.minor}). "
        "Installez-le depuis python.org puis relancez."
    )

from jules.cli import main

main()
