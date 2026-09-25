"""Tests de l'epreuve sans aide : choix des notions, deroulement, resultat dans le suivi et le bilan."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from jules.modules.epreuve import candidates, lire_resultats
from jules.modules.rapport import donnees_du_jour, texte_rapport
from jules.stockage import Message

AUJOURDHUI = date(2026, 9, 24)


def ev(jour: str, notion: str, statut: str, matiere: str = "Mathématiques") -> dict:
    return {"horodatage": f"{jour}T18:00:00+02:00", "donnees": {"matiere": matiere, "notion": notion, "statut": statut}}


def test_candidates_dernier_etat_compris_et_assez_ancien():
    evenements = [  # du plus recent au plus ancien, comme Stockage.evenements
        ev("2026-09-23", "racine carrée", "compris"),  # trop recent (moins de 3 jours)
        ev("2026-09-20", "fractions", "bloque"),  # dernier etat : bloque -> pas candidate
        ev("2026-09-18", "fractions", "compris"),
        ev("2026-09-19", "Thalès", "compris"),
        ev("2026-09-15", "passé composé", "compris", "Français"),
        ev("2026-08-01", "médiane", "compris"),  # hors fenetre (30 jours)
        ev("2026-09-16", "vacances", "hors_scolaire"),
    ]
    retenues = candidates(evenements, AUJOURDHUI, delai_jours=3, fenetre_jours=30, maximum=3)
    assert [n["notion"] for n in retenues] == ["passé composé", "Thalès"]  # la plus ancienne d'abord
    assert retenues[0] == {"matiere": "Français", "notion": "passé composé", "jour": "2026-09-15"}
    assert candidates(evenements, AUJOURDHUI, 3, 30, maximum=1) == retenues[:1]


def test_une_notion_deja_passee_a_l_epreuve_n_est_plus_proposee():
    evenements = [ev("2026-09-22", "Thalès", "acquis"), ev("2026-09-15", "Thalès", "compris")]
    assert candidates(evenements, AUJOURDHUI, 3, 30, 3) == []


def test_lire_resultats_ramene_aux_libelles_de_l_epreuve():
    notions = [{"matiere": "Mathématiques", "notion": "Thalès"}, {"matiere": "Français", "notion": "passé composé"}]
    brut = (
        '```json\n{"resultats": [{"notion": "mathématiques : thalès", "tenu": true}, '
        '{"notion": "Français : passé composé", "tenu": false}, {"notion": "Inventée : x", "tenu": true}, '
        '{"notion": "Mathématiques : Thalès", "tenu": "oui"}]}\n```'
    )
    assert lire_resultats(brut, notions) == {"Mathématiques : Thalès": True, "Français : passé composé": False}
    assert lire_resultats("pas de JSON", notions) == {}


def preparer_notions_comprises(tuteur):
    """Deux notions comprises il y a 5 jours (conversation normale), directement dans la base."""
    stockage = tuteur.stockage
    conv = stockage.creer_conversation("aide-devoirs")
    for notion in ("Thalès", "racine carrée"):
        stockage.ajouter_evenement(
            "suivi", {"matiere": "Mathématiques", "notion": notion, "statut": "compris", "resume": ""}, conv.id
        )
    il_y_a_5_jours = (datetime.now().astimezone() - timedelta(days=5)).isoformat(timespec="seconds")
    with stockage._verrou, stockage._cx:
        stockage._cx.execute("UPDATE evenements SET horodatage = ?", (il_y_a_5_jours,))


def test_epreuve_de_bout_en_bout(tuteur):
    preparer_notions_comprises(tuteur)
    module = tuteur.module("epreuve")
    assert [n["notion"] for n in module.candidates()] == ["Thalès", "racine carrée"]

    lancee = module.commencer()
    assert lancee["mode"] == "epreuve" and "sans aide" in lancee["presentation"]
    assert "Thalès, racine carrée" in lancee["presentation"] and "{" not in lancee["presentation"]

    base = tuteur.llm.regle
    analyses: list[str] = []

    def regle(systeme, tours, modele):
        if "bilan final d'une épreuve" in systeme:
            return (
                '{"resultats": [{"notion": "Mathématiques : Thalès", "tenu": true}, '
                '{"notion": "Mathématiques : racine carrée", "tenu": false}]}'
            )
        if modele == "principal" and "Question" not in tours[-1].texte and "prêt" not in tours[-1].texte:
            return "Thalès : a tenu. Racine carrée : n'a pas tenu. Bravo pour tes efforts. Épreuve terminée."
        if "suivi scolaire" in systeme or "UNE notion d'une liste fermée" in systeme:
            analyses.append(systeme)
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle
    tuteur.echanger(lancee["id"], "prêt")
    tuteur.attendre_fond()
    systeme = tuteur.systeme(tuteur.stockage.conversation(lancee["id"]))
    assert "Mathématiques : Thalès (marquée comprise le" in systeme  # Jules connait la liste
    assert "tu n'aides pas" in systeme and "Choisir une notion" not in systeme
    assert tuteur.stockage.evenements("epreuve") == []  # pas encore finie

    tuteur.echanger(lancee["id"], "Réponse à la dernière question : 7")
    tuteur.attendre_fond()
    assert analyses == []  # ni suivi ni detection de notion pendant l'epreuve

    resultat = tuteur.stockage.evenements("epreuve")[0]["donnees"]
    assert resultat["tenues"] == ["Mathématiques : Thalès"]
    assert resultat["pas_tenues"] == ["Mathématiques : racine carrée"]
    statuts = {e["donnees"]["notion"]: e["donnees"]["statut"] for e in tuteur.stockage.evenements("suivi")[:2]}
    assert statuts == {"Thalès": "acquis", "racine carrée": "en_cours"}
    assert module.candidates() == []  # plus rien a reprendre (et une epreuve par jour au plus)

    # un nouveau message apres la fin ne recompte rien
    tuteur.echanger(lancee["id"], "merci")
    tuteur.attendre_fond()
    assert len(tuteur.stockage.evenements("epreuve")) == 1

    # le bilan du soir le dit au parent
    jour = datetime.now().astimezone().date().isoformat()
    texte = tuteur.module("rapport").rapport(jour)["texte"]
    assert "Épreuve sans aide : 1 notion(s) sur 2 ont tenu ; à retravailler : Mathématiques : racine carrée." in texte
    assert "[ACQUIS] Mathématiques : Thalès" in texte
    # et la memoire de Jules le sait pour la suite
    autre = tuteur.stockage.creer_conversation("aide-devoirs")
    assert "Notions qui ont tenu à une épreuve sans aide : Mathématiques : Thalès" in tuteur.systeme(autre)


def test_mode_epreuve_ni_dans_la_grille_ni_ouvrable_directement(tuteur):
    modes = tuteur.infos_interface()["modes"]
    # Membership plutôt qu'égalité stricte : d'autres modes cachés (ex. "cours", lancé par le
    # module cours et non depuis la grille) peuvent coexister sans invalider ce test.
    assert "epreuve" in [m["id"] for m in modes if m["cache"]]
    assert tuteur.module("modes").valider("epreuve") == "aide-devoirs"


def test_rien_a_reprendre_refus_propre(tuteur):
    from fastapi.testclient import TestClient

    from jules.web.app import creer_app

    with TestClient(creer_app(tuteur)) as client:
        assert client.get("/api/eleve/epreuve/proposition").json() == {"notions": []}
        assert client.post("/api/eleve/epreuve/commencer").status_code == 409
        preparer_notions_comprises(tuteur)
        lancee = client.post("/api/eleve/epreuve/commencer").json()
        assert lancee["titre"] == "Épreuve sans aide"
        assert client.post("/api/conversations", json={"mode": "epreuve"}).json()["mode"] == "aide-devoirs"


def test_texte_rapport_sans_epreuve_inchange():
    d = donnees_du_jour([{"conversation": "a", "role": "eleve", "horodatage": "2026-09-24T18:00:00+02:00"}], [], [])
    assert "Épreuve" not in texte_rapport("Camille", "2026-09-24", d)


def test_message_de_fin_sans_epreuve_enregistree_ignore(tuteur):
    conv = tuteur.stockage.creer_conversation("epreuve")  # etat absent : rien a enregistrer
    tuteur.module("epreuve").apres_echange(conv, Message("eleve", "x"), Message("bot", "Épreuve terminée."))
    assert tuteur.stockage.evenements("epreuve") == []


def test_une_epreuve_par_jour_au_plus(tuteur):
    """L'invitation disparait des le lancement : pas de deuxieme epreuve le meme jour, meme inachevee."""
    preparer_notions_comprises(tuteur)
    module = tuteur.module("epreuve")
    module.commencer()
    assert module.candidates() == []
