"""Tests du module `jules.revisions` (repetition espacee, docs/STUDIO-CONTRAT.md §4)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from jules.revisions import (
    ETATS_CARTE,
    PALIERS_JOURS,
    cartes_dues,
    prochaine_revision,
    reinitialiser,
)


def carte(**kwargs):
    base = {
        "id": "c1",
        "recto": "recto",
        "verso": "verso",
        "etat": "nouvelle",
        "prochaine_revision": None,
        "palier": 0,
    }
    base.update(kwargs)
    return base


# --- reponse "rate" ----------------------------------------------------------------------


def test_rate_remet_a_zero_et_reprogramme_demain():
    depart = carte(etat="apprentissage", palier=3, prochaine_revision="2024-06-01")
    resultat = prochaine_revision(depart, "rate", date(2024, 6, 10))
    assert resultat["palier"] == 0
    assert resultat["etat"] == "apprentissage"
    assert resultat["prochaine_revision"] == "2024-06-11"


def test_rate_depuis_une_carte_acquise_repart_de_zero():
    depart = carte(etat="acquise", palier=len(PALIERS_JOURS) - 1, prochaine_revision="2024-06-01")
    resultat = prochaine_revision(depart, "rate", date(2024, 6, 10))
    assert resultat["palier"] == 0
    assert resultat["etat"] == "apprentissage"


# --- reponse "difficile" ------------------------------------------------------------------


def test_difficile_garde_le_palier_et_reprogramme_au_meme_delai():
    depart = carte(etat="apprentissage", palier=2, prochaine_revision="2024-06-01")
    resultat = prochaine_revision(depart, "difficile", date(2024, 6, 10))
    assert resultat["palier"] == 2
    assert resultat["etat"] == "apprentissage"
    # delai du palier 2 == PALIERS_JOURS[2] == 7 jours
    assert resultat["prochaine_revision"] == "2024-06-17"


def test_difficile_sur_carte_acquise_reste_au_dernier_palier():
    dernier = len(PALIERS_JOURS) - 1
    depart = carte(etat="acquise", palier=dernier, prochaine_revision="2024-06-01")
    resultat = prochaine_revision(depart, "difficile", date(2024, 6, 10))
    assert resultat["palier"] == dernier
    assert resultat["etat"] == "apprentissage"
    assert resultat["prochaine_revision"] == (date(2024, 6, 10) + timedelta(days=PALIERS_JOURS[dernier])).isoformat()


# --- reponse "facile" ----------------------------------------------------------------------


def test_facile_avance_d_un_palier():
    depart = carte(etat="nouvelle", palier=0, prochaine_revision=None)
    resultat = prochaine_revision(depart, "facile", date(2024, 6, 10))
    assert resultat["palier"] == 1
    assert resultat["etat"] == "apprentissage"
    assert resultat["prochaine_revision"] == "2024-06-13"  # +3 jours (PALIERS_JOURS[1])


def test_facile_plafonne_au_dernier_palier_et_devient_acquise():
    dernier = len(PALIERS_JOURS) - 1
    depart = carte(etat="apprentissage", palier=dernier - 1)
    resultat = prochaine_revision(depart, "facile", date(2024, 6, 10))
    assert resultat["palier"] == dernier
    assert resultat["etat"] == "acquise"
    assert resultat["prochaine_revision"] == "2024-08-09"  # +60 jours


def test_carte_deja_acquise_reprise_a_60_jours_ne_depasse_pas_le_plafond():
    """Une carte 'acquise' reste reprise au dernier palier (60 jours), jamais au-dela."""
    dernier = len(PALIERS_JOURS) - 1
    depart = carte(etat="acquise", palier=dernier, prochaine_revision="2024-06-01")
    resultat = prochaine_revision(depart, "facile", date(2024, 6, 10))
    assert resultat["palier"] == dernier
    assert resultat["etat"] == "acquise"
    assert PALIERS_JOURS[resultat["palier"]] == 60
    assert resultat["prochaine_revision"] == "2024-08-09"


# --- reponse inconnue ------------------------------------------------------------------------


def test_reponse_inconnue_leve_value_error_avec_message_clair():
    depart = carte()
    with pytest.raises(ValueError, match="reponse de carte inconnue"):
        prochaine_revision(depart, "moyen", date(2024, 6, 10))


# --- pas de modification en place -------------------------------------------------------------


def test_prochaine_revision_ne_modifie_pas_la_carte_d_origine():
    depart = carte(etat="nouvelle", palier=0, prochaine_revision=None)
    original = dict(depart)
    prochaine_revision(depart, "facile", date(2024, 6, 10))
    assert depart == original


def test_reinitialiser_ne_modifie_pas_la_carte_d_origine():
    depart = carte(etat="acquise", palier=5, prochaine_revision="2024-06-01")
    original = dict(depart)
    reinitialiser(depart)
    assert depart == original


# --- cartes_dues : selection et ordre -----------------------------------------------------


def test_cartes_dues_filtre_par_date():
    aujourdhui = date(2024, 6, 10)
    due = carte(id="due", prochaine_revision="2024-06-10", etat="apprentissage")
    pas_due = carte(id="pas_due", prochaine_revision="2024-06-11", etat="apprentissage")
    passee = carte(id="passee", prochaine_revision="2024-06-01", etat="apprentissage")
    resultat = cartes_dues([due, pas_due, passee], aujourdhui)
    ids = [c["id"] for c in resultat]
    assert "due" in ids
    assert "passee" in ids
    assert "pas_due" not in ids


def test_cartes_dues_place_les_nouvelles_jamais_revisees_en_premier():
    aujourdhui = date(2024, 6, 10)
    ancienne_due = carte(id="ancienne", etat="apprentissage", prochaine_revision="2024-06-01")
    nouvelle = carte(id="nouvelle", etat="nouvelle", prochaine_revision=None)
    autre_ancienne = carte(id="autre", etat="apprentissage", prochaine_revision="2024-06-05")
    resultat = cartes_dues([ancienne_due, nouvelle, autre_ancienne], aujourdhui)
    assert resultat[0]["id"] == "nouvelle"
    ids = [c["id"] for c in resultat]
    assert ids == ["nouvelle", "ancienne", "autre"]


def test_cartes_dues_retourne_des_copies():
    aujourdhui = date(2024, 6, 10)
    depart = carte(id="c1", etat="nouvelle", prochaine_revision=None)
    resultat = cartes_dues([depart], aujourdhui)
    resultat[0]["etat"] = "modifie"
    assert depart["etat"] == "nouvelle"


def test_cartes_dues_exclut_les_cartes_non_dues():
    aujourdhui = date(2024, 6, 10)
    future = carte(id="future", etat="apprentissage", prochaine_revision="2024-07-01")
    assert cartes_dues([future], aujourdhui) == []


# --- passage d'un mois ou d'une annee ----------------------------------------------------


def test_passage_d_un_mois():
    depart = carte(etat="apprentissage", palier=3)  # palier 3 -> 15 jours
    resultat = prochaine_revision(depart, "facile", date(2024, 1, 20))
    # palier passe a 4 -> +30 jours -> 2024-02-19
    assert resultat["prochaine_revision"] == "2024-02-19"


def test_passage_d_une_annee():
    dernier = len(PALIERS_JOURS) - 1
    depart = carte(etat="apprentissage", palier=dernier - 1)
    resultat = prochaine_revision(depart, "facile", date(2024, 12, 15))
    # dernier palier -> +60 jours, franchit le 31 decembre
    assert resultat["prochaine_revision"] == "2025-02-13"
    assert resultat["etat"] == "acquise"


# --- reinitialiser (devalidation, §3) -----------------------------------------------------


def test_reinitialiser_remet_a_l_etat_nouvelle():
    depart = carte(etat="acquise", palier=5, prochaine_revision="2024-06-01")
    resultat = reinitialiser(depart)
    assert resultat["prochaine_revision"] is None
    assert resultat["palier"] == 0
    assert resultat["etat"] == "nouvelle"
    assert resultat["etat"] in ETATS_CARTE


def test_reinitialiser_garde_les_autres_champs():
    depart = carte(id="c42", recto="Question", verso="Reponse", etat="apprentissage", palier=2)
    resultat = reinitialiser(depart)
    assert resultat["id"] == "c42"
    assert resultat["recto"] == "Question"
    assert resultat["verso"] == "Reponse"
