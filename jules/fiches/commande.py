"""Commande `jules fiches` : verifier et signer les fiches v2, et controler l'index des declencheurs.

  jules fiches verifier [DOSSIER...]   contrat v2, prerequis, index (collisions) ; code de sortie 1 si manquement
  jules fiches signer DOSSIER...       scelle les fiches conformes (etat verifiee, empreinte, version)

Sans DOSSIER : toutes les bibliotheques de `bibliotheque/` qui contiennent des fiches v2.
Le referentiel de `bibliotheque/programme` sert a verifier `notion` et `prerequis`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from jules.bibliotheques import charger_catalogue
from jules.fiches.schema import collisions, est_v2, signer, verifier_fiche

ENTETE = (
    "# Fiche v2 (format : docs/FICHES-V2.md). EXPÉRIMENTALE tant que `relecture.statut` n'est pas `relue`.\n"
    "# Licence : voir `sources` et le bibliotheque.yaml du dossier. Relecture bienvenue.\n"
)


def fiches_v2(dossier: Path) -> dict[Path, dict[str, Any]]:
    trouvees = {}
    for chemin in sorted((dossier / "fiches").rglob("*.yaml")):
        contenu = yaml.safe_load(chemin.read_text(encoding="utf-8"))
        if isinstance(contenu, dict) and est_v2(contenu):
            trouvees[chemin] = contenu
    return trouvees


def dossiers_par_defaut(racine: Path) -> list[Path]:
    return [p.parent for p in sorted(racine.glob("*/bibliotheque.yaml")) if fiches_v2(p.parent)]


def notions_du_referentiel(racine: Path) -> set[str]:
    return set(charger_catalogue(racine, ["programme"], None).notions)


def verifier(racine: Path, dossiers: list[Path]) -> int:
    notions = notions_du_referentiel(racine)
    manquements = 0
    for dossier in dossiers:
        fiches = fiches_v2(dossier)
        print(f"{dossier.name} : {len(fiches)} fiche(s) v2")
        for chemin, fiche in fiches.items():
            erreurs = verifier_fiche(fiche, notions)
            if chemin.stem != fiche.get("notion"):
                erreurs.append(f"{chemin.name} : le nom du fichier doit etre l'identifiant de la notion")
            manquements += len(erreurs)
            etat = "OK" if not erreurs else f"{len(erreurs)} manquement(s)"
            print(f"  {chemin.parent.name}/{chemin.name} [{fiche.get('etat')}] {etat}")
            for erreur in erreurs:
                print(f"    - {erreur}")
        doublons = collisions({str(f.get("notion")): f for f in fiches.values()})
        for declencheur, visees in doublons.items():
            print(f"  - declencheur « {declencheur} » revendique par : {', '.join(sorted(visees))}")
        manquements += len(doublons)
    print("Conforme." if not manquements else f"{manquements} manquement(s).")
    return 1 if manquements else 0


def signer_dossiers(racine: Path, dossiers: list[Path]) -> int:
    notions = notions_du_referentiel(racine)
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


def main(args: list[str], racine: Path) -> None:
    if not args or args[0] not in ("verifier", "signer"):
        print(__doc__)
        return
    dossiers = [Path(a).resolve() for a in args[1:]] or dossiers_par_defaut(racine)
    if args[0] == "signer" and not args[1:]:
        sys.exit("Indiquer le ou les dossiers a signer (la signature reecrit les fichiers).")
    code = verifier(racine, dossiers) if args[0] == "verifier" else signer_dossiers(racine, dossiers)
    sys.exit(code)
