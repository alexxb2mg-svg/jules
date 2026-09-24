"""Point d'entree sans installation : `python lancer.py [commande]` (voir jules/cli.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jules.cli import main

if __name__ == "__main__":
    main()
