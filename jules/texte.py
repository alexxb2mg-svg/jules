"""Remplissage des textes (persona, consignes, modes) a partir du profil de l'eleve.

Deux mecanismes, appliques dans cet ordre :

1. Accords selon le genre de l'eleve : ``{{elle|il|iel}}`` donne la 1re forme pour
   ``genre: fille``, la 2e pour ``garcon`` et la 3e pour ``neutre``. Avec deux formes
   seulement (``{{une collégienne|un collégien}}``), la forme neutre s'ecrit en toutes
   lettres a partir des deux (``une collégienne ou un collégien``).
2. Variables du profil : ``{prenom}``, ``{classe}``, ``{parent}``... Une accolade inconnue
   est laissee telle quelle (pas d'erreur sur un texte qui contient une accolade).
"""

from __future__ import annotations

import re

GENRES = ("fille", "garcon", "neutre")
GENRE_DEFAUT = "neutre"

_ACCORD = re.compile(r"\{\{([^{}|]*(?:\|[^{}|]*){1,2})\}\}")
_ALIAS = {
    "f": "fille",
    "fille": "fille",
    "feminin": "fille",
    "féminin": "fille",
    "g": "garcon",
    "garcon": "garcon",
    "garçon": "garcon",
    "m": "garcon",
    "masculin": "garcon",
    "n": "neutre",
    "neutre": "neutre",
    "": "neutre",
}


def normaliser_genre(valeur: object) -> str:
    """Ramene une saisie libre (``Fille``, ``garçon``, ``F``...) a fille / garcon / neutre."""
    cle = str(valeur or "").strip().lower()
    if cle not in _ALIAS:
        raise ValueError(f"Genre inconnu : {valeur!r} (attendu : fille, garcon ou neutre)")
    return _ALIAS[cle]


def accorder(texte: str, genre: str) -> str:
    """Remplace chaque ``{{f|g}}`` ou ``{{f|g|n}}`` par la forme du genre demande."""
    indice = GENRES.index(genre)

    def choisir(correspondance: re.Match[str]) -> str:
        formes = correspondance.group(1).split("|")
        if len(formes) == 3:
            return formes[indice]
        feminin, masculin = formes
        return (feminin, masculin, f"{feminin} ou {masculin}")[indice]

    return _ACCORD.sub(choisir, texte)


def remplir(texte: str, variables: dict[str, str], genre: str = GENRE_DEFAUT) -> str:
    """Accorde le texte selon le genre, puis remplace les ``{variables}`` connues."""
    texte = accorder(texte, genre)
    for cle, valeur in variables.items():
        texte = texte.replace("{" + cle + "}", valeur)
    return texte
