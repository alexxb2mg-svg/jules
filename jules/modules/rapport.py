"""Module 'rapport' : resume quotidien pour le parent.

Chiffres calcules (conversations, temps estime, matieres, notions) + une courte synthese
redigee par le modele rapide + une ou deux questions que le parent peut poser a l'eleve
sans savoir faire l'exercice lui-meme (« Explique-moi comment tu sais que... »).
Si le modele ne propose pas de question lisible, une question simple est construite
a partir des notions du jour : le parent en a toujours une.
Envoye chaque soir a l'heure reglee via les notifieurs, et consultable a tout moment
sur la page parent.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from itertools import pairwise
from typing import Any

from fastapi import APIRouter

from jules.llm.base import Tour
from jules.modules.base import Module, Tache, extraire_json
from jules.texte import remplir

journal = logging.getLogger("jules.rapport")

PAUSE_MAX_S = 15 * 60  # au-dela, l'ecart entre deux messages ne compte pas comme du travail

CONSIGNE_SYNTHESE = """Tu écris à l'adulte qui suit {prenom},
{{une collégienne|un collégien|un ou une élève de collège}}, le résumé de sa séance de travail
avec son tuteur IA, et une ou deux questions à lui poser ce soir. En français, ton simple et bienveillant.
Réponds UNIQUEMENT par un objet JSON, sans texte autour :
{"resume": "...", "questions": ["...", "..."]}
- resume : 3 phrases maximum, sans titre ni liste. Désigne l'élève par son prénom et accorde au bon genre.
  Dis ce qui a été travaillé, ce qui a bien marché, et le point à surveiller s'il y en a un.
  N'invente rien au-delà des données fournies.
- questions : 1 ou 2 questions que l'adulte pose à {prenom}, en le tutoyant, sur les notions du jour
  (une notion bloquée d'abord). L'adulte doit pouvoir les poser sans savoir faire l'exercice :
  l'élève explique, montre ou raconte comment il s'y prend.
  Exemple : « Explique-moi comment tu sais qu'un nombre est premier. »
  Jamais de calcul à vérifier, jamais de question à laquelle on répond par oui ou non,
  jamais de reproche. Ne parle pas des signaux de vigilance : l'adulte les voit à part."""

QUESTIONS_MAX = 2
QUESTION_LONGUEUR_MAX = 240

# Questions de secours, posables sans connaitre la notion : l'eleve explique, l'adulte ecoute.
MODELES_QUESTION = {
    "bloque": "Sur « {notion} » : montre-moi jusqu'où tu arrives, et dis-moi où ça coince.",
    "en_cours": "Sur « {notion} » : raconte-moi ce que tu as appris aujourd'hui.",
    "compris": "Sur « {notion} » : explique-moi comment tu t'y prends, comme si je n'y connaissais rien.",
}
ORDRE_QUESTIONS = ("bloque", "en_cours", "compris")


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


def questions_de_secours(d: dict[str, Any]) -> list[str]:
    """Une ou deux questions construites sans IA : notion bloquee d'abord, puis en cours, puis comprise."""
    rangees = sorted(
        (ORDRE_QUESTIONS.index(info["statut"]), cle.split(" : ", 1)[-1])
        for cle, info in d["notions"].items()
        if info.get("statut") in ORDRE_QUESTIONS
    )
    return [MODELES_QUESTION[ORDRE_QUESTIONS[rang]].format(notion=notion) for rang, notion in rangees[:QUESTIONS_MAX]]


def lire_synthese(brut: str) -> tuple[str, list[str]]:
    """Resume et questions depuis la reponse du modele. Texte libre accepte : tout devient le resume."""
    objet = extraire_json(brut)
    if objet is None:
        return brut.strip(), []
    resume = str(objet.get("resume") or "").strip()
    questions = objet.get("questions") or []
    if isinstance(questions, str):
        questions = [questions]
    propres = [str(q).strip()[:QUESTION_LONGUEUR_MAX] for q in questions if str(q).strip()]
    return resume, propres[:QUESTIONS_MAX]


def texte_rapport(
    prenom: str, jour: str, d: dict[str, Any], synthese: str = "", questions: list[str] | None = None
) -> str:
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
    if questions:
        lignes += ["", f"À demander à {prenom} ce soir (pas besoin de savoir faire l'exercice) :"]
        lignes += [f"- {q}" for q in questions]
    return "\n".join(lignes)


class Brique(Module):
    id = "rapport"
    _syntheses: dict[str, tuple[str, list[str]]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._syntheses = {}

    def synthese(self, jour: str, d: dict[str, Any]) -> tuple[str, list[str]]:
        """Resume et questions redigees par le modele rapide, gardes en memoire pour les memes donnees."""
        cle = f"{jour}|{hash(repr(d))}"  # memes donnees -> meme synthese, pas de nouvel appel
        if cle in self._syntheses:
            return self._syntheses[cle]
        try:
            profil = self.tuteur.profil()
            consigne = remplir(CONSIGNE_SYNTHESE, profil.variables(), profil.genre)
            brut = self.tuteur.llm.repondre(consigne, [Tour(role="user", texte=str(d))], "rapide")
        except Exception:
            journal.exception("Synthese du rapport impossible")
            return "", []
        self._syntheses[cle] = lire_synthese(brut)
        return self._syntheses[cle]

    def rapport(self, jour: str, avec_synthese: bool = True) -> dict[str, Any]:
        stockage = self.tuteur.stockage
        d = donnees_du_jour(
            stockage.messages_du_jour(jour),
            stockage.evenements("suivi", jour=jour),
            stockage.evenements("vigilance", jour=jour),
        )
        synthese, questions = "", []
        if d["messages_eleve"] and avec_synthese and self.reglages.get("synthese", True):
            synthese, questions = self.synthese(jour, d)
        if d["messages_eleve"] and self.reglages.get("questions", True):
            questions = questions or questions_de_secours(d)  # le parent a toujours une question
        else:
            questions = []
        prenom = self.tuteur.profil().prenom
        return {
            "jour": jour,
            "donnees": d,
            "questions": questions,
            "texte": texte_rapport(prenom, jour, d, synthese, questions),
        }

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
