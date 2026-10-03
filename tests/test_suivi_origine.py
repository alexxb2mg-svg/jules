"""Tests de l'origine des evenements 'suivi' et de l'arbitrage du statut 'acquis'.

Revue du 27/09/2026 : un evenement 'suivi' d'origine 'analyse' (le modele rapide, en tache de fond,
sur un echange qui peut etre hors sujet) ne doit jamais retrograder un statut 'acquis' deja retenu.
Seule une origine qui reprend directement la notion (epreuve, cours, exercices) le peut.
"""

from __future__ import annotations

from jules.modules.suivi import (
    ORIGINE_DEFAUT,
    ORIGINES_SUIVI,
    dernier_statut,
    evenement_suivi,
)


def ev(jour: str, notion: str, statut: str, origine: str | None = None, matiere: str = "Mathématiques") -> dict:
    donnees = {"matiere": matiere, "notion": notion, "statut": statut}
    if origine is not None:
        donnees["origine"] = origine
    return {"horodatage": f"{jour}T18:00:00+02:00", "donnees": donnees}


def test_evenement_suivi_porte_l_origine():
    d = evenement_suivi("Mathématiques", "Thalès", "compris", resume="ok", titre="Thalès", origine="cours")
    assert d == {
        "matiere": "Mathématiques",
        "notion": "Thalès",
        "statut": "compris",
        "resume": "ok",
        "titre": "Thalès",
        "origine": "cours",
    }
    assert set(ORIGINES_SUIVI) == {"analyse", "epreuve", "cours", "exercices", "studio", "annales"}


def test_evenement_suivi_refuse_une_origine_inconnue():
    try:
        evenement_suivi("Mathématiques", "Thalès", "compris", origine="invente")
    except ValueError:
        pass
    else:
        raise AssertionError("une origine inconnue doit lever ValueError")


def test_acquis_resiste_a_une_analyse_plus_recente():
    """acquis -> injection d'un suivi 'analyse' en_cours -> reste acquis."""
    evenements = [  # du plus recent au plus ancien
        ev("2026-09-24", "Thalès", "en_cours", origine="analyse"),
        ev("2026-09-20", "Thalès", "acquis", origine="epreuve"),
    ]
    retenu = dernier_statut(evenements)
    cle = ("mathématiques", "thalès")
    assert retenu[cle]["donnees"]["statut"] == "acquis"


def test_acquis_retrograde_par_une_epreuve():
    """acquis -> suivi 'epreuve' en_cours -> devient en_cours."""
    evenements = [
        ev("2026-09-24", "Thalès", "en_cours", origine="epreuve"),
        ev("2026-09-20", "Thalès", "acquis", origine="epreuve"),
    ]
    retenu = dernier_statut(evenements)
    cle = ("mathématiques", "thalès")
    assert retenu[cle]["donnees"]["statut"] == "en_cours"


def test_acquis_retrograde_par_une_reprise_directe_cours_ou_exercices():
    for origine in ("cours", "exercices"):
        evenements = [
            ev("2026-09-24", "Thalès", "en_cours", origine=origine),
            ev("2026-09-20", "Thalès", "acquis", origine="epreuve"),
        ]
        retenu = dernier_statut(evenements)
        assert retenu[("mathématiques", "thalès")]["donnees"]["statut"] == "en_cours"


def test_compris_bloque_par_une_analyse_normale():
    """compris -> analyse bloque -> bloque (comportement inchange pour les autres statuts)."""
    evenements = [
        ev("2026-09-24", "fractions", "bloque", origine="analyse"),
        ev("2026-09-20", "fractions", "compris", origine="analyse"),
    ]
    retenu = dernier_statut(evenements)
    assert retenu[("mathématiques", "fractions")]["donnees"]["statut"] == "bloque"


def test_evenement_sans_origine_traite_comme_analyse():
    """Un evenement ecrit avant l'introduction du champ 'origine' ne retrograde pas un acquis."""
    evenements = [
        ev("2026-09-24", "Thalès", "en_cours", origine=None),
        ev("2026-09-20", "Thalès", "acquis", origine="epreuve"),
    ]
    retenu = dernier_statut(evenements)
    assert retenu[("mathématiques", "thalès")]["donnees"]["statut"] == "acquis"
    assert ORIGINE_DEFAUT == "analyse"


def test_hors_scolaire_et_notions_incompletes_ignores():
    evenements = [
        {"horodatage": "2026-09-24T18:00:00", "donnees": {"matiere": "Autre", "statut": "hors_scolaire"}},
        {"horodatage": "2026-09-23T18:00:00", "donnees": {"statut": "compris"}},  # pas de notion
        ev("2026-09-20", "Thalès", "compris"),
    ]
    retenu = dernier_statut(evenements)
    assert list(retenu.keys()) == [("mathématiques", "thalès")]
