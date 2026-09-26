"""Module 'suivi' : analyse chaque echange (matiere, notion, statut) en tache de fond.

Produit des evenements 'suivi' lus par les modules memoire et rapport.
Donne aussi un titre a la conversation au premier echange.
"""

from __future__ import annotations

import logging
from typing import Any

from jules.llm.base import Tour
from jules.modules.base import Module, extraire_json
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.suivi")

STATUTS = ("compris", "en_cours", "bloque", "hors_scolaire")
# "acquis" n'est jamais donne par l'analyse : seul le module epreuve l'ecrit, apres une epreuve sans aide.
MODES_IGNORES = ("epreuve", "exercice")

CONSIGNE = """Tu analyses un échange entre un élève de collège et son tuteur IA, pour le suivi scolaire.
Réponds UNIQUEMENT par un objet JSON, sans texte autour :
{"matiere": "...", "notion": "...", "statut": "...", "resume": "...", "titre": "..."}
- matiere : Mathématiques, Français, Anglais, Espagnol, Allemand, Histoire-Géographie, EMC,
  SVT, Physique-Chimie, Technologie, Latin, Musique, Arts plastiques, Autre.
- notion : la notion précise travaillée (ex. "fractions : addition", "passé composé"), 6 mots max.
  Laisse "" tant que l'élève n'a pas encore dit sur quoi il travaille (« j'ai un exo »).
- Une ligne « [Correction automatique] Réponse juste » veut dire que l'élève a trouvé seul la bonne
  réponse à l'exercice : c'est le dernier état de l'exercice, même si la discussion d'avant hésitait.
- statut : "compris" seulement si l'élève a trouvé ou expliqué LUI-MÊME (une réponse donnée ou écrite
  par le tuteur, puis recopiée ou approuvée par l'élève, ne compte pas) ; "bloque" si l'élève bute
  (erreurs répétées, "je comprends pas") ; "en_cours" sinon ; "hors_scolaire" si ce n'est pas scolaire.
  Un exercice scolaire reste scolaire même si l'élève répond par "jsp" ou très court.
- resume : une phrase factuelle pour le parent (ce qui a été fait, où en est l'élève). Distingue ce que
  l'élève a trouvé seul de ce que le tuteur a fourni (« le tuteur a donné la forme went »). Ne dis jamais
  « maîtrise » ni « a construit seul » si le tuteur a fait une partie du travail.
- titre : titre court de la conversation (4 mots max)."""


def normaliser(analyse: dict[str, Any]) -> dict[str, str]:
    statut = str(analyse.get("statut") or "en_cours")
    return {
        "matiere": str(analyse.get("matiere") or "Autre")[:40],
        "notion": str(analyse.get("notion") or "")[:80],
        "statut": statut if statut in STATUTS else "en_cours",
        "resume": str(analyse.get("resume") or "")[:300],
        "titre": str(analyse.get("titre") or "")[:60],
    }


def extrait(conv: Conversation, nb: int = 6) -> str:
    lignes = []
    for m in conv.messages[-nb:]:
        qui = "ÉLÈVE" if m.role == "eleve" else "TUTEUR"
        photo = " [+ photo]" if m.images else ""
        lignes.append(f"{qui}{photo} : {m.texte[:1500]}")
    return "\n".join(lignes)


class Brique(Module):
    id = "suivi"

    def notions_connues(self, maximum: int = 40) -> list[str]:
        vues: list[str] = []
        for ev in self.tuteur.stockage.evenements("suivi", limite=300):
            d = ev["donnees"]
            if not d.get("notion") or d.get("statut") == "hors_scolaire":
                continue
            libelle = f"{d.get('matiere', 'Autre')} | {d['notion']}"
            if libelle not in vues:
                vues.append(libelle)
            if len(vues) >= maximum:
                break
        return vues

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        if conv.mode in self.reglages.get("modes_ignores", MODES_IGNORES):
            return  # l'epreuve sans aide tient son propre suivi : pas d'analyse pendant qu'elle se deroule
        connues = self.notions_connues()
        consigne = CONSIGNE
        if connues:
            consigne += (
                "\nNotions déjà suivies (si c'est la même notion, reprends EXACTEMENT le même libellé "
                "et la même matière) :\n" + "\n".join(f"- {n}" for n in connues)
            )
        tours = [Tour(role="user", texte=f"Mode : {conv.mode}\n\n{extrait(conv)}")]
        brut = self.tuteur.llm.repondre(consigne, tours, "rapide")
        analyse = extraire_json(brut)
        if analyse is None:
            journal.warning("Analyse de suivi illisible : %s", brut[:200])
            return
        donnees = normaliser(analyse)
        self.tuteur.stockage.ajouter_evenement("suivi", donnees, conv.id)
        if not conv.titre and donnees["titre"]:
            self.tuteur.stockage.renommer(conv.id, donnees["titre"])
            conv.titre = donnees["titre"]
