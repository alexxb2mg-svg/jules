"""EX-010 (docs/spec/ADAPTATIONS.md) : aucune taille de police en px dans les CSS de jules/web/static/.

Les tailles en `rem` suivent la taille de la racine : un futur reglage « taille du texte » agira partout.
"""

from __future__ import annotations

import re
from pathlib import Path

STATIQUE = Path(__file__).resolve().parents[1] / "jules" / "web" / "static"
# `font-size: 18px` et le raccourci `font: 500 15px/1.35 ...`
TAILLE_PX = re.compile(r"font-size\s*:[^;{}]*?\d(?:\.\d+)?px|font\s*:[^;{}]*?\d(?:\.\d+)?px", re.IGNORECASE)


def test_il_y_a_des_css_a_verifier():
    assert len(list(STATIQUE.glob("*.css"))) >= 5


def test_aucune_taille_de_police_en_px():
    fautes = []
    for css in sorted(STATIQUE.glob("*.css")):
        for n, ligne in enumerate(css.read_text(encoding="utf-8").splitlines(), 1):
            if TAILLE_PX.search(ligne):
                fautes.append(f"{css.name}:{n}: {ligne.strip()}")
    assert not fautes, "tailles de police en px (utiliser rem, EX-010) :\n" + "\n".join(fautes)


def test_le_motif_attrape_les_deux_ecritures():
    assert TAILLE_PX.search(".a { font-size: 14px; }")
    assert TAILLE_PX.search(".b { font: 500 15px/1.35 sans-serif; }")
    assert not TAILLE_PX.search(".c { font-size: 0.875rem; padding: 12px; }")
    assert not TAILLE_PX.search(".d { font: inherit; padding: 8px 10px; }")
