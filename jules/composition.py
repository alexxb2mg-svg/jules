"""Profil de l'eleve (profils/<id>.yaml) et assemblage du prompt systeme.

Ordre d'assemblage (le dernier bloc prime en cas de conflit) :
  1. persona (qui parle, comment)
  2. profil de l'eleve
  3. pedagogie + format (consignes communes, independantes de la persona)
  3b. expression adaptee (consignes des amenagements actifs, docs/spec/ADAPTATIONS.md EX-004/005)
  4. contributions des modules (mode choisi, memoire...)
  5. securite (non negociable, toujours en dernier)

Amenagements : le profil liste des identifiants (`amenagements: [amenagement-test-a, ...]`). Ces
identifiants ne partent JAMAIS chez le fournisseur du modele : ils sont retires des champs libres du
profil, et le modele ne recoit que le texte des consignes d'expression correspondantes
(consignes/amenagements/<id>.md), sous un titre neutre.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jules.persona import Persona
from jules.texte import GENRE_DEFAUT, normaliser_genre, remplir

journal = logging.getLogger("jules")

CONSIGNES_COMMUNES = ("pedagogie.md", "format.md")
CONSIGNES_FINALES = ("securite.md",)
DOSSIER_AMENAGEMENTS = "amenagements"  # sous consignes/
TITRE_EXPRESSION = "Expression adaptée"
MOTIF_ID_AMENAGEMENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Profil:
    prenom: str
    classe: str
    parent: str = "ses parents"
    genre: str = GENRE_DEFAUT
    details: dict[str, Any] = field(default_factory=dict)
    amenagements: list[str] = field(default_factory=list)  # identifiants : jamais dans le prompt

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
    amenagements = lire_ids_amenagements(brut.pop("amenagements", None))
    brut.pop("preferences", None)  # reglages d'affichage du parent (EX-108) : jamais dans le prompt
    details = effacer_ids(brut, amenagements)
    return Profil(prenom=prenom, classe=classe, parent=parent, genre=genre, details=details, amenagements=amenagements)


def lire_ids_amenagements(valeur: Any) -> list[str]:
    """`amenagements` du profil -> liste d'identifiants sans doublon (une chaine seule est acceptee)."""
    if valeur in (None, "", [], {}):
        return []
    brutes = valeur if isinstance(valeur, list) else [valeur]
    ids: list[str] = []
    for brute in brutes:
        ident = str(brute).strip().lower()
        if ident and ident not in ids:
            ids.append(ident)
    return ids


def effacer_ids(valeur: Any, ids: list[str]) -> Any:
    """Retire les identifiants d'amenagement d'un champ libre (texte, liste ou dictionnaire imbriques)."""
    if not ids:
        return valeur
    if isinstance(valeur, str):
        texte = valeur
        for ident in sorted(ids, key=len, reverse=True):
            # mot entier : l'identifiant « lecture » n'ampute pas « relecture »
            texte = re.sub(rf"(?<![\w-]){re.escape(ident)}(?![\w-])", "", texte, flags=re.IGNORECASE)
        return re.sub(r"[ \t]{2,}", " ", texte).strip()
    if isinstance(valeur, list):
        return [v for v in (effacer_ids(v, ids) for v in valeur) if v not in ("", None)]
    if isinstance(valeur, dict):
        return {
            cle: effacer_ids(v, ids)
            for cle, v in valeur.items()
            if str(cle).strip().lower().replace("_", "-") not in ids
        }
    return valeur


def consignes_amenagements(dossier: Path, profil: Profil) -> list[tuple[str, str]]:
    """Un seul bloc, titre neutre, avec les consignes d'expression de chaque amenagement actif (EX-005).

    Ni l'identifiant ni le nom de l'amenagement ne sont repris : seul le corps du fichier (apres son
    en-tete YAML) part dans le prompt. Un identifiant inconnu ou mal forme est ignore et journalise.
    """
    textes = []
    for ident in profil.amenagements:
        chemin = dossier / DOSSIER_AMENAGEMENTS / f"{ident}.md"
        if not MOTIF_ID_AMENAGEMENT.match(ident) or not chemin.is_file():
            journal.warning("Amenagement inconnu dans le profil, ignore (voir consignes/%s/)", DOSSIER_AMENAGEMENTS)
            continue
        corps = corps_sans_entete(chemin.read_text(encoding="utf-8"))
        if corps:
            textes.append(remplir(corps, profil.variables(), profil.genre))
    return [(TITRE_EXPRESSION, "\n".join(textes))] if textes else []


def corps_sans_entete(texte: str) -> str:
    if texte.startswith("---"):
        _, _, texte = texte.split("---", 2)
    return texte.strip()


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
    blocs += consignes_amenagements(dossier_consignes, profil)
    blocs += [(titre, remplir(texte, profil.variables(), profil.genre)) for titre, texte in contributions if texte]
    blocs += lire_consignes(dossier_consignes, CONSIGNES_FINALES, profil)
    return "\n\n".join(f"# {titre}\n{texte.strip()}" for titre, texte in blocs if texte.strip())
