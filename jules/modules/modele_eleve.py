"""Module 'modele_eleve' : le modele chiffre de l'eleve, branche sur Jules (docs/MODELE-ELEVE.md).

Le calcul vit dans jules/apprentissage/ (pur, teste sans IA). Cette brique fait le lien :
  - apres_echange : extraction des faits par le modele 'principal' (§2), observations, estimateur,
    etat de seance (politique) ; lit aussi les evenements 'suivi' (capteur jugement_ia) et
    'epreuve' (prediction figee, lecture du resultat, calibration, surprise -> carnet) ;
  - contribution : reglage de comportement pour le message suivant (§6.4) et lecons (§8.4) ;
  - routes parent : ce que Jules croit, avec quelle confiance, et s'il juge bien (§11).

Stockage (§11), espace 'modele_eleve' :
  notion:<matiere> : <notion>  -> EtatNotion.vers_dict()
  seance:<conversation>        -> EtatSeance.vers_dict()
  calibration                  -> resultat de la derniere calibration (absent tant qu'elle n'a pas tourne)
  carnet                       -> [Lecon.vers_dict()]
Evenements : 'observation' (une par Observation), 'prediction' (figee au lancement d'une epreuve).
L'etat des notions et la calibration se reconstruisent a partir des evenements (reconstruire).

Tant que `actif: false` dans config.yaml, la brique n'est pas chargee. Lot 7 pour le branchement,
apres les lots 2 a 6 et leurs criteres d'acceptation (§12).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from jules.apprentissage import estimateurs, parametres
from jules.apprentissage.etat import EtatSeance, Reglage
from jules.modules.base import Module
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.modele_eleve")

ESPACE = "modele_eleve"
FICHIER_POLITIQUE = Path(__file__).resolve().parents[2] / "consignes" / "politique.yaml"


def charger_textes_politique(chemin: Path = FICHIER_POLITIQUE) -> dict[str, dict[str, str]]:
    """consignes/politique.yaml : un texte par etat, plus les phrases des curseurs (§6.3)."""
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    return {str(k): dict(v or {}) for k, v in brut.items()}


def texte_reglage(reglage: Reglage, textes: dict[str, dict[str, str]]) -> str:
    """Assemble la consigne injectee : texte de l'etat + une phrase par curseur. Lot 7."""
    raise NotImplementedError("lot 7 : docs/MODELE-ELEVE.md §6.4")


class Brique(Module):
    id = "modele_eleve"
    titre = "Où en est l'élève, et comment l'accompagner maintenant"

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self.parametres = parametres.depuis_reglages(reglages)  # refuse une configuration absurde
        self.estimateur = estimateurs.creer(str(reglages.get("estimateur", "bkt")), self.parametres)
        self.textes = charger_textes_politique()

    def seance(self, conv_id: str) -> EtatSeance:
        brut = self.tuteur.stockage.lire_etat(ESPACE, f"seance:{conv_id}", None)
        return EtatSeance.depuis_dict(brut) if brut else EtatSeance(seance=conv_id)

    def reconstruire(self) -> None:
        """Rejoue tous les evenements 'observation', 'suivi' et 'epreuve' depuis zero (§11) : apres un
        changement de reglages, un effacement partiel, ou pour comparer deux estimateurs. Lot 7."""
        raise NotImplementedError("lot 7")

    def contribution(self, conv: Conversation) -> str | None:
        """§6.4 et §8.4 : jamais de chiffre dans le prompt. Rien en mode epreuve (elle a ses regles)."""
        raise NotImplementedError("lot 7")

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        """Lot 7 :
        1. mode epreuve : ne rien extraire ; si l'evenement 'epreuve' de cette conversation vient
           d'etre ecrit, lire_epreuve pour chaque notion, completer les predictions, recalibrer si
           le nombre d'epreuves le permet, et declencher le carnet pour chaque surprise (§8.1).
        2. sinon : extraction (§2, modele 'principal', notions deja suivies en liste fermee),
           observations -> evenements 'observation' -> estimateur -> politique.avancer.
        3. le capteur jugement_ia vient des evenements 'suivi' ecrits par le module suivi.
        Toute erreur est journalisee et n'interrompt jamais la conversation.
        """
        raise NotImplementedError("lot 7")

    def routes(self) -> Any:
        """Parent (§11) : GET /notions, GET /fiabilite, GET /lecons, DELETE /lecons/{id},
        POST /reinitialiser. Lot 7."""
        raise NotImplementedError("lot 7")
