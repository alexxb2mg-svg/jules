"""Module 'fiches_visuelles' : sert les fiches visuelles a l'ecran d'accueil « Mes fiches ».

Rendu 100% deterministe (cadrage interface, 25/09/2026) : ce module ne fait AUCUN appel au
modele d'IA. Il lit les fiches (jules/fiches_visuelles.py), verifie que chaque notion existe
dans le referentiel de programme (module 'notions'), et expose :
  - la liste des notions du niveau qui ont une fiche visuelle (pour construire le rail) ;
  - le contenu complet d'une fiche, avec ses attendus officiels rattaches automatiquement.

Reglages (config.yaml) :
  bibliotheques: [fiches-visuelles-3e-experimentales]   # bibliotheques de type 'fiches-visuelles'
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from jules.extensions import figures_fournies
from jules.fiches_visuelles import FicheVisuelle, charger_fiches_visuelles
from jules.modules.base import Module

journal = logging.getLogger("jules.fiches_visuelles_module")


class Brique(Module):
    id = "fiches_visuelles"
    titre = "Mes fiches"

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self.ids = [str(i) for i in reglages.get("bibliotheques") or []]
        self._fiches: dict[str, FicheVisuelle] | None = None

    # --- catalogue -------------------------------------------------------------
    @property
    def notions_module(self) -> Any:
        module = self.tuteur.module("notions")
        if module is None:
            raise RuntimeError("Le module 'fiches_visuelles' necessite le module 'notions'")
        return module

    @property
    def fiches(self) -> dict[str, FicheVisuelle]:
        """Fiches chargees (une bibliotheque absente ou vide : le module demarre sans fiche)."""
        if self._fiches is None:
            catalogue = self.notions_module.catalogue
            self._fiches = charger_fiches_visuelles(
                self.tuteur.config.dossiers_bibliotheques,
                self.ids,
                catalogue.notions,
                frozenset(figures_fournies(self.tuteur.extensions)),
            )
        return self._fiches

    def recharger(self) -> None:
        self._fiches = None

    # --- interface ---------------------------------------------------------------
    def infos_interface(self) -> dict[str, Any]:
        """Signale a la page eleve qu'un lien 'Mes fiches' doit s'afficher (voir eleve.js)."""
        return {"fiches_visuelles": bool(self.fiches)}

    # --- liste par matiere ---------------------------------------------------------
    def liste(self) -> dict[str, Any]:
        catalogue = self.notions_module.catalogue
        matieres = []
        for mid, nom, notions in catalogue.matieres():
            avec_fiche = [n for n in notions if n.id in self.fiches]
            if not avec_fiche:
                continue
            matieres.append(
                {
                    "id": mid,
                    "nom": nom,
                    "notions": [{"id": n.id, "titre": n.titre, "chapitre": n.chapitre} for n in avec_fiche],
                }
            )
        return {"matieres": matieres}

    # --- une fiche -----------------------------------------------------------------
    def fiche(self, notion_id: str) -> dict[str, Any]:
        fiche = self.fiches.get(notion_id)
        if fiche is None:
            raise KeyError(notion_id)
        notion = self.notions_module.catalogue.notion(notion_id)
        attendus = notion.attendus if notion else []
        publique = fiche.publique(attendus)
        publique["licence"] = fiche.licence
        publique["nom_matiere"] = notion.nom_matiere if notion else fiche.matiere
        publique["relecture_a_relire"] = fiche.relecture == "a_relire"
        return publique

    # --- routes eleve ---------------------------------------------------------------
    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/notions")
        def liste_route() -> dict[str, Any]:
            return self.liste()

        @routeur.get("/notions/{notion_id}/rappels")
        def rappels_route(notion_id: str) -> dict[str, Any]:
            # Pour toutes les pages (discussion, studio, cours) : ce qui est propre a la notion (sens
            # des lettres, abreviations), rappele au survol par symboles.js. Sans fiche : rien.
            fiche = self.fiches.get(notion_id)
            if fiche is None:
                return {"variables": {}, "abreviations": {}}
            return {"variables": fiche.toutes_les_variables(), "abreviations": dict(fiche.abreviations)}

        @routeur.get("/notions/{notion_id}")
        def fiche_route(notion_id: str) -> dict[str, Any]:
            try:
                return self.fiche(notion_id)
            except KeyError as err:
                raise HTTPException(404, "Aucune fiche visuelle pour cette notion") from err

        return routeur
