"""Commande `jules generateurs` : voir ce que fabrique un générateur, sans lancer le serveur.

jules generateurs                       liste les notions couvertes et leurs variantes
jules generateurs apercu NOTION [--graine N] [--difficulte 1|2|3] [--variante V] [--nombre K]
                                        affiche K exercices (énoncé, réponse, indices, pièges, solution)
jules generateurs eprouver [NOTION]     génère beaucoup d'exercices (toutes variantes, difficultés, graines)
                                        et rapporte les ErreurGeneration ; code de sortie 1 s'il y en a
"""

from __future__ import annotations

import itertools
import sys
from typing import Any

from jules.generateurs import MODULES
from jules.generateurs.briques import ErreurGeneration

GRAINES_EPREUVE = 300


def _options(args: list[str]) -> tuple[list[str], dict[str, str]]:
    positionnels: list[str] = []
    options: dict[str, str] = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            options[args[i][2:]] = args[i + 1]
            i += 2
        else:
            positionnels.append(args[i])
            i += 1
    return positionnels, options


def _afficher(ex: dict[str, Any]) -> str:
    lignes = [f"[{ex['id']}]  type={ex['type']}  difficulté={ex['difficulte']}", f"  Énoncé   : {ex['enonce']}"]
    rep = ex["reponse"]
    if ex["type"] == "choix":
        for o in rep["options"]:
            lignes.append(f"             {o['id']}) {o['texte']}")
        lignes.append(f"  Réponse  : {', '.join(rep['bonnes'])}")
    else:
        lignes.append(f"  Réponse  : {rep}")
    for palier_indice, texte in ex["indices"].items():
        lignes.append(f"  Indice {palier_indice:<8}: {texte}")
    for piege in ex["pieges"]:
        lignes.append(f"  Piège {piege['si']} -> {piege['relance']}")
    lignes.append(f"  Solution : {ex['solution']}")
    return "\n".join(lignes)


def lister() -> str:
    lignes = []
    for notion, module in sorted(MODULES.items()):
        lignes.append(f"{notion}: {', '.join(module.VARIANTES)}")
    return "\n".join(lignes) if lignes else "(aucun générateur)"


def apercu(notion: str, graine: int, difficulte: int, variante: str | None, nombre: int) -> str:
    module = MODULES[notion]
    blocs = []
    for k in range(nombre):
        ex = module.generer(graine + k, difficulte, variante)
        blocs.append(f"--- graine {graine + k} ---\n{_afficher(ex)}")
    return "\n\n".join(blocs)


def eprouver(notions: list[str], graines: int = GRAINES_EPREUVE) -> list[str]:
    """Les erreurs de génération rencontrées (« notion/variante/difficulté/graine : manquements »)."""
    erreurs: list[str] = []
    for notion in notions:
        module = MODULES[notion]
        for variante, difficulte, graine in itertools.product(module.VARIANTES, (1, 2, 3), range(graines)):
            try:
                module.generer(graine, difficulte, variante)
            except ErreurGeneration as err:
                erreurs.append(f"{notion}/{variante}/{difficulte}/{graine} : {err}")
    return erreurs


def main(args: list[str]) -> None:
    positionnels, options = _options(args)
    if not positionnels:
        print(lister())
        return
    commande = positionnels[0]
    if commande == "apercu" and len(positionnels) == 2:
        notion = positionnels[1]
        if notion not in MODULES:
            print(f"Pas de générateur pour {notion!r}. Notions couvertes :\n{lister()}")
            sys.exit(1)
        print(
            apercu(
                notion,
                int(options.get("graine", 0)),
                int(options.get("difficulte", 1)),
                options.get("variante"),
                int(options.get("nombre", 3)),
            )
        )
    elif commande == "eprouver":
        notions = positionnels[1:] or sorted(MODULES)
        inconnues = [n for n in notions if n not in MODULES]
        if inconnues:
            print(f"Pas de générateur pour : {', '.join(inconnues)}")
            sys.exit(1)
        erreurs = eprouver(notions)
        total = sum(len(MODULES[n].VARIANTES) * 3 * GRAINES_EPREUVE for n in notions)
        if erreurs:
            print("\n".join(erreurs))
            print(f"\n{len(erreurs)} exercice(s) non conforme(s) sur {total}.")
            sys.exit(1)
        print(f"{total} exercices générés, tous conformes au contrat v2 ({', '.join(notions)}).")
    else:
        print(__doc__)
