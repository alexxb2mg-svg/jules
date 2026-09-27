"""Page parent : amenagements du PAP, preferences hors PAP et conflits (docs/spec/ADAPTATIONS-LOT2.md, EX-108).

- `niveau_de_classe` deduit le niveau du PAP (maternelle, elementaire, college, lycee) de la classe du profil ;
- `etat` prepare ce que la page affiche : libelle PAP du niveau de l'eleve, ou la rubrique « Autres
  amenagements et adaptations » avec la mention « a inscrire par l'equipe educative » (§3), les
  preferences hors PAP (police, fond, lecture automatique) et les conflits renvoyes par EX-104, montres
  tels quels sans rien trancher (§4) ;
- `valider_choix` refuse, avec un message, toute entree hors liste avant l'appel a `resoudre` : un
  amenagement inconnu, une preference hors §3 ou une valeur hors de la liste fermee du levier (y compris
  une valeur non hachable) n'y arrive jamais ;
- `enregistrer` ecrit dans le profil les seules cles `amenagements` (liste d'identifiants) et
  `preferences` (identifiant de levier -> identifiant de valeur). Le reste du fichier est garde tel quel.

Aucun nom de trouble ici : la page ne montre que les libelles du PAP et des mots neutres.
"""

from __future__ import annotations

import logging
import os
import re
import tempfile
import time
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jules.amenagements import (
    MENTION_AUTRES,
    NIVEAUX,
    PAGES_RUBRIQUE_AUTRES,
    RUBRIQUE_AUTRES,
    Amenagement,
    charger_amenagements,
)
from jules.combinaison import PREFERENCES_PARENT, resoudre
from jules.composition import lire_ids_amenagements
from jules.leviers import Levier, charger_leviers

journal = logging.getLogger("jules")

CLE_AMENAGEMENTS = "amenagements"
CLE_PREFERENCES = "preferences"
NIVEAU_PAR_DEFAUT = "college"  # classe absente ou non reconnue : Jules vise d'abord le college
NOMS_NIVEAUX = {"maternelle": "maternelle", "elementaire": "élémentaire", "college": "collège", "lycee": "lycée"}
# Libelles affiches pour les valeurs des preferences (les identifiants restent dans le profil).
LIBELLES_VALEURS = {
    "police": {"defaut": "Police habituelle de Jules", "arial": "Arial", "verdana": "Verdana"},
    "fond": {"blanc": "Blanc", "creme": "Crème", "bleu-pale": "Bleu pâle"},
}
LECTURE_AUTOMATIQUE = "automatique"
AMENAGEMENTS_MAX = 50

_CLASSES = (
    ("maternelle", r"(ps|ms|gs|tps|petite section|moyenne section|grande section|maternelle)"),
    ("elementaire", r"(cp|ce ?1|ce ?2|cm ?1|cm ?2|elementaire)"),
    ("college", r"([3-6] ?(e|eme)?|sixieme|cinquieme|quatrieme|troisieme|college)"),
    ("lycee", r"(2 ?(nde|de)|seconde|1 ?(re|ere)|premiere|t|tle|terminale|lycee)"),
)


class ChoixInvalide(ValueError):
    """Entree de la page parent refusee avant tout appel a `resoudre` (message montre au parent)."""


def _normaliser(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte.casefold())
    return " ".join("".join(c for c in decompose if not unicodedata.combining(c)).split())


def niveau_de_classe(classe: str | None) -> str | None:
    """Niveau du PAP pour une classe (« 4e », « CM1 », « 2nde »...), None si non reconnue."""
    texte = _normaliser(str(classe or ""))
    for niveau, motif in _CLASSES:
        if re.fullmatch(rf"{motif}\b.*", texte):
            return niveau
    return None


@dataclass(frozen=True)
class Choix:
    amenagements: list[str]  # identifiants du catalogue coches par le parent
    preferences: dict[str, str]  # levier -> identifiant de valeur (liste fermee)


def valider_preferences(brut: Any, leviers: Mapping[str, Levier]) -> dict[str, str]:
    """Preferences hors PAP (§3) validees ; toute autre entree leve ChoixInvalide, sans rien transmettre."""
    if brut is None:
        return {}
    if not isinstance(brut, Mapping):
        raise ChoixInvalide("Préférences : un ensemble de réglages est attendu.")
    preferences: dict[str, str] = {}
    for nom, valeur in brut.items():
        if not isinstance(nom, str) or nom not in PREFERENCES_PARENT or nom not in leviers:
            raise ChoixInvalide(f"Préférence non prévue : {str(nom)[:40]!r}.")
        levier = leviers[nom]
        permises = PREFERENCES_PARENT[nom]
        admises = [v for v in levier.valeurs if permises is None or v in permises]
        # Comparaison par egalite a une liste de chaines : une valeur non hachable est refusee, pas levee.
        if not isinstance(valeur, str) or valeur not in admises:
            raise ChoixInvalide(f"Valeur non prévue pour {nom} : choisir parmi {', '.join(admises)}.")
        if valeur == levier.neutre:
            continue  # la valeur neutre n'est pas une preference : rien a enregistrer
        preferences[nom] = valeur
    return preferences


def valider_choix(amenagements: Any, preferences: Any, catalogue: Mapping[str, Amenagement], leviers) -> Choix:
    if not isinstance(amenagements, list) or len(amenagements) > AMENAGEMENTS_MAX:
        raise ChoixInvalide("Aménagements : une liste d'identifiants est attendue.")
    ids: list[str] = []
    for ident in amenagements:
        if not isinstance(ident, str) or ident not in catalogue:
            raise ChoixInvalide(f"Aménagement inconnu : {str(ident)[:40]!r}.")
        if ident not in ids:
            ids.append(ident)
    return Choix(ids, valider_preferences(preferences, leviers))


def lire_profil(chemin: Path) -> dict[str, Any]:
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) if chemin.is_file() else None
    return brut if isinstance(brut, dict) else {}


def preferences_du_profil(brut: Mapping[str, Any], leviers: Mapping[str, Levier]) -> dict[str, str]:
    """Preferences lues dans le profil ; un profil modifie a la main et invalide est ignore et journalise."""
    try:
        return valider_preferences(brut.get(CLE_PREFERENCES), leviers)
    except ChoixInvalide:
        journal.warning("Preferences du profil invalides, ignorees (voir docs/spec/ADAPTATIONS-LOT2.md, §3)")
        return {}


def etat(chemin_profil: Path, choix: Choix | None = None) -> dict[str, Any]:
    """Ce que la page parent affiche. `choix` (valide) remplace ce qui est enregistre : apercu des conflits."""
    leviers = charger_leviers()
    catalogue = charger_amenagements(leviers=leviers)
    brut = lire_profil(chemin_profil)
    classe = str(brut.get("classe") or "")
    reconnu = niveau_de_classe(classe)
    niveau = reconnu or NIVEAU_PAR_DEFAUT
    ids_profil = lire_ids_amenagements(brut.get(CLE_AMENAGEMENTS))
    if choix is None:
        coches = [i for i in ids_profil if i in catalogue]
        preferences = preferences_du_profil(brut, leviers)
    else:
        coches, preferences = choix.amenagements, choix.preferences

    lignes = []
    for amenagement in catalogue.values():
        affichage = amenagement.affichage(niveau)
        if affichage is None:
            continue  # maternelle sans libelle : pas de rubrique « Autres » a ce niveau (§3)
        ligne: dict[str, Any] = {
            "id": amenagement.id,
            "coche": amenagement.id in coches,
            "rubrique_autres": affichage.rubrique_autres,
            "texte": affichage.texte,
            "page": affichage.page,
        }
        if affichage.rubrique_autres:
            # Intitule de reference : le libelle d'un autre niveau, cite avec son niveau et sa page.
            ligne["mention"] = affichage.mention
            ligne["reference"] = _reference(amenagement, niveau)
        lignes.append(ligne)

    resolution = resoudre(coches, preferences, amenagements=catalogue, leviers=leviers)
    return {
        "classe": classe,
        "niveau": niveau,
        "nom_niveau": NOMS_NIVEAUX[niveau],
        "niveau_reconnu": reconnu is not None,
        "rubrique_autres": {
            "titre": RUBRIQUE_AUTRES,
            "page": PAGES_RUBRIQUE_AUTRES.get(niveau),
            "mention": MENTION_AUTRES,
        },
        "amenagements": lignes,
        "preferences": {
            nom: {
                "valeur": preferences.get(nom, leviers[nom].neutre),
                "choix": [{"valeur": v, "libelle": LIBELLES_VALEURS[nom].get(v, v)} for v in leviers[nom].valeurs],
            }
            for nom in ("police", "fond")
        },
        "lecture_automatique": preferences.get("lecture-vocale") == LECTURE_AUTOMATIQUE,
        "conflits": [{"id": c.id, "message": c.message} for c in resolution.conflits],
    }


def _reference(amenagement: Amenagement, niveau: str) -> dict[str, Any] | None:
    ordre = sorted(NIVEAUX, key=lambda n: abs(NIVEAUX.index(n) - NIVEAUX.index(niveau)))
    for autre in ordre:
        if libelle := amenagement.libelles.get(autre):
            return {"niveau": autre, "nom_niveau": NOMS_NIVEAUX[autre], "page": libelle.page, "texte": libelle.texte}
    return None


def choix_depuis_entree(amenagements: Any, preferences: Any) -> Choix:
    leviers = charger_leviers()
    return valider_choix(amenagements, preferences, charger_amenagements(leviers=leviers), leviers)


def enregistrer(chemin_profil: Path, choix: Choix) -> None:
    """Ecrit `amenagements` et `preferences` (identifiants seulement) ; le reste du profil est garde tel quel.

    Les identifiants du profil absents du catalogue (amenagements du lot 1, actifs par leurs consignes)
    restent en tete, dans leur ordre. Ecriture atomique, verifiee par relecture.
    """
    catalogue = charger_amenagements()
    texte = chemin_profil.read_text(encoding="utf-8") if chemin_profil.is_file() else ""
    avant = yaml.safe_load(texte) if texte.strip() else {}
    if not isinstance(avant, dict):
        raise ChoixInvalide("Le profil n'est pas lisible : rien n'a été enregistré.")
    gardes = [i for i in lire_ids_amenagements(avant.get(CLE_AMENAGEMENTS)) if i not in catalogue]
    ids = [*gardes, *[i for i in choix.amenagements if i not in gardes]]

    lignes = _sans_cles(texte.splitlines(), (CLE_AMENAGEMENTS, CLE_PREFERENCES))
    while lignes and not lignes[-1].strip():
        lignes.pop()
    ajout: dict[str, Any] = {CLE_AMENAGEMENTS: ids}
    if choix.preferences:
        ajout[CLE_PREFERENCES] = dict(choix.preferences)
    nouveau = "\n".join(lignes) + ("\n" if lignes else "")
    nouveau += yaml.safe_dump(ajout, allow_unicode=True, sort_keys=False, default_flow_style=False)

    apres = yaml.safe_load(nouveau)
    attendu = {k: v for k, v in avant.items() if k not in (CLE_AMENAGEMENTS, CLE_PREFERENCES)} | ajout
    if apres != attendu:
        raise ChoixInvalide("Le profil n'a pas pu être réécrit sans risque : rien n'a été enregistré.")
    descripteur, temporaire = tempfile.mkstemp(dir=chemin_profil.parent, prefix=".profil-", suffix=".yaml")
    try:
        with os.fdopen(descripteur, "w", encoding="utf-8", newline="\n") as fichier:
            fichier.write(nouveau)
        _remplacer(Path(temporaire), chemin_profil)
    except BaseException:
        Path(temporaire).unlink(missing_ok=True)
        raise


def _remplacer(source: Path, cible: Path, essais: int = 40, pause: float = 0.01) -> None:
    """os.replace avec reessai : sous Windows, un lecteur qui tient le profil ouvert (serveur, antivirus)
    fait echouer le remplacement en PermissionError le temps de sa lecture. Pause croissante plafonnee a
    0,1 s ; au-dela d'environ 3,5 s l'erreur remonte (rien n'est enregistre)."""
    for essai in range(essais):
        try:
            source.replace(cible)
            return
        except PermissionError:
            if essai == essais - 1:
                raise
            time.sleep(min(pause * 2**essai, 0.1))


def _sans_cles(lignes: list[str], cles: tuple[str, ...]) -> list[str]:
    """Retire les blocs de premier niveau `cle:` (et leurs lignes indentees ou de liste) du texte YAML."""
    motif = re.compile(rf"^(?:{'|'.join(re.escape(c) for c in cles)})\s*:")
    gardees: list[str] = []
    dans_bloc = False
    for ligne in lignes:
        if motif.match(ligne):
            dans_bloc = True
            continue
        if dans_bloc and ligne.strip() and (ligne[0] in " \t" or ligne.startswith("-")):
            continue
        dans_bloc = False
        gardees.append(ligne)
    return gardees
