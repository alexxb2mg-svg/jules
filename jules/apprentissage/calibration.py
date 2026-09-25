"""Calibration : chaque epreuve sans aide corrige la fiabilite des indices de Jules (§7).

Methode : EM avec a priori Beta (MAP-EM) sur des chaines de Markov cachees a deux etats (non L, L),
une par notion. L'epreuve est l'ancre : ses vraisemblances (§5.3) ne sont jamais recalees.

Le modele generatif rejoue exactement l'estimateur en ligne (§4, §5) :
  - juste avant le premier pas d'une seance, ou avant une epreuve, oubli : L -> non L avec probabilite
    1 - R, R etant la retention que l'estimateur en ligne a calculee a cet instant ;
  - emission d'une observation (capteur k, valeur x, poids w) : P(x | etat) ** w (vraisemblance temperee),
    poids apres decroissance intra-seance (§4.3) mais SANS plafond (garde-fou de l'estimateur en ligne) ;
  - emission d'une epreuve : P(tenu | L) = 1 - s_e, P(tenu | non L) = g_e ;
  - apres une tentative d'aide a : non L -> L avec probabilite T_a (§4.4) ; jamais L -> non L.
Les retentions R se calculent une fois : elles viennent de FSRS, pas des capteurs recales.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace

from jules.apprentissage import estimateurs
from jules.apprentissage.etat import (
    CAPTEURS_CALIBRABLES,
    CAPTEURS_TENTATIVE,
    EtatNotion,
    Observation,
    ResultatEpreuve,
)
from jules.apprentissage.parametres import Capteur, Parametres

MARGE_INFORMATIF = 0.02  # §7.2 : Se + Sp >= 1,02 apres chaque etape M
TOLERANCE = 1e-4
ITERATIONS_MAX = 50
PLANCHER = 1e-12
BORNE = 0.99  # Se et Sp restent dans [0,01 ; 0,99]


@dataclass(frozen=True)
class Pas:
    """Un pas de la chaine d'une notion : une observation, ou le resultat d'une epreuve.

    `retention` : probabilite de garder L juste AVANT ce pas (1 au milieu d'une seance ; R au premier pas
    d'une seance et a une epreuve, §5). `transition` : probabilite T de passer de non L a L APRES ce pas
    (0 pour les capteurs non tentative et pour l'epreuve), cf. §4.4.
    """

    capteur: str
    valeur: int
    poids: float
    transition: float
    retention: float = 1.0


@dataclass
class Chaine:
    notion: str
    matiere: str
    prior: float  # P(L) au premier pas
    pas: list[Pas] = field(default_factory=list)

    @property
    def a_une_epreuve(self) -> bool:
        return any(p.capteur == "epreuve" for p in self.pas)


def construire_chaines(
    observations: Sequence[Observation], epreuves: Sequence[ResultatEpreuve], parametres: Parametres
) -> list[Chaine]:
    """Regroupe observations et epreuves par notion, dans l'ordre chronologique (a egalite, l'epreuve
    apres les observations), en rejouant l'estimateur en ligne pour connaitre les retentions."""
    modele = estimateurs.EstimateurBKT(parametres)
    evenements: list[tuple[str, int, Observation | ResultatEpreuve]] = [(o.horodatage, 0, o) for o in observations]
    evenements += [(e.horodatage, 1, e) for e in epreuves]
    evenements.sort(key=lambda x: (x[0], x[1]))
    etats: dict[str, EtatNotion] = {}
    chaines: dict[str, Chaine] = {}
    rangs: dict[tuple[str, str, str], int] = defaultdict(int)
    for horodatage, _, ev in evenements:
        matiere = estimateurs.matiere_de(ev.notion)
        chaine = chaines.setdefault(ev.notion, Chaine(ev.notion, matiere, parametres.prior_global))
        etat = etats.get(ev.notion)
        if isinstance(ev, Observation):
            nouvelle = etat is None or ev.seance != etat.seance_courante
            etat = modele.observer(etat, ev, etats)
            etats[ev.notion] = etat
            retention = 1.0
            if nouvelle and etat.retention_seance is not None:
                retention = etat.retention_seance
            cle = (ev.notion, ev.seance, ev.capteur)
            rangs[cle] += 1
            poids = estimateurs.poids_decroissant(ev.poids, rangs[cle], parametres.decroissance)
            t = parametres.apprentissage.get(ev.aide, 0.0) if ev.capteur in CAPTEURS_TENTATIVE else 0.0
            chaine.pas.append(Pas(ev.capteur, ev.valeur, poids, t, retention))
        elif etat is not None:
            etat = modele.clore_seance(etat, etat.derniere_observation or horodatage)
            retention = estimateurs.retention_actuelle(etat, horodatage)
            etats[ev.notion] = modele.lire_epreuve(etat, ev.tenu, horodatage)
            chaine.pas.append(Pas("epreuve", int(ev.tenu), 1.0, 0.0, retention))
    return [c for c in chaines.values() if c.pas]


def _emission(pas: Pas, capteurs: Mapping[str, Capteur], parametres: Parametres) -> tuple[float, float]:
    """(P(x | non L), P(x | L)), temperees par le poids."""
    if pas.capteur == "epreuve":
        s_e, g_e = parametres.glissement_epreuve, parametres.chance_epreuve
        return (g_e, 1 - s_e) if pas.valeur else (1 - g_e, s_e)
    c = capteurs[pas.capteur]
    si_l, si_non_l = (c.se, 1 - c.sp) if pas.valeur else (1 - c.se, c.sp)
    return max(PLANCHER, si_non_l) ** pas.poids, max(PLANCHER, si_l) ** pas.poids


def avant_arriere(chaine: Chaine, capteurs: Mapping[str, Capteur], parametres: Parametres) -> list[float]:
    """Passes avant-arriere normalisees : gamma_i = P(L_i | toute la chaine) pour chaque pas.

    Transition de s_(i-1) a s_i : apprentissage T_(i-1) puis retention R_i, soit
    P(L | non L) = T R et P(L | L) = R.
    """
    n = len(chaine.pas)
    if n == 0:
        return []
    emissions = [_emission(p, capteurs, parametres) for p in chaine.pas]

    alphas: list[tuple[float, float]] = []
    p_l = chaine.prior * chaine.pas[0].retention
    for i in range(n):
        if i > 0:
            t, r = chaine.pas[i - 1].transition, chaine.pas[i].retention
            p_l = (alphas[-1][1] + alphas[-1][0] * t) * r
        e0, e1 = emissions[i]
        a0, a1 = (1 - p_l) * e0, p_l * e1
        z = max(PLANCHER, a0 + a1)
        alphas.append((a0 / z, a1 / z))

    betas: list[tuple[float, float]] = [(1.0, 1.0)] * n
    b0, b1 = 1.0, 1.0
    for i in range(n - 2, -1, -1):
        t, r = chaine.pas[i].transition, chaine.pas[i + 1].retention
        e0, e1 = emissions[i + 1]
        suite0, suite1 = e0 * b0, e1 * b1
        n0 = (1 - t * r) * suite0 + t * r * suite1
        n1 = (1 - r) * suite0 + r * suite1
        z = max(PLANCHER, n0 + n1)
        b0, b1 = n0 / z, n1 / z
        betas[i] = (b0, b1)

    gammas = []
    for (a0, a1), (b0, b1) in zip(alphas, betas, strict=True):
        g0, g1 = a0 * b0, a1 * b1
        gammas.append(g1 / max(PLANCHER, g0 + g1))
    return gammas


def projeter(se: float, sp: float) -> Capteur:
    """Ramene (Se, Sp) dans la zone informative Se + Sp >= 1 + marge (projection orthogonale sur la
    frontiere), puis borne chaque valeur a [1 - BORNE, BORNE]."""
    manque = 1 + MARGE_INFORMATIF - (se + sp)
    if manque > 0:
        se, sp = se + manque / 2, sp + manque / 2
    return Capteur(min(BORNE, max(1 - BORNE, se)), min(BORNE, max(1 - BORNE, sp)))


def etape_m(
    chaines: Sequence[Chaine], gammas: Sequence[Sequence[float]], a_priori: Mapping[str, Capteur], force: float
) -> dict[str, Capteur]:
    """Etape M du §7.2 : Se et Sp de chaque capteur calibrable, estimateurs MAP a a priori Beta de force
    `force` centre sur `a_priori`, puis projection dans la zone informative."""
    num_se: dict[str, float] = defaultdict(float)
    den_se: dict[str, float] = defaultdict(float)
    num_sp: dict[str, float] = defaultdict(float)
    den_sp: dict[str, float] = defaultdict(float)
    for chaine, g in zip(chaines, gammas, strict=True):
        for pas, gamma in zip(chaine.pas, g, strict=True):
            if pas.capteur not in CAPTEURS_CALIBRABLES:
                continue
            k, w, x = pas.capteur, pas.poids, pas.valeur
            num_se[k] += w * gamma * x
            den_se[k] += w * gamma
            num_sp[k] += w * (1 - gamma) * (1 - x)
            den_sp[k] += w * (1 - gamma)
    sortie = {}
    for k in CAPTEURS_CALIBRABLES:
        if k not in a_priori:
            continue
        c0 = a_priori[k]
        se = (num_se[k] + force * c0.se) / (den_se[k] + force)
        sp = (num_sp[k] + force * c0.sp) / (den_sp[k] + force)
        sortie[k] = projeter(se, sp)
    return sortie


def em(
    chaines: Sequence[Chaine], a_priori: Mapping[str, Capteur], force: float, parametres: Parametres
) -> tuple[dict[str, Capteur], int, bool]:
    """Alterne E et M jusqu'a stabilite ; renvoie (capteurs, iterations, converge)."""
    courant = dict(a_priori)
    for iteration in range(1, ITERATIONS_MAX + 1):
        gammas = [avant_arriere(c, courant, parametres) for c in chaines]
        suivant = etape_m(chaines, gammas, a_priori, force)
        ecart = max(
            (max(abs(suivant[k].se - courant[k].se), abs(suivant[k].sp - courant[k].sp)) for k in suivant),
            default=0.0,
        )
        courant.update(suivant)
        if ecart < TOLERANCE:
            return courant, iteration, True
    return courant, ITERATIONS_MAX, False


@dataclass(frozen=True)
class ResultatCalibration:
    capteurs: dict[str, Capteur]  # toutes matieres confondues
    par_matiere: dict[str, dict[str, Capteur]]  # a priori = capteurs de l'eleve
    iterations: int
    converge: bool
    epreuves: int

    def vers_dict(self) -> dict[str, object]:
        return {
            "capteurs": {k: [c.se, c.sp] for k, c in self.capteurs.items()},
            "par_matiere": {m: {k: [c.se, c.sp] for k, c in cs.items()} for m, cs in self.par_matiere.items()},
            "iterations": self.iterations,
            "converge": self.converge,
            "epreuves": self.epreuves,
        }

    @classmethod
    def depuis_dict(cls, d: Mapping[str, object]) -> ResultatCalibration:
        brut_capteurs: dict[str, list[float]] = dict(d["capteurs"])  # type: ignore[call-overload]
        brut_matieres: dict[str, dict[str, list[float]]] = dict(d["par_matiere"])  # type: ignore[call-overload]
        return cls(
            capteurs={k: Capteur(*v) for k, v in brut_capteurs.items()},
            par_matiere={m: {k: Capteur(*v) for k, v in cs.items()} for m, cs in brut_matieres.items()},
            iterations=int(d["iterations"]),  # type: ignore[call-overload]
            converge=bool(d["converge"]),
            epreuves=int(d["epreuves"]),  # type: ignore[call-overload]
        )

    def appliquer(self, parametres: Parametres) -> Parametres:
        return parametres.avec_capteurs(self.capteurs, self.par_matiere)


def calibrer(
    observations: Sequence[Observation], epreuves: Sequence[ResultatEpreuve], parametres: Parametres
) -> ResultatCalibration | None:
    """Point d'entree. None tant qu'il y a moins de `epreuves_min` epreuves (on garde les defauts).

    1. chaines rejouees depuis les parametres de depart ; on ne garde que celles qui ont une epreuve ;
    2. EM eleve : a priori = parametres.capteurs, force = parametres.force_a_priori ;
    3. EM par matiere, pour les matieres qui ont elles-memes `epreuves_min` epreuves : a priori = etape 2
       (hierarchie a deux niveaux). Le capteur `epreuve` n'est jamais recale.
    """
    if not parametres.calibration_active or len(epreuves) < parametres.epreuves_min:
        return None
    depart = replace(parametres, capteurs_matiere={})
    chaines = [c for c in construire_chaines(observations, epreuves, depart) if c.a_une_epreuve]
    if not chaines:
        return None
    a_priori = {k: c for k, c in depart.capteurs.items() if k in CAPTEURS_CALIBRABLES}
    capteurs, iterations, converge = em(chaines, a_priori, parametres.force_a_priori, depart)
    par_matiere: dict[str, dict[str, Capteur]] = {}
    epreuves_matiere: dict[str, int] = defaultdict(int)
    for e in epreuves:
        epreuves_matiere[estimateurs.matiere_de(e.notion)] += 1
    for matiere, nombre in sorted(epreuves_matiere.items()):
        siennes = [c for c in chaines if c.matiere == matiere]
        if nombre >= parametres.epreuves_min and siennes:
            par_matiere[matiere], _, _ = em(siennes, capteurs, parametres.force_a_priori, depart)
    return ResultatCalibration(capteurs, par_matiere, iterations, converge, len(epreuves))
