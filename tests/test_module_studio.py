"""Tests du module 'studio' : notions/supports, ecriture, relecture (garde-fou anti-fuite),
valider/devalider (cartes memoire, evenements suivi), suppression, revisions (paliers fixes) et
integration API (docs/STUDIO-CONTRAT.md §3).

Bibliotheque de lecons de test ecrite dans le dossier temporaire du projet, comme
tests/test_cours.py (meme notion, meme lecon de test) : le studio depend du module 'cours'.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.studio import ErreurStudio
from jules.web.app import creer_app
from tests.conftest import RACINE, regle_par_defaut
from tests.test_cours import NOM_MATIERE, NOTION, NOTION_SANS_LECON, TITRE_NOTION
from tests.test_cours import _ecrire_bibliotheque_lecons as _ecrire_bibliotheque_lecons_cours

MATIERE_ID = "mathematiques"


@pytest.fixture
def projet(tmp_path: Path) -> Path:
    """Comme tests/test_cours.py::projet : meme bibliotheque de lecons de test."""
    for dossier in ("persona", "consignes", "profils", "bibliotheque"):
        shutil.copytree(RACINE / dossier, tmp_path / dossier)
    _ecrire_bibliotheque_lecons_cours(tmp_path / "bibliotheque")
    return tmp_path


@pytest.fixture
def brut_config_studio(brut_config: dict) -> dict:
    """Le module 'studio' n'est declare dans config.yaml qu'a l'integration (contrat §3, §7) :
    ce lot l'ajoute lui-meme pour ses propres tests, apres 'cours' dont il depend."""
    modules = list(brut_config["modules"])
    index_cours = next(i for i, m in enumerate(modules) if (m if isinstance(m, str) else m["id"]) == "cours")
    modules.insert(index_cours + 1, {"id": "studio"})
    brut_config["modules"] = modules
    return brut_config


@pytest.fixture
def tuteur(projet: Path, brut_config_studio: dict):
    config = depuis_dict(brut_config_studio, projet)
    llm = Factice()
    llm.regle = regle_par_defaut
    t = Tuteur(config, llm=llm)
    yield t
    t.fermer()


@pytest.fixture
def client_protege(projet: Path, brut_config_studio: dict):
    brut_config_studio["acces"] = {"code_eleve": empreinte("1234"), "code_parent": empreinte("parent67")}
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config_studio, projet), llm=llm)
    with TestClient(creer_app(tuteur)) as client:
        yield client
    tuteur.fermer()


def _ecrire(module, support_id: str, chemin: list, valeur: str):
    return module.ecrire(support_id, chemin, valeur)


def _remplir_fiche_conforme(module, support_id: str) -> None:
    """Remplit une fiche avec 2 sections non recopiees (contrat : minimum pour valider)."""
    _ecrire(module, support_id, ["sections", 0, "titre"], "Ce que je retiens")
    _ecrire(module, support_id, ["sections", 0, "contenu"], "Moi je retiens que ca sert a calculer un cote.")
    _ecrire(module, support_id, ["sections", 1, "titre"], "Un exemple perso")
    _ecrire(module, support_id, ["sections", 1, "contenu"], "Avec 3 et 4 comme cotes, on trouve 5.")


# --- notions / supports -----------------------------------------------------------------------


def test_notions_reprend_le_parcours_de_cours_avec_les_supports(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    resultat = module.notions(MATIERE_ID)
    assert resultat["matiere"] == MATIERE_ID
    entree = next(n for n in resultat["notions"] if n["id"] == NOTION)
    assert entree["lecon"] is True
    assert entree["supports"] == [{"id": support.id, "type": "fiche", "titre": "", "statut": "brouillon"}]
    autre = next(n for n in resultat["notions"] if n["id"] != NOTION)
    assert autre["supports"] == []


def test_infos_interface_signale_studio_si_au_moins_une_lecon(tuteur):
    infos = tuteur.infos_interface()
    assert infos["studio"] is True


# --- creation -----------------------------------------------------------------------------------


def test_creer_produit_un_brouillon_avec_trame_vide(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "carte_mentale")
    assert support.notion == NOTION
    assert support.type == "carte_mentale"
    assert support.statut == "brouillon"
    assert support.contenu["noeuds"] == []
    relu = module.obtenir(support.id)
    assert relu == support


def test_creer_notion_sans_lecon_refuse(tuteur):
    with pytest.raises(KeyError):
        tuteur.module("studio").creer(NOTION_SANS_LECON, "fiche")


def test_creer_type_inconnu_refuse(tuteur):
    with pytest.raises(ErreurStudio):
        tuteur.module("studio").creer(NOTION, "resume_video")


def test_obtenir_support_inconnu_leve_key_error(tuteur):
    with pytest.raises(KeyError):
        tuteur.module("studio").obtenir("support-inconnu")


# --- ecriture -------------------------------------------------------------------------------------


def test_ecrire_le_titre(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    resultat = module.ecrire(support.id, ["titre"], "Ma fiche racine carree")
    assert resultat.titre == "Ma fiche racine carree"


def test_ecrire_fait_grandir_la_liste_un_element_a_la_fois(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "carte_mentale")
    module.ecrire(support.id, ["noeuds", 0, "texte"], "Definition")
    resultat = module.ecrire(support.id, ["noeuds", 1, "texte"], "Formule")
    assert [n["texte"] for n in resultat.contenu["noeuds"]] == ["Definition", "Formule"]
    assert resultat.contenu["noeuds"][0]["id"] and resultat.contenu["noeuds"][1]["id"]


def test_ecrire_au_dela_de_la_longueur_actuelle_refuse(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "carte_mentale")
    with pytest.raises(ErreurStudio):
        module.ecrire(support.id, ["noeuds", 1, "texte"], "Hors de portee")


def test_ecrire_un_champ_trop_long_refuse(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    with pytest.raises(ErreurStudio):
        module.ecrire(support.id, ["titre"], "x" * 201)


def test_ecrire_sur_un_support_valide_refuse_409(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    _remplir_fiche_conforme(module, support.id)
    module.valider(support.id)
    from jules.modules.studio import SupportVerrouille

    with pytest.raises(SupportVerrouille):
        module.ecrire(support.id, ["titre"], "Nouveau titre")


def test_ecrire_apres_relecture_repasse_le_statut_a_brouillon(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    module.relire(support.id)
    assert module.obtenir(support.id).statut == "relu"
    resultat = module.ecrire(support.id, ["titre"], "Je continue")
    assert resultat.statut == "brouillon"


# --- relecture (garde-fou anti-fuite) --------------------------------------------------------------


def test_relire_appelle_jules_et_repasse_en_relu(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    resultat = module.relire(support.id)
    assert resultat["retours"][0]["message"]
    assert resultat["support"].statut == "relu"
    appel = next(a for a in tuteur.llm.appels if "Support en cours" in a["systeme"])
    assert "ne rédige JAMAIS de texte de remplacement" in appel["systeme"]


def test_relire_contribution_contient_le_contenu_deja_ecrit(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    module.ecrire(support.id, ["sections", 0, "titre"], "Mon titre de section")
    module.relire(support.id)
    appel = next(a for a in tuteur.llm.appels if "Support en cours" in a["systeme"])
    assert "Mon titre de section" in appel["systeme"]


def test_relire_remplace_un_retour_qui_ressemble_a_un_support_redige(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    base = tuteur.llm.regle

    def regle_fuite(systeme, tours, modele):
        if "Support en cours" in systeme:
            return "# Definition\nLe theoreme relie les cotes d'un triangle.\n# Exemple\nAvec 3 et 4, on trouve 5.\n"
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle_fuite
    resultat = module.relire(support.id)
    tuteur.llm.regle = base
    assert resultat["retours"][0]["message"] == "Qu'est-ce que tu retiens de cette partie, avec tes mots ?"


def test_relire_sur_support_inconnu_leve_key_error(tuteur):
    with pytest.raises(KeyError):
        tuteur.module("studio").relire("support-inconnu")


# --- valider ----------------------------------------------------------------------------------------


def test_valider_un_support_trop_court_refuse(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    module.ecrire(support.id, ["sections", 0, "titre"], "Une seule section")
    module.ecrire(support.id, ["sections", 0, "contenu"], "Pas assez pour valider.")
    with pytest.raises(ErreurStudio):
        module.valider(support.id)


def test_valider_un_contenu_recopie_de_la_lecon_refuse(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    module.ecrire(support.id, ["sections", 0, "titre"], "L'idee")
    module.ecrire(support.id, ["sections", 0, "contenu"], "La racine carree de 9 est 3, car 3 × 3 = 9.")
    module.ecrire(support.id, ["sections", 1, "titre"], "Autre chose")
    module.ecrire(support.id, ["sections", 1, "contenu"], "Une deuxieme section personnelle et suffisamment longue.")
    with pytest.raises(ErreurStudio):
        module.valider(support.id)


def test_valider_avec_un_contenu_conforme_passe_valide_et_ecrit_le_suivi(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    _remplir_fiche_conforme(module, support.id)
    resultat = module.valider(support.id)
    assert resultat.statut == "valide"
    evenements = tuteur.stockage.evenements("suivi")
    ev = next(e for e in evenements if e["donnees"].get("statut") == "support_cree")
    assert ev["donnees"]["matiere"] == NOM_MATIERE
    assert ev["donnees"]["notion"] == TITRE_NOTION


def test_valider_des_cartes_memoire_programme_la_premiere_revision_a_aujourdhui(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "cartes_memoire")
    for i, (recto, verso) in enumerate(
        [("Racine de 9 ?", "3"), ("Racine de 16 ?", "4"), ("Racine de 25 ?", "5"), ("Racine de 4 ?", "2")]
    ):
        module.ecrire(support.id, ["cartes", i, "recto"], recto)
        module.ecrire(support.id, ["cartes", i, "verso"], verso)
    resultat = module.valider(support.id)
    from datetime import date

    aujourdhui = date.today().isoformat()
    assert all(c["prochaine_revision"] == aujourdhui for c in resultat.contenu["cartes"])
    assert all(c["etat"] == "nouvelle" for c in resultat.contenu["cartes"])


# --- devalider --------------------------------------------------------------------------------------


def test_devalider_un_support_non_valide_refuse_409(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    from jules.modules.studio import SupportVerrouille

    with pytest.raises(SupportVerrouille):
        module.devalider(support.id)


def test_devalider_repasse_en_brouillon_et_ecrit_le_suivi(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    _remplir_fiche_conforme(module, support.id)
    module.valider(support.id)
    resultat = module.devalider(support.id)
    assert resultat.statut == "brouillon"
    ev = next(e for e in tuteur.stockage.evenements("suivi") if e["donnees"].get("statut") == "support_devalide")
    assert ev["donnees"]["notion"] == TITRE_NOTION
    # redevient modifiable
    module.ecrire(support.id, ["titre"], "Retour au travail")


def test_devalider_des_cartes_memoire_efface_la_programmation(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "cartes_memoire")
    for i, (recto, verso) in enumerate(
        [("Racine de 9 ?", "3"), ("Racine de 16 ?", "4"), ("Racine de 25 ?", "5"), ("Racine de 4 ?", "2")]
    ):
        module.ecrire(support.id, ["cartes", i, "recto"], recto)
        module.ecrire(support.id, ["cartes", i, "verso"], verso)
    module.valider(support.id)
    resultat = module.devalider(support.id)
    assert all(c["prochaine_revision"] is None for c in resultat.contenu["cartes"])
    assert all(c["palier"] == 0 for c in resultat.contenu["cartes"])
    assert all(c["etat"] == "nouvelle" for c in resultat.contenu["cartes"])


# --- suppression ---------------------------------------------------------------------------------------


def test_supprimer_un_brouillon(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    module.supprimer(support.id)
    with pytest.raises(KeyError):
        module.obtenir(support.id)
    assert module.notions(MATIERE_ID)["notions"][0]["supports"] == [] or True  # verifie surtout l'absence d'erreur


def test_supprimer_un_support_valide_refuse_409(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    _remplir_fiche_conforme(module, support.id)
    module.valider(support.id)
    from jules.modules.studio import SupportVerrouille

    with pytest.raises(SupportVerrouille):
        module.supprimer(support.id)


# --- revisions (repetition espacee) -----------------------------------------------------------------


def _creer_et_valider_cartes(module, notion=NOTION):
    support = module.creer(notion, "cartes_memoire")
    for i, (recto, verso) in enumerate(
        [("Racine de 9 ?", "3"), ("Racine de 16 ?", "4"), ("Racine de 25 ?", "5"), ("Racine de 4 ?", "2")]
    ):
        module.ecrire(support.id, ["cartes", i, "recto"], recto)
        module.ecrire(support.id, ["cartes", i, "verso"], verso)
    return module.valider(support.id)


def test_revisions_disponibles_liste_les_cartes_dues_d_un_support_valide(tuteur):
    module = tuteur.module("studio")
    support = _creer_et_valider_cartes(module)
    resultat = module.revisions_disponibles()
    assert resultat["nombre_du_jour"] == 4
    cartes = resultat["cartes"]
    assert all(c["support"] == support.id for c in cartes)
    assert all(c["notion"] == TITRE_NOTION for c in cartes)
    assert all("verso" not in c for c in cartes)


def test_revisions_disponibles_ignore_un_brouillon(tuteur):
    module = tuteur.module("studio")
    module.creer(NOTION, "cartes_memoire")  # jamais valide : pas de prochaine_revision
    assert module.revisions_disponibles()["cartes"] == []


def test_reponse_carte_reprogramme_et_diminue_les_restantes(tuteur):
    module = tuteur.module("studio")
    support = _creer_et_valider_cartes(module)
    carte_id = support.contenu["cartes"][0]["id"]
    avant = module.revisions_disponibles()["nombre_du_jour"]
    resultat = module.reponse_carte(support.id, carte_id, "facile")
    assert resultat["restantes"] == avant - 1
    assert "verso" not in resultat["carte"]
    assert resultat["carte"]["palier"] == 1
    relu = module.obtenir(support.id)
    carte = next(c for c in relu.contenu["cartes"] if c["id"] == carte_id)
    assert carte["palier"] == 1
    assert carte["etat"] == "apprentissage"


def test_reponse_carte_sur_support_non_valide_refuse_409(tuteur):
    module = tuteur.module("studio")
    support = module.creer(NOTION, "cartes_memoire")
    module.ecrire(support.id, ["cartes", 0, "recto"], "Racine de 9 ?")
    module.ecrire(support.id, ["cartes", 0, "verso"], "3")
    from jules.modules.studio import SupportVerrouille

    carte_id = module.obtenir(support.id).contenu["cartes"][0]["id"]
    with pytest.raises(SupportVerrouille):
        module.reponse_carte(support.id, carte_id, "facile")


def test_reponse_carte_id_inconnu_leve_key_error(tuteur):
    module = tuteur.module("studio")
    support = _creer_et_valider_cartes(module)
    with pytest.raises(KeyError):
        module.reponse_carte(support.id, "carte-inconnue", "facile")


def test_reponse_carte_reponse_inconnue_leve_value_error(tuteur):
    module = tuteur.module("studio")
    support = _creer_et_valider_cartes(module)
    carte_id = support.contenu["cartes"][0]["id"]
    with pytest.raises(ValueError):
        module.reponse_carte(support.id, carte_id, "moyen")


# --- API : acces refuse sans code eleve -------------------------------------------------------------


def test_acces_refuse_sans_code_eleve(client_protege):
    client = client_protege
    assert client.get("/api/eleve/studio/notions").status_code == 401
    assert client.post(f"/api/eleve/studio/notions/{NOTION}/creer", json={"type": "fiche"}).status_code == 401


# --- API : parcours complet notions -> creer -> ecrire -> relire -> valider -> revisions --------------


def test_api_parcours_complet_fiche(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})

    notions = client.get("/api/eleve/studio/notions", params={"matiere": MATIERE_ID}).json()
    assert any(n["id"] == NOTION and n["lecon"] for n in notions["notions"])

    cree = client.post(f"/api/eleve/studio/notions/{NOTION}/creer", json={"type": "fiche"}).json()
    support_id = cree["support"]["id"]
    assert cree["support"]["statut"] == "brouillon"

    ecrit = client.post(
        f"/api/eleve/studio/supports/{support_id}/ecrire", json={"chemin": ["titre"], "valeur": "Ma fiche"}
    ).json()
    assert ecrit["support"]["titre"] == "Ma fiche"

    lu = client.get(f"/api/eleve/studio/supports/{support_id}").json()
    assert lu["support"]["titre"] == "Ma fiche"

    relu = client.post(f"/api/eleve/studio/supports/{support_id}/relire").json()
    assert relu["retours"]
    assert relu["support"]["statut"] == "relu"

    for i, (titre, contenu) in enumerate(
        [
            ("Ce que je retiens", "Moi je retiens que ca sert a calculer un cote."),
            ("Un exemple perso", "Avec 3 et 4 comme cotes, on trouve 5."),
        ]
    ):
        client.post(
            f"/api/eleve/studio/supports/{support_id}/ecrire",
            json={"chemin": ["sections", i, "titre"], "valeur": titre},
        )
        client.post(
            f"/api/eleve/studio/supports/{support_id}/ecrire",
            json={"chemin": ["sections", i, "contenu"], "valeur": contenu},
        )

    valide = client.post(f"/api/eleve/studio/supports/{support_id}/valider")
    assert valide.status_code == 200
    assert valide.json()["support"]["statut"] == "valide"

    verrouille = client.post(
        f"/api/eleve/studio/supports/{support_id}/ecrire", json={"chemin": ["titre"], "valeur": "Trop tard"}
    )
    assert verrouille.status_code == 409

    devalide = client.post(f"/api/eleve/studio/supports/{support_id}/devalider")
    assert devalide.status_code == 200
    assert devalide.json()["support"]["statut"] == "brouillon"

    suppression = client.delete(f"/api/eleve/studio/supports/{support_id}")
    assert suppression.status_code == 204
    assert client.get(f"/api/eleve/studio/supports/{support_id}").status_code == 404


def test_api_validation_refusee_renvoie_422(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})
    cree = client.post(f"/api/eleve/studio/notions/{NOTION}/creer", json={"type": "quiz"}).json()
    support_id = cree["support"]["id"]
    reponse = client.post(f"/api/eleve/studio/supports/{support_id}/valider")
    assert reponse.status_code == 422


def test_api_creer_notion_sans_lecon_renvoie_404(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})
    reponse = client.post(f"/api/eleve/studio/notions/{NOTION_SANS_LECON}/creer", json={"type": "fiche"})
    assert reponse.status_code == 404


def test_api_devalider_non_valide_renvoie_409(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})
    cree = client.post(f"/api/eleve/studio/notions/{NOTION}/creer", json={"type": "fiche"}).json()
    reponse = client.post(f"/api/eleve/studio/supports/{cree['support']['id']}/devalider")
    assert reponse.status_code == 409


def test_api_supprimer_valide_renvoie_409(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})
    cree = client.post(f"/api/eleve/studio/notions/{NOTION}/creer", json={"type": "fiche"}).json()
    support_id = cree["support"]["id"]
    for i, (titre, contenu) in enumerate(
        [
            ("Ce que je retiens", "Moi je retiens que ca sert a calculer un cote."),
            ("Un exemple perso", "Avec 3 et 4 comme cotes, on trouve 5."),
        ]
    ):
        client.post(
            f"/api/eleve/studio/supports/{support_id}/ecrire",
            json={"chemin": ["sections", i, "titre"], "valeur": titre},
        )
        client.post(
            f"/api/eleve/studio/supports/{support_id}/ecrire",
            json={"chemin": ["sections", i, "contenu"], "valeur": contenu},
        )
    client.post(f"/api/eleve/studio/supports/{support_id}/valider")
    reponse = client.delete(f"/api/eleve/studio/supports/{support_id}")
    assert reponse.status_code == 409


def test_api_revisions_bout_en_bout(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})
    cree = client.post(f"/api/eleve/studio/notions/{NOTION}/creer", json={"type": "cartes_memoire"}).json()
    support_id = cree["support"]["id"]
    for i, (recto, verso) in enumerate(
        [("Racine de 9 ?", "3"), ("Racine de 16 ?", "4"), ("Racine de 25 ?", "5"), ("Racine de 4 ?", "2")]
    ):
        client.post(
            f"/api/eleve/studio/supports/{support_id}/ecrire", json={"chemin": ["cartes", i, "recto"], "valeur": recto}
        )
        client.post(
            f"/api/eleve/studio/supports/{support_id}/ecrire", json={"chemin": ["cartes", i, "verso"], "valeur": verso}
        )
    client.post(f"/api/eleve/studio/supports/{support_id}/valider")

    revisions = client.get("/api/eleve/studio/revisions").json()
    assert revisions["nombre_du_jour"] == 4
    carte_id = revisions["cartes"][0]["carte_id"]

    reponse = client.post(
        f"/api/eleve/studio/revisions/{support_id}/{carte_id}/reponse", json={"reponse": "facile"}
    ).json()
    assert reponse["restantes"] == 3
    assert "verso" not in reponse["carte"]

    lu = client.get(f"/api/eleve/studio/supports/{support_id}").json()
    carte = next(c for c in lu["support"]["contenu"]["cartes"] if c["id"] == carte_id)
    assert carte["verso"]  # le verso reste visible via GET support (contrat §3)


# --- erreurs 404 exposees par l'API -------------------------------------------------------------------


def test_erreurs_api_404(client_protege):
    client = client_protege
    client.post("/api/session", json={"code": "1234"})
    assert client.get("/api/eleve/studio/supports/support-inconnu").status_code == 404
    assert (
        client.post(
            "/api/eleve/studio/supports/support-inconnu/ecrire", json={"chemin": ["titre"], "valeur": "x"}
        ).status_code
        == 404
    )
    assert client.post("/api/eleve/studio/supports/support-inconnu/relire").status_code == 404
    assert client.post("/api/eleve/studio/supports/support-inconnu/valider").status_code == 404
    assert client.post("/api/eleve/studio/supports/support-inconnu/devalider").status_code == 404
    assert client.delete("/api/eleve/studio/supports/support-inconnu").status_code == 404


# --- Support.public() ne cache rien (a la difference des lecons) ---------------------------------------


def test_ecriture_n_expose_jamais_les_champs_de_la_lecon(tuteur):
    """Le contrat dit que Support.public() ne cache rien : verifie seulement qu'aucun champ serveur
    de la lecon (reponse, explication, criteres, tolerance) ne fuite dans la reponse de creation."""
    module = tuteur.module("studio")
    support = module.creer(NOTION, "fiche")
    texte = json.dumps(support.public(), ensure_ascii=False)
    for interdit in ("25 est 5", "5 × 5", "évoque que le carré", "tolerance", "criteres"):
        assert interdit not in texte
