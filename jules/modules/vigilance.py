"""Module 'vigilance' : repere les signaux inquietants et previent le parent tout de suite.

Chaque message de l'eleve est relu par le modele rapide. Niveau 'moyen' ou 'eleve' :
alerte immediate via les notifieurs. Tous les signaux sont journalises (evenements 'vigilance').
La conduite du bot face a ces situations est dans consignes/securite.md.
"""

from __future__ import annotations

import logging
from typing import Any

from jules.llm.base import Tour
from jules.modules.base import Module, extraire_json
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.vigilance")

NIVEAUX = ("aucun", "faible", "moyen", "eleve")

CONSIGNE = """Tu protèges un élève de collège qui utilise un tuteur scolaire IA. Lis SON message
(et la réponse du tuteur) et détecte un signal qui mérite l'attention de ses parents :
tristesse profonde, idées noires, auto-agression, harcèlement (école ou en ligne), violence subie,
contact inquiétant avec un adulte ou un inconnu, mise en danger, détresse forte, ou demande d'aide.
Ne signale PAS : le stress normal des contrôles, l'agacement contre un exercice, les blagues évidentes,
les gros mots isolés.
Ne signale PAS non plus les expressions courantes (« je vais mourir mdr », « ma mère va me tuer »,
« ce contrôle va me tuer ») quand le contexte est clairement celui du travail scolaire.
Réponds UNIQUEMENT par un objet JSON :
{"niveau": "aucun|faible|moyen|eleve", "motif": "une phrase factuelle, vide si aucun"}
Le motif dit exactement qui a dit ou demandé quoi (« un adulte de 24 ans lui propose un rendez-vous
et lui demande de le cacher à sa mère »), sans l'attribuer à l'élève par erreur."""


def doit_alerter(niveau: str, seuil: str) -> bool:
    if niveau not in NIVEAUX or seuil not in NIVEAUX:
        return False
    return NIVEAUX.index(niveau) >= NIVEAUX.index(seuil)


class Brique(Module):
    id = "vigilance"

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        texte = f"MESSAGE DE L'ÉLÈVE :\n{eleve.texte[:3000]}\n\nRÉPONSE DU TUTEUR :\n{bot.texte[:1500]}"
        brut = self.tuteur.llm.repondre(CONSIGNE, [Tour(role="user", texte=texte)], "rapide")
        analyse = extraire_json(brut)
        if analyse is None:
            journal.warning("Analyse de vigilance illisible : %s", brut[:200])
            return
        niveau = str(analyse.get("niveau") or "aucun")
        if niveau == "aucun":
            return
        donnees: dict[str, Any] = {"niveau": niveau, "motif": str(analyse.get("motif") or "")[:300]}
        self.tuteur.stockage.ajouter_evenement("vigilance", donnees, conv.id)
        if doit_alerter(niveau, str(self.reglages.get("seuil_alerte", "moyen"))):
            prenom = self.tuteur.profil().prenom
            self.tuteur.notifier(
                f"Jules : attention ({niveau})",
                f"{prenom} a écrit quelque chose qui mérite ton attention.\n"
                f"Motif : {donnees['motif']}\n"
                f"Message : « {eleve.texte[:400]} »\n"
                f"Conversation : {conv.id} (page parent).",
                urgent=True,
            )
