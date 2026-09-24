"""Module 'outils' : sert les outils du dossier `outils/` sous `/api/eleve/outils` (voir
docs/OUTILS-CONTRAT.md). Volontairement séparé de `jules/web/app.py` (mécanisme `routes_eleve()`
existant, comme tous les modules) : rien n'y est ajouté par cette étape.

Chaque réponse porte ses propres en-têtes de sécurité (CSP sans réseau, `X-Frame-Options:
SAMEORIGIN` pour permettre l'iframe same-origin de la page /cours à l'étape suivante, alors que
`jules/web/app.py` pose `X-Frame-Options: DENY` par défaut pour tout le reste du site).

Ce module ne fait QUE servir des fichiers statiques déjà vérifiés par `jules/outils.py` au
chargement : aucune exécution, aucune transformation du contenu.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from jules.modules.base import Module
from jules.outils import Outil, charger_outils

# CSP propre à un outil (voir docs/OUTILS-CONTRAT.md, section 3) : aucun réseau, aucune source
# externe, l'outil ne charge que ce qui est dans son propre dossier.
ENTETES_OUTIL = {
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "font-src 'self'; connect-src 'none'; frame-src 'none'; frame-ancestors 'self'; "
        "form-action 'none'; base-uri 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}

# Extensions servies : uniquement le code de l'outil, jamais outil.yaml ni un fichier de données.
EXTENSIONS_SERVIES = (".html", ".js", ".css")

TYPES_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


def _media_type(chemin: Path) -> str:
    return TYPES_MIME.get(chemin.suffix.lower(), "application/octet-stream")


def _chemin_sur(dossier: Path, sous_chemin: str) -> Path | None:
    """Chemin résolu dans `dossier`, ou None s'il en sort ou a une extension non autorisée."""
    relatif = Path(sous_chemin)
    if relatif.is_absolute() or ".." in relatif.parts:
        return None
    if relatif.suffix.lower() not in EXTENSIONS_SERVIES:
        return None
    cible = (dossier / relatif).resolve()
    try:
        cible.relative_to(dossier.resolve())
    except ValueError:
        return None
    return cible if cible.is_file() else None


class Brique(Module):
    id = "outils"
    titre = "Outils"

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self._outils: dict[str, Outil] | None = None

    @property
    def outils(self) -> dict[str, Outil]:
        if self._outils is None:
            self._outils = charger_outils(self.tuteur.config.dossier_outils)
        return self._outils

    def recharger(self) -> None:
        self._outils = None

    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/catalogue")
        def catalogue() -> list[dict[str, Any]]:
            return [o.publique() for o in self.outils.values()]

        @routeur.get("/{outil_id}")
        @routeur.get("/{outil_id}/")
        def entree(outil_id: str) -> Response:
            outil = self.outils.get(outil_id)
            if outil is None:
                raise HTTPException(404, "Outil introuvable")
            cible = outil.dossier / outil.entree
            return FileResponse(cible, headers=ENTETES_OUTIL, media_type=_media_type(cible))

        @routeur.get("/{outil_id}/{chemin:path}")
        def fichier(outil_id: str, chemin: str) -> Response:
            outil = self.outils.get(outil_id)
            if outil is None:
                raise HTTPException(404, "Outil introuvable")
            cible = _chemin_sur(outil.dossier, chemin)
            if cible is None:
                raise HTTPException(404)
            return FileResponse(cible, headers=ENTETES_OUTIL, media_type=_media_type(cible))

        return routeur

    def infos_interface(self) -> dict[str, Any]:
        return {"outils": {"catalogue": [o.publique() for o in self.outils.values()]}}
