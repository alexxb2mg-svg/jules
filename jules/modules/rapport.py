"""Module 'rapport' : resume quotidien pour le parent.

Chiffres calcules (conversations, temps estime, matieres, notions) + une courte synthese
redigee par le modele rapide. Envoye chaque soir a l'heure reglee via les notifieurs,
et consultable a tout moment sur la page parent.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from itertools import pairwise
from typing import Any

from fastapi import APIRouter

from jules.llm.base import Tour
from jules.modules.base import Module, Tache
from jules.texte import remplir

journal = logging.getLogger("jules.rapport")

PAUSE_MAX_S = 15 * 60  # au-dela, l'ecart entre deux messages ne compte pas comme du travail

CONSIGNE_SYNTHESE = """Tu écris à l'adulte qui suit {prenom},
{{une collégienne|un collégien|un ou une élève de collège}}, un résumé de sa séance de travail
avec son tuteur IA. 3 phrases maximum, ton simple et bienveillant, en français, sans titre ni liste.
Désigne l'élève par son prénom et accorde au bon genre.
Dis ce qui a été travaillé, ce qui a bien marché, et le point à surveiller s'il y en a un.
N'invente rien au-delà des données fournies."""


def minutes_travail(messages: list[dict[str, Any]]) -> int:
    par_conv: dict[str, list[datetime]] = defaultdict(list)
    for m in messages:
        par_conv[m["conversation"]].append(datetime.fromisoformat(m["horodatage"]))
    total = 0.0
    for instants in par_conv.values():
        instants.sort()
        for avant, apres in pairwise(instants):
            ecart = (apres - avant).total_seconds()
            total += min(ecart, PAUSE_MAX_S)
    return round(total / 60)


def donnees_du_jour(
    messages: list[dict[str, Any]], suivis: list[dict[str, Any]], alertes: list[dict[str, Any]]
) -> dict[str, Any]:
    notions: dict[str, dict[str, str]] = {}
    for ev in reversed(suivis):  # du plus ancien au plus recent : le dernier statut gagne
        d = ev["donnees"]
        if d.get("statut") == "hors_scolaire" or not d.get("notion"):
            continue
        notions[f"{d['matiere']} : {d['notion']}"] = {"statut": d["statut"], "resume": d.get("resume", "")}
    matieres = sorted({cle.split(" : ")[0] for cle in notions})
    return {
        "conversations": len({m["conversation"] for m in messages}),
        "messages_eleve": sum(1 for m in messages if m["role"] == "eleve"),
        "minutes": minutes_travail(messages),
        "matieres": matieres,
        "notions": notions,
        "hors_scolaire": sum(1 for ev in suivis if ev["donnees"].get("statut") == "hors_scolaire"),
        "alertes": [ev["donnees"] for ev in alertes],
    }


def texte_rapport(prenom: str, jour: str, d: dict[str, Any], synthese: str = "") -> str:
    if not d["messages_eleve"]:
        return f"{prenom} n'a pas utilisé Jules le {jour}."
    lignes = [
        f"Rapport du {jour} pour {prenom}",
        f"{d['conversations']} conversation(s), {d['messages_eleve']} message(s), environ {d['minutes']} min.",
    ]
    if d["matieres"]:
        lignes.append("Matières : " + ", ".join(d["matieres"]))
    marques = {"compris": "[OK]", "bloque": "[BLOQUE]", "en_cours": "[EN COURS]"}
    for notion, info in d["notions"].items():
        lignes.append(f"  {marques.get(info['statut'], '')} {notion}")
    if d["hors_scolaire"]:
        lignes.append(f"Échanges hors scolaire : {d['hors_scolaire']}")
    for alerte in d["alertes"]:
        lignes.append(f"Signal ({alerte['niveau']}) : {alerte['motif']}")
    if synthese:
        lignes += ["", synthese]
    return "\n".join(lignes)


class Brique(Module):
    id = "rapport"
    _syntheses: dict[str, str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._syntheses = {}

    def rapport(self, jour: str, avec_synthese: bool = True) -> dict[str, Any]:
        stockage = self.tuteur.stockage
        d = donnees_du_jour(
            stockage.messages_du_jour(jour),
            stockage.evenements("suivi", jour=jour),
            stockage.evenements("vigilance", jour=jour),
        )
        synthese = ""
        if avec_synthese and d["messages_eleve"] and self.reglages.get("synthese", True):
            cle = f"{jour}|{hash(repr(d))}"  # meme donnees -> meme synthese, pas de nouvel appel
            synthese = self._syntheses.get(cle, "")
            if not synthese:
                try:
                    profil = self.tuteur.profil()
                    consigne = remplir(CONSIGNE_SYNTHESE, profil.variables(), profil.genre)
                    synthese = self.tuteur.llm.repondre(consigne, [Tour(role="user", texte=str(d))], "rapide")
                    self._syntheses[cle] = synthese
                except Exception:
                    journal.exception("Synthese du rapport impossible")
        prenom = self.tuteur.profil().prenom
        return {"jour": jour, "donnees": d, "texte": texte_rapport(prenom, jour, d, synthese)}

    def envoyer(self, jour: str | None = None) -> dict[str, Any]:
        jour = jour or datetime.now().astimezone().date().isoformat()
        r = self.rapport(jour)
        if r["donnees"]["messages_eleve"] or self.reglages.get("envoyer_si_vide", False):
            erreurs = self.tuteur.notifier(f"Jules : rapport du {jour}", r["texte"])
            r["envoye"] = not erreurs
            r["erreurs"] = erreurs
        else:
            r["envoye"] = False
        return r

    def taches(self) -> list[Tache]:
        heure = str(self.reglages.get("heure", "20:00"))
        return [Tache(nom="rapport_quotidien", heure=heure, action=self.envoyer_du_jour)]

    def envoyer_du_jour(self) -> None:
        self.envoyer(None)

    def routes(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/jour")
        def lire(date: str | None = None) -> dict[str, Any]:
            jour = date or datetime.now().astimezone().date().isoformat()
            return self.rapport(jour)

        @routeur.post("/envoyer")
        def envoyer_maintenant(date: str | None = None) -> dict[str, Any]:
            return self.envoyer(date)

        return routeur
