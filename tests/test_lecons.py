"""Tests du module lecons (lecture, verification, correction, chargement par bibliotheque)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from jules.bibliotheques import Bibliotheque, Notion
from jules.config import Config, RefBrique
from jules.lecons import (
    Bloc,
    ErreurLecon,
    charger_lecons,
    contient_la_reponse,
    lire_lecon,
    verifier_reponse,
)

RACINE = Path(__file__).resolve().parents[1]


def ecrire(chemin: Path, contenu: dict) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(yaml.safe_dump(contenu, allow_unicode=True), encoding="utf-8")


def notions() -> dict[str, Notion]:
    return {
        "pythagore": Notion(
            id="pythagore", titre="Théorème de Pythagore", matiere="maths", nom_matiere="Maths", niveau="3e"
        ),
    }


def bibliotheque(dossier: Path, licence: str = "CC-BY-SA-4.0") -> Bibliotheque:
    return Bibliotheque(
        id="lecons-test",
        titre="Lecons de test",
        type="lecons",
        statut="experimentale",
        licence=licence,
        dossier=dossier,
        avertissement="Contenu de test.",
    )


def blocs_valides() -> list[dict]:
    """Un jeu minimal (4 blocs) qui respecte toutes les regles du contrat."""
    return [
        {"type": "objectifs", "items": ["Calculer une longueur"]},
        {"type": "texte", "titre": "L'idee", "contenu": "Dans un triangle rectangle, BC² = AB² + AC²."},
        {
            "type": "exercice",
            "enonce": "AB = 6 cm, AC = 8 cm. Calcule BC.",
            "forme": "nombre",
            "reponse": 10,
            "tolerance": 0.01,
            "unite": "cm",
            "indices": ["Quel est le plus grand cote ?", "Ecris l'egalite de Pythagore."],
            "explication": "BC = 10 cm.",
        },
        {"type": "synthese", "consigne": "Ecris en deux phrases ce que tu retiens."},
    ]


def lecon_valide(matiere_id: str = "pythagore", **remplacements) -> dict:
    donnees = {
        "notion": "pythagore",
        "titre": "Le theoreme de Pythagore",
        "duree_minutes": 25,
        "licence": "CC-BY-SA-4.0",
        "sources": [{"titre": "Manuel", "url": "https://exemple.fr/pythagore", "licence": "CC-BY-SA-4.0"}],
        "relecture": {"statut": "a_relire"},
        "blocs": blocs_valides(),
    }
    donnees.update(remplacements)
    return donnees


@pytest.fixture
def biblio(tmp_path: Path) -> Bibliotheque:
    return bibliotheque(tmp_path)


# --- lire_lecon : cas valide --------------------------------------------------


def test_lecon_valide_est_lue(tmp_path, biblio):
    fichier = tmp_path / "pythagore.yaml"
    ecrire(fichier, lecon_valide())
    lecon = lire_lecon(fichier, notions(), biblio)
    assert lecon.notion == "pythagore"
    assert lecon.titre == "Le theoreme de Pythagore"
    assert lecon.matiere == "maths" and lecon.niveau == "3e"
    assert lecon.bibliotheque == "lecons-test" and lecon.statut == "experimentale"
    assert len(lecon.blocs) == 4
    assert lecon.sources and lecon.sources[0]["titre"] == "Manuel"


# --- lire_lecon : chaque regle de refus du contrat, message clair ------------


def test_notion_inconnue_refusee(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    ecrire(fichier, lecon_valide(notion="nexistepas"))
    with pytest.raises(ErreurLecon, match="inconnue"):
        lire_lecon(fichier, notions(), biblio)


def test_type_de_bloc_inconnu_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    blocs = blocs_valides()
    blocs[0] = {"type": "video", "url": "https://exemple.fr"}
    ecrire(fichier, lecon_valide(blocs=blocs))
    with pytest.raises(ErreurLecon, match="type"):
        lire_lecon(fichier, notions(), biblio)


def test_exercice_sans_reponse_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    blocs = blocs_valides()
    del blocs[2]["reponse"]
    ecrire(fichier, lecon_valide(blocs=blocs))
    with pytest.raises(ErreurLecon, match="reponse"):
        lire_lecon(fichier, notions(), biblio)


def test_exercice_forme_inconnue_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    blocs = blocs_valides()
    blocs[2]["forme"] = "dessin"
    ecrire(fichier, lecon_valide(blocs=blocs))
    with pytest.raises(ErreurLecon, match="forme"):
        lire_lecon(fichier, notions(), biblio)


def test_qcm_sans_choix_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    blocs = blocs_valides()
    blocs[2] = {"type": "exercice", "enonce": "1+1 ?", "forme": "qcm", "reponse": 0, "choix": ["2"]}
    ecrire(fichier, lecon_valide(blocs=blocs))
    with pytest.raises(ErreurLecon, match="deux choix"):
        lire_lecon(fichier, notions(), biblio)


def test_qcm_reponse_hors_choix_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    blocs = blocs_valides()
    blocs[2] = {
        "type": "exercice",
        "enonce": "1+1 ?",
        "forme": "qcm",
        "reponse": "5",
        "choix": ["2", "3"],
    }
    ecrire(fichier, lecon_valide(blocs=blocs))
    with pytest.raises(ErreurLecon, match="qcm"):
        lire_lecon(fichier, notions(), biblio)


def test_indice_qui_contient_la_reponse_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    blocs = blocs_valides()
    blocs[2]["indices"] = ["La reponse est 10 cm."]
    ecrire(fichier, lecon_valide(blocs=blocs))
    with pytest.raises(ErreurLecon, match="indice"):
        lire_lecon(fichier, notions(), biblio)


def test_moins_de_trois_blocs_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    ecrire(fichier, lecon_valide(blocs=blocs_valides()[:2]))
    with pytest.raises(ErreurLecon, match="blocs"):
        lire_lecon(fichier, notions(), biblio)


def test_plus_de_vingt_blocs_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    blocs = [{"type": "texte", "titre": "T", "contenu": "..."} for _ in range(21)]
    ecrire(fichier, lecon_valide(blocs=blocs))
    with pytest.raises(ErreurLecon, match="blocs"):
        lire_lecon(fichier, notions(), biblio)


def test_aucune_source_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    ecrire(fichier, lecon_valide(sources=[]))
    with pytest.raises(ErreurLecon, match="source"):
        lire_lecon(fichier, notions(), biblio)


def test_licence_non_libre_refusee(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    ecrire(fichier, lecon_valide(licence="tous-droits-reserves"))
    with pytest.raises(ErreurLecon, match="licence"):
        lire_lecon(fichier, notions(), biblio)


def test_fichier_trop_gros_refuse(tmp_path, biblio):
    fichier = tmp_path / "x.yaml"
    donnees = lecon_valide()
    donnees["blocs"][1]["contenu"] = "x" * 250_000
    ecrire(fichier, donnees)
    with pytest.raises(ErreurLecon, match="gros"):
        lire_lecon(fichier, notions(), biblio)


# --- Bloc.public() ne laisse jamais fuir les champs serveur -----------------


def test_bloc_public_ne_fuit_jamais_la_reponse(tmp_path, biblio):
    """Cherche la valeur de la reponse (10) dans le JSON serialise de Lecon.publique() entiere."""
    fichier = tmp_path / "x.yaml"
    ecrire(fichier, lecon_valide())
    lecon = lire_lecon(fichier, notions(), biblio)
    public = lecon.publique()
    serialise = json.dumps(public, ensure_ascii=False)
    for champ in ("reponse", "reponses_acceptees", "tolerance", "explication", "criteres"):
        assert champ not in serialise
    # la valeur de la reponse elle-meme (10) ne doit apparaitre nulle part (hors la note 4e bloc, "10 cm" absent)
    assert "10 cm" not in serialise
    assert "BC = 10" not in serialise
    bloc_exercice = next(b for b in public["blocs"] if b["type"] == "exercice")
    assert set(bloc_exercice) == {"index", "type", "enonce", "forme", "unite", "indices"}


def test_bloc_public_qcm_ne_fuit_pas_lindex():
    bloc = Bloc(
        "exercice",
        {"enonce": "1+1 ?", "forme": "qcm", "choix": ["1", "2", "3"], "reponse": 1, "explication": "car 1+1=2"},
    )
    public = bloc.public()
    assert "reponse" not in public and "explication" not in public
    assert set(public) == {"type", "enonce", "forme", "choix"}


def test_bloc_public_question_ouverte_ne_fuit_pas_les_criteres():
    bloc = Bloc("question_ouverte", {"question": "Pourquoi ?", "criteres": ["cite un exemple"]})
    public = bloc.public()
    assert "criteres" not in public


# --- verifier_reponse : nombre ------------------------------------------------


@pytest.mark.parametrize(
    "reponse",
    ["10", "10.0", "10,0", " 10 ", "10cm", "10 cm", "10\u202fcm", "10\xa0cm"],
)
def test_verifier_reponse_nombre_formes_variees(reponse):
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": 10, "tolerance": 0.01})
    assert verifier_reponse(bloc, reponse) is True


def test_verifier_reponse_nombre_tolerance():
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": 10, "tolerance": 0.5})
    assert verifier_reponse(bloc, "10.4") is True
    assert verifier_reponse(bloc, "10.6") is False


def test_verifier_reponse_nombre_faux():
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": 10, "tolerance": 0.01})
    assert verifier_reponse(bloc, "9") is False


def test_verifier_reponse_nombre_non_numerique():
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": 10})
    assert verifier_reponse(bloc, "dix") is False
    assert verifier_reponse(bloc, "") is False


# --- verifier_reponse : reponse_courte ---------------------------------------


@pytest.mark.parametrize(
    "reponse",
    ["hypoténuse", "Hypoténuse", "HYPOTENUSE", "hypotenuse.", "hypotenuse !", " hypoténuse "],
)
def test_verifier_reponse_courte_casse_accents_ponctuation(reponse):
    bloc = Bloc("exercice", {"forme": "reponse_courte", "reponse": "hypoténuse"})
    assert verifier_reponse(bloc, reponse) is True


def test_verifier_reponse_courte_variante_acceptee():
    bloc = Bloc(
        "exercice",
        {"forme": "reponse_courte", "reponse": "hypoténuse", "reponses_acceptees": ["le plus grand cote"]},
    )
    assert verifier_reponse(bloc, "le plus grand côté") is True
    assert verifier_reponse(bloc, "autre chose") is False


# --- verifier_reponse : qcm ---------------------------------------------------


def test_verifier_reponse_qcm_index_int():
    bloc = Bloc("exercice", {"forme": "qcm", "choix": ["Faux", "Vrai"], "reponse": 1})
    assert verifier_reponse(bloc, 1) is True
    assert verifier_reponse(bloc, 0) is False


def test_verifier_reponse_qcm_index_texte():
    bloc = Bloc("exercice", {"forme": "qcm", "choix": ["Faux", "Vrai"], "reponse": 1})
    assert verifier_reponse(bloc, "1") is True


def test_verifier_reponse_qcm_texte_du_choix():
    bloc = Bloc("exercice", {"forme": "qcm", "choix": ["Faux", "Vrai"], "reponse": 1})
    assert verifier_reponse(bloc, "vrai") is True
    assert verifier_reponse(bloc, "Faux") is False


def test_verifier_reponse_qcm_reponse_donnee_par_texte_du_choix():
    """La reponse elle-meme peut etre le texte du choix (pas seulement son index)."""
    bloc = Bloc("exercice", {"forme": "qcm", "choix": ["Faux", "Vrai"], "reponse": "Vrai"})
    assert verifier_reponse(bloc, 1) is True
    assert verifier_reponse(bloc, "vrai") is True


# --- verifier_reponse : None pour question_ouverte / synthese ---------------


def test_verifier_reponse_none_pour_question_ouverte():
    bloc = Bloc("question_ouverte", {"question": "Pourquoi ?"})
    assert verifier_reponse(bloc, "parce que") is None


def test_verifier_reponse_none_pour_synthese():
    bloc = Bloc("synthese", {"consigne": "Resume."})
    assert verifier_reponse(bloc, "voila mon resume") is None


def test_verifier_reponse_none_pour_bloc_non_exercice_texte():
    bloc = Bloc("texte", {"contenu": "..."})
    assert verifier_reponse(bloc, "10") is None


# --- contient_la_reponse : detection et faux positifs -------------------------


def test_contient_la_reponse_detecte_le_nombre_avec_unite():
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": 10, "tolerance": 0.01})
    assert contient_la_reponse("Donc BC = 10 cm.", bloc) is True


def test_contient_la_reponse_ignore_un_nombre_different():
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": 10, "tolerance": 0.01})
    assert contient_la_reponse("As-tu essaye avec 100 ?", bloc) is False


def test_contient_la_reponse_moins_typographique():
    """Les modeles ecrivent souvent le moins typographique (U+2212) : « x = −3 » donne bien la reponse -3."""
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": -3, "tolerance": 0.01})
    assert contient_la_reponse("Donc x = \u22123 !", bloc) is True
    assert contient_la_reponse("tu as presque trouvé (\u22123.8 au lieu de \u22123)", bloc) is True
    assert contient_la_reponse("7 \u2212 2x = 3x + 22", bloc) is False  # l'enonce seul ne donne pas -3
    assert verifier_reponse(bloc, "\u22123") is True


def test_contient_la_reponse_faux_positif_numero_de_question():
    """Pour une reponse 1 ou 2, un message 'Question 1/2' ne doit pas etre bloque a tort."""
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": 1, "tolerance": 0.01})
    assert contient_la_reponse("Regarde la question 1/2 de l'exercice.", bloc) is False
    bloc2 = Bloc("exercice", {"forme": "nombre", "reponse": 2, "tolerance": 0.01})
    assert contient_la_reponse("C'est l'exercice 2, deuxieme partie.", bloc2) is False


def test_contient_la_reponse_detecte_quand_meme_le_petit_nombre_hors_contexte():
    """Le meme petit nombre, hors contexte 'question/exercice/N/N', doit rester detecte."""
    bloc = Bloc("exercice", {"forme": "nombre", "reponse": 2, "tolerance": 0.01})
    assert contient_la_reponse("La reponse est 2.", bloc) is True


def test_contient_la_reponse_reponse_courte():
    bloc = Bloc("exercice", {"forme": "reponse_courte", "reponse": "hypoténuse"})
    assert contient_la_reponse("C'est l'HYPOTENUSE, le plus grand cote.", bloc) is True
    assert contient_la_reponse("C'est le plus grand cote.", bloc) is False


def test_contient_la_reponse_qcm_texte_long():
    bloc = Bloc("exercice", {"forme": "qcm", "choix": ["Faux", "Theoreme de Pythagore"], "reponse": 1})
    assert contient_la_reponse("Utilise le theoreme de Pythagore ici.", bloc) is True
    assert contient_la_reponse("Non.", bloc) is False


def test_contient_la_reponse_faux_pour_non_exercice():
    bloc = Bloc("texte", {"contenu": "10 cm"})
    assert contient_la_reponse("10 cm", bloc) is False


# --- charger_lecons : priorite, isolation des erreurs, type de bibliotheque -


def preparer_referentiel(tmp_path: Path) -> None:
    ecrire(
        tmp_path / "programme" / "bibliotheque.yaml",
        {"id": "programme", "type": "referentiel", "statut": "experimentale", "licence": "MIT", "niveaux": ["3e"]},
    )


@pytest.fixture
def lecons_dir(tmp_path: Path) -> Path:
    """Racine bibliotheque/ avec deux bibliotheques de lecons en concurrence sur 'pythagore'."""
    for biblio_id, titre in (("lecons-a", "Version A"), ("lecons-b", "Version B")):
        ecrire(
            tmp_path / biblio_id / "bibliotheque.yaml",
            {
                "id": biblio_id,
                "type": "lecons",
                "statut": "experimentale",
                "licence": "CC-BY-SA-4.0",
                "avertissement": "Test.",
            },
        )
        ecrire(tmp_path / biblio_id / "lecons" / "maths" / "pythagore.yaml", lecon_valide(titre=titre))
    return tmp_path


def test_charger_lecons_priorite_premiere_bibliotheque(lecons_dir):
    lecons = charger_lecons(lecons_dir, ["lecons-a", "lecons-b"], notions())
    assert lecons["pythagore"].titre == "Version A"


def test_charger_lecons_priorite_inversee(lecons_dir):
    lecons = charger_lecons(lecons_dir, ["lecons-b", "lecons-a"], notions())
    assert lecons["pythagore"].titre == "Version B"


def test_charger_lecons_lecon_invalide_ecartee_sans_bloquer(tmp_path):
    ecrire(
        tmp_path / "lecons-a" / "bibliotheque.yaml",
        {
            "id": "lecons-a",
            "type": "lecons",
            "statut": "experimentale",
            "licence": "CC-BY-SA-4.0",
            "avertissement": "T",
        },
    )
    ecrire(tmp_path / "lecons-a" / "lecons" / "maths" / "pythagore.yaml", lecon_valide())
    ecrire(tmp_path / "lecons-a" / "lecons" / "maths" / "cassee.yaml", lecon_valide(notion="nexistepas"))
    lecons = charger_lecons(tmp_path, ["lecons-a"], notions())
    assert list(lecons) == ["pythagore"]


def test_charger_lecons_bibliotheque_mauvais_type_ecartee(tmp_path):
    ecrire(
        tmp_path / "pas-des-lecons" / "bibliotheque.yaml",
        {"id": "pas-des-lecons", "type": "fiches", "statut": "experimentale", "licence": "MIT", "avertissement": "T"},
    )
    lecons = charger_lecons(tmp_path, ["pas-des-lecons"], notions())
    assert lecons == {}


def test_charger_lecons_bibliotheque_absente_ecartee(tmp_path):
    lecons = charger_lecons(tmp_path, ["nexistepas"], notions())
    assert lecons == {}


# --- jules verifier : controle des lecons du module 'cours' -----------------


def _config_avec_module_cours(tmp_path: Path, reglages_cours: dict | None) -> Config:
    modules = [RefBrique(id="notions")]
    if reglages_cours is not None:
        modules.append(RefBrique(id="cours", reglages=reglages_cours))
    return Config(
        racine=tmp_path,
        donnees=tmp_path / "donnees",
        hote="127.0.0.1",
        port=8795,
        persona="jules",
        profil="exemple",
        llm={},
        acces={},
        modules=modules,
        notifieurs=[],
    )


def _preparer_bibliotheques_cours(tmp_path: Path) -> None:
    """Un referentiel minimal + une bibliotheque 'lecons' avec une lecon valide et une invalide."""
    ecrire(
        tmp_path / "bibliotheque" / "programme" / "bibliotheque.yaml",
        {
            "id": "programme",
            "type": "referentiel",
            "statut": "experimentale",
            "licence": "MIT",
            "niveaux": ["3e"],
            "avertissement": "Test.",
        },
    )
    ecrire(
        tmp_path / "bibliotheque" / "programme" / "3e" / "maths.yaml",
        {
            "matiere": "Maths",
            "id": "maths",
            "themes": [
                {
                    "titre": "Géométrie",
                    "chapitres": [
                        {
                            "titre": "Triangles",
                            "notions": [{"id": "pythagore", "titre": "Théorème de Pythagore"}],
                        }
                    ],
                }
            ],
        },
    )
    ecrire(
        tmp_path / "bibliotheque" / "lecons-3e-test" / "bibliotheque.yaml",
        {
            "id": "lecons-3e-test",
            "type": "lecons",
            "statut": "experimentale",
            "licence": "CC-BY-SA-4.0",
            "niveaux": ["3e"],
            "avertissement": "Test.",
        },
    )
    ecrire(tmp_path / "bibliotheque" / "lecons-3e-test" / "lecons" / "maths" / "pythagore.yaml", lecon_valide())
    ecrire(
        tmp_path / "bibliotheque" / "lecons-3e-test" / "lecons" / "maths" / "cassee.yaml",
        lecon_valide(notion="nexistepas"),
    )


def test_verifier_lecons_charge_et_rapporte_les_ecarts(tmp_path, capsys):
    from jules.cli import verifier_lecons

    _preparer_bibliotheques_cours(tmp_path)
    config = _config_avec_module_cours(tmp_path, {"bibliotheques": ["lecons-3e-test"]})
    verifier_lecons(config)
    sortie = capsys.readouterr().out
    assert "1 lecon(s) chargee(s)" in sortie and "pythagore" in sortie
    assert "1 lecon(s) ecartee(s)" in sortie and "nexistepas" in sortie


def test_verifier_lecons_sans_module_cours_ne_fait_rien(tmp_path, capsys):
    """Comportement d'avant l'etape 2 inchange quand le module 'cours' n'est pas dans la config."""
    from jules.cli import verifier_lecons

    config = _config_avec_module_cours(tmp_path, reglages_cours=None)
    verifier_lecons(config)
    sortie = capsys.readouterr().out
    assert sortie == ""


def test_verifier_lecons_module_cours_sans_bibliotheques(tmp_path, capsys):
    from jules.cli import verifier_lecons

    config = _config_avec_module_cours(tmp_path, {})
    verifier_lecons(config)
    sortie = capsys.readouterr().out
    assert "rien a charger" in sortie
