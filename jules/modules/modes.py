"""Module 'modes' : modes de travail (aide aux devoirs, quiz, fiche...).

Un mode = un fichier consignes/modes/<id>.md avec un en-tete YAML :
    ---
    nom: Aide aux devoirs
    icone: ✏️
    description: Je t'aide à trouver par toi-même
    ordre: 1
    ---
    <consignes du mode>
Ajouter un mode = deposer un fichier. Aucun code a toucher.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jules.modules.base import Module
from jules.stockage import Conversation

MODE_DEFAUT = "aide-devoirs"


@dataclass
class Mode:
    id: str
    nom: str
    icone: str
    description: str
    ordre: int
    consignes: str


def lire_mode(chemin: Path) -> Mode:
    texte = chemin.read_text(encoding="utf-8")
    entete: dict[str, Any] = {}
    if texte.startswith("---"):
        _, brut, texte = texte.split("---", 2)
        entete = yaml.safe_load(brut) or {}
    return Mode(
        id=chemin.stem,
        nom=str(entete.get("nom") or chemin.stem),
        icone=str(entete.get("icone") or ""),
        description=str(entete.get("description") or ""),
        ordre=int(entete.get("ordre") or 99),
        consignes=texte.strip(),
    )


def lister_modes(dossier: Path) -> list[Mode]:
    return sorted((lire_mode(p) for p in dossier.glob("*.md")), key=lambda m: (m.ordre, m.nom))


class Brique(Module):
    id = "modes"
    titre = "Mode de travail choisi"

    @property
    def dossier(self) -> Path:
        return self.tuteur.config.dossier_consignes / "modes"

    def mode(self, identifiant: str) -> Mode | None:
        chemin = self.dossier / f"{identifiant}.md"
        return lire_mode(chemin) if chemin.is_file() else None

    def valider(self, identifiant: str | None) -> str:
        return identifiant if identifiant and self.mode(identifiant) else MODE_DEFAUT

    def contribution(self, conv: Conversation) -> str | None:
        mode = self.mode(conv.mode) or self.mode(MODE_DEFAUT)
        if mode is None:
            return None
        return f"Mode : {mode.nom}\n{mode.consignes}"

    def infos_interface(self) -> dict[str, Any]:
        return {
            "modes": [
                {"id": m.id, "nom": m.nom, "icone": m.icone, "description": m.description}
                for m in lister_modes(self.dossier)
            ]
        }
