"""Point d'entree sans installation : `python lancer.py [commande]` (voir jules/cli.py)."""

import sys

if sys.version_info < (3, 10):  # noqa: UP036 - verifie l'interpreteur qui EXECUTE ce fichier, pas la cible ruff
    sys.exit(
        f"Jules a besoin de Python 3.10 ou plus (vous avez {sys.version_info.major}.{sys.version_info.minor}). "
        "Installez-le depuis python.org puis relancez."
    )

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jules.cli import main

if __name__ == "__main__":
    main()
