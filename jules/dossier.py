"""Le dossier de l'eleve, entre les mains du parent : tout exporter, tout effacer.

Le dossier, c'est tout ce que Jules garde sur l'ordinateur de la famille dans donnees/ :
conversations et photos, analyses (notions, signaux de vigilance), notes du parent,
bilans envoyes (donnees/notifications) et journal technique (donnees/jules.log).

Ce qui n'en fait pas partie et reste en place : le profil (profils/<nom>.yaml, que
l'export contient quand meme), la configuration et les codes d'acces, et l'etat du
planificateur (la date du dernier bilan envoye, pour ne pas le renvoyer).
Ce qui a deja ete envoye ailleurs (Telegram...) ne peut pas etre efface d'ici.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from jules.planificateur import ESPACE as ESPACE_PLANIFICATEUR

if TYPE_CHECKING:
    from jules.moteur import Tuteur

MOT_DE_CONFIRMATION = "EFFACER"
FORMAT = "jules-dossier"
VERSION = 1

LISEZMOI = """Dossier de {prenom}, exporte de Jules le {date}.

dossier.json      conversations et messages, analyses (notions travaillees, signaux
                  de vigilance), notes laissees par le parent. Format JSON, lisible
                  avec n'importe quel editeur de texte.
images/           photos envoyees par l'eleve (le nom est cite dans dossier.json).
notifications/    bilans du soir et alertes, tels qu'ils ont ete envoyes.
profil.yaml       profil de l'eleve (prenom, classe...), tel que rempli a l'installation.

Ce fichier contient des informations personnelles sur un enfant : a garder pour soi.
"""


class Confirmation(BaseModel):
    confirmation: str = ""


def nom_archive(instant: datetime | None = None) -> str:
    instant = instant or datetime.now().astimezone()
    return f"jules-dossier-{instant:%Y-%m-%d}.zip"


def exporter(tuteur: Tuteur) -> bytes:
    """Archive zip de tout le dossier de l'eleve."""
    instant = datetime.now().astimezone()
    stockage = tuteur.stockage
    contenu: dict[str, Any] = {
        "format": FORMAT,
        "version": VERSION,
        "exporte_le": instant.isoformat(timespec="seconds"),
        **stockage.tout_lire(),
    }
    contenu["etat"].pop(ESPACE_PLANIFICATEUR, None)  # technique, rien sur l'eleve
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as zf:
        prenom = tuteur.profil().prenom
        zf.writestr("LISEZMOI.txt", LISEZMOI.format(prenom=prenom, date=f"{instant:%Y-%m-%d}"))
        zf.writestr("dossier.json", json.dumps(contenu, ensure_ascii=False, indent=2))
        for image in sorted(stockage.dossier_images.iterdir()):
            if image.is_file():
                zf.write(image, f"images/{image.name}")
        notifications = tuteur.config.donnees / "notifications"
        if notifications.is_dir():
            for bilan in sorted(notifications.glob("*.log")):
                zf.write(bilan, f"notifications/{bilan.name}")
        if tuteur.config.fichier_profil.is_file():
            zf.write(tuteur.config.fichier_profil, "profil.yaml")
    return tampon.getvalue()


def effacer_tout(tuteur: Tuteur) -> dict[str, int]:
    """Efface tout le dossier. Irreversible : la page parent demande de taper le mot de confirmation."""
    tuteur.attendre_fond()  # une analyse en cours ne doit pas reecrire apres l'effacement
    avant = tuteur.stockage.tout_lire()
    tuteur.stockage.effacer_tout(garder_espaces=(ESPACE_PLANIFICATEUR,))
    bilans = 0
    notifications = tuteur.config.donnees / "notifications"
    if notifications.is_dir():
        for bilan in notifications.glob("*.log"):
            bilan.unlink()
            bilans += 1
    journal_technique = tuteur.config.donnees / "jules.log"
    if journal_technique.is_file():
        journal_technique.write_text("", encoding="utf-8")  # vide, mais garde : le serveur y ecrit encore
    return {"conversations": len(avant["conversations"]), "evenements": len(avant["evenements"]), "bilans": bilans}
