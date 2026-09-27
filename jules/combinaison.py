"""Combinaison des amenagements et conflits (docs/spec/ADAPTATIONS-LOT2.md, §2 et §4, EX-104).

Le profil ne stocke que des identifiants d'amenagements (lot 1). `resoudre` part de ces identifiants et des
preferences du parent et donne la valeur de chaque levier selon sa regle de combinaison (§2) :

- `max` : la plus grande valeur ; pour un choix, la plus avancee dans l'ordre de la plage ;
- `min` : la plus petite valeur ;
- `ou` : vrai des qu'un amenagement le met a vrai ;
- `plus-restrictif` : la valeur la plus avancee dans la plage, ordonnee du moins au plus restrictif ;
- `arbitrage-parent` : la preference du parent, sinon la valeur neutre (aucun amenagement ne la regle).

Un levier qu'aucune source ne regle garde sa valeur neutre. Les preferences du parent hors PAP (§3) sont
`police`, `fond` et `lecture-vocale = automatique` ; une autre preference est ignoree et signalee, comme
un amenagement inconnu. La lecture automatique se combine par la regle du levier (`max`) : elle l'emporte
sur « proposee » venue d'un amenagement.

Les conflits du §4 sont renvoyes tels quels, sans rien trancher : les valeurs restent appliquees, le
parent voit un avertissement (EX-108).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from jules.amenagements import Amenagement, charger_amenagements
from jules.leviers import Levier, charger_leviers

journal = logging.getLogger("jules")

PARENT = "parent"  # origine d'une valeur venue d'une preference du parent
# Preferences hors PAP (§3) : levier -> valeurs que le parent peut choisir (None = toute la plage).
PREFERENCES_PARENT: dict[str, frozenset[Any] | None] = {
    "police": None,
    "fond": None,
    "lecture-vocale": frozenset({"automatique"}),
}

# Conflits du §4 : identifiants stables (repris par la page parent) et message affiche au parent.
CONFLIT_TAILLE_DENSITE = "taille-texte-et-densite"
CONFLIT_REPERES_DENSITE = "reperes-rang-chiffres-et-densite"
CONFLIT_SURLIGNAGE_DENSITE = "surlignage-mots-cles-et-densite"
CONFLIT_LECTURE_AUTOMATIQUE = "lecture-vocale-automatique"
MESSAGES_CONFLITS = {
    CONFLIT_TAILLE_DENSITE: "Texte agrandi et un exercice à la fois : peu de contenu visible à l'écran.",
    CONFLIT_REPERES_DENSITE: "Repères de couleur et un exercice à la fois : ajout d'information visuelle.",
    CONFLIT_SURLIGNAGE_DENSITE: "Mots-clés surlignés et un exercice à la fois : ajout d'information visuelle.",
    CONFLIT_LECTURE_AUTOMATIQUE: (
        "Lecture automatique : chaque réponse de Jules est lue à voix haute, "
        "ce qui peut gêner un élève en difficulté de compréhension orale."
    ),
}
DENSITE_REDUITE = "un-exercice"


@dataclass(frozen=True)
class Conflit:
    """Un conflit du §4 : les leviers en cause et le message pour le parent. Jamais tranche ici."""

    id: str
    leviers: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class Resolution:
    valeurs: dict[str, Any]  # chaque levier -> valeur retenue (neutre si aucune source)
    origines: dict[str, tuple[str, ...]]  # levier regle -> amenagements (et PARENT) qui le reglent
    conflits: tuple[Conflit, ...]
    inconnus: tuple[str, ...]  # identifiants d'amenagements ignores (aucun fichier sous adaptations/)
    preferences_ignorees: tuple[str, ...]  # leviers de preference refuses (hors §3 ou valeur hors plage)


def resoudre(
    ids: Iterable[str],
    preferences: Mapping[str, Any] | None = None,
    *,
    amenagements: Mapping[str, Amenagement] | None = None,
    leviers: Mapping[str, Levier] | None = None,
) -> Resolution:
    """Valeur de chaque levier pour les amenagements coches `ids` et les `preferences` du parent (EX-104)."""
    leviers = charger_leviers() if leviers is None else leviers
    amenagements = charger_amenagements(leviers=dict(leviers)) if amenagements is None else amenagements

    propositions: dict[str, list[tuple[str, Any]]] = {}
    inconnus: list[str] = []
    vus: set[str] = set()
    for ident in ids:
        if ident in vus:
            continue
        vus.add(ident)
        amenagement = amenagements.get(ident)
        if amenagement is None:
            inconnus.append(ident)
            continue
        for nom, valeur in amenagement.leviers.items():
            # Garde-fou (deja assure par le chargeur d'EX-103) : un amenagement ne regle jamais une
            # preference du parent ni la lecture automatique (§3, §4).
            if nom in ("police", "fond") or (nom == "lecture-vocale" and valeur == "automatique"):
                raise ValueError(f"{ident} : {nom} = {valeur!r} est reserve au choix du parent")
            propositions.setdefault(nom, []).append((ident, valeur))

    ignorees: list[str] = []
    for nom, valeur in (preferences or {}).items():
        permises = PREFERENCES_PARENT.get(nom, frozenset())
        levier = leviers.get(nom)
        if levier is None or (permises is not None and valeur not in permises) or not levier.dans_la_plage(valeur):
            ignorees.append(nom)
            continue
        propositions.setdefault(nom, []).append((PARENT, valeur))

    if inconnus:
        journal.warning("%d amenagement(s) inconnu(s) dans le profil, ignore(s) (voir adaptations/)", len(inconnus))
    if ignorees:
        journal.warning("%d preference(s) du parent ignoree(s) (hors §3 ou hors plage)", len(ignorees))

    valeurs = {nom: _combiner(levier, [v for _, v in propositions.get(nom, [])]) for nom, levier in leviers.items()}
    origines = {nom: tuple(o for o, _ in props) for nom, props in propositions.items() if nom in leviers}
    return Resolution(
        valeurs=valeurs,
        origines=origines,
        conflits=conflits(valeurs, leviers),
        inconnus=tuple(inconnus),
        preferences_ignorees=tuple(ignorees),
    )


def _combiner(levier: Levier, valeurs: list[Any]) -> Any:
    if not valeurs:
        return levier.neutre
    regle = levier.combinaison
    if regle == "ou":
        return any(valeurs)
    if regle == "arbitrage-parent":
        return valeurs[-1]  # seule source admise : la preference du parent
    if levier.type == "choix":  # max et plus-restrictif : rang dans la plage ordonnee
        rang = max if regle in ("max", "plus-restrictif") else min
        return levier.valeurs[rang(levier.valeurs.index(v) for v in valeurs)]
    if regle == "max":
        return max(valeurs)
    if regle == "min":
        return min(valeurs)
    raise ValueError(f"{levier.id} : regle {regle!r} non applicable a un {levier.type}")


def conflits(valeurs: Mapping[str, Any], leviers: Mapping[str, Levier]) -> tuple[Conflit, ...]:
    """Conflits du §4 presents dans `valeurs` (resultat de la combinaison)."""
    trouves: list[tuple[str, tuple[str, ...]]] = []
    densite_reduite = valeurs.get("densite") == DENSITE_REDUITE
    if densite_reduite and _taille_elevee(valeurs, leviers):
        trouves.append((CONFLIT_TAILLE_DENSITE, ("taille-texte", "densite")))
    if densite_reduite and valeurs.get("reperes-rang-chiffres") is True:
        trouves.append((CONFLIT_REPERES_DENSITE, ("reperes-rang-chiffres", "densite")))
    if densite_reduite and valeurs.get("surlignage-mots-cles") is True:
        trouves.append((CONFLIT_SURLIGNAGE_DENSITE, ("surlignage-mots-cles", "densite")))
    if valeurs.get("lecture-vocale") == "automatique":
        trouves.append((CONFLIT_LECTURE_AUTOMATIQUE, ("lecture-vocale",)))
    return tuple(Conflit(ident, leviers_en_cause, MESSAGES_CONFLITS[ident]) for ident, leviers_en_cause in trouves)


def _taille_elevee(valeurs: Mapping[str, Any], leviers: Mapping[str, Levier]) -> bool:
    """« Taille-texte elevee » (§4) : au-dessus de la valeur neutre. La spec ne fixe pas de seuil plus haut."""
    levier = leviers.get("taille-texte")
    taille = valeurs.get("taille-texte")
    return levier is not None and isinstance(taille, (int, float)) and taille > levier.neutre
