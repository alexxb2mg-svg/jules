"""Estimateurs : des observations a une croyance chiffree par notion (docs/MODELE-ELEVE.md, §4, §5.3).

Deux estimateurs, interchangeables par le reglage `estimateur` :
  - `bkt`            : tracage bayesien multi-capteurs, avec oubli FSRS-4.5 (le modele) ;
  - `dernier_statut` : l'ancienne regle « le dernier statut gagne », gardee comme reference de mesure.

Fonctions pures : un estimateur ne modifie jamais l'etat recu, il en renvoie un nouveau.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Protocol

from jules.apprentissage import oubli
from jules.apprentissage.etat import CAPTEURS_TENTATIVE, EtatNotion, Observation, Prediction
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


def matiere_de(notion: str) -> str:
    """La matiere d'une cle de notion (« Mathématiques : fractions » -> « Mathématiques »)."""
    return notion.split(" : ", 1)[0]


def p_de(etat: EtatNotion) -> float:
    return sigmoide(etat.log_odds)


def retention_actuelle(etat: EtatNotion, horodatage: str) -> float:
    """R(t, S) depuis la derniere revision ; 1 tant que la notion n'a pas de stabilite."""
    if etat.stabilite is None or etat.derniere_revision is None:
        return 1.0
    return oubli.retention(oubli.jours_entre(etat.derniere_revision, horodatage), etat.stabilite)


def a_reviser(etats: Iterable[EtatNotion], horodatage: str, retention_cible: float, maximum: int) -> list[EtatNotion]:
    """§5.4 : notions dont la retention predite est passee sous la cible, les plus exposees d'abord."""
    candidates = []
    for e in etats:
        if e.stabilite is None:
            continue
        r = retention_actuelle(e, horodatage)
        if r < retention_cible:
            candidates.append((r, e.notion, e))
    candidates.sort(key=lambda c: (c[0], c[1]))
    return [e for _, _, e in candidates[:maximum]]


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
    """Tracage bayesien multi-capteurs, avec oubli FSRS-4.5 (§4, §5).

    Convention : `log_odds` est la croyance P(L) a l'instant `derniere_revision`. Entre deux revisions,
    la probabilite que la notion soit encore disponible vaut p x R(t, S) (§5.3). Au debut d'une nouvelle
    seance sur la notion, cet oubli est applique (p <- p R) et la seance devient la nouvelle revision :
    c'est le meme modele generatif que celui de l'epreuve, donc la calibration (§7) peut le rejouer.
    """

    def __init__(self, parametres: Parametres) -> None:
        self.parametres = parametres

    # --- seances -------------------------------------------------------------
    def _nouvelle_seance(self, etat: EtatNotion, seance: str, horodatage: str) -> EtatNotion:
        if etat.seance_courante is not None and not etat.seance_close:
            etat = self.clore_seance(etat, etat.derniere_observation or horodatage)
        log_odds, retention_debut = etat.log_odds, None
        revision = etat.derniere_revision
        if etat.stabilite is not None and etat.derniere_revision is not None:
            retention_debut = retention_actuelle(etat, horodatage)
            log_odds = borner(logit(sigmoide(etat.log_odds) * retention_debut))
            revision = horodatage
        return replace(
            etat,
            log_odds=log_odds,
            derniere_revision=revision,
            seance_courante=seance,
            seance_close=False,
            retention_seance=retention_debut,
            delta_seance=0.0,
            rangs_seance={},
            reussite_sans_aide_seance=False,
            reussite_avec_aide_seance=False,
        )

    def observer(self, etat: EtatNotion | None, obs: Observation, voisines: Mapping[str, EtatNotion]) -> EtatNotion:
        """Integre une observation (§4.2 a §4.5). `etat` None : notion nouvelle.

        Ordre : prior (notion nouvelle) ; nouvelle seance (cloture FSRS de la precedente, oubli p <- p R) ;
        poids decroissant par capteur dans la seance ; delta log-odds plafonne sur la seance ; transition
        d'apprentissage apres une tentative. L'epreuve ne passe PAS par ici : voir lire_epreuve.
        """
        par = self.parametres
        if obs.capteur == "epreuve" or obs.capteur not in par.capteurs:
            raise ValueError(f"capteur non observable ici : {obs.capteur}")
        if etat is None:
            matiere = matiere_de(obs.notion)
            memes = [(e.log_odds, e.n_eff) for k, e in voisines.items() if k != obs.notion and matiere_de(k) == matiere]
            etat = EtatNotion(obs.notion, prior_notion(memes, par.prior_global, par.prior_force))
        if obs.seance != etat.seance_courante:
            etat = self._nouvelle_seance(etat, obs.seance, obs.horodatage)

        rangs = dict(etat.rangs_seance)
        rang = rangs.get(obs.capteur, 0) + 1
        rangs[obs.capteur] = rang
        poids = poids_decroissant(obs.poids, rang, par.decroissance)
        brut = delta_log_odds(par.capteur(obs.capteur, matiere_de(obs.notion)), obs.valeur, poids)
        delta = plafonner(brut, etat.delta_seance, par.plafond_seance)
        log_odds = borner(etat.log_odds + delta)

        sans_aide, avec_aide = etat.reussite_sans_aide_seance, etat.reussite_avec_aide_seance
        if obs.capteur in CAPTEURS_TENTATIVE:
            log_odds = borner(logit(transition(sigmoide(log_odds), par.apprentissage.get(obs.aide, 0.0))))
            if obs.valeur == 1 and not obs.partiel:
                if obs.aide == 0:
                    sans_aide = True
                else:
                    avec_aide = True
        return replace(
            etat,
            log_odds=log_odds,
            n_eff=etat.n_eff + poids,
            delta_seance=etat.delta_seance + delta,
            rangs_seance=rangs,
            reussite_sans_aide_seance=sans_aide,
            reussite_avec_aide_seance=avec_aide,
            derniere_observation=obs.horodatage,
        )

    def clore_seance(self, etat: EtatNotion, horodatage: str) -> EtatNotion:
        """Fin de seance : premiere seance -> S0, D0 (§5.1) ; seance suivante -> revision FSRS (§5.2).

        Idempotent. Note d'une revision : good si reussite sans aide, hard si reussite avec aide seulement,
        again sinon. Une revision le jour meme laisse S presque inchange (R proche de 1) : c'est FSRS.
        """
        if etat.seance_courante is None or etat.seance_close:
            return etat
        w, p = self.parametres.fsrs, sigmoide(etat.log_odds)
        if etat.stabilite is None or etat.difficulte is None:
            note = oubli.note_premiere_seance(etat.reussite_sans_aide_seance, etat.reussite_avec_aide_seance, p)
            stabilite, difficulte = oubli.stabilite_initiale(note, w), oubli.difficulte_initiale(note, w)
        else:
            note = 3 if etat.reussite_sans_aide_seance else 2 if etat.reussite_avec_aide_seance else 1
            r = etat.retention_seance if etat.retention_seance is not None else 1.0
            if note == 1:
                stabilite = oubli.stabilite_apres_oubli(etat.difficulte, etat.stabilite, r, w)
            else:
                stabilite = oubli.stabilite_apres_succes(etat.difficulte, etat.stabilite, r, note, w)
            difficulte = oubli.difficulte_suivante(etat.difficulte, note, w)
        return replace(
            etat, stabilite=stabilite, difficulte=difficulte, derniere_revision=horodatage, seance_close=True
        )

    # --- epreuves ------------------------------------------------------------
    def predire_epreuve(self, etat: EtatNotion, horodatage: str, epreuve: str) -> Prediction:
        """§5.3 : pi = p [R (1 - s_e) + (1 - R) g_e] + (1 - p) g_e, figee au lancement."""
        etat = self.clore_seance(etat, etat.derniere_observation or horodatage)
        par, p = self.parametres, sigmoide(etat.log_odds)
        r = retention_actuelle(etat, horodatage)
        pi = oubli.proba_epreuve(p, r, par.glissement_epreuve, par.chance_epreuve)
        return Prediction(etat.notion, pi=pi, p=p, retention=r, epreuve=epreuve, horodatage=horodatage)

    def lire_epreuve(self, etat: EtatNotion, tenu: bool, horodatage: str) -> EtatNotion:
        """§5.3 puis §5.2 : P(L maintenant) = p R, Bayes par l'epreuve (non plafonnee), puis S et D par
        FSRS (good si tenu, again sinon). L'epreuve devient la derniere revision."""
        etat = self.clore_seance(etat, etat.derniere_observation or horodatage)
        par, w = self.parametres, self.parametres.fsrs
        r = retention_actuelle(etat, horodatage)
        maintenant = sigmoide(etat.log_odds) * r
        s_e, g_e = par.glissement_epreuve, par.chance_epreuve
        vrai_l, vrai_non_l = (1 - s_e, g_e) if tenu else (s_e, 1 - g_e)
        log_odds = mise_a_jour_bayes(logit(maintenant), vrai_l, vrai_non_l)
        note = 3 if tenu else 1
        if etat.stabilite is None or etat.difficulte is None:
            stabilite, difficulte = oubli.stabilite_initiale(note, w), oubli.difficulte_initiale(note, w)
        else:
            if tenu:
                stabilite = oubli.stabilite_apres_succes(etat.difficulte, etat.stabilite, r, note, w)
            else:
                stabilite = oubli.stabilite_apres_oubli(etat.difficulte, etat.stabilite, r, w)
            difficulte = oubli.difficulte_suivante(etat.difficulte, note, w)
        return replace(
            etat,
            log_odds=log_odds,
            n_eff=etat.n_eff + 1.0,
            stabilite=stabilite,
            difficulte=difficulte,
            derniere_revision=horodatage,
            seance_courante=None,
            seance_close=True,
            retention_seance=None,
        )


class EstimateurDernierStatut:
    """Reference de mesure : l'ancienne regle « le dernier statut gagne ».

    p = 0,8 si le dernier jugement_ia vaut 1, 0,2 s'il vaut 0, 0,5 sinon ; une epreuve tenue fixe p a
    0,95, une epreuve ratee a 0,2. Aucun oubli : pi = p. Sert uniquement au critere A1.
    """

    def __init__(self, parametres: Parametres) -> None:
        self.parametres = parametres

    def observer(self, etat: EtatNotion | None, obs: Observation, voisines: Mapping[str, EtatNotion]) -> EtatNotion:
        etat = etat or EtatNotion(obs.notion, 0.0)
        log_odds = logit(0.8 if obs.valeur else 0.2) if obs.capteur == "jugement_ia" else etat.log_odds
        return replace(
            etat,
            log_odds=log_odds,
            n_eff=etat.n_eff + obs.poids,
            seance_courante=obs.seance,
            derniere_observation=obs.horodatage,
            derniere_revision=obs.horodatage,
        )

    def clore_seance(self, etat: EtatNotion, horodatage: str) -> EtatNotion:
        return etat

    def predire_epreuve(self, etat: EtatNotion, horodatage: str, epreuve: str) -> Prediction:
        p = sigmoide(etat.log_odds)
        return Prediction(etat.notion, pi=p, p=p, retention=1.0, epreuve=epreuve, horodatage=horodatage)

    def lire_epreuve(self, etat: EtatNotion, tenu: bool, horodatage: str) -> EtatNotion:
        return replace(
            etat, log_odds=logit(0.95 if tenu else 0.2), n_eff=etat.n_eff + 1.0, derniere_revision=horodatage
        )


ESTIMATEURS: dict[str, type] = {"bkt": EstimateurBKT, "dernier_statut": EstimateurDernierStatut}


def creer(nom: str, parametres: Parametres) -> Estimateur:
    if nom not in ESTIMATEURS:
        raise ValueError(f"estimateur inconnu : {nom} (connus : {', '.join(ESTIMATEURS)})")
    estimateur: Estimateur = ESTIMATEURS[nom](parametres)
    return estimateur
