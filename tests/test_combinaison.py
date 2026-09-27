"""Combinaison des amenagements et conflits (docs/spec/ADAPTATIONS-LOT2.md, §2 et §4) : EX-104.

Valeurs attendues calculees a la main a partir des fichiers de adaptations/ (lot 2) :

profils/test-cumul.yaml coche supports-aeres-agrandis, limiter-quantite-ecrit, surligner-mots-cles,
lecture-oralisee et consignes-decomposees (plus amenagement-test-a, amenagement-test-b, du lot 1, et
amenagement-inexistant : aucun fichier sous adaptations/amenagements/, donc ignores et signales).

- espacement-lettres 0.18, espacement-mots 0.5, interligne 2.0, taille-texte 1.6875, longueur-ligne 80 :
  seul supports-aeres-agrandis les regle ;
- densite un-exercice (limiter-quantite-ecrit) ; surlignage-mots-cles vrai (surligner-mots-cles) ;
- lecture-vocale proposee (lecture-oralisee) ; consignes-decoupees et phrases-courtes vrais
  (consignes-decomposees) ;
- police defaut, fond blanc, reperes-rang-chiffres faux : aucune source, valeur neutre ;
- conflits : taille-texte 1.6875 > 1.125 avec densite un-exercice, et surlignage avec densite.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml

from jules.amenagements import Amenagement, charger_amenagements
from jules.combinaison import (
    CONFLIT_LECTURE_AUTOMATIQUE,
    CONFLIT_REPERES_DENSITE,
    CONFLIT_SURLIGNAGE_DENSITE,
    CONFLIT_TAILLE_DENSITE,
    MESSAGES_CONFLITS,
    PARENT,
    resoudre,
)
from jules.composition import charger_profil
from jules.leviers import charger_leviers
from tests.termes_interdits import termes_interdits, trouver_terme

RACINE = Path(__file__).resolve().parents[1]
PROFIL_CUMUL = RACINE / "profils" / "test-cumul.yaml"

ATTENDU_CUMUL = {
    "espacement-lettres": 0.18,
    "espacement-mots": 0.5,
    "interligne": 2.0,
    "taille-texte": 1.6875,
    "longueur-ligne": 80,
    "police": "defaut",
    "fond": "blanc",
    "densite": "un-exercice",
    "lecture-vocale": "proposee",
    "consignes-decoupees": True,
    "phrases-courtes": True,
    "reperes-rang-chiffres": False,
    "surlignage-mots-cles": True,
}
INCONNUS_CUMUL = ("amenagement-test-a", "amenagement-test-b", "amenagement-inexistant")


@pytest.fixture(scope="module")
def leviers():
    return charger_leviers()


@pytest.fixture(scope="module")
def amenagements(leviers):
    return charger_amenagements(leviers=leviers)


def ids_cumul() -> list[str]:
    return charger_profil(PROFIL_CUMUL).amenagements


def essai(ident: str, **valeurs) -> Amenagement:
    """Amenagement fictif (hors fichiers) pour tester une regle avec deux sources sur un meme levier."""
    return Amenagement(id=ident, libelles={}, leviers={k.replace("_", "-"): v for k, v in valeurs.items()})


def ids_conflits(resolution) -> set[str]:
    return {c.id for c in resolution.conflits}


# --- test-cumul.yaml ----------------------------------------------------------------------------
def test_profil_cumul_valeurs_calculees_a_la_main(leviers, amenagements):
    resolution = resoudre(ids_cumul(), leviers=leviers, amenagements=amenagements)
    assert resolution.valeurs == ATTENDU_CUMUL
    assert set(resolution.valeurs) == set(leviers), "une valeur pour chaque levier"
    assert resolution.origines["phrases-courtes"] == ("consignes-decomposees",)
    assert resolution.origines["densite"] == ("limiter-quantite-ecrit",)
    assert "police" not in resolution.origines and "reperes-rang-chiffres" not in resolution.origines


def test_profil_cumul_conflits_renvoyes_sans_trancher(leviers, amenagements):
    resolution = resoudre(ids_cumul(), leviers=leviers, amenagements=amenagements)
    assert ids_conflits(resolution) == {CONFLIT_TAILLE_DENSITE, CONFLIT_SURLIGNAGE_DENSITE}
    # rien n'est tranche : les deux leviers en conflit gardent la valeur de leur regle
    assert resolution.valeurs["taille-texte"] == 1.6875 and resolution.valeurs["densite"] == "un-exercice"
    assert resolution.valeurs["surlignage-mots-cles"] is True


def test_profil_cumul_inconnus_ignores_et_signales(leviers, amenagements, caplog):
    with caplog.at_level(logging.WARNING, logger="jules"):
        resolution = resoudre(ids_cumul(), leviers=leviers, amenagements=amenagements)
    assert resolution.inconnus == INCONNUS_CUMUL
    assert "3 amenagement(s) inconnu(s)" in caplog.text
    for ident in INCONNUS_CUMUL:  # signale au code appelant, pas recopie dans le journal
        assert ident not in caplog.text


def test_profil_cumul_avec_preferences_du_parent(leviers, amenagements):
    preferences = {"police": "arial", "fond": "creme", "lecture-vocale": "automatique"}
    resolution = resoudre(ids_cumul(), preferences, leviers=leviers, amenagements=amenagements)
    assert resolution.valeurs == {**ATTENDU_CUMUL, **preferences}
    assert resolution.origines["lecture-vocale"] == ("lecture-oralisee", PARENT)
    assert resolution.origines["police"] == (PARENT,)
    assert ids_conflits(resolution) == {
        CONFLIT_TAILLE_DENSITE,
        CONFLIT_SURLIGNAGE_DENSITE,
        CONFLIT_LECTURE_AUTOMATIQUE,
    }
    assert resolution.preferences_ignorees == ()


# --- un cas par conflit du §4 -------------------------------------------------------------------
def test_conflit_taille_texte_elevee_et_densite(leviers, amenagements):
    resolution = resoudre(
        ["supports-aeres-agrandis", "limiter-quantite-ecrit"], leviers=leviers, amenagements=amenagements
    )
    assert ids_conflits(resolution) == {CONFLIT_TAILLE_DENSITE}
    (conflit,) = resolution.conflits
    assert conflit.leviers == ("taille-texte", "densite")
    assert resolution.valeurs["taille-texte"] == 1.6875 and resolution.valeurs["densite"] == "un-exercice"
    # chacun seul : pas de conflit
    assert resoudre(["supports-aeres-agrandis"], leviers=leviers, amenagements=amenagements).conflits == ()
    assert resoudre(["limiter-quantite-ecrit"], leviers=leviers, amenagements=amenagements).conflits == ()


def test_taille_texte_neutre_avec_densite_sans_conflit(leviers):
    # « elevee » = au-dessus de la neutre (1,125) : juste au-dessus, conflit ; a la neutre, aucun.
    base = {"d": essai("d", densite="un-exercice")}
    haute = resoudre(["d", "t"], leviers=leviers, amenagements={**base, "t": essai("t", taille_texte=1.2)})
    assert ids_conflits(haute) == {CONFLIT_TAILLE_DENSITE}
    assert resoudre(["d"], leviers=leviers, amenagements=base).conflits == ()


def test_conflit_reperes_rang_chiffres_et_densite(leviers, amenagements):
    resolution = resoudre(
        ["reperes-couleur-calcul", "limiter-quantite-ecrit"], leviers=leviers, amenagements=amenagements
    )
    assert ids_conflits(resolution) == {CONFLIT_REPERES_DENSITE}
    assert resolution.conflits[0].leviers == ("reperes-rang-chiffres", "densite")
    assert resolution.valeurs["reperes-rang-chiffres"] is True and resolution.valeurs["densite"] == "un-exercice"
    assert resoudre(["reperes-couleur-calcul"], leviers=leviers, amenagements=amenagements).conflits == ()


def test_conflit_surlignage_mots_cles_et_densite(leviers, amenagements):
    resolution = resoudre(["surligner-mots-cles", "limiter-quantite-ecrit"], leviers=leviers, amenagements=amenagements)
    assert ids_conflits(resolution) == {CONFLIT_SURLIGNAGE_DENSITE}
    assert resolution.conflits[0].leviers == ("surlignage-mots-cles", "densite")
    assert resoudre(["surligner-mots-cles"], leviers=leviers, amenagements=amenagements).conflits == ()


def test_conflit_lecture_automatique_seulement_par_le_parent(leviers, amenagements):
    # l'amenagement seul donne « proposee » : aucun conflit
    seul = resoudre(["lecture-oralisee"], leviers=leviers, amenagements=amenagements)
    assert seul.valeurs["lecture-vocale"] == "proposee" and seul.conflits == ()
    # le choix explicite du parent : automatique, renvoye comme conflit, applique quand meme
    choix = resoudre([], {"lecture-vocale": "automatique"}, leviers=leviers, amenagements=amenagements)
    assert choix.valeurs["lecture-vocale"] == "automatique"
    assert ids_conflits(choix) == {CONFLIT_LECTURE_AUTOMATIQUE}
    assert choix.conflits[0].leviers == ("lecture-vocale",)
    # un amenagement ne peut jamais l'activer
    with pytest.raises(ValueError, match="reserve au choix du parent"):
        resoudre(["x"], leviers=leviers, amenagements={"x": essai("x", lecture_vocale="automatique")})


def test_messages_des_conflits_sans_nom_de_trouble():
    termes = termes_interdits()
    assert set(MESSAGES_CONFLITS) == {
        CONFLIT_TAILLE_DENSITE,
        CONFLIT_REPERES_DENSITE,
        CONFLIT_SURLIGNAGE_DENSITE,
        CONFLIT_LECTURE_AUTOMATIQUE,
    }
    for message in MESSAGES_CONFLITS.values():
        assert trouver_terme(message, termes) is None, message


# --- regles de combinaison du §2 (deux sources sur un meme levier) ------------------------------
def test_regle_max_nombre(leviers):
    a, b = essai("a", taille_texte=1.25, interligne=2.0), essai("b", taille_texte=1.5, interligne=1.8)
    valeurs = resoudre(["a", "b"], leviers=leviers, amenagements={"a": a, "b": b}).valeurs
    assert valeurs["taille-texte"] == 1.5 and valeurs["interligne"] == 2.0


def test_regle_min(leviers):
    a, b = essai("a", longueur_ligne=80), essai("b", longueur_ligne=60)
    assert resoudre(["a", "b"], leviers=leviers, amenagements={"a": a, "b": b}).valeurs["longueur-ligne"] == 60


def test_regle_ou(leviers):
    a, b = essai("a", phrases_courtes=True), essai("b", consignes_decoupees=True)
    valeurs = resoudre(["a", "b"], leviers=leviers, amenagements={"a": a, "b": b}).valeurs
    assert valeurs["phrases-courtes"] is True and valeurs["consignes-decoupees"] is True
    assert valeurs["surlignage-mots-cles"] is False


def test_regle_plus_restrictif(leviers):
    a, b = essai("a", densite="un-exercice"), essai("b", densite="tout")
    for ordre in (["a", "b"], ["b", "a"]):
        assert resoudre(ordre, leviers=leviers, amenagements={"a": a, "b": b}).valeurs["densite"] == "un-exercice"


def test_regle_max_sur_un_choix_ordonne(leviers, amenagements):
    # lecture-vocale : max dans l'ordre de la plage (absente < proposee < automatique)
    resolution = resoudre(
        ["lecture-oralisee"], {"lecture-vocale": "automatique"}, leviers=leviers, amenagements=amenagements
    )
    assert resolution.valeurs["lecture-vocale"] == "automatique"


def test_regle_arbitrage_parent(leviers, amenagements):
    assert resoudre([], leviers=leviers, amenagements=amenagements).valeurs["police"] == "defaut"
    assert (
        resoudre([], {"police": "verdana"}, leviers=leviers, amenagements=amenagements).valeurs["police"] == "verdana"
    )
    with pytest.raises(ValueError, match="reserve au choix du parent"):
        resoudre(["x"], leviers=leviers, amenagements={"x": essai("x", fond="creme")})


def test_ordre_et_doublons_sans_effet(leviers, amenagements):
    ids = ids_cumul()
    reference = resoudre(ids, leviers=leviers, amenagements=amenagements)
    inverse = resoudre([*reversed(ids), *ids], leviers=leviers, amenagements=amenagements)
    assert inverse.valeurs == reference.valeurs
    assert ids_conflits(inverse) == ids_conflits(reference)
    assert sorted(inverse.inconnus) == sorted(reference.inconnus)


def test_sans_amenagement_tout_est_neutre(leviers, amenagements):
    resolution = resoudre([], leviers=leviers, amenagements=amenagements)
    assert resolution.valeurs == {nom: levier.neutre for nom, levier in leviers.items()}
    assert resolution.conflits == () and resolution.inconnus == () and resolution.origines == {}


# --- preferences refusees -----------------------------------------------------------------------
@pytest.mark.parametrize(
    "preferences",
    [
        {"lecture-vocale": "proposee"},  # seule « automatique » est une preference hors PAP (§3)
        {"taille-texte": 1.5},  # levier regle par amenagement, pas une preference
        {"police": "comic"},  # hors de la liste fermee
        {"fond": "jaune"},
        {"levier-inconnu": True},
    ],
)
def test_preference_hors_para_3_ignoree_et_signalee(leviers, amenagements, preferences, caplog):
    with caplog.at_level(logging.WARNING, logger="jules"):
        resolution = resoudre([], preferences, leviers=leviers, amenagements=amenagements)
    assert resolution.preferences_ignorees == tuple(preferences)
    assert resolution.valeurs == {nom: levier.neutre for nom, levier in leviers.items()}
    assert "preference(s) du parent ignoree(s)" in caplog.text


# --- sans arguments : lit adaptations/ ----------------------------------------------------------
def test_chargement_par_defaut():
    assert resoudre(ids_cumul()).valeurs == ATTENDU_CUMUL


def test_le_profil_cumul_reste_un_fichier_d_identifiants():
    brut = yaml.safe_load(PROFIL_CUMUL.read_text(encoding="utf-8"))
    assert all(isinstance(i, str) for i in brut["amenagements"])
    assert not {"leviers", "preferences"} & set(brut), "le profil ne stocke que des identifiants"
