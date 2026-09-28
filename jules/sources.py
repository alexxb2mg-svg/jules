"""Sources personnelles : un document de l'eleve (photos, PDF, texte colle) devient une fiche visuelle
rangee dans sa bibliotheque personnelle. Contrat : docs/SOURCES-CONTRAT.md.

Le parcours (contrat §2) : lire -> proposer la notion -> generer -> controler -> ranger.
  - la notion est choisie par le modele dans une LISTE FERMEE ; le code verifie l'id (inconnu = aucune) ;
  - la fiche est ecrite au format des fiches visuelles, avec la meme charte et le meme format que le
    patron de generation (jules/chantier_visuel.py), et controlee par le meme validateur
    (jules/fiches_visuelles.py, `lire_fiche_personnelle`) ; un seul nouvel essai, motif a l'appui ;
  - rien n'est ecrit sous bibliotheque/ : tout vit dans les donnees de l'eleve (etat 'sources' de la
    base, fichiers dans le dossier des images), donc exporte et efface avec le dossier de l'eleve.

Ce fichier ne connait ni FastAPI ni l'interface : le module jules/modules/sources.py l'expose.
"""

from __future__ import annotations

import io
import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from jules.bibliotheques import Notion
from jules.fiches_visuelles import ErreurFicheVisuelle, FicheVisuelle, lire_fiche_personnelle
from jules.llm.base import Tour
from jules.modules.base import extraire_json

# --- limites (contrat §3) ------------------------------------------------------------------------

PHOTOS_MAX = 5
PHOTO_MAX_OCTETS = 8 * 1024 * 1024
PDF_MAX_OCTETS = 10 * 1024 * 1024
PDF_PAGES_MAX = 20
PAGES_SCANNEES_MAX = 5  # un PDF sans texte : ses premieres pages, converties en images (comme des photos)
TEXTE_MAX = 30_000
TEXTE_MIN = 120  # en dessous, pas de quoi faire 3 blocs : on le dit a l'eleve (contrat §5)
TEXTE_PDF_MIN = 200  # un PDF qui a moins de texte que cela est traite comme un scan
NOM_DOSSIER_MAX = 40
ESSAIS_GENERATION = 2  # le premier + un seul nouvel essai (contrat §2, point 5)

ESPACE = "sources"
NON_CLASSE = "non-classe"
ETAT_A_RANGER = "a_ranger"
ETAT_RANGEE = "rangee"


class ErreurSource(ValueError):
    """Message clair, destine a l'eleve."""


# --- lecture de la source -------------------------------------------------------------------------


def type_image(contenu: bytes) -> str | None:
    """Type d'image d'apres les premiers octets (le nom du fichier ne suffit pas)."""
    if contenu.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if contenu.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if contenu[:4] == b"RIFF" and contenu[8:12] == b"WEBP":
        return "webp"
    if contenu[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1", b"ftypmsf1", b"ftyphevc"):
        return "heic"
    return None


def heic_en_jpeg(contenu: bytes) -> bytes:
    """Photo d'iPhone (HEIC) -> JPEG (contrat, Q3). Sans pillow-heif : message clair."""
    try:
        import pillow_heif
        from PIL import Image
    except ImportError as err:
        raise ErreurSource(
            "Les photos d'iPhone (HEIC) ne sont pas lues sur cet ordinateur : envoie-la en JPEG."
        ) from err
    pillow_heif.register_heif_opener()
    image = Image.open(io.BytesIO(contenu)).convert("RGB")
    sortie = io.BytesIO()
    image.save(sortie, "JPEG", quality=88)
    return sortie.getvalue()


def lire_pdf(contenu: bytes) -> tuple[str, list[bytes]]:
    """(texte, pages en PNG si le PDF n'a pas de texte). Refuse un PDF illisible, protege ou trop long."""
    if not contenu.startswith(b"%PDF"):
        raise ErreurSource("Ce fichier n'est pas un PDF.")
    try:
        import pypdfium2 as pdfium
    except ImportError as err:
        raise ErreurSource("Les PDF ne sont pas lus sur cet ordinateur : envoie des photos de ton cours.") from err
    try:
        document = pdfium.PdfDocument(contenu)
    except pdfium.PdfiumError as err:
        raise ErreurSource("Ce PDF est illisible ou protégé par un mot de passe.") from err
    try:
        if len(document) > PDF_PAGES_MAX:
            raise ErreurSource(
                f"Ce PDF a {len(document)} pages : {PDF_PAGES_MAX} au plus, garde seulement ton chapitre."
            )
        textes = []
        for page in document:
            textes.append(page.get_textpage().get_text_range())
        texte = "\n\n".join(t.strip() for t in textes if t.strip())
        if len(texte) >= TEXTE_PDF_MIN:
            return texte[:TEXTE_MAX], []
        pages = []
        for i in range(min(len(document), PAGES_SCANNEES_MAX)):
            image = document[i].render(scale=1.6).to_pil().convert("RGB")
            sortie = io.BytesIO()
            image.save(sortie, "JPEG", quality=85)
            pages.append(sortie.getvalue())
        return "", pages
    finally:
        document.close()


@dataclass
class Source:
    """Ce que l'eleve apporte, deja lu : du texte et/ou des images (chemins dans le dossier des images)."""

    id: str
    type: str  # photos | pdf | texte
    titre: str
    texte: str = ""
    images: list[Path] = field(default_factory=list)
    fichiers: list[str] = field(default_factory=list)  # noms dans le dossier des images (photos, pdf)

    def resume(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type, "titre": self.titre, "fichiers": list(self.fichiers)}


def titre_source(type_: str, jour: datetime | None = None) -> str:
    jour = jour or datetime.now()
    nom = {"photos": "Mes photos", "pdf": "Mon PDF", "texte": "Mon texte"}.get(type_, "Mon document")
    return f"{nom} du {jour:%d/%m}"


# --- rattachement a une notion (contrat §4) -------------------------------------------------------

CONSIGNE_RATTACHEMENT = """Tu rattaches le cours d'un élève à UNE notion d'une liste fermée.
(marqueur : RATTACHEMENT_SOURCE)
Lis son document (texte et/ou photos), puis réponds UNIQUEMENT par un objet JSON :
{"notion": "<identifiant de la liste, ou null>", "matiere": "<identifiant de matière, ou null>",
 "raison": "<une phrase>"}
- Choisis l'identifiant tel quel dans la liste, sans l'inventer ni le modifier.
- "notion": null si aucune notion de la liste ne correspond vraiment au document.
- "matiere" : la matière du document (identifiant de la liste), même si aucune notion ne convient.
Liste (identifiant | matière | chapitre | notion) :
"""


@dataclass
class Suggestion:
    notion: Notion | None
    matiere: str | None
    raison: str
    avertissement: str = ""  # « Ça ressemble à de l'histoire, pas à de la physique. »

    def publique(self) -> dict[str, Any]:
        return {
            "notion": self.notion.id if self.notion else None,
            "titre_notion": self.notion.titre if self.notion else None,
            "matiere": self.matiere,
            "raison": self.raison,
            "avertissement": self.avertissement,
        }


def _liste_notions(notions: dict[str, Notion], matiere_choisie: str | None) -> str:
    ordre = sorted(notions.values(), key=lambda n: (n.matiere != matiere_choisie, n.matiere, n.chapitre, n.titre))
    return "\n".join(f"{n.id} | {n.matiere} | {n.chapitre} | {n.titre}" for n in ordre)


def proposer_notion(
    llm: Any, notions: dict[str, Notion], matieres: dict[str, str], source: Source, matiere_choisie: str | None
) -> Suggestion:
    """La notion la plus proche, choisie par le modele et CONTROLEE par le code (id inconnu = aucune)."""
    texte = source.texte[:6000] or "(document en photos)"
    if matiere_choisie:
        texte = f"(L'élève pense que c'est : {matieres.get(matiere_choisie, matiere_choisie)})\n\n{texte}"
    brut = llm.repondre(
        CONSIGNE_RATTACHEMENT + _liste_notions(notions, matiere_choisie), [Tour("user", texte, source.images)], "rapide"
    )
    reponse = extraire_json(brut) or {}
    identifiant = str(reponse.get("notion") or "").strip()
    notion = notions.get(identifiant)
    lue = notion.matiere if notion else str(reponse.get("matiere") or "").strip()
    matiere = lue if lue in matieres else None
    raison = str(reponse.get("raison") or "").strip()[:200]
    avertissement = ""
    if matiere and matiere_choisie and matiere != matiere_choisie:
        avertissement = f"Ça ressemble à {matieres[matiere]}, pas à {matieres.get(matiere_choisie, matiere_choisie)}."
    return Suggestion(notion=notion, matiere=matiere, raison=raison, avertissement=avertissement)


# --- generation (contrat §5) ----------------------------------------------------------------------

CONSIGNES_GENERATION = """\
# Fiche personnelle Jules (marqueur : GENERATION_FICHE_PERSONNELLE)

Tu écris UNE fiche visuelle pour Jules, un tuteur libre pour les élèves, à partir du document qu'un élève
de {niveau} a apporté (photo de son cours, PDF ou texte collé). La fiche va dans SA bibliothèque personnelle.

Règle de fidélité (la plus importante) :
- Le contenu vient du document de l'élève. Tu reformules, structures et mets en valeur ce qu'il dit ;
  tu n'ajoutes pas de notion absente du document.
- La carte, la méthode et le piège peuvent être déduits du document.
- Un exemple ou un schéma absent du document est permis s'il illustre ce que dit le document : sa bulle
  `jules:` commence alors par « Exemple ajouté par Jules. » (ou « Schéma ajouté par Jules. »).
- Si le document est illisible ou trop pauvre pour 3 blocs, réponds seulement : TROP_COURT

Ce que tu rends : UNIQUEMENT le YAML de la fiche, dans un bloc ```yaml, sans rien d'autre.
- En-tête : `notion: {notion}`, `matiere: {matiere}`, `titre:` (le sujet du document, court).
- N'écris PAS `sources`, `licence`, `relecture`, `auteurs` ni `generation` : Jules les remplit.
- Un bloc `schema` a son SVG EN LIGNE (`svg: "<svg ...>...</svg>"`), jamais un fichier à côté.
- Pas de bloc `renfort` (il renvoie vers des outils du programme, pas vers le document de l'élève).

Règles d'écriture YAML : guillemets doubles autour de toute chaîne qui contient « : », « # » ou des `**`.
Suis la charte et le format ci-dessous à la lettre : un programme contrôle la fiche avant de l'afficher.
"""


def paquet_generation(racines: Any, niveau: str, suggestion: Suggestion) -> str:
    """Le prompt systeme : consignes propres aux fiches personnelles + la MEME charte, le MEME format et
    la MEME fiche modele que le patron de generation (jules/chantier_visuel.py). Pas de deuxieme charte."""
    from jules.chantier_visuel import CHARTE, FORMAT, _document, _modele

    notion = suggestion.notion
    parties = [
        CONSIGNES_GENERATION.format(
            niveau=niveau or "collège",
            notion=notion.id if notion else "(aucune : n'écris pas le champ notion)",
            matiere=suggestion.matiere or "(inconnue : n'écris pas le champ matiere)",
        ).rstrip(),
        "## La charte (docs/FICHES-VISUELLES.md)\n\n" + _document(CHARTE),
        "## Le format (bibliotheque/SCHEMA-FICHE-VISUELLE.md)\n\n" + _document(FORMAT),
    ]
    modele_id, modele, _svgs = _modele(racines, [notion] if notion else [])
    if modele:
        parties.append(
            f"## Une fiche conforme, pour la forme et le niveau de soin (`{modele_id}`)\n\n"
            "Ne reprends pas son contenu : elle montre la structure, le ton et la facture attendus.\n\n"
            f"```yaml\n{modele}\n```"
        )
    if notion:
        lignes = [f"## La notion du programme : {notion.titre} ({notion.nom_matiere}, {notion.niveau})", ""]
        lignes += [
            "Attendus officiels (pour le niveau et le vocabulaire ; n'ajoute rien qui ne soit pas dans le document) :"
        ]
        lignes += [f"- {a}" for a in notion.attendus]
        if notion.limites:
            lignes += ["", "Limites du programme (ne pas aller au-delà) :", *[f"- {x}" for x in notion.limites]]
        parties.append("\n".join(lignes))
    return "\n\n".join(parties) + "\n"


_BLOC_YAML = re.compile(r"```(?:yaml|yml)?\s*\n(.*?)```", re.DOTALL)


def lire_reponse_yaml(texte: str) -> Any:
    if "TROP_COURT" in texte and "blocs" not in texte:
        raise ErreurSource("Ton document est trop court pour une fiche : ajoute une photo ou colle plus de texte.")
    bloc = _BLOC_YAML.search(texte)
    try:
        return yaml.safe_load(bloc.group(1) if bloc else texte)
    except yaml.YAMLError as err:
        raise ErreurFicheVisuelle(f"YAML illisible ({str(err)[:200]})") from err


def generer_fiche(
    llm: Any,
    systeme: str,
    source: Source,
    notions: dict[str, Notion],
    matieres: dict[str, str],
    niveau: str,
    gabarits: frozenset[str],
) -> tuple[Any, FicheVisuelle]:
    """(brut, fiche controlee). Un seul nouvel essai, avec le motif du refus (contrat §2, point 5)."""
    tours = [Tour("user", source.texte or "(Le document est dans les photos jointes.)", source.images)]
    motif = ""
    for _essai in range(ESSAIS_GENERATION):
        reponse = llm.repondre(systeme, tours, "principal")
        try:
            brut = lire_reponse_yaml(reponse)
            fiche = lire_fiche_personnelle(brut, notions, matieres, niveau, source.resume(), gabarits)
            return brut, fiche
        except ErreurFicheVisuelle as err:
            motif = str(err)
            tours = [
                *tours,
                Tour("assistant", reponse[:20_000]),
                Tour(
                    "user",
                    f"Le contrôle a refusé cette fiche : {motif}\n"
                    "Corrige et renvoie la fiche entière, dans un bloc ```yaml.",
                ),
            ]
    raise ErreurSource(f"Je n'ai pas réussi à en faire une fiche propre ({motif}).")


# --- la bibliotheque personnelle (contrat §6) -----------------------------------------------------


def maintenant() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Bibliotheque:
    """Index, fiches et dossiers de l'eleve, dans l'etat 'sources' de la base (efface et exporte avec
    le dossier de l'eleve). Une fiche : cle 'fiche:<id>' (le YAML genere, tel que controle)."""

    def __init__(self, stockage: Any) -> None:
        self.stockage = stockage

    # index et dossiers
    def index(self) -> dict[str, dict[str, Any]]:
        return dict(self.stockage.lire_etat(ESPACE, "index", {}) or {})

    def _ecrire_index(self, index: dict[str, dict[str, Any]]) -> None:
        self.stockage.ecrire_etat(ESPACE, "index", index)

    def dossiers(self) -> list[dict[str, str]]:
        return list(self.stockage.lire_etat(ESPACE, "dossiers", []) or [])

    def entree(self, fiche_id: str) -> dict[str, Any]:
        entree = self.index().get(fiche_id)
        if entree is None:
            raise KeyError(fiche_id)
        return entree

    def brut(self, fiche_id: str) -> Any:
        return self.stockage.lire_etat(ESPACE, f"fiche:{fiche_id}")

    # ecriture
    def ajouter(self, source: Source, suggestion: Suggestion, brut: Any, fiche: FicheVisuelle) -> dict[str, Any]:
        fiche_id = uuid.uuid4().hex[:12]
        entree = {
            "id": fiche_id,
            "titre": fiche.titre,
            "notion": None,
            "matiere": fiche.matiere or None,
            "dossier": None,
            "etat": ETAT_A_RANGER,
            "suggestion": suggestion.publique(),
            "source": source.resume(),
            "cree_le": maintenant(),
        }
        self.stockage.ecrire_etat(ESPACE, f"fiche:{fiche_id}", brut)
        if source.texte:
            self.stockage.ecrire_etat(ESPACE, f"texte:{source.id}", source.texte)
        index = self.index()
        index[fiche_id] = entree
        self._ecrire_index(index)
        return entree

    def ranger(self, fiche_id: str, mode: str, dossier: str | None = None) -> dict[str, Any]:
        """mode : notion (la notion suggeree) | dossier (+ notion suggeree gardee, Q5) | non_classe."""
        index = self.index()
        entree = index.get(fiche_id)
        if entree is None:
            raise KeyError(fiche_id)
        suggeree = (entree.get("suggestion") or {}).get("notion")
        if mode == "notion":
            if not suggeree:
                raise ErreurSource("Jules n'a trouvé aucune notion pour cette fiche : range-la dans un dossier.")
            entree.update({"notion": suggeree, "dossier": None})
        elif mode == "dossier":
            if dossier not in {d["id"] for d in self.dossiers()}:
                raise ErreurSource("Ce dossier n'existe pas.")
            entree.update({"notion": suggeree, "dossier": dossier})
        elif mode == "non_classe":
            entree.update({"notion": None, "dossier": None})
        else:
            raise ErreurSource(f"Rangement inconnu : {mode}")
        entree["etat"] = ETAT_RANGEE
        entree["range_le"] = maintenant()
        index[fiche_id] = entree
        self._ecrire_index(index)
        return entree

    def renommer(self, fiche_id: str, titre: str) -> dict[str, Any]:
        titre = titre.strip()
        if not titre or len(titre) > 90:
            raise ErreurSource("Un titre de 1 à 90 caractères.")
        index = self.index()
        if fiche_id not in index:
            raise KeyError(fiche_id)
        index[fiche_id]["titre"] = titre
        self._ecrire_index(index)
        return index[fiche_id]

    def supprimer(self, fiche_id: str) -> dict[str, Any]:
        """Supprime la fiche ET sa source (texte et fichiers), sauf si une autre fiche en depend."""
        index = self.index()
        entree = index.pop(fiche_id, None)
        if entree is None:
            raise KeyError(fiche_id)
        self._ecrire_index(index)
        self.stockage.ecrire_etat(ESPACE, f"fiche:{fiche_id}", None)
        source = entree.get("source") or {}
        if not any((e.get("source") or {}).get("id") == source.get("id") for e in index.values()):
            self.stockage.ecrire_etat(ESPACE, f"texte:{source.get('id')}", None)
            for nom in source.get("fichiers") or []:
                chemin = self.stockage.chemin_image(nom)
                if chemin is not None:
                    chemin.unlink(missing_ok=True)
        return entree

    def creer_dossier(self, nom: str) -> dict[str, str]:
        nom = " ".join(nom.split())
        if not nom or len(nom) > NOM_DOSSIER_MAX:
            raise ErreurSource(f"Un nom de dossier de 1 à {NOM_DOSSIER_MAX} caractères.")
        dossiers = self.dossiers()
        if any(d["nom"].lower() == nom.lower() for d in dossiers):
            raise ErreurSource("Tu as déjà un dossier de ce nom.")
        dossier = {"id": uuid.uuid4().hex[:10], "nom": nom}
        self.stockage.ecrire_etat(ESPACE, "dossiers", [*dossiers, dossier])
        return dossier

    def renommer_dossier(self, dossier_id: str, nom: str) -> dict[str, str]:
        nom = " ".join(nom.split())
        if not nom or len(nom) > NOM_DOSSIER_MAX:
            raise ErreurSource(f"Un nom de dossier de 1 à {NOM_DOSSIER_MAX} caractères.")
        dossiers = self.dossiers()
        for d in dossiers:
            if d["id"] == dossier_id:
                d["nom"] = nom
                self.stockage.ecrire_etat(ESPACE, "dossiers", dossiers)
                return d
        raise KeyError(dossier_id)

    def supprimer_dossier(self, dossier_id: str) -> int:
        """Le dossier disparait, ses fiches restent : elles vont dans leur notion, sinon dans Non classe."""
        dossiers = self.dossiers()
        if dossier_id not in {d["id"] for d in dossiers}:
            raise KeyError(dossier_id)
        self.stockage.ecrire_etat(ESPACE, "dossiers", [d for d in dossiers if d["id"] != dossier_id])
        index = self.index()
        deplacees = 0
        for entree in index.values():
            if entree.get("dossier") == dossier_id:
                entree["dossier"] = None
                deplacees += 1
        self._ecrire_index(index)
        return deplacees

    def a_ranger(self) -> list[dict[str, Any]]:
        return [e for e in self.index().values() if e.get("etat") == ETAT_A_RANGER]


def extraire(stockage: Any, photos: list[bytes], pdf: bytes | None, texte: str, jour: datetime | None = None) -> Source:
    """Lit la source (une seule forme a la fois) et range ses fichiers dans le dossier des images."""
    formes = sum(1 for x in (photos, pdf, texte.strip()) if x)
    if formes != 1:
        raise ErreurSource("Envoie des photos, OU un PDF, OU un texte collé.")
    source_id = uuid.uuid4().hex[:12]
    if texte.strip():
        texte = texte.strip()
        if len(texte) > TEXTE_MAX:
            raise ErreurSource(f"Ton texte est trop long ({len(texte)} caractères, {TEXTE_MAX} au plus).")
        if len(texte) < TEXTE_MIN:
            raise ErreurSource("Ton document est trop court pour une fiche : ajoute une photo ou colle plus de texte.")
        return Source(source_id, "texte", titre_source("texte", jour), texte=texte)
    if pdf is not None:
        if len(pdf) > PDF_MAX_OCTETS:
            raise ErreurSource("Ce PDF dépasse 10 Mo.")
        contenu, pages = lire_pdf(pdf)
        nom_pdf = stockage.enregistrer_image(pdf, "pdf")
        noms = [stockage.enregistrer_image(p, "jpg") for p in pages]
        images = [p for p in (stockage.chemin_image(n) for n in noms) if p is not None]
        return Source(
            source_id, "pdf", titre_source("pdf", jour), texte=contenu, images=images, fichiers=[nom_pdf, *noms]
        )
    if len(photos) > PHOTOS_MAX:
        raise ErreurSource(f"{PHOTOS_MAX} photos au plus.")
    noms = []
    for photo in photos:
        if len(photo) > PHOTO_MAX_OCTETS:
            raise ErreurSource("Une photo dépasse 8 Mo.")
        genre = type_image(photo)
        if genre is None:
            raise ErreurSource("Une des photos n'est pas une image (JPEG, PNG, WebP ou HEIC).")
        if genre == "heic":
            photo, genre = heic_en_jpeg(photo), "jpg"
        noms.append(stockage.enregistrer_image(photo, genre))
    images = [p for p in (stockage.chemin_image(n) for n in noms) if p is not None]
    return Source(source_id, "photos", titre_source("photos", jour), images=images, fichiers=noms)


def parcours(
    llm: Any,
    stockage: Any,
    racines: Any,
    notions: dict[str, Notion],
    matieres: dict[str, str],
    niveau: str,
    gabarits: frozenset[str],
    source: Source,
    matiere_choisie: str | None,
    retirer_fichiers: bool = True,
) -> Iterator[dict[str, Any]]:
    """Les etapes reelles (contrat §8 : jamais une barre qui fait semblant), puis la fiche rangee
    'a ranger'. Une erreur est rendue comme etape 'erreur' ; les fichiers de la source sont alors retires."""
    try:
        yield {"etape": "notion"}
        suggestion = proposer_notion(llm, notions, matieres, source, matiere_choisie)
        yield {"etape": "ecriture", "suggestion": suggestion.publique()}
        systeme = paquet_generation(racines, niveau, suggestion)
        brut, fiche = generer_fiche(llm, systeme, source, notions, matieres, niveau, gabarits)
        yield {"etape": "verification"}
        entree = Bibliotheque(stockage).ajouter(source, suggestion, brut, fiche)
        yield {"etape": "fin", "fiche": entree}
    except (ErreurSource, ErreurFicheVisuelle) as err:
        # Premiere generation ratee : la source n'appartient a aucune fiche, on la retire.
        # Regeneration ratee : la source reste a la fiche d'origine.
        for nom in source.fichiers if retirer_fichiers else []:
            chemin = stockage.chemin_image(nom)
            if chemin is not None:
                chemin.unlink(missing_ok=True)
        yield {"etape": "erreur", "message": str(err)}
