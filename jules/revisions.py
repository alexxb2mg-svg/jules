"""Repetition espacee des cartes memoire du studio (docs/STUDIO-CONTRAT.md §4).

Algorithme volontairement simple : des paliers fixes, pas de facteur de difficulte ajuste
carte par carte comme SM-2 (voir docs/VISION.md, "Ce que Jules ne fait pas encore").

Module separe, sans stockage : toutes les fonctions sont pures et ne lisent jamais la date
systeme (`aujourdhui` est toujours passe en parametre par l'appelant, `jules/modules/studio.py`
pour ce projet). Une carte est un simple dict (forme decrite dans docs/STUDIO-CONTRAT.md §1) :

    {id, recto, verso, etat, prochaine_revision, palier}

`etat` est l'un de `ETATS_CARTE`, `prochaine_revision` une date ISO (AAAA-MM-JJ) ou `None`,
`palier` un index dans `PALIERS_JOURS`. Aucune fonction ici ne modifie une carte en place :
chacune retourne une copie.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

PALIERS_JOURS: tuple[int, ...] = (1, 3, 7, 15, 30, 60)
ETATS_CARTE: tuple[str, ...] = ("nouvelle", "apprentissage", "acquise")
REPONSES_CARTE: tuple[str, ...] = ("facile", "difficile", "rate")

_DERNIER_PALIER = len(PALIERS_JOURS) - 1


def prochaine_revision(carte: dict[str, Any], reponse: str, aujourdhui: date) -> dict[str, Any]:
    """Retourne une copie de `carte` reprogrammee selon `reponse` (facile, difficile, rate).

    - "rate" : palier remis a 0, etat "apprentissage", revision demain ;
    - "difficile" : palier inchange, etat "apprentissage", revision au meme delai que le
      palier actuel ;
    - "facile" : palier augmente de un (plafonne au dernier palier), etat "acquise" si le
      palier atteint est le dernier, sinon "apprentissage", revision au delai du nouveau
      palier.

    Leve `ValueError` si `reponse` n'est pas dans `REPONSES_CARTE`.
    """
    if reponse not in REPONSES_CARTE:
        raise ValueError(f"reponse de carte inconnue : {reponse!r} (attendu l'une de : {', '.join(REPONSES_CARTE)})")

    resultat = dict(carte)
    palier_actuel = int(carte.get("palier") or 0)

    if reponse == "rate":
        resultat["palier"] = 0
        resultat["etat"] = "apprentissage"
        resultat["prochaine_revision"] = (aujourdhui + timedelta(days=1)).isoformat()
    elif reponse == "difficile":
        resultat["palier"] = palier_actuel
        resultat["etat"] = "apprentissage"
        resultat["prochaine_revision"] = (aujourdhui + timedelta(days=PALIERS_JOURS[palier_actuel])).isoformat()
    else:  # "facile"
        nouveau_palier = min(palier_actuel + 1, _DERNIER_PALIER)
        resultat["palier"] = nouveau_palier
        resultat["etat"] = "acquise" if nouveau_palier == _DERNIER_PALIER else "apprentissage"
        resultat["prochaine_revision"] = (aujourdhui + timedelta(days=PALIERS_JOURS[nouveau_palier])).isoformat()

    return resultat


def cartes_dues(cartes: list[dict[str, Any]], aujourdhui: date) -> list[dict[str, Any]]:
    """Retourne les cartes dont `prochaine_revision <= aujourdhui`, copiees et triees.

    Les cartes "nouvelle" (jamais encore revisees) arrivent en premier ; les autres suivent,
    triees par `prochaine_revision` croissante. Une carte sans `prochaine_revision` (jamais
    programmee) est consideree due, defensivement.
    """

    def est_due(carte: dict[str, Any]) -> bool:
        valeur = carte.get("prochaine_revision")
        if valeur is None:
            return True
        return date.fromisoformat(valeur) <= aujourdhui

    def cle_tri(carte: dict[str, Any]) -> tuple[int, str]:
        nouvelle = carte.get("etat") == "nouvelle"
        return (0 if nouvelle else 1, carte.get("prochaine_revision") or "")

    dues = [dict(carte) for carte in cartes if est_due(carte)]
    dues.sort(key=cle_tri)
    return dues


def reinitialiser(carte: dict[str, Any]) -> dict[str, Any]:
    """Retourne une copie de `carte` remise a zero (dévalidation du support, §3 du contrat)."""
    resultat = dict(carte)
    resultat["prochaine_revision"] = None
    resultat["palier"] = 0
    resultat["etat"] = "nouvelle"
    return resultat
