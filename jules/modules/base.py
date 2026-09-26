"""Contrat commun des modules.

Un module = jules/modules/<id>.py avec une classe `Brique(Module)`. Il peut :
  - agir avant la reponse (bloquant, court) -> avant_echange(conv, eleve)
  - decider seul de la reponse, sans IA     -> repondre_a_la_place(conv, eleve)
  - contribuer au prompt systeme           -> contribution(conv)
  - agir apres chaque echange (en tache de fond) -> apres_echange(conv, eleve, bot)
  - relire la reponse avant envoi (garde-fou) -> filtrer_reponse(conv, texte, relancer)
  - declarer des taches planifiees          -> taches()
  - exposer des routes HTTP parent         -> routes()  (montees sous /api/modules/<id>)
  - exposer des routes HTTP eleve          -> routes_eleve()  (montees sous /api/eleve/<id>)
  - donner des infos a l'interface          -> infos_interface()
  - observer le parcours de l'eleve         -> bloc_consulte(conv, adresse, notion), fin_de_seance(conv)
    (points d'accroche des extensions, voir docs/EXTENSIONS.md : ils ne donnent que ce que leur nom
    promet et ne declenchent jamais d'appel IA par eux-memes)
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

    def repondre_a_la_place(self, conv: Conversation, eleve: Message) -> str | None:
        """Un module peut decider seul de la reponse (aucun appel au modele). None : ce n'est pas son tour."""
        return None

    def contribution(self, conv: Conversation) -> str | None:
        return None

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        return None

    def bloc_consulte(self, conv: Conversation | None, adresse: str, notion: str | None = None) -> None:
        """L'eleve a clique sur un bloc de fiche (adresse `fiche/<id>`, `carte/<id>`, `graphe/<id>`...).
        `conv` n'est renseignee que si la page a une conversation en cours (jamais sur « Mes fiches »)."""
        return None

    def fin_de_seance(self, conv: Conversation | None) -> None:
        """L'eleve a ferme l'application, ou il est reste inactif : la seance est finie.
        `conv` est la derniere conversation touchee pendant la seance, s'il y en a une."""
        return None

    def filtrer_reponse(self, conv: Conversation, texte: str, relancer: Callable[[], str]) -> str:
        """Relit la reponse de Jules avant qu'elle soit enregistree et montree (garde-fou), qu'elle
        vienne du modele ou d'un module ayant repondu a sa place. `relancer()` redemande une reponse
        au modele avec le meme prompt (sans effet si la reponse initiale ne venait pas du modele).
        Par defaut : rien a changer."""
        return texte

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
