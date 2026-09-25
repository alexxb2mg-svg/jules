"""Tests du coeur : briques, persona, assemblage du prompt, echange, modules."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from jules.briques import ErreurBrique, classe_brique
from jules.modules.base import Tache, extraire_json
from jules.modules.memoire import bilan_notions
from jules.modules.rapport import donnees_du_jour, lire_synthese, minutes_travail, questions_de_secours, texte_rapport
from jules.modules.vigilance import doit_alerter
from jules.planificateur import Planificateur


def test_briques_chargees_depuis_la_config(tuteur):
    assert [m.id for m in tuteur.modules] == [
        "modes",
        "notions",
        "cours",
        "studio",
        "memoire",
        "suivi",
        "vigilance",
        "epreuve",
        "rapport",
    ]
    assert [type(n).__module__ for n in tuteur.notifieurs] == ["jules.notifieurs.fichier"]


def test_brique_inconnue_refusee():
    with pytest.raises(ErreurBrique):
        classe_brique("modules", "nexistepas")
    with pytest.raises(ErreurBrique):
        classe_brique("modules", "../secret")


def test_prompt_assemble_dans_le_bon_ordre(tuteur):
    conv = tuteur.stockage.creer_conversation("quiz")
    systeme = tuteur.systeme(conv)
    ordre = ["# Qui tu es", "# Profil de l'élève", "# Pedagogie", "# Format", "# Mode de travail choisi", "# Securite"]
    positions = [systeme.index(titre) for titre in ordre]
    assert positions == sorted(positions)
    assert "Camille" in systeme and "{prenom}" not in systeme and "{parent}" not in systeme
    assert "Mode : Quiz" in systeme


def test_persona_modifiee_a_chaud(tuteur):
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    fichier = tuteur.config.dossier_persona / "ton.md"
    fichier.write_text("Parle comme un pirate.", encoding="utf-8")
    assert "Parle comme un pirate." in tuteur.systeme(conv)


def test_mode_inconnu_remplace_par_defaut(tuteur):
    assert tuteur.module("modes").valider("nimportequoi") == "aide-devoirs"
    assert tuteur.module("modes").valider("quiz") == "quiz"


def test_ajouter_un_mode_sans_code(tuteur):
    (tuteur.config.dossier_consignes / "modes" / "dictee.md").write_text(
        "---\nnom: Dictée\nicone: x\ndescription: d\nordre: 9\n---\nFais une dictée.", encoding="utf-8"
    )
    ids = [m["id"] for m in tuteur.infos_interface()["modes"]]
    assert "dictee" in ids


def test_echange_complet_et_modules_de_fond(tuteur):
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    reponse = tuteur.echanger(conv.id, "Combien font 1/2 + 1/3 ?")
    tuteur.attendre_fond()
    assert reponse.texte == "Qu'est-ce que tu as déjà essayé ?"
    relue = tuteur.stockage.conversation(conv.id)
    assert [m.role for m in relue.messages] == ["eleve", "bot"]
    assert relue.titre == "Fractions"
    suivis = tuteur.stockage.evenements("suivi")
    assert suivis[0]["donnees"]["statut"] == "bloque"
    assert tuteur.stockage.evenements("vigilance") == []
    # le modele principal sert a l'eleve (une fois), le rapide aux analyses (notion, suivi, vigilance)
    modeles = [a["modele"] for a in tuteur.llm.appels]
    assert modeles.count("principal") == 1 and set(modeles) == {"principal", "rapide"}


def test_memoire_reinjectee_au_tour_suivant(tuteur):
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "1/2 + 1/3 ?")
    tuteur.attendre_fond()
    tuteur.stockage.ecrire_etat("memoire", "notes", [{"id": "a", "texte": "Contrôle vendredi", "jusqu_au": None}])
    systeme = tuteur.systeme(tuteur.stockage.conversation(conv.id))
    assert "Mathématiques : fractions : addition" in systeme
    assert "Contrôle vendredi" in systeme


def test_panne_du_moteur_message_gentil(tuteur):
    def panne(*_):
        raise RuntimeError("reseau coupe")

    tuteur.llm.regle = panne
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    reponse = tuteur.echanger(conv.id, "Bonjour")
    assert "pause" in reponse.texte
    assert tuteur.stockage.evenements("erreur")[0]["donnees"]["message"] == "reseau coupe"


def test_vigilance_alerte_le_parent(tuteur):
    base = tuteur.llm.regle

    def regle(systeme, tours, modele):
        if "Tu protèges un élève" in systeme:
            return '{"niveau": "eleve", "motif": "Dit être harcelé au collège."}'
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "des élèves m'embêtent tous les jours")
    tuteur.attendre_fond()
    journal = next((tuteur.config.donnees / "notifications").glob("*.log")).read_text(encoding="utf-8")
    assert "[URGENT]" in journal and "harcelé" in journal


def test_seuil_vigilance():
    assert doit_alerter("moyen", "moyen") and doit_alerter("eleve", "moyen")
    assert not doit_alerter("faible", "moyen") and not doit_alerter("bizarre", "moyen")


def test_rapport_du_jour(tuteur):
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "1/2 + 1/3 ?")
    tuteur.attendre_fond()
    jour = datetime.now().astimezone().date().isoformat()
    r = tuteur.module("rapport").envoyer(jour)
    assert r["envoye"] is True
    assert "[BLOQUE] Mathématiques : fractions : addition" in r["texte"]
    assert "Belle séance" in r["texte"]
    # le modele a repondu en texte libre : une question de secours est construite sur la notion bloquee
    assert r["questions"] == ["Sur « fractions : addition » : montre-moi jusqu'où tu arrives, et dis-moi où ça coince."]
    assert "pas besoin de savoir faire l'exercice" in r["texte"]
    assert r["texte"].rstrip().endswith("où ça coince.")


def test_rapport_questions_du_modele(tuteur):
    regle_normale = tuteur.llm.regle

    def regle(systeme, tours, modele):
        if "résumé de sa séance" in systeme:
            return (
                '```json\n{"resume": "Camille a travaillé les fractions.", "questions": '
                '["Explique-moi comment tu additionnes deux fractions.", "Montre-moi ton brouillon.", "Trop."]}\n```'
            )
        return regle_normale(systeme, tours, modele)

    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "1/2 + 1/3 ?")
    tuteur.attendre_fond()
    r = tuteur.module("rapport").rapport(datetime.now().astimezone().date().isoformat())
    assert r["questions"] == ["Explique-moi comment tu additionnes deux fractions.", "Montre-moi ton brouillon."]
    assert "Camille a travaillé les fractions." in r["texte"]
    assert "```" not in r["texte"] and '"resume"' not in r["texte"]
    assert "- Montre-moi ton brouillon." in r["texte"] and "Trop." not in r["texte"]


def test_rapport_questions_desactivables(tuteur):
    tuteur.module("rapport").reglages["questions"] = False
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "1/2 + 1/3 ?")
    tuteur.attendre_fond()
    r = tuteur.module("rapport").rapport(datetime.now().astimezone().date().isoformat())
    assert r["questions"] == [] and "À demander" not in r["texte"]


def test_questions_de_secours_notion_bloquee_d_abord():
    d = {
        "notions": {
            "SVT : cellule": {"statut": "compris", "resume": ""},
            "Maths : Thalès": {"statut": "en_cours", "resume": ""},
            "Maths : nombres premiers": {"statut": "bloque", "resume": ""},
        }
    }
    questions = questions_de_secours(d)
    assert len(questions) == 2
    assert questions[0].startswith("Sur « nombres premiers » : montre-moi")
    assert questions[1].startswith("Sur « Thalès » : raconte-moi")
    assert questions_de_secours({"notions": {}}) == []


def test_lire_synthese_tolere_les_reponses_bancales():
    assert lire_synthese("Belle séance.") == ("Belle séance.", [])
    assert lire_synthese('{"resume": "Bien.", "questions": "Explique-moi."}') == ("Bien.", ["Explique-moi."])
    assert lire_synthese('{"resume": "Bien.", "questions": ["", "  "]}') == ("Bien.", [])
    assert lire_synthese('{"questions": ["' + "x" * 500 + '"]}')[1][0] == "x" * 240


def test_rapport_vide_sans_question():
    d = donnees_du_jour([], [], [])
    texte = texte_rapport("Camille", "2026-09-23", d, "", ["Explique-moi."])
    assert texte == "Camille n'a pas utilisé Jules le 2026-09-23."


def test_minutes_travail_ignore_les_pauses():
    msgs = [
        {"conversation": "a", "role": "eleve", "horodatage": "2026-09-23T17:00:00+02:00"},
        {"conversation": "a", "role": "bot", "horodatage": "2026-09-23T17:05:00+02:00"},
        {"conversation": "a", "role": "eleve", "horodatage": "2026-09-23T19:00:00+02:00"},
    ]
    assert minutes_travail(msgs) == 20  # 5 min + pause plafonnee a 15 min


def test_rapport_dernier_statut_gagne():
    suivis = [  # du plus recent au plus ancien, comme renvoye par la base
        {"donnees": {"matiere": "Maths", "notion": "Thalès", "statut": "compris", "resume": ""}},
        {"donnees": {"matiere": "Maths", "notion": "Thalès", "statut": "bloque", "resume": ""}},
    ]
    d = donnees_du_jour([], suivis, [])
    assert d["notions"]["Maths : Thalès"]["statut"] == "compris"


def test_bilan_notions_fenetre():
    evs = [
        {"horodatage": "2026-09-22T10:00:00", "donnees": {"matiere": "SVT", "notion": "cellule", "statut": "compris"}},
        {"horodatage": "2026-08-01T10:00:00", "donnees": {"matiere": "SVT", "notion": "vieux", "statut": "bloque"}},
    ]
    bilan = bilan_notions(evs, 21, date(2026, 9, 23))
    assert bilan == {"bloque": [], "compris": ["SVT : cellule"], "acquis": []}


def test_planificateur_une_fois_par_jour(tuteur):
    appels = []
    p = Planificateur([Tache("t", "20:00", lambda: appels.append(1))], tuteur.stockage)
    assert p.tourner_une_fois(datetime(2026, 9, 23, 19, 59)) == []
    assert p.tourner_une_fois(datetime(2026, 9, 23, 20, 0)) == ["t"]
    assert p.tourner_une_fois(datetime(2026, 9, 23, 21, 0)) == []
    assert p.tourner_une_fois(datetime(2026, 9, 24, 20, 30)) == ["t"]
    assert len(appels) == 2


def test_extraire_json_tolerant():
    assert extraire_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extraire_json("pas de json") is None
