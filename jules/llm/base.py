"""Interface commune des moteurs d'IA.

Un moteur recoit : un prompt systeme, l'historique (tours), un nom de modele logique
('principal' ou 'rapide'), et renvoie du texte. Rien d'autre ne connait le fournisseur.
"""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class ErreurLLM(RuntimeError):
    pass


@dataclass
class Tour:
    role: str  # 'user' ou 'assistant'
    texte: str
    images: list[Path] = field(default_factory=list)


class MoteurLLM(Protocol):
    def repondre(self, systeme: str, tours: list[Tour], modele: str = "principal") -> str: ...


MEDIAS = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif"}
TEXTE_PHOTO_SEULE = "(photo envoyée sans texte)"
_REFLEXION = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def type_media(chemin: Path) -> str:
    return MEDIAS.get(chemin.suffix.lower().lstrip("."), "image/jpeg")


def image_base64(chemin: Path) -> str:
    return base64.b64encode(chemin.read_bytes()).decode("ascii")


def nom_modele(reglages: dict[str, Any], logique: str) -> str:
    """Nom reel du modele pour un role logique ('principal', 'rapide')."""
    modeles = reglages.get("modeles") or {}
    nom = modeles.get(logique) or modeles.get("principal")
    if not nom:
        raise ErreurLLM("llm.modeles.principal manquant dans la configuration")
    return str(nom)


def cle_api(reglages: dict[str, Any], obligatoire: bool = True) -> str:
    """Lit la cle dans la variable d'environnement nommee par `cle_env` (jamais dans un fichier suivi)."""
    nom = str(reglages.get("cle_env") or "")
    valeur = os.environ.get(nom, "") if nom else ""
    if obligatoire and not valeur:
        raise ErreurLLM(f"Cle API absente : definir la variable {nom or '(llm.cle_env non renseigne)'} dans .env")
    return valeur


def nettoyer(texte: str) -> str:
    """Retire les blocs de reflexion <think>...</think> de certains modeles locaux."""
    return _REFLEXION.sub("", texte or "").strip()
