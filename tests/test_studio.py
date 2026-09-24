"""Tests du module jules.studio (formats, validation, garde-fous), docs/STUDIO-CONTRAT.md §1 et §2.

Chaque regle de validation est testee dans les deux sens (accepte / refuse), suivant le meme
esprit que tests/test_lecons.py.
"""

from __future__ import annotations

from typing import Any

import pytest

from jules.studio import (
    STATUTS_SUPPORT,
    TAILLE_CHAMP_MAX,
    TYPES_SUPPORT,
    ErreurStudio,
    Support,
    pret_a_valider,
    ressemble_a_un_support_redige,
    trame_vide,
    valider_champ,
)

HORODATAGE = "2026-09-24T10:00:00"


def support(
    type_support: str,
    contenu: dict[str, Any],
    titre: str = "Le theoreme de Pythagore",
    statut: str = "brouillon",
) -> Support:
    return Support(
        id="support-1",
        notion="pythagore",
        type=type_support,
        titre=titre,
        contenu=contenu,
        statut=statut,
        cree_le=HORODATAGE,
        modifie_le=HORODATAGE,
    )


def carte_mentale_contenu(*textes: str) -> dict[str, Any]:
    defauts = ["Definition", "Formule", "Un exemple d'application"]
    valeurs = list(textes) or defauts
    return {
        "type": "carte_mentale",
        "notion": "pythagore",
        "titre": "Pythagore",
        "noeuds": [{"id": f"n{i}", "texte": v, "parent": None} for i, v in enumerate(valeurs)],
    }


def fiche_contenu(*contenus: str) -> dict[str, Any]:
    defauts = [
        "Dans un triangle rectangle, le carre de l'hypotenuse vaut la somme des carres.",
        "Sert a calculer une longueur manquante.",
    ]
    valeurs = list(contenus) or defauts
    return {
        "type": "fiche",
        "notion": "pythagore",
        "titre": "Pythagore",
        "sections": [{"id": f"s{i}", "titre": f"Section {i}", "contenu": v} for i, v in enumerate(valeurs)],
    }


def quiz_contenu(*paires: tuple[str, str]) -> dict[str, Any]:
    defauts = [
        ("A quoi sert le theoreme de Pythagore ?", "A calculer une longueur dans un triangle rectangle."),
        ("Quelle est la formule ?", "BC carre egale AB carre plus AC carre."),
        ("Sur quel type de triangle s'applique-t-il ?", "Un triangle rectangle."),
    ]
    valeurs = list(paires) or defauts
    return {
        "type": "quiz",
        "notion": "pythagore",
        "titre": "Quiz Pythagore",
        "questions": [
            {"id": f"q{i}", "question": q, "reponse": r, "forme": "libre"} for i, (q, r) in enumerate(valeurs)
        ],
    }


def cartes_memoire_contenu(*paires: tuple[str, str]) -> dict[str, Any]:
    defauts = [
        ("Pythagore, a quoi ca sert ?", "A calculer le troisieme cote d'un triangle rectangle."),
        ("BC²", "AB² + AC²"),
        ("Hypotenuse", "Le plus grand cote, en face de l'angle droit."),
        ("Condition", "Le triangle doit etre rectangle."),
    ]
    valeurs = list(paires) or defauts
    return {
        "type": "cartes_memoire",
        "notion": "pythagore",
        "titre": "Cartes Pythagore",
        "cartes": [
            {"id": f"c{i}", "recto": r, "verso": v, "etat": "nouvelle", "prochaine_revision": None, "palier": 0}
            for i, (r, v) in enumerate(valeurs)
        ],
    }


# --- constantes figees ------------------------------------------------------------------------


def test_constantes_figees_par_le_contrat():
    assert TYPES_SUPPORT == ("carte_mentale", "fiche", "quiz", "cartes_memoire")
    assert STATUTS_SUPPORT == ("brouillon", "relu", "valide")
    assert TAILLE_CHAMP_MAX == 200


# --- Support.public() --------------------------------------------------------------------------


def test_support_public_ne_retire_aucun_champ():
    s = support("fiche", fiche_contenu())
    public = s.public()
    assert public == {
        "id": "support-1",
        "notion": "pythagore",
        "type": "fiche",
        "titre": "Le theoreme de Pythagore",
        "contenu": s.contenu,
        "statut": "brouillon",
        "cree_le": HORODATAGE,
        "modifie_le": HORODATAGE,
    }


# --- trame_vide --------------------------------------------------------------------------------


@pytest.mark.parametrize("type_support", TYPES_SUPPORT)
def test_trame_vide_accepte_chaque_type_connu(type_support):
    trame = trame_vide(type_support, "pythagore", "Mon support")
    assert trame["type"] == type_support
    assert trame["notion"] == "pythagore"
    assert trame["titre"] == "Mon support"
    nom_liste = {"carte_mentale": "noeuds", "fiche": "sections", "quiz": "questions", "cartes_memoire": "cartes"}[
        type_support
    ]
    assert trame[nom_liste] == []


def test_trame_vide_refuse_un_type_inconnu():
    with pytest.raises(ErreurStudio):
        trame_vide("resume_video", "pythagore", "Mon support")


# --- valider_champ -------------------------------------------------------------------------------


def test_valider_champ_accepte_le_titre_du_support():
    valider_champ("fiche", ["titre"], "Un titre correct")


def test_valider_champ_refuse_un_titre_trop_long():
    with pytest.raises(ErreurStudio):
        valider_champ("fiche", ["titre"], "x" * (TAILLE_CHAMP_MAX + 1))


def test_valider_champ_accepte_une_valeur_a_la_limite_exacte():
    valider_champ("fiche", ["titre"], "x" * TAILLE_CHAMP_MAX)


@pytest.mark.parametrize(
    "type_support,chemin",
    [
        ("carte_mentale", ["noeuds", 0, "texte"]),
        ("fiche", ["sections", 0, "titre"]),
        ("fiche", ["sections", 1, "contenu"]),
        ("quiz", ["questions", 2, "question"]),
        ("quiz", ["questions", 0, "reponse"]),
        ("cartes_memoire", ["cartes", 0, "recto"]),
        ("cartes_memoire", ["cartes", 3, "verso"]),
    ],
)
def test_valider_champ_accepte_un_chemin_conforme_au_gabarit(type_support, chemin):
    valider_champ(type_support, chemin, "Une valeur raisonnable")


@pytest.mark.parametrize(
    "type_support,chemin",
    [
        ("carte_mentale", ["noeuds", 0, "parent"]),  # champ non editable en texte libre
        ("carte_mentale", ["sections", 0, "texte"]),  # mauvais nom de liste pour ce type
        ("fiche", ["sections", "0", "contenu"]),  # index non entier
        ("fiche", ["sections", -1, "contenu"]),  # index negatif
        ("fiche", ["sections", 0, "cote"]),  # champ inexistant
        ("quiz", ["questions", 0, "forme"]),  # champ fixe, pas texte libre editable
        ("quiz", ["questions"]),  # chemin incomplet (pointe sur la liste, pas un champ)
        ("cartes_memoire", ["cartes", 0, "etat"]),  # gere par les revisions, pas par l'eleve
        ("cartes_memoire", ["notion"]),  # champ du gabarit, mais pas editable par l'eleve
    ],
)
def test_valider_champ_refuse_un_chemin_hors_gabarit(type_support, chemin):
    with pytest.raises(ErreurStudio):
        valider_champ(type_support, chemin, "Une valeur")


def test_valider_champ_refuse_un_type_de_support_inconnu():
    with pytest.raises(ErreurStudio):
        valider_champ("resume_video", ["titre"], "Une valeur")


# --- pret_a_valider : nombre minimal d'elements -------------------------------------------------


def test_pret_a_valider_accepte_une_carte_mentale_a_trois_noeuds():
    s = support("carte_mentale", carte_mentale_contenu())
    pret_a_valider(s, lecon_textes=[], messages_jules=[])


def test_pret_a_valider_refuse_une_carte_mentale_a_deux_noeuds():
    s = support("carte_mentale", carte_mentale_contenu("Definition", "Formule"))
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[], messages_jules=[])


def test_pret_a_valider_accepte_une_fiche_a_deux_sections_remplies():
    s = support("fiche", fiche_contenu())
    pret_a_valider(s, lecon_textes=[], messages_jules=[])


def test_pret_a_valider_refuse_une_fiche_avec_une_seule_section_remplie():
    contenu = fiche_contenu("La seule section remplie de cette fiche.", "")
    s = support("fiche", contenu)
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[], messages_jules=[])


def test_pret_a_valider_accepte_un_quiz_a_trois_questions():
    s = support("quiz", quiz_contenu())
    pret_a_valider(s, lecon_textes=[], messages_jules=[])


def test_pret_a_valider_refuse_un_quiz_a_deux_questions():
    contenu = quiz_contenu(("Question 1 ?", "Reponse 1"), ("Question 2 ?", "Reponse 2"))
    s = support("quiz", contenu)
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[], messages_jules=[])


def test_pret_a_valider_accepte_quatre_cartes_memoire():
    s = support("cartes_memoire", cartes_memoire_contenu())
    pret_a_valider(s, lecon_textes=[], messages_jules=[])


def test_pret_a_valider_refuse_trois_cartes_memoire():
    contenu = cartes_memoire_contenu(("R1", "V1"), ("R2", "V2"), ("R3", "V3"))
    s = support("cartes_memoire", contenu)
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[], messages_jules=[])


# --- pret_a_valider : garde-fou anti-copie -------------------------------------------------------

PASSAGE_LECON = "Dans un triangle rectangle, le carre de l'hypotenuse vaut la somme des carres."
MESSAGE_JULES = "N'oublie pas de preciser l'unite de longueur dans ta reponse."


def test_pret_a_valider_accepte_un_contenu_reformule_par_l_eleve():
    contenu = fiche_contenu(
        "Moi je retiens que dans un triangle avec un angle droit, il y a une formule avec des carres.",
        "Ca sert a trouver une longueur qu'on ne connait pas encore.",
    )
    s = support("fiche", contenu)
    pret_a_valider(s, lecon_textes=[PASSAGE_LECON], messages_jules=[MESSAGE_JULES])


def test_pret_a_valider_refuse_un_contenu_recopie_a_l_identique_de_la_lecon():
    contenu = fiche_contenu(PASSAGE_LECON, "Une deuxieme section personnelle et suffisamment longue.")
    s = support("fiche", contenu)
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[PASSAGE_LECON], messages_jules=[])


def test_pret_a_valider_refuse_un_contenu_recopie_d_un_message_de_jules():
    contenu = fiche_contenu(MESSAGE_JULES, "Une deuxieme section personnelle et suffisamment longue.")
    s = support("fiche", contenu)
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[], messages_jules=[MESSAGE_JULES])


@pytest.mark.parametrize(
    "variante",
    [
        PASSAGE_LECON.upper(),
        PASSAGE_LECON.lower(),
        "  " + PASSAGE_LECON + "   ",
        PASSAGE_LECON.replace(" ", "   "),
        PASSAGE_LECON.replace(",", " ,").replace(".", " ."),
        PASSAGE_LECON.replace("'", " ").rstrip(".") + " !",
    ],
)
def test_pret_a_valider_refuse_des_variations_de_casse_et_de_ponctuation(variante):
    contenu = fiche_contenu(variante, "Une deuxieme section personnelle et suffisamment longue.")
    s = support("fiche", contenu)
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[PASSAGE_LECON], messages_jules=[])


def test_pret_a_valider_refuse_une_copie_dans_une_carte_mentale():
    s = support("carte_mentale", carte_mentale_contenu(PASSAGE_LECON, "Formule", "Un exemple perso"))
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[PASSAGE_LECON], messages_jules=[])


def test_pret_a_valider_refuse_une_copie_dans_des_cartes_memoire():
    contenu = cartes_memoire_contenu(
        ("Le recto", PASSAGE_LECON),
        ("R2", "V2 personnel et distinct"),
        ("R3", "V3 personnel et distinct"),
        ("R4", "V4 personnel et distinct"),
    )
    s = support("cartes_memoire", contenu)
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[PASSAGE_LECON], messages_jules=[])


def test_pret_a_valider_refuse_un_type_de_support_inconnu():
    s = support("resume_video", {"resume_video": []})
    with pytest.raises(ErreurStudio):
        pret_a_valider(s, lecon_textes=[], messages_jules=[])


# --- ressemble_a_un_support_redige ---------------------------------------------------------------

TEXTES_POSITIFS = [
    # 1. liste a puces longue (>= 3 items)
    "Voici les points cles :\n"
    "- Le theoreme de Pythagore relie les cotes d'un triangle rectangle.\n"
    "- La formule est BC carre egale AB carre plus AC carre.\n"
    "- Il sert a calculer une longueur inconnue.\n",
    # 2. liste numerotee longue
    "1. Identifie l'angle droit.\n2. Repere l'hypotenuse, le plus grand cote.\n3. Applique la formule.\n",
    # 3. plusieurs titres markdown
    "# Definition\nLe theoreme de Pythagore enonce une relation entre les cotes d'un triangle rectangle.\n"
    "# Exemple\nSi AB vaut 3 et AC vaut 4, alors BC vaut 5.\n",
    # 4. plusieurs titres en style etiquette (":")
    "Definition :\nDans un triangle rectangle, le carre de l'hypotenuse vaut la somme des carres.\n"
    "Exemple :\nAvec 3 et 4, on trouve 5.\n",
    # 5. long paragraphe de definition, sans question
    "Le theoreme de Pythagore est une relation fondamentale de la geometrie qui relie les longueurs "
    "des trois cotes d'un triangle rectangle. Il affirme que le carre de la longueur de l'hypotenuse, "
    "c'est-a-dire le cote oppose a l'angle droit, est toujours egal a la somme des carres des longueurs "
    "des deux autres cotes. Cette propriete permet de calculer une longueur manquante des que les deux "
    "autres sont connues, ce qui en fait un outil tres utilise en geometrie et en physique.",
    # 6. liste a puces melee a des titres, contenu clairement pret a copier
    "Fiche express :\n- BC carre egale AB carre plus AC carre\n- s'applique seulement au triangle rectangle\n"
    "- l'hypotenuse est le plus grand cote\n- utile pour calculer une longueur manquante\n",
]

TEXTES_NEGATIFS = [
    # 1. question courte
    "Qu'est-ce que tu retiens de cette partie, avec tes mots ?",
    # 2. remarque courte positive
    "Bien vu, continue comme ca !",
    # 3. signalement d'oubli, sous forme de question
    "Tu as oublie de preciser l'unite, non ?",
    # 4. remarque de relecture moyenne, sans liste ni titre, sous le seuil de longueur
    "Cette section repete surtout le titre : qu'est-ce qu'elle ajoute de nouveau par rapport a la lecon ?",
    # 5. demande de reformulation
    "Peux-tu reformuler cette phrase avec tes propres mots ?",
    # 6. remarque avec un ":" au milieu de la phrase (pas un titre isole sur sa ligne)
    "Attention : tu as invers\u00e9 le recto et le verso de cette carte.",
    # 7. remarque courte sur une carte memoire
    "Ce recto et ce verso se ressemblent beaucoup, tu peux les distinguer davantage ?",
]


@pytest.mark.parametrize("texte", TEXTES_POSITIFS)
def test_ressemble_a_un_support_redige_detecte_un_contenu_pret_a_copier(texte):
    assert ressemble_a_un_support_redige(texte) is True


@pytest.mark.parametrize("texte", TEXTES_NEGATIFS)
def test_ressemble_a_un_support_redige_laisse_passer_une_question_ou_remarque_courte(texte):
    assert ressemble_a_un_support_redige(texte) is False


def test_ressemble_a_un_support_redige_refuse_un_texte_vide():
    assert ressemble_a_un_support_redige("") is False
    assert ressemble_a_un_support_redige("   ") is False
