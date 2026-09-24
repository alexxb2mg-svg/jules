"""Criteres d'acceptation A1 a A8 du modele de l'eleve (docs/MODELE-ELEVE.md, §9).

Tout passe par le simulateur d'eleves virtuels, a graine fixee : ces tests sont deterministes. Ils
sont plus longs que les autres (quelques dizaines de secondes en tout) ; les tailles de population
sont reduites par rapport au §9 pour la CI, les mesures en pleine taille sont dans le document.
"""

from __future__ import annotations

import statistics
import time
from dataclasses import replace

import pytest

from jules.apprentissage import calibration, estimateurs, mesures, politique, simulateur
from jules.apprentissage.etat import EtatNotion, EtatSeance
from jules.apprentissage.parametres import Parametres

PAR = Parametres()


def evaluer(traces: list[simulateur.Trace], nom: str, recalibrer: int = 0) -> tuple[list[float], list[int]]:
    pis: list[float] = []
    ys: list[int] = []
    for trace in traces:
        for prediction, tenu in simulateur.rejouer(trace, nom, PAR, recalibrer_tous=recalibrer):
            pis.append(prediction.pi)
            ys.append(int(tenu))
    return pis, ys


@pytest.fixture(scope="module")
def population() -> list[simulateur.Trace]:
    return simulateur.simuler(simulateur.Scenario(eleves=60))


def test_a1_a2_a3_le_modele_predit_mieux_que_l_ancienne_regle(population: list[simulateur.Trace]) -> None:
    pis, ys = evaluer(population, "bkt")
    ref_pis, ref_ys = evaluer(population, "dernier_statut")
    assert len(ys) > 1000
    b, b_ref = mesures.brier(pis, ys), mesures.brier(ref_pis, ref_ys)
    assert b_ref - b >= 0.03, (b, b_ref)  # A1
    assert mesures.competence(b, mesures.brier_climatologie(ys)) > 0.10  # A2
    assert mesures.ece(pis, ys) < 0.08  # A3


def test_a4_la_calibration_corrige_un_juge_biaise() -> None:
    """Juge biaise (dit « compris » a tort 40 points plus souvent) : sur un trimestre de donnees, la
    calibration ramene l'erreur sur Sp(jugement_ia) de 0,38 (valeur par defaut) a moins de 0,10 en
    mediane. Seuil §9 revu apres mesure (voir le document) : 60 jours ne suffisent pas pour un seul
    eleve, et c'est ce que le parent doit savoir."""
    traces = simulateur.simuler(simulateur.Scenario(eleves=16, jours=180, biais_juge=0.4, graine=7))
    ecarts, ecarts_defaut = [], []
    for trace in traces:
        r = calibration.calibrer(trace.observations, trace.epreuves, PAR)
        assert r is not None
        vrai = trace.profil.capteurs["jugement_ia"].sp
        ecarts.append(abs(r.capteurs["jugement_ia"].sp - vrai))
        ecarts_defaut.append(abs(PAR.capteurs["jugement_ia"].sp - vrai))
    assert statistics.median(ecarts) < 0.10
    assert statistics.median(ecarts) < statistics.median(ecarts_defaut) / 3
    assert sum(e <= 0.15 for e in ecarts) / len(ecarts) >= 0.6


def test_a5_la_calibration_ne_degrade_pas_un_juge_honnete() -> None:
    traces = simulateur.simuler(simulateur.Scenario(eleves=12, biais_juge=0.0, graine=11))
    sans = mesures.brier(*evaluer(traces, "bkt"))
    avec = mesures.brier(*evaluer(traces, "bkt", recalibrer=8))
    assert avec - sans <= 0.005, (sans, avec)


def test_a5_bis_la_calibration_ameliore_un_juge_biaise() -> None:
    traces = simulateur.simuler(simulateur.Scenario(eleves=12, biais_juge=0.4, jours=120, graine=13))
    sans = mesures.brier(*evaluer(traces, "bkt"))
    avec = mesures.brier(*evaluer(traces, "bkt", recalibrer=8))
    assert avec <= sans, (sans, avec)


def test_a6_la_politique_n_oscille_pas(population: list[simulateur.Trace]) -> None:
    changements = messages = allers_retours = 0
    for trace in population[:30]:
        e = estimateurs.EstimateurBKT(PAR)
        notions: dict[str, EtatNotion] = {}
        for seance in trace.seances:
            s = EtatSeance(seance[0].seance)
            historique = [s.etat]
            for o in seance:
                notions[o.notion] = e.observer(notions.get(o.notion), o, notions)
                suivant = politique.avancer(s, o, notions[o.notion], PAR.politique, o.horodatage)
                changements += suivant.etat != s.etat
                messages += 1
                s = suivant
                historique.append(s.etat)
            allers_retours += sum(
                1 for i in range(2, len(historique)) if historique[i] == historique[i - 2] != historique[i - 1]
            )
            notions[seance[0].notion] = e.clore_seance(notions[seance[0].notion], seance[-1].horodatage)
    assert 4 * changements / messages <= 1.0
    assert allers_retours / messages < 0.02  # A-B-A en deux messages : l'anti-oscillation l'interdit presque


def test_a8_mise_a_jour_en_moins_de_5_ms(population: list[simulateur.Trace]) -> None:
    """Estimateur + politique pour une observation, sur un etat deja charge (hors IA et stockage)."""
    trace = population[0]
    e = estimateurs.EstimateurBKT(PAR)
    notions: dict[str, EtatNotion] = {}
    s = EtatSeance("x")
    debut = time.perf_counter()
    for o in trace.observations:
        notions[o.notion] = e.observer(notions.get(o.notion), o, notions)
        s = politique.avancer(replace(s, seance=o.seance), o, notions[o.notion], PAR.politique, o.horodatage)
    moyenne_ms = (time.perf_counter() - debut) * 1000 / len(trace.observations)
    assert moyenne_ms < 5, moyenne_ms
