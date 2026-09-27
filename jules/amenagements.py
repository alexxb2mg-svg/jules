"""Amenagements coches par le parent (docs/spec/ADAPTATIONS-LOT2.md, §3, EX-103).

Un amenagement reprend un item du PAP (modele officiel, circulaire 2015-016) sur lequel un logiciel
peut agir. Il est declare une seule fois, dans adaptations/amenagements/<id>.yaml, avec :

- `id` : identifiant neutre (egal au nom du fichier) ;
- `libelles` : par niveau (`maternelle`, `elementaire`, `college`, `lycee`), `{page, texte}` recopies
  en entier depuis docs/spec/pap-libelles.txt (texte affiche du PDF, jamais tronque) ;
- `leviers` : la valeur que l'amenagement donne a chaque levier qu'il regle (adaptations/leviers/).

Un niveau sans libelle n'a pas d'item correspondant dans le PAP : l'amenagement est alors affiche sous
la rubrique libre du PAP « Autres amenagements et adaptations », avec la mention « a inscrire par
l'equipe educative ». La maternelle n'a pas cette rubrique : un amenagement sans libelle maternelle
n'y est pas affiche (`affichage` renvoie None).

Garde-fous du chargeur : levier inconnu, valeur hors de la plage du levier, levier a arbitrage du
parent (`police`, `fond` : preferences hors PAP) et `lecture-vocale = automatique` (reservee au
parent, §4) sont refuses. La combinaison de plusieurs amenagements releve d'EX-104.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jules.leviers import Levier, charger_leviers

DOSSIER_AMENAGEMENTS = Path(__file__).resolve().parents[1] / "adaptations" / "amenagements"
NIVEAUX = ("maternelle", "elementaire", "college", "lycee")
CHAMPS = ("id", "libelles", "leviers")
# Rubrique libre du PAP, titre et pages recopies du §3 de la spec (absente en maternelle).
RUBRIQUE_AUTRES = "Autres aménagements et adaptations"
PAGES_RUBRIQUE_AUTRES = {"elementaire": 5, "college": 8, "lycee": 11}
MENTION_AUTRES = "à inscrire par l'équipe éducative"


class AmenagementInvalide(ValueError):
    """Declaration d'amenagement incomplete ou incoherente."""


@dataclass(frozen=True)
class Libelle:
    niveau: str
    page: int
    texte: str


@dataclass(frozen=True)
class Affichage:
    """Ce que la page parent montre pour un amenagement a un niveau donne."""

    niveau: str
    page: int
    texte: str | None  # libelle PAP ; None sous la rubrique « Autres amenagements et adaptations »
    rubrique_autres: bool
    mention: str | None = None


@dataclass(frozen=True)
class Amenagement:
    id: str
    libelles: dict[str, Libelle]
    leviers: dict[str, Any]

    def affichage(self, niveau: str) -> Affichage | None:
        """Libelle PAP du niveau, sinon la rubrique « Autres... » ; None en maternelle sans libelle."""
        if niveau not in NIVEAUX:
            raise ValueError(f"niveau {niveau!r} inconnu (attendu parmi {NIVEAUX})")
        if libelle := self.libelles.get(niveau):
            return Affichage(niveau, libelle.page, libelle.texte, rubrique_autres=False)
        if niveau in PAGES_RUBRIQUE_AUTRES:
            return Affichage(niveau, PAGES_RUBRIQUE_AUTRES[niveau], None, rubrique_autres=True, mention=MENTION_AUTRES)
        return None


def charger_amenagement(chemin: Path, leviers: dict[str, Levier]) -> Amenagement:
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    if not isinstance(brut, dict):
        raise AmenagementInvalide(f"{chemin.name} : pas un dictionnaire YAML")
    manquants = [c for c in CHAMPS if c not in brut]
    if manquants:
        raise AmenagementInvalide(f"{chemin.name} : champs manquants {manquants}")
    inconnus = sorted(set(brut) - set(CHAMPS))
    if inconnus:
        raise AmenagementInvalide(f"{chemin.name} : champs inconnus {inconnus}")
    ident = str(brut["id"])
    if ident != chemin.stem:
        raise AmenagementInvalide(f"{chemin.name} : id {ident!r} different du nom du fichier")
    return Amenagement(
        id=ident, libelles=_libelles(ident, brut["libelles"]), leviers=_leviers(ident, brut["leviers"], leviers)
    )


def _libelles(ident: str, brut: Any) -> dict[str, Libelle]:
    if not isinstance(brut, dict) or not brut:
        raise AmenagementInvalide(f"{ident} : libelles = {{niveau: {{page, texte}}}}, au moins un niveau")
    libelles: dict[str, Libelle] = {}
    for niveau, valeur in brut.items():
        if niveau not in NIVEAUX:
            raise AmenagementInvalide(f"{ident} : niveau {niveau!r} inconnu (attendu parmi {NIVEAUX})")
        if not isinstance(valeur, dict) or set(valeur) != {"page", "texte"}:
            raise AmenagementInvalide(f"{ident} : libelle {niveau} = {{page, texte}}")
        page, texte = valeur["page"], valeur["texte"]
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise AmenagementInvalide(f"{ident} : page du libelle {niveau} invalide ({page!r})")
        if not isinstance(texte, str) or not texte.strip():
            raise AmenagementInvalide(f"{ident} : texte du libelle {niveau} vide")
        libelles[niveau] = Libelle(niveau, page, texte)
    return libelles


def _leviers(ident: str, brut: Any, leviers: dict[str, Levier]) -> dict[str, Any]:
    if not isinstance(brut, dict) or not brut:
        raise AmenagementInvalide(f"{ident} : leviers = {{levier: valeur}}, au moins un levier")
    for nom, valeur in brut.items():
        levier = leviers.get(nom)
        if levier is None:
            raise AmenagementInvalide(f"{ident} : levier {nom!r} inconnu")
        if levier.combinaison == "arbitrage-parent":
            raise AmenagementInvalide(f"{ident} : {nom} est une preference du parent, pas d'un amenagement")
        if not levier.dans_la_plage(valeur):
            raise AmenagementInvalide(f"{ident} : {nom} = {valeur!r} hors de la plage")
        if valeur == levier.neutre:
            raise AmenagementInvalide(f"{ident} : {nom} = valeur neutre, sans effet")
        if nom == "lecture-vocale" and valeur == "automatique" and levier.details.get("automatique_reserve_au_parent"):
            raise AmenagementInvalide(f"{ident} : lecture-vocale automatique est reservee au choix du parent")
    return dict(brut)


def charger_amenagements(
    dossier: Path = DOSSIER_AMENAGEMENTS, leviers: dict[str, Levier] | None = None
) -> dict[str, Amenagement]:
    """Tous les amenagements du dossier, par identifiant. Une declaration invalide leve AmenagementInvalide."""
    leviers = charger_leviers() if leviers is None else leviers
    amenagements: dict[str, Amenagement] = {}
    for chemin in sorted(dossier.glob("*.yaml")):
        amenagement = charger_amenagement(chemin, leviers)
        amenagements[amenagement.id] = amenagement
    return amenagements
