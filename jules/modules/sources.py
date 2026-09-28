"""Module 'sources' : la bibliotheque personnelle de l'eleve (docs/SOURCES-CONTRAT.md).

L'eleve apporte un document (photos, PDF, texte colle) ; Jules en fait une fiche visuelle au format des
fiches natives, proposee dans la notion qu'il reconnait, et l'eleve decide de la garder et ou la ranger.

Routes eleve (/api/eleve/sources) :
  POST   /deposer                        multipart photos[] | pdf | texte, matiere? -> etapes en flux (NDJSON)
  GET    /fiches?filtre=toutes|perso     index de la bibliotheque personnelle + dossiers
  GET    /fiches/<id>                    une fiche (meme forme que /fiches_visuelles/notions/<id>)
  POST   /fiches/<id>/ranger             {mode: notion|dossier|non_classe, dossier?}
  PATCH  /fiches/<id>                    {titre}
  DELETE /fiches/<id>                    fiche et source supprimees (« ne pas garder »)
  POST   /fiches/<id>/regenerer          nouvelle fiche depuis la meme source, etapes en flux
  GET    /a_ranger                       fiches en attente de reponse a « on la garde ? »
  GET/POST /dossiers, PATCH/DELETE /dossiers/<id>
Routes parent (/api/modules/sources) : liste des fiches personnelles, suppression.

Reglages (config.yaml) : generations_par_jour (10 par defaut, contrat Q8).
Une fiche personnelle n'est jamais un `suivi` de notion : elle ne dit rien de ce que l'eleve sait.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import date
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from jules import sources as src
from jules.extensions import figures_fournies
from jules.fiches_visuelles import ErreurFicheVisuelle, lire_fiche_personnelle
from jules.modules.base import Module
from jules.modules.notions import niveau_du_profil

journal = logging.getLogger("jules.sources_module")

EVENEMENT_GENERATION = "sources.generation"
EVENEMENT_SUPPRESSION = "sources.suppression"


class Rangement(BaseModel):
    mode: str = Field(pattern="^(notion|dossier|non_classe)$")
    dossier: str | None = Field(default=None, max_length=20)


class Titre(BaseModel):
    titre: str = Field(max_length=200)


class NomDossier(BaseModel):
    nom: str = Field(max_length=200)


class Brique(Module):
    id = "sources"
    titre = "Mes fiches perso"

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self.quota = int(reglages.get("generations_par_jour", 10))

    # --- contexte ------------------------------------------------------------------
    @property
    def catalogue(self) -> Any:
        module: Any = self.tuteur.module("notions")
        if module is None:
            raise RuntimeError("Le module 'sources' necessite le module 'notions'")
        return module.catalogue

    def matieres(self) -> dict[str, str]:
        return {mid: nom for mid, nom, _n in self.catalogue.matieres()}

    def niveau(self) -> str:
        return niveau_du_profil(self.tuteur.profil().classe) or ""

    def gabarits(self) -> frozenset[str]:
        return frozenset(figures_fournies(self.tuteur.extensions))

    @property
    def bibliotheque(self) -> src.Bibliotheque:
        return src.Bibliotheque(self.tuteur.stockage)

    def generations_du_jour(self) -> int:
        return len(self.tuteur.stockage.evenements(EVENEMENT_GENERATION, jour=date.today().isoformat()))

    def infos_interface(self) -> dict[str, Any]:
        return {"sources": True}

    # --- lecture d'une fiche --------------------------------------------------------
    def fiche(self, fiche_id: str) -> dict[str, Any]:
        entree = self.bibliotheque.entree(fiche_id)
        brut = self.bibliotheque.brut(fiche_id)
        # Relue par le validateur a chaque ouverture (comme une fiche native au chargement) :
        # une fiche stockee qui ne passerait plus le controle n'est jamais servie.
        fiche = lire_fiche_personnelle(
            brut, self.catalogue.notions, self.matieres(), self.niveau(), entree["source"], self.gabarits()
        )
        publique = fiche.publique([])
        matiere = fiche.matiere or ""
        publique.update(
            {
                "id": fiche_id,
                "titre": entree.get("titre") or fiche.titre,
                "licence": fiche.licence,
                "nom_matiere": self.matieres().get(matiere, "Mon document"),
                "relecture_a_relire": False,  # l'avertissement « pas encore relue » vise les fiches natives
                "rangement": {k: entree.get(k) for k in ("etat", "notion", "dossier", "suggestion", "cree_le")},
                "source": entree.get("source"),
            }
        )
        return publique

    def liste(self) -> dict[str, Any]:
        matieres = self.matieres()
        fiches = []
        for e in sorted(self.bibliotheque.index().values(), key=lambda e: e.get("cree_le") or "", reverse=True):
            notion = self.catalogue.notion(e.get("notion") or "")
            fiches.append(
                {
                    **e,
                    "titre_notion": notion.titre if notion else None,
                    "chapitre": notion.chapitre if notion else None,
                    "nom_matiere": matieres.get(e.get("matiere") or "", None),
                }
            )
        return {
            "fiches": fiches,
            "dossiers": self.bibliotheque.dossiers(),
            "quota": {"par_jour": self.quota, "utilisees": self.generations_du_jour()},
        }

    # --- generation -------------------------------------------------------------------
    def generer(self, source: src.Source, matiere: str | None, retirer_fichiers: bool = True) -> Iterator[bytes]:
        self.tuteur.stockage.ajouter_evenement(EVENEMENT_GENERATION, {"source": source.id, "type": source.type})
        for etape in src.parcours(
            self.tuteur.llm,
            self.tuteur.stockage,
            self.tuteur.config.dossiers_bibliotheques,
            self.catalogue.notions,
            self.matieres(),
            self.niveau(),
            self.gabarits(),
            source,
            matiere if matiere in self.matieres() else None,
            retirer_fichiers,
        ):
            if etape["etape"] == "erreur":
                journal.info("Source %s : %s", source.id, etape["message"])
            yield (json.dumps(etape, ensure_ascii=False) + "\n").encode("utf-8")

    def verifier_quota(self) -> None:
        if self.generations_du_jour() >= self.quota:
            raise HTTPException(429, f"Tu as déjà fait {self.quota} fiches aujourd'hui : on reprend demain.")

    # --- routes eleve --------------------------------------------------------------------
    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        def introuvable() -> HTTPException:
            return HTTPException(404, "Cette fiche n'existe plus")

        @routeur.post("/deposer")
        async def deposer(
            photos: list[UploadFile] | None = File(None),  # noqa: B008 - idiome FastAPI
            pdf: UploadFile | None = File(None),  # noqa: B008
            texte: str = Form(""),
            matiere: str = Form(""),
        ) -> StreamingResponse:
            self.verifier_quota()
            contenus = []
            for photo in photos or []:
                contenus.append(await photo.read(src.PHOTO_MAX_OCTETS + 1))
            contenu_pdf = await pdf.read(src.PDF_MAX_OCTETS + 1) if pdf is not None else None
            try:
                source = src.extraire(self.tuteur.stockage, contenus, contenu_pdf, texte)
            except src.ErreurSource as err:
                raise HTTPException(400, str(err)) from err
            return StreamingResponse(self.generer(source, matiere or None), media_type="application/x-ndjson")

        @routeur.get("/fiches")
        def liste_route(filtre: str = "toutes") -> dict[str, Any]:
            return self.liste()

        @routeur.get("/fiches/{fiche_id}")
        def fiche_route(fiche_id: str) -> dict[str, Any]:
            try:
                return self.fiche(fiche_id)
            except KeyError as err:
                raise introuvable() from err
            except ErreurFicheVisuelle as err:
                journal.error("Fiche personnelle %s non servie : %s", fiche_id, err)
                raise HTTPException(409, "Cette fiche est abîmée : supprime-la et refais-la.") from err

        @routeur.post("/fiches/{fiche_id}/ranger")
        def ranger_route(fiche_id: str, entree: Rangement) -> dict[str, Any]:
            try:
                return self.bibliotheque.ranger(fiche_id, entree.mode, entree.dossier)
            except KeyError as err:
                raise introuvable() from err
            except src.ErreurSource as err:
                raise HTTPException(400, str(err)) from err

        @routeur.patch("/fiches/{fiche_id}")
        def renommer_route(fiche_id: str, entree: Titre) -> dict[str, Any]:
            try:
                return self.bibliotheque.renommer(fiche_id, entree.titre)
            except KeyError as err:
                raise introuvable() from err
            except src.ErreurSource as err:
                raise HTTPException(400, str(err)) from err

        @routeur.delete("/fiches/{fiche_id}")
        def supprimer_route(fiche_id: str) -> dict[str, bool]:
            try:
                self.bibliotheque.supprimer(fiche_id)
            except KeyError as err:
                raise introuvable() from err
            return {"ok": True}

        @routeur.post("/fiches/{fiche_id}/regenerer")
        def regenerer_route(fiche_id: str) -> StreamingResponse:
            try:
                entree = self.bibliotheque.entree(fiche_id)
            except KeyError as err:
                raise introuvable() from err
            self.verifier_quota()
            resume = entree.get("source") or {}
            texte = self.tuteur.stockage.lire_etat(src.ESPACE, f"texte:{resume.get('id')}", "") or ""
            images = [
                p
                for p in (self.tuteur.stockage.chemin_image(n) for n in resume.get("fichiers") or [])
                if p is not None and p.suffix.lower() != ".pdf"
            ]
            source = src.Source(
                id=str(resume.get("id")), type=str(resume.get("type")), titre=str(resume.get("titre")),
                texte=texte, images=images, fichiers=list(resume.get("fichiers") or []),
            )  # fmt: skip
            # Meme source pour les deux fiches : ses fichiers ne partent qu'avec la derniere (Bibliotheque.supprimer).
            return StreamingResponse(
                self.generer(source, entree.get("matiere"), retirer_fichiers=False), media_type="application/x-ndjson"
            )

        @routeur.get("/a_ranger")
        def a_ranger_route() -> list[dict[str, Any]]:
            return self.bibliotheque.a_ranger()

        @routeur.get("/dossiers")
        def dossiers_route() -> list[dict[str, str]]:
            return self.bibliotheque.dossiers()

        @routeur.post("/dossiers")
        def creer_dossier_route(entree: NomDossier) -> dict[str, str]:
            try:
                return self.bibliotheque.creer_dossier(entree.nom)
            except src.ErreurSource as err:
                raise HTTPException(400, str(err)) from err

        @routeur.patch("/dossiers/{dossier_id}")
        def renommer_dossier_route(dossier_id: str, entree: NomDossier) -> dict[str, str]:
            try:
                return self.bibliotheque.renommer_dossier(dossier_id, entree.nom)
            except KeyError as err:
                raise HTTPException(404, "Ce dossier n'existe plus") from err
            except src.ErreurSource as err:
                raise HTTPException(400, str(err)) from err

        @routeur.delete("/dossiers/{dossier_id}")
        def supprimer_dossier_route(dossier_id: str) -> dict[str, int]:
            try:
                return {"deplacees": self.bibliotheque.supprimer_dossier(dossier_id)}
            except KeyError as err:
                raise HTTPException(404, "Ce dossier n'existe plus") from err

        return routeur

    # --- routes parent (regle 3 : le parent voit et peut supprimer) --------------------------
    def routes(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/fiches")
        def liste_parent() -> list[dict[str, Any]]:
            # Une fiche pas encore rangee n'a pas de notion : le parent voit alors la notion suggeree.
            return [
                {
                    **{k: f.get(k) for k in ("id", "titre", "nom_matiere", "etat", "cree_le")},
                    "titre_notion": f.get("titre_notion") or (f.get("suggestion") or {}).get("titre_notion"),
                }
                for f in self.liste()["fiches"]
            ]

        @routeur.delete("/fiches/{fiche_id}")
        def supprimer_parent(fiche_id: str) -> dict[str, bool]:
            try:
                entree = self.bibliotheque.supprimer(fiche_id)
            except KeyError as err:
                raise HTTPException(404, "Cette fiche n'existe plus") from err
            self.tuteur.stockage.ajouter_evenement(
                EVENEMENT_SUPPRESSION, {"titre": entree.get("titre"), "par": "parent"}
            )
            return {"ok": True}

        return routeur
