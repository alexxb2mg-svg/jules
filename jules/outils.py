"""Outils : petites applications qui s'ouvrent dans une leçon (voir docs/OUTILS-CONTRAT.md).

Un outil est un dossier `outils/<id>/` qui se présente dans `outil.yaml` :

    id: frise-chronologique
    titre: "Frise chronologique"
    matieres: [histoire]
    niveaux: [6e, 5e, 4e, 3e]
    entree: index.html
    actions: [afficher_periode, exercice_remettre_dans_l_ordre]
    evenements: [evenement_consulte, reponse_proposee]
    permissions: []
    auteurs: ["pseudo-github"]
    licence: MIT

Ce module ne fait que lire, vérifier et lister les fichiers d'un outil : il ne sert aucune page
(voir `jules/modules/outils.py` pour ça) et ne parle jamais au modèle d'IA.

Contrôles automatiques (avant même la relecture humaine, section 4 de docs/VISION.md et
docs/OUTILS-CONTRAT.md) :
  - fiche conforme (voir `lire_outil`) ;
  - aucune permission qui ne soit pas explicitement validée ici (`PERMISSIONS_CONNUES`) ;
  - aucune adresse externe ni motif réseau/exécution dynamique dans le code de l'outil (voir
    `_controler_code`) : ceci ne remplace pas la relecture humaine, seulement un premier filtre.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

journal = logging.getLogger("jules.outils")

# Aucune permission n'est encore validée (étape 3 : trois outils de référence, sans accès
# particulier). Ajouter une permission ici est une décision à part, prise avec les mainteneurs
# (section 4 de docs/VISION.md : justifiée, validée, puis acceptée par le parent).
PERMISSIONS_CONNUES: frozenset[str] = frozenset()

_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_IDENTIFIANT = re.compile(r"^[a-z][a-z0-9_]*$")
TAILLE_MAX_FICHIER = 200_000  # octets, par fichier de l'outil (fiche ou code)
EXTENSIONS_CODE = (".html", ".js", ".css")

# Premier filtre automatique : un outil ne doit ni appeler le réseau ni exécuter du code
# dynamique (section 4 de docs/VISION.md, "Contrôles automatiques"). Ce n'est PAS la sandbox :
# la vraie protection est l'iframe sandbox="allow-scripts" (sans allow-same-origin) et la CSP
# servies par jules/modules/outils.py. Ce filtre attrape les cas évidents avant la relecture.
_MOTIFS_INTERDITS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"https?://"), "adresse externe (http/https)"),
    (re.compile(r"\bfetch\s*\("), "fetch("),
    (re.compile(r"XMLHttpRequest"), "XMLHttpRequest"),
    (re.compile(r"\bWebSocket\b"), "WebSocket"),
    (re.compile(r"\beval\s*\("), "eval("),
    (re.compile(r"\bnew\s+Function\s*\("), "new Function("),
    (re.compile(r"\bimport\s*\("), "import() dynamique"),
    (re.compile(r"\bnew\s+Worker\s*\("), "Worker("),
    (re.compile(r"navigator\.sendBeacon"), "navigator.sendBeacon"),
    (re.compile(r"document\.cookie"), "document.cookie"),
)


class ErreurOutil(ValueError):
    pass


@dataclass
class Outil:
    id: str
    titre: str
    dossier: Path
    entree: str
    matieres: list[str] = field(default_factory=list)
    niveaux: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    evenements: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    auteurs: list[str] = field(default_factory=list)
    licence: str = ""

    def publique(self) -> dict[str, Any]:
        """Ce que l'interface (et Jules) peuvent savoir d'un outil : jamais le contenu des fichiers."""
        return {
            "id": self.id,
            "titre": self.titre,
            "matieres": self.matieres,
            "niveaux": self.niveaux,
            "entree": self.entree,
            "actions": self.actions,
            "evenements": self.evenements,
        }


def _lire_yaml(chemin: Path) -> dict[str, Any]:
    if chemin.stat().st_size > TAILLE_MAX_FICHIER:
        raise ErreurOutil(f"{chemin.name} : fichier trop gros")
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    if not isinstance(brut, dict):
        raise ErreurOutil(f"{chemin.name} : un objet YAML est attendu")
    return brut


def _liste_str(brut: dict[str, Any], champ: str) -> list[str]:
    valeur = brut.get(champ) or []
    if not isinstance(valeur, list) or not all(isinstance(v, str) for v in valeur):
        raise ErreurOutil(f"{champ} : une liste de textes est attendue")
    return list(valeur)


def _controler_identifiants(valeurs: list[str], champ: str) -> None:
    for v in valeurs:
        if not _IDENTIFIANT.match(v):
            raise ErreurOutil(f"{champ} : identifiant invalide {v!r} (attendu : minuscules_et_chiffres)")


def _controler_code(dossier: Path) -> None:
    """Premier filtre automatique sur le code de l'outil (voir le commentaire sur _MOTIFS_INTERDITS)."""
    for chemin in sorted(dossier.rglob("*")):
        if not chemin.is_file() or chemin.suffix.lower() not in EXTENSIONS_CODE:
            continue
        if chemin.stat().st_size > TAILLE_MAX_FICHIER:
            raise ErreurOutil(f"{chemin.relative_to(dossier)} : fichier trop gros")
        texte = chemin.read_text(encoding="utf-8", errors="replace")
        for motif, nom in _MOTIFS_INTERDITS:
            if motif.search(texte):
                raise ErreurOutil(f"{chemin.relative_to(dossier)} : motif interdit ({nom})")


def _controler_entree(dossier: Path, entree: str) -> None:
    chemin = Path(entree)
    if chemin.is_absolute() or ".." in chemin.parts:
        raise ErreurOutil(f"entree invalide : {entree!r}")
    if chemin.suffix.lower() != ".html":
        raise ErreurOutil(f"entree doit être une page .html : {entree!r}")
    if not (dossier / chemin).is_file():
        raise ErreurOutil(f"fichier d'entrée introuvable : {entree}")


def lire_outil(dossier: Path) -> Outil:
    """Lit et vérifie `outil.yaml`, puis contrôle le code (voir `_controler_code`)."""
    fichier = dossier / "outil.yaml"
    if not fichier.is_file():
        raise ErreurOutil(f"{dossier.name} : outil.yaml manquant")
    brut = _lire_yaml(fichier)
    identifiant = str(brut.get("id") or "")
    if identifiant != dossier.name:
        raise ErreurOutil(f"{dossier.name} : l'id ({identifiant!r}) doit être le nom du dossier")
    if not _ID.match(identifiant):
        raise ErreurOutil(f"{identifiant} : identifiant invalide (attendu : minuscules-et-tirets)")
    titre = str(brut.get("titre") or "").strip()
    if not titre:
        raise ErreurOutil(f"{identifiant} : titre manquant")
    entree = str(brut.get("entree") or "index.html")
    try:
        _controler_entree(dossier, entree)
    except ErreurOutil as err:
        raise ErreurOutil(f"{identifiant} : {err}") from err
    actions = _liste_str(brut, "actions")
    evenements = _liste_str(brut, "evenements")
    try:
        _controler_identifiants(actions, "actions")
        _controler_identifiants(evenements, "evenements")
    except ErreurOutil as err:
        raise ErreurOutil(f"{identifiant} : {err}") from err
    permissions = _liste_str(brut, "permissions")
    inconnues = [p for p in permissions if p not in PERMISSIONS_CONNUES]
    if inconnues:
        raise ErreurOutil(f"{identifiant} : permission(s) non validée(s) : {', '.join(inconnues)}")
    licence = str(brut.get("licence") or "")
    if not licence:
        raise ErreurOutil(f"{identifiant} : licence manquante")
    try:
        _controler_code(dossier)
    except ErreurOutil as err:
        raise ErreurOutil(f"{identifiant} : {err}") from err
    return Outil(
        id=identifiant,
        titre=titre,
        dossier=dossier,
        entree=entree,
        matieres=_liste_str(brut, "matieres"),
        niveaux=[str(n) for n in brut.get("niveaux") or []],
        actions=actions,
        evenements=evenements,
        permissions=permissions,
        auteurs=[str(a) for a in brut.get("auteurs") or []],
        licence=licence,
    )


def charger_outils(racine: Path, dossiers_extensions: list[Path] | None = None) -> dict[str, Outil]:
    """Charge tous les outils de `racine` (dossier `outils/`), puis ceux des extensions actives
    (`dossiers_extensions`, voir `dossiers_outils` de jules/extensions.py), vérifiés de la même façon.

    Un outil illisible (fiche invalide, motif interdit dans le code...) est écarté et journalisé :
    Jules continue sans lui, comme pour une bibliothèque (voir `jules/bibliotheques.py`). Un id
    déjà chargé l'emporte sur un doublon venu ensuite.
    """
    outils: dict[str, Outil] = {}
    dossiers = sorted(p for p in racine.iterdir() if p.is_dir()) if racine.is_dir() else []
    for dossier in [*dossiers, *(dossiers_extensions or [])]:
        if dossier.name in outils:
            journal.error("Outil %s écarté : id déjà fourni ailleurs", dossier.name)
            continue
        try:
            outils[dossier.name] = lire_outil(dossier)
        except (ErreurOutil, OSError, yaml.YAMLError) as err:
            journal.error("Outil %s écarté : %s", dossier.name, err)
    return outils
