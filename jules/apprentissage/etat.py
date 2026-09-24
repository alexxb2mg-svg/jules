"""Structures de donnees du modele de l'eleve (docs/MODELE-ELEVE.md, §3, §4.6, §6, §8).

Toutes serialisables en JSON par `vers_dict` / `depuis_dict` : elles vivent dans le stockage existant
(evenements et etat cle/valeur), jamais dans une table a part.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any, Literal, TypeVar

Capteur = Literal[
    "tentative_aide0",
    "tentative_aide1",
    "tentative_aide2",
    "tentative_aide3",
    "auto_correction",
    "explication",
    "declaration",
    "jugement_ia",
    "epreuve",
]
CAPTEURS: tuple[str, ...] = Capteur.__args__  # type: ignore[attr-defined]
CAPTEURS_TENTATIVE: tuple[str, ...] = ("tentative_aide0", "tentative_aide1", "tentative_aide2", "tentative_aide3")
CAPTEURS_CALIBRABLES: tuple[str, ...] = tuple(c for c in CAPTEURS if c != "epreuve")  # l'epreuve est l'ancre

EtatPolitique = Literal["frustration", "fatigue", "decouverte", "fragile", "trop_facile", "zone_cible"]
ETATS_POLITIQUE: tuple[str, ...] = EtatPolitique.__args__  # type: ignore[attr-defined]

T = TypeVar("T")


def cle_notion(matiere: str, notion: str) -> str:
    """Libelle unique d'une notion, identique a celui des modules suivi, memoire et epreuve."""
    return f"{matiere or 'Autre'} : {notion}"


def _depuis(cls: type[T], donnees: dict[str, Any]) -> T:
    connus = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    return cls(**{k: v for k, v in donnees.items() if k in connus})


@dataclass(frozen=True)
class Observation:
    """Un fait constate sur un echange, reduit a un capteur binaire (§3)."""

    notion: str  # cle_notion(matiere, notion)
    capteur: str  # un des CAPTEURS
    valeur: int  # 0 ou 1
    poids: float  # (0, 1] : certitude de lecture x reduction eventuelle (resultat partiel)
    seance: str  # id de la conversation
    horodatage: str  # ISO 8601 avec fuseau
    aide: int = 0  # niveau d'aide recu avant la tentative (0 a 3), sert a la transition §4.4
    partiel: bool = False  # resultat "partiel" : credit divise par deux dans la politique (§6.1)
    affect: str = "neutre"

    def vers_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def depuis_dict(cls, donnees: dict[str, Any]) -> Observation:
        return _depuis(cls, donnees)


@dataclass
class EtatNotion:
    """Ce que Jules croit d'une notion (§4.6)."""

    notion: str
    log_odds: float  # logit de p(L)
    n_eff: float = 0.0  # somme des poids des preuves recues
    stabilite: float | None = None  # jours (FSRS) ; None tant que la premiere seance n'est pas close
    difficulte: float | None = None  # [1, 10] (FSRS)
    derniere_revision: str | None = None  # ISO : fin de la derniere seance ou epreuve
    derniere_observation: str | None = None
    seance_courante: str | None = None
    delta_seance: float = 0.0  # somme des delta log-odds de la seance courante (plafond §4.3)
    rangs_seance: dict[str, int] = field(default_factory=dict)  # capteur -> nombre d'observations (§4.3)
    reussite_sans_aide_seance: bool = False  # pour la note FSRS de premiere seance (§5.1)
    reussite_avec_aide_seance: bool = False

    def vers_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def depuis_dict(cls, donnees: dict[str, Any]) -> EtatNotion:
        return _depuis(cls, donnees)


@dataclass
class EtatSeance:
    """Indicateurs de la seance en cours (§6.1) et etat de politique retenu (§6.2)."""

    seance: str
    notion: str | None = None
    reussite: float | None = None  # moyenne mobile ; None avant la premiere tentative
    frustration: float = 0.0
    erreurs_consecutives: int = 0
    tentatives_sans_aide: int = 0
    historique_credits: list[float] = field(default_factory=list)  # pour la tendance (fatigue)
    debut: str | None = None
    minutes: float = 0.0
    dernier_message: str | None = None
    etat: str = "decouverte"  # etat applique
    candidat: str | None = None  # etat vise, en attente de confirmation (anti-oscillation)
    maintien_candidat: int = 0

    def vers_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def depuis_dict(cls, donnees: dict[str, Any]) -> EtatSeance:
        return _depuis(cls, donnees)


@dataclass(frozen=True)
class Reglage:
    """Curseurs que la politique a le droit de toucher (§6.3). Rien d'autre."""

    etat: str
    etayage: int  # 0 a 3 : aide maximale avant nouvelle tentative
    difficulte: int  # -1, 0, +1
    exiger_explication: bool
    proposer_pause: bool


@dataclass(frozen=True)
class Prediction:
    """Prediction figee au lancement d'une epreuve (§5.3, §7.4)."""

    notion: str
    pi: float  # P(tient a l'epreuve)
    p: float  # P(L) au lancement
    retention: float  # R(t, S) au lancement
    epreuve: str  # id de la conversation d'epreuve
    horodatage: str

    def vers_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def depuis_dict(cls, donnees: dict[str, Any]) -> Prediction:
        return _depuis(cls, donnees)


@dataclass
class Lecon:
    """Une entree du carnet (§8)."""

    id: str
    portee: Literal["notion", "matiere", "global"]
    cle: str  # la notion, la matiere, ou "" pour global
    sens: Literal["surestimation", "sous_estimation"]
    texte: str
    creee: str  # ISO
    statut: Literal["active", "confirmee", "retiree"] = "active"
    pertes_avant: list[float] = field(default_factory=list)  # perte log. des epreuves de la portee, avant
    pertes_apres: list[float] = field(default_factory=list)
    motif_retrait: str = ""

    def vers_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def depuis_dict(cls, donnees: dict[str, Any]) -> Lecon:
        return _depuis(cls, donnees)
