"""Coeur : assemble les briques et orchestre un echange.

Le moteur ne sait rien des matieres, des modes ni du rapport : tout passe par les modules.
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from typing import Any

from jules.briques import classe_brique
from jules.composition import Profil, assembler, charger_profil
from jules.config import Config
from jules.llm.base import MoteurLLM, Tour
from jules.modules.base import Module, Tache
from jules.persona import Persona, charger_persona
from jules.stockage import Conversation, Message, Stockage

journal = logging.getLogger("jules")

MESSAGE_PANNE = (
    "Oups, mon cerveau a fait une petite pause. Réessaie dans un instant, "
    "et si ça continue, préviens un adulte à la maison."
)


class Tuteur:
    def __init__(self, config: Config, llm: MoteurLLM | None = None) -> None:
        self.config = config
        self.stockage = Stockage(config.donnees)
        self.llm: MoteurLLM = llm or classe_brique("llm", config.llm.get("backend", "demo"))(config.llm)
        self.historique_max = int(config.llm.get("historique_max", 30))
        self.notifieurs = [
            classe_brique("notifieurs", ref.id)(config, ref.reglages) for ref in config.notifieurs if ref.actif
        ]
        self.modules: list[Module] = [
            classe_brique("modules", ref.id)(self, ref.reglages) for ref in config.modules if ref.actif
        ]
        self._fond = ThreadPoolExecutor(max_workers=1, thread_name_prefix="jules-fond")
        self._verrou_conv = threading.Lock()

    # --- briques rechargees a chaque message (peaufinage a chaud) -------
    def profil(self) -> Profil:
        return charger_profil(self.config.fichier_profil)

    def persona(self) -> Persona:
        profil = self.profil()
        return charger_persona(self.config.dossier_persona, profil.variables(), profil.genre)

    def module(self, identifiant: str) -> Module | None:
        return next((m for m in self.modules if m.id == identifiant), None)

    # --- prompt ----------------------------------------------------------
    def systeme(self, conv: Conversation) -> str:
        contributions: list[tuple[str, str]] = []
        for module in self.modules:
            try:
                texte = module.contribution(conv)
            except Exception:
                journal.exception("Module %s : contribution en echec", module.id)
                continue
            if texte:
                contributions.append((module.titre or module.id, texte))
        contributions.append(("Date", f"Nous sommes le {datetime.now().astimezone():%A %d/%m/%Y, %H:%M}."))
        return assembler(self.persona(), self.profil(), self.config.dossier_consignes, contributions)

    def tours(self, conv: Conversation) -> list[Tour]:
        messages = conv.messages[-self.historique_max :]
        while messages and messages[0].role != "eleve":
            messages = messages[1:]
        tours = []
        for m in messages:
            images = [p for nom in m.images if (p := self.stockage.chemin_image(nom))]
            tours.append(Tour(role="user" if m.role == "eleve" else "assistant", texte=m.texte, images=images))
        return tours

    # --- echange ---------------------------------------------------------
    def echanger(self, conv_id: str, texte: str, images: list[str] | None = None) -> Message:
        conv = self.stockage.conversation(conv_id)
        if conv is None:
            raise KeyError(conv_id)
        eleve = self.stockage.ajouter_message(conv_id, Message(role="eleve", texte=texte, images=images or []))
        conv.messages.append(eleve)
        for module in self.modules:
            try:
                module.avant_echange(conv, eleve)
            except Exception:
                journal.exception("Module %s : avant_echange en echec", module.id)
        try:
            reponse = self.llm.repondre(self.systeme(conv), self.tours(conv), "principal")
        except Exception as err:
            journal.exception("Echec du moteur d'IA")
            self.stockage.ajouter_evenement("erreur", {"message": str(err)[:500]}, conv_id)
            return Message(role="bot", texte=MESSAGE_PANNE)
        bot = self.stockage.ajouter_message(conv_id, Message(role="bot", texte=reponse or "…"))
        conv.messages.append(bot)
        self._lancer_apres_echange(conv, eleve, bot)
        return bot

    def _lancer_apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> Future[None]:
        return self._fond.submit(self._apres_echange, conv, eleve, bot)

    def _apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        for module in self.modules:
            try:
                module.apres_echange(conv, eleve, bot)
            except Exception:
                journal.exception("Module %s : apres_echange en echec", module.id)

    def attendre_fond(self) -> None:
        """Attend la fin des traitements de fond (tests, arret propre)."""
        self._fond.submit(lambda: None).result(timeout=600)

    # --- services communs pour les modules --------------------------------
    def notifier(self, sujet: str, texte: str, urgent: bool = False) -> list[str]:
        erreurs = []
        for notifieur in self.notifieurs:
            try:
                notifieur.envoyer(sujet, texte, urgent)
            except Exception as err:
                journal.exception("Notifieur %s en echec", type(notifieur).__module__)
                erreurs.append(f"{type(notifieur).__module__}: {err}")
        return erreurs

    def taches(self) -> list[Tache]:
        return [t for m in self.modules for t in m.taches()]

    def infos_interface(self) -> dict[str, Any]:
        infos: dict[str, Any] = {"persona": self.persona().publique(), "prenom": self.profil().prenom}
        for module in self.modules:
            infos.update(module.infos_interface())
        return infos

    def fermer(self) -> None:
        self._fond.shutdown(wait=True)
        self.stockage.fermer()
