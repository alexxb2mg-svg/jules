"""Estimateurs : des observations a une croyance chiffree par notion (docs/MODELE-ELEVE.md, §4, §5.3).

Deux estimateurs, interchangeables par le reglage `estimateur` :
  - `bkt`            : tracage bayesien multi-capteurs (le modele) ;
  - `dernier_statut` : l'ancienne regle « le dernier statut gagne », gardee comme reference de mesure.

Les primitives de calcul (logit, mise a jour, transition, prior) sont ecrites et testees.
L'orchestration (Estimateur*) est a ecrire, lot 2.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Protocol

from jules.apprentissage.etat import EtatNotion, Observation, Prediction
from jules.apprentissage.parametres import Capteur, Parametres

LOGIT_MAX = 12.0  # p dans [6e-6, 1 - 6e-6] : aucune preuve ne rend Jules certain


# --- primitives --------------------------------------------------------------
def logit(p: float) -> float:
    p = min(1 - 1e-9, max(1e-9, p))
    return math.log(p / (1 - p))


def sigmoide(x: float) -> float:
    if x >= 0:
        return 1 / (1 + math.exp(-x))
    e = math.exp(x)
    return e / (1 + e)


def borner(log_odds: float) -> float:
    return max(-LOGIT_MAX, min(LOGIT_MAX, log_odds))


def delta_log_odds(capteur: Capteur, valeur: int, poids: float) -> float:
    """§4.2 : w * ln(P(x | L) / P(x | non L)). Vraisemblance temperee par le poids."""
    if valeur:
        return poids * math.log(capteur.se / (1 - capteur.sp))
    return poids * math.log((1 - capteur.se) / capteur.sp)


def poids_decroissant(poids: float, rang: int, decroissance: float) -> float:
    """§4.3 : la j-ieme observation (rang = j, a partir de 1) d'un meme capteur dans une seance."""
    return poids / (1 + decroissance * (rang - 1))


def plafonner(delta: float, cumul_seance: float, plafond: float) -> float:
    """§4.3 : ramene delta pour que le cumul de la seance reste dans [-plafond, +plafond]."""
    nouveau = max(-plafond, min(plafond, cumul_seance + delta))
    return nouveau - cumul_seance


def transition(p: float, t: float) -> float:
    """§4.4 : p <- p + (1 - p) T. L'eleve peut apprendre pendant une tentative, pas desapprendre."""
    return p + (1 - p) * t


def prior_notion(voisines: Iterable[tuple[float, float]], prior_global: float, force: float) -> float:
    """§4.5 : log-odds de depart d'une notion nouvelle, tire vers les notions de la meme matiere.

    `voisines` : couples (log_odds, n_eff) des notions deja suivies dans la matiere.
    """
    num = force * logit(prior_global)
    den = force
    for lo, n in voisines:
        num += n * lo
        den += n
    return num / den


def mise_a_jour_bayes(log_odds: float, vrai_si_l: float, vrai_si_non_l: float) -> float:
    """Mise a jour exacte par une vraisemblance quelconque (utilisee pour l'epreuve, §5.3)."""
    return borner(log_odds + math.log(vrai_si_l / vrai_si_non_l))


def intervalle_wilson(p: float, n: float, z: float = 1.2816) -> tuple[float, float]:
    """§4.6 : fourchette affichee au parent (z = 1,2816 pour 80 %). n = n_eff ; n = 0 -> [0, 1]."""
    if n <= 0:
        return 0.0, 1.0
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    demi = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - demi), min(1.0, centre + demi)


# --- contrat commun ----------------------------------------------------------
class Estimateur(Protocol):
    def observer(self, etat: EtatNotion | None, obs: Observation, voisines: Mapping[str, EtatNotion]) -> EtatNotion:
        """Integre une observation. `etat` None : notion nouvelle (prior §4.5 depuis `voisines`)."""
        ...

    def clore_seance(self, etat: EtatNotion, horodatage: str) -> EtatNotion:
        """Fin de seance sur la notion : note FSRS de premiere seance (§5.1) ou nouvelle revision."""
        ...

    def predire_epreuve(self, etat: EtatNotion, horodatage: str, epreuve: str) -> Prediction:
        """§5.3 : prediction figee au lancement d'une epreuve."""
        ...

    def lire_epreuve(self, etat: EtatNotion, tenu: bool, horodatage: str) -> EtatNotion:
        """§5.3 et §5.2 : met a jour p (Bayes, vraisemblances de l'epreuve), puis S et D (FSRS)."""
        ...


class EstimateurBKT:
    """Tracage bayesien multi-capteurs, avec oubli FSRS-4.5. Lot 2."""

    def __init__(self, parametres: Parametres) -> None:
        self.parametres = parametres

    def observer(self, etat: EtatNotion | None, obs: Observation, voisines: Mapping[str, EtatNotion]) -> EtatNotion:
        """Ordre des operations, a respecter pour que les tests de reference passent :

        1. etat None -> EtatNotion(obs.notion, prior_notion(voisines de la meme matiere)).
        2. Nouvelle seance (obs.seance != etat.seance_courante) -> remise a zero de delta_seance,
           rangs_seance et des deux drapeaux de reussite.
        3. rang = rangs_seance[capteur] + 1 ; poids = poids_decroissant(obs.poids, rang, rho).
        4. delta = delta_log_odds(capteur, valeur, poids), puis plafonner(delta, delta_seance, c).
        5. log_odds = borner(log_odds + delta) ; n_eff += poids ; delta_seance += delta.
        6. Si capteur de tentative : transition(p, T[obs.aide]) ; drapeaux de reussite si valeur = 1.
        7. derniere_observation = obs.horodatage.
        L'epreuve ne passe PAS par ici : voir lire_epreuve.
        """
        raise NotImplementedError("lot 2 : docs/MODELE-ELEVE.md §4.2 a §4.5")

    def clore_seance(self, etat: EtatNotion, horodatage: str) -> EtatNotion:
        raise NotImplementedError("lot 2 : docs/MODELE-ELEVE.md §5.1")

    def predire_epreuve(self, etat: EtatNotion, horodatage: str, epreuve: str) -> Prediction:
        raise NotImplementedError("lot 2 : docs/MODELE-ELEVE.md §5.3")

    def lire_epreuve(self, etat: EtatNotion, tenu: bool, horodatage: str) -> EtatNotion:
        raise NotImplementedError("lot 2 : docs/MODELE-ELEVE.md §5.2 et §5.3")


class EstimateurDernierStatut:
    """Reference de mesure : p = 0,8 si le dernier jugement_ia vaut 1, 0,2 s'il vaut 0, 0,5 sinon ;
    une epreuve tenue fixe p a 0,95, une epreuve ratee a 0,2. Aucun oubli. Lot 2.

    Sert uniquement a verifier que le modele fait mieux que ce qu'on a aujourd'hui (critere A1).
    """

    def __init__(self, parametres: Parametres) -> None:
        self.parametres = parametres

    def observer(self, etat: EtatNotion | None, obs: Observation, voisines: Mapping[str, EtatNotion]) -> EtatNotion:
        raise NotImplementedError("lot 2")

    def clore_seance(self, etat: EtatNotion, horodatage: str) -> EtatNotion:
        raise NotImplementedError("lot 2")

    def predire_epreuve(self, etat: EtatNotion, horodatage: str, epreuve: str) -> Prediction:
        raise NotImplementedError("lot 2")

    def lire_epreuve(self, etat: EtatNotion, tenu: bool, horodatage: str) -> EtatNotion:
        raise NotImplementedError("lot 2")


ESTIMATEURS: dict[str, type] = {"bkt": EstimateurBKT, "dernier_statut": EstimateurDernierStatut}


def creer(nom: str, parametres: Parametres) -> Estimateur:
    if nom not in ESTIMATEURS:
        raise ValueError(f"estimateur inconnu : {nom} (connus : {', '.join(ESTIMATEURS)})")
    estimateur: Estimateur = ESTIMATEURS[nom](parametres)
    return estimateur
