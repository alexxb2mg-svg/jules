"""Etape 3 des extensions : les points d'accroche `bloc_consulte` et `fin_de_seance`
(voir docs/EXTENSIONS.md, jules/modules/base.py, jules/moteur.py)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.extensions import ErreurExtension, charger_extensions, lire_extension
from jules.llm.factice import Brique as Factice
from jules.modules.base import Module
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import regle_par_defaut

RACINE = Path(__file__).resolve().parents[1]
EXEMPLE = "exemple-observateur"


class Espion(Module):
    """Module de test : retient ce que les points d'accroche lui donnent."""

    id = "espion"

    def __init__(self, tuteur, reglages):
        super().__init__(tuteur, reglages)
        self.appels: list[tuple] = []

    def bloc_consulte(self, conv, adresse, notion=None):
        self.appels.append(("bloc_consulte", conv.id if conv else None, adresse, notion))

    def fin_de_seance(self, conv):
        self.appels.append(("fin_de_seance", conv.id if conv else None))


class Casse(Module):
    id = "casse"

    def bloc_consulte(self, conv, adresse, notion=None):
        raise RuntimeError("module en panne")

    def fin_de_seance(self, conv):
        raise RuntimeError("module en panne")


class Muet(Module):
    """N'implemente aucun point d'accroche : ne doit rien casser."""

    id = "muet"


def evenements(tuteur: Tuteur) -> list[dict]:
    tuteur.attendre_fond()
    return tuteur.stockage.evenements("observateur-exemple")[::-1]  # du plus ancien au plus recent


@pytest.fixture
def avec_exemple(projet, brut_config):
    """Un tuteur (et son client web) ou l'extension d'exemple est activee."""
    brut_config["acces"] = {"code_eleve": empreinte("1234")}
    brut_config["extensions"] = [*brut_config["extensions"], EXEMPLE]
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    client = TestClient(creer_app(tuteur))
    client.post("/api/session", json={"code": "1234"})
    yield tuteur, client
    tuteur.fermer()


# --- le contrat : valeur par defaut -----------------------------------------------------


def test_comportement_par_defaut_ne_fait_rien(tuteur):
    module = Muet(tuteur, {})
    assert module.bloc_consulte(None, "fiche/x") is None
    assert module.fin_de_seance(None) is None


def test_module_muet_et_module_casse_ne_genent_personne(tuteur):
    espion = Espion(tuteur, {})
    tuteur.modules += [Muet(tuteur, {}), Casse(tuteur, {}), espion]
    tuteur.bloc_consulte("fiche/formule", "fractions")
    assert tuteur.fin_de_seance() is True
    tuteur.attendre_fond()
    assert espion.appels == [("bloc_consulte", None, "fiche/formule", "fractions"), ("fin_de_seance", None)]


# --- les modules des extensions actives ---------------------------------------------------


def test_le_depot_n_active_pas_l_exemple():
    ids = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))["extensions"]
    assert EXEMPLE not in ids
    assert EXEMPLE in charger_extensions(RACINE / "extensions", [EXEMPLE])  # mais il est valide


def test_module_d_extension_absent_si_extension_non_activee(tuteur):
    assert tuteur.module("exemple_observateur") is None


def test_module_d_extension_charge_apres_les_modules_de_la_config(avec_exemple):
    tuteur, _ = avec_exemple
    ids = [m.id for m in tuteur.modules]
    assert "exemple_observateur" in ids
    assert ids.index("exemple_observateur") > ids.index("modes")


def test_manifeste_qui_fournit_un_module_sans_fichier_refuse(tmp_path):
    dossier = tmp_path / "sans-code"
    dossier.mkdir()
    (dossier / "extension.yaml").write_text(
        'id: sans-code\ntitre: "x"\nversion: "1"\nlicence: MIT\nfournit:\n  modules: [absent]\n', encoding="utf-8"
    )
    with pytest.raises(ErreurExtension, match=r"absent\.py"):
        lire_extension(dossier)


def test_module_d_extension_qui_ne_se_charge_pas_est_ecarte(projet, brut_config):
    dossier = projet / "extensions" / "casse-au-chargement"
    dossier.mkdir()
    (dossier / "extension.yaml").write_text(
        'id: casse-au-chargement\ntitre: "x"\nversion: "1"\nlicence: MIT\nfournit:\n  modules: [boum]\n',
        encoding="utf-8",
    )
    (dossier / "boum.py").write_text("raise RuntimeError('boum')\n", encoding="utf-8")
    brut_config["extensions"] = ["casse-au-chargement"]
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    try:
        assert [m.id for m in tuteur.modules] == [m["id"] for m in brut_config["modules"] if m.get("actif", True)]
    finally:
        tuteur.fermer()


# --- bloc_consulte : du clic a l'evenement --------------------------------------------------


def test_clic_sur_un_bloc_arrive_au_module_de_l_extension(avec_exemple):
    tuteur, client = avec_exemple
    r = client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/formule", "notion": "thales"})
    assert r.status_code == 200
    r = client.post("/api/seance/bloc_consulte", json={"adresse": "carte/n1"})
    assert r.status_code == 200
    assert [(e["donnees"]["point"], e["donnees"]["adresse"], e["donnees"]["notion"]) for e in evenements(tuteur)] == [
        ("bloc_consulte", "fiche/formule", "thales"),
        ("bloc_consulte", "carte/n1", None),
    ]


def test_bloc_consulte_avec_conversation_donne_la_conversation(avec_exemple):
    tuteur, client = avec_exemple
    conv = tuteur.stockage.creer_conversation("libre")
    client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/a", "conversation": conv.id})
    client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/b", "conversation": "inconnue"})
    assert [e["conversation"] for e in evenements(tuteur)] == [conv.id, None]


@pytest.mark.parametrize(
    "adresse", ["", "fiche", "fiche/", "Fiche/x", "fiche/x y", "fiche/" + "a" * 200, "../etc/passwd"]
)
def test_adresse_mal_formee_refusee(avec_exemple, adresse):
    tuteur, client = avec_exemple
    assert client.post("/api/seance/bloc_consulte", json={"adresse": adresse}).status_code == 422
    assert evenements(tuteur) == []


def test_les_deux_routes_demandent_le_code_eleve(avec_exemple):
    tuteur, _ = avec_exemple
    anonyme = TestClient(creer_app(tuteur))
    assert anonyme.post("/api/seance/bloc_consulte", json={"adresse": "fiche/x"}).status_code == 401
    assert anonyme.post("/api/seance/fin").status_code == 401


def test_le_coeur_n_appelle_aucun_modele_d_ia(avec_exemple):
    tuteur, client = avec_exemple
    client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/x"})
    client.post("/api/seance/fin")
    tuteur.attendre_fond()
    assert tuteur.llm.appels == []


# --- fin_de_seance -----------------------------------------------------------------------


def test_signal_de_fermeture_clot_la_seance_une_seule_fois(avec_exemple):
    tuteur, client = avec_exemple
    client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/x"})
    assert client.post("/api/seance/fin").json() == {"ok": True}
    assert client.post("/api/seance/fin").json() == {"ok": False}  # pas de seance ouverte : rien
    assert [e["donnees"]["point"] for e in evenements(tuteur)] == ["bloc_consulte", "fin_de_seance"]


def test_fermeture_sans_seance_ne_fait_rien(avec_exemple):
    tuteur, client = avec_exemple
    assert client.post("/api/seance/fin").json() == {"ok": False}
    assert evenements(tuteur) == []


def test_fin_de_seance_donne_la_derniere_conversation(avec_exemple):
    tuteur, client = avec_exemple
    conv = tuteur.stockage.creer_conversation("libre")
    tuteur.echanger(conv.id, "Bonjour")
    client.post("/api/seance/fin")
    assert [(e["donnees"]["point"], e["conversation"]) for e in evenements(tuteur)] == [("fin_de_seance", conv.id)]


def test_inactivite_detectee_par_la_veille(avec_exemple):
    tuteur, client = avec_exemple
    instant = [1000.0]
    tuteur._horloge = lambda: instant[0]
    client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/x"})
    instant[0] += tuteur.inactivite_s - 1
    assert tuteur.verifier_inactivite() is False  # pas encore
    instant[0] += 2
    assert tuteur.verifier_inactivite() is True
    assert tuteur.verifier_inactivite() is False  # deja close
    assert [e["donnees"]["point"] for e in evenements(tuteur)] == ["bloc_consulte", "fin_de_seance"]


def test_le_planificateur_lance_la_veille_a_chaque_tour(avec_exemple):
    from jules.planificateur import Planificateur

    tuteur, client = avec_exemple
    instant = [1000.0]
    tuteur._horloge = lambda: instant[0]
    client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/x"})
    planificateur = Planificateur([], tuteur.stockage, veilles=[tuteur.verifier_inactivite])
    planificateur.tourner_une_fois()
    instant[0] += tuteur.inactivite_s + 1
    planificateur.tourner_une_fois()
    assert [e["donnees"]["point"] for e in evenements(tuteur)] == ["bloc_consulte", "fin_de_seance"]


def test_retour_apres_une_longue_pause_clot_l_ancienne_seance_avant_d_en_ouvrir_une(avec_exemple):
    tuteur, client = avec_exemple
    instant = [1000.0]
    tuteur._horloge = lambda: instant[0]
    client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/a"})
    instant[0] += tuteur.inactivite_s + 1
    client.post("/api/seance/bloc_consulte", json={"adresse": "fiche/b"})
    assert [(e["donnees"]["point"], e["donnees"].get("adresse")) for e in evenements(tuteur)] == [
        ("bloc_consulte", "fiche/a"),
        ("fin_de_seance", None),
        ("bloc_consulte", "fiche/b"),
    ]
    assert tuteur.fin_de_seance() is True  # la nouvelle seance est ouverte


def test_activite_reguliere_ne_clot_pas_la_seance(avec_exemple):
    tuteur, client = avec_exemple
    instant = [1000.0]
    tuteur._horloge = lambda: instant[0]
    for adresse in ("fiche/a", "fiche/b", "fiche/c"):
        client.post("/api/seance/bloc_consulte", json={"adresse": adresse})
        instant[0] += tuteur.inactivite_s - 1
    assert [e["donnees"]["point"] for e in evenements(tuteur)] == ["bloc_consulte"] * 3
