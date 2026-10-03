"""Tests de la brique vigilance : plancher deterministe, alerte avant le modele, escalade, place du module."""

from __future__ import annotations

import re
import time

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
        "je vais me couper les cheveux ce week-end",
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


# --- l'alerte du plancher n'attend pas le modele ; le modele ne peut qu'aggraver -------------------


def _notifications(tuteur) -> list[str]:
    """En-tete de chaque notification ecrite par le notifieur fichier, dans l'ordre d'envoi."""
    dossier = tuteur.config.donnees / "notifications"
    return [
        ligne
        for fichier in sorted(dossier.glob("*.log"))
        for ligne in fichier.read_text(encoding="utf-8").splitlines()
        if ligne.startswith("=== ")
    ]


def _regle_vigilance(reponse: str):
    """Regle factice : `reponse` pour l'analyse de vigilance, une reponse de tuteur pour tout le reste."""

    def regle(systeme, tours, modele):
        if "Tu protèges un élève" in systeme:
            return reponse
        return "Qu'est-ce que tu as déjà essayé ?"

    return regle


def test_alerte_du_plancher_ecrite_avant_que_le_modele_rende_la_main(tuteur, monkeypatch):
    """Panne d'API : chaque appel au modele 'rapide' dort puis echoue, comme un delai_s depasse. L'alerte
    du plancher est deja dans donnees/notifications/*.log quand l'analyse de vigilance commence, et quand
    celle du suivi commence (vigilance passe avant suivi) : elle n'attend aucun des deux appels."""
    lenteur_s = 0.5
    dossier = tuteur.config.donnees / "notifications"
    alerte_deja_ecrite: dict[str, bool] = {}
    instants: dict[str, float] = {}

    def alerte_sur_le_disque() -> bool:
        return any("[URGENT]" in f.read_text(encoding="utf-8") for f in dossier.glob("*.log"))

    def regle(systeme, tours, modele):
        if modele != "rapide":
            return "Qu'est-ce que tu as déjà essayé ?"
        if "Tu protèges un élève" in systeme:
            analyse = "vigilance"
        elif "suivi scolaire" in systeme:
            analyse = "suivi"
        else:
            analyse = "autre"
        alerte_deja_ecrite[analyse] = alerte_sur_le_disque()
        time.sleep(lenteur_s)
        instants[f"retour_{analyse}"] = time.perf_counter()
        raise RuntimeError("delai depasse (simule)")

    notifieur_fichier = tuteur.notifieurs[0]
    envoyer = notifieur_fichier.envoyer

    def envoyer_et_dater(sujet, texte, urgent=False):
        envoyer(sujet, texte, urgent)
        instants.setdefault("alerte_ecrite", time.perf_counter())

    monkeypatch.setattr(notifieur_fichier, "envoyer", envoyer_et_dater)
    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "j'ai envie de me suicider")
    tuteur.attendre_fond()

    assert alerte_deja_ecrite["vigilance"] and alerte_deja_ecrite["suivi"]
    # l'alerte est ecrite au moins une lenteur (a la precision de l'horloge pres) avant le retour du modele
    assert instants["retour_vigilance"] - instants["alerte_ecrite"] >= 0.8 * lenteur_s
    evenements = tuteur.stockage.evenements("vigilance")
    assert [e["donnees"]["niveau"] for e in evenements] == ["eleve"]  # pas d'evenement de repli en plus
    assert len(_notifications(tuteur)) == 1


@pytest.mark.parametrize(
    "texte,niveau_plancher,niveau_modele",
    [
        ("mon père me frappe souvent", "moyen", "moyen"),  # le modele confirme
        ("mon père me frappe souvent", "moyen", "faible"),  # le modele dit moins
        ("j'ai envie de me suicider", "eleve", "moyen"),
        ("j'ai envie de me suicider", "eleve", "aucun"),
    ],
)
def test_modele_qui_confirme_ou_dit_moins_pas_de_doublon(tuteur, texte, niveau_plancher, niveau_modele):
    tuteur.llm.regle = _regle_vigilance(f'{{"niveau": "{niveau_modele}", "motif": "Vu par le modèle."}}')
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, texte)
    tuteur.attendre_fond()
    evenements = tuteur.stockage.evenements("vigilance")
    assert len(evenements) == 1
    assert evenements[0]["donnees"]["niveau"] == niveau_plancher
    assert evenements[0]["donnees"]["motif"] == evaluer_plancher(texte)[1]
    notifications = _notifications(tuteur)
    assert len(notifications) == 1 and "[URGENT]" in notifications[0]


def test_modele_plus_grave_que_le_plancher_escalade(tuteur):
    motif_modele = "Coups répétés à la maison, il dit avoir peur de rentrer."
    tuteur.llm.regle = _regle_vigilance(f'{{"niveau": "eleve", "motif": "{motif_modele}"}}')
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "mon père me frappe souvent")
    tuteur.attendre_fond()
    evenements = tuteur.stockage.evenements("vigilance")  # du plus recent au plus ancien
    assert [e["donnees"]["niveau"] for e in evenements] == ["eleve", "moyen"]
    assert evenements[0]["donnees"]["motif"] == motif_modele
    notifications = _notifications(tuteur)  # dans l'ordre d'envoi : plancher, puis escalade
    assert len(notifications) == 2 and all("[URGENT]" in n for n in notifications)
    assert notifications[0].endswith("attention (moyen)") and notifications[1].endswith("attention (eleve)")


def test_place_de_vigilance_sans_effet_sur_le_prompt(tuteur):
    """config.yaml fait passer 'vigilance' avant 'memoire' et 'suivi'. La brique ne contribue pas au prompt
    systeme : Tuteur.systeme() est le meme qu'avec l'ancien ordre (vigilance juste apres suivi)."""
    ids = [m.id for m in tuteur.modules]
    assert ids.index("vigilance") < ids.index("memoire") < ids.index("suivi")
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "1/2 + 1/3 ?")
    tuteur.attendre_fond()
    conv = tuteur.stockage.conversation(conv.id)

    def sans_la_date(systeme: str) -> str:
        return re.sub(r"Nous sommes le .*", "", systeme)  # change a l'heure pile, sans rapport avec l'ordre

    avec_le_nouvel_ordre = tuteur.systeme(conv)
    vigilance = tuteur.module("vigilance")
    tuteur.modules.remove(vigilance)
    tuteur.modules.insert([m.id for m in tuteur.modules].index("suivi") + 1, vigilance)
    ancien_ordre = [m.id for m in tuteur.modules]
    assert ancien_ordre[ancien_ordre.index("suivi") + 1] == "vigilance"
    assert sans_la_date(tuteur.systeme(conv)) == sans_la_date(avec_le_nouvel_ordre)
