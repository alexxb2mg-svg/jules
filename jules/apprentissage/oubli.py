"""Oubli : courbe de retention et stabilite, d'apres FSRS-4.5 (docs/MODELE-ELEVE.md, §5).

Formules reprises telles quelles du wiki « The Algorithm » (open-spaced-repetition/awesome-fsrs),
section FSRS-4.5. Parametres w : `parametres.FSRS45_DEFAUT`.
Notes FSRS : 1 again, 2 hard, 3 good, 4 easy. Jules n'utilise que 1, 2 et 3.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime

DECAY = -0.5
FACTOR = 19 / 81  # R(S, S) = 0,9
D_MIN, D_MAX = 1.0, 10.0
S_MIN = 0.01  # jours : evite les divisions par zero sur une stabilite degeneree


def jours_entre(debut: str, fin: str) -> float:
    """Ecart en jours (fractionnaires) entre deux horodatages ISO 8601 ; jamais negatif."""
    ecart = datetime.fromisoformat(fin) - datetime.fromisoformat(debut)
    return max(0.0, ecart.total_seconds() / 86400)


def _bornee(d: float) -> float:
    return min(D_MAX, max(D_MIN, d))


def retention(jours: float, stabilite: float) -> float:
    """R(t, S) = (1 + F t / S) ^ DECAY. t < 0 est traite comme 0."""
    t = max(0.0, jours)
    return float((1 + FACTOR * t / max(stabilite, S_MIN)) ** DECAY)


def intervalle(retention_cible: float, stabilite: float) -> float:
    """Jours avant que R passe sous la cible : I(r, S) = S / F * (r^(1/DECAY) - 1)."""
    if not 0 < retention_cible < 1:
        raise ValueError("retention_cible doit etre dans ]0, 1[")
    return stabilite / FACTOR * (retention_cible ** (1 / DECAY) - 1)


def stabilite_initiale(note: int, w: Sequence[float]) -> float:
    """S0(G) = w[G-1]."""
    if note not in (1, 2, 3, 4):
        raise ValueError(f"note FSRS 1 a 4 attendue, recu {note}")
    return float(w[note - 1])


def difficulte_initiale(note: int, w: Sequence[float]) -> float:
    """D0(G) = w4 - (G - 3) w5, bornee a [1, 10]."""
    return _bornee(w[4] - (note - 3) * w[5])


def difficulte_suivante(difficulte: float, note: int, w: Sequence[float]) -> float:
    """D' = w7 D0(3) + (1 - w7) (D - w6 (G - 3)), bornee a [1, 10] (retour a la moyenne)."""
    d0 = w[4]  # D0(3)
    return _bornee(w[7] * d0 + (1 - w[7]) * (difficulte - w[6] * (note - 3)))


def stabilite_apres_succes(difficulte: float, stabilite: float, r: float, note: int, w: Sequence[float]) -> float:
    """S'_r = S (e^w8 (11 - D) S^-w9 (e^(w10 (1 - R)) - 1) x w15 si hard x w16 si easy + 1)."""
    facteur = 1.0
    if note == 2:
        facteur = w[15]
    elif note == 4:
        facteur = w[16]
    inc = math.exp(w[8]) * (11 - difficulte) * stabilite ** (-w[9]) * (math.exp(w[10] * (1 - r)) - 1) * facteur
    return stabilite * (inc + 1)


def stabilite_apres_oubli(difficulte: float, stabilite: float, r: float, w: Sequence[float]) -> float:
    """S'_f = w11 D^-w12 ((S + 1)^w13 - 1) e^(w14 (1 - R)), jamais au-dessus de S."""
    s = w[11] * difficulte ** (-w[12]) * ((stabilite + 1) ** w[13] - 1) * math.exp(w[14] * (1 - r))
    return max(S_MIN, min(s, stabilite))


def note_premiere_seance(reussite_sans_aide: bool, reussite_avec_aide: bool, p: float) -> int:
    """§5.1 : good si reussite sans aide et p >= 0,7 ; hard si reussite seulement avec aide ; again sinon."""
    if reussite_sans_aide and p >= 0.7:
        return 3
    if reussite_sans_aide or reussite_avec_aide:
        return 2
    return 1


def proba_epreuve(p: float, r: float, glissement: float, chance: float) -> float:
    """§5.3 : pi = p [R (1 - s_e) + (1 - R) g_e] + (1 - p) g_e."""
    return p * (r * (1 - glissement) + (1 - r) * chance) + (1 - p) * chance


def vraisemblances_epreuve(r: float, glissement: float, chance: float) -> tuple[float, float]:
    """P(tenu | L), P(tenu | non L) : de quoi mettre p a jour apres une epreuve (§5.3)."""
    return r * (1 - glissement) + (1 - r) * chance, chance
