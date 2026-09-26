"""Analyse d'un tour du banc : taux, notes, cout, latence, par modele, profil, surface.

Usage : python evaluation/eleves/analyse.py r1 [r2]   -> evaluation/eleves/runs/<run>/ANALYSE.md + analyse.json
Avec deux tours : comparaison avant / apres sur les memes scenarios.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

DOSSIER = Path(__file__).resolve().parent
# Tarifs API publics (USD par million de jetons, septembre 2026) : entree, sortie
TARIFS = {"haiku": (1.0, 5.0), "sonnet": (2.0, 10.0)}
ROLES_JULES = ("jules", "suivi", "vigilance", "detection", "rapport", "bilan_epreuve", "rapide_autre")


def charger(run: str) -> dict[str, list[dict[str, Any]]]:
    res = {}
    for f in sorted((DOSSIER / "runs" / run).glob("*.jsonl")):
        lignes = [json.loads(ligne) for ligne in f.read_text(encoding="utf-8").splitlines() if ligne.strip()]
        # derniere version de chaque (id, repetition)
        par_cle = {(r["id"], r["repetition"]): r for r in lignes}
        res[f.stem] = list(par_cle.values())
    return res


def socles() -> dict[str, int]:
    f = DOSSIER / "socles.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def famille(modele: str) -> str:
    m = modele.casefold()
    return "haiku" if "haiku" in m else "sonnet" if "sonnet" in m else "opus" if "opus" in m else m


def cout_api(appels: list[dict[str, Any]], soc: dict[str, int]) -> tuple[float, dict[str, float]]:
    """Cout au tarif API des appels faits PAR JULES (hors eleve simule et juge), socle du CLI retire."""
    total = 0.0
    par_role: dict[str, float] = defaultdict(float)
    for a in appels:
        if a["role"] not in ROLES_JULES:
            continue
        fam = famille(a["modele"])
        if fam not in TARIFS:
            continue
        entree = max(0, a["entree"] - soc.get(fam, 0))
        c = (entree * TARIFS[fam][0] + a["sortie"] * TARIFS[fam][1]) / 1e6
        total += c
        par_role[a["role"]] += c
    return total, dict(par_role)


def pct(n: int, d: int) -> str:
    return f"{n}/{d} ({100 * n / d:.0f} %)" if d else "n/a"


def moyenne(valeurs: list[float]) -> float | None:
    v = [x for x in valeurs if isinstance(x, int | float)]
    return round(statistics.mean(v), 2) if v else None


def quantile(valeurs: list[float], q: float) -> float | None:
    v = sorted(valeurs)
    if not v:
        return None
    return round(v[min(len(v) - 1, int(q * len(v)))], 1)


def stats_modele(lignes: list[dict[str, Any]], soc: dict[str, int]) -> dict[str, Any]:
    ok = [r for r in lignes if not r.get("erreur") and isinstance(r.get("juge"), dict) and "note_globale" in r["juge"]]
    err = [r for r in lignes if r.get("erreur")]
    n = len(ok)
    j = [r["juge"] for r in ok]
    m = [r["mesures"] for r in ok]
    fuite_juge = [r for r in ok if r["juge"].get("fuite")]
    fuite_det = [r for r in ok if r["mesures"].get("fuite_detecteur")]
    a_la_place = [r for r in ok if r["juge"].get("fait_a_la_place")]
    erreur_fond = [r for r in ok if r["juge"].get("erreur_de_fond")]
    valid_err = [r for r in ok if r["juge"].get("validation_erronee")]
    trouve = [r for r in ok if r["juge"].get("eleve_a_trouve") in ("oui", "non")]
    vig_attendue = [r for r in ok if r["mesures"]["vigilance_attendue"] == "alerte"]
    vig_pas = [r for r in ok if r["mesures"]["vigilance_attendue"] == "aucune"]
    notion = [r for r in ok if r["mesures"].get("notion_ok") is not None]
    rapport = [r for r in ok if isinstance(r["juge"].get("rapport_fidele"), bool)]
    durees = [d for r in ok for d in r["mesures"]["duree_jules_s"]]
    couts = [cout_api(r["appels"], soc)[0] for r in ok]
    tours = [r["mesures"]["tours_eleve"] for r in ok]
    cout_par_tour = [c / t for c, t in zip(couts, tours, strict=True) if t]
    roles: dict[str, float] = defaultdict(float)
    for r in ok:
        for role, c in cout_api(r["appels"], soc)[1].items():
            roles[role] += c
    total_roles = sum(roles.values()) or 1
    jetons_sys = [a["car_systeme"] for r in ok for a in r["appels"] if a["role"] == "jules"]
    appels_par_echange = [
        sum(1 for a in r["appels"] if a["role"] in ROLES_JULES) / r["mesures"]["tours_eleve"]
        for r in ok
        if r["mesures"]["tours_eleve"]
    ]
    phrases = [p for r in ok for p in r["mesures"]["phrases"]]
    return {
        "conversations": n,
        "erreurs": len(err),
        "erreurs_detail": [f"{r['id']}#{r['repetition']}: {r['erreur'][:150]}" for r in err],
        "fuite_juge": pct(len(fuite_juge), n),
        "fuite_detecteur": pct(len(fuite_det), n),
        "fait_a_la_place": pct(len(a_la_place), n),
        "erreur_de_fond": pct(len(erreur_fond), n),
        "validation_erronee": pct(len(valid_err), n),
        "eleve_a_trouve": pct(sum(r["juge"]["eleve_a_trouve"] == "oui" for r in trouve), len(trouve)),
        "vigilance_rappel": pct(sum(r["mesures"]["vigilance_alerte"] for r in vig_attendue), len(vig_attendue)),
        "vigilance_faux_positifs": pct(sum(r["mesures"]["vigilance_alerte"] for r in vig_pas), len(vig_pas)),
        "detection_notion": pct(sum(r["mesures"]["notion_ok"] for r in notion), len(notion)),
        "rapport_fidele": pct(sum(r["juge"]["rapport_fidele"] for r in rapport), len(rapport)),
        "note_globale": moyenne([x.get("note_globale") for x in j]),
        "guidage": moyenne([x.get("guidage") for x in j]),
        "adaptation": moyenne([x.get("adaptation") for x in j]),
        "ton": moyenne([x.get("ton") for x in j]),
        "fermete": moyenne([x.get("fermete") for x in j]),
        "securite": moyenne([x.get("securite") for x in j]),
        "respect_mode": moyenne([x.get("respect_mode") for x in j]),
        "programme": moyenne([x.get("programme") for x in j]),
        "attendus_specifiques": moyenne([x.get("attendus_specifiques") for x in j]),
        "phrases_moy": moyenne(phrases),
        "pct_msg_plus_6_phrases": round(sum(p > 6 for p in phrases) / len(phrases), 3) if phrases else None,
        "pct_msg_avec_question": moyenne([x["pct_msg_avec_question"] for x in m]),
        "pct_msg_plusieurs_questions": moyenne([x["pct_msg_plusieurs_questions"] for x in m]),
        "latence_p50_s": quantile(durees, 0.5),
        "latence_p95_s": quantile(durees, 0.95),
        "cout_moyen_conversation_usd": round(statistics.mean(couts), 4) if couts else None,
        "cout_par_echange_usd": round(statistics.mean(cout_par_tour), 5) if cout_par_tour else None,
        "cout_seance_20min_usd": round(statistics.mean(cout_par_tour) * 15, 3) if cout_par_tour else None,
        "part_cout_par_role": {
            k: f"{100 * v / total_roles:.0f} %" for k, v in sorted(roles.items(), key=lambda x: -x[1])
        },
        "appels_ia_par_echange": moyenne(appels_par_echange),
        "prompt_systeme_jules_car_moy": moyenne(jetons_sys),
    }


def par_groupe(lignes: list[dict[str, Any]], cle: str) -> dict[str, dict[str, Any]]:
    groupes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in lignes:
        if not r.get("erreur") and isinstance(r.get("juge"), dict) and "note_globale" in r["juge"]:
            groupes[r[cle]].append(r)
    return {
        g: {
            "n": len(rs),
            "note": moyenne([r["juge"]["note_globale"] for r in rs]),
            "fuites": sum(bool(r["juge"].get("fuite")) for r in rs),
            "a_la_place": sum(bool(r["juge"].get("fait_a_la_place")) for r in rs),
            "erreur_fond": sum(bool(r["juge"].get("erreur_de_fond")) for r in rs),
        }
        for g, rs in sorted(groupes.items())
    }


def variance_critiques(lignes: list[dict[str, Any]]) -> dict[str, Any]:
    groupes: dict[str, list[float]] = defaultdict(list)
    for r in lignes:
        if r.get("critique") and not r.get("erreur") and "note_globale" in (r.get("juge") or {}):
            groupes[r["id"]].append(r["juge"]["note_globale"])
    return {k: {"notes": v, "ecart": round(max(v) - min(v), 1)} for k, v in sorted(groupes.items()) if len(v) > 1}


def points_faibles(lignes: list[dict[str, Any]]) -> list[str]:
    return [
        f"[{r['id']}#{r['repetition']} note {r['juge'].get('note_globale')}] {p}"
        for r in lignes
        if isinstance(r.get("juge"), dict)
        for p in r["juge"].get("points_faibles") or []
    ]


def main() -> None:
    runs = sys.argv[1:]
    soc = socles()
    sortie: dict[str, Any] = {}
    md: list[str] = []
    for run in runs:
        donnees = charger(run)
        sortie[run] = {}
        md.append(f"# Tour {run}\n")
        for modele, lignes in donnees.items():
            s = stats_modele(lignes, soc)
            sortie[run][modele] = {
                "global": s,
                "par_eleve": par_groupe(lignes, "eleve"),
                "par_surface": par_groupe(lignes, "mode"),
                "par_matiere": par_groupe(lignes, "matiere"),
                "variance_critiques": variance_critiques(lignes),
                "points_faibles": points_faibles(lignes),
                "notes_par_scenario": {
                    f"{r['id']}#{r['repetition']}": (r.get("juge") or {}).get("note_globale") for r in lignes
                },
            }
            md.append(f"## {modele}\n")
            md += [f"- {k} : {v}" for k, v in s.items() if k != "erreurs_detail"]
            md.append("")
    dernier = runs[-1]
    (DOSSIER / "runs" / dernier / "analyse.json").write_text(
        json.dumps(sortie, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
    )
    (DOSSIER / "runs" / dernier / "ANALYSE.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
