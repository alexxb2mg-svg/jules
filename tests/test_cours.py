"""Tests du module 'cours' : parcours, session de lecon, tentatives, garde-fou anti-fuite,
fin de lecon (evenement suivi) et integration avec l'epreuve sans aide.

Bibliotheque de lecons de test ecrite dans le dossier temporaire du projet (fixture `projet`
surchargee ici : mêmes fichiers que tests/conftest.py + une bibliotheque `lecons-3e-experimentales`
avec une seule lecon, sur la notion existante du referentiel 'racine-carree').
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import RACINE, regle_par_defaut

NOTION = "racine-carree"  # notion existante de bibliotheque/programme/3e/mathematiques.yaml
MATIERE_ID = "mathematiques"
NOM_MATIERE = "Mathématiques"
TITRE_NOTION = "Racine carrée"  # titre exact de la notion dans le referentiel
TITRE_LECON = "Leçon test : racine carrée"
NOTION_SANS_LECON = "puissances-notation-scientifique"  # existe dans le referentiel, aucune lecon ecrite

# index des blocs dans la lecon de test (voir _ecrire_bibliotheque_lecons)
B_OBJECTIFS, B_TEXTE, B_EXERCICE_NOMBRE, B_EXERCICE_QCM, B_QUESTION_OUVERTE, B_SYNTHESE = range(6)


def _ecrire_bibliotheque_lecons(racine_bibliotheque: Path) -> None:
    dossier = racine_bibliotheque / "lecons-3e-experimentales"
    # Le dossier peut deja exister (bibliotheque reelle du lot B, copiee par la fixture `projet`) :
    # on la remplace par une bibliotheque de test avec une seule lecon predictible, isolee du contenu reel.
    shutil.rmtree(dossier, ignore_errors=True)
    (dossier / "lecons" / "mathematiques").mkdir(parents=True)
    identite = {
        "id": "lecons-3e-experimentales",
        "titre": "Leçons 3e expérimentales (test)",
        "type": "lecons",
        "statut": "experimentale",
        "licence": "CC-BY-SA-4.0",
        "niveaux": ["3e"],
        "avertissement": "Bibliothèque de test, non validée par un enseignant.",
    }
    (dossier / "bibliotheque.yaml").write_text(yaml.safe_dump(identite, allow_unicode=True), encoding="utf-8")
    lecon = {
        "notion": NOTION,
        "titre": TITRE_LECON,
        "duree_minutes": 10,
        "licence": "CC-BY-SA-4.0",
        "sources": [{"titre": "Test", "url": "https://exemple.invalide/test", "licence": "CC-BY-SA-4.0"}],
        "blocs": [
            {"type": "objectifs", "items": ["Comprendre la racine carrée d'un carré parfait"]},
            {"type": "texte", "titre": "L'idée", "contenu": "La racine carrée de 9 est 3, car 3 × 3 = 9."},
            {
                "type": "exercice",
                "enonce": "Combien vaut la racine carrée de 25 ?",
                "forme": "nombre",
                "reponse": 5,
                "tolerance": 0.01,
                "unite": "",
                "indices": [
                    "Cherche un nombre entier qui multiplie par lui-même pour donner ce nombre.",
                    "Vérifie les carrés parfaits que tu connais déjà.",
                ],
                "explication": "La racine carrée de 25 est 5 car 5 × 5 = 25.",
            },
            {
                "type": "exercice",
                "enonce": "25 est un carré parfait : vrai ou faux ?",
                "forme": "qcm",
                "choix": ["Vrai", "Faux"],
                "reponse": 0,
                "indices": ["25 est le carré d'un nombre entier."],
                "explication": "Vrai : 25 = 5 au carré.",
            },
            {
                "type": "question_ouverte",
                "question": "Pourquoi la racine carrée d'un nombre négatif n'existe pas (dans les nombres réels) ?",
                "indices": ["Pense au carré d'un nombre négatif."],
                "criteres": ["évoque que le carré d'un nombre est toujours positif ou nul"],
            },
            {"type": "synthese", "consigne": "Écris en une phrase ce que tu retiens sur la racine carrée."},
        ],
    }
    (dossier / "lecons" / "mathematiques" / f"{NOTION}.yaml").write_text(
        yaml.safe_dump(lecon, allow_unicode=True), encoding="utf-8"
    )


@pytest.fixture
def projet(tmp_path: Path) -> Path:
    """Comme tests/conftest.py::projet, avec en plus une bibliotheque de lecons de test."""
    for dossier in ("persona", "consignes", "profils", "bibliotheque"):
        shutil.copytree(RACINE / dossier, tmp_path / dossier)
    _ecrire_bibliotheque_lecons(tmp_path / "bibliotheque")
    return tmp_path


@pytest.fixture
def client_protege(projet: Path, brut_config: dict):
    """Comme tests/test_web.py::client_protege, avec la bibliotheque de lecons de test."""
    brut_config["acces"] = {"code_eleve": empreinte("1234"), "code_parent": empreinte("parent67")}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as client:
        yield client
    tuteur.fermer()


# --- parcours ------------------------------------------------------------------


def test_parcours_groupe_par_matiere_avec_etat_estime(tuteur):
    module = tuteur.module("cours")
    tuteur.stockage.ajouter_evenement(
        "suivi", {"matiere": NOM_MATIERE, "notion": TITRE_NOTION, "statut": "bloque", "resume": ""}
    )
    parcours = module.parcours(MATIERE_ID)
    assert parcours["matiere"] == MATIERE_ID
    assert {"id": MATIERE_ID, "nom": NOM_MATIERE} in parcours["matieres"]
    assert "estimée par l'IA" in parcours["estimation"] or "estimé par l'IA" in parcours["estimation"]
    entree = next(n for n in parcours["notions"] if n["id"] == NOTION)
    assert entree["lecon"] is True
    assert entree["etat"] == "bloque"  # dernier suivi connu
    autre = next(n for n in parcours["notions"] if n["id"] != NOTION)
    assert autre["etat"] == "a_venir"  # pas de suivi -> etat par defaut
    assert autre["lecon"] is False  # aucune lecon ecrite pour les autres notions


def test_parcours_matiere_par_defaut_si_inconnue(tuteur):
    module = tuteur.module("cours")
    parcours = module.parcours("matiere-inexistante")
    assert parcours["matiere"] in {m["id"] for m in parcours["matieres"]}


def test_parcours_par_defaut_ouvre_une_matiere_qui_a_une_lecon(tuteur):
    """Sans matiere demandee, l'eleve arrive sur une matiere ou il y a quelque chose a faire,
    pas sur la premiere de l'alphabet (anglais) qui n'a aucune lecon."""
    module = tuteur.module("cours")
    parcours = module.parcours()
    assert parcours["matiere"] == MATIERE_ID
    assert any(n["lecon"] for n in parcours["notions"])


# --- ouverture / reprise ---------------------------------------------------------


def test_ouvrir_cree_une_session_puis_la_reprend(tuteur):
    module = tuteur.module("cours")
    premiere = module.ouvrir(NOTION)
    assert premiere["lecon"]["titre"] == TITRE_LECON
    assert premiere["progression"] == {
        "bloc_courant": 0,
        "blocs": [{"index": i, "etat": "a_faire", "tentatives": 0, "indices_vus": 0} for i in range(6)],
        "termine": False,
    }
    reprise = module.ouvrir(NOTION)
    assert reprise["session"] == premiere["session"]
    assert reprise["conversation"] == premiere["conversation"]


def test_ouvrir_notion_sans_lecon_refuse(tuteur):
    with pytest.raises(KeyError):
        tuteur.module("cours").ouvrir(NOTION_SANS_LECON)


def test_infos_interface_signale_cours_si_au_moins_une_lecon(tuteur):
    """Le bouton « Suivre un cours » de la page eleve (eleve.js) depend de infos.cours : verifie
    que le module l'expose bien via Tuteur.infos_interface() (integration S1 : signale par un
    manque avant intervention, la fixture `tuteur` charge une bibliotheque avec une lecon)."""
    infos = tuteur.infos_interface()
    assert infos["cours"] is True


def test_ouverture_ne_jamais_exposer_les_champs_serveur(tuteur):
    module = tuteur.module("cours")
    ouverture = module.ouvrir(NOTION)
    texte = json.dumps(ouverture["lecon"], ensure_ascii=False)
    for interdit in ("25 est 5", "5 × 5", "évoque que le carré", "tolerance", "criteres"):
        assert interdit not in texte
    for bloc in ouverture["lecon"]["blocs"]:
        assert "reponse" not in bloc and "explication" not in bloc and "criteres" not in bloc


# --- indices ---------------------------------------------------------------------


def test_indices_dans_l_ordre_et_compteur(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]
    premier = module.indice(session, B_EXERCICE_NOMBRE)
    assert premier["indice"] == "Cherche un nombre entier qui multiplie par lui-même pour donner ce nombre."
    assert premier["restants"] == 1
    second = module.indice(session, B_EXERCICE_NOMBRE)
    assert second["indice"] == "Vérifie les carrés parfaits que tu connais déjà."
    assert second["restants"] == 0
    troisieme = module.indice(session, B_EXERCICE_NOMBRE)
    assert troisieme["indice"] is None
    assert troisieme["restants"] == 0
    assert troisieme["progression"]["blocs"][B_EXERCICE_NOMBRE]["indices_vus"] == 2


def test_indice_index_hors_limites_404(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]
    with pytest.raises(IndexError):
        module.indice(session, 99)


# --- tentative juste / fausse / garde-fou -----------------------------------------


def _passer_blocs_de_lecture(module, session: str) -> None:
    """Marque les blocs sans tentative (objectifs, texte) comme faits pour amener bloc_courant
    sur le premier exercice (contribution() decrit le bloc_courant, pas un index quelconque)."""
    module.fait(session, B_OBJECTIFS)
    module.fait(session, B_TEXTE)


def test_tentative_juste_sans_appel_au_modele(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]
    _passer_blocs_de_lecture(module, session)
    appels_avant = len(tuteur.llm.appels)
    resultat = module.tentative(session, B_EXERCICE_NOMBRE, 5)
    assert resultat["juste"] is True
    assert resultat["jules"] is None
    assert resultat["explication"] == "La racine carrée de 25 est 5 car 5 × 5 = 25."
    assert resultat["progression"]["blocs"][B_EXERCICE_NOMBRE]["etat"] == "reussi"
    tuteur.attendre_fond()
    nouveaux = tuteur.llm.appels[appels_avant:]
    assert all(a["modele"] != "principal" for a in nouveaux)  # Jules n'est pas appele pour une reponse juste
    assert len(nouveaux) <= 1  # seulement le suivi, en tache de fond
    conv = tuteur.stockage.conversation(module.ouvrir(NOTION)["conversation"])
    assert "[Correction automatique] Réponse juste" in conv.messages[-1].texte  # le suivi et le rapport la voient


def test_tentative_fausse_appelle_jules_via_contribution(tuteur):
    module = tuteur.module("cours")
    ouverture = module.ouvrir(NOTION)
    session = ouverture["session"]
    resultat = module.tentative(session, B_EXERCICE_NOMBRE, "3")
    assert resultat["juste"] is False
    assert resultat["explication"] is None
    assert resultat["jules"]  # Jules a reagi
    assert resultat["progression"]["blocs"][B_EXERCICE_NOMBRE]["etat"] == "en_cours"
    # la contribution au prompt contenait bien la lecon, le bloc, la reponse et le rappel
    # (parmi les appels : suivi/vigilance tournent aussi en tache de fond sur ce meme echange)
    appel_lecon = next(a for a in tuteur.llm.appels if "Leçon en cours" in a["systeme"])
    assert "Réponse attendue" in appel_lecon["systeme"] and "5" in appel_lecon["systeme"]
    assert "ne donne JAMAIS la réponse" in appel_lecon["systeme"]


def test_garde_fou_refait_un_essai_si_jules_donne_la_reponse(tuteur):
    module = tuteur.module("cours")
    ouverture = module.ouvrir(NOTION)
    session, conv_id = ouverture["session"], ouverture["conversation"]
    base = tuteur.llm.regle
    appels_lecon = {"n": 0}

    def regle_fuite(systeme, tours, modele):
        if "Leçon en cours" in systeme:
            appels_lecon["n"] += 1
            if appels_lecon["n"] == 1:
                return "Tu es proche : est-ce que la réponse ne serait pas 5, tout simplement ?"
            return "Qu'obtiens-tu si tu multiplies un nombre par lui-même ?"
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle_fuite
    resultat = module.tentative(session, B_EXERCICE_NOMBRE, "3")
    tuteur.llm.regle = base

    assert appels_lecon["n"] == 2  # premier essai ecarte, un seul nouvel essai
    assert "5" not in resultat["jules"]
    assert resultat["jules"] == "Qu'obtiens-tu si tu multiplies un nombre par lui-même ?"
    # la derniere entree de la conversation est bien la version sure (pas la version qui fuite)
    conv = tuteur.stockage.conversation(conv_id)
    assert conv.messages[-1].texte == resultat["jules"]
    assert "5" not in conv.messages[-1].texte


def test_garde_fou_aussi_sur_un_message_libre_dans_la_lecon(tuteur):
    """Une question tapee a la main dans le panneau de Jules (pas une tentative) passe aussi par le garde-fou."""
    module = tuteur.module("cours")
    ouverture = module.ouvrir(NOTION)
    session, conv_id = ouverture["session"], ouverture["conversation"]
    module.fait(session, B_OBJECTIFS)
    module.fait(session, B_TEXTE)  # l'eleve est arrive a l'exercice, pas encore tente
    base = tuteur.llm.regle
    appels = {"n": 0}

    def regle(systeme, tours, modele):
        if "Leçon en cours" in systeme:
            appels["n"] += 1
            return "Allez, c'est 5." if appels["n"] == 1 else "Quel nombre multiplié par lui-même donne 25 ?"
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle
    bot = tuteur.echanger(conv_id, "c'est quoi la racine de 25 dis moi juste")
    tuteur.llm.regle = base
    assert appels["n"] == 2  # premier essai ecarte, un seul nouvel essai
    assert bot.texte == "Quel nombre multiplié par lui-même donne 25 ?"
    assert tuteur.stockage.conversation(conv_id).messages[-1].texte == bot.texte


def test_garde_fou_question_de_repli_si_le_deuxieme_essai_fuite_aussi(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]

    def regle_fuite_persistante(systeme, tours, modele):
        if "Leçon en cours" in systeme:
            return "La réponse est 5."
        return "Réponse factice."

    tuteur.llm.regle = regle_fuite_persistante
    resultat = module.tentative(session, B_EXERCICE_NOMBRE, "3")
    assert resultat["jules"] == "Qu'est-ce qui te fait penser ça ? Reprends l'énoncé étape par étape."


def test_trois_tentatives_fausses_explication_et_a_revoir(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]
    for _ in range(2):
        resultat = module.tentative(session, B_EXERCICE_NOMBRE, "0")
        assert resultat["juste"] is False
        assert resultat["explication"] is None
    dernier = module.tentative(session, B_EXERCICE_NOMBRE, "0")
    assert dernier["juste"] is False
    assert dernier["tentatives"] == 3
    assert dernier["explication"] == "La racine carrée de 25 est 5 car 5 × 5 = 25."
    assert dernier["progression"]["blocs"][B_EXERCICE_NOMBRE]["etat"] == "a_revoir"


def test_reponse_et_explication_jamais_exposees_avant_la_condition(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})
    ouverture = client.post(f"/api/eleve/cours/lecons/{NOTION}/ouvrir").json()
    session = ouverture["session"]
    lue = client.get(f"/api/eleve/cours/sessions/{session}").json()
    indice = client.post(f"/api/eleve/cours/sessions/{session}/blocs/{B_EXERCICE_NOMBRE}/indice").json()
    fausse = client.post(
        f"/api/eleve/cours/sessions/{session}/blocs/{B_EXERCICE_NOMBRE}/tentative", json={"reponse": 999}
    ).json()
    interdits = ["25 est 5", "5 × 5", "évoque que le carré", "criteres", "tolerance"]
    for donnees in (ouverture, lue, indice, fausse):
        texte = json.dumps(donnees, ensure_ascii=False)
        for mot in interdits:
            assert mot not in texte
    assert fausse["explication"] is None


# --- blocs sans tentative (fait) -----------------------------------------------------


def test_fait_sur_bloc_sans_tentative(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]
    resultat = module.fait(session, B_OBJECTIFS)
    assert resultat["progression"]["blocs"][B_OBJECTIFS]["etat"] == "fait"
    assert resultat["progression"]["bloc_courant"] == B_TEXTE  # avance au bloc suivant


def test_fait_sur_bloc_avec_tentative_refuse(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]
    with pytest.raises(ValueError):
        module.fait(session, B_EXERCICE_NOMBRE)


def test_tentative_sur_bloc_sans_tentative_refuse(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]
    with pytest.raises(ValueError):
        module.tentative(session, B_OBJECTIFS, "peu importe")


# --- fin de lecon : evenement suivi + integration epreuve ---------------------------


def test_fin_de_lecon_ecrit_le_suivi_et_alimente_l_epreuve(tuteur):
    module = tuteur.module("cours")
    ouverture = module.ouvrir(NOTION)
    session, conv_id = ouverture["session"], ouverture["conversation"]

    assert module.fait(session, B_OBJECTIFS)["progression"]["blocs"][B_OBJECTIFS]["etat"] == "fait"
    assert module.fait(session, B_TEXTE)["progression"]["blocs"][B_TEXTE]["etat"] == "fait"
    assert module.tentative(session, B_EXERCICE_NOMBRE, 5)["juste"] is True
    assert module.tentative(session, B_EXERCICE_QCM, 0)["juste"] is True
    assert module.tentative(session, B_QUESTION_OUVERTE, "Un carré est toujours positif ou nul.")["juste"] is None
    fin = module.tentative(session, B_SYNTHESE, "La racine carrée inverse le carré.")
    assert fin["juste"] is None
    assert fin["progression"]["termine"] is True

    tuteur.attendre_fond()
    evenements = tuteur.stockage.evenements("suivi")
    ev = next(e for e in evenements if e["donnees"].get("notion") == TITRE_NOTION)
    assert ev["donnees"]["matiere"] == NOM_MATIERE
    assert ev["donnees"]["statut"] == "compris"  # tout reussi, rien a revoir

    # vieillie de 4 jours : l'epreuve sans aide doit pouvoir la reprendre (voir tests/test_epreuve.py)
    il_y_a_4_jours = (datetime.now().astimezone() - timedelta(days=4)).isoformat(timespec="seconds")
    with tuteur.stockage._verrou, tuteur.stockage._cx:
        tuteur.stockage._cx.execute(
            "UPDATE evenements SET horodatage = ? WHERE type = 'suivi' AND conversation = ?",
            (il_y_a_4_jours, conv_id),
        )
    candidates = tuteur.module("epreuve").candidates()
    assert any(c["matiere"] == NOM_MATIERE and c["notion"] == TITRE_NOTION for c in candidates)


def test_fin_de_lecon_avec_un_bloc_a_revoir_donne_en_cours(tuteur):
    module = tuteur.module("cours")
    session = module.ouvrir(NOTION)["session"]
    module.fait(session, B_OBJECTIFS)
    module.fait(session, B_TEXTE)
    for _ in range(3):
        module.tentative(session, B_EXERCICE_NOMBRE, "0")  # jamais bon -> a_revoir
    module.tentative(session, B_EXERCICE_QCM, 0)
    module.tentative(session, B_QUESTION_OUVERTE, "réponse")
    fin = module.tentative(session, B_SYNTHESE, "synthese")
    assert fin["progression"]["termine"] is True
    tuteur.attendre_fond()
    ev = next(e for e in tuteur.stockage.evenements("suivi") if e["donnees"].get("notion") == TITRE_NOTION)
    assert ev["donnees"]["statut"] == "en_cours"


# --- erreurs 404 / 400 exposees par l'API --------------------------------------------


def test_erreurs_api_404_et_400(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})
    assert client.post(f"/api/eleve/cours/lecons/{NOTION_SANS_LECON}/ouvrir").status_code == 404
    assert client.get("/api/eleve/cours/sessions/session-inconnue").status_code == 404
    reponse_tentative = client.post("/api/eleve/cours/sessions/session-inconnue/blocs/0/tentative", json={"reponse": 1})
    assert reponse_tentative.status_code == 404
    assert client.post("/api/eleve/cours/sessions/session-inconnue/blocs/0/indice").status_code == 404
    assert client.post("/api/eleve/cours/sessions/session-inconnue/blocs/0/fait").status_code == 404

    ouverture = client.post(f"/api/eleve/cours/lecons/{NOTION}/ouvrir").json()
    session = ouverture["session"]
    assert (
        client.post(f"/api/eleve/cours/sessions/{session}/blocs/99/tentative", json={"reponse": 1}).status_code == 404
    )
    assert client.post(f"/api/eleve/cours/sessions/{session}/blocs/99/indice").status_code == 404
    assert client.post(f"/api/eleve/cours/sessions/{session}/blocs/99/fait").status_code == 404
    assert (
        client.post(
            f"/api/eleve/cours/sessions/{session}/blocs/{B_OBJECTIFS}/tentative", json={"reponse": 1}
        ).status_code
        == 400
    )
    assert client.post(f"/api/eleve/cours/sessions/{session}/blocs/{B_EXERCICE_NOMBRE}/fait").status_code == 400


# --- acces refuse sans code eleve -----------------------------------------------------


def test_acces_refuse_sans_code_eleve(client_protege):
    client = client_protege
    assert client.get("/api/eleve/cours/parcours").status_code == 401
    assert client.post(f"/api/eleve/cours/lecons/{NOTION}/ouvrir").status_code == 401


# --- exemples de reponses JSON via l'API (parcours -> ouvrir -> session -> tentative) ------


def test_api_parcours_ouvrir_session_tentative_indice_fait(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})

    parcours = client.get("/api/eleve/cours/parcours", params={"matiere": MATIERE_ID}).json()
    assert parcours["matiere"] == MATIERE_ID
    assert any(n["id"] == NOTION and n["lecon"] for n in parcours["notions"])

    ouverture = client.post(f"/api/eleve/cours/lecons/{NOTION}/ouvrir").json()
    session = ouverture["session"]
    assert ouverture["progression"]["bloc_courant"] == 0

    lue = client.get(f"/api/eleve/cours/sessions/{session}").json()
    assert lue["lecon"]["titre"] == TITRE_LECON
    assert lue["session"] == session

    indice = client.post(f"/api/eleve/cours/sessions/{session}/blocs/{B_EXERCICE_NOMBRE}/indice").json()
    assert indice["restants"] == 1

    tentative = client.post(
        f"/api/eleve/cours/sessions/{session}/blocs/{B_EXERCICE_NOMBRE}/tentative", json={"reponse": 5}
    ).json()
    assert tentative["juste"] is True
    assert tentative["explication"]

    fait = client.post(f"/api/eleve/cours/sessions/{session}/blocs/{B_OBJECTIFS}/fait").json()
    assert fait["progression"]["blocs"][B_OBJECTIFS]["etat"] == "fait"
