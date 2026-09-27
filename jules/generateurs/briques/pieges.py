"""Construire les pièges d'un exercice et écarter ceux qui ne serviraient jamais.

Un piège = une erreur typique calculée par le générateur + la relance qui remet sur la voie.
Trois conditions existent dans le contrat v2 (docs/FICHES-V2.md) :

  piege_valeur(v, relance)       la réponse de l'élève vaut v            (nombre, expression, texte_court)
  piege_contient(ids, relance)   l'élève a coché ces options fausses     (choix)
  piege_diagnostic(d, relance)   le correcteur a rendu ce diagnostic     (d dans DIAGNOSTICS[type])

Règle apprise sur le premier générateur : selon les valeurs tirées, un piège « valeur » peut tomber
sur la bonne réponse, ou sur la valeur d'un piège précédent (qui l'intercepterait). Le vérificateur
refuse ces exercices. `filtrer_pieges` les écarte à la construction, ce qui évite à chaque notion
de recoder ces cas particuliers.
"""

from __future__ import annotations

from typing import Any

from jules.fiches.correction import DIAGNOSTICS, ILLISIBLE, corriger, piege_declenche

Piege = dict[str, Any]


def piege_valeur(valeur: Any, relance: str) -> Piege:
    return {"si": {"valeur": valeur}, "relance": relance}


def piege_contient(options: list[str], relance: str) -> Piege:
    return {"si": {"contient": list(options)}, "relance": relance}


def piege_diagnostic(diagnostic: str, relance: str) -> Piege:
    return {"si": {"diagnostic": diagnostic}, "relance": relance}


def diagnostic_permis(type_exercice: str, diagnostic: str) -> bool:
    """Un générateur n'invente jamais un diagnostic : il n'utilise que ceux du correcteur."""
    return diagnostic in DIAGNOSTICS.get(type_exercice, ())


def filtrer_pieges(exercice: dict[str, Any], candidats: list[Piege]) -> list[Piege]:
    """Les pièges qui se déclencheraient vraiment, dans l'ordre donné.

    Écartés : un piège « valeur » dont la valeur est jugée juste, illisible, ou déjà interceptée par
    un piège gardé avant lui. Les pièges « contient » et « diagnostic » sont gardés tels quels (le
    vérificateur contrôle leur forme). `exercice` doit déjà porter `type` et `reponse`.
    """
    gardes: list[Piege] = []
    for piege in candidats:
        condition = piege["si"]
        if "valeur" in condition:
            verdict = corriger(exercice, condition["valeur"])
            if verdict.juste or verdict.diagnostic == ILLISIBLE:
                continue
            essai = {**exercice, "pieges": [*gardes, piege]}
            if piege_declenche(essai, condition["valeur"], verdict) != piege:
                continue
        gardes.append(piege)
    return gardes
