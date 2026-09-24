"""Ligne de commande de Jules.

  jules installer            assistant : profil de l'enfant et choix du moteur d'IA
  jules                      demarre le serveur (page eleve : /, page parent : /parent)
  jules verifier             charge toutes les briques et affiche le prompt assemble
  jules code eleve           definit le code d'acces eleve (idem : parent)
  jules rapport [JOUR]       affiche le rapport d'un jour (AAAA-MM-JJ), sans l'envoyer

Sans installation : `python lancer.py <commande>` depuis le dossier du projet.
"""

from __future__ import annotations

import getpass
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

from jules.acces import LONGUEUR_MIN, ROLES, code_evident, empreinte, verifier_exposition
from jules.config import RACINE, charger_config
from jules.moteur import Tuteur
from jules.stockage import Conversation

FICHIER_CONFIG = RACINE / "config.yaml"
FICHIER_LOCAL = RACINE / "config.local.yaml"
ENTETE_LOCAL = (
    "# Reglages propres a cette famille (profil, codes d'acces, moteur IA...).\n"
    "# Fusionne par-dessus config.yaml. Ce fichier n'est jamais publie (.gitignore).\n"
)


def journaliser(dossier: Path) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s : %(message)s",
        handlers=[logging.FileHandler(dossier / "jules.log", encoding="utf-8"), logging.StreamHandler()],
    )


def servir() -> None:
    import uvicorn

    from jules.planificateur import Planificateur
    from jules.web.app import creer_app

    config = charger_config(FICHIER_CONFIG)
    verifier_exposition(config.hote, config.acces)
    journaliser(config.donnees)
    tuteur = Tuteur(config)
    planificateur = Planificateur(tuteur.taches(), tuteur.stockage)
    planificateur.demarrer()
    print(f"Jules : http://{config.hote}:{config.port}/  (parent : /parent)")
    try:
        uvicorn.run(creer_app(tuteur), host=config.hote, port=config.port, log_level="warning")
    finally:
        planificateur.arreter()
        tuteur.fermer()


def verifier() -> None:
    config = charger_config(FICHIER_CONFIG)
    tuteur = Tuteur(config)
    conv = Conversation(id="verification", debut="", mode="aide-devoirs", titre="")
    print(f"Persona : {tuteur.persona().nom} | profil : {tuteur.profil().prenom} ({tuteur.profil().genre})")
    print(f"Moteur : {type(tuteur.llm).__module__}")
    print("Modules : " + ", ".join(m.id for m in tuteur.modules))
    print("Notifieurs : " + ", ".join(type(n).__module__ for n in tuteur.notifieurs))
    print("Taches : " + ", ".join(f"{t.nom} @ {t.heure}" for t in tuteur.taches()))
    print("\n----- PROMPT SYSTEME ASSEMBLE -----\n")
    print(tuteur.systeme(conv))
    tuteur.fermer()


def enregistrer_code(fichier: Path, role: str, code: str) -> None:
    """Ecrit l'empreinte du code dans config.local.yaml (cree au besoin), jamais le code lui-meme."""
    local: dict[str, Any] = {}
    if fichier.is_file():
        local = yaml.safe_load(fichier.read_text(encoding="utf-8")) or {}
    local.setdefault("acces", {})[f"code_{role}"] = empreinte(code)
    contenu = ENTETE_LOCAL + yaml.safe_dump(local, allow_unicode=True, sort_keys=False)
    fichier.write_text(contenu, encoding="utf-8")


def definir_code(role: str) -> None:
    if role not in ROLES:
        sys.exit(f"Role inconnu : {role} (attendu : {', '.join(ROLES)})")
    minimum = LONGUEUR_MIN[role]
    code = getpass.getpass(f"Nouveau code {role} ({minimum} caracteres minimum, rien ne s'affiche) : ")
    nettoye = code.strip()
    if len(nettoye) < minimum:
        sys.exit(f"Code trop court ({minimum} caracteres minimum).")
    if code_evident(nettoye):
        sys.exit("Code trop evident (suite, caractere repete ou mot de passe courant) : choisis-en un autre.")
    if getpass.getpass("Confirme : ") != code:
        sys.exit("Les deux saisies different.")
    enregistrer_code(FICHIER_LOCAL, role, code)
    print(f"Code {role} enregistre dans config.local.yaml (empreinte seulement). Redemarre le serveur.")


def rapport(jour: str | None) -> None:
    from datetime import date

    config = charger_config(FICHIER_CONFIG)
    tuteur = Tuteur(config)
    module = tuteur.module("rapport")
    if module is None:
        sys.exit("Module rapport desactive")
    print(module.rapport(jour or date.today().isoformat())["texte"])  # type: ignore[attr-defined]
    tuteur.fermer()


def console_utf8() -> None:
    """Les consoles Windows sont souvent en cp1252 : sans cela, un caractere comme « √ » fait planter."""
    for flux in (sys.stdout, sys.stderr):
        reconfigurer = getattr(flux, "reconfigure", None)
        if reconfigurer is not None:
            reconfigurer(encoding="utf-8", errors="replace")


def main(args: list[str] | None = None) -> None:
    console_utf8()
    args = sys.argv[1:] if args is None else args
    if not args or args[0] == "serveur":
        servir()
    elif args[0] == "installer":
        from jules.installation import lancer

        lancer(RACINE)
    elif args[0] == "verifier":
        verifier()
    elif args[0] == "code" and len(args) == 2:
        definir_code(args[1])
    elif args[0] == "rapport":
        rapport(args[1] if len(args) > 1 else None)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
