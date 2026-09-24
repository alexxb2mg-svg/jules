"""Bibliotheques : le referentiel des notions et les contenus qui s'y rattachent.

Une bibliotheque est un dossier `bibliotheque/<id>/` qui se presente dans `bibliotheque.yaml`.
Trois types, qui se combinent :

  - referentiel : la liste des notions (le programme officiel), une par niveau et par matiere.
                  C'est lui qui donne les identifiants de notions ; tout le reste s'y rattache.
  - fiches      : des reperes par notion (essentiel, methode, erreurs frequentes, exercices...).
  - direction   : la direction pedagogique d'un enseignant (approche, vocabulaire, redaction...).

Chaque bibliotheque declare son statut (experimentale, certifiee, enseignant, exemple) et sa
licence. L'ordre de la liste dans la configuration est l'ordre de priorite : pour un meme champ,
la premiere bibliotheque qui le renseigne l'emporte. Les directions, elles, s'additionnent.

Ce fichier ne fait que lire et verifier : il ne parle ni au modele d'IA ni a l'interface.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

journal = logging.getLogger("jules.bibliotheques")

TYPES = ("referentiel", "fiches", "direction")
STATUTS = ("experimentale", "certifiee", "enseignant", "exemple")
# Licences qui autorisent a reutiliser, modifier et redistribuer (identifiants SPDX quand ils existent).
LICENCES_LIBRES = (
    "domaine-public",
    "CC0-1.0",
    "CC-BY-2.0-FR",
    "CC-BY-3.0",
    "CC-BY-4.0",
    "CC-BY-SA-2.0-FR",
    "CC-BY-SA-3.0",
    "CC-BY-SA-4.0",
    "GFDL-1.2-or-later",
    "GFDL-1.3-or-later",
    "etalab-2.0",
    "MIT",
)
# Champs d'une fiche qui ne sont pas des reperes de cours (metadonnees ou direction de l'enseignant).
# Champs d'une fiche qui ne sont pas du contenu de cours (non injectes dans le prompt comme tels).
# `declencheurs` : mots qu'un eleve emploie sans nommer la notion (« soldes », « lutin », « méridien »),
# utilises seulement pour preselectionner les notions candidates a la detection.
CHAMPS_HORS_CONTENU = frozenset({"notion", "direction", "sources", "relecture", "declencheurs"})
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAILLE_MAX_FICHIER = 200_000  # octets : une fiche est un texte court, pas un manuel


class ErreurBibliotheque(ValueError):
    pass


# --- structures ------------------------------------------------------------------


@dataclass
class Notion:
    id: str
    titre: str
    matiere: str  # id de la matiere (= nom du fichier du referentiel)
    nom_matiere: str
    niveau: str
    niveau_programme: str = ""
    theme: str = ""
    chapitre: str = ""
    attendus: list[str] = field(default_factory=list)
    mots_cles: list[str] = field(default_factory=list)
    brevet: bool = False
    source: str = ""


@dataclass
class Bibliotheque:
    id: str
    titre: str
    type: str
    statut: str
    licence: str
    dossier: Path
    niveaux: list[str] = field(default_factory=list)
    avertissement: str = ""
    description: str = ""
    fiches: dict[str, dict[str, Any]] = field(default_factory=dict)  # id de notion -> fiche
    directions_matieres: dict[str, dict[str, Any]] = field(default_factory=dict)  # id de matiere -> direction

    def publique(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "titre": self.titre,
            "type": self.type,
            "statut": self.statut,
            "licence": self.licence,
            "avertissement": self.avertissement,
            "nb_fiches": len(self.fiches),
        }


@dataclass
class Catalogue:
    """Ce que Jules a charge : un referentiel (les notions) et des bibliotheques de contenu, par priorite."""

    notions: dict[str, Notion]
    referentiel: Bibliotheque | None
    contenus: list[Bibliotheque]

    def notion(self, identifiant: str) -> Notion | None:
        return self.notions.get(identifiant)

    def matieres(self) -> list[tuple[str, str, list[Notion]]]:
        """(id, nom, notions) dans l'ordre du referentiel."""
        ordre: dict[str, tuple[str, list[Notion]]] = {}
        for n in self.notions.values():
            ordre.setdefault(n.matiere, (n.nom_matiere, []))[1].append(n)
        return [(mid, nom, notions) for mid, (nom, notions) in ordre.items()]

    def a_une_fiche(self, identifiant: str) -> bool:
        """Vrai si une bibliotheque apporte du contenu (pas seulement une direction) sur la notion."""
        return any(any(cle not in CHAMPS_HORS_CONTENU for cle in b.fiches.get(identifiant, {})) for b in self.contenus)

    def fiche(self, identifiant: str) -> tuple[dict[str, Any], list[Bibliotheque]]:
        """Fiche fusionnee (premier qui renseigne un champ l'emporte) et bibliotheques qui y ont contribue."""
        fusion: dict[str, Any] = {}
        origines: list[Bibliotheque] = []
        for biblio in self.contenus:
            fiche = biblio.fiches.get(identifiant)
            if not fiche:
                continue
            apport = False
            for cle, valeur in fiche.items():
                if cle in CHAMPS_HORS_CONTENU or valeur in (None, "", [], {}):
                    continue
                if cle not in fusion:
                    fusion[cle] = valeur
                    apport = True
            if apport:
                origines.append(biblio)
        return fusion, origines

    def declencheurs(self, identifiant: str) -> list[str]:
        """Mots declencheurs apportes par les fiches (toutes bibliotheques confondues)."""
        vus: list[str] = []
        for biblio in self.contenus:
            for mot in (biblio.fiches.get(identifiant) or {}).get("declencheurs") or []:
                if str(mot) not in vus:
                    vus.append(str(mot))
        return vus

    def directions(self, notion: Notion) -> list[tuple[Bibliotheque, dict[str, Any]]]:
        """Directions pedagogiques qui s'appliquent : celle de la matiere puis celle de la notion."""
        resultat = []
        for biblio in self.contenus:
            generale = biblio.directions_matieres.get(notion.matiere)
            if generale:
                resultat.append((biblio, generale))
            fiche = biblio.fiches.get(notion.id) or {}
            if fiche.get("direction"):
                resultat.append((biblio, fiche["direction"]))
        return resultat


# --- lecture ---------------------------------------------------------------------


def _lire_yaml(chemin: Path) -> dict[str, Any]:
    if chemin.stat().st_size > TAILLE_MAX_FICHIER:
        raise ErreurBibliotheque(f"{chemin.name} : fichier trop gros")
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    if not isinstance(brut, dict):
        raise ErreurBibliotheque(f"{chemin.name} : un objet YAML est attendu")
    return brut


def lire_identite(dossier: Path) -> Bibliotheque:
    """Lit et verifie `bibliotheque.yaml`."""
    fichier = dossier / "bibliotheque.yaml"
    if not fichier.is_file():
        raise ErreurBibliotheque(f"{dossier.name} : bibliotheque.yaml manquant")
    brut = _lire_yaml(fichier)
    identifiant = str(brut.get("id") or "")
    if identifiant != dossier.name:
        raise ErreurBibliotheque(f"{dossier.name} : l'id ({identifiant!r}) doit etre le nom du dossier")
    type_ = str(brut.get("type") or "")
    statut = str(brut.get("statut") or "")
    licence = str(brut.get("licence") or "")
    if type_ not in TYPES:
        raise ErreurBibliotheque(f"{identifiant} : type {type_!r} inconnu (attendu : {', '.join(TYPES)})")
    if statut not in STATUTS:
        raise ErreurBibliotheque(f"{identifiant} : statut {statut!r} inconnu (attendu : {', '.join(STATUTS)})")
    if not licence:
        raise ErreurBibliotheque(f"{identifiant} : licence manquante")
    avertissement = str(brut.get("avertissement") or "").strip()
    if statut in ("experimentale", "exemple") and not avertissement:
        raise ErreurBibliotheque(f"{identifiant} : une bibliotheque {statut} doit porter un avertissement")
    return Bibliotheque(
        id=identifiant,
        titre=str(brut.get("titre") or identifiant),
        type=type_,
        statut=statut,
        licence=licence,
        dossier=dossier,
        niveaux=[str(n) for n in brut.get("niveaux") or []],
        avertissement=avertissement,
        description=str(brut.get("description") or "").strip(),
    )


def lire_referentiel(biblio: Bibliotheque, niveaux: list[str] | None = None) -> dict[str, Notion]:
    """Notions du referentiel : `<niveau>/<matiere>.yaml` (les fichiers `_*.yaml` sont des annexes)."""
    notions: dict[str, Notion] = {}
    for niveau in biblio.niveaux:
        if niveaux and niveau not in niveaux:
            continue
        for fichier in sorted((biblio.dossier / niveau).glob("*.yaml")):
            if fichier.name.startswith("_"):
                continue
            brut = _lire_yaml(fichier)
            matiere = str(brut.get("id") or fichier.stem)
            for theme in brut.get("themes") or []:
                for chapitre in theme.get("chapitres") or []:
                    for n in chapitre.get("notions") or []:
                        identifiant = str(n["id"])
                        if identifiant in notions:
                            raise ErreurBibliotheque(f"{biblio.id} : notion {identifiant!r} en double")
                        notions[identifiant] = Notion(
                            id=identifiant,
                            titre=str(n.get("titre") or identifiant),
                            matiere=matiere,
                            nom_matiere=str(brut.get("matiere") or matiere),
                            niveau=niveau,
                            niveau_programme=str(n.get("niveau_programme") or ""),
                            theme=str(theme.get("titre") or ""),
                            chapitre=str(chapitre.get("titre") or ""),
                            attendus=[str(a) for a in n.get("attendus") or []],
                            mots_cles=[str(m) for m in n.get("mots_cles") or []],
                            brevet=bool(n.get("brevet")),
                            source=str(n.get("source") or ""),
                        )
    return notions


def lire_contenus(biblio: Bibliotheque, notions: dict[str, Notion]) -> None:
    """Charge `fiches/**/*.yaml` et `matieres/*.yaml`. Une fiche sur une notion inconnue est ignoree."""
    for fichier in sorted((biblio.dossier / "fiches").rglob("*.yaml")):
        fiche = _lire_yaml(fichier)
        identifiant = str(fiche.get("notion") or "")
        if identifiant not in notions:
            journal.warning("%s : fiche %s ignoree (notion %r inconnue)", biblio.id, fichier.name, identifiant)
            continue
        biblio.fiches[identifiant] = fiche
    for fichier in sorted((biblio.dossier / "matieres").glob("*.yaml")):
        brut = _lire_yaml(fichier)
        if brut.get("direction"):
            biblio.directions_matieres[str(brut.get("matiere") or fichier.stem)] = brut["direction"]


def charger_catalogue(racine: Path, ids: list[str], niveau: str | None = None) -> Catalogue:
    """Charge les bibliotheques citees (dans l'ordre de priorite) pour un niveau donne (tous si None).

    Une bibliotheque illisible est signalee et ecartee : Jules continue sans elle.
    """
    referentiel: Bibliotheque | None = None
    notions: dict[str, Notion] = {}
    contenus: list[Bibliotheque] = []
    niveaux = [niveau] if niveau else None
    lues: list[Bibliotheque] = []
    for identifiant in ids:
        if not _ID.match(identifiant):
            journal.error("Identifiant de bibliotheque invalide : %r", identifiant)
            continue
        try:
            lues.append(lire_identite(racine / identifiant))
        except (ErreurBibliotheque, OSError, yaml.YAMLError) as err:
            journal.error("Bibliotheque %s ecartee : %s", identifiant, err)
    for biblio in lues:
        if biblio.type != "referentiel":
            continue
        if referentiel is not None:
            journal.error("Un seul referentiel a la fois : %s ignore", biblio.id)
            continue
        try:
            notions = lire_referentiel(biblio, niveaux)
            referentiel = biblio
        except (ErreurBibliotheque, OSError, KeyError, yaml.YAMLError) as err:
            journal.error("Referentiel %s ecarte : %s", biblio.id, err)
    for biblio in lues:
        if biblio.type == "referentiel":
            continue
        if niveau and biblio.niveaux and niveau not in biblio.niveaux:
            continue
        try:
            lire_contenus(biblio, notions)
            contenus.append(biblio)
        except (ErreurBibliotheque, OSError, yaml.YAMLError) as err:
            journal.error("Bibliotheque %s ecartee : %s", biblio.id, err)
    return Catalogue(notions=notions, referentiel=referentiel, contenus=contenus)


# --- recherche ------------------------------------------------------------------


def normaliser(texte: str) -> str:
    """Minuscules sans accents, pour comparer des mots."""
    decompose = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in decompose if not unicodedata.combining(c))


_MOT = re.compile(r"[a-z0-9]+")
_MOTS_VIDES = (
    "le la les un une des de du d l a au aux et ou en dans sur pour par avec que qui quoi est "
    "sont ce cette ces se sa son ses mon ma mes ton ta tes il elle on je tu nous vous ils "
    "elles pas ne plus y faire fait calculer exercice question reponse comment pourquoi aide"
)
_VIDES = frozenset(_MOTS_VIDES.split())


_SYMBOLES = {"%": " pourcent ", "√": " racine "}  # symboles qu'un eleve tape a la place du mot


def mots(texte: str) -> set[str]:
    for symbole, mot in _SYMBOLES.items():
        texte = texte.replace(symbole, mot)
    return {m for m in _MOT.findall(normaliser(texte)) if len(m) > 2 and m not in _VIDES}


def candidats(catalogue: Catalogue, texte: str, maximum: int = 25) -> list[Notion]:
    """Notions dont le titre, les mots-cles ou les declencheurs recoupent le texte, les plus proches d'abord."""
    cherches = mots(texte)
    if not cherches:
        return []
    scores: list[tuple[float, Notion]] = []
    for n in catalogue.notions.values():
        score = 0.0
        for cle in [*n.mots_cles, *catalogue.declencheurs(n.id)]:
            mc = mots(cle)
            if mc and mc <= cherches:
                score += 3
            else:
                score += len(mc & cherches)
        score += 1.5 * len(mots(n.titre) & cherches)
        score += 0.3 * len(mots(" ".join(n.attendus)) & cherches)
        if score > 0:
            scores.append((score, n))
    scores.sort(key=lambda s: -s[0])
    return [n for _, n in scores[:maximum]]


# --- rendu pour le prompt -----------------------------------------------------

_LIBELLES_DIRECTION = {
    "approche": "Approche",
    "a_privilegier": "À privilégier",
    "a_eviter": "À éviter",
    "vocabulaire": "Vocabulaire attendu",
    "redaction_attendue": "Rédaction attendue",
    "remarques": "Remarques",
}


def _liste(valeur: Any) -> list[str]:
    if isinstance(valeur, list):
        return [str(v).strip() for v in valeur if str(v).strip()]
    return [str(valeur).strip()] if str(valeur or "").strip() else []


def texte_direction(direction: dict[str, Any]) -> str:
    lignes = []
    for cle, valeur in direction.items():
        libelle = _LIBELLES_DIRECTION.get(cle, cle.replace("_", " ").capitalize())
        elements = _liste(valeur)
        if len(elements) == 1:
            lignes.append(f"- {libelle} : {elements[0]}")
        elif elements:
            lignes.append(f"- {libelle} :")
            lignes += [f"  - {e}" for e in elements]
    return "\n".join(lignes)


def texte_fiche(fiche: dict[str, Any], limite: int = 7000) -> str:
    """Met une fiche en texte pour le modele, en coupant si elle est trop longue."""
    blocs: list[str] = []
    if fiche.get("couverture"):
        blocs.append(f"Couverture partielle : {str(fiche['couverture']).strip()}")
    if fiche.get("essentiel"):
        blocs.append("Essentiel du cours :\n" + str(fiche["essentiel"]).strip())
    if fiche.get("methode"):
        blocs.append("Méthode :\n" + "\n".join(f"{i}. {e}" for i, e in enumerate(_liste(fiche["methode"]), 1)))
    if fiche.get("vocabulaire"):
        termes = []
        for v in fiche["vocabulaire"]:
            if isinstance(v, dict):
                termes.append(f"- {v.get('terme', '')} : {v.get('definition', '')}")
            else:
                termes.append(f"- {v}")
        blocs.append("Vocabulaire :\n" + "\n".join(termes))
    if fiche.get("erreurs_frequentes"):
        blocs.append("Erreurs fréquentes :\n" + "\n".join(f"- {e}" for e in _liste(fiche["erreurs_frequentes"])))
    exemple = fiche.get("exemple")
    if isinstance(exemple, dict) and exemple.get("enonce"):
        blocs.append(
            "Exemple résolu (à montrer seulement s'il diffère de l'exercice de l'élève) :\n"
            f"Énoncé : {str(exemple['enonce']).strip()}\nSolution : {str(exemple.get('solution', '')).strip()}"
        )
    exercices = [e for e in fiche.get("exercices") or [] if isinstance(e, dict) and e.get("enonce")]
    if exercices:
        lignes = ["Exercices d'entraînement (solutions réservées à toi : jamais avant que l'élève ait cherché) :"]
        for i, ex in enumerate(exercices, 1):
            lignes.append(f"{i}) {str(ex['enonce']).strip()}")
            for j, indice in enumerate(_liste(ex.get("indices")), 1):
                lignes.append(f"   Indice {j} : {indice}")
            if ex.get("solution"):
                lignes.append(f"   Solution : {str(ex['solution']).strip()}")
        blocs.append("\n".join(lignes))
    texte = "\n\n".join(blocs)
    if len(texte) > limite:
        texte = texte[:limite].rsplit("\n", 1)[0] + "\n[… fiche tronquée]"
    return texte
