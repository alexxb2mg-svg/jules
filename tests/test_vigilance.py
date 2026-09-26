"""Tests du plancher deterministe de la brique vigilance."""

from __future__ import annotations

import pytest

from jules.modules.vigilance import charger_plancher, evaluer_plancher


@pytest.fixture
def plancher():
    charger_plancher.cache_clear()
    return charger_plancher()


# --- evaluer_plancher : detection ---------------------------------------------------------------


@pytest.mark.parametrize(
    "texte,niveau_attendu",
    [
        ("je veux me suicider", "eleve"),
        ("j'ai envie de mourir en ce moment", "eleve"),
        ("des fois j'ai juste envie de me faire du mal", "eleve"),
        ("je me suis mise à me couper depuis quelques semaines", "eleve"),
        ("mon père me frappe quand il rentre saoul", "moyen"),
        ("des élèves me harcèlent sur insta", "moyen"),
        ("ils ont fait un groupe snap sur moi avec des photos", "moyen"),
        ("un mec de 24 ans veut qu'on se voie samedi, il m'a dit de pas en parler à ma mère", "moyen"),
    ],
)
def test_plancher_detecte(plancher, texte, niveau_attendu):
    niveau, motif = evaluer_plancher(texte, plancher)
    assert niveau == niveau_attendu
    assert motif


@pytest.mark.parametrize(
    "texte",
    [
        "ce contrôle va me tuer, j'ai rien révisé",
        "ma mère va me tuer si je rate encore ce contrôle",
        "je suis morte mdr, cette blague est nulle",
        "1/2 + 1/3 ?",
        "le prof nous a mis une punition, c'est trop injuste",
        "jvais me pendre avec ma trousse 😂",
    ],
)
def test_plancher_ignore_les_faux_positifs_scolaires(plancher, texte):
    niveau, _ = evaluer_plancher(texte, plancher)
    assert niveau == "aucun"


def test_plancher_prend_le_niveau_le_plus_haut_si_plusieurs_correspondent(plancher):
    texte = "il me frappe et j'ai envie de me faire du mal"
    niveau, _ = evaluer_plancher(texte, plancher)
    assert niveau == "eleve"


# --- integration avec la brique -----------------------------------------------------------------


def test_plancher_seul_declenche_alors_que_le_modele_est_muet(tuteur):
    def regle(systeme, tours, modele):
        if "Tu protèges un élève" in systeme:
            return '{"niveau": "aucun", "motif": ""}'
        return "Qu'est-ce que tu as déjà essayé ?"

    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "j'ai envie de me suicider")
    tuteur.attendre_fond()
    evenements = tuteur.stockage.evenements("vigilance")
    assert evenements and evenements[0]["donnees"]["niveau"] == "eleve"
    journal = next((tuteur.config.donnees / "notifications").glob("*.log")).read_text(encoding="utf-8")
    assert "[URGENT]" in journal


def test_modele_en_panne_avec_plancher_alerte_quand_meme(tuteur):
    def regle(systeme, tours, modele):
        if "Tu protèges un élève" in systeme:
            raise RuntimeError("backend indisponible")
        return "Qu'est-ce que tu as déjà essayé ?"

    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "mon père me frappe souvent")
    tuteur.attendre_fond()
    evenements = tuteur.stockage.evenements("vigilance")
    assert evenements and evenements[0]["donnees"]["niveau"] == "moyen"
    journal = next((tuteur.config.donnees / "notifications").glob("*.log")).read_text(encoding="utf-8")
    assert "[URGENT]" in journal


def test_modele_en_panne_sans_plancher_enregistre_un_repli_sans_notifier(tuteur):
    def regle(systeme, tours, modele):
        if "Tu protèges un élève" in systeme:
            raise RuntimeError("backend indisponible")
        return "Qu'est-ce que tu as déjà essayé ?"

    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "1/2 + 1/3 ?")
    tuteur.attendre_fond()
    evenements = tuteur.stockage.evenements("vigilance")
    assert evenements and evenements[0]["donnees"] == {"niveau": "faible", "motif": "analyse indisponible"}
    dossier_notifs = tuteur.config.donnees / "notifications"
    assert not list(dossier_notifs.glob("*.log"))


def test_modele_dit_aucun_mais_plancher_eleve_alerte_eleve(tuteur):
    def regle(systeme, tours, modele):
        if "Tu protèges un élève" in systeme:
            return '{"niveau": "aucun", "motif": ""}'
        return "Qu'est-ce que tu as déjà essayé ?"

    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "j'ai vraiment envie de mourir")
    tuteur.attendre_fond()
    evenements = tuteur.stockage.evenements("vigilance")
    assert evenements and evenements[0]["donnees"]["niveau"] == "eleve"


def test_json_illisible_avec_plancher_alerte(tuteur):
    def regle(systeme, tours, modele):
        if "Tu protèges un élève" in systeme:
            return "n'importe quoi, pas du JSON"
        return "Qu'est-ce que tu as déjà essayé ?"

    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "je veux me suicider")
    tuteur.attendre_fond()
    evenements = tuteur.stockage.evenements("vigilance")
    assert evenements and evenements[0]["donnees"]["niveau"] == "eleve"
