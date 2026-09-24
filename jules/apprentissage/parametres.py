"""Parametres du modele de l'eleve : valeurs par defaut sourcees, lecture et validation (§10).

Une valeur absurde arrete le demarrage avec un message clair (ErreurParametres), plutot que de
produire en silence des probabilites fausses.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from jules.apprentissage.etat import CAPTEURS, CAPTEURS_TENTATIVE


class ErreurParametres(ValueError):
    pass


@dataclass(frozen=True)
class Capteur:
    se: float  # P(x=1 | L)
    sp: float  # P(x=0 | non L)

    def informatif(self, marge: float = 0.0) -> bool:
        return self.se + self.sp > 1.0 + marge


# §4.1 - points de depart, recales ensuite par la calibration (§7)
CAPTEURS_DEFAUT: dict[str, Capteur] = {
    "tentative_aide0": Capteur(0.85, 0.80),
    "tentative_aide1": Capteur(0.85, 0.65),
    "tentative_aide2": Capteur(0.85, 0.50),
    "tentative_aide3": Capteur(0.90, 0.35),
    "auto_correction": Capteur(0.45, 0.92),
    "explication": Capteur(0.55, 0.90),
    "declaration": Capteur(0.90, 0.25),
    "jugement_ia": Capteur(0.85, 0.60),
    "epreuve": Capteur(0.95, 0.90),  # indicatif : l'epreuve passe par la vraisemblance du §5.3
}

# §4.4 - probabilite d'apprendre pendant une tentative, selon l'aide recue avant
APPRENTISSAGE_DEFAUT: dict[int, float] = {0: 0.10, 1: 0.12, 2: 0.15, 3: 0.15}

# §5.2 - FSRS-4.5, vecteur publie (wiki "The Algorithm", open-spaced-repetition/awesome-fsrs)
FSRS45_DEFAUT: tuple[float, ...] = (
    0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474,
    0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755,
)  # fmt: skip


@dataclass(frozen=True)
class Politique:
    """Seuils du §6.2 (entree / sortie, pour l'hysteresis)."""

    gamma_reussite: float = 0.4
    gamma_frustration: float = 0.5
    erreurs_consecutives: int = 3
    frustration_entree: float = 0.60
    frustration_sortie: float = 0.45
    fatigue_minutes: float = 40.0
    fatigue_fenetre: int = 4
    decouverte_n_eff: float = 3.0
    fragile_entree: float = 0.55
    fragile_sortie: float = 0.62
    facile_entree: float = 0.90
    facile_sortie: float = 0.83
    facile_tentatives: int = 3
    maintien: int = 2
    pause_ecart_minutes: float = 10.0


@dataclass(frozen=True)
class Parametres:
    capteurs: dict[str, Capteur] = field(default_factory=lambda: dict(CAPTEURS_DEFAUT))
    apprentissage: dict[int, float] = field(default_factory=lambda: dict(APPRENTISSAGE_DEFAUT))
    poids_certitude: dict[str, float] = field(default_factory=lambda: {"haute": 1.0, "moyenne": 0.7, "basse": 0.4})
    poids_partiel: float = 0.5
    prior_global: float = 0.30
    prior_force: float = 5.0
    decroissance: float = 0.5  # rho, §4.3
    plafond_seance: float = 2.0  # c, en log-odds, §4.3
    fsrs: tuple[float, ...] = FSRS45_DEFAUT
    retention_cible: float = 0.85
    glissement_epreuve: float = 0.05  # s_e, fixe
    chance_epreuve: float = 0.10  # g_e, fixe
    politique: Politique = field(default_factory=Politique)
    calibration_active: bool = True
    epreuves_min: int = 8
    force_a_priori: float = 5.0
    fenetre_mesure: int = 60
    carnet_actif: bool = True
    seuil_surprise: float = 1.386  # ln 4 arrondi : Jules donnait 25 % ou moins a ce qui s'est passe (§8.1)
    max_lecons: int = 12
    expiration_jours: int = 45
    lecons_prompt: int = 5

    def avec_capteurs(self, capteurs: dict[str, Capteur]) -> Parametres:
        """Copie avec des capteurs recales (la calibration ne modifie jamais les parametres en place)."""
        return replace(self, capteurs={**self.capteurs, **capteurs})


def _proba(nom: str, valeur: Any, ouvert: bool = True) -> float:
    try:
        v = float(valeur)
    except (TypeError, ValueError) as err:
        raise ErreurParametres(f"{nom} : nombre attendu, recu {valeur!r}") from err
    if not (0.0 < v < 1.0 if ouvert else 0.0 <= v <= 1.0):
        bornes = "]0, 1[" if ouvert else "[0, 1]"
        raise ErreurParametres(f"{nom} : doit etre dans {bornes}, recu {v}")
    return v


def _positif(nom: str, valeur: Any) -> float:
    try:
        v = float(valeur)
    except (TypeError, ValueError) as err:
        raise ErreurParametres(f"{nom} : nombre attendu, recu {valeur!r}") from err
    if v <= 0:
        raise ErreurParametres(f"{nom} : doit etre > 0, recu {v}")
    return v


def depuis_reglages(reglages: dict[str, Any] | None) -> Parametres:
    """Lit la section `reglages` du module modele_eleve (config.yaml) et valide tout."""
    r = reglages or {}
    defaut = Parametres()

    capteurs = dict(defaut.capteurs)
    for nom, brut in (r.get("capteurs") or {}).items():
        if nom not in CAPTEURS:
            raise ErreurParametres(f"capteurs.{nom} : capteur inconnu (connus : {', '.join(CAPTEURS)})")
        brut = brut or {}
        capteurs[nom] = Capteur(
            _proba(f"capteurs.{nom}.se", brut.get("se", capteurs[nom].se)),
            _proba(f"capteurs.{nom}.sp", brut.get("sp", capteurs[nom].sp)),
        )
    for nom, c in capteurs.items():
        if not c.informatif():
            raise ErreurParametres(f"capteurs.{nom} : se + sp doit depasser 1 (sinon le capteur ment), recu {c}")

    apprentissage = dict(defaut.apprentissage)
    for cle, valeur in (r.get("apprentissage") or {}).items():
        niveau = int(str(cle).removeprefix("aide"))
        if niveau not in apprentissage:
            raise ErreurParametres(f"apprentissage.{cle} : niveau d'aide 0 a 3 attendu")
        apprentissage[niveau] = _proba(f"apprentissage.{cle}", valeur, ouvert=False)

    prior = r.get("prior") or {}
    repetition = r.get("repetition") or {}
    oubli = r.get("oubli") or {}
    calibration = r.get("calibration") or {}
    carnet = r.get("carnet") or {}

    pol_brut = r.get("politique") or {}
    inconnus = set(pol_brut) - set(Politique.__dataclass_fields__)
    if inconnus:
        raise ErreurParametres(f"politique : reglages inconnus {sorted(inconnus)}")
    politique = replace(defaut.politique, **pol_brut)
    for entree, sortie, sens in (
        ("frustration_entree", "frustration_sortie", "descend"),
        ("fragile_entree", "fragile_sortie", "monte"),
        ("facile_entree", "facile_sortie", "descend"),
    ):
        e, s = getattr(politique, entree), getattr(politique, sortie)
        _proba(f"politique.{entree}", e)
        _proba(f"politique.{sortie}", s)
        if (sens == "descend" and not s < e) or (sens == "monte" and not s > e):
            raise ErreurParametres(f"politique : hysteresis inversee entre {entree}={e} et {sortie}={s}")
    if not politique.fragile_sortie < politique.facile_sortie:
        raise ErreurParametres("politique : les zones fragile et trop_facile se chevauchent")

    parametres = Parametres(
        capteurs=capteurs,
        apprentissage=apprentissage,
        prior_global=_proba("prior.global", prior.get("global", defaut.prior_global)),
        prior_force=_positif("prior.force", prior.get("force", defaut.prior_force)),
        decroissance=float(repetition.get("decroissance", defaut.decroissance)),
        plafond_seance=_positif("repetition.plafond_seance", repetition.get("plafond_seance", defaut.plafond_seance)),
        retention_cible=_proba("oubli.retention_cible", oubli.get("retention_cible", defaut.retention_cible)),
        glissement_epreuve=_proba(
            "oubli.glissement_epreuve", oubli.get("glissement_epreuve", defaut.glissement_epreuve)
        ),
        chance_epreuve=_proba("oubli.chance_epreuve", oubli.get("chance_epreuve", defaut.chance_epreuve)),
        politique=politique,
        calibration_active=bool(calibration.get("actif", defaut.calibration_active)),
        epreuves_min=int(calibration.get("epreuves_min", defaut.epreuves_min)),
        force_a_priori=_positif("calibration.force_a_priori", calibration.get("force_a_priori", defaut.force_a_priori)),
        fenetre_mesure=int(calibration.get("fenetre_mesure", defaut.fenetre_mesure)),
        carnet_actif=bool(carnet.get("actif", defaut.carnet_actif)),
        seuil_surprise=_positif("carnet.seuil_surprise", carnet.get("seuil_surprise", defaut.seuil_surprise)),
        max_lecons=int(carnet.get("max_lecons", defaut.max_lecons)),
        expiration_jours=int(carnet.get("expiration_jours", defaut.expiration_jours)),
    )
    if parametres.decroissance < 0:
        raise ErreurParametres("repetition.decroissance : doit etre >= 0")
    if parametres.glissement_epreuve + parametres.chance_epreuve >= 1:
        raise ErreurParametres("oubli : glissement_epreuve + chance_epreuve doit rester < 1")
    if set(CAPTEURS_TENTATIVE) - set(parametres.capteurs):
        raise ErreurParametres("capteurs : les quatre capteurs de tentative sont obligatoires")
    return parametres
