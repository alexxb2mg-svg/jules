"""Tests du modele de l'eleve (docs/MODELE-ELEVE.md).

Deux familles :
  - ce qui est ecrit dans le squelette (primitives, oubli FSRS, parametres, extraction, filtre du
    carnet, mesures) : teste tout de suite, valeurs de reference calculees a la main ;
  - les criteres d'acceptation A1 a A8 (§9) : marques `lot N`, a activer par le lot qui les rend
    possibles. Un lot n'est pas fini tant que ses tests ne passent pas sans marque.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

from jules.apprentissage import carnet, estimateurs, mesures, observations, oubli, parametres
from jules.apprentissage.etat import EtatNotion, EtatSeance, Lecon, Observation, cle_notion
from jules.apprentissage.parametres import FSRS45_DEFAUT, Capteur, ErreurParametres, Parametres

DONNEES = Path(__file__).parent / "cas" / "modele_eleve"
W = FSRS45_DEFAUT


def lot(n: int) -> pytest.MarkDecorator:
    return pytest.mark.skip(reason=f"lot {n} : docs/MODELE-ELEVE.md §12")


# --- primitives bayesiennes (§4) ---------------------------------------------
def test_logit_et_sigmoide_sont_inverses() -> None:
    for p in (0.01, 0.3, 0.5, 0.88, 0.999):
        assert estimateurs.sigmoide(estimateurs.logit(p)) == pytest.approx(p)
    assert estimateurs.sigmoide(-800) == pytest.approx(0.0)  # pas de debordement
    assert estimateurs.sigmoide(800) == pytest.approx(1.0)


def test_delta_log_odds_reproduit_la_table_du_4_1() -> None:
    aide0 = parametres.CAPTEURS_DEFAUT["tentative_aide0"]
    assert math.exp(estimateurs.delta_log_odds(aide0, 1, 1.0)) == pytest.approx(4.25)
    assert math.exp(estimateurs.delta_log_odds(aide0, 0, 1.0)) == pytest.approx(0.1875)
    declaration = parametres.CAPTEURS_DEFAUT["declaration"]
    assert math.exp(estimateurs.delta_log_odds(declaration, 1, 1.0)) == pytest.approx(1.2)


def test_poids_tempere_la_vraisemblance() -> None:
    c = Capteur(0.85, 0.80)
    assert estimateurs.delta_log_odds(c, 1, 0.5) == pytest.approx(0.5 * estimateurs.delta_log_odds(c, 1, 1.0))


def test_bayes_exact_sur_un_cas_calcule_a_la_main() -> None:
    # p = 0,3 ; tentative sans aide juste : P = 0,3*0,85 / (0,3*0,85 + 0,7*0,2) = 0,255 / 0,395
    lo = estimateurs.logit(0.3) + estimateurs.delta_log_odds(Capteur(0.85, 0.80), 1, 1.0)
    assert estimateurs.sigmoide(lo) == pytest.approx(0.255 / 0.395)


def test_decroissance_intra_seance() -> None:
    assert [estimateurs.poids_decroissant(1.0, j, 0.5) for j in (1, 2, 3, 5)] == pytest.approx([1, 2 / 3, 0.5, 1 / 3])


def test_plafond_de_seance() -> None:
    assert estimateurs.plafonner(1.5, 0.0, 2.0) == pytest.approx(1.5)
    assert estimateurs.plafonner(1.5, 1.0, 2.0) == pytest.approx(1.0)
    assert estimateurs.plafonner(1.5, 2.0, 2.0) == pytest.approx(0.0)
    assert estimateurs.plafonner(-3.0, 1.0, 2.0) == pytest.approx(-3.0)
    assert estimateurs.plafonner(-3.0, -1.0, 2.0) == pytest.approx(-1.0)
    assert estimateurs.sigmoide(2.0) == pytest.approx(0.8808, abs=1e-4)  # « de 0,5 a 0,88 » du §4.3


def test_transition_ne_fait_que_monter() -> None:
    assert estimateurs.transition(0.4, 0.1) == pytest.approx(0.46)
    assert estimateurs.transition(1.0, 0.15) == pytest.approx(1.0)


def test_prior_tire_vers_la_matiere() -> None:
    base = estimateurs.logit(0.30)
    assert estimateurs.prior_notion([], 0.30, 5) == pytest.approx(base)
    fort = estimateurs.prior_notion([(estimateurs.logit(0.9), 10.0)], 0.30, 5)
    assert base < fort < estimateurs.logit(0.9)
    assert fort == pytest.approx((5 * base + 10 * estimateurs.logit(0.9)) / 15)


def test_borne_de_certitude() -> None:
    assert estimateurs.borner(40) == estimateurs.LOGIT_MAX
    assert estimateurs.mise_a_jour_bayes(11.9, 0.99, 0.001) == estimateurs.LOGIT_MAX


def test_intervalle_wilson() -> None:
    assert estimateurs.intervalle_wilson(0.5, 0) == (0.0, 1.0)
    bas, haut = estimateurs.intervalle_wilson(0.8, 4)
    bas2, haut2 = estimateurs.intervalle_wilson(0.8, 40)
    assert bas < bas2 < 0.8 < haut2 < haut  # plus de preuves, fourchette plus etroite


# --- oubli FSRS-4.5 (§5), valeurs recalculees depuis le wiki ------------------
def test_retention_vaut_0_9_a_t_egal_s() -> None:
    for s in (0.5, 3.7145, 42.0):
        assert oubli.retention(s, s) == pytest.approx(0.9)
    assert oubli.retention(0, 3) == 1.0
    assert oubli.retention(-2, 3) == 1.0


def test_intervalle_inverse_la_retention() -> None:
    s = 3.7145
    t = oubli.intervalle(0.85, s)
    assert oubli.retention(t, s) == pytest.approx(0.85)
    assert oubli.intervalle(0.9, s) == pytest.approx(s)


def test_stabilites_initiales() -> None:
    assert [oubli.stabilite_initiale(g, W) for g in (1, 2, 3)] == [0.4872, 1.4003, 3.7145]
    with pytest.raises(ValueError):
        oubli.stabilite_initiale(0, W)


def test_difficulte_initiale_et_bornes() -> None:
    assert oubli.difficulte_initiale(3, W) == pytest.approx(5.1618)
    assert oubli.difficulte_initiale(1, W) == pytest.approx(5.1618 + 2 * 1.2298)
    assert oubli.difficulte_suivante(10, 1, W) <= 10
    assert oubli.difficulte_suivante(1, 4, W) >= 1


def test_succes_augmente_la_stabilite_oubli_la_diminue() -> None:
    d, s = 5.0, 3.7145
    r = oubli.retention(4, s)
    apres_succes = oubli.stabilite_apres_succes(d, s, r, 3, W)
    apres_oubli = oubli.stabilite_apres_oubli(d, s, r, W)
    assert apres_succes > s > apres_oubli > 0
    # valeur de reference, calculee a la main depuis la formule du wiki
    attendu = s * (math.exp(W[8]) * (11 - d) * s ** (-W[9]) * (math.exp(W[10] * (1 - r)) - 1) + 1)
    assert apres_succes == pytest.approx(attendu)


def test_effet_d_espacement() -> None:
    """Reviser plus tard (R plus bas) fait gagner plus de stabilite (§5, propriete 3 du wiki)."""
    d, s = 5.0, 3.0
    tot = oubli.stabilite_apres_succes(d, s, oubli.retention(1, s), 3, W)
    tard = oubli.stabilite_apres_succes(d, s, oubli.retention(6, s), 3, W)
    assert tard > tot


def test_note_de_premiere_seance() -> None:
    assert oubli.note_premiere_seance(True, False, 0.8) == 3
    assert oubli.note_premiere_seance(True, False, 0.6) == 2
    assert oubli.note_premiere_seance(False, True, 0.9) == 2
    assert oubli.note_premiere_seance(False, False, 0.9) == 1


def test_prediction_d_epreuve() -> None:
    # notion comprise, rien oublie : ne tient pas seulement par inattention
    assert oubli.proba_epreuve(1.0, 1.0, 0.05, 0.10) == pytest.approx(0.95)
    # jamais comprise : on ne reussit que par chance
    assert oubli.proba_epreuve(0.0, 0.3, 0.05, 0.10) == pytest.approx(0.10)
    # un echec du a l'oubli pese moins qu'un echec avec une memoire fraiche
    frais = oubli.vraisemblances_epreuve(0.95, 0.05, 0.10)
    oublie = oubli.vraisemblances_epreuve(0.4, 0.05, 0.10)
    rapport_echec_frais = (1 - frais[0]) / (1 - frais[1])
    rapport_echec_oublie = (1 - oublie[0]) / (1 - oublie[1])
    assert rapport_echec_frais < rapport_echec_oublie < 1


# --- parametres (§10) ----------------------------------------------------------
def test_parametres_par_defaut_et_config_yaml_concordent() -> None:
    config = yaml.safe_load((Path(__file__).parents[1] / "config.yaml").read_text(encoding="utf-8"))
    ref = next(m for m in config["modules"] if m["id"] == "modele_eleve")
    assert ref["actif"] is False  # squelette : jamais actif par defaut
    assert parametres.depuis_reglages(ref["reglages"]) == Parametres()


@pytest.mark.parametrize(
    ("reglages", "message"),
    [
        ({"capteurs": {"jugement_ia": {"se": 0.5, "sp": 0.4}}}, "se + sp"),
        ({"capteurs": {"inconnu": {"se": 0.9, "sp": 0.9}}}, "inconnu"),
        ({"capteurs": {"declaration": {"se": 1.2}}}, "]0, 1["),
        ({"politique": {"fragile_entree": 0.7, "fragile_sortie": 0.6}}, "hysteresis"),
        ({"politique": {"fragile_sortie": 0.9, "facile_sortie": 0.85, "facile_entree": 0.95}}, "chevauchent"),
        ({"politique": {"seuil_magique": 1}}, "inconnus"),
        ({"oubli": {"glissement_epreuve": 0.5, "chance_epreuve": 0.6}}, "< 1"),
        ({"prior": {"force": 0}}, "> 0"),
    ],
)
def test_configuration_absurde_refusee(reglages: dict, message: str) -> None:
    with pytest.raises(ErreurParametres, match=message.replace("[", r"\[").replace("]", r"\]").replace("+", r"\+")):
        parametres.depuis_reglages(reglages)


# --- observations (§3) -----------------------------------------------------------
def test_extraction_normalise_et_rejette_le_bruit() -> None:
    brut = """```json
    {"tentatives": [
      {"matiere": "Mathématiques", "notion": "fractions : addition", "tentative": true, "resultat": "juste",
       "aide": 7, "affect": "furieux", "certitude": "haute"},
      {"notion": "", "tentative": true, "resultat": "faux"},
      "pas un objet"
    ]}```"""
    t = observations.lire_extraction(brut)
    assert len(t) == 1
    assert t[0]["aide"] == 3 and t[0]["affect"] == "neutre" and t[0]["resultat"] == "juste"
    assert observations.lire_extraction("désolé, je ne peux pas") == []


def test_pas_de_tentative_sans_resultat() -> None:
    t = observations.normaliser_tentative({"notion": "COD", "tentative": False, "resultat": "juste"})
    assert t is not None and t["resultat"] == "sans_objet" and t["tentative"] is False


def test_vers_observations() -> None:
    p = Parametres()
    tentative = observations.normaliser_tentative(
        {"matiere": "Mathématiques", "notion": "équations", "tentative": True, "resultat": "partiel",
         "aide": 2, "auto_correction": True, "declare_compris": True, "certitude": "moyenne"}
    )  # fmt: skip
    assert tentative is not None
    obs = observations.vers_observations(tentative, "conv1", "2026-09-24T10:00:00+02:00", p)
    capteurs = {o.capteur: o for o in obs}
    assert set(capteurs) == {"tentative_aide2", "auto_correction", "declaration"}
    assert capteurs["tentative_aide2"].valeur == 1
    assert capteurs["tentative_aide2"].poids == pytest.approx(0.7 * 0.5)  # certitude moyenne x partiel
    assert capteurs["tentative_aide2"].partiel is True
    assert capteurs["tentative_aide2"].notion == cle_notion("Mathématiques", "équations")


def test_statut_du_suivi_devient_jugement_ia() -> None:
    o = observations.depuis_statut_suivi({"matiere": "SVT", "notion": "cellule", "statut": "compris"}, "c", "h")
    assert o is not None and o.capteur == "jugement_ia" and o.valeur == 1
    assert observations.depuis_statut_suivi({"notion": "x", "statut": "en_cours"}, "c", "h") is None
    assert observations.depuis_statut_suivi({"notion": "x", "statut": "acquis"}, "c", "h") is None  # epreuve : a part


def test_banc_d_essai_bien_forme() -> None:
    banc = yaml.safe_load((DONNEES / "echanges_annotes.yaml").read_text(encoding="utf-8"))
    ids = [e["id"] for e in banc["echanges"]]
    assert len(ids) == len(set(ids)) >= 15
    for e in banc["echanges"]:
        assert e["messages"][-1]["role"] == "eleve"
        for a in e["attendu"]:
            assert a.get("resultat", "sans_objet") in observations.RESULTATS
            assert a.get("affect", "neutre") in observations.AFFECTS
            assert 0 <= a.get("aide", 0) <= 3


# --- serialisation (§11) -----------------------------------------------------------
def test_aller_retour_json() -> None:
    etat = EtatNotion("Maths : x", 0.4, n_eff=2.5, rangs_seance={"tentative_aide0": 2})
    assert EtatNotion.depuis_dict(etat.vers_dict()) == etat
    assert EtatNotion.depuis_dict({**etat.vers_dict(), "champ_futur": 1}) == etat  # tolere les ajouts
    seance = EtatSeance("c1", historique_credits=[1.0, 0.5])
    assert EtatSeance.depuis_dict(seance.vers_dict()) == seance


# --- carnet : filtre (§8.2, critere A7) -------------------------------------------
FILTRE = yaml.safe_load((DONNEES / "lecons_filtre.yaml").read_text(encoding="utf-8"))


def _lecon(texte: str, **k: str) -> Lecon:
    return Lecon(id="t", portee=k.get("portee", "matiere"), cle="Mathématiques", sens="surestimation",  # type: ignore[arg-type]
                 texte=texte, creee="2026-09-24")  # fmt: skip


@pytest.mark.parametrize("cas", FILTRE["refusees"], ids=lambda c: c["motif"] + ":" + c["texte"][:30])
def test_a7_le_filtre_refuse(cas: dict) -> None:
    assert carnet.motif_refus(_lecon(cas["texte"]), []) is not None


@pytest.mark.parametrize("texte", FILTRE["acceptees"])
def test_le_filtre_laisse_passer_les_bonnes_lecons(texte: str) -> None:
    assert carnet.motif_refus(_lecon(texte), []) is None


def test_le_filtre_refuse_les_doublons() -> None:
    a = _lecon("En géométrie, faire refaire une figure seule avant de conclure qu'elle est comprise.")
    b = _lecon("En géométrie, faire refaire la figure seule avant de conclure qu'elle est comprise.")
    assert "double" in (carnet.motif_refus(b, [a]) or "")
    assert carnet.motif_refus(b, [Lecon(**{**a.vers_dict(), "statut": "retiree"})]) is None


# --- politique : textes et reglages (§6.3) ---------------------------------------------
def test_politique_couvre_chaque_etat_sans_chiffre() -> None:
    import re

    from jules.apprentissage import politique
    from jules.apprentissage.etat import ETATS_POLITIQUE
    from jules.modules.modele_eleve import charger_textes_politique

    textes = charger_textes_politique()
    assert set(textes["etats"]) == set(ETATS_POLITIQUE) == set(politique.REGLAGES)
    for etat in ETATS_POLITIQUE:
        assert not re.search(r"\d", textes["etats"][etat]["texte"]), f"chiffre dans le texte de {etat}"
    for r in politique.REGLAGES.values():
        assert 0 <= r.etayage <= 3 and r.difficulte in (-1, 0, 1)


def test_credit_et_moyenne_mobile() -> None:
    from jules.apprentissage import politique

    base = {"notion": "n", "seance": "s", "horodatage": "h"}
    assert politique.credit(Observation(capteur="tentative_aide0", valeur=1, poids=1.0, **base)) == 1.0
    assert (
        politique.credit(Observation(capteur="tentative_aide2", valeur=1, poids=0.5, aide=2, partiel=True, **base))
        == 0.25
    )
    assert politique.credit(Observation(capteur="tentative_aide1", valeur=0, poids=1.0, aide=1, **base)) == 0.0
    assert politique.credit(Observation(capteur="declaration", valeur=1, poids=1.0, **base)) is None
    assert politique.ema(None, 0.8, 0.4) == 0.8
    assert politique.ema(1.0, 0.0, 0.4) == pytest.approx(0.6)


# --- mesures (§7.4) ------------------------------------------------------------------
def test_brier_et_perte_log() -> None:
    assert mesures.brier([0.5, 0.5], [0, 1]) == pytest.approx(0.25)
    assert mesures.brier([1.0, 0.0], [1, 0]) == 0
    assert mesures.perte_log(0.25, 1) == pytest.approx(math.log(4))  # seuil de surprise du §8.1
    assert mesures.perte_log(1.0, 0) < 30  # pas d'infini


def test_competence_contre_la_climatologie() -> None:
    y = [1, 1, 1, 0]
    ref = mesures.brier_climatologie(y)
    assert ref == pytest.approx(0.1875)
    assert mesures.competence(mesures.brier([0.75] * 4, y), ref) == pytest.approx(0.0)
    assert mesures.competence(mesures.brier([0.9, 0.9, 0.9, 0.1], y), ref) > 0


def test_table_de_fiabilite_et_ece() -> None:
    preds = [0.1, 0.15, 0.85, 0.9, 0.95]
    y = [0, 0, 1, 1, 0]
    table = mesures.table_fiabilite(preds, y)
    assert [c.effectif for c in table] == [2, 3]
    assert table[1].frequence_observee == pytest.approx(2 / 3)
    assert mesures.ece([0.8] * 5, [1, 1, 1, 1, 0]) == pytest.approx(0.0)


def test_mesures_refusent_les_entrees_invalides() -> None:
    with pytest.raises(ValueError):
        mesures.brier([0.5], [2])
    with pytest.raises(ValueError):
        mesures.brier([1.5], [1])


# --- criteres d'acceptation (§9), a activer par les lots -----------------------------
@lot(2)
def test_estimateur_bkt_ordre_des_operations() -> None:
    """Un cas deroule a la main : prior, trois tentatives, plafond, transition."""
    e = estimateurs.creer("bkt", Parametres())
    obs = Observation("Maths : x", "tentative_aide0", 1, 1.0, "s1", "2026-09-24T10:00:00+02:00")
    etat = e.observer(None, obs, {})
    assert etat.n_eff == pytest.approx(1.0)


@lot(3)
def test_a1_a2_a3_le_modele_predit_mieux_que_l_ancienne_regle() -> None: ...


@lot(4)
def test_a4_la_calibration_corrige_un_juge_biaise() -> None: ...


@lot(4)
def test_a5_la_calibration_ne_degrade_pas_un_juge_honnete() -> None: ...


@lot(5)
def test_a6_la_politique_n_oscille_pas() -> None: ...


@lot(7)
def test_a8_mise_a_jour_en_moins_de_5_ms() -> None: ...
