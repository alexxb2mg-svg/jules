"""Application web : page eleve (chat), page parent (suivi), API JSON.

Les routes des modules sont montees automatiquement sous /api/modules/<id> (acces parent).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from jules import dossier
from jules.acces import COOKIE, DUREE_S, Acces
from jules.moteur import Tuteur

STATIQUE = Path(__file__).parent / "static"
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
IMAGE_MAX_OCTETS = 8 * 1024 * 1024
IMAGES_PAR_MESSAGE = 3
TEXTE_MAX = 6000
ESSAIS_MAX = 8  # tentatives de code par tranche de 10 min et par adresse
ENTETES_SECURITE = {
    # Aucun script, style ou image venant d'ailleurs ; pas d'affichage dans un cadre d'un autre site.
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(self), microphone=(), geolocation=()",
}


def extension_reelle(contenu: bytes) -> str | None:
    """Type d'image deduit des premiers octets (le type annonce par le navigateur ne suffit pas)."""
    if contenu.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if contenu.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if contenu[:4] == b"RIFF" and contenu[8:12] == b"WEBP":
        return "webp"
    if contenu[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    return None


class CodeEntree(BaseModel):
    code: str


class NouvelleConversation(BaseModel):
    mode: str | None = None


def creer_app(tuteur: Tuteur) -> FastAPI:
    app = FastAPI(title="Jules", docs_url=None, redoc_url=None, openapi_url=None)
    acces = Acces(tuteur.config.acces, tuteur.config.donnees / "secret.key")
    essais: dict[str, deque[float]] = defaultdict(deque)
    app.state.tuteur = tuteur
    app.state.acces = acces

    @app.middleware("http")
    async def entetes_securite(request: Request, call_next):
        reponse = await call_next(request)
        for nom, valeur in ENTETES_SECURITE.items():
            reponse.headers.setdefault(nom, valeur)
        if request.url.path.startswith("/api/"):
            reponse.headers.setdefault("Cache-Control", "no-store")
        return reponse

    def role_de(request: Request) -> str | None:
        return acces.lire_jeton(request.cookies.get(COOKIE))

    def exiger(role_requis: str):
        def verifier(request: Request) -> str:
            role = role_de(request)
            if not acces.autorise(role, role_requis):
                raise HTTPException(401, "Code requis")
            return role or role_requis

        return verifier

    eleve = Depends(exiger("eleve"))
    parent = Depends(exiger("parent"))

    # --- pages -----------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    def page_eleve() -> HTMLResponse:
        return HTMLResponse((STATIQUE / "eleve.html").read_text(encoding="utf-8"))

    @app.get("/parent", response_class=HTMLResponse)
    def page_parent() -> HTMLResponse:
        return HTMLResponse((STATIQUE / "parent.html").read_text(encoding="utf-8"))

    @app.get("/cours", response_class=HTMLResponse)
    def page_cours() -> HTMLResponse:
        return HTMLResponse((STATIQUE / "cours.html").read_text(encoding="utf-8"))

    app.mount("/static", StaticFiles(directory=STATIQUE), name="static")

    # --- session ---------------------------------------------------------
    @app.post("/api/session")
    def ouvrir(entree: CodeEntree, request: Request, response: Response) -> dict[str, str]:
        adresse = request.client.host if request.client else "?"
        fenetre = essais[adresse]
        while fenetre and fenetre[0] < time.time() - 600:
            fenetre.popleft()
        if len(fenetre) >= ESSAIS_MAX:
            raise HTTPException(429, "Trop d'essais, attends 10 minutes")
        role = acces.verifier_code(entree.code)
        if role is None:
            fenetre.append(time.time())
            raise HTTPException(401, "Code incorrect")
        response.set_cookie(COOKIE, acces.jeton(role), max_age=DUREE_S, httponly=True, samesite="strict")
        return {"role": role}

    @app.delete("/api/session")
    def fermer(response: Response) -> dict[str, bool]:
        response.delete_cookie(COOKIE)
        return {"ok": True}

    @app.get("/api/session")
    def etat_session(request: Request) -> dict[str, Any]:
        role = role_de(request)
        return {
            "role": role,
            "eleve": acces.autorise(role, "eleve"),
            "parent": acces.autorise(role, "parent"),
        }

    # --- eleve -----------------------------------------------------------
    @app.get("/api/infos")
    def infos(_: str = eleve) -> dict[str, Any]:
        return tuteur.infos_interface()

    @app.get("/api/persona/avatar")
    def avatar() -> FileResponse:
        persona = tuteur.persona()
        if persona.avatar is None:
            raise HTTPException(404)
        return FileResponse(persona.avatar)

    @app.get("/api/conversations")
    def conversations(jour: str | None = None, _: str = eleve) -> list[dict[str, Any]]:
        return tuteur.stockage.lister_conversations(jour=jour, limite=30)

    @app.post("/api/conversations")
    def nouvelle(entree: NouvelleConversation, _: str = eleve) -> dict[str, Any]:
        module_modes = tuteur.module("modes")
        mode = module_modes.valider(entree.mode) if module_modes else (entree.mode or "libre")  # type: ignore[attr-defined]
        conv = tuteur.stockage.creer_conversation(mode)
        return {"id": conv.id, "mode": conv.mode}

    @app.get("/api/conversations/{conv_id}")
    def lire(conv_id: str, _: str = eleve) -> dict[str, Any]:
        conv = tuteur.stockage.conversation(conv_id)
        if conv is None:
            raise HTTPException(404, "Conversation introuvable")
        return {
            "id": conv.id,
            "mode": conv.mode,
            "titre": conv.titre,
            "messages": [m.__dict__ for m in conv.messages],
        }

    @app.post("/api/conversations/{conv_id}/messages")
    async def envoyer(
        conv_id: str,
        texte: str = Form(""),
        photos: list[UploadFile] | None = File(None),  # noqa: B008 - idiome FastAPI
        _: str = eleve,
    ) -> dict[str, Any]:
        texte = texte.strip()[:TEXTE_MAX]
        photos = photos or []
        if not texte and not photos:
            raise HTTPException(400, "Message vide")
        if len(photos) > IMAGES_PAR_MESSAGE:
            raise HTTPException(400, f"{IMAGES_PAR_MESSAGE} photos maximum par message")
        noms = []
        for photo in photos:
            if photo.content_type not in EXTENSIONS:
                raise HTTPException(400, "Format de photo non accepté (JPEG, PNG, WebP, GIF)")
            contenu = await photo.read(IMAGE_MAX_OCTETS + 1)
            if len(contenu) > IMAGE_MAX_OCTETS:
                raise HTTPException(400, "Photo trop lourde (8 Mo maximum)")
            extension = extension_reelle(contenu)
            if extension is None:
                raise HTTPException(400, "Ce fichier n'est pas une image valide")
            noms.append(tuteur.stockage.enregistrer_image(contenu, extension))
        try:
            reponse = await _en_fil(tuteur.echanger, conv_id, texte, noms)
        except KeyError as err:
            raise HTTPException(404, "Conversation introuvable") from err
        return {"reponse": reponse.texte, "horodatage": reponse.horodatage}

    @app.get("/api/images/{nom}")
    def image(nom: str, _: str = eleve) -> FileResponse:
        chemin = tuteur.stockage.chemin_image(nom)
        if chemin is None:
            raise HTTPException(404)
        return FileResponse(chemin)

    # --- parent ----------------------------------------------------------
    @app.get("/api/parent/evenements/{type_}")
    def evenements(type_: str, jour: str | None = None, _: str = parent) -> list[dict[str, Any]]:
        return tuteur.stockage.evenements(type_, jour=jour, limite=200)

    app.include_router(routes_dossier(tuteur), prefix="/api/parent", dependencies=[parent])

    @app.get("/api/parent/modules")
    def modules(_: str = parent) -> list[dict[str, Any]]:
        return [{"id": m.id, "routes": m.routes() is not None} for m in tuteur.modules]

    for module in tuteur.modules:
        for routeur, garde, prefixe in (
            (module.routes(), parent, f"/api/modules/{module.id}"),
            (module.routes_eleve(), eleve, f"/api/eleve/{module.id}"),
        ):
            if routeur is None:
                continue
            enveloppe = APIRouter(dependencies=[garde])
            enveloppe.include_router(routeur)
            app.include_router(enveloppe, prefix=prefixe)

    return app


def routes_dossier(tuteur: Tuteur) -> APIRouter:
    """Le dossier de l'eleve entre les mains du parent : effacer une conversation, tout exporter, tout effacer."""
    routeur = APIRouter()

    @routeur.delete("/conversations/{conv_id}")
    def effacer_conversation(conv_id: str) -> dict[str, bool]:
        tuteur.attendre_fond()  # l'analyse de fond du dernier echange ne doit pas revenir apres
        if not tuteur.stockage.effacer_conversation(conv_id):
            raise HTTPException(404, "Conversation introuvable")
        return {"ok": True}

    @routeur.get("/dossier/export")
    def exporter_dossier() -> Response:
        contenu = dossier.exporter(tuteur)
        entetes = {"Content-Disposition": f'attachment; filename="{dossier.nom_archive()}"'}
        return Response(contenu, media_type="application/zip", headers=entetes)

    @routeur.post("/dossier/effacer")
    def effacer_dossier(entree: dossier.Confirmation) -> dict[str, Any]:
        if entree.confirmation.strip().upper() != dossier.MOT_DE_CONFIRMATION:
            raise HTTPException(400, f"Tape {dossier.MOT_DE_CONFIRMATION} pour confirmer")
        return {"ok": True, "efface": dossier.effacer_tout(tuteur)}

    return routeur


async def _en_fil(fonction, *args):
    """Execute un appel bloquant (moteur d'IA) sans geler le serveur."""
    return await run_in_threadpool(fonction, *args)
