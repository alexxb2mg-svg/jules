"""Coeur : assemble les briques et orchestre un echange.

Le moteur ne sait rien des matieres, des modes ni du rapport : tout passe par les modules.
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from typing import Any

from jules.briques import classe_brique
from jules.composition import Profil, assembler, charger_profil
from jules.config import Config
from jules.extensions import charger_extensions, modules_des_extensions
from jules.llm.base import MoteurLLM, Tour
from jules.modules.base import Module, Tache
from jules.persona import Persona, charger_persona
from jules.stockage import Conversation, Message, Stockage

journal = logging.getLogger("jules")

MESSAGE_PANNE = (
    "Oups, mon cerveau a fait une petite pause. Réessaie dans un instant, "
    "et si ça continue, préviens un adulte à la maison."
)

INACTIVITE_S = 20 * 60  # apres ce delai sans activite de l'eleve, la seance est finie


class Tuteur:
    def __init__(self, config: Config, llm: MoteurLLM | None = None) -> None:
        self.config = config
        self.stockage = Stockage(config.donnees)
        self.llm: MoteurLLM = llm or classe_brique("llm", config.llm.get("backend", "demo"))(config.llm)
        self.historique_max = int(config.llm.get("historique_max", 30))
        self.extensions = charger_extensions(config.dossier_extensions, config.extensions)
        self.notifieurs = [
            classe_brique("notifieurs", ref.id)(config, ref.reglages) for ref in config.notifieurs if ref.actif
        ]
        self.modules: list[Module] = [
            classe_brique("modules", ref.id)(self, ref.reglages) for ref in config.modules if ref.actif
        ]
        self.modules += modules_des_extensions(self, self.extensions, {m.id for m in self.modules})
        self.inactivite_s = INACTIVITE_S
        self._horloge = time.monotonic  # remplacable dans les tests
        self._seance: dict[str, Any] | None = None  # {"conv": id ou None, "dernier": instant} tant qu'une seance court
        self._verrou_seance = threading.Lock()
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
        # A l'heure pres, pas a la minute : le prompt systeme reste identique d'un message a l'autre dans
        # l'heure, et le cache du fournisseur d'IA s'applique (mesure : evaluation/eleves).
        maintenant = datetime.now().astimezone()
        contributions.append(("Date", f"Nous sommes le {maintenant:%A %d/%m/%Y}, vers {maintenant:%H} h."))
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
        self._activite(conv_id)
        eleve = self.stockage.ajouter_message(conv_id, Message(role="eleve", texte=texte, images=images or []))
        conv.messages.append(eleve)
        for module in self.modules:
            try:
                module.avant_echange(conv, eleve)
            except Exception:
                journal.exception("Module %s : avant_echange en echec", module.id)
        reponse_module: str | None = None
        for module in self.modules:
            try:
                reponse_module = module.repondre_a_la_place(conv, eleve)
            except Exception:
                journal.exception("Module %s : repondre_a_la_place en echec", module.id)
                continue
            if reponse_module is not None:
                break
        try:
            if reponse_module is not None:
                reponse = reponse_module

                def relancer() -> str:
                    return reponse_module  # type: ignore[return-value]

            else:
                systeme, tours = self.systeme(conv), self.tours(conv)
                reponse = self.llm.repondre(systeme, tours, "principal")

                def relancer() -> str:
                    return self.llm.repondre(systeme, tours, "principal")

            for module in self.modules:
                try:
                    reponse = module.filtrer_reponse(conv, reponse, relancer)
                except Exception:
                    journal.exception("Module %s : filtrer_reponse en echec", module.id)
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

    # --- points d'accroche du parcours de l'eleve (voir docs/EXTENSIONS.md) ---
    # Un module ne recoit que ce que le nom du point promet (l'adresse, la conversation en cours) ; le
    # coeur ne lance aucun appel IA a cette occasion. Les modules sont prevenus en tache de fond, comme
    # apres_echange : un clic ne doit jamais attendre un module lent, et un module en echec ne gene personne.
    def bloc_consulte(self, adresse: str, notion: str | None = None, conv_id: str | None = None) -> None:
        """L'eleve a clique sur un bloc de fiche : ouvre (ou prolonge) la seance et previent les modules."""
        self._activite(conv_id)
        self._fond.submit(self._diffuser, "bloc_consulte", conv_id, adresse, notion)

    def fin_de_seance(self) -> bool:
        """L'eleve a ferme l'application : clot la seance en cours. Sans seance ouverte, ne fait rien
        (le signal de fermeture part parfois plusieurs fois, et sans qu'on ait rien fait)."""
        return self._clore_seance(seulement_si_perimee=False)

    def verifier_inactivite(self) -> bool:
        """Clot la seance si l'eleve est inactif depuis trop longtemps (appele par le planificateur)."""
        return self._clore_seance(seulement_si_perimee=True)

    def _seance_perimee(self, instant: float) -> bool:
        return self._seance is not None and instant - self._seance["dernier"] > self.inactivite_s

    def _clore_seance(self, seulement_si_perimee: bool) -> bool:
        with self._verrou_seance:
            seance = self._seance
            if seance is None or (seulement_si_perimee and not self._seance_perimee(self._horloge())):
                return False
            self._seance = None
        self._fond.submit(self._diffuser, "fin_de_seance", seance["conv"])
        return True

    def _activite(self, conv_id: str | None) -> None:
        """Note une activite de l'eleve. Si la derniere est trop ancienne, la seance d'avant se termine
        ici (cas d'un eleve qui revient apres une longue pause, sans que le planificateur l'ait vu)."""
        with self._verrou_seance:
            instant = self._horloge()
            perimee = self._seance if self._seance_perimee(instant) else None
            precedente = None if perimee else self._seance
            conv = conv_id or (precedente["conv"] if precedente else None)
            self._seance = {"conv": conv, "dernier": instant}
        if perimee:
            self._fond.submit(self._diffuser, "fin_de_seance", perimee["conv"])

    def _diffuser(self, point: str, conv_id: str | None, *args: Any) -> None:
        conv = self.stockage.conversation(conv_id) if conv_id else None
        for module in self.modules:
            try:
                getattr(module, point)(conv, *args)
            except Exception:
                journal.exception("Module %s : %s en echec", module.id, point)

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
