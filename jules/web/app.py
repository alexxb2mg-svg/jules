"""Application web : page eleve (chat), page parent (suivi), API JSON.

Les routes des modules sont montees automatiquement sous /api/modules/<id> (acces parent).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool
from starlette.middleware.gzip import GZipMiddleware

from jules import dossier, page_adaptations
from jules.acces import COOKIE, DUREE_S, Acces, requete_distante
from jules.extensions import code_des_figures, code_des_rappels
from jules.moteur import Tuteur
from jules.web.limite import LimiteEssais
from jules.web.pronote_routes import routes_pronote

STATIQUE = Path(__file__).parent / "static"
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
IMAGE_MAX_OCTETS = 8 * 1024 * 1024
IMAGES_PAR_MESSAGE = 3
TEXTE_MAX = 6000
ESSAIS_MAX = 8  # tentatives de code par tranche de 10 min et par adresse
ESSAIS_MAX_GLOBAL = 30  # meme fenetre, toutes IP confondues (LAN familial avec plusieurs appareils)
ADRESSE_BLOC = re.compile(r"[a-z_]+(?:/[\w.-]+){1,3}")  # type de bloc, puis un a trois identifiants
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


class BlocConsulte(BaseModel):
    adresse: str = Field(max_length=200)  # « fiche/<id> », « carte/<id> », « fiche/<id>/<sous-id> »...
    notion: str | None = Field(default=None, max_length=80)
    conversation: str | None = Field(default=None, max_length=32)

    @field_validator("adresse")
    @classmethod
    def adresse_bien_formee(cls, valeur: str) -> str:
        if not ADRESSE_BLOC.fullmatch(valeur):
            raise ValueError("adresse de bloc mal formee")
        return valeur


class NouvelleConversation(BaseModel):
    mode: str | None = None


PAGE_ADMIN_LOCALE = (
    '<!doctype html><html lang="fr"><meta charset="utf-8"><title>Jules</title>'
    "<p style=\"font-family:sans-serif;margin:3rem\">L'espace d'administration ne s'ouvre que sur "
    "l'ordinateur où tourne Jules.</p></html>"
)


def _charger_config_brute(racine: Path) -> dict[str, Any]:
    """Relit config.yaml + config.local.yaml comme dict brut (pour les sections non portées par Config).
    Les deux sont facultatifs : une config construite en mémoire (depuis_dict, tests) n'a pas de fichier."""
    import yaml

    base = racine / "config.yaml"
    brut = (yaml.safe_load(base.read_text(encoding="utf-8")) or {}) if base.is_file() else {}
    local = racine / "config.local.yaml"
    if local.is_file():
        surcharge = yaml.safe_load(local.read_text(encoding="utf-8")) or {}
        brut.update(surcharge)
    return brut


def creer_app(tuteur: Tuteur) -> FastAPI:
    app = FastAPI(title="Jules", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    acces = Acces(tuteur.config.acces, tuteur.config.donnees / "secret.key")
    essais = LimiteEssais(ESSAIS_MAX, ESSAIS_MAX_GLOBAL)
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

    def distante(request: Request) -> bool:
        return requete_distante(request.headers, request.client.host if request.client else None)

    def exiger(role_requis: str):
        def verifier(request: Request) -> str:
            role = role_de(request)
            loin = distante(request)
            if not acces.autorise(role, role_requis, distant=loin):
                if loin and role_requis == "parent":
                    raise HTTPException(403, "Réservé à l'administrateur, sur son ordinateur")
                raise HTTPException(401, "Code requis")
            return role or role_requis

        return verifier

    eleve = Depends(exiger("eleve"))
    parent = Depends(exiger("parent"))

    # --- pages : tout redirige vers la nouvelle interface React (/app#/…) ---
    @app.get("/")
    def page_accueil() -> RedirectResponse:
        return RedirectResponse("/app#/fiches", status_code=302)

    @app.get("/discuter")
    def page_eleve() -> RedirectResponse:
        return RedirectResponse("/app#/discuter", status_code=302)

    @app.get("/parent", response_model=None)
    def page_parent(request: Request) -> RedirectResponse | HTMLResponse:
        if distante(request):
            return HTMLResponse(PAGE_ADMIN_LOCALE, status_code=403)
        return RedirectResponse("/app#/parent", status_code=302)

    @app.get("/cours")
    def page_cours() -> RedirectResponse:
        return RedirectResponse("/app#/lecons", status_code=302)

    @app.get("/studio")
    def page_studio() -> RedirectResponse:
        return RedirectResponse("/app#/supports", status_code=302)

    @app.get("/app", response_class=HTMLResponse)
    def page_app() -> HTMLResponse:
        """Nouvelle interface (front/, build Vite dans static/app) : a cote des pages existantes, sans
        les remplacer. Le build n'est pas versionne : `npm run build` dans front/ le produit."""
        index = STATIQUE / "app" / "index.html"
        if not index.is_file():
            message = "Nouvelle interface non construite : lancer `npm run build` dans front/."
            return HTMLResponse(message, status_code=404)
        return HTMLResponse(index.read_text(encoding="utf-8"))

    # --- Routeur API Pronote (optionnel, si section pronote: dans config.local.yaml) ---
    _config_brute = _charger_config_brute(tuteur.config.racine)
    _routeur_pronote = routes_pronote(_config_brute)
    if _routeur_pronote is not None:
        # Espace de l'eleve (edt, devoirs, notes de l'eleve) : le code eleve suffit, y compris a distance (tunnel).
        # Les identifiants Pronote restent cote serveur, jamais renvoyes.
        enveloppe_pronote = APIRouter(dependencies=[eleve])
        enveloppe_pronote.include_router(_routeur_pronote)
        app.include_router(enveloppe_pronote, prefix="/api/pronote")

    @app.get("/gabarits.js")
    def gabarits() -> Response:
        """Code des figures fournies par les extensions actives (voir jules/extensions.py) : public
        comme /static, ou vivaient les gabarits avant l'etape 2 des extensions."""
        return Response(code_des_figures(tuteur.extensions), media_type="text/javascript; charset=utf-8")

    @app.get("/rappels.js")
    def rappels() -> Response:
        """Regles des bulles de rappel fournies par les extensions actives (famille `rappels`), a
        charger apres le coeur /static/symboles.js : public comme /static et /gabarits.js."""
        return Response(code_des_rappels(tuteur.extensions), media_type="text/javascript; charset=utf-8")

    app.mount("/static", StaticFiles(directory=STATIQUE), name="static")

    # --- session ---------------------------------------------------------
    @app.post("/api/session")
    def ouvrir(entree: CodeEntree, request: Request, response: Response) -> dict[str, str]:
        adresse = request.client.host if request.client else "?"
        if not essais.autorise(adresse):
            raise HTTPException(429, "Trop d'essais, attends 10 minutes")
        role = acces.verifier_code(entree.code)
        if role is None:
            essais.enregistrer_echec(adresse)
            raise HTTPException(401, "Code incorrect")
        if distante(request):
            role = "eleve"  # a distance, meme le code parent n'ouvre que l'espace eleve
        response.set_cookie(COOKIE, acces.jeton(role), max_age=DUREE_S, httponly=True, samesite="strict")
        return {"role": role}

    @app.delete("/api/session")
    def fermer(response: Response) -> dict[str, bool]:
        response.delete_cookie(COOKIE)
        return {"ok": True}

    @app.get("/api/session")
    def etat_session(request: Request) -> dict[str, Any]:
        role = role_de(request)
        loin = distante(request)
        return {
            "role": role,
            "eleve": acces.autorise(role, "eleve", distant=loin),
            "parent": acces.autorise(role, "parent", distant=loin),
            "distant": loin,
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

    # --- parcours de l'eleve : points d'accroche des extensions (docs/EXTENSIONS.md) ---
    @app.post("/api/seance/bloc_consulte")
    def bloc_consulte(entree: BlocConsulte, _: str = eleve) -> dict[str, bool]:
        tuteur.bloc_consulte(entree.adresse, entree.notion, entree.conversation)
        return {"ok": True}

    @app.post("/api/seance/fin")
    def fin_de_seance(_: str = eleve) -> dict[str, bool]:
        """Appelee par le navigateur a la fermeture de la page (navigator.sendBeacon, sans corps)."""
        return {"ok": tuteur.fin_de_seance()}

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
    app.include_router(routes_adaptations(tuteur), prefix="/api/parent", dependencies=[parent])

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

    # Fichiers statiques sans cookie (iframe a origine opaque, docs/OUTILS-CONTRAT.md),
    # montes apres les routes gardees :
    # /api/eleve/outils/<id>/<fichier> repond sans session ; le catalogue et l'entree restent gardes.
    for module in tuteur.modules:
        statiques = module.routes_statiques()
        if statiques is not None:
            app.include_router(statiques, prefix=f"/api/eleve/{module.id}")

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


class ChoixAdaptations(BaseModel):
    # Types laisses ouverts : la validation (liste fermee, message au parent) est celle de
    # jules/page_adaptations.py, pour que rien d'inattendu n'arrive jusqu'a resoudre() (EX-104).
    amenagements: Any = Field(default_factory=list)
    preferences: Any = Field(default_factory=dict)


def routes_adaptations(tuteur: Tuteur) -> APIRouter:
    """Amenagements du PAP et preferences hors PAP, cotes parent (docs/spec/ADAPTATIONS-LOT2.md, EX-108)."""
    routeur = APIRouter()

    def choix(entree: ChoixAdaptations) -> page_adaptations.Choix:
        try:
            return page_adaptations.choix_depuis_entree(entree.amenagements, entree.preferences)
        except page_adaptations.ChoixInvalide as err:
            raise HTTPException(400, str(err)) from err

    @routeur.get("/adaptations")
    def lire_adaptations() -> dict[str, Any]:
        return page_adaptations.etat(tuteur.config.fichier_profil)

    @routeur.post("/adaptations/apercu")
    def apercu_adaptations(entree: ChoixAdaptations) -> dict[str, Any]:
        """Conflits du choix en cours, avant enregistrement (rien n'est ecrit)."""
        return page_adaptations.etat(tuteur.config.fichier_profil, choix(entree))

    @routeur.put("/adaptations")
    def enregistrer_adaptations(entree: ChoixAdaptations) -> dict[str, Any]:
        valide = choix(entree)
        try:
            page_adaptations.enregistrer(tuteur.config.fichier_profil, valide)
        except page_adaptations.ChoixInvalide as err:
            raise HTTPException(409, str(err)) from err
        return page_adaptations.etat(tuteur.config.fichier_profil)

    return routeur


async def _en_fil(fonction, *args):
    """Execute un appel bloquant (moteur d'IA) sans geler le serveur."""
    return await run_in_threadpool(fonction, *args)
