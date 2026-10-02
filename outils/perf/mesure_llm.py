# ruff: noqa: E501, B007 - script de mesure ponctuel (prompts longs en dur)
"""Mesure des temps de reponse de Jules (chemin de production claude_cli), Haiku 4.5 vs Sonnet 5.5.

Config reelle (config.yaml + config.local.yaml), mais donnees dans un dossier jetable : rien n'est
ecrit dans donnees/ de l'eleve. Les modeles sont surcharges pour les trois roles (principal, rapide, redaction).
"""

from __future__ import annotations

import dataclasses
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from jules import sources as src  # noqa: E402
from jules.config import charger_config  # noqa: E402
from jules.llm.base import Tour  # noqa: E402
from jules.moteur import Tuteur  # noqa: E402

MODELES = sys.argv[1].split(",") if len(sys.argv) > 1 else ["claude-haiku-4-5", "claude-sonnet-5-5"]
N_APPELS = int(__import__("os").environ.get("N_APPELS", 5))
N_ECHANGES = int(__import__("os").environ.get("N_ECH", 3))
N_GEN = int(sys.argv[2]) if len(sys.argv) > 2 else 2

QUESTION = "j'ai un exo de maths sur le theoreme de Pythagore, je bloque : ABC est rectangle en A, AB = 6 cm et AC = 8 cm, je dois calculer BC"
COURS = """Le théorème de Pythagore

Dans un triangle rectangle, le carré de la longueur de l'hypoténuse est égal à la somme des carrés des longueurs des deux autres côtés.
L'hypoténuse est le côté opposé à l'angle droit, c'est le plus long côté du triangle.

Si ABC est rectangle en A, alors BC² = AB² + AC².

Exemple : ABC rectangle en A avec AB = 3 cm et AC = 4 cm.
BC² = AB² + AC² = 3² + 4² = 9 + 16 = 25 donc BC = 5 cm.

Réciproque : si dans un triangle le carré du plus grand côté est égal à la somme des carrés des deux autres côtés, alors ce triangle est rectangle.
Exemple : un triangle a pour côtés 5 cm, 12 cm et 13 cm. 13² = 169 et 5² + 12² = 25 + 144 = 169 donc le triangle est rectangle.

Méthode pour calculer une longueur : 1) je repère l'angle droit et l'hypoténuse ; 2) j'écris l'égalité de Pythagore ; 3) je remplace par les valeurs ; 4) je calcule ; 5) je prends la racine carrée et je donne l'unité.
Attention : pour un côté de l'angle droit, on soustrait : AB² = BC² - AC².
"""


def stats(v: list[float]) -> dict:
    return {
        "n": len(v),
        "mediane": round(statistics.median(v), 2),
        "min": round(min(v), 2),
        "max": round(max(v), 2),
        "valeurs": [round(x, 2) for x in v],
    }


def mesurer(modele: str) -> dict:
    base = charger_config()
    llm = dict(base.llm)
    llm["backend"] = "claude_cli"
    llm["modeles"] = {"principal": modele, "rapide": modele, "redaction": modele}
    with tempfile.TemporaryDirectory(prefix="jules_perf_") as tmp:
        config = dataclasses.replace(base, donnees=Path(tmp), llm=llm)
        tuteur = Tuteur(config)
        res: dict = {"modele": modele}
        try:
            # A. appel minimal
            t = []
            for _ in range(N_APPELS):
                d = time.perf_counter()
                tuteur.llm.repondre("Reponds par un seul mot.", [Tour("user", "Dis OK")], "principal")
                t.append(time.perf_counter() - d)
                print(f"[{modele}] minimal {t[-1]:.2f}s", flush=True)
            res["minimal"] = stats(t)

            # B. prompt systeme reel + question d'eleve (un seul appel, sans les modules)
            conv = tuteur.stockage.creer_conversation("aide-devoirs")
            tuteur.stockage.ajouter_message(
                conv.id, __import__("jules.stockage", fromlist=["Message"]).Message(role="eleve", texte=QUESTION)
            )
            conv = tuteur.stockage.conversation(conv.id)
            systeme = tuteur.systeme(conv)
            tours = [Tour("user", QUESTION)]
            res["taille_prompt_systeme_caracteres"] = len(systeme)
            t = []
            for _ in range(N_APPELS):
                d = time.perf_counter()
                rep = tuteur.llm.repondre(systeme, tours, "principal")
                t.append(time.perf_counter() - d)
                print(f"[{modele}] realiste {t[-1]:.2f}s ({len(rep)} car.)", flush=True)
            res["realiste"] = stats(t)
            res["exemple_reponse"] = rep[:400]

            # C. echange complet de bout en bout (detection de notion + reponse), puis modules de fond
            t_ech, t_fond = [], []
            for _ in range(N_ECHANGES):
                c = tuteur.stockage.creer_conversation("aide-devoirs")
                d = time.perf_counter()
                tuteur.echanger(c.id, QUESTION)
                t_ech.append(time.perf_counter() - d)
                d = time.perf_counter()
                tuteur.attendre_fond()
                t_fond.append(time.perf_counter() - d)
                print(f"[{modele}] echange complet {t_ech[-1]:.2f}s + fond {t_fond[-1]:.2f}s", flush=True)
            res["echange_complet_premier_message"] = stats(t_ech)
            res["fond_apres_reponse"] = stats(t_fond)

            # D. generation d'une fiche perso a partir d'un texte (parcours reel : notion + ecriture + controle)
            gen, etapes_ok = [], []
            module = tuteur.module("sources")
            for i in range(N_GEN):
                source = src.extraire(tuteur.stockage, [], None, COURS)
                d = time.perf_counter()
                fin = None
                for ligne in module.generer(source, "mathematiques"):
                    etape = json.loads(ligne)
                    if etape["etape"] in ("fin", "erreur"):
                        fin = etape
                gen.append(time.perf_counter() - d)
                etapes_ok.append(fin["etape"] if fin else "?")
                print(
                    f"[{modele}] generation fiche {gen[-1]:.1f}s -> {etapes_ok[-1]} {fin.get('message', '') if fin else ''}",
                    flush=True,
                )
            res["generation_fiche"] = stats(gen)
            res["generation_issue"] = etapes_ok
        finally:
            tuteur.fermer()
    return res


if __name__ == "__main__":
    sortie = []
    for m in MODELES:
        sortie.append(mesurer(m))
    chemin = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(tempfile.gettempdir()) / "mesure_llm.json"
    chemin.write_text(json.dumps(sortie, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ECRIT", chemin)
    print(json.dumps(sortie, ensure_ascii=False, indent=2))
