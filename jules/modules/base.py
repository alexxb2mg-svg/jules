"""Contrat commun des modules.

Un module = jules/modules/<id>.py avec une classe `Brique(Module)`. Il peut :
  - agir avant la reponse (bloquant, court) -> avant_echange(conv, eleve)
  - contribuer au prompt systeme           -> contribution(conv)
  - agir apres chaque echange (en tache de fond) -> apres_echange(conv, eleve, bot)
  - declarer des taches planifiees          -> taches()
  - exposer des routes HTTP parent         -> routes()  (montees sous /api/modules/<id>)
  - exposer des routes HTTP eleve          -> routes_eleve()  (montees sous /api/eleve/<id>)
  - donner des infos a l'interface          -> infos_interface()
Tout est optionnel : un module n'implemente que ce dont il a besoin.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import APIRouter

    from jules.moteur import Tuteur
    from jules.stockage import Conversation, Message


@dataclass
class Tache:
    nom: str
    heure: str  # "HH:MM", heure locale
    action: Callable[[], None]


class Module:
    id = "module"
    titre = ""  # titre de la section ajoutee au prompt

    def __init__(self, tuteur: Tuteur, reglages: dict[str, Any]) -> None:
        self.tuteur = tuteur
        self.reglages = reglages

    def avant_echange(self, conv: Conversation, eleve: Message) -> None:
        return None

    def contribution(self, conv: Conversation) -> str | None:
        return None

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        return None

    def taches(self) -> list[Tache]:
        return []

    def routes(self) -> APIRouter | None:
        return None

    def routes_eleve(self) -> APIRouter | None:
        return None

    def infos_interface(self) -> dict[str, Any]:
        return {}


def extraire_json(texte: str) -> dict[str, Any] | None:
    """Recupere le premier objet JSON d'une reponse de modele (tolere ```json ... ```)."""
    correspondance = re.search(r"\{.*\}", texte, re.DOTALL)
    if not correspondance:
        return None
    try:
        objet = json.loads(correspondance.group(0))
    except json.JSONDecodeError:
        return None
    return objet if isinstance(objet, dict) else None
