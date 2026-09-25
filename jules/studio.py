"""Studio : les supports de revision que l'eleve construit lui-meme (carte mentale, fiche, quiz,
cartes memoire). Jules relit ce qui existe deja, il n'ecrit jamais le contenu a la place de l'eleve.

Format complet, regles de validation et garde-fous : docs/STUDIO-CONTRAT.md, sections 1 et 2.

Regle de fond : un support ne peut etre valide (`pret_a_valider`) que si l'eleve y a lui-meme
ecrit du contenu. Le garde-fou anti-copie refuse un contenu identique, une fois normalise, a un
passage de la lecon ou a un message de Jules : un support recopie n'est pas un support produit.

Ce fichier ne fait que definir les formats et les valider : aucune dependance au stockage ni au
serveur (voir docs/STUDIO-CONTRAT.md §2, signatures figees).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jules.bibliotheques import normaliser

TYPES_SUPPORT = ("carte_mentale", "fiche", "quiz", "cartes_memoire")
STATUTS_SUPPORT = ("brouillon", "relu", "valide")
TAILLE_CHAMP_MAX = 200

# Pour chaque type : le nom du champ liste du gabarit, et les champs texte libres de chacun de
# ses elements (voir docs/STUDIO-CONTRAT.md §1). Le titre du support lui-meme est toujours editable
# et n'est pas repete ici.
_CHAMPS_LISTE: dict[str, tuple[str, tuple[str, ...]]] = {
    "carte_mentale": ("noeuds", ("texte",)),
    "fiche": ("sections", ("titre", "contenu")),
    "quiz": ("questions", ("question", "reponse")),
    "cartes_memoire": ("cartes", ("recto", "verso")),
}

# Nombre minimal d'elements (ou de sections remplies, pour la fiche) exige par `pret_a_valider`.
_MINIMUM_ELEMENTS: dict[str, int] = {
    "carte_mentale": 3,
    "fiche": 2,
    "quiz": 3,
    "cartes_memoire": 4,
}

_NOMS_TYPE: dict[str, str] = {
    "carte_mentale": "une carte mentale",
    "fiche": "une fiche",
    "quiz": "un quiz",
    "cartes_memoire": "des cartes mémoire",
}

_NOMS_ELEMENTS: dict[str, str] = {
    "carte_mentale": "branches",
    "fiche": "sections remplies",
    "quiz": "questions",
    "cartes_memoire": "cartes",
}


class ErreurStudio(ValueError):
    """Support de studio non conforme : le message dit quoi corriger, en francais simple."""


@dataclass
class Support:
    id: str
    notion: str
    type: str
    titre: str
    contenu: dict[str, Any]  # forme selon `type`, voir docs/STUDIO-CONTRAT.md §1
    statut: str  # STATUTS_SUPPORT
    cree_le: str
    modifie_le: str

    def public(self) -> dict[str, Any]:
        """Rien a retirer ici (a la difference de `Bloc.public()`) : le support appartient a l'eleve."""
        return {
            "id": self.id,
            "notion": self.notion,
            "type": self.type,
            "titre": self.titre,
            "contenu": self.contenu,
            "statut": self.statut,
            "cree_le": self.cree_le,
            "modifie_le": self.modifie_le,
        }


def _verifier_type(type_support: str) -> tuple[str, tuple[str, ...]]:
    if type_support not in TYPES_SUPPORT:
        raise ErreurStudio(f"Type de support {type_support!r} inconnu (attendu : {', '.join(TYPES_SUPPORT)}).")
    return _CHAMPS_LISTE[type_support]


def trame_vide(type_support: str, notion: str, titre: str) -> dict[str, Any]:
    """Gabarit vide du type demande (voir docs/STUDIO-CONTRAT.md §1) : aucun champ pre-rempli.

    Leve ErreurStudio si `type_support` est inconnu.
    """
    nom_liste, _ = _verifier_type(type_support)
    return {"type": type_support, "notion": notion, "titre": titre, nom_liste: []}


def valider_champ(type_support: str, chemin: list[str | int], valeur: str) -> None:
    """Leve ErreurStudio si `valeur` est trop longue, ou si `chemin` n'existe pas dans le gabarit
    du type demande (voir docs/STUDIO-CONTRAT.md §1, "taille" et §2, `valider_champ`).
    """
    nom_liste, champs = _verifier_type(type_support)
    if len(valeur) > TAILLE_CHAMP_MAX:
        raise ErreurStudio(
            f"C'est trop long ({len(valeur)} caractères, {TAILLE_CHAMP_MAX} au maximum) : "
            "essaie de resumer en une phrase ou deux."
        )
    if list(chemin) == ["titre"]:
        return
    chemin_valide = (
        len(chemin) == 3
        and chemin[0] == nom_liste
        and isinstance(chemin[1], int)
        and not isinstance(chemin[1], bool)
        and chemin[1] >= 0
        and chemin[2] in champs
    )
    if not chemin_valide:
        raise ErreurStudio(f"Ce champ n'existe pas pour {_NOMS_TYPE[type_support]} : vérifie l'emplacement.")


def _normaliser_pour_comparaison(texte: str) -> str:
    """Casse, accents, espaces et ponctuation ignores, pour reperer un contenu recopie tel quel."""
    sans_accents = normaliser(texte)
    sans_ponctuation = re.sub(r"[^a-z0-9]+", " ", sans_accents)
    return re.sub(r"\s+", " ", sans_ponctuation).strip()


def _champs_textuels(support: Support) -> list[tuple[str, str]]:
    """Chaque champ texte libre du support, avec un nom lisible pour un message d'erreur."""
    champs: list[tuple[str, str]] = [("titre", support.titre)]
    nom_liste, noms_champs = _CHAMPS_LISTE[support.type]
    elements = support.contenu.get(nom_liste) or []
    for i, element in enumerate(elements):
        if not isinstance(element, dict):
            continue
        for nom in noms_champs:
            champs.append((f"{nom_liste}[{i}].{nom}", str(element.get(nom) or "")))
    return champs


def _verifier_nombre_elements(support: Support) -> None:
    nom_liste, _ = _CHAMPS_LISTE[support.type]
    elements = support.contenu.get(nom_liste) or []
    if support.type == "fiche":
        nombre = sum(1 for e in elements if isinstance(e, dict) and str(e.get("contenu") or "").strip())
    else:
        nombre = len(elements)
    minimum = _MINIMUM_ELEMENTS[support.type]
    if nombre < minimum:
        raise ErreurStudio(
            f"Encore un peu court pour être un support utile : il faut au moins {minimum} "
            f"{_NOMS_ELEMENTS[support.type]} pour {_NOMS_TYPE[support.type]}."
        )


# Un champ de l'eleve est considere comme recopie s'il est identique a un texte de reference, ou
# s'il en reprend un passage d'au moins ce nombre de mots (en dessous, une coincidence est
# normale : « le theoreme de Pythagore », « en 1905 »...).
MOTS_MIN_PASSAGE_RECOPIE = 8


def _est_recopie(valeur_normalisee: str, references: set[str]) -> bool:
    if valeur_normalisee in references:
        return True
    if len(valeur_normalisee.split()) < MOTS_MIN_PASSAGE_RECOPIE:
        return False
    motif = f" {valeur_normalisee} "
    return any(motif in f" {reference} " for reference in references)


def pret_a_valider(support: Support, lecon_textes: list[str], messages_jules: list[str]) -> None:
    """Leve ErreurStudio si le nombre d'elements est insuffisant, ou si du contenu est recopie
    (comparaison normalisee avec `lecon_textes` et `messages_jules`), voir docs/STUDIO-CONTRAT.md §1.
    """
    _verifier_type(support.type)
    _verifier_nombre_elements(support)
    references = {_normaliser_pour_comparaison(t) for t in lecon_textes if t}
    references |= {_normaliser_pour_comparaison(m) for m in messages_jules if m}
    for nom_champ, valeur in _champs_textuels(support):
        valeur = valeur.strip()
        if not valeur:
            continue
        if _est_recopie(_normaliser_pour_comparaison(valeur), references):
            raise ErreurStudio(
                f"Ce que tu as écrit dans « {nom_champ} » est recopié mot pour mot de la leçon "
                "ou d'un message de Jules : réécris-le avec tes propres mots."
            )


# Une ligne de liste a puces ou numerotee ("- ...", "* ...", "1. ...", "2) ...").
_MOTIF_PUCE = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s+\S")
# Un titre : soit un titre markdown ("# ..."), soit une courte etiquette seule sur sa ligne,
# terminee par ":" (par exemple "Definition :"), sans point d'interrogation.
_MOTIF_TITRE = re.compile(r"^(?:#{1,6}\s+\S.+|[^\n:?]{1,60}:)$")


def ressemble_a_un_support_redige(texte_jules: str) -> bool:
    """Heuristique (meme esprit que `jules.lecons.contient_la_reponse`) : vrai si `texte_jules`
    ressemble a un contenu pret a copier pour l'eleve (longue liste a puces, plusieurs titres,
    paragraphe de definition), plutot qu'a une question ou une remarque courte de relecture
    (voir docs/STUDIO-CONTRAT.md §2 et §5).
    """
    texte = (texte_jules or "").strip()
    if not texte:
        return False
    lignes = [ligne.strip() for ligne in texte.splitlines() if ligne.strip()]
    puces = sum(1 for ligne in lignes if _MOTIF_PUCE.match(ligne))
    if puces >= 3:
        return True
    titres = sum(1 for ligne in lignes if _MOTIF_TITRE.match(ligne))
    if titres >= 2:
        return True
    return "?" not in texte and len(texte) >= 220 and texte.count(".") >= 2
