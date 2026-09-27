"""GABARIT d'un générateur de notion. Copie ce fichier sous `jules/generateurs/<matiere>/<notion>.py`,
remplace NOTION et les variantes, enregistre le module dans `jules/generateurs/__init__.py` (MODULES).
Le test générique `tests/test_generateurs.py` couvre alors ta notion sans une ligne de test à écrire.

Ce que le contrat exige (docs/GENERATEURS-CONTRAT.md, la version longue) :

  1. Tout est calculé à partir des valeurs tirées : la réponse vient du calcul, jamais d'une table.
  2. Aucune valeur n'est tirée avec le module `random` : uniquement le `rng` reçu.
  3. On construit avec `exercice_v2(...)` : il filtre les pièges et vérifie le contrat v2 avant de rendre.
  4. Un piège « diagnostic » n'utilise que les diagnostics du correcteur (DIAGNOSTICS[type]).
     Si le correcteur ne sait pas reconnaître une erreur, on l'ajoute AU CORRECTEUR (avec ses tests),
     pas dans le générateur.
  5. Un indice ne contient jamais la réponse, même sous une autre écriture (le vérificateur le voit).
  6. Ce module ne contient que ce qui est propre à la notion : une mise en forme ou un tirage
     réutilisable va dans `jules/generateurs/briques/`.

Ce gabarit est un module valide : `_exemple` fabrique un exercice de type « nombre ». Remplace-le.
"""

from __future__ import annotations

import random
from typing import Any

from jules.generateurs.briques import exercice_v2, generer_notion, palier, piege_diagnostic, piege_valeur

NOTION = "identifiant-exact-du-referentiel"  # bibliotheque/programme/<niveau>/<matiere>.yaml
VARIANTES = ("exemple",)

_PALIERS_EXEMPLE = {
    # difficulté : (plus petit facteur, plus grand facteur)
    1: (2, 9),
    2: (10, 30),
    3: (30, 99),
}


def _exemple(rng: random.Random, difficulte: int) -> dict[str, Any]:
    bas, haut = palier(_PALIERS_EXEMPLE, difficulte)
    a, b = rng.randint(bas, haut), rng.randint(bas, haut)
    produit = a * b
    return exercice_v2(
        id=f"exemple-{a}-{b}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Calcule {a} × {b}.",
        reponse={"valeur": produit, "forme": "entier"},
        indices={
            "relance": f"Que vaut {a} × 10 ? Et {a} × 1 ?",
            "methode": "Décompose un des deux facteurs en dizaines et unités, multiplie chaque partie, "
            "puis additionne.",
            "etape": f"{a} × {b} = {a} × {b // 10 * 10} + {a} × {b % 10}." if b >= 10 else f"Compte {b} fois {a}.",
        },
        pieges=[
            piege_valeur(a + b, "Tu as additionné les deux nombres. Ici, on les multiplie."),
            piege_diagnostic("valeur_fausse", "Refais le calcul en posant la multiplication."),
        ],
        solution=f"{a} × {b} = {produit}.",
        lieu=f"{NOTION}/exemple/{a}-{b}",
    )


_VARIANTES = {"exemple": _exemple}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
