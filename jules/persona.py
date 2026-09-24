"""Chargement de la persona : persona/<id>/persona.yaml + fichiers de consignes .md.

Changer de personnalite = creer un autre dossier persona/<id>/ et changer `persona:`
dans la configuration. Peaufiner = editer les .md, pris en compte au message suivant.
Les textes acceptent les variables du profil ({prenom}...) et les accords {{elle|il|iel}}.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jules.texte import GENRE_DEFAUT, remplir


@dataclass
class Persona:
    id: str
    nom: str
    accueil: str
    couleurs: dict[str, str]
    avatar: Path | None
    sections: list[tuple[str, str]] = field(default_factory=list)
    reglages: dict[str, Any] = field(default_factory=dict)

    def publique(self) -> dict[str, Any]:
        """Ce que l'interface a le droit de connaitre (pas les consignes)."""
        return {
            "id": self.id,
            "nom": self.nom,
            "accueil": self.accueil,
            "couleurs": self.couleurs,
            "avatar": bool(self.avatar),
        }


class ErreurPersona(RuntimeError):
    pass


def _dans(dossier: Path, relatif: str) -> Path:
    """Chemin d'un fichier de la persona, refuse s'il sort du dossier (ex. ../../secret)."""
    chemin = (dossier / relatif).resolve()
    if chemin.parent != dossier.resolve():
        raise ErreurPersona(f"Fichier hors du dossier de la persona : {relatif}")
    return chemin


def charger_persona(dossier: Path, variables: dict[str, str] | None = None, genre: str = GENRE_DEFAUT) -> Persona:
    fiche = dossier / "persona.yaml"
    if not fiche.is_file():
        raise ErreurPersona(f"Persona introuvable : {fiche}")
    brut = yaml.safe_load(fiche.read_text(encoding="utf-8")) or {}
    variables = variables or {}
    sections: list[tuple[str, str]] = []
    for entree in brut.get("consignes") or []:
        chemin = _dans(dossier, str(entree["fichier"]))
        if not chemin.is_file():
            raise ErreurPersona(f"Fichier de persona manquant : {entree['fichier']}")
        texte = remplir(chemin.read_text(encoding="utf-8"), variables, genre)
        sections.append((str(entree.get("titre") or chemin.stem), texte.strip()))
    avatar = _dans(dossier, str(brut.get("avatar") or "avatar.png"))
    return Persona(
        id=dossier.name,
        nom=str(brut.get("nom") or dossier.name),
        accueil=remplir(str(brut.get("accueil") or ""), variables, genre),
        couleurs=dict(brut.get("couleurs") or {}),
        avatar=avatar if avatar.is_file() else None,
        sections=sections,
        reglages=dict(brut.get("reglages") or {}),
    )
