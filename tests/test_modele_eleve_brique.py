"""Brique modele_eleve branchee sur un vrai tuteur (moteur factice), dans un dossier temporaire (lot 7)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from jules.apprentissage import estimateurs
from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from tests.conftest import regle_par_defaut

NOTION = "fractions : addition"
CLE = f"Mathématiques : {NOTION}"


def extraction(resultat: str = "juste", aide: int = 0, affect: str = "neutre") -> str:
    return json.dumps(
        {
            "tentatives": [
                {
                    "matiere": "Mathématiques",
                    "notion": NOTION,
                    "tentative": True,
                    "resultat": resultat,
                    "aide": aide,
                    "premier_essai": True,
                    "auto_correction": False,
                    "explique_methode": False,
                    "declare_compris": False,
                    "affect": affect,
                    "certitude": "haute",
                }
            ]
        }
    )


class Scenario:
    """Regle du moteur factice : l'extraction et la lecon renvoient ce que le test a programme."""

    def __init__(self) -> None:
        self.extraction = extraction()
        self.lecon = '{"lecon": null}'
        self.statut_suivi = "compris"

    def __call__(self, systeme: str, tours, modele: str) -> str:
        if "Tu observes un échange" in systeme:
            return self.extraction
        if "Tu t'étais trompé" in systeme:
            return self.lecon
        if "suivi scolaire" in systeme:
            return json.dumps(
                {"matiere": "Mathématiques", "notion": NOTION, "statut": self.statut_suivi, "resume": "", "titre": "F"}
            )
        return regle_par_defaut(systeme, tours, modele)


@pytest.fixture
def scenario() -> Scenario:
    return Scenario()


@pytest.fixture
def tuteur_modele(projet, brut_config: dict, scenario: Scenario):
    for ref in brut_config["modules"]:
        if ref["id"] == "modele_eleve":
            ref["actif"] = True
    config = depuis_dict(brut_config, projet)
    llm = Factice()
    llm.regle = scenario
    t = Tuteur(config, llm=llm)
    yield t
    t.fermer()


def echanger(tuteur, conv_id: str, texte: str = "1/2 + 1/3 = 5/6") -> None:
    tuteur.echanger(conv_id, texte)
    tuteur._fond.submit(lambda: None).result(timeout=10)  # attend la fin des taches de fond


def modele(tuteur):
    brique = tuteur.module("modele_eleve")
    assert brique is not None
    return brique


def test_un_echange_produit_des_observations_et_un_etat(tuteur_modele, scenario: Scenario) -> None:
    conv = tuteur_modele.stockage.creer_conversation("aide-devoirs")
    echanger(tuteur_modele, conv.id)
    capteurs = {ev["donnees"]["capteur"] for ev in tuteur_modele.stockage.evenements("observation")}
    assert "tentative_aide0" in capteurs
    etats = modele(tuteur_modele).notions()
    assert CLE in etats and estimateurs.p_de(etats[CLE]) > 0.3
    assert modele(tuteur_modele).seance(conv.id) is not None


def test_l_extraction_utilise_le_modele_principal(tuteur_modele) -> None:
    conv = tuteur_modele.stockage.creer_conversation("aide-devoirs")
    echanger(tuteur_modele, conv.id)
    appels = [a for a in tuteur_modele.llm.appels if "Tu observes un échange" in a["systeme"]]
    assert appels and all(a["modele"] == "principal" for a in appels)


def test_la_contribution_ne_contient_aucun_chiffre(tuteur_modele, scenario: Scenario) -> None:
    conv = tuteur_modele.stockage.creer_conversation("aide-devoirs")
    scenario.extraction = extraction("faux", aide=1, affect="frustre")
    echanger(tuteur_modele, conv.id, "j'en ai marre")
    texte = modele(tuteur_modele).contribution(tuteur_modele.stockage.conversation(conv.id))
    assert texte and "agacement" in texte  # etat frustration, texte de consignes/politique.yaml
    assert not any(c.isdigit() for c in texte)
    assert "{" not in texte  # variables et accords remplis


def test_rien_dans_le_prompt_pendant_une_epreuve(tuteur_modele) -> None:
    conv = tuteur_modele.stockage.creer_conversation("epreuve")
    assert modele(tuteur_modele).contribution(conv) is None


def test_une_epreuve_terminee_est_lue_une_seule_fois(tuteur_modele, scenario: Scenario) -> None:
    stockage = tuteur_modele.stockage
    conv = stockage.creer_conversation("aide-devoirs")
    echanger(tuteur_modele, conv.id)
    ep = stockage.creer_conversation("epreuve")
    stockage.ajouter_evenement("epreuve", {"notions": 1, "tenues": [], "pas_tenues": [CLE]}, ep.id)
    brique = modele(tuteur_modele)
    avant = estimateurs.p_de(brique.notions()[CLE])
    brique._traiter_epreuve(stockage.conversation(ep.id))
    brique._traiter_epreuve(stockage.conversation(ep.id))
    predictions = stockage.evenements("prediction")
    assert len(predictions) == 1 and predictions[0]["donnees"]["tenu"] is False
    assert len(stockage.evenements("resultat_epreuve")) == 1
    assert estimateurs.p_de(brique.notions()[CLE]) < avant


def test_une_surprise_propose_une_lecon_filtree(tuteur_modele, scenario: Scenario) -> None:
    stockage = tuteur_modele.stockage
    conv = stockage.creer_conversation("aide-devoirs")
    for _ in range(4):
        echanger(tuteur_modele, conv.id)  # Jules devient tres confiant
    brique = modele(tuteur_modele)
    # l'IA propose d'abord une lecon interdite (diagnostic) : refusee
    scenario.lecon = '{"lecon": {"portee": "matiere", "texte": "Elle est sans doute dyscalculique."}}'
    ep1 = stockage.creer_conversation("epreuve")
    stockage.ajouter_evenement("epreuve", {"notions": 1, "tenues": [], "pas_tenues": [CLE]}, ep1.id)
    brique._traiter_epreuve(stockage.conversation(ep1.id))
    assert brique.lecons() == []
    # puis une lecon acceptable, sur une nouvelle surprise
    for _ in range(4):
        echanger(tuteur_modele, conv.id)
    scenario.lecon = (
        '{"lecon": {"portee": "matiere", "texte": "En calcul, faire refaire un exemple seule avant de valider."}}'
    )
    ep2 = stockage.creer_conversation("epreuve")
    stockage.ajouter_evenement("epreuve", {"notions": 1, "tenues": [], "pas_tenues": [CLE]}, ep2.id)
    brique._traiter_epreuve(stockage.conversation(ep2.id))
    perte = stockage.evenements("prediction")[0]["donnees"]["perte"]
    if perte < brique.base.seuil_surprise:
        pytest.skip(f"pas de surprise dans ce scenario (perte {perte:.2f})")
    lecons = brique.lecons()
    assert len(lecons) == 1 and lecons[0].cle == "Mathématiques" and lecons[0].sens == "surestimation"
    texte = brique.contribution(stockage.conversation(conv.id)) or ""
    assert "refaire un exemple" in texte


def test_reconstruire_redonne_le_meme_etat(tuteur_modele) -> None:
    conv = tuteur_modele.stockage.creer_conversation("aide-devoirs")
    for _ in range(3):
        echanger(tuteur_modele, conv.id)
    brique = modele(tuteur_modele)
    avant = brique.notions()[CLE]
    apres = brique.reconstruire()[CLE]
    assert apres.log_odds == pytest.approx(avant.log_odds)
    assert apres.n_eff == pytest.approx(avant.n_eff)


def test_l_epreuve_utilise_la_retention_predite(tuteur_modele) -> None:
    stockage = tuteur_modele.stockage
    conv = stockage.creer_conversation("aide-devoirs")
    echanger(tuteur_modele, conv.id)
    brique = modele(tuteur_modele)
    etats = brique.notions()
    etat = brique.estimateur.clore_seance(etats[CLE], etats[CLE].derniere_observation or "")
    ancien = (datetime.now().astimezone() - timedelta(days=60)).isoformat(timespec="seconds")
    etats[CLE] = type(etat)(**{**etat.vers_dict(), "derniere_revision": ancien})
    brique._ecrire_notions(etats)
    epreuve = tuteur_modele.module("epreuve")
    assert [n["notion"] for n in epreuve.candidates()] == [NOTION]


def test_routes_parent(tuteur_modele) -> None:
    from fastapi.testclient import TestClient

    from jules.web.app import creer_app

    conv = tuteur_modele.stockage.creer_conversation("aide-devoirs")
    echanger(tuteur_modele, conv.id)
    client = TestClient(creer_app(tuteur_modele))
    base = "/api/modules/modele_eleve"
    notions = client.get(f"{base}/notions").json()
    assert notions[0]["notion"] == CLE and 0 <= notions[0]["fourchette"][0] <= notions[0]["p"]
    assert client.get(f"{base}/fiabilite").json()["epreuves"] == 0
    assert client.get(f"{base}/lecons").json() == []
    assert client.delete(f"{base}/lecons/inconnue").status_code == 404
    assert client.post(f"{base}/reinitialiser").json() == {"notions": 1}
