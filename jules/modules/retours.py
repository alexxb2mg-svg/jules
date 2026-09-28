"""Module 'retours' : le petit bouton « Un souci, une idée ? » présent sur chaque page.

L'eleve (ou le parent qui teste) signale un bug, un dysfonctionnement, une suggestion ou une idee
d'amelioration. Le signalement garde l'adresse exacte de la page (fragment compris : #/fiche/<id>...),
le titre de la page et la taille de l'ecran, pour qu'on puisse revoir la meme chose.

- Aucun appel au modele, aucun envoi hors de la machine : les retours restent dans la base locale
  (evenements 'retour'), exportes et effaces avec le dossier de l'eleve.
- L'eleve depose : POST /api/eleve/retours/deposer.
- Le parent les lit (GET /api/modules/retours/liste), les marque traites (PATCH /<id>) ou les supprime (DELETE /<id>).
- Ce n'est pas un canal vers Jules : un retour n'entre jamais dans une conversation ni dans le suivi.

Reglages (config.yaml) : aucun obligatoire.
  par_jour: 30   # garde-fou contre un clic en boucle
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from jules.modules.base import Module

ESPACE = "retours"
TYPES = ("bug", "dysfonctionnement", "suggestion", "amelioration")
TEXTE_MAX = 2000
ADRESSE_MAX = 500


class RetourEntree(BaseModel):
    type: Literal["bug", "dysfonctionnement", "suggestion", "amelioration"]
    texte: str = Field(min_length=3, max_length=TEXTE_MAX)
    adresse: str = Field(default="", max_length=ADRESSE_MAX)
    titre_page: str = Field(default="", max_length=200)
    ecran: str = Field(default="", max_length=40)


class EtatEntree(BaseModel):
    traite: bool


def _nettoyer_adresse(adresse: str) -> str:
    """Garde le chemin et le fragment (/app/#/fiche/x), jamais un hote externe ni un schema etrange."""
    a = adresse.strip()
    if "://" in a:
        a = a.split("://", 1)[1]
        a = a[a.find("/") :] if "/" in a else "/"
    return a if a.startswith("/") else "/" + a


class Brique(Module):
    id = "retours"
    titre = "Retours : bugs et suggestions"

    # --- stockage : une liste dans l'etat du module (petit volume, lu d'un bloc par le parent) -------
    def liste(self) -> list[dict[str, Any]]:
        return list(self.tuteur.stockage.lire_etat(ESPACE, "liste", []))

    def _ecrire(self, liste: list[dict[str, Any]]) -> None:
        self.tuteur.stockage.ecrire_etat(ESPACE, "liste", liste)

    def ajouter(self, entree: RetourEntree) -> dict[str, Any]:
        texte = entree.texte.strip()
        if len(texte) < 3:
            raise ValueError("Écris quelques mots pour qu'on comprenne.")
        maintenant = datetime.now().astimezone()
        liste = self.liste()
        du_jour = sum(1 for r in liste if r["cree_le"][:10] == maintenant.date().isoformat())
        if du_jour >= int(self.reglages.get("par_jour", 30)):
            raise PermissionError("Beaucoup de retours aujourd'hui : on en reparle demain.")
        retour = {
            "id": uuid.uuid4().hex[:10],
            "type": entree.type,
            "texte": texte,
            "adresse": _nettoyer_adresse(entree.adresse),
            "titre_page": entree.titre_page.strip(),
            "ecran": entree.ecran.strip(),
            "cree_le": maintenant.isoformat(timespec="seconds"),
            "traite": False,
        }
        self._ecrire([retour, *liste])
        return retour

    # --- routes eleve : deposer seulement (l'eleve ne relit pas la liste) -------------------------
    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.post("/deposer")
        def deposer(entree: RetourEntree) -> dict[str, Any]:
            try:
                r = self.ajouter(entree)
            except ValueError as err:
                raise HTTPException(400, str(err)) from err
            except PermissionError as err:
                raise HTTPException(429, str(err)) from err
            return {"id": r["id"], "ok": True}

        return routeur

    # --- routes parent : lire, marquer traite, supprimer --------------------------------------------
    def routes(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/liste")
        def lister(type: str | None = None, traite: bool | None = None) -> list[dict[str, Any]]:
            return [
                r for r in self.liste()
                if (type is None or r["type"] == type) and (traite is None or r["traite"] == traite)
            ]  # fmt: skip

        @routeur.patch("/{retour_id}")
        def marquer(retour_id: str, entree: EtatEntree) -> dict[str, Any]:
            liste = self.liste()
            for r in liste:
                if r["id"] == retour_id:
                    r["traite"] = entree.traite
                    self._ecrire(liste)
                    return r
            raise HTTPException(404, "Ce retour n'existe plus")

        @routeur.delete("/{retour_id}")
        def supprimer(retour_id: str) -> dict[str, bool]:
            liste = self.liste()
            reste = [r for r in liste if r["id"] != retour_id]
            if len(reste) == len(liste):
                raise HTTPException(404, "Ce retour n'existe plus")
            self._ecrire(reste)
            return {"ok": True}

        return routeur

    def infos_interface(self) -> dict[str, Any]:
        return {"retours": {"types": list(TYPES)}}
