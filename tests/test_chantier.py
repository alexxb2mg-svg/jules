"""Appel a contributions : bibliotheques externes, propositions, etat du chantier, paquet de generation."""

from __future__ import annotations

import copy
import json
import shutil
from datetime import date
from pathlib import Path

import pytest
import yaml

from jules.bibliotheques import charger_catalogue, dossier_bibliotheque
from jules.chantier import (
    etat_du_chantier,
    lire_reservations,
    notions_citees,
    paquet,
    rendre_etat,
    version_paquet,
)
from jules.config import depuis_dict
from jules.fiches.commande import dossiers_par_defaut, verifier
from jules.fiches.schema import verifier_fiche

RACINE = Path(__file__).resolve().parents[1]
BIBLIOTHEQUES = RACINE / "bibliotheque"
DEMO = BIBLIOTHEQUES / "fiches-v2-demonstration"
IDENTITE = {
    "id": "fiches-v2-3e",
    "titre": "Fiches v2 3e",
    "type": "fiches",
    "statut": "experimentale",
    "licence": "CC-BY-SA-4.0",
    "niveaux": ["3e"],
    "avertissement": "Expérimental.",
}


def maths() -> dict:
    chemin = next((DEMO / "fiches").rglob("nombres-premiers-decomposition.yaml"))
    return yaml.safe_load(chemin.read_text(encoding="utf-8"))


def ecrire(chemin: Path, contenu: dict) -> Path:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(yaml.safe_dump(contenu, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return chemin


@pytest.fixture
def externe(tmp_path: Path) -> Path:
    """Un depot de bibliotheques a cote du projet, avec une bibliotheque de fiches v2."""
    depot = tmp_path / "jules-bibliotheques"
    ecrire(depot / "fiches-v2-3e" / "bibliotheque.yaml", IDENTITE)
    return depot


# --- bibliotheques externes ---------------------------------------------------------------------


def test_une_bibliotheque_externe_se_charge_apres_celles_du_projet(externe):
    fiche = maths()
    ecrire(externe / "fiches-v2-3e" / "fiches" / "mathematiques" / "nombres-premiers-decomposition.yaml", fiche)
    racines = [BIBLIOTHEQUES, externe]
    assert dossier_bibliotheque(racines, "programme") == BIBLIOTHEQUES / "programme"
    assert dossier_bibliotheque(racines, "fiches-v2-3e") == externe / "fiches-v2-3e"
    catalogue = charger_catalogue(racines, ["programme", "fiches-v2-3e"], "3e")
    assert [b.id for b in catalogue.contenus] == ["fiches-v2-3e"]
    assert catalogue.a_une_fiche("nombres-premiers-decomposition")
    # Une seule racine, comme avant : la bibliotheque externe n'est pas trouvee, Jules continue sans elle.
    assert [b.id for b in charger_catalogue(BIBLIOTHEQUES, ["programme", "fiches-v2-3e"]).contenus] == []


def test_config_bibliotheques_externes_relatives_a_la_racine(tmp_path):
    brut = {"persona": "jules", "profil": "exemple", "bibliotheques_externes": ["../depot", "/absolu/depot"]}
    config = depuis_dict(brut, tmp_path)
    assert config.dossiers_bibliotheques == [tmp_path / "bibliotheque", tmp_path / "../depot", Path("/absolu/depot")]
    assert depuis_dict({"persona": "jules", "profil": "exemple"}, tmp_path).dossiers_bibliotheques == [
        tmp_path / "bibliotheque"
    ]


def test_verifier_parcourt_aussi_les_depots_externes(externe):
    ecrire(externe / "fiches-v2-3e" / "fiches" / "mathematiques" / "nombres-premiers-decomposition.yaml", maths())
    trouves = dossiers_par_defaut([BIBLIOTHEQUES, externe])
    assert DEMO in trouves and externe / "fiches-v2-3e" in trouves


# --- propositions : plusieurs generations pour une notion ----------------------------------------


def test_les_propositions_sont_verifiees_mais_jamais_servies(externe, capsys):
    biblio = externe / "fiches-v2-3e"
    fiche = maths()
    ecrire(biblio / "fiches" / "mathematiques" / "nombres-premiers-decomposition.yaml", fiche)
    autre = copy.deepcopy(fiche)
    autre.update(etat="generee", version=1)
    autre.pop("empreinte")
    ecrire(biblio / "propositions" / "mathematiques" / "nombres-premiers-decomposition" / "camille.yaml", autre)
    # Une proposition double sa notion : pas une collision de declencheurs.
    assert verifier(BIBLIOTHEQUES, [biblio]) == 0
    sortie = capsys.readouterr().out
    assert "propositions/mathematiques/nombres-premiers-decomposition/camille.yaml [generee] OK" in sortie
    catalogue = charger_catalogue([BIBLIOTHEQUES, externe], ["programme", "fiches-v2-3e"], "3e")
    assert catalogue.contenus[0].fiches["nombres-premiers-decomposition"]["etat"] == "verifiee"


def test_une_proposition_mal_rangee_est_refusee(externe, capsys):
    biblio = externe / "fiches-v2-3e"
    ecrire(biblio / "propositions" / "mathematiques" / "camille.yaml", maths())
    assert verifier(BIBLIOTHEQUES, [biblio]) == 1
    assert "propositions/<matiere>/nombres-premiers-decomposition/" in capsys.readouterr().out


# --- etat du chantier ---------------------------------------------------------------------------


def test_notions_citees_ne_prend_que_les_lignes_d_identifiants():
    notions = {"ratio", "racine-carree", "fractions-irreductibles"}
    corps = "### Notions\n\nracine-carree, `ratio`\n- fractions-irreductibles\n\nJe connais bien le ratio."
    assert notions_citees(corps, notions) == ["racine-carree", "ratio", "fractions-irreductibles"]
    assert notions_citees("Je prends le ratio et la racine-carree", notions) == []


def test_etat_du_chantier(externe, tmp_path):
    biblio = externe / "fiches-v2-3e"
    fiche = maths()
    ecrire(biblio / "fiches" / "mathematiques" / "nombres-premiers-decomposition.yaml", fiche)
    modifiee = copy.deepcopy(fiche)
    modifiee["notion"] = "fractions-irreductibles"  # verifiee, mais le contenu ne correspond plus a l'empreinte
    ecrire(biblio / "fiches" / "mathematiques" / "fractions-irreductibles.yaml", modifiee)
    proposition = copy.deepcopy(fiche)
    ecrire(biblio / "propositions" / "mathematiques" / "nombres-premiers-decomposition" / "lou.yaml", proposition)
    tickets = tmp_path / "tickets.json"
    corps = "racine-carree\nnombres-premiers-decomposition"
    ouvert = {"number": 7, "body": corps, "author": {"login": "camille"}, "updatedAt": "2026-09-20T10:00:00Z"}
    oublie = {"number": 2, "body": "ratio", "author": {"login": "lou"}, "updatedAt": "2026-08-01T10:00:00Z"}
    tickets.write_text(json.dumps([ouvert, oublie]), encoding="utf-8")
    notions = set(charger_catalogue(BIBLIOTHEQUES, ["programme"]).notions)
    reservations = lire_reservations(tickets, notions, jour=date(2026, 9, 26))
    assert "ratio" not in reservations  # plus de 21 jours sans activite : la reservation est tombee

    etats = {e.notion.id: e for e in etat_du_chantier([BIBLIOTHEQUES], [biblio], reservations)}
    assert len(etats) == len(notions)
    assert etats["nombres-premiers-decomposition"].etat == "verifiee"
    assert etats["nombres-premiers-decomposition"].propositions == 1
    assert etats["nombres-premiers-decomposition"].reservations == [(7, "camille")]
    assert etats["fractions-irreductibles"].etat == "a reverifier"
    assert etats["racine-carree"].etat == "reservee"
    assert etats["ratio"].etat == "a faire"

    page = rendre_etat(list(etats.values()), depot="exemple/depot", jour="2026-09-26")
    assert "*Page générée le 2026-09-26" in page
    assert "| 3e | 252 | 249 | 1 | 0 | 1 | 1 | 0 | 0 % |" in page
    assert "| Racine carrée (`racine-carree`) |" in page
    assert "@camille ([#7](https://github.com/exemple/depot/issues/7))" in page


# --- paquet de generation -----------------------------------------------------------------------


def test_paquet_contient_contrat_modele_attendus_et_regles():
    texte = paquet([BIBLIOTHEQUES], ["racine-carree", "guerre-totale-1914-1918"], par="camille", jour="2026-09-26")
    assert "Tu vas écrire 2 fiche(s)" in texte
    assert "## Le contrat" in texte and "## Les types d'exercice" in texte  # extrait de docs/FICHES-V2.md
    assert "N'invente jamais une source ni une URL" in texte
    assert 'par: "camille"' in texte and 'le: "2026-09-26"' in texte and version_paquet() in texte
    assert "`racine-carree`" in texte and "fiches/mathematiques/racine-carree.yaml" in texte
    assert "Attendus officiels" in texte and "etalab-2.0" in texte
    # Fiche modele : jamais celle d'une notion demandee, et presentee comme generee, sans empreinte.
    assert "Une fiche conforme, pour la forme seulement (`nombres-premiers-decomposition`)" in texte
    modele = texte.split("## Une fiche conforme")[1].split("## Les notions")[0]
    assert "notion: nombres-premiers-decomposition" in modele and "etat: generee" in modele
    assert "empreinte" not in modele


def test_paquet_prerequis_de_la_meme_matiere_et_du_niveau_d_avant():
    texte = paquet([BIBLIOTHEQUES], ["racine-carree"])
    prerequis = texte.split("Prérequis possibles")[1]
    assert "`4e-racine-carree`" in prerequis and "`puissances-notation-scientifique`" in prerequis
    assert "`racine-carree`" not in prerequis and "`guerre-totale-1914-1918`" not in prerequis
    assert "cm1-" not in prerequis and "5e-" not in prerequis


def test_paquet_refuse_une_notion_inconnue():
    with pytest.raises(ValueError, match="inconnue"):
        paquet([BIBLIOTHEQUES], ["racine-carree", "pas-une-notion"])


def test_la_generation_peut_dire_son_modele_et_son_paquet():
    fiche = maths()
    fiche["generation"] = {"par": "camille", "le": "2026-09-26", "modele": "x", "paquet": version_paquet()}
    notions = set(charger_catalogue(BIBLIOTHEQUES, ["programme"]).notions)
    assert not [e for e in verifier_fiche(fiche, notions, controler_empreinte=False) if "generation" in e]
    fiche["generation"]["outil"] = "?"
    assert [e for e in verifier_fiche(fiche, notions, controler_empreinte=False) if "generation" in e]


def test_paquet_sans_depot_de_demonstration(tmp_path):
    """Un paquet reste utilisable si la bibliotheque de demonstration manque (pas de fiche modele)."""
    shutil.copytree(BIBLIOTHEQUES / "programme", tmp_path / "programme")
    texte = paquet([tmp_path], ["ratio"])
    assert "Une fiche conforme" not in texte and "`ratio`" in texte


def test_un_yaml_casse_est_un_manquement_pas_un_plantage(externe, capsys):
    biblio = externe / "fiches-v2-3e"
    chemin = biblio / "fiches" / "mathematiques" / "ratio.yaml"
    chemin.parent.mkdir(parents=True)
    chemin.write_text("format: 2\nnotion: ratio\nessentiel: le ratio 2 : 3 se lit\n  deux pour trois : ok\n", "utf-8")
    assert verifier(BIBLIOTHEQUES, [biblio]) == 1
    assert "ratio.yaml YAML illisible" in capsys.readouterr().out
