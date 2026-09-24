"""Module 'memoire' : ce que le bot sait du parcours de l'eleve.

Deux sources :
  - les analyses du module suivi (notions bloquees / comprises ces derniers jours) ;
  - les notes du parent (ex. "controle de maths vendredi sur les fractions"),
    saisies sur la page parent, avec une date de fin optionnelle.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jules.modules.base import Module
from jules.stockage import Conversation

ESPACE = "memoire"


class NoteEntree(BaseModel):
    texte: str
    jusqu_au: str | None = None  # AAAA-MM-JJ


def bilan_notions(evenements: list[dict[str, Any]], jours: int, aujourdhui: date) -> dict[str, list[str]]:
    """Derniere situation connue de chaque notion sur la periode (evenements du plus recent au plus ancien)."""
    limite = (aujourdhui - timedelta(days=jours)).isoformat()
    vus: dict[str, str] = {}
    for ev in evenements:
        if ev["horodatage"][:10] < limite:
            continue
        d = ev["donnees"]
        if d.get("statut") == "hors_scolaire" or not d.get("notion"):
            continue
        cle = f"{d.get('matiere', 'Autre')} : {d['notion']}"
        vus.setdefault(cle, d["statut"])
    return {
        "bloque": [n for n, s in vus.items() if s == "bloque"],
        "compris": [n for n, s in vus.items() if s == "compris"],
    }


def notes_valides(notes: list[dict[str, Any]], aujourdhui: date) -> list[dict[str, Any]]:
    return [n for n in notes if not n.get("jusqu_au") or n["jusqu_au"] >= aujourdhui.isoformat()]


class Brique(Module):
    id = "memoire"
    titre = "Ce que tu sais déjà de l'élève"

    def notes(self) -> list[dict[str, Any]]:
        return list(self.tuteur.stockage.lire_etat(ESPACE, "notes", []))

    def contribution(self, conv: Conversation) -> str | None:
        aujourdhui = datetime.now().astimezone().date()
        jours = int(self.reglages.get("jours", 21))
        bilan = bilan_notions(self.tuteur.stockage.evenements("suivi", limite=400), jours, aujourdhui)
        lignes = []
        for note in notes_valides(self.notes(), aujourdhui):
            echeance = f" (jusqu'au {note['jusqu_au']})" if note.get("jusqu_au") else ""
            lignes.append(f"- Info du parent{echeance} : {note['texte']}")
        if bilan["bloque"]:
            lignes.append("- Notions qui lui ont posé problème récemment : " + " ; ".join(bilan["bloque"][:8]))
        if bilan["compris"]:
            lignes.append("- Notions réussies récemment : " + " ; ".join(bilan["compris"][:8]))
        if not lignes:
            return None
        lignes.append(
            "Utilise ces infos avec tact : propose de revenir sur une notion difficile si l'occasion "
            "se présente, ne récite pas cette liste."
        )
        return "\n".join(lignes)

    def routes(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/notes")
        def lire() -> list[dict[str, Any]]:
            return self.notes()

        @routeur.post("/notes")
        def ajouter(note: NoteEntree) -> dict[str, Any]:
            texte = note.texte.strip()
            if not texte:
                raise HTTPException(400, "Note vide")
            entree = {"id": uuid.uuid4().hex[:8], "texte": texte[:500], "jusqu_au": note.jusqu_au or None}
            self.tuteur.stockage.ecrire_etat(ESPACE, "notes", [*self.notes(), entree])
            return entree

        @routeur.delete("/notes/{note_id}")
        def supprimer(note_id: str) -> dict[str, bool]:
            restantes = [n for n in self.notes() if n["id"] != note_id]
            self.tuteur.stockage.ecrire_etat(ESPACE, "notes", restantes)
            return {"ok": True}

        return routeur
