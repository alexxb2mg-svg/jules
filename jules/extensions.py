"""Extensions : le contrat unique de Jules (voir `docs/EXTENSIONS.md`).

Une extension = un dossier `extensions/<id>/` avec un manifeste `extension.yaml` qui declare ce
qu'elle fournit (modules, moteurs, notifieurs, outils, figures, types de blocs, bibliotheques) et
ses permissions (reseau, appel IA, ecriture dans le dossier eleve, notification parent).

Ce module ne fait que lire, verifier et charger la liste des extensions ACTIVEES (citees dans
`extensions:` de config.yaml). Le Tuteur les charge une fois au demarrage (`Tuteur.extensions`) ;
deux familles en dependent deja (etape 2 de jules_architecture_plugins.md) :
  - figures : le code `gabarit.js` de l'extension (voir `code_des_figures`), et les ids de
    `fournit.figures` sont les seuls gabarits acceptes dans une fiche visuelle ;
  - outils : chaque outil fourni est lu par jules/outils.py comme un dossier `outils/<id>/`
    (voir `dossiers_outils`).
Les autres familles (modules, moteurs, notifieurs, bibliotheques) restent chargees comme avant.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from jules.outils import _MOTIFS_INTERDITS

journal = logging.getLogger("jules.extensions")

_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAILLE_MAX_FICHIER = 50_000  # octets : un manifeste est un petit fichier declaratif
TAILLE_MAX_GABARIT = 200_000  # octets : meme plafond que le code d'un outil (jules/outils.py)
FICHIER_FIGURES = "gabarit.js"  # code des figures d'une extension (un seul fichier, une ou plusieurs figures)
# Le seul "http://" admis dans un gabarit : l'espace de noms SVG passe a createElementNS (ce n'est
# pas un appel reseau). Toute autre adresse reste refusee par le premier filtre des outils.
_ESPACE_SVG = "http://www.w3.org/2000/svg"

# Familles connues sous `fournit:` (le coeur ne connait aucune extension par son nom, mais il
# connait les familles : elargir le contrat = ajouter une cle ici, jamais un cas particulier).
CLES_FOURNIT = frozenset({"modules", "moteurs", "notifieurs", "outils", "figures", "types_de_blocs", "bibliotheques"})
# Permissions connues sous `permissions:` ; toute cle absente vaut False.
CLES_PERMISSIONS = frozenset({"reseau", "appel_ia", "ecriture_dossier_eleve", "notification_parent"})


class ErreurExtension(ValueError):
    """Manifeste illisible ou non conforme : le message dit quoi corriger, en francais."""


@dataclass
class Extension:
    id: str
    titre: str
    version: str
    licence: str
    dossier: Path
    auteurs: list[str] = field(default_factory=list)
    fournit: dict[str, list[str]] = field(default_factory=dict)
    permissions: dict[str, bool] = field(default_factory=dict)

    def fournit_liste(self, famille: str) -> list[str]:
        """Ce que l'extension fournit dans une famille donnee (liste vide si elle n'y touche pas)."""
        return list(self.fournit.get(famille, []))

    def a_permission(self, nom: str) -> bool:
        return bool(self.permissions.get(nom, False))


def _lire_yaml(chemin: Path) -> dict[str, Any]:
    if chemin.stat().st_size > TAILLE_MAX_FICHIER:
        raise ErreurExtension(f"{chemin.name} : fichier trop gros")
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    if not isinstance(brut, dict):
        raise ErreurExtension(f"{chemin.name} : un objet YAML est attendu")
    return brut


def _texte_obligatoire(brut: dict[str, Any], champ: str, identifiant: str) -> str:
    valeur = str(brut.get(champ) or "").strip()
    if not valeur:
        raise ErreurExtension(f"{identifiant} : champ {champ!r} manquant")
    return valeur


def _liste_textes(valeur: Any, ou: str) -> list[str]:
    if valeur is None:
        return []
    if not isinstance(valeur, list) or not all(isinstance(v, str) for v in valeur):
        raise ErreurExtension(f"{ou} : une liste de textes est attendue")
    return list(valeur)


def _lire_fournit(brut: Any, identifiant: str) -> dict[str, list[str]]:
    if brut is None:
        return {}
    if not isinstance(brut, dict):
        raise ErreurExtension(f"{identifiant} : 'fournit' doit etre un objet")
    inconnues = set(brut) - CLES_FOURNIT
    if inconnues:
        raise ErreurExtension(
            f"{identifiant} : 'fournit' contient une cle inconnue ({', '.join(sorted(inconnues))}), "
            f"attendu parmi {', '.join(sorted(CLES_FOURNIT))}"
        )
    return {cle: _liste_textes(valeur, f"{identifiant}, fournit.{cle}") for cle, valeur in brut.items()}


def _lire_permissions(brut: Any, identifiant: str) -> dict[str, bool]:
    if brut is None:
        return {}
    if not isinstance(brut, dict):
        raise ErreurExtension(f"{identifiant} : 'permissions' doit etre un objet")
    inconnues = set(brut) - CLES_PERMISSIONS
    if inconnues:
        raise ErreurExtension(
            f"{identifiant} : 'permissions' contient une cle inconnue ({', '.join(sorted(inconnues))}), "
            f"attendu parmi {', '.join(sorted(CLES_PERMISSIONS))}"
        )
    resultat: dict[str, bool] = {}
    for cle, valeur in brut.items():
        if not isinstance(valeur, bool):
            raise ErreurExtension(f"{identifiant} : permission {cle!r} doit etre un booleen (true/false)")
        resultat[cle] = valeur
    return resultat


def _controler_gabarit(chemin: Path, identifiant: str) -> None:
    """Le code des figures s'execute dans la page de l'eleve (pas dans une iframe isolee comme un
    outil) : meme premier filtre que le code d'un outil (jules/outils.py), avant la relecture."""
    if not chemin.is_file():
        raise ErreurExtension(f"{identifiant} : fournit des figures mais {FICHIER_FIGURES} est absent")
    if chemin.stat().st_size > TAILLE_MAX_GABARIT:
        raise ErreurExtension(f"{identifiant} : {FICHIER_FIGURES} trop gros")
    # Les lignes de commentaire entieres sont ignorees ("// ... aucun eval()" est une promesse, pas
    # un appel) ; une ligne de commentaire ne peut rien executer.
    lignes = chemin.read_text(encoding="utf-8", errors="replace").splitlines()
    texte = "\n".join(ligne for ligne in lignes if not ligne.strip().startswith("//")).replace(_ESPACE_SVG, "")
    for motif, nom in _MOTIFS_INTERDITS:
        if motif.search(texte):
            raise ErreurExtension(f"{identifiant} : {FICHIER_FIGURES}, motif interdit ({nom})")


def lire_extension(dossier: Path) -> Extension:
    """Lit et verifie `extension.yaml`. Leve ErreurExtension avec un message clair sinon."""
    fichier = dossier / "extension.yaml"
    if not fichier.is_file():
        raise ErreurExtension(f"{dossier.name} : extension.yaml manquant")
    brut = _lire_yaml(fichier)
    identifiant = str(brut.get("id") or "")
    if identifiant != dossier.name:
        raise ErreurExtension(f"{dossier.name} : l'id ({identifiant!r}) doit etre le nom du dossier")
    if not _ID.match(identifiant):
        raise ErreurExtension(f"{identifiant} : identifiant invalide (attendu : minuscules-et-tirets)")
    titre = _texte_obligatoire(brut, "titre", identifiant)
    version = _texte_obligatoire(brut, "version", identifiant)
    licence = _texte_obligatoire(brut, "licence", identifiant)
    auteurs = _liste_textes(brut.get("auteurs"), f"{identifiant}, auteurs")
    fournit = _lire_fournit(brut.get("fournit"), identifiant)
    permissions = _lire_permissions(brut.get("permissions"), identifiant)
    if fournit.get("figures"):
        _controler_gabarit(dossier / FICHIER_FIGURES, identifiant)
    return Extension(
        id=identifiant,
        titre=titre,
        version=version,
        licence=licence,
        dossier=dossier,
        auteurs=auteurs,
        fournit=fournit,
        permissions=permissions,
    )


def decouvrir_extensions(racine: Path) -> dict[str, Extension]:
    """Toutes les extensions valides de `racine` (dossier `extensions/`), quel que soit leur activation."""
    trouvees: dict[str, Extension] = {}
    if not racine.is_dir():
        return trouvees
    for dossier in sorted(p for p in racine.iterdir() if p.is_dir()):
        try:
            trouvees[dossier.name] = lire_extension(dossier)
        except (ErreurExtension, OSError, yaml.YAMLError) as err:
            journal.error("Extension %s ecartee : %s", dossier.name, err)
    return trouvees


def charger_extensions(racine: Path, ids_actives: list[str]) -> dict[str, Extension]:
    """Charge uniquement les extensions activees dans `config.yaml` (cle `extensions:`).

    Absente de la configuration ou vide : aucune extension externe n'est chargee. Un id active
    mais introuvable ou invalide est signale et ignore : Jules continue sans lui, comme pour une
    bibliotheque ou un outil (voir jules/bibliotheques.py, jules/outils.py).
    """
    disponibles = decouvrir_extensions(racine)
    chargees: dict[str, Extension] = {}
    for identifiant in ids_actives:
        extension = disponibles.get(identifiant)
        if extension is None:
            journal.error("Extension activee introuvable ou invalide : %s", identifiant)
            continue
        chargees[identifiant] = extension
    return chargees


def figures_fournies(extensions: dict[str, Extension]) -> dict[str, str]:
    """Association {id de gabarit -> id de l'extension qui le fournit}, pour verification."""
    resultat: dict[str, str] = {}
    for extension in extensions.values():
        for figure in extension.fournit_liste("figures"):
            resultat[figure] = extension.id
    return resultat


def code_des_figures(extensions: dict[str, Extension]) -> str:
    """Les `gabarit.js` des extensions actives qui fournissent des figures, mis bout a bout (dans
    l'ordre de `extensions:`) : c'est le seul script de figures que charge la page d'accueil."""
    morceaux = []
    for extension in extensions.values():
        if extension.fournit_liste("figures"):
            code = (extension.dossier / FICHIER_FIGURES).read_text(encoding="utf-8")
            morceaux.append(f"// --- extension {extension.id} ---\n{code}\n;")
    return "\n".join(morceaux)


def dossiers_outils(extensions: dict[str, Extension]) -> list[Path]:
    """Dossier de chaque outil fourni : l'extension elle-meme si l'outil porte son id (cas d'une
    extension qui embarque un seul outil), sinon son sous-dossier `<id de l'outil>/`."""
    return [
        extension.dossier if outil == extension.id else extension.dossier / outil
        for extension in extensions.values()
        for outil in extension.fournit_liste("outils")
    ]
