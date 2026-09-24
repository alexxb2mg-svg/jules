"""Simulateur d'eleves virtuels : la preuve, avant de toucher un vrai eleve (docs/MODELE-ELEVE.md, §9).

Un eleve virtuel a une verite cachee que le modele ne voit pas : etat compris / pas compris par notion,
vrais slip et guess, vraie stabilite de memoire, et un juge IA eventuellement biaise. Le simulateur
produit exactement ce que la brique produirait en vrai (observations, epreuves), si bien que
l'estimateur, la calibration et la politique se mesurent contre la verite.

Tout est deterministe a graine fixee (random.Random(graine)) : les criteres A1 a A8 sont des tests.
Lot 3.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from jules.apprentissage.etat import Observation
from jules.apprentissage.parametres import Capteur


@dataclass(frozen=True)
class ProfilVirtuel:
    """Les parametres VRAIS d'un eleve virtuel (tires une fois a sa creation).

    Les capteurs vrais s'ecartent volontairement des valeurs par defaut du modele, sinon la calibration
    n'aurait rien a corriger. `biais_juge` : probabilite que le juge IA dise « compris » a tort.
    """

    graine: int
    capteurs: dict[str, Capteur]
    apprentissage: dict[int, float]
    stabilite_initiale: float  # jours
    prior: float  # P(L) des notions au depart
    biais_juge: float = 0.0
    propension_declarer: float = 0.5  # dit « j'ai compris » apres une reussite, avec cette probabilite
    frustration_apres_erreurs: int = 3


@dataclass(frozen=True)
class Scenario:
    eleves: int = 200
    notions: int = 20
    jours: int = 60
    seances_par_semaine: float = 4.0
    tentatives_par_seance: tuple[int, int] = (4, 12)
    biais_juge: float = 0.0
    graine: int = 20260924


@dataclass
class Trace:
    """Ce que le simulateur a produit pour un eleve : observations et epreuves dans l'ordre, et la verite."""

    profil: ProfilVirtuel
    observations: list[Observation] = field(default_factory=list)
    epreuves: list[tuple[str, str, bool, float]] = field(default_factory=list)  # comme calibration.calibrer
    verite: dict[str, list[tuple[str, bool]]] = field(default_factory=dict)  # notion -> (horodatage, L vrai)


def tirer_profil(rng: random.Random, biais_juge: float) -> ProfilVirtuel:
    """Lot 3 : Se/Sp vrais = defauts du modele +- bruit uniforme de 0,10, en gardant Se + Sp >= 1,05 ;
    jugement_ia : Sp vrai = Sp par defaut - biais_juge (borne a 0,05). Prior dans [0,1 ; 0,5].
    Stabilite initiale vraie : log-normale centree sur 3 jours."""
    raise NotImplementedError("lot 3")


def simuler_eleve(profil: ProfilVirtuel, scenario: Scenario, politique_active: bool = False) -> Trace:
    """Lot 3. Pour chaque seance :
      - choisir une notion (les notions sont introduites progressivement, puis revues) ;
      - pour chaque tentative : aide tiree (plus d'aide si la politique est en `fragile`) ; resultat tire
        selon L vrai et le capteur vrai du niveau d'aide ; transition vraie non L -> L ;
      - emettre les observations comme observations.vers_observations le ferait, dont `declaration`
        et un `jugement_ia` en fin de seance selon le juge vrai (biais compris) ;
      - entre les seances, oubli vrai : L vrai se perd avec probabilite 1 - R(t, S vrai).
    Epreuves : proposees par la regle du §5.4 appliquee aux ETATS DU MODELE (pas a la verite), resultat
    tire selon la verite (§5.3 avec s_e, g_e vrais = ceux du modele : l'ancre est supposee juste).
    """
    raise NotImplementedError("lot 3")


def simuler(scenario: Scenario) -> list[Trace]:
    rng = random.Random(scenario.graine)  # noqa: S311 - simulation reproductible, pas de la cryptographie
    return [
        simuler_eleve(tirer_profil(random.Random(rng.randrange(2**32)), scenario.biais_juge), scenario)  # noqa: S311
        for _ in range(scenario.eleves)
    ]
