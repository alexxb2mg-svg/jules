"""Simulateur d'eleves virtuels : la preuve, avant de toucher un vrai eleve (docs/MODELE-ELEVE.md, §9).

Un eleve virtuel a une verite cachee que le modele ne voit pas : etat compris / pas compris par notion,
vrais capteurs, vraie vitesse d'apprentissage, vraie stabilite de memoire, et un juge IA eventuellement
biaise. Le simulateur produit exactement ce que la brique produirait en vrai (observations, epreuves),
si bien que l'estimateur, la calibration et la politique se mesurent contre la verite.

La memoire vraie suit FSRS-4.5 avec une stabilite initiale propre a l'eleve (log-normale autour de
3 jours) : le modele, lui, part des valeurs publiees. L'ecart entre les deux est voulu.

Tout est deterministe a graine fixee : les criteres A1 a A6 sont des tests.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from jules.apprentissage import estimateurs, oubli
from jules.apprentissage.etat import EtatNotion, Observation, Prediction, ResultatEpreuve
from jules.apprentissage.parametres import Capteur, Parametres

DEBUT = datetime.fromisoformat("2026-09-01T17:00:00+02:00")
CAPTEURS_BONUS = ("auto_correction", "explication")  # emis de temps en temps, pas a chaque tentative


@dataclass(frozen=True)
class ProfilVirtuel:
    """Les parametres VRAIS d'un eleve virtuel (tires une fois a sa creation).

    Les capteurs vrais s'ecartent volontairement des valeurs par defaut du modele, sinon la calibration
    n'aurait rien a corriger. `biais_juge` : de combien le juge IA surestime (Sp vrai plus bas).
    """

    graine: int
    capteurs: dict[str, Capteur]
    apprentissage: dict[int, float]
    stabilite_initiale: float  # jours
    prior: float  # P(L) des notions au depart
    biais_juge: float = 0.0
    propension_declarer: float = 0.5  # dit « j'ai compris » en fin de seance, avec cette probabilite
    frustration_apres_erreurs: int = 3


@dataclass(frozen=True)
class Scenario:
    eleves: int = 200
    notions: int = 20
    jours: int = 60
    seances_par_semaine: float = 4.0
    tentatives_par_seance: tuple[int, int] = (4, 12)
    biais_juge: float = 0.0
    epreuve_notions_max: int = 3
    graine: int = 20260924


@dataclass
class Trace:
    """Ce que le simulateur a produit pour un eleve : observations et epreuves dans l'ordre, et la verite."""

    profil: ProfilVirtuel
    observations: list[Observation] = field(default_factory=list)
    epreuves: list[ResultatEpreuve] = field(default_factory=list)
    verite: dict[str, list[tuple[str, bool]]] = field(default_factory=dict)  # notion -> (horodatage, L vrai)
    seances: list[list[Observation]] = field(default_factory=list)  # observations groupees par seance


def _bruite(rng: random.Random, v: float, amplitude: float) -> float:
    return min(0.98, max(0.02, v + rng.uniform(-amplitude, amplitude)))


def tirer_profil(rng: random.Random, biais_juge: float, parametres: Parametres | None = None) -> ProfilVirtuel:
    """Se/Sp vrais = defauts du modele +- 0,10 (Se + Sp >= 1,05) ; jugement_ia : Sp vrai = Sp tire -
    biais_juge (borne a 0,05) ; apprentissage vrai = defaut x [0,5 ; 1,5] ; prior dans [0,1 ; 0,5] ;
    stabilite initiale vraie log-normale centree sur 3 jours (sigma 0,5)."""
    par = parametres or Parametres()
    capteurs: dict[str, Capteur] = {}
    for nom, c in par.capteurs.items():
        if nom == "epreuve":
            continue
        for _ in range(50):
            se, sp = _bruite(rng, c.se, 0.10), _bruite(rng, c.sp, 0.10)
            if se + sp >= 1.05:
                break
        else:
            se, sp = c.se, c.sp
        if nom == "jugement_ia":
            sp = max(0.05, sp - biais_juge)
        capteurs[nom] = Capteur(se, sp)
    apprentissage = {a: min(0.9, t * rng.uniform(0.5, 1.5)) for a, t in par.apprentissage.items()}
    return ProfilVirtuel(
        graine=rng.randrange(2**31),
        capteurs=capteurs,
        apprentissage=apprentissage,
        stabilite_initiale=math.exp(math.log(3.0) + rng.gauss(0, 0.5)),
        prior=rng.uniform(0.1, 0.5),
        biais_juge=biais_juge,
        propension_declarer=rng.uniform(0.3, 0.8),
    )


@dataclass
class _Verite:
    compris: bool
    stabilite: float
    difficulte: float
    revision: datetime | None = None


def _heure(t: datetime) -> str:
    return t.isoformat(timespec="seconds")


def _oublier(v: _Verite, t: datetime, rng: random.Random) -> float:
    """Oubli vrai depuis la derniere revision ; renvoie R vrai. La revision est mise a t."""
    r = 1.0
    if v.revision is not None:
        r = oubli.retention((t - v.revision).total_seconds() / 86400, v.stabilite)
        if v.compris and rng.random() > r:
            v.compris = False
    return r


def _reviser(v: _Verite, r: float, reussi: bool, w: Sequence[float], premiere: bool, s0: float) -> None:
    if premiere:
        v.stabilite = s0 * (1.0 if reussi else 0.4)
        return
    if reussi:
        v.stabilite = oubli.stabilite_apres_succes(v.difficulte, v.stabilite, r, 3, w)
        v.difficulte = oubli.difficulte_suivante(v.difficulte, 3, w)
    else:
        v.stabilite = oubli.stabilite_apres_oubli(v.difficulte, v.stabilite, r, w)
        v.difficulte = oubli.difficulte_suivante(v.difficulte, 1, w)


def simuler_eleve(
    profil: ProfilVirtuel,
    scenario: Scenario,
    parametres: Parametres | None = None,
    politique_active: bool = False,
) -> Trace:
    """Une scolarite virtuelle de `scenario.jours` jours.

    Chaque jour : peut-etre une epreuve (regle du §5.4 appliquee aux etats du MODELE, au plus une par
    jour), puis peut-etre une seance sur une notion (nouvelle ou a revoir). Pendant la seance, l'aide
    monte apres une erreur et retombe apres une reussite ; le resultat est tire selon L vrai et le
    capteur vrai du niveau d'aide ; l'eleve peut apprendre a chaque tentative. En fin de seance : une
    declaration et un jugement_ia, tires selon les capteurs vrais (juge biaise compris).
    """
    par = parametres or Parametres()
    rng = random.Random(profil.graine)  # noqa: S311 - simulation reproductible, pas de la cryptographie
    modele = estimateurs.EstimateurBKT(par)
    etats: dict[str, EtatNotion] = {}
    verites: dict[str, _Verite] = {}
    trace = Trace(profil)
    w = par.fsrs
    matieres = ("Mathématiques", "Français", "Histoire-Géographie")
    noms = [f"{matieres[i % len(matieres)]} : notion {i:02d}" for i in range(scenario.notions)]
    vues: list[str] = []
    numero = 0

    def emettre(obs: Observation, seance: list[Observation]) -> None:
        seance.append(obs)
        trace.observations.append(obs)
        etats[obs.notion] = modele.observer(etats.get(obs.notion), obs, etats)

    def tirer(nom: str, compris: bool) -> int:
        c = profil.capteurs[nom]
        return int(rng.random() < (c.se if compris else 1 - c.sp))

    for jour in range(scenario.jours):
        t = DEBUT + timedelta(days=jour)
        # --- epreuve eventuelle, sur les etats du modele ---
        a_faire = estimateurs.a_reviser(etats.values(), _heure(t), par.retention_cible, scenario.epreuve_notions_max)
        if a_faire and rng.random() < 0.6:
            numero += 1
            ident = f"epreuve-{numero}"
            for e in a_faire:
                v = verites[e.notion]
                r = _oublier(v, t, rng)
                tenu = rng.random() < ((1 - par.glissement_epreuve) if v.compris else par.chance_epreuve)
                trace.epreuves.append(ResultatEpreuve(e.notion, _heure(t), tenu, ident))
                etats[e.notion] = modele.lire_epreuve(etats[e.notion], tenu, _heure(t))
                _reviser(v, r, v.compris, w, False, profil.stabilite_initiale)
                v.revision = t
                trace.verite.setdefault(e.notion, []).append((_heure(t), v.compris))
            t += timedelta(minutes=10)
        # --- seance eventuelle ---
        if rng.random() >= scenario.seances_par_semaine / 7:
            continue
        numero += 1
        ident = f"seance-{numero}"
        nouvelles = [n for n in noms if n not in vues]
        if nouvelles and (not vues or rng.random() < 0.45):
            notion = nouvelles[0]
            vues.append(notion)
            verites[notion] = _Verite(rng.random() < profil.prior, profil.stabilite_initiale, w[4])
        else:
            notion = rng.choice(vues)
        v = verites[notion]
        premiere = v.revision is None
        r = _oublier(v, t, rng)
        trace.verite.setdefault(notion, []).append((_heure(t), v.compris))
        seance: list[Observation] = []
        aide, erreurs, reussite_sans_aide = 0, 0, False
        for _ in range(rng.randint(*scenario.tentatives_par_seance)):
            t += timedelta(minutes=3)
            compris_avant = v.compris
            juste = tirer(f"tentative_aide{aide}", compris_avant)
            affect = "frustre" if erreurs + (1 - juste) >= profil.frustration_apres_erreurs else "neutre"
            emettre(
                Observation(notion, f"tentative_aide{aide}", juste, 1.0, ident, _heure(t), aide=aide, affect=affect),
                seance,
            )
            if not v.compris and rng.random() < profil.apprentissage[aide]:
                v.compris = True
            if juste:
                reussite_sans_aide = reussite_sans_aide or aide == 0
                erreurs, aide = 0, 0
            else:
                erreurs += 1
                aide = min(3, aide + 1)
            if juste and rng.random() < 0.15:
                nom = rng.choice(CAPTEURS_BONUS)
                emettre(Observation(notion, nom, tirer(nom, v.compris), 1.0, ident, _heure(t)), seance)
        t += timedelta(minutes=1)
        if rng.random() < profil.propension_declarer:
            emettre(Observation(notion, "declaration", tirer("declaration", v.compris), 1.0, ident, _heure(t)), seance)
        emettre(Observation(notion, "jugement_ia", tirer("jugement_ia", v.compris), 1.0, ident, _heure(t)), seance)
        etats[notion] = modele.clore_seance(etats[notion], _heure(t))
        _reviser(v, r, v.compris and reussite_sans_aide, w, premiere, profil.stabilite_initiale)
        v.revision = t
        trace.seances.append(seance)
    return trace


def simuler(scenario: Scenario, parametres: Parametres | None = None) -> list[Trace]:
    rng = random.Random(scenario.graine)  # noqa: S311 - simulation reproductible, pas de la cryptographie
    traces = []
    for _ in range(scenario.eleves):
        rng_eleve = random.Random(rng.randrange(2**32))  # noqa: S311
        traces.append(simuler_eleve(tirer_profil(rng_eleve, scenario.biais_juge, parametres), scenario, parametres))
    return traces


def rejouer(
    trace: Trace,
    nom_estimateur: str,
    parametres: Parametres | None = None,
    recalibrer_tous: int = 0,
) -> list[tuple[Prediction, bool]]:
    """Rejoue une trace avec un estimateur : (prediction figee, resultat) pour chaque epreuve.

    Les observations et les epreuves sont fusionnees dans l'ordre chronologique ; a egalite, l'epreuve
    passe apres les observations du meme instant. Avec `recalibrer_tous` = n > 0, la calibration (§7)
    tourne toutes les n epreuves sur les seules donnees deja vues, puis les etats sont reconstruits avec
    les capteurs recales : c'est ce que fera la brique en vrai, sans jamais regarder l'avenir.
    """
    from jules.apprentissage import calibration  # import local : calibration depend de ce module-ci

    depart = parametres or Parametres()
    evenements: list[tuple[str, int, Observation | ResultatEpreuve]] = [
        (o.horodatage, 0, o) for o in trace.observations
    ]
    evenements += [(ep.horodatage, 1, ep) for ep in trace.epreuves]
    evenements.sort(key=lambda x: (x[0], x[1]))

    def rejouer_jusqu_a(fin: int, par: Parametres) -> tuple[estimateurs.Estimateur, dict[str, EtatNotion]]:
        e = estimateurs.creer(nom_estimateur, par)
        etats: dict[str, EtatNotion] = {}
        for _, _, ev in evenements[:fin]:
            if isinstance(ev, Observation):
                etats[ev.notion] = e.observer(etats.get(ev.notion), ev, etats)
            elif ev.notion in etats:
                etats[ev.notion] = e.lire_epreuve(etats[ev.notion], ev.tenu, ev.horodatage)
        return e, etats

    e, etats = rejouer_jusqu_a(0, depart)
    vues_obs: list[Observation] = []
    vues_ep: list[ResultatEpreuve] = []
    sortie: list[tuple[Prediction, bool]] = []
    for i, (_, _, ev) in enumerate(evenements):
        if isinstance(ev, Observation):
            vues_obs.append(ev)
            etats[ev.notion] = e.observer(etats.get(ev.notion), ev, etats)
            continue
        if ev.notion in etats:
            sortie.append((e.predire_epreuve(etats[ev.notion], ev.horodatage, ev.epreuve), ev.tenu))
            etats[ev.notion] = e.lire_epreuve(etats[ev.notion], ev.tenu, ev.horodatage)
        vues_ep.append(ev)
        if recalibrer_tous and len(vues_ep) % recalibrer_tous == 0:
            resultat = calibration.calibrer(vues_obs, vues_ep, depart)
            if resultat is not None:
                e, etats = rejouer_jusqu_a(i + 1, resultat.appliquer(depart))
    return sortie
