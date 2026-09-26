"""Fiches visuelles : une notion du programme condensee en blocs visuels (formule, carte,
graphe interactif, methode, piege, exemple, renfort), commentes par Jules avec des phrases
preecrites (`jules:`). Format valide par Alex : voir `bibliotheque/SCHEMA-FICHE-VISUELLE.md`.

Une fiche visuelle vit dans une bibliotheque de type `fiches-visuelles` :
    bibliotheque/<id>/bibliotheque.yaml                     (type: fiches-visuelles)
    bibliotheque/<id>/fiches/<matiere>/<notion>.yaml

Contrairement aux fiches de reperes (jules/bibliotheques.py) qui nourrissent le prompt du chat,
une fiche visuelle est faite pour etre AFFICHEE telle quelle, sans passer par un modele d'IA
(voir `jules_cadrage_interface.md` : rendu 100% deterministe). Chaque bloc a un `id` unique dans
la fiche ; son adresse est `fiche/<id>` (et `fiche/<id>/<sous-id>` pour ses elements, ex. un
curseur). C'est ce que Jules recevra plus tard pour commenter, et ce sur quoi les gabarits de
figures interactives (extensions/<id>/gabarit.js, voir docs/EXTENSIONS.md) s'appuient pour leurs lectures.

Regle de securite : les conditions `si` d'un bloc `graphe` (ex. "a > 0", "a >= 1 && b < 0") ne
sont JAMAIS evaluees par eval() : `analyser_condition` les decoupe en une petite liste de
comparaisons (variable, operateur, nombre), rien d'autre n'est accepte.

Ce fichier ne fait que lire, verifier et corriger : il ne parle ni au modele d'IA ni a l'interface.
"""

from __future__ import annotations

import operator
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jules.bibliotheques import (
    LICENCES_LIBRES,
    TAILLE_MAX_FICHIER,
    Bibliotheque,
    ErreurBibliotheque,
    Notion,
    Racines,
    dossier_bibliotheque,
    lire_identite,
)
from jules.svg_sur import ErreurSvg, nettoyer_svg

# --- constantes du format --------------------------------------------------------

TYPES_BLOCS = ("formule", "carte", "graphe", "methode", "piege", "exemple", "renfort", "schema")
TAILLE_MAX_SVG = 100_000  # octets : un schema est un dessin simple, pas une image lourde
ID_ATTENDUS = "attendus"  # adresse reservee : reprend automatiquement les attendus du referentiel
_ID_BLOC = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Gabarits de figures interactives : une fiche ne peut pas embarquer de code libre, seulement
# choisir un gabarit declare et lui donner ses parametres. Les gabarits acceptes sont ceux que
# fournissent les extensions actives (`figures_fournies` de jules/extensions.py) : ce fichier n'en
# connait aucun par son nom, ils lui sont passes en parametre (`gabarits`).

# Longueurs plafonnees pour rester lisible sur tablette (cadrage interface, 25/09/2026).
LIMITE_JULES = 320  # 1 a 3 phrases
LIMITE_LEGENDE = 160
LIMITE_TEXTE = 260
LIMITE_TITRE = 90
LIMITE_CURSEURS = 6
LIMITE_ETAPES = 6
LIMITE_LIENS_RENFORT = 6
LIMITE_NOEUDS_CARTE = 8

MIN_BLOCS = 3
MAX_BLOCS = 12


class ErreurFicheVisuelle(ValueError):
    """Fiche illisible ou non conforme : le message dit quoi corriger, en francais."""


# --- petit analyseur de conditions, jamais d'eval() -------------------------------

_VARIABLE = r"[a-zA-Z_][a-zA-Z0-9_]*"
_NOMBRE = r"-?\d+(?:\.\d+)?"
_OPERATEURS = ("<=", ">=", "==", "!=", "<", ">")
_ATOME = re.compile(rf"^\s*({_VARIABLE})\s*({'|'.join(_OPERATEURS)})\s*({_NOMBRE})\s*$")

_FONCTIONS_OP = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
}


def analyser_condition(expression: str) -> list[tuple[str, str, float]]:
    """Decoupe une condition `si` en atomes (variable, operateur, nombre), lies par des « && ».

    N'accepte QUE des comparaisons simples entre une variable et un nombre litteral : jamais
    d'eval(), jamais d'appel de fonction, jamais d'operateur non liste ci-dessus.
    """
    atomes: list[tuple[str, str, float]] = []
    for morceau in expression.split("&&"):
        trouve = _ATOME.match(morceau)
        if not trouve:
            raise ErreurFicheVisuelle(f"condition illisible : {expression!r}")
        variable, op, nombre = trouve.groups()
        atomes.append((variable, op, float(nombre)))
    if not atomes:
        raise ErreurFicheVisuelle(f"condition vide : {expression!r}")
    return atomes


def evaluer_condition(expression: str, variables: dict[str, float]) -> bool:
    """Vrai si toutes les comparaisons de la condition sont vraies pour ces variables."""
    for variable, op, nombre in analyser_condition(expression):
        if variable not in variables:
            return False
        if not _FONCTIONS_OP[op](float(variables[variable]), nombre):
            return False
    return True


# --- structures --------------------------------------------------------------------


@dataclass
class BlocFiche:
    id: str
    type: str
    donnees: dict[str, Any] = field(default_factory=dict)
    jules: str = ""

    def public(self) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self.id, "type": self.type, "adresse": f"fiche/{self.id}", "jules": self.jules}
        d.update(self.donnees)
        return d


@dataclass
class FicheVisuelle:
    notion: str
    titre: str
    matiere: str
    niveau: str
    bibliotheque: str
    statut: str
    licence: str
    sources: list[dict[str, str]] = field(default_factory=list)
    relecture: str = "a_relire"
    blocs: list[BlocFiche] = field(default_factory=list)
    avertissement: str = ""
    variables: dict[str, str] = field(default_factory=dict)

    def toutes_les_variables(self) -> dict[str, str]:
        """Le sens des lettres de grandeur de la notion (champ `variables:`), rappele au survol sur
        toutes les pages. Seules les lettres declarees : jamais un symbole chimique ni une unite."""
        return dict(self.variables)

    def publique(self, attendus: list[str]) -> dict[str, Any]:
        blocs: list[dict[str, Any]] = []
        if attendus:
            blocs.append(
                {"id": ID_ATTENDUS, "type": ID_ATTENDUS, "adresse": f"fiche/{ID_ATTENDUS}", "attendus": attendus}
            )
        blocs.extend(b.public() for b in self.blocs)
        return {
            "notion": self.notion,
            "titre": self.titre,
            "matiere": self.matiere,
            "niveau": self.niveau,
            "statut": self.statut,
            "relecture": self.relecture,
            "avertissement": self.avertissement,
            "sources": self.sources,
            "blocs": blocs,
            "variables": self.toutes_les_variables(),
        }


# --- verifications de contenu -------------------------------------------------------


_ACCENT = re.compile(r"\*\*(.+?)\*\*")
ACCENTS_MAX = 4  # notions cles par champ
LIMITE_ACCENT = 40  # caracteres par notion cle
PART_ACCENT_MAX = 0.6  # au plus 60 % du texte mis en valeur : sinon plus rien ne ressort


def texte_sans_accents(texte: str) -> str:
    """Le texte tel que l'eleve le lit, sans les marques ** des notions cles."""
    return _ACCENT.sub(r"\1", texte)


def _verifier_accents(v: str, champ: str, ou: str) -> str:
    """Notions cles marquees **ainsi** : peu nombreuses, courtes, bien fermees. Renvoie le texte sans marques."""
    segments = _ACCENT.findall(v)
    lisible = texte_sans_accents(v)
    if "**" in _ACCENT.sub("", v):
        raise ErreurFicheVisuelle(f"{ou} : champ {champ!r} : marque ** non fermee")
    if len(segments) > ACCENTS_MAX:
        raise ErreurFicheVisuelle(f"{ou} : champ {champ!r} : {len(segments)} notions cles, max {ACCENTS_MAX}")
    for seg in segments:
        if seg != seg.strip() or len(seg) > LIMITE_ACCENT:
            raise ErreurFicheVisuelle(
                f"{ou} : champ {champ!r} : notion cle {seg!r} (sans espace au bord, {LIMITE_ACCENT} caracteres max)"
            )
    if segments and sum(len(x) for x in segments) > PART_ACCENT_MAX * len(lisible):
        raise ErreurFicheVisuelle(f"{ou} : champ {champ!r} : trop de texte mis en valeur (60 % au plus)")
    return lisible


# Nom d'une grandeur dans une formule : une lettre (latine ou grecque), suivie au plus de 3 lettres,
# chiffres ou indices (v, Ec, ρ, V₁, Epp). La bulle de la page rappelle son sens au survol.
NOM_VARIABLE = re.compile(r"^[A-Za-zΑ-Ωα-ωµ][A-Za-z0-9₀-₉]{0,3}$")
VARIABLES_MAX = 12
LIMITE_VARIABLE = 120


def _verifier_variables(brut: Any, nom: str) -> dict[str, str]:
    if brut is None:
        return {}
    if not isinstance(brut, dict) or len(brut) > VARIABLES_MAX:
        raise ErreurFicheVisuelle(f"{nom} : 'variables' doit etre un objet de {VARIABLES_MAX} lettres au plus")
    variables: dict[str, str] = {}
    for lettre, sens in brut.items():
        lettre = str(lettre)
        if not NOM_VARIABLE.match(lettre):
            raise ErreurFicheVisuelle(f"{nom} : variable {lettre!r} : une lettre, puis 3 lettres, chiffres ou indices")
        variables[lettre] = _texte(sens, f"variables.{lettre}", nom, limite=LIMITE_VARIABLE)
    return variables


# Division : l'eleve de college ecrit « ÷ » ; la barre « / » n'est permise que dans une unite collee
# (m/s, g/cm³). Une barre entouree d'espaces (« m / V ») est refusee partout, schemas compris.
_BARRE_DE_DIVISION = re.compile(r"\S\s+/\s+\S")


def _verifier_division(texte: str, champ: str, ou: str) -> None:
    if _BARRE_DE_DIVISION.search(texte):
        raise ErreurFicheVisuelle(f"{ou} : champ {champ!r} : division ecrite « / », ecrire « ÷ » (m ÷ V)")


def _texte(
    valeur: Any, champ: str, ou: str, limite: int = LIMITE_TEXTE, obligatoire: bool = True, riche: bool = False
) -> str:
    """Un champ texte. `riche` : l'affichage met en valeur les notions cles marquees **ainsi** ;
    ailleurs (identifiants, titres de carte...) la marque est refusee, elle s'afficherait telle quelle."""
    v = str(valeur or "").strip()
    if obligatoire and not v:
        raise ErreurFicheVisuelle(f"{ou} : champ {champ!r} manquant")
    _verifier_division(v, champ, ou)
    if riche:
        lisible = _verifier_accents(v, champ, ou)
    elif "**" in v:
        raise ErreurFicheVisuelle(f"{ou} : champ {champ!r} : pas de mise en valeur ** dans ce champ")
    else:
        lisible = v
    if len(lisible) > limite:
        raise ErreurFicheVisuelle(f"{ou} : champ {champ!r} trop long ({len(lisible)} caracteres, max {limite})")
    return v


def _verifier_jules(valeur: Any, ou: str) -> str:
    texte = str(valeur or "").strip()
    if not texte:
        return ""
    _verifier_division(texte, "jules", ou)
    lisible = _verifier_accents(texte, "jules", ou)
    if len(lisible) > LIMITE_JULES:
        raise ErreurFicheVisuelle(
            f"{ou} : commentaire 'jules' trop long ({len(lisible)} caracteres, max {LIMITE_JULES})"
        )
    phrases = [p for p in re.split(r"[.!?]+", lisible) if p.strip()]
    if not 1 <= len(phrases) <= 3:
        raise ErreurFicheVisuelle(f"{ou} : commentaire 'jules' doit tenir en 1 a 3 phrases (trouve {len(phrases)})")
    return texte


def _nombre(valeur: Any, champ: str, ou: str) -> float:
    if isinstance(valeur, bool) or not isinstance(valeur, int | float):
        raise ErreurFicheVisuelle(f"{ou} : champ {champ!r} doit etre un nombre")
    return float(valeur)


def _verifier_curseurs(curseurs: Any, ou: str) -> list[dict[str, Any]]:
    if not isinstance(curseurs, list) or not curseurs:
        raise ErreurFicheVisuelle(f"{ou} : au moins un curseur attendu")
    if len(curseurs) > LIMITE_CURSEURS:
        raise ErreurFicheVisuelle(f"{ou} : trop de curseurs (max {LIMITE_CURSEURS})")
    vus: set[str] = set()
    resultat = []
    for i, c in enumerate(curseurs):
        sous_ou = f"{ou}, curseur {i + 1}"
        if not isinstance(c, dict):
            raise ErreurFicheVisuelle(f"{sous_ou} : un objet est attendu")
        identifiant = _texte(c.get("id"), "id", sous_ou, limite=40)
        if not _ID_BLOC.match(identifiant):
            raise ErreurFicheVisuelle(f"{sous_ou} : id {identifiant!r} invalide (minuscules, chiffres, tirets)")
        if identifiant in vus:
            raise ErreurFicheVisuelle(f"{sous_ou} : id {identifiant!r} en double")
        vus.add(identifiant)
        nom = _texte(c.get("nom"), "nom", sous_ou, limite=20)
        mini = _nombre(c.get("min"), "min", sous_ou)
        maxi = _nombre(c.get("max"), "max", sous_ou)
        pas = _nombre(c.get("pas"), "pas", sous_ou)
        depart = _nombre(c.get("depart"), "depart", sous_ou)
        if pas <= 0:
            raise ErreurFicheVisuelle(f"{sous_ou} : pas doit etre strictement positif")
        if not mini <= maxi:
            raise ErreurFicheVisuelle(f"{sous_ou} : min doit etre inferieur ou egal a max")
        if not mini <= depart <= maxi:
            raise ErreurFicheVisuelle(f"{sous_ou} : depart doit etre compris entre min et max")
        resultat.append({"id": identifiant, "nom": nom, "min": mini, "max": maxi, "pas": pas, "depart": depart})
    return resultat


def _verifier_lectures(lectures: Any, noms_curseurs: set[str], ou: str) -> list[dict[str, str]]:
    if lectures is None:
        return []
    if not isinstance(lectures, list):
        raise ErreurFicheVisuelle(f"{ou} : 'lectures' doit etre une liste")
    resultat = []
    for i, lecture in enumerate(lectures):
        sous_ou = f"{ou}, lecture {i + 1}"
        if not isinstance(lecture, dict):
            raise ErreurFicheVisuelle(f"{sous_ou} : un objet est attendu")
        condition = _texte(lecture.get("si"), "si", sous_ou, limite=60)
        for variable, _, _ in analyser_condition(condition):
            if variable not in noms_curseurs:
                raise ErreurFicheVisuelle(
                    f"{sous_ou} : variable {variable!r} inconnue (curseurs : {sorted(noms_curseurs)})"
                )
        texte = _texte(lecture.get("texte"), "texte", sous_ou, riche=True)
        resultat.append({"si": condition, "texte": texte})
    return resultat


def _verifier_figure(figure: dict[str, Any], ou: str, gabarits: frozenset[str]) -> dict[str, Any]:
    gabarit = str(figure.get("gabarit") or "")
    if gabarit not in gabarits:
        attendus = ", ".join(sorted(gabarits)) or "aucune extension de figures active"
        raise ErreurFicheVisuelle(f"{ou} : gabarit {gabarit!r} inconnu (attendu : {attendus})")
    curseurs = _verifier_curseurs(figure.get("curseurs"), ou)
    noms = {c["nom"] for c in curseurs}
    lectures = _verifier_lectures(figure.get("lectures"), noms, ou)
    return {"gabarit": gabarit, "curseurs": curseurs, "lectures": lectures}


def _verifier_formule(d: dict[str, Any], ou: str) -> dict[str, Any]:
    expression = _texte(d.get("expression"), "expression", ou, limite=80)
    termes_bruts = d.get("termes") or {}
    if not isinstance(termes_bruts, dict):
        raise ErreurFicheVisuelle(f"{ou} : 'termes' doit etre un objet")
    termes = {}
    for lettre, info in termes_bruts.items():
        if not isinstance(info, dict):
            raise ErreurFicheVisuelle(f"{ou}, terme {lettre!r} : un objet est attendu")
        termes[str(lettre)] = {
            "couleur": _texte(info.get("couleur"), "couleur", f"{ou}, terme {lettre}", limite=20),
            "legende": _texte(
                info.get("legende"), "legende", f"{ou}, terme {lettre}", limite=LIMITE_LEGENDE, riche=True
            ),
        }
    return {"expression": expression, "termes": termes}


def _verifier_carte(d: dict[str, Any], ou: str) -> dict[str, Any]:
    noeuds_bruts = d.get("noeuds") or []
    if not isinstance(noeuds_bruts, list) or len(noeuds_bruts) < 2:
        raise ErreurFicheVisuelle(f"{ou} : au moins deux noeuds attendus dans la carte")
    if len(noeuds_bruts) > LIMITE_NOEUDS_CARTE:
        raise ErreurFicheVisuelle(f"{ou} : trop de noeuds (max {LIMITE_NOEUDS_CARTE})")
    ids: set[str] = set()
    noeuds = []
    for i, n in enumerate(noeuds_bruts):
        sous_ou = f"{ou}, noeud {i + 1}"
        if not isinstance(n, dict):
            raise ErreurFicheVisuelle(f"{sous_ou} : un objet est attendu")
        identifiant = _texte(n.get("id"), "id", sous_ou, limite=40)
        if not _ID_BLOC.match(identifiant):
            raise ErreurFicheVisuelle(f"{sous_ou} : id {identifiant!r} invalide")
        if identifiant in ids:
            raise ErreurFicheVisuelle(f"{sous_ou} : id {identifiant!r} en double")
        ids.add(identifiant)
        noeuds.append(
            {
                "id": identifiant,
                "titre": _texte(n.get("titre"), "titre", sous_ou, limite=LIMITE_TITRE),
                "sous_titre": _texte(
                    n.get("sous_titre"), "sous_titre", sous_ou, limite=LIMITE_TITRE, obligatoire=False
                ),
                "principal": bool(n.get("principal", False)),
            }
        )
    liens_bruts = d.get("liens") or []
    if not isinstance(liens_bruts, list):
        raise ErreurFicheVisuelle(f"{ou} : 'liens' doit etre une liste")
    liens = []
    for i, lien in enumerate(liens_bruts):
        sous_ou = f"{ou}, lien {i + 1}"
        if not isinstance(lien, dict):
            raise ErreurFicheVisuelle(f"{sous_ou} : un objet est attendu")
        de, vers = str(lien.get("de") or ""), str(lien.get("vers") or "")
        if de not in ids or vers not in ids:
            raise ErreurFicheVisuelle(f"{sous_ou} : 'de' et 'vers' doivent citer des noeuds existants")
        liens.append(
            {
                "de": de,
                "vers": vers,
                "libelle": _texte(lien.get("libelle"), "libelle", sous_ou, limite=40, obligatoire=False),
            }
        )
    return {"noeuds": noeuds, "liens": liens}


def _verifier_methode(d: dict[str, Any], ou: str) -> dict[str, Any]:
    etapes_brutes = d.get("etapes") or []
    if not isinstance(etapes_brutes, list) or not 2 <= len(etapes_brutes) <= LIMITE_ETAPES:
        raise ErreurFicheVisuelle(f"{ou} : entre 2 et {LIMITE_ETAPES} etapes attendues")
    etapes = [
        _texte(e, "etape", f"{ou}, etape {i + 1}", limite=LIMITE_TEXTE, riche=True) for i, e in enumerate(etapes_brutes)
    ]
    return {"etapes": etapes}


def _verifier_piege(d: dict[str, Any], ou: str) -> dict[str, Any]:
    return {
        "mauvaise_idee": _texte(d.get("mauvaise_idee"), "mauvaise_idee", ou, riche=True),
        "pourquoi_faux": _texte(d.get("pourquoi_faux"), "pourquoi_faux", ou, riche=True),
        "bonne_idee": _texte(d.get("bonne_idee"), "bonne_idee", ou, riche=True),
    }


def _verifier_exemple(d: dict[str, Any], ou: str, gabarits: frozenset[str]) -> dict[str, Any]:
    resultat: dict[str, Any] = {
        "situation": _texte(d.get("situation"), "situation", ou, limite=400, riche=True),
        "calcul": _texte(d.get("calcul"), "calcul", ou, limite=400, obligatoire=False, riche=True),
        "conclusion": _texte(d.get("conclusion"), "conclusion", ou, limite=400, riche=True),
    }
    if d.get("figure"):
        if not isinstance(d["figure"], dict):
            raise ErreurFicheVisuelle(f"{ou} : 'figure' doit etre un objet")
        resultat["figure"] = _verifier_figure(d["figure"], f"{ou}, figure", gabarits)
    return resultat


def _verifier_renfort(d: dict[str, Any], ou: str) -> dict[str, Any]:
    liens_bruts = d.get("liens") or []
    if not isinstance(liens_bruts, list) or not liens_bruts:
        raise ErreurFicheVisuelle(f"{ou} : au moins un lien de renforcement attendu")
    if len(liens_bruts) > LIMITE_LIENS_RENFORT:
        raise ErreurFicheVisuelle(f"{ou} : trop de liens (max {LIMITE_LIENS_RENFORT})")
    liens = []
    for i, lien in enumerate(liens_bruts):
        sous_ou = f"{ou}, lien {i + 1}"
        if not isinstance(lien, dict):
            raise ErreurFicheVisuelle(f"{sous_ou} : un objet est attendu")
        liens.append(
            {
                "icone": _texte(lien.get("icone"), "icone", sous_ou, limite=8, obligatoire=False),
                "titre": _texte(lien.get("titre"), "titre", sous_ou, limite=LIMITE_TITRE),
                "description": _texte(
                    lien.get("description"), "description", sous_ou, limite=LIMITE_TEXTE, obligatoire=False
                ),
                "outil": _texte(lien.get("outil"), "outil", sous_ou, limite=40, obligatoire=False),
            }
        )
    return {"liens": liens}


def _verifier_schema(d: dict[str, Any], ou: str, dossier_fiche: Path) -> dict[str, Any]:
    """Bloc `schema` : un SVG nettoye par liste blanche (jules/svg_sur.py), jamais servi brut.

    `svg` est soit un SVG en ligne (commence par `<svg`), soit le nom d'un fichier .svg a cote
    de la fiche (jamais un chemin absolu ni `..` : voir le controle ci-dessous, meme regle que
    pour l'entree d'un outil, jules/outils.py `_controler_entree`).
    """
    titre = _texte(d.get("titre"), "titre", ou, limite=LIMITE_TITRE)
    brut_svg = str(d.get("svg") or "").strip()
    if not brut_svg:
        raise ErreurFicheVisuelle(f"{ou} : champ 'svg' manquant")
    if brut_svg.lstrip().startswith("<svg"):
        source_svg = brut_svg
    else:
        chemin = Path(brut_svg)
        if chemin.is_absolute() or ".." in chemin.parts or chemin.suffix.lower() != ".svg":
            raise ErreurFicheVisuelle(f"{ou} : 'svg' doit etre un SVG en ligne ou un fichier .svg local ({brut_svg!r})")
        fichier = dossier_fiche / chemin
        if not fichier.is_file():
            raise ErreurFicheVisuelle(f"{ou} : fichier SVG introuvable ({brut_svg})")
        if fichier.stat().st_size > TAILLE_MAX_SVG:
            raise ErreurFicheVisuelle(f"{ou} : fichier SVG trop gros ({brut_svg})")
        source_svg = fichier.read_text(encoding="utf-8")
    try:
        propre = nettoyer_svg(source_svg, ou=ou)
        for texte_svg in re.findall(r">([^<]+)<", propre):
            _verifier_division(texte_svg, "svg", ou)
    except ErreurSvg as err:
        raise ErreurFicheVisuelle(str(err)) from err
    return {"titre": titre, "svg": propre}


_VERIFICATEURS = {
    "formule": _verifier_formule,
    "carte": _verifier_carte,
    "methode": _verifier_methode,
    "piege": _verifier_piege,
    "renfort": _verifier_renfort,
}
# Blocs qui peuvent contenir une figure : leur verificateur recoit les gabarits acceptes.
_VERIFICATEURS_FIGURE = {"graphe": _verifier_figure, "exemple": _verifier_exemple}


def _verifier_bloc(
    bloc: dict[str, Any], position: int, nom: str, dossier_fiche: Path, gabarits: frozenset[str]
) -> BlocFiche:
    ou = f"{nom}, bloc {position + 1}"
    if not isinstance(bloc, dict):
        raise ErreurFicheVisuelle(f"{ou} : un objet est attendu")
    identifiant = str(bloc.get("id") or "")
    if not _ID_BLOC.match(identifiant):
        raise ErreurFicheVisuelle(f"{ou} : id {identifiant!r} invalide (minuscules, chiffres, tirets)")
    if identifiant == ID_ATTENDUS:
        raise ErreurFicheVisuelle(f"{ou} : l'id {ID_ATTENDUS!r} est reserve au bloc des attendus officiels")
    type_ = str(bloc.get("type") or "")
    if type_ not in TYPES_BLOCS:
        raise ErreurFicheVisuelle(f"{ou} : type {type_!r} inconnu (attendu : {', '.join(TYPES_BLOCS)})")
    jules = _verifier_jules(bloc.get("jules"), ou)
    champs = {k: v for k, v in bloc.items() if k not in ("id", "type", "jules")}
    if type_ == "schema":
        donnees = _verifier_schema(champs, ou, dossier_fiche)
    elif type_ in _VERIFICATEURS_FIGURE:
        donnees = _VERIFICATEURS_FIGURE[type_](champs, ou, gabarits)
    else:
        donnees = _VERIFICATEURS[type_](champs, ou)
    return BlocFiche(id=identifiant, type=type_, donnees=donnees, jules=jules)


# --- lecture -------------------------------------------------------------------------


def lire_fiche_visuelle(
    chemin: Path, notions: dict[str, Notion], bibliotheque: Bibliotheque, gabarits: frozenset[str]
) -> FicheVisuelle:
    """Lit et verifie une fiche visuelle. Leve ErreurFicheVisuelle avec un message clair sinon.

    `gabarits` : ids des figures acceptees (celles des extensions actives, voir jules/extensions.py).
    """
    nom = chemin.name
    if chemin.stat().st_size > TAILLE_MAX_FICHIER:
        raise ErreurFicheVisuelle(f"{nom} : fichier trop gros")
    try:
        brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as err:
        raise ErreurFicheVisuelle(f"{nom} : YAML illisible ({err})") from err
    if not isinstance(brut, dict):
        raise ErreurFicheVisuelle(f"{nom} : un objet YAML est attendu")
    identifiant = str(brut.get("notion") or "")
    notion = notions.get(identifiant)
    if notion is None:
        raise ErreurFicheVisuelle(f"{nom} : notion {identifiant!r} inconnue du referentiel")
    titre = str(brut.get("titre") or "").strip() or notion.titre
    _verifier_division(titre, "titre", nom)
    licence = str(brut.get("licence") or bibliotheque.licence)
    if licence not in LICENCES_LIBRES:
        raise ErreurFicheVisuelle(f"{nom} : licence {licence!r} non libre ou inconnue")
    sources = brut.get("sources") or []
    if not isinstance(sources, list) or not sources:
        raise ErreurFicheVisuelle(f"{nom} : au moins une source est attendue")
    for source in sources:
        if not isinstance(source, dict) or not str(source.get("url") or "").startswith("https://"):
            raise ErreurFicheVisuelle(f"{nom} : chaque source doit avoir une url https")
        if str(source.get("licence") or "") not in LICENCES_LIBRES:
            raise ErreurFicheVisuelle(f"{nom} : licence de source non libre")
    relecture = str((brut.get("relecture") or {}).get("statut") or "")
    if relecture not in ("a_relire", "relue"):
        raise ErreurFicheVisuelle(f"{nom} : relecture.statut doit etre 'a_relire' ou 'relue'")
    blocs_bruts = brut.get("blocs") or []
    if not isinstance(blocs_bruts, list) or not MIN_BLOCS <= len(blocs_bruts) <= MAX_BLOCS:
        raise ErreurFicheVisuelle(f"{nom} : entre {MIN_BLOCS} et {MAX_BLOCS} blocs attendus")
    blocs = [_verifier_bloc(b, i, nom, chemin.parent, gabarits) for i, b in enumerate(blocs_bruts)]
    ids = [b.id for b in blocs]
    if len(ids) != len(set(ids)):
        raise ErreurFicheVisuelle(f"{nom} : des ids de blocs sont en double")
    return FicheVisuelle(
        notion=identifiant,
        titre=titre,
        matiere=notion.matiere,
        niveau=notion.niveau,
        bibliotheque=bibliotheque.id,
        statut=bibliotheque.statut,
        licence=licence,
        sources=[{k: str(v) for k, v in s.items()} for s in sources if isinstance(s, dict)],
        relecture=relecture,
        blocs=blocs,
        avertissement=bibliotheque.avertissement,
        variables=_verifier_variables(brut.get("variables"), nom),
    )


def charger_fiches_visuelles(
    racine: Racines, ids: list[str], notions: dict[str, Notion], gabarits: frozenset[str]
) -> dict[str, FicheVisuelle]:
    """Fiches visuelles des bibliotheques citees, par ordre de priorite (une notion = une fiche).

    Une fiche non conforme est signalee dans le journal et ecartee : Jules continue sans elle.
    """
    import logging

    journal = logging.getLogger("jules.fiches_visuelles")
    fiches: dict[str, FicheVisuelle] = {}
    for identifiant in ids:
        try:
            biblio = lire_identite(dossier_bibliotheque(racine, identifiant))
        except (ErreurBibliotheque, OSError, yaml.YAMLError) as err:
            journal.error("Bibliotheque de fiches visuelles %s ecartee : %s", identifiant, err)
            continue
        if biblio.type != "fiches-visuelles":
            journal.error("Bibliotheque %s : type %r, 'fiches-visuelles' attendu", identifiant, biblio.type)
            continue
        for fichier in sorted((biblio.dossier / "fiches").rglob("*.yaml")):
            try:
                fiche = lire_fiche_visuelle(fichier, notions, biblio, gabarits)
            except (ErreurFicheVisuelle, OSError) as err:
                journal.error("Fiche visuelle ecartee : %s", err)
                continue
            fiches.setdefault(fiche.notion, fiche)
    return fiches
