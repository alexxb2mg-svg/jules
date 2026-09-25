"""Politique : l'etat de la seance -> un reglage du comportement de Jules pour le message suivant (§6).

La politique ne touche que les curseurs de `Reglage` (etayage, difficulte, explication, pause).
Elle ne peut lever aucune regle de consignes/pedagogie.md ni de consignes/securite.md : le texte
injecte vient de consignes/politique.yaml, relu par des humains, et passe APRES la pedagogie.
"""

from __future__ import annotations

from dataclasses import replace

from jules.apprentissage.estimateurs import sigmoide
from jules.apprentissage.etat import EtatNotion, EtatSeance, Observation, Reglage
from jules.apprentissage.oubli import jours_entre
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


def pente(valeurs: list[float]) -> float:
    """Pente de la droite des moindres carres de valeurs equidistantes (0 si moins de deux points)."""
    n = len(valeurs)
    if n < 2:
        return 0.0
    xm = (n - 1) / 2
    ym = sum(valeurs) / n
    num = sum((i - xm) * (v - ym) for i, v in enumerate(valeurs))
    den = sum((i - xm) ** 2 for i in range(n))
    return num / den


def etat_vise(seance: EtatSeance, notion: EtatNotion | None, reglages: Politique) -> str:
    """§6.2 : l'etat que les indicateurs designent, avec l'hysteresis appliquee depuis l'etat actuel.

    Priorite : frustration, fatigue, decouverte, fragile, trop_facile, zone_cible. Les seuils de sortie
    s'appliquent quand l'etat applique (`seance.etat`) est deja celui-la : on n'en sort pas au premier
    fremissement.
    """
    actuel = seance.etat
    f = seance.frustration
    if f >= reglages.frustration_entree or (actuel == "frustration" and f >= reglages.frustration_sortie):
        return "frustration"
    fenetre = seance.historique_credits[-reglages.fatigue_fenetre :]
    en_baisse = len(fenetre) >= reglages.fatigue_fenetre and pente(fenetre) < 0
    if actuel == "fatigue" or (seance.minutes >= reglages.fatigue_minutes and en_baisse):
        return "fatigue"
    if notion is None or notion.n_eff < reglages.decouverte_n_eff:
        return "decouverte"
    s = seance.reussite
    if s is None:
        return actuel if actuel in ("fragile", "trop_facile", "zone_cible") else "zone_cible"
    if s < reglages.fragile_entree or (actuel == "fragile" and s < reglages.fragile_sortie):
        return "fragile"
    facile = s >= reglages.facile_entree and seance.tentatives_sans_aide >= reglages.facile_tentatives
    if facile or (actuel == "trop_facile" and s >= reglages.facile_sortie):
        return "trop_facile"
    return "zone_cible"


def avancer(
    seance: EtatSeance, obs: Observation, notion: EtatNotion | None, reglages: Politique, horodatage: str
) -> EtatSeance:
    """§6.1 et §6.2 : integre une observation dans la seance et decide de l'etat applique.

    1. minutes : ajoute l'ecart depuis le dernier message s'il est <= pause_ecart_minutes ;
    2. si tentative : reussite (moyenne mobile ; la premiere tentative de la seance part de la moyenne
       de son credit et du p de la notion), historique des credits, erreurs d'affilee, tentatives sans aide ;
    3. frustration (moyenne mobile du signal) ;
    4. etat vise, puis anti-oscillation : on bascule apres `maintien` messages consecutifs ou le meme etat
       est vise ; vers `frustration`, tout de suite.
    Pure : renvoie une nouvelle EtatSeance, ne modifie pas celle recue.
    """
    s = replace(seance, historique_credits=list(seance.historique_credits))
    premier = s.dernier_message is None
    if s.debut is None:
        s.debut = horodatage
    if s.dernier_message is not None:
        ecart = jours_entre(s.dernier_message, horodatage) * 24 * 60
        if ecart <= reglages.pause_ecart_minutes:
            s.minutes += ecart
    s.dernier_message = horodatage
    s.notion = obs.notion

    c = credit(obs)
    if c is not None:
        if s.reussite is None:
            p = sigmoide(notion.log_odds) if notion is not None else 0.5
            s.reussite = (c + p) / 2
        else:
            s.reussite = ema(s.reussite, c, reglages.gamma_reussite)
        s.historique_credits.append(c)
        s.erreurs_consecutives = 0 if c > 0 else s.erreurs_consecutives + 1
        if obs.aide == 0 and obs.valeur == 1:
            s.tentatives_sans_aide += 1
    s.frustration = ema(
        None if premier else s.frustration,
        signal_frustration(obs, s.erreurs_consecutives, reglages.erreurs_consecutives),
        reglages.gamma_frustration,
    )

    vise = etat_vise(s, notion, reglages)
    if vise == s.etat:
        s.candidat, s.maintien_candidat = None, 0
    elif vise == "frustration":
        s.etat, s.candidat, s.maintien_candidat = vise, None, 0
    else:
        s.maintien_candidat = s.maintien_candidat + 1 if vise == s.candidat else 1
        s.candidat = vise
        if s.maintien_candidat >= reglages.maintien:
            s.etat, s.candidat, s.maintien_candidat = vise, None, 0
    return s


def reglage(seance: EtatSeance) -> Reglage:
    return REGLAGES.get(seance.etat, REGLAGES["zone_cible"])
