"""Module 'synchro' : l'etat de l'interface suit l'eleve d'un appareil a l'autre.

Avant ce module, la progression (« fiche lue, lecon, entrainement »), la matiere choisie, le filtre des
fiches et les fiches ouvertes recemment vivaient seulement dans le localStorage du navigateur : telephone,
PC et tunnel sont autant d'origines differentes, donc autant de memoires separees (retour d'Ellie du
02/10/2026 : « ce que j'ai enregistre sur mon telephone n'est pas synchronise avec mon pc »).

- GET /api/eleve/synchro/etat : l'etat connu du serveur, {cle: valeur} (seulement les cles deja ecrites).
- PUT /api/eleve/synchro/{cle} : {"valeur": ...} ; renvoie la valeur retenue par le serveur.
- Aucun appel au modele, rien ne sort de la machine. Le navigateur garde son localStorage (affichage
  immediat, hors ligne) ; le serveur est la source commune.
- Cles acceptees : liste blanche, valeur de forme verifiee et de taille bornee.
- « etapes » se FUSIONNE (union par notion) : une etape faite sur un appareil n'est jamais effacee
  par un autre appareil qui ne la connaissait pas encore. Les autres cles : derniere ecriture gagnante.

Reglages (config.yaml) : aucun.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jules.modules.base import Module

ESPACE = "synchro"
TAILLE_MAX = 20_000  # octets de JSON par cle : garde-fou, l'etat reel est de quelques centaines d'octets
ETAPES_VALIDES = ("fiche", "lecon", "exercices")
GENRES_RECENTE = ("native", "perso")


def _chaine(v: Any) -> bool:
    return isinstance(v, str) and len(v) <= 200


def _verifier_matiere(v: Any) -> Any:
    if v is not None and not _chaine(v):
        raise ValueError("matiere : texte court ou null")
    return v


def _verifier_filtre(v: Any) -> Any:
    if v not in ("toutes", "natives", "perso"):
        raise ValueError("filtre_fiches : valeur inconnue")
    return v


def _verifier_etapes(v: Any) -> dict[str, list[str]]:
    if not isinstance(v, dict):
        raise ValueError("etapes : objet {notion: [etapes]}")
    propre: dict[str, list[str]] = {}
    for notion, liste in v.items():
        if not _chaine(notion) or not isinstance(liste, list):
            raise ValueError("etapes : forme invalide")
        propre[notion] = [e for e in ETAPES_VALIDES if e in liste]
    return propre


def _verifier_recentes(v: Any) -> list[dict[str, str]]:
    if not isinstance(v, list) or len(v) > 6:
        raise ValueError("fiches_recentes : 6 elements au plus")
    propre = []
    for r in v:
        if not isinstance(r, dict) or r.get("genre") not in GENRES_RECENTE:
            raise ValueError("fiches_recentes : forme invalide")
        if not all(_chaine(r.get(k)) for k in ("id", "titre", "matiere")):
            raise ValueError("fiches_recentes : forme invalide")
        propre.append({k: r[k] for k in ("genre", "id", "titre", "matiere")})
    return propre


# cle -> (verificateur, valeur par defaut)
CLES: dict[str, tuple[Any, Any]] = {
    "matiere": (_verifier_matiere, None),
    "filtre_fiches": (_verifier_filtre, "toutes"),
    "etapes": (_verifier_etapes, {}),
    "fiches_recentes": (_verifier_recentes, []),
}


def fusionner_etapes(a: dict[str, list[str]], b: dict[str, list[str]]) -> dict[str, list[str]]:
    """Union par notion, dans l'ordre fiche, lecon, exercices."""
    out: dict[str, list[str]] = {}
    for notion in {*a, *b}:
        vues = {*a.get(notion, []), *b.get(notion, [])}
        out[notion] = [e for e in ETAPES_VALIDES if e in vues]
    return out


class ValeurEntree(BaseModel):
    valeur: Any = None


class Brique(Module):
    id = "synchro"
    titre = "Synchronisation de l'etat entre appareils"

    def lire(self, cle: str) -> Any:
        return self.tuteur.stockage.lire_etat(ESPACE, cle, CLES[cle][1])

    def tout(self) -> dict[str, Any]:
        """Seulement les cles deja ecrites : le client distingue « jamais choisi » de « choisi : rien »."""
        absent = object()
        etat = {cle: self.tuteur.stockage.lire_etat(ESPACE, cle, absent) for cle in CLES}
        return {cle: v for cle, v in etat.items() if v is not absent}

    def ecrire(self, cle: str, valeur: Any) -> Any:
        verifier = CLES[cle][0]
        try:
            propre = verifier(valeur)
        except ValueError as err:
            raise HTTPException(422, str(err)) from err
        if cle == "etapes":
            propre = fusionner_etapes(self.lire("etapes"), propre)
        if len(json.dumps(propre, ensure_ascii=False)) > TAILLE_MAX:
            raise HTTPException(413, "Etat trop volumineux")
        self.tuteur.stockage.ecrire_etat(ESPACE, cle, propre)
        return propre

    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/etat")
        def lire_tout() -> dict[str, Any]:
            return self.tout()

        @routeur.put("/{cle}")
        def ecrire(cle: str, entree: ValeurEntree) -> dict[str, Any]:
            if cle not in CLES:
                raise HTTPException(404, "Cle inconnue")
            return {"valeur": self.ecrire(cle, entree.valeur)}

        return routeur
