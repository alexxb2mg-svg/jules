"""Politique : l'etat de la seance -> un reglage du comportement de Jules pour le message suivant (§6).

La politique ne touche que les curseurs de `Reglage` (etayage, difficulte, explication, pause).
Elle ne peut lever aucune regle de consignes/pedagogie.md ni de consignes/securite.md : le texte
injecte vient de consignes/politique.yaml, relu par des humains, et passe APRES la pedagogie.
"""

from __future__ import annotations

from jules.apprentissage.etat import EtatNotion, EtatSeance, Observation, Reglage
from jules.apprentissage.parametres import Politique

# §6.3 - un reglage par etat. Modifiable par configuration dans une version ulterieure si besoin.
REGLAGES: dict[str, Reglage] = {
    "frustration": Reglage("frustration", etayage=3, difficulte=-1, exiger_explication=False, proposer_pause=True),
    "fatigue": Reglage("fatigue", etayage=2, difficulte=-1, exiger_explication=False, proposer_pause=True),
    "decouverte": Reglage("decouverte", etayage=2, difficulte=0, exiger_explication=True, proposer_pause=False),
    "fragile": Reglage("fragile", etayage=2, difficulte=-1, exiger_explication=True, proposer_pause=False),
    "trop_facile": Reglage("trop_facile", etayage=1, difficulte=1, exiger_explication=False, proposer_pause=False),
    "zone_cible": Reglage("zone_cible", etayage=1, difficulte=0, exiger_explication=True, proposer_pause=False),
}

CREDITS_AIDE = {0: 1.0, 1: 0.75, 2: 0.5, 3: 0.25}  # §6.1


def ema(precedent: float | None, x: float, gamma: float) -> float:
    """s_t = gamma x_t + (1 - gamma) s_(t-1) ; premier point : x."""
    return x if precedent is None else gamma * x + (1 - gamma) * precedent


def credit(obs: Observation) -> float | None:
    """§6.1 : credit d'une tentative (None si l'observation n'est pas une tentative)."""
    if not obs.capteur.startswith("tentative_aide"):
        return None
    if obs.valeur == 0:
        return 0.0
    base = CREDITS_AIDE.get(obs.aide, 0.25)
    return base * 0.5 if obs.partiel else base


def signal_frustration(obs: Observation, erreurs_consecutives: int, seuil_erreurs: int) -> float:
    """§6.1 : 1 si frustre/decourage, 0,5 si hesitant, +0,5 des la n-ieme erreur d'affilee, borne a 1."""
    x = {"frustre": 1.0, "decourage": 1.0, "hesitant": 0.5}.get(obs.affect, 0.0)
    if erreurs_consecutives >= seuil_erreurs:
        x += 0.5
    return min(1.0, x)


def etat_vise(seance: EtatSeance, notion: EtatNotion | None, reglages: Politique) -> str:
    """§6.2 : l'etat que les indicateurs designent, avec l'hysteresis appliquee depuis l'etat actuel.

    Priorite : frustration, fatigue, decouverte, fragile, trop_facile, zone_cible.
    Lot 5 - regles precises :
      - frustration : entree f >= frustration_entree ; si on y est deja, on y reste tant que
        f >= frustration_sortie.
      - fatigue : minutes >= fatigue_minutes ET les `fatigue_fenetre` derniers credits ont une pente
        de regression strictement negative. Ne se quitte qu'en changeant de seance.
      - decouverte : notion None ou notion.n_eff < decouverte_n_eff.
      - fragile : entree reussite < fragile_entree ; sortie quand reussite >= fragile_sortie.
      - trop_facile : entree reussite >= facile_entree ET tentatives_sans_aide >= facile_tentatives ;
        sortie quand reussite < facile_sortie.
      - zone_cible : sinon.
    """
    raise NotImplementedError("lot 5 : docs/MODELE-ELEVE.md §6.2")


def avancer(
    seance: EtatSeance, obs: Observation, notion: EtatNotion | None, reglages: Politique, horodatage: str
) -> EtatSeance:
    """§6.1 et §6.2 : integre une observation dans la seance et decide de l'etat applique.

    Lot 5 :
      1. minutes : ajoute l'ecart depuis dernier_message s'il est <= pause_ecart_minutes.
      2. si tentative : reussite = ema(reussite, credit, gamma_reussite), la premiere tentative de la
         seance partant de (credit + p de la notion) / 2 ; historique_credits ;
         erreurs_consecutives (remise a 0 sur un credit > 0) ; tentatives_sans_aide.
      3. frustration = ema(frustration, signal_frustration(...), gamma_frustration).
      4. vise = etat_vise(...). Anti-oscillation : on bascule vers `vise` apres `maintien` messages
         consecutifs ou il est vise ; vers `frustration`, tout de suite.
    Pure : renvoie une nouvelle EtatSeance, ne modifie pas celle recue.
    """
    raise NotImplementedError("lot 5 : docs/MODELE-ELEVE.md §6.1 et §6.2")


def reglage(seance: EtatSeance) -> Reglage:
    return REGLAGES.get(seance.etat, REGLAGES["zone_cible"])
