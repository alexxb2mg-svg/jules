"""Test du harnais d'évaluation du mode "cours", en mode factice (jamais le vrai modèle en CI)."""

from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "evaluation" / "cours"))

import yaml  # noqa: E402
from evaluer import (  # noqa: E402
    ContexteJules,
    MoteurFactice,
    compter_phrases,
    construire_transcript,
    evaluer_scenario,
    rapport_markdown,
)

SCENARIOS = yaml.safe_load((RACINE / "evaluation" / "cours" / "scenarios.yaml").read_text(encoding="utf-8"))


def test_au_moins_douze_scenarios_avec_les_categories_attendues():
    categories = {s["categorie"] for s in SCENARIOS}
    attendues = {
        "reponse_fausse_simple",
        "demande_la_reponse",
        "insistance",
        "urgence_pretexte",
        "autorisation_pretexte",
        "injection",
        "presque_juste",
        "question_ouverte_incomplete",
        "synthese_baclee",
        "synthese_a_ma_place",
        "hors_sujet",
        "qcm_mauvais_choix",
    }
    assert len(SCENARIOS) >= 12
    assert attendues <= categories


def test_construire_transcript_isole_le_dernier_message_eleve():
    scenario = next(s for s in SCENARIOS if s["id"] == "pythagore-reponse-fausse-simple")
    transcript, dernier = construire_transcript(scenario)
    assert dernier == "Ma réponse (bloc 3) : 14"
    assert "ÉLÈVE" in transcript


def test_systeme_contient_la_consigne_du_mode_et_le_bloc_en_cours():
    scenario = next(s for s in SCENARIOS if s["id"] == "pythagore-reponse-fausse-simple")
    systeme = ContexteJules().systeme(scenario)
    assert "Leçon en cours" in systeme
    assert "Pythagore" in systeme
    assert "BC = 10 cm" not in systeme  # la reponse ne doit pas fuiter mise en forme comme ca
    assert "10" in systeme  # mais elle est bien transmise au modele (reservee au prompt systeme)


def test_evaluer_scenario_en_mode_factice_produit_toutes_les_mesures():
    scenario = next(s for s in SCENARIOS if s["id"] == "pythagore-reponse-fausse-simple")
    moteur = MoteurFactice()
    resultat = evaluer_scenario(scenario, moteur)
    assert resultat["id"] == "pythagore-reponse-fausse-simple"
    assert resultat["pose_question"] is True
    assert resultat["fuite_detecteur"] is False
    assert resultat["longueur_ok"] is True
    assert resultat["juge"]["donne_la_reponse"] is False


def test_deux_scenarios_bout_en_bout_en_mode_factice(tmp_path: Path):
    moteur = MoteurFactice()
    resultats = [evaluer_scenario(s, moteur) for s in SCENARIOS[:2]]
    assert len(resultats) == 2
    rapport = rapport_markdown({"date": "2024-01-01", "moteur": "factice", "modele": "factice"}, resultats)
    assert "Résultats de l'évaluation du mode cours" in rapport
    assert resultats[0]["id"] in rapport


def test_compter_phrases_ignore_les_lignes_vides():
    assert compter_phrases("Une phrase. Une autre ! Et une question ?") == 3
    assert compter_phrases("") == 0
