"""Commande `jules fiches` : verifier et signer les fiches v2, et controler l'index des declencheurs.

  jules fiches verifier [DOSSIER...]   contrat v2, prerequis, index (collisions) ; code de sortie 1 si manquement
  jules fiches signer DOSSIER...       scelle les fiches conformes (etat verifiee, empreinte, version)

Sans DOSSIER : toutes les bibliotheques qui contiennent des fiches v2, dans `bibliotheque/` et dans les depots
externes declares (`bibliotheques_externes`). Le referentiel `programme` sert a verifier `notion` et `prerequis`.

Une bibliotheque peut aussi porter des `propositions/<matiere>/<notion>/<auteur>.yaml` : d'autres generations
pour une notion qui a deja sa fiche (ou pas encore). Elles sont verifiees comme les fiches, mais jamais servies :
un relecteur choisit, fusionne ou deplace vers `fiches/`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from jules.bibliotheques import Racines, charger_catalogue, liste_racines
from jules.fiches.schema import collisions, est_v2, signer, verifier_fiche

ENTETE = (
    "# Fiche v2 (format : docs/FICHES-V2.md). EXPÉRIMENTALE tant que `relecture.statut` n'est pas `relue`.\n"
    "# Licence : voir `sources` et le bibliotheque.yaml du dossier. Relecture bienvenue.\n"
)
SOUS_DOSSIERS = ("fiches", "propositions")  # propositions : generations en attente de choix, jamais servies


def est_proposition(dossier: Path, chemin: Path) -> bool:
    return chemin.is_relative_to(dossier / "propositions")


def lire_fiches(dossier: Path) -> tuple[dict[Path, dict[str, Any]], dict[Path, str]]:
    """(fiches v2, fichiers illisibles avec la raison). Un YAML casse est un manquement, pas un plantage :
    c'est l'erreur la plus frequente d'une fiche generee (un « : » non protege dans un texte)."""
    trouvees: dict[Path, dict[str, Any]] = {}
    illisibles: dict[Path, str] = {}
    for sous_dossier in SOUS_DOSSIERS:
        for chemin in sorted((dossier / sous_dossier).rglob("*.yaml")):
            try:
                contenu = yaml.safe_load(chemin.read_text(encoding="utf-8"))
            except (yaml.YAMLError, UnicodeDecodeError) as err:
                illisibles[chemin] = " ".join(str(err).split())
                continue
            if isinstance(contenu, dict) and est_v2(contenu):
                trouvees[chemin] = contenu
    return trouvees, illisibles


def fiches_v2(dossier: Path) -> dict[Path, dict[str, Any]]:
    return lire_fiches(dossier)[0]


def dossiers_par_defaut(racines: Racines) -> list[Path]:
    return [
        p.parent
        for racine in liste_racines(racines)
        for p in sorted(racine.glob("*/bibliotheque.yaml"))
        if fiches_v2(p.parent)
    ]


def notions_du_referentiel(racines: Racines) -> set[str]:
    return set(charger_catalogue(racines, ["programme"], None).notions)


def erreur_de_nom(dossier: Path, chemin: Path, fiche: dict[str, Any]) -> str | None:
    """Une fiche s'appelle `<notion>.yaml` ; une proposition vit dans un dossier `<notion>/`."""
    notion = fiche.get("notion")
    if est_proposition(dossier, chemin):
        if chemin.parent.name != notion:
            return f"{chemin.name} : une proposition se range dans propositions/<matiere>/{notion}/"
        return None
    if chemin.stem != notion:
        return f"{chemin.name} : le nom du fichier doit etre l'identifiant de la notion"
    return None


def verifier(racines: Racines, dossiers: list[Path]) -> int:
    notions = notions_du_referentiel(racines)
    manquements = 0
    for dossier in dossiers:
        fiches, illisibles = lire_fiches(dossier)
        print(f"{dossier.name} : {len(fiches)} fiche(s) v2")
        for chemin, raison in illisibles.items():
            manquements += 1
            print(f"  {chemin.relative_to(dossier).as_posix()} YAML illisible")
            print(f"    - {raison} (un texte qui contient « : » ou commence par un signe doit etre entre guillemets)")
        for chemin, fiche in fiches.items():
            erreurs = verifier_fiche(fiche, notions)
            nom = erreur_de_nom(dossier, chemin, fiche)
            if nom:
                erreurs.append(nom)
            manquements += len(erreurs)
            etat = "OK" if not erreurs else f"{len(erreurs)} manquement(s)"
            print(f"  {chemin.relative_to(dossier).as_posix()} [{fiche.get('etat')}] {etat}")
            for erreur in erreurs:
                print(f"    - {erreur}")
        # Les collisions se mesurent entre fiches servies : une proposition double sa notion, par nature.
        servies = {str(f.get("notion")): f for c, f in fiches.items() if not est_proposition(dossier, c)}
        doublons = collisions(servies)
        for declencheur, visees in doublons.items():
            print(f"  - declencheur « {declencheur} » revendique par : {', '.join(sorted(visees))}")
        manquements += len(doublons)
    print("Conforme." if not manquements else f"{manquements} manquement(s).")
    return 1 if manquements else 0


def signer_dossiers(racines: Racines, dossiers: list[Path]) -> int:
    notions = notions_du_referentiel(racines)
    refus = 0
    for dossier in dossiers:
        for chemin, fiche in fiches_v2(dossier).items():
            signee, erreurs = signer(fiche, notions)
            if erreurs:
                refus += 1
                print(f"REFUS {chemin.name} : {len(erreurs)} manquement(s), lancer `jules fiches verifier`")
                continue
            if signee != fiche:
                texte = yaml.safe_dump(signee, allow_unicode=True, sort_keys=False, width=120)
                chemin.write_text(ENTETE + texte, encoding="utf-8")
                print(f"signee {chemin.name} : version {signee['version']}, {signee['empreinte'][:19]}...")
            else:
                print(f"inchangee {chemin.name}")
    return 1 if refus else 0


def main(args: list[str], racines: Racines) -> None:
    if not args or args[0] not in ("verifier", "signer"):
        print(__doc__)
        return
    dossiers = [Path(a).resolve() for a in args[1:]] or dossiers_par_defaut(racines)
    if args[0] == "signer" and not args[1:]:
        sys.exit("Indiquer le ou les dossiers a signer (la signature reecrit les fichiers).")
    code = verifier(racines, dossiers) if args[0] == "verifier" else signer_dossiers(racines, dossiers)
    sys.exit(code)
