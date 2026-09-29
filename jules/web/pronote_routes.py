"""Routes API Pronote pour l'application Jules.

Monte sous /api/pronote — protégé par l'accès élève (code élève, y compris à distance).
Aucune donnée personnelle dans ce fichier (publiable sur GitHub).
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from jules.pronote import PronoteClient, from_config

log = logging.getLogger("jules.pronote.routes")


def routes_pronote(config_brute: dict[str, Any]) -> APIRouter | None:
    """Crée le routeur Pronote si la section `pronote:` existe dans la config.

    Retourne None si pas de config Pronote.
    """
    client = from_config(config_brute)
    if client is None:
        return None

    routeur = APIRouter()

    def _client() -> PronoteClient:
        if not client.connected:
            ok = client.connect()
            if not ok:
                raise HTTPException(503, "Impossible de se connecter à Pronote")
        return client

    @routeur.get("/status")
    def status() -> dict[str, Any]:
        """État de la connexion et infos de l'élève."""
        try:
            c = _client()
            return c.info()
        except HTTPException:
            return {"connected": False, "error": "Connexion impossible"}

    @routeur.get("/timetable")
    def timetable(
        date: str | None = Query(None, description="Date de début YYYY-MM-DD"),
        weeks: int = Query(1, ge=1, le=4),
    ) -> list[dict[str, Any]]:
        """Emploi du temps (EDT)."""
        c = _client()
        d = datetime.date.fromisoformat(date) if date else None
        return c.timetable(date=d, weeks=weeks)

    @routeur.get("/homework")
    def homework(
        date_from: str | None = Query(None, description="À partir de YYYY-MM-DD"),
    ) -> list[dict[str, Any]]:
        """Travail à faire."""
        c = _client()
        d = datetime.date.fromisoformat(date_from) if date_from else None
        return c.homework(date_from=d)

    @routeur.get("/grades")
    def grades(
        period: str | None = Query(None, description="Nom de la période"),
    ) -> list[dict[str, Any]]:
        """Notes."""
        c = _client()
        return c.grades(period=period)

    @routeur.get("/feed")
    def feed(
        weeks: int = Query(1, ge=1, le=4),
    ) -> dict[str, Any]:
        """Flux complet : EDT de la semaine + devoirs + dernières notes."""
        c = _client()
        today = datetime.date.today()
        return {
            "date": today.isoformat(),
            "timetable": c.timetable(date=today, weeks=weeks),
            "homework": c.homework(date_from=today),
            "grades": c.grades(),
            "info": c.info(),
        }

    return routeur
