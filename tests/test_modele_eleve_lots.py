"""Tests unitaires des lots 2 a 7 du modele de l'eleve (docs/MODELE-ELEVE.md, §12).

Valeurs de reference calculees a la main a partir des formules du document. Les criteres
d'acceptation statistiques (A1 a A8, simulateur) sont dans test_modele_eleve_acceptation.py.
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from jules.apprentissage import calibration, carnet, estimateurs, mesures, oubli, politique, simulateur
from jules.apprentissage.etat import EtatNotion, EtatSeance, Lecon, Observation, ResultatEpreuve
from jules.apprentissage.parametres import Capteur, Parametres

PAR = Parametres()
N = "Mathématiques : fractions"
T0 = datetime.fromisoformat("2026-09-24T17:00:00+02:00")


def h(minutes: float = 0, jours: float = 0) -> str:
    return (T0 + timedelta(minutes=minutes, days=jours)).isoformat()


def obs(capteur: str, valeur: int, seance: str = "s1", minutes: float = 0, jours: float = 0, **k) -> Observation:
    aide = int(capteur[-1]) if capteur.startswith("tentative_aide") else 0
    return Observation(N, capteur, valeur, k.pop("poids", 1.0), seance, h(minutes, jours), aide=aide, **k)


# --- lot 2 : estimateur BKT ---------------------------------------------------------------
def test_premiere_observation_prior_bayes_transition() -> None:
    """Prior 0,30 ; juste sans aide : Bayes (0,255 / 0,395) puis transition T0 = 0,10."""
    e = estimateurs.EstimateurBKT(PAR)
    etat = e.observer(None, obs("tentative_aide0", 1), {})
    apres_bayes = 0.255 / 0.395
    attendu = apres_bayes + (1 - apres_bayes) * PAR.apprentissage[0]
    assert estimateurs.p_de(etat) == pytest.approx(attendu)
    assert etat.n_eff == pytest.approx(1.0)
    assert etat.reussite_sans_aide_seance and not etat.reussite_avec_aide_seance
    assert etat.stabilite is None  # la seance n'est pas close


def test_repetition_dans_la_seance_pese_de_moins_en_moins() -> None:
    e = estimateurs.EstimateurBKT(PAR)
    etat = e.observer(None, obs("declaration", 1), {})
    lo1 = etat.log_odds
    etat = e.observer(etat, obs("declaration", 1, minutes=1), {})
    gain2 = etat.log_odds - lo1
    gain1 = lo1 - estimateurs.logit(PAR.prior_global)
    assert gain2 == pytest.approx(gain1 * 2 / 3)  # rang 2 : poids 1 / (1 + 0,5)
    assert etat.n_eff == pytest.approx(1 + 2 / 3)


def test_plafond_de_seance_puis_remise_a_zero() -> None:
    e = estimateurs.EstimateurBKT(PAR)
    etat = None
    for i in range(12):
        etat = e.observer(etat, obs("explication", 1, minutes=i), {})
    assert etat is not None
    assert etat.delta_seance == pytest.approx(PAR.plafond_seance)
    # nouvelle seance : le plafond repart de zero
    etat = e.observer(etat, obs("explication", 1, seance="s2", jours=1), {})
    assert 0 < etat.delta_seance <= PAR.plafond_seance


def test_le_plafond_ne_bride_pas_une_chute() -> None:
    """Le plafond borne le cumul de la seance dans les deux sens : une serie d'echecs apres une serie de
    reussites fait redescendre, sans jamais depasser -plafond."""
    e = estimateurs.EstimateurBKT(PAR)
    etat = None
    for i in range(6):
        etat = e.observer(etat, obs("tentative_aide0", 0, minutes=i), {})
    assert etat is not None and etat.delta_seance == pytest.approx(-PAR.plafond_seance)


def test_prior_d_une_notion_nouvelle_tire_vers_la_matiere() -> None:
    e = estimateurs.EstimateurBKT(PAR)
    forte = EtatNotion("Mathématiques : Thalès", estimateurs.logit(0.9), n_eff=10)
    autre = EtatNotion("Français : accords", estimateurs.logit(0.05), n_eff=50)
    etat = e.observer(None, obs("declaration", 1), {forte.notion: forte, autre.notion: autre})
    sans = e.observer(None, obs("declaration", 1), {})
    assert etat.log_odds > sans.log_odds  # Thales compte, pas le francais


def test_clore_seance_premiere_note_et_idempotence() -> None:
    e = estimateurs.EstimateurBKT(PAR)
    etat = e.observer(None, obs("tentative_aide2", 1), {})
    close = e.clore_seance(etat, h(5))
    assert close.stabilite == pytest.approx(PAR.fsrs[1])  # hard : reussite avec aide seulement
    assert close.difficulte == pytest.approx(oubli.difficulte_initiale(2, PAR.fsrs))
    assert e.clore_seance(close, h(10)) == close


def test_oubli_applique_au_debut_de_la_seance_suivante() -> None:
    e = estimateurs.EstimateurBKT(PAR)
    etat = e.clore_seance(e.observer(None, obs("tentative_aide0", 1), {}), h(1))
    p_fin = estimateurs.p_de(etat)
    r = oubli.retention(oubli.jours_entre(h(1), h(jours=10)), etat.stabilite or 0)
    suivant = e.observer(etat, obs("declaration", 1, seance="s2", jours=10), {})
    # oubli p <- p R, puis la declaration (Se 0,90, Sp 0,25) : rapport de vraisemblance 1,2
    attendu = estimateurs.sigmoide(estimateurs.logit(p_fin * r) + math.log(1.2))
    assert estimateurs.p_de(suivant) == pytest.approx(attendu)
    assert suivant.retention_seance == pytest.approx(r)


def test_prediction_et_lecture_d_epreuve() -> None:
    e = estimateurs.EstimateurBKT(PAR)
    etat = e.clore_seance(e.observer(None, obs("tentative_aide0", 1), {}), h(1))
    pred = e.predire_epreuve(etat, h(jours=5), "ep1")
    r = oubli.retention(oubli.jours_entre(h(1), h(jours=5)), etat.stabilite or 0)
    assert pred.retention == pytest.approx(r)
    assert pred.pi == pytest.approx(oubli.proba_epreuve(pred.p, r, 0.05, 0.10))
    tenu = e.lire_epreuve(etat, True, h(jours=5))
    rate = e.lire_epreuve(etat, False, h(jours=5))
    assert estimateurs.p_de(rate) < estimateurs.p_de(etat) < estimateurs.p_de(tenu)
    assert (tenu.stabilite or 0) > (etat.stabilite or 0) > (rate.stabilite or 0)
    assert tenu.derniere_revision == h(jours=5)


def test_a_reviser_prend_les_plus_exposees() -> None:
    e = estimateurs.EstimateurBKT(PAR)
    a = e.clore_seance(e.observer(None, obs("tentative_aide0", 1), {}), h(1))
    b = replace(a, notion="Mathématiques : Thalès", stabilite=30.0)
    choix = estimateurs.a_reviser([a, b], h(jours=6), 0.85, 3)
    assert [c.notion for c in choix] == [N]  # Thales (S = 30 j) tient encore
    assert estimateurs.a_reviser([a, b], h(jours=200), 0.85, 1)[0].notion == N


def test_estimateur_de_reference() -> None:
    e = estimateurs.EstimateurDernierStatut(PAR)
    etat = e.observer(None, obs("jugement_ia", 1), {})
    assert estimateurs.p_de(etat) == pytest.approx(0.8)
    assert e.predire_epreuve(etat, h(jours=50), "x").pi == pytest.approx(0.8)  # aucun oubli


def test_l_epreuve_ne_passe_pas_par_observer() -> None:
    with pytest.raises(ValueError):
        estimateurs.EstimateurBKT(PAR).observer(None, obs("epreuve", 1), {})


# --- lot 3 : simulateur --------------------------------------------------------------------
def test_simulateur_deterministe_et_coherent() -> None:
    sc = simulateur.Scenario(eleves=3, jours=30)
    a, b = simulateur.simuler(sc), simulateur.simuler(sc)
    assert [len(t.observations) for t in a] == [len(t.observations) for t in b]
    assert [t.epreuves for t in a] == [t.epreuves for t in b]
    for trace in a:
        assert trace.observations and all(o.capteur != "epreuve" for o in trace.observations)
        horodatages = [o.horodatage for o in trace.observations]
        assert horodatages == sorted(horodatages)
        assert {e.notion for e in trace.epreuves} <= {o.notion for o in trace.observations}


def test_juge_biaise_dit_compris_a_tort() -> None:
    import random

    honnete = simulateur.tirer_profil(random.Random(1), 0.0)  # noqa: S311
    biaise = simulateur.tirer_profil(random.Random(1), 0.4)  # noqa: S311
    assert biaise.capteurs["jugement_ia"].sp == pytest.approx(honnete.capteurs["jugement_ia"].sp - 0.4, abs=1e-9)


# --- lot 4 : calibration ---------------------------------------------------------------------
def test_avant_arriere_sur_une_chaine_a_un_pas() -> None:
    """Une seule observation : gamma = posterior de Bayes, calculable a la main."""
    chaine = calibration.Chaine(N, "Mathématiques", 0.3, [calibration.Pas("tentative_aide0", 1, 1.0, 0.0)])
    g = calibration.avant_arriere(chaine, PAR.capteurs, PAR)
    assert g == pytest.approx([0.255 / 0.395])


def test_avant_arriere_l_epreuve_informe_le_passe() -> None:
    pas = [calibration.Pas("jugement_ia", 1, 1.0, 0.0), calibration.Pas("epreuve", 0, 1.0, 0.0, 0.95)]
    chaine = calibration.Chaine(N, "Mathématiques", 0.3, pas)
    seul = calibration.avant_arriere(calibration.Chaine(N, "Mathématiques", 0.3, pas[:1]), PAR.capteurs, PAR)
    avec = calibration.avant_arriere(chaine, PAR.capteurs, PAR)
    assert avec[0] < seul[0]  # une epreuve ratee rend moins probable que « compris » etait vrai


def test_projection_dans_la_zone_informative() -> None:
    c = calibration.projeter(0.5, 0.4)
    assert c.se + c.sp == pytest.approx(1 + calibration.MARGE_INFORMATIF)
    assert calibration.projeter(0.9, 0.8) == Capteur(0.9, 0.8)


def test_calibrer_attend_assez_d_epreuves() -> None:
    o = [obs("jugement_ia", 1)]
    epreuves = [ResultatEpreuve(N, h(jours=3), True, "e")] * (PAR.epreuves_min - 1)
    assert calibration.calibrer(o, epreuves, PAR) is None


def test_calibration_aller_retour_et_application() -> None:
    traces = simulateur.simuler(simulateur.Scenario(eleves=1, jours=90, biais_juge=0.4))
    r = calibration.calibrer(traces[0].observations, traces[0].epreuves, PAR)
    assert r is not None and "epreuve" not in r.capteurs
    assert calibration.ResultatCalibration.depuis_dict(r.vers_dict()) == r
    appliques = r.appliquer(PAR)
    assert appliques.capteurs["jugement_ia"] == r.capteurs["jugement_ia"]
    # la direction de la correction se juge sur une population (A4), pas sur un seul eleve : avec
    # quelques dizaines de jugements, un eleve isole peut rester loin de la verite (voir §9)


# --- lot 5 : politique ------------------------------------------------------------------------
POL = PAR.politique


def avancer_serie(valeurs: list[tuple[str, int]], notion: EtatNotion | None = None) -> EtatSeance:
    s = EtatSeance("s1")
    notion = notion or EtatNotion(N, 0.0, n_eff=10)
    for i, (capteur, v) in enumerate(valeurs):
        s = politique.avancer(s, obs(capteur, v, minutes=i), notion, POL, h(i))
    return s


def test_decouverte_tant_que_peu_de_preuves() -> None:
    s = avancer_serie([("tentative_aide0", 1)] * 3, EtatNotion(N, 0.0, n_eff=1))
    assert s.etat == "decouverte"


def test_fragile_puis_hysteresis() -> None:
    s = avancer_serie([("tentative_aide0", 0)] * 2 + [("tentative_aide0", 1)] + [("tentative_aide0", 0)])
    assert s.etat == "fragile"
    # une reussite isolee ne fait pas sortir : la reussite remonte sous le seuil de sortie
    s2 = politique.avancer(s, obs("tentative_aide0", 1, minutes=5), EtatNotion(N, 0.0, n_eff=10), POL, h(5))
    assert (s2.reussite or 0) < POL.fragile_sortie and s2.etat == "fragile"


def test_trop_facile_exige_des_reussites_sans_aide() -> None:
    s = avancer_serie([("tentative_aide0", 1)] * 6, EtatNotion(N, 3.0, n_eff=10))
    assert s.etat == "trop_facile"
    aide = avancer_serie([("tentative_aide2", 1)] * 6, EtatNotion(N, 3.0, n_eff=10))
    assert aide.etat != "trop_facile"


def test_frustration_immediate() -> None:
    s = EtatSeance("s1", etat="zone_cible", reussite=0.7, dernier_message=h(-1))
    s = politique.avancer(s, obs("tentative_aide1", 0, affect="frustre"), EtatNotion(N, 0.0, n_eff=10), POL, h())
    assert s.etat == "frustration"
    hesite = EtatSeance("s1", etat="zone_cible", reussite=0.7, dernier_message=h(-1))
    hesite = politique.avancer(
        hesite, obs("tentative_aide1", 0, affect="hesitant"), EtatNotion(N, 0, n_eff=10), POL, h()
    )
    assert hesite.etat != "frustration"  # une hesitation seule ne suffit pas


def test_fatigue_apres_longue_seance_en_baisse() -> None:
    s = EtatSeance("s1", etat="zone_cible", reussite=0.7, minutes=45, historique_credits=[1, 1, 0.75, 0.5])
    s = politique.avancer(s, obs("tentative_aide1", 0), EtatNotion(N, 0.0, n_eff=10), POL, h())
    s = politique.avancer(s, obs("tentative_aide1", 0, minutes=1), EtatNotion(N, 0.0, n_eff=10), POL, h(1))
    assert s.etat == "fatigue"


def test_avancer_est_pure() -> None:
    s = EtatSeance("s1", historique_credits=[0.5])
    politique.avancer(s, obs("tentative_aide0", 1), None, POL, h())
    assert s.historique_credits == [0.5] and s.reussite is None


def test_les_pauses_ne_comptent_pas_dans_la_duree() -> None:
    s = avancer_serie([("tentative_aide0", 1)] * 2)
    assert s.minutes == pytest.approx(1)
    s = politique.avancer(s, obs("tentative_aide0", 1, minutes=60), EtatNotion(N, 0, n_eff=10), POL, h(60))
    assert s.minutes == pytest.approx(1)


# --- lot 6 : carnet ------------------------------------------------------------------------------
def lecon(texte: str = "En géométrie, faire refaire une figure seule avant de conclure.", **k) -> Lecon:
    base = {"id": "l1", "portee": "matiere", "cle": "Mathématiques", "sens": "surestimation", "texte": texte,
            "creee": h(), "pertes_avant": [2.0]}  # fmt: skip
    base.update(k)
    return Lecon(**base)  # type: ignore[arg-type]


def test_portee_des_lecons() -> None:
    assert carnet.dans_la_portee(lecon(), N)
    assert not carnet.dans_la_portee(lecon(), "Français : accords")
    assert carnet.dans_la_portee(lecon(portee="global", cle=""), "Français : accords")
    assert not carnet.dans_la_portee(lecon(portee="notion", cle="Mathématiques : Thalès"), N)


def test_une_epreuve_ne_prouve_pas_la_lecon_qu_elle_a_declenchee() -> None:
    lecons = carnet.enregistrer_epreuve([lecon()], N, 0.3, h())
    assert lecons[0].pertes_apres == []
    lecons = carnet.enregistrer_epreuve(lecons, N, 0.3, h(jours=2))
    assert lecons[0].pertes_apres == [0.3] and lecons[0].derniere_epreuve == h(jours=2)


def test_confirmation_retrait_expiration() -> None:
    maintenant = T0 + timedelta(days=10)
    assert carnet.evaluer(lecon(pertes_apres=[0.5, 0.4]), maintenant).statut == "active"
    assert carnet.evaluer(lecon(pertes_apres=[0.5, 0.4, 0.6]), maintenant).statut == "confirmee"
    pire = carnet.evaluer(lecon(pertes_apres=[2.5] * 5), maintenant)
    assert pire.statut == "retiree" and pire.motif_retrait == "n'a pas aide"
    vieille = carnet.evaluer(lecon(), T0 + timedelta(days=46))
    assert vieille.statut == "retiree" and vieille.motif_retrait == "expiree"


def test_budget_retire_d_abord_les_non_confirmees_anciennes() -> None:
    lecons = [
        lecon(id="a", creee=h(jours=0)),
        lecon(id="b", creee=h(jours=1), statut="confirmee"),
        lecon(id="c", creee=h(jours=2)),
    ]
    garde = {x.id: x.statut for x in carnet.elaguer(lecons, 2)}
    assert garde == {"a": "retiree", "b": "confirmee", "c": "active"}


def test_lecons_pour_le_prompt() -> None:
    lecons = [
        lecon(id="a", creee=h(jours=0)),
        lecon(id="b", creee=h(jours=1), statut="confirmee"),
        lecon(id="c", creee=h(jours=2), portee="matiere", cle="Français"),
        lecon(id="d", creee=h(jours=3), portee="global", cle=""),
        lecon(id="e", creee=h(jours=4), statut="retiree"),
    ]
    choisies = carnet.pour_le_prompt(lecons, "Mathématiques", N, 5)
    assert [x.id for x in choisies] == ["b", "d", "a"]  # confirmee d'abord, puis la plus recente
    assert len(carnet.pour_le_prompt(lecons, "Mathématiques", N, 1)) == 1


# --- mesures sur les predictions de la brique ----------------------------------------------------
def test_perte_de_la_surprise() -> None:
    assert mesures.perte_log(0.25, 0) < PAR.seuil_surprise < mesures.perte_log(0.2, 1)
