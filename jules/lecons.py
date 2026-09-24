"""Lecons : une notion du programme expliquee en blocs (objectifs, texte, exemple, exercice...).

Une lecon vit dans une bibliotheque de type `lecons` :
    bibliotheque/<id>/bibliotheque.yaml            (type: lecons)
    bibliotheque/<id>/lecons/<matiere>/<notion>.yaml

Format complet : bibliotheque/SCHEMA-LECON.md et docs/COURS-CONTRAT.md.

Regle de fond : la reponse attendue d'un exercice ne quitte jamais le serveur avant une tentative
de l'eleve. `Bloc.public()` retire les champs reserves au serveur (CHAMPS_SERVEUR).

Ce fichier ne fait que lire, verifier et corriger : il ne parle ni au modele d'IA ni a l'interface.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jules.bibliotheques import (
    LICENCES_LIBRES,
    TAILLE_MAX_FICHIER,
    Bibliotheque,
    ErreurBibliotheque,
    Notion,
    lire_identite,
    normaliser,
)

journal = logging.getLogger("jules.lecons")

TYPES_BLOCS = ("objectifs", "texte", "exemple", "exercice", "question_ouverte", "synthese", "outil")
FORMES_EXERCICE = ("nombre", "reponse_courte", "qcm")
CHAMPS_SERVEUR = ("reponse", "reponses_acceptees", "tolerance", "explication", "criteres")
TENTATIVES_AVANT_CORRECTION = 3
BLOCS_MIN = 3
BLOCS_MAX = 20
TOLERANCE_DEFAUT = 1e-9


class ErreurLecon(ValueError):
    """Lecon illisible ou non conforme : le message dit quoi corriger, en francais."""


@dataclass
class Bloc:
    type: str
    donnees: dict[str, Any] = field(default_factory=dict)

    def public(self) -> dict[str, Any]:
        """Ce qui peut partir vers le navigateur : jamais la reponse, l'explication ni les criteres."""
        return {"type": self.type, **{k: v for k, v in self.donnees.items() if k not in CHAMPS_SERVEUR}}


@dataclass
class Lecon:
    notion: str
    titre: str
    matiere: str
    niveau: str
    bibliotheque: str
    statut: str
    licence: str
    duree_minutes: int = 0
    blocs: list[Bloc] = field(default_factory=list)
    sources: list[dict[str, str]] = field(default_factory=list)
    avertissement: str = ""

    def publique(self) -> dict[str, Any]:
        return {
            "notion": self.notion,
            "titre": self.titre,
            "matiere": self.matiere,
            "niveau": self.niveau,
            "statut": self.statut,
            "avertissement": self.avertissement,
            "duree_minutes": self.duree_minutes,
            "sources": self.sources,
            "blocs": [{"index": i, **b.public()} for i, b in enumerate(self.blocs)],
        }


# --- lecture et verification ---------------------------------------------------


def _verifier_bloc(bloc: dict[str, Any], position: int, nom: str) -> Bloc:
    ou = f"{nom}, bloc {position + 1}"
    if not isinstance(bloc, dict):
        raise ErreurLecon(f"{ou} : un objet est attendu")
    type_ = str(bloc.get("type") or "")
    if type_ not in TYPES_BLOCS:
        raise ErreurLecon(f"{ou} : type {type_!r} inconnu (attendu : {', '.join(TYPES_BLOCS)})")
    donnees = {k: v for k, v in bloc.items() if k != "type"}
    if type_ == "exercice":
        forme = str(donnees.get("forme") or "")
        if forme not in FORMES_EXERCICE:
            raise ErreurLecon(f"{ou} : forme {forme!r} inconnue (attendu : {', '.join(FORMES_EXERCICE)})")
        if donnees.get("reponse") in (None, ""):
            raise ErreurLecon(f"{ou} : un exercice doit avoir une reponse")
        if not str(donnees.get("enonce") or "").strip():
            raise ErreurLecon(f"{ou} : un exercice doit avoir un enonce")
        if forme == "qcm":
            choix = donnees.get("choix") or []
            if not isinstance(choix, list) or len(choix) < 2:
                raise ErreurLecon(f"{ou} : un qcm doit proposer au moins deux choix")
            if _index_qcm(donnees) is None:
                raise ErreurLecon(f"{ou} : la reponse du qcm doit etre un des choix (ou son numero, a partir de 0)")
        if forme == "nombre" and _nombre(donnees.get("reponse")) is None:
            raise ErreurLecon(f"{ou} : la reponse d'un exercice 'nombre' doit etre un nombre")
        provisoire = Bloc(type_, donnees)
        for indice in donnees.get("indices") or []:
            if forme != "qcm" and contient_la_reponse(str(indice), provisoire):
                raise ErreurLecon(f"{ou} : un indice contient la reponse ({indice!r})")
    if type_ == "question_ouverte" and not str(donnees.get("question") or "").strip():
        raise ErreurLecon(f"{ou} : une question ouverte doit avoir une question")
    if type_ == "synthese" and not str(donnees.get("consigne") or "").strip():
        raise ErreurLecon(f"{ou} : une synthese doit avoir une consigne")
    return Bloc(type_, donnees)


def lire_lecon(chemin: Path, notions: dict[str, Notion], bibliotheque: Bibliotheque) -> Lecon:
    """Lit et verifie une lecon. Leve ErreurLecon avec un message clair si elle n'est pas conforme."""
    nom = chemin.name
    if chemin.stat().st_size > TAILLE_MAX_FICHIER:
        raise ErreurLecon(f"{nom} : fichier trop gros")
    try:
        brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as err:
        raise ErreurLecon(f"{nom} : YAML illisible ({err})") from err
    if not isinstance(brut, dict):
        raise ErreurLecon(f"{nom} : un objet YAML est attendu")
    identifiant = str(brut.get("notion") or "")
    notion = notions.get(identifiant)
    if notion is None:
        raise ErreurLecon(f"{nom} : notion {identifiant!r} inconnue du referentiel")
    titre = str(brut.get("titre") or "").strip()
    if not titre:
        raise ErreurLecon(f"{nom} : titre manquant")
    licence = str(brut.get("licence") or bibliotheque.licence)
    if licence not in LICENCES_LIBRES:
        raise ErreurLecon(f"{nom} : licence {licence!r} non libre ou inconnue")
    sources = brut.get("sources") or []
    if not isinstance(sources, list) or not sources:
        raise ErreurLecon(f"{nom} : au moins une source est attendue")
    blocs_bruts = brut.get("blocs") or []
    if not isinstance(blocs_bruts, list) or not BLOCS_MIN <= len(blocs_bruts) <= BLOCS_MAX:
        raise ErreurLecon(f"{nom} : entre {BLOCS_MIN} et {BLOCS_MAX} blocs attendus")
    blocs = [_verifier_bloc(b, i, nom) for i, b in enumerate(blocs_bruts)]
    return Lecon(
        notion=identifiant,
        titre=titre,
        matiere=notion.matiere,
        niveau=notion.niveau,
        bibliotheque=bibliotheque.id,
        statut=bibliotheque.statut,
        licence=licence,
        duree_minutes=int(brut.get("duree_minutes") or 0),
        blocs=blocs,
        sources=[{k: str(v) for k, v in s.items()} for s in sources if isinstance(s, dict)],
        avertissement=bibliotheque.avertissement,
    )


def charger_lecons(racine: Path, ids: list[str], notions: dict[str, Notion]) -> dict[str, Lecon]:
    """Lecons des bibliotheques citees, par ordre de priorite (une notion = une lecon).

    Une lecon non conforme est signalee dans le journal et ecartee : Jules continue sans elle.
    """
    lecons: dict[str, Lecon] = {}
    for identifiant in ids:
        try:
            biblio = lire_identite(racine / identifiant)
        except (ErreurBibliotheque, OSError, yaml.YAMLError) as err:
            journal.error("Bibliotheque de lecons %s ecartee : %s", identifiant, err)
            continue
        if biblio.type != "lecons":
            journal.error("Bibliotheque %s : type %r, 'lecons' attendu", identifiant, biblio.type)
            continue
        for fichier in sorted((biblio.dossier / "lecons").rglob("*.yaml")):
            try:
                lecon = lire_lecon(fichier, notions, biblio)
            except (ErreurLecon, OSError) as err:
                journal.error("Lecon ecartee : %s", err)
                continue
            lecons.setdefault(lecon.notion, lecon)
    return lecons


# --- correction -----------------------------------------------------------------

_NOMBRE = re.compile(r"-?\d+(?:[.,]\d+)?")


def _nombre(valeur: object) -> float | None:
    if isinstance(valeur, bool):
        return None
    if isinstance(valeur, int | float):
        return float(valeur)
    texte = str(valeur or "").replace("\u202f", "").replace("\xa0", "").replace(" ", "")
    trouve = _NOMBRE.search(texte)
    if not trouve:
        return None
    try:
        return float(trouve.group(0).replace(",", "."))
    except ValueError:
        return None


def _texte(valeur: object) -> str:
    """Casse, accents, espaces multiples et ponctuation finale ignores."""
    return re.sub(r"\s+", " ", normaliser(str(valeur or ""))).strip().rstrip(".!?;: ").strip()


def _index_qcm(donnees: dict[str, Any]) -> int | None:
    choix = [str(c) for c in donnees.get("choix") or []]
    reponse = donnees.get("reponse")
    if isinstance(reponse, int) and not isinstance(reponse, bool):
        return reponse if 0 <= reponse < len(choix) else None
    return choix.index(str(reponse)) if str(reponse) in choix else None


def verifier_reponse(bloc: Bloc, reponse: object) -> bool | None:
    """Juste / faux pour un exercice ; None s'il n'y a pas de correction automatique."""
    if bloc.type != "exercice":
        return None
    d = bloc.donnees
    forme = d.get("forme")
    if forme == "nombre":
        attendu, donne = _nombre(d.get("reponse")), _nombre(reponse)
        if attendu is None or donne is None:
            return False
        return abs(attendu - donne) <= float(d.get("tolerance") or TOLERANCE_DEFAUT)
    if forme == "reponse_courte":
        admises = {_texte(d.get("reponse"))} | {_texte(v) for v in d.get("reponses_acceptees") or []}
        return _texte(reponse) in admises
    if forme == "qcm":
        index = _index_qcm(d)
        choix = [str(c) for c in d.get("choix") or []]
        if isinstance(reponse, int) and not isinstance(reponse, bool):
            return reponse == index
        texte = str(reponse).strip()
        if texte.isdigit():
            return int(texte) == index
        return index is not None and _texte(texte) == _texte(choix[index])
    return None


def contient_la_reponse(texte: str, bloc: Bloc) -> bool:
    """Vrai si `texte` donne la reponse attendue d'un exercice (garde-fou avant d'afficher Jules)."""
    if bloc.type != "exercice":
        return False
    d = bloc.donnees
    forme = d.get("forme")
    if forme == "nombre":
        attendu = _nombre(d.get("reponse"))
        if attendu is None:
            return False
        tolerance = float(d.get("tolerance") or TOLERANCE_DEFAUT)
        return any(abs(float(n.replace(",", ".")) - attendu) <= tolerance for n in _NOMBRE.findall(texte))
    if forme == "reponse_courte":
        propre = f" {_texte(texte)} "
        admises = [_texte(d.get("reponse"))] + [_texte(v) for v in d.get("reponses_acceptees") or []]
        return any(a and f" {a} " in propre for a in admises)
    if forme == "qcm":
        index = _index_qcm(d)
        if index is None:
            return False
        choix = str((d.get("choix") or [])[index])
        return len(_texte(choix)) > 3 and _texte(choix) in _texte(texte)
    return False
