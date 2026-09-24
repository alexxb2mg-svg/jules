"""Profil de l'eleve (profils/<id>.yaml) et assemblage du prompt systeme.

Ordre d'assemblage (le dernier bloc prime en cas de conflit) :
  1. persona (qui parle, comment)
  2. profil de l'eleve
  3. pedagogie + format (consignes communes, independantes de la persona)
  4. contributions des modules (mode choisi, memoire...)
  5. securite (non negociable, toujours en dernier)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jules.persona import Persona
from jules.texte import GENRE_DEFAUT, normaliser_genre, remplir

CONSIGNES_COMMUNES = ("pedagogie.md", "format.md")
CONSIGNES_FINALES = ("securite.md",)


@dataclass
class Profil:
    prenom: str
    classe: str
    parent: str = "ses parents"
    genre: str = GENRE_DEFAUT
    details: dict[str, Any] = field(default_factory=dict)

    def variables(self) -> dict[str, str]:
        return {"prenom": self.prenom, "classe": self.classe, "parent": self.parent}

    def texte(self) -> str:
        lignes = [f"- Prénom : {self.prenom}", f"- Classe : {self.classe}"]
        if self.genre != GENRE_DEFAUT:
            lignes.append(f"- Genre : {self.genre.replace('garcon', 'garçon')}")
        for cle, valeur in self.details.items():
            if valeur in (None, "", [], {}):
                continue
            if isinstance(valeur, list):
                valeur = ", ".join(str(v) for v in valeur)
            lignes.append(f"- {cle.replace('_', ' ').capitalize()} : {valeur}")
        return "\n".join(lignes)


def charger_profil(chemin: Path) -> Profil:
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    prenom = str(brut.pop("prenom", "") or "l'élève")
    classe = str(brut.pop("classe", "") or "non précisée (demande-la gentiment au début)")
    parent = str(brut.pop("parent", "") or "ses parents")
    genre = normaliser_genre(brut.pop("genre", GENRE_DEFAUT))
    return Profil(prenom=prenom, classe=classe, parent=parent, genre=genre, details=brut)


def lire_consignes(dossier: Path, noms: tuple[str, ...], profil: Profil) -> list[tuple[str, str]]:
    sections = []
    for nom in noms:
        chemin = dossier / nom
        if chemin.is_file():
            texte = remplir(chemin.read_text(encoding="utf-8"), profil.variables(), profil.genre)
            sections.append((chemin.stem.capitalize(), texte.strip()))
    return sections


def assembler(
    persona: Persona,
    profil: Profil,
    dossier_consignes: Path,
    contributions: list[tuple[str, str]],
) -> str:
    blocs: list[tuple[str, str]] = list(persona.sections)
    blocs.append(("Profil de l'élève", profil.texte()))
    blocs += lire_consignes(dossier_consignes, CONSIGNES_COMMUNES, profil)
    blocs += [(titre, remplir(texte, profil.variables(), profil.genre)) for titre, texte in contributions if texte]
    blocs += lire_consignes(dossier_consignes, CONSIGNES_FINALES, profil)
    return "\n\n".join(f"# {titre}\n{texte.strip()}" for titre, texte in blocs if texte.strip())
