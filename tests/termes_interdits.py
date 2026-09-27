"""Termes interdits (noms de troubles) : lus dans docs/spec/termes-interdits.txt (propriete SPEC).

Regles de recherche, fixees en tete de ce fichier de spec :
- insensible a la casse et aux accents (NFKD, diacritiques retires) ;
- apostrophes typographiques (U+2019, U+2018, U+02BC) remplacees par ' avant comparaison ;
- un terme sur plusieurs mots est cherche avec n'importe quelle suite d'espaces entre eux ;
- une ligne = un radical cherche en sous-chaine ;
- une ligne prefixee « mot: » est cherchee en mot entier ;
- lignes vides et commentaires (#) ignores.
Les tests n'ecrivent jamais ces termes en clair : ils les lisent ici.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

FICHIER = Path(__file__).resolve().parents[1] / "docs" / "spec" / "termes-interdits.txt"
PREFIXE_MOT = "mot:"
APOSTROPHES = str.maketrans(dict.fromkeys("\u2019\u2018\u02bc", "'"))


@dataclass(frozen=True)
class Terme:
    texte: str  # tel qu'ecrit dans le fichier, sans le prefixe
    mot_entier: bool
    motif: re.Pattern[str]


def normaliser(texte: str) -> str:
    """Minuscules, sans accents (NFKD), apostrophes typographiques ramenees a l'apostrophe droite."""
    decompose = unicodedata.normalize("NFKD", texte.casefold().translate(APOSTROPHES))
    return "".join(c for c in decompose if not unicodedata.combining(c))


def termes_interdits() -> list[Terme]:
    termes = []
    for brute in FICHIER.read_text(encoding="utf-8").splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#"):
            continue
        mot_entier = ligne.startswith(PREFIXE_MOT)
        texte = ligne[len(PREFIXE_MOT) :].strip() if mot_entier else ligne
        echappe = r"\s+".join(re.escape(mot) for mot in normaliser(texte).split())
        motif = re.compile(rf"(?<![a-z0-9]){echappe}(?![a-z0-9])" if mot_entier else echappe)
        termes.append(Terme(texte, mot_entier, motif))
    return termes


def trouver_terme(texte: str, termes: list[Terme]) -> str | None:
    """Premier terme present dans le texte (selon les regles ci-dessus), ou None."""
    t = normaliser(texte)
    return next((terme.texte for terme in termes if terme.motif.search(t)), None)
