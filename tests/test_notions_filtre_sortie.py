"""Garde-fou de sortie du module 'notions' (jules/modules/notions.py::Brique.filtrer_reponse) :

une reponse de Jules qui contiendrait la bonne reponse d'un exercice FERME (auto-corrige par le code)
de la fiche de la notion courante est ecartee, dans les modes qui donnent droit a une notion. Bibliotheque
`fiches-3e-experimentales` remplacee ici par une fiche de test au format v2 (champs `type`/`reponse`
structures), sur une notion existante du referentiel (mesure : revue du 27/09/2026, BLOQUANT).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from tests.conftest import RACINE

NOTION = "nombres-premiers-decomposition"  # notion existante de bibliotheque/programme/3e/mathematiques.yaml


def _fiche_v2_de_test() -> dict:
    return {
        "notion": NOTION,
        "declencheurs": ["nombre premier", "décomposition"],
        "essentiel": "Un nombre premier n'a que deux diviseurs : 1 et lui-même.",
        "exercices": [
            {
                "id": "produit-de-12",
                "type": "nombre",
                "enonce": "Combien vaut 12 × 12 ?",
                "reponse": {"valeur": 144, "forme": "libre"},
                "indices": {"relance": "Décompose 12 × 12 en (10+2) × (10+2).", "methode": "x", "etape": "x"},
                "solution": "12 × 12 = 144.",
            },
            {
                "id": "nombre-premier-91",
                "type": "texte_court",
                "enonce": "91 est-il premier ? Réponds par oui ou par non.",
                "reponse": {"acceptees": ["non"]},
                "indices": {"relance": "Teste la division par 7.", "methode": "x", "etape": "x"},
                "solution": "Non : 91 = 7 × 13.",
            },
            {
                "id": "lequel-est-premier",
                "type": "choix",
                "enonce": "Lequel de ces nombres est premier ?",
                "reponse": {
                    "options": [
                        {"id": "a", "texte": "quatre-vingt-onze"},
                        {"id": "b", "texte": "quatre-vingt-dix-sept"},
                    ],
                    "bonnes": ["b"],
                },
                "indices": {"relance": "Teste 2, 3, 5, 7.", "methode": "x", "etape": "x"},
                "solution": "quatre-vingt-dix-sept est premier.",
            },
            {
                "id": "explique",
                "type": "ouverte",
                "enonce": "Explique pourquoi 97 est premier.",
                "solution": "97 n'est divisible ni par 2, 3, 5 ni 7, et 11² > 97.",
            },
        ],
        "sources": [{"titre": "Test", "url": "https://exemple.invalide/test", "licence": "CC-BY-SA-4.0"}],
    }


@pytest.fixture
def projet(tmp_path: Path) -> Path:
    """Comme tests/conftest.py::projet, avec la fiche de test v2 ci-dessus a la place de la bibliotheque

    `fiches-3e-experimentales` reelle (deja citee dans config.yaml pour le module 'notions').
    """
    for dossier in ("persona", "consignes", "profils", "bibliotheque", "extensions"):
        shutil.copytree(RACINE / dossier, tmp_path / dossier)
    cible = tmp_path / "bibliotheque" / "fiches-3e-experimentales" / "fiches" / "mathematiques"
    shutil.rmtree(cible, ignore_errors=True)
    cible.mkdir(parents=True)
    (cible / f"{NOTION}.yaml").write_text(yaml.safe_dump(_fiche_v2_de_test(), allow_unicode=True), encoding="utf-8")
    return tmp_path


def _preparer(tuteur, mode: str = "aide-devoirs"):
    module = tuteur.module("notions")
    conv = tuteur.stockage.creer_conversation(mode)
    module.fixer(conv.id, NOTION, origine="eleve")
    return module, conv.id


# --- le detecteur ecarte une fuite de la reponse fermee, en mode aide-devoirs --------------------


def test_filtre_ecarte_une_fuite_de_la_reponse_nombre_et_relance_une_fois(tuteur):
    _module, conv_id = _preparer(tuteur)
    base = tuteur.llm.regle
    appels = {"n": 0}

    def regle(systeme, tours, modele):
        if "Notion travaillée" in systeme:
            appels["n"] += 1
            if appels["n"] == 1:
                return "La réponse est 144 (12 × 12 = 144)."
            return "Qu'obtiens-tu si tu poses la multiplication en colonnes ?"
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle
    bot = tuteur.echanger(conv_id, "12 fois 12 ça fait quoi ?")
    tuteur.llm.regle = base

    assert appels["n"] == 2  # premier essai ecarte, une seule relance
    assert "144" not in bot.texte
    assert bot.texte == "Qu'obtiens-tu si tu poses la multiplication en colonnes ?"
    conv = tuteur.stockage.conversation(conv_id)
    assert conv.messages[-1].texte == bot.texte  # la version enregistree est bien la version sure
    assert "144" not in conv.messages[-1].texte


def test_filtre_repli_si_la_relance_fuit_encore(tuteur):
    """Si meme la relance contient la reponse, une question de repli neutre est renvoyee (jamais la reponse)."""
    _module, conv_id = _preparer(tuteur)
    base = tuteur.llm.regle

    def regle_qui_fuit_toujours(systeme, tours, modele):
        if "Notion travaillée" in systeme:
            return "Allez, 144, c'est la réponse."
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle_qui_fuit_toujours
    bot = tuteur.echanger(conv_id, "12 fois 12 ça fait quoi ?")
    tuteur.llm.regle = base

    assert "144" not in bot.texte
    assert bot.texte == "Qu'est-ce qui te fait penser ça ? Reprends l'énoncé étape par étape."


def test_filtre_detecte_le_nombre_en_lettres(tuteur):
    """Renforcement demande par la revue : « cent quarante-quatre » doit aussi etre ecarte."""
    _module, conv_id = _preparer(tuteur)
    base = tuteur.llm.regle
    appels = {"n": 0}

    def regle(systeme, tours, modele):
        if "Notion travaillée" in systeme:
            appels["n"] += 1
            if appels["n"] == 1:
                return "La réponse est cent quarante-quatre."
            return "Essaie de poser l'opération."
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle
    bot = tuteur.echanger(conv_id, "12 fois 12 ça fait quoi ?")
    tuteur.llm.regle = base

    assert appels["n"] == 2
    assert "cent quarante-quatre" not in bot.texte and "144" not in bot.texte


def test_filtre_detecte_la_fuite_texte_court_et_qcm(tuteur):
    _module, conv_id = _preparer(tuteur)
    base = tuteur.llm.regle

    def fuite_texte_court(systeme, tours, modele):
        if "Notion travaillée" in systeme:
            return "Non, 91 n'est pas premier."
        return base(systeme, tours, modele)

    tuteur.llm.regle = fuite_texte_court
    bot = tuteur.echanger(conv_id, "91 est-il premier ?")
    tuteur.llm.regle = base
    assert "non, 91 n'est pas premier" not in bot.texte.lower()

    def fuite_qcm(systeme, tours, modele):
        if "Notion travaillée" in systeme:
            return "C'est quatre-vingt-dix-sept qui est premier."
        return base(systeme, tours, modele)

    _module2, conv_id2 = _preparer(tuteur)
    tuteur.llm.regle = fuite_qcm
    bot2 = tuteur.echanger(conv_id2, "lequel est premier entre 91 et 97 ?")
    tuteur.llm.regle = base
    assert "quatre-vingt-dix-sept" not in bot2.texte.lower()


def test_filtre_n_agit_pas_sur_un_exercice_ouvert(tuteur):
    """Un exercice 'ouverte' n'est jamais corrige par le code : sa solution reste dans le prompt, le

    garde-fou de sortie ne doit donc pas l'ecarter (ce serait un faux positif genant pour Jules)."""
    _module, conv_id = _preparer(tuteur)
    base = tuteur.llm.regle
    texte_solution = "97 n'est divisible ni par 2, 3, 5 ni 7, et 11² > 97."

    def regle(systeme, tours, modele):
        if "Notion travaillée" in systeme:
            return texte_solution
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle
    bot = tuteur.echanger(conv_id, "explique-moi pourquoi 97 est premier")
    tuteur.llm.regle = base
    assert bot.texte == texte_solution  # pas ecarte : aucun exercice FERME ne contient ce texte


# --- modes hors notion : jamais filtre (le module n'a rien a filtrer) ----------------------------


@pytest.mark.parametrize("mode", ["epreuve", "exercice"])
def test_modes_sans_notion_jamais_filtres(tuteur, mode):
    _module, conv_id = _preparer(tuteur, mode=mode)
    base = tuteur.llm.regle

    def regle(systeme, tours, modele):
        return "La réponse est 144."

    tuteur.llm.regle = regle
    bot = tuteur.echanger(conv_id, "12 fois 12 ça fait quoi ?")
    tuteur.llm.regle = base
    assert bot.texte == "La réponse est 144."  # ces modes n'ont pas de notion associee : rien a filtrer


def test_reglage_filtre_sortie_peut_etre_coupe(tuteur):
    module, conv_id = _preparer(tuteur)
    module.filtre_sortie = False
    base = tuteur.llm.regle

    def regle(systeme, tours, modele):
        if "Notion travaillée" in systeme:
            return "La réponse est 144."
        return base(systeme, tours, modele)

    tuteur.llm.regle = regle
    bot = tuteur.echanger(conv_id, "12 fois 12 ça fait quoi ?")
    tuteur.llm.regle = base
    assert bot.texte == "La réponse est 144."  # reglage coupe : le module ne filtre plus


# --- preuve que c'est bien le moteur (boucle Tuteur.echanger) qui appelle le filtre --------------


def test_le_moteur_appelle_bien_filtrer_reponse_du_module_notions(tuteur, monkeypatch):
    module, conv_id = _preparer(tuteur)
    appels: list[str] = []
    original = module.filtrer_reponse

    def espion(conv, texte, relancer):
        appels.append(texte)
        return original(conv, texte, relancer)

    monkeypatch.setattr(module, "filtrer_reponse", espion)
    tuteur.echanger(conv_id, "12 fois 12 ça fait quoi ?")
    assert appels  # filtrer_reponse a bien ete invoque par la boucle du moteur, pas seulement testable a la main
