"""Registre des figures du depot, LU dans le depot plutot que recopie dans les tests.

Avant : chaque test tenait sa propre liste fermee de gabarits (DECLARATIONS_DU_DEPOT, FIGURES, GABARITS_DECLARES,
REVELENT). Chaque nouveau gabarit obligeait a modifier quatre tables, et dix branches paralleles se marchaient
dessus. Desormais les listes sont decouvertes :

- les declarations `discussion` sont lues en YAML brut dans `extensions/*/extension.yaml` (lecture independante de
  jules/extensions.py : les tests comparent les deux lectures) ;
- les figures actives viennent de la liste `extensions:` de `config.yaml` et de `fournit.figures` de chaque
  extension activee.

Les controles de fond restent dans les tests (noms lus par gabarit.js = noms declares, bornes coherentes, `revele`
booleen, aucune extension ecartee, chaque figure active declaree pour la discussion).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

RACINE = Path(__file__).resolve().parents[1]
EXTENSIONS = RACINE / "extensions"

# Valeurs qu'un gabarit lit SANS les declarer pour la discussion : curseurs que seule une fiche visuelle porte
# (souvent figes, min = max). Toute entree ici est une exception relue a la main, avec sa raison.
LUES_HORS_DISCUSSION: dict[str, set[str]] = {
    # frise generique : unite « mois » ou « souvenir » (age), second repere (intervalle, auteur), periode
    # surlignee (de, a / à) et « début » accentue ; voir extensions/frise/extension.yaml.
    "frise": {"début", "mois", "souvenir", "auteur", "intervalle", "de", "a", "à"},
}


def _manifeste(dossier: Path) -> dict[str, Any]:
    brut = yaml.safe_load((dossier / "extension.yaml").read_text(encoding="utf-8")) or {}
    assert isinstance(brut, dict), dossier.name
    return brut


def manifestes() -> dict[str, dict[str, Any]]:
    """Tous les manifestes du depot, actifs ou non : {id du dossier: YAML brut}."""
    return {d.name: _manifeste(d) for d in sorted(EXTENSIONS.iterdir()) if (d / "extension.yaml").is_file()}


def extensions_actives() -> list[str]:
    """La liste `extensions:` de config.yaml, dans l'ordre."""
    return list(yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))["extensions"])


def figures_actives() -> set[str]:
    """Les gabarits fournis (`fournit.figures`) par les extensions activees dans config.yaml."""
    tous = manifestes()
    return {f for i in extensions_actives() for f in ((tous[i].get("fournit") or {}).get("figures") or [])}


def declarations_brutes() -> dict[str, dict[str, Any]]:
    """{gabarit: declaration `discussion` brute} pour toutes les extensions du depot."""
    resultat: dict[str, dict[str, Any]] = {}
    for identifiant, manifeste in manifestes().items():
        for gabarit, declaration in (manifeste.get("discussion") or {}).items():
            assert gabarit not in resultat, f"{gabarit} declare deux fois ({identifiant})"
            resultat[gabarit] = declaration
    return resultat


def declarations_du_depot() -> dict[str, tuple[bool, dict[str, tuple[float, float, float, float]]]]:
    """{gabarit: (revele, {nom: (min, max, pas, defaut)})}, meme forme que l'ancienne table en dur."""
    return {
        gabarit: (
            d.get("revele", False),
            {nom: tuple(b[c] for c in ("min", "max", "pas", "defaut")) for nom, b in (d.get("valeurs") or {}).items()},
        )
        for gabarit, d in declarations_brutes().items()
    }


def valeurs_lues_par_le_gabarit(gabarit: str) -> set[str]:
    """Noms de valeurs que gabarit.js lit : `valeurs.<nom>`, `valeurs["<nom>"]` et `"<nom>" in valeurs`."""
    code = (EXTENSIONS / gabarit / "gabarit.js").read_text(encoding="utf-8")
    noms = set(re.findall(r"valeurs\.(\w+)", code))
    noms |= set(re.findall(r"valeurs\[\s*[\"']([^\"']+)[\"']\s*\]", code))
    noms |= set(re.findall(r"[\"']([^\"']+)[\"']\s+in\s+valeurs\b", code))
    return noms
