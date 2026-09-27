"""Leviers d'adaptation (docs/spec/ADAPTATIONS-LOT2.md, §2, EX-101 et EX-107).

Un levier est un reglage elementaire de l'interface ou de l'expression de Jules (espacement des lettres,
taille du texte, lecture vocale...). Chaque levier est declare une seule fois, dans
adaptations/leviers/<id>.yaml, avec :

- `id` : identifiant neutre (egal au nom du fichier) ;
- `canal` : ou il agit (`css` affichage, `consigne` au modele, `js` comportement, `outils`) ;
- `type` : `nombre` (valeur et `unite`), `choix` (liste fermee, dans l'ordre) ou `booleen` ;
- `neutre` : la valeur d'aujourd'hui, qui ne change rien au rendu ;
- `plage` : `{min, max}` pour un nombre (au moins une borne ; sans `min`, la valeur doit etre
  strictement positive), la liste fermee des valeurs permises sinon (attribut Python `Levier.valeurs`) ;
- `combinaison` : regle quand plusieurs amenagements reglent le meme levier (COMBINAISONS) ;
- `source` : `{nature, reference}`, nature parmi NATURES_SOURCE.

Ce module ne fait que charger et valider : l'application des leviers (CSS, outils, prompt) et leur
combinaison sont traitees par d'autres exigences (EX-104, EX-105).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DOSSIER_LEVIERS = Path(__file__).resolve().parents[1] / "adaptations" / "leviers"
CANAUX = frozenset({"css", "consigne", "js", "outils"})
TYPES = frozenset({"nombre", "choix", "booleen"})
# Regles du §2 : max, min, ou (booleens), le plus restrictif (dernier de la liste ordonnee),
# arbitrage parent (pas de combinaison automatique : le parent choisit).
COMBINAISONS = frozenset({"max", "min", "ou", "plus-restrictif", "arbitrage-parent"})
NATURES_SOURCE = frozenset({"etude", "norme", "usage", "preference", "droit"})
CHAMPS = ("id", "canal", "type", "neutre", "plage", "combinaison", "source")


class LevierInvalide(ValueError):
    """Declaration de levier incomplete ou incoherente."""


@dataclass(frozen=True)
class Levier:
    id: str
    canal: tuple[str, ...]
    type: str
    neutre: Any
    combinaison: str
    source: dict[str, str]
    unite: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    valeurs: tuple[Any, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)  # champs propres a un levier (ex. familles de police)

    def dans_la_plage(self, valeur: Any) -> bool:
        if self.type == "booleen":
            return isinstance(valeur, bool)
        if self.type == "choix":
            return valeur in self.valeurs
        if valeur is None:  # nombre sans valeur : aucun reglage (ex. aucune limite de longueur de ligne)
            return self.details.get("neutre_signifie") is not None
        if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
            return False
        if self.minimum is None and valeur <= 0:
            # Sans borne basse declaree, seule une grandeur strictement positive a un sens :
            # `max-width: 0ch` ou `-10ch` serait vide ou invalide (ignore sans bruit par le navigateur).
            return False
        return (self.minimum is None or valeur >= self.minimum) and (self.maximum is None or valeur <= self.maximum)


def charger_levier(chemin: Path) -> Levier:
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    if not isinstance(brut, dict):
        raise LevierInvalide(f"{chemin.name} : pas un dictionnaire YAML")
    manquants = [c for c in CHAMPS if c not in brut]
    if manquants:
        raise LevierInvalide(f"{chemin.name} : champs manquants {manquants}")
    ident = str(brut["id"])
    if ident != chemin.stem:
        raise LevierInvalide(f"{chemin.name} : id {ident!r} different du nom du fichier")
    canal = brut["canal"] if isinstance(brut["canal"], list) else [brut["canal"]]
    if not canal or any(c not in CANAUX for c in canal):
        raise LevierInvalide(f"{ident} : canal {canal!r} inconnu (attendu parmi {sorted(CANAUX)})")
    type_ = brut["type"]
    if type_ not in TYPES:
        raise LevierInvalide(f"{ident} : type {type_!r} inconnu")
    if brut["combinaison"] not in COMBINAISONS:
        raise LevierInvalide(f"{ident} : combinaison {brut['combinaison']!r} inconnue")
    source = brut["source"]
    if not isinstance(source, dict) or source.get("nature") not in NATURES_SOURCE or not source.get("reference"):
        raise LevierInvalide(f"{ident} : source incomplete (nature parmi {sorted(NATURES_SOURCE)} et reference)")
    plage = brut["plage"]
    connus = {*CHAMPS, "unite", "valeurs"}
    details = {k: v for k, v in brut.items() if k not in connus}
    levier = Levier(
        id=ident,
        canal=tuple(canal),
        type=type_,
        neutre=brut["neutre"],
        combinaison=brut["combinaison"],
        source={str(k): str(v) for k, v in source.items()},
        details=details,
        **_plage(ident, type_, plage, brut),
    )
    if not levier.dans_la_plage(levier.neutre):
        raise LevierInvalide(f"{ident} : valeur neutre {levier.neutre!r} hors de la plage")
    return levier


def _plage(ident: str, type_: str, plage: Any, brut: dict[str, Any]) -> dict[str, Any]:
    if type_ == "nombre":
        if not isinstance(plage, dict) or not ({"min", "max"} & plage.keys()):
            raise LevierInvalide(f"{ident} : plage d'un nombre = {{min, max}} (au moins une borne)")
        if not brut.get("unite"):
            raise LevierInvalide(f"{ident} : unite manquante")
        mini, maxi = plage.get("min"), plage.get("max")
        if mini is not None and maxi is not None and mini > maxi:
            raise LevierInvalide(f"{ident} : plage inversee")
        return {"unite": str(brut["unite"]), "minimum": mini, "maximum": maxi}
    if type_ == "booleen":
        if plage != [False, True]:
            raise LevierInvalide(f"{ident} : plage d'un booleen = [false, true]")
        return {"valeurs": (False, True)}
    if not isinstance(plage, list) or len(plage) < 2 or len(set(plage)) != len(plage):
        raise LevierInvalide(f"{ident} : plage d'un choix = liste fermee d'au moins deux valeurs distinctes")
    return {"valeurs": tuple(plage)}


def charger_leviers(dossier: Path = DOSSIER_LEVIERS) -> dict[str, Levier]:
    """Tous les leviers du dossier, par identifiant. Une declaration invalide leve LevierInvalide."""
    leviers: dict[str, Levier] = {}
    for chemin in sorted(dossier.glob("*.yaml")):
        levier = charger_levier(chemin)
        leviers[levier.id] = levier
    return leviers


# --- application des leviers CSS (EX-105) ---------------------------------------------------------
# Variable derivee de `taille-texte` : rapport a la valeur neutre. Les tailles des feuilles de style
# (en rem, EX-010) sont ecrites `calc(Xrem * var(--adapt-echelle-texte, 1))` : une variable posee sur
# <body> ne peut pas changer la taille de la racine, et diviser deux longueurs en CSS n'est possible
# que dans les navigateurs les plus recents.
VARIABLE_ECHELLE = "--adapt-echelle-texte"


def _nombre(valeur: float) -> str:
    return f"{round(float(valeur), 6):g}"


def _valeur_css(levier: Levier, valeur: Any) -> str | None:
    """Valeur CSS de la variable du levier, ou None si le levier n'en a pas de sensee."""
    if levier.type == "booleen":
        return "1"
    if levier.type == "choix":
        table = levier.details.get("familles") or levier.details.get("couleurs")
        return str(table[valeur]) if isinstance(table, dict) and valeur in table else None
    unite = "" if levier.unite == "multiplicateur" else levier.unite
    return f"{_nombre(valeur)}{unite}"


def leviers_resolus(leviers: dict[str, Levier], valeurs: dict[str, Any]) -> dict[str, Any]:
    """Leviers regles pour l'eleve, valeurs brutes : `infos.leviers` de /api/infos (identifiant -> valeur).

    `valeurs` : identifiant -> valeur voulue (combinaison des amenagements, EX-104). Seules les valeurs
    d'un levier connu, dans sa plage et differentes du neutre sont gardees : quand tout est neutre, le
    resultat est vide et le rendu reste celui d'aujourd'hui (EX-102). Meme forme que le message
    `{type: "adaptations", leviers}` envoye aux outils (docs/OUTILS-CONTRAT.md).
    """
    retenus: dict[str, Any] = {}
    for ident, valeur in sorted(valeurs.items()):
        levier = leviers.get(ident)
        if levier is None or valeur is None or valeur == levier.neutre or not levier.dans_la_plage(valeur):
            continue
        if levier.type == "booleen" and valeur is not True:
            continue
        retenus[ident] = valeur
    return retenus


def leviers_css(leviers: dict[str, Levier], resolus: dict[str, Any]) -> dict[str, str]:
    """Variables CSS a poser sur <body> (EX-105) : `infos.leviers_css`, derive de `infos.leviers`
    (jamais l'inverse). Un levier sans canal `css` ou sans valeur CSS sensee n'en donne aucune."""
    variables: dict[str, str] = {}
    for ident, valeur in sorted(leviers_resolus(leviers, resolus).items()):
        levier = leviers[ident]
        variable = levier.details.get("variable_css")
        if "css" not in levier.canal or not variable:
            continue
        css = _valeur_css(levier, valeur)
        if css is None:
            continue
        variables[str(variable)] = css
        if ident == "taille-texte" and isinstance(levier.neutre, (int, float)) and levier.neutre > 0:
            variables[VARIABLE_ECHELLE] = _nombre(valeur / levier.neutre)
    return variables
