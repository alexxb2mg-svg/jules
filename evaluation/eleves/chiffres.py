"""Chiffres de la campagne eleves simules (tours r1, r2, r3), recalcules depuis les fichiers .jsonl.

Usage : python evaluation/eleves/chiffres.py -> evaluation/eleves/chiffres_campagne.json
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from analyse import socles, stats_modele  # noqa: E402

PROJETS = ICI.parents[2]
TOURS = {
    "r1": PROJETS / "jules-eval-eleves" / "evaluation" / "eleves" / "runs" / "r1",
    "r2": PROJETS / "jules-eval-corr" / "evaluation" / "eleves" / "runs" / "r2",
    "r3": ICI / "runs" / "r3",
}


def charger(dossier: Path, modele: str) -> list[dict]:
    f = dossier / f"{modele}.jsonl"
    if not f.is_file():
        return []
    return [json.loads(ligne) for ligne in f.read_text(encoding="utf-8").splitlines() if ligne.strip()]


def par_profil(rs: list[dict]) -> dict[str, float]:
    notes: dict[str, list[float]] = {}
    for r in rs:
        n = (r.get("juge") or {}).get("note_globale")
        if isinstance(n, int | float):
            notes.setdefault(r["eleve"], []).append(n)
    return {k: round(statistics.mean(v), 1) for k, v in sorted(notes.items())}


def main() -> None:
    sortie: dict = {}
    for tour, dossier in TOURS.items():
        for modele in ("haiku", "sonnet"):
            rs = charger(dossier, modele)
            if not rs:
                continue
            s = stats_modele(rs, socles())
            s["par_profil"] = par_profil(rs)
            sortie.setdefault(tour, {})[modele] = s
    (ICI / "chiffres_campagne.json").write_text(json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
    for tour, d in sortie.items():
        for modele, s in d.items():
            print(tour, modele, s.get("conversations"), s.get("fuite_juge"), s.get("note_globale"))


if __name__ == "__main__":
    main()
