"""Tests des bibliotheques et du module 'notions' (choix, detection, prompt, statut experimental)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from jules.bibliotheques import (
    LICENCES_LIBRES,
    ErreurBibliotheque,
    candidats,
    charger_catalogue,
    lire_identite,
    texte_direction,
    texte_fiche,
)
from jules.modules.notions import niveau_du_profil
from jules.stockage import Message
from jules.web.app import creer_app

RACINE = Path(__file__).resolve().parents[1]
BIBLIOTHEQUES = RACINE / "bibliotheque"


def ecrire(chemin: Path, contenu: dict) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(yaml.safe_dump(contenu, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def mini(tmp_path: Path) -> Path:
    """Un referentiel de deux notions, une bibliotheque de fiches experimentale, une direction d'enseignant."""
    ecrire(
        tmp_path / "ref" / "bibliotheque.yaml",
        {
            "id": "ref",
            "type": "referentiel",
            "statut": "exemple",
            "licence": "MIT",
            "niveaux": ["3e"],
            "avertissement": "fictif",
        },
    )
    ecrire(
        tmp_path / "ref" / "3e" / "maths.yaml",
        {
            "matiere": "Maths",
            "id": "maths",
            "themes": [
                {
                    "titre": "Géométrie",
                    "chapitres": [
                        {
                            "titre": "Triangles",
                            "notions": [
                                {
                                    "id": "pythagore",
                                    "titre": "Théorème de Pythagore",
                                    "attendus": ["Calculer une longueur"],
                                    "mots_cles": ["Pythagore", "hypoténuse"],
                                },
                                {"id": "thales", "titre": "Théorème de Thalès", "mots_cles": ["Thalès"]},
                            ],
                        }
                    ],
                }
            ],
        },
    )
    ecrire(tmp_path / "ref" / "3e" / "_annexe.yaml", {"dnb": {}})
    ecrire(
        tmp_path / "fiches" / "bibliotheque.yaml",
        {
            "id": "fiches",
            "type": "fiches",
            "statut": "experimentale",
            "licence": "CC-BY-SA-4.0",
            "niveaux": ["3e"],
            "avertissement": "Pour tester.",
        },
    )
    ecrire(
        tmp_path / "fiches" / "fiches" / "maths" / "pythagore.yaml",
        {
            "notion": "pythagore",
            "essentiel": "Dans un triangle rectangle, BC² = AB² + AC².",
            "methode": ["Repérer l'angle droit", "Écrire l'égalité"],
            "erreurs_frequentes": ["Oublier la racine carrée"],
            "exercices": [{"enonce": "AB = 3, AC = 4 : BC ?", "indices": ["Le plus grand côté ?"], "solution": "5"}],
            "sources": [{"titre": "Sésamath", "licence": "CC-BY-SA-2.0-FR"}],
        },
    )
    ecrire(tmp_path / "fiches" / "fiches" / "maths" / "inconnue.yaml", {"notion": "nexistepas", "essentiel": "x"})
    ecrire(
        tmp_path / "prof" / "bibliotheque.yaml",
        {"id": "prof", "type": "direction", "statut": "enseignant", "licence": "MIT", "niveaux": ["3e"]},
    )
    ecrire(
        tmp_path / "prof" / "matieres" / "maths.yaml",
        {"matiere": "maths", "direction": {"redaction_attendue": "On sait que... Or... Donc..."}},
    )
    ecrire(
        tmp_path / "prof" / "fiches" / "pythagore.yaml",
        {"notion": "pythagore", "essentiel": "Version du professeur.", "direction": {"a_eviter": ["La calculatrice"]}},
    )
    return tmp_path


# --- lecture et verification -------------------------------------------------


def test_catalogue_priorite_et_directions(mini):
    cat = charger_catalogue(mini, ["ref", "prof", "fiches"], "3e")
    assert set(cat.notions) == {"pythagore", "thales"}  # l'annexe _annexe.yaml est ignoree
    fiche, origines = cat.fiche("pythagore")
    assert fiche["essentiel"] == "Version du professeur."  # la premiere bibliotheque citee l'emporte
    assert fiche["methode"][0] == "Repérer l'angle droit"  # complete par la suivante
    assert [b.id for b in origines] == ["prof", "fiches"]
    directions = cat.directions(cat.notion("pythagore"))
    assert [b.id for b, _ in directions] == ["prof", "prof"]
    assert not cat.a_une_fiche("thales")
    assert all("nexistepas" not in b.fiches for b in cat.contenus)  # fiche sur notion inconnue ignoree


def test_bibliotheque_invalide_ecartee_sans_bloquer(mini):
    ecrire(mini / "cassee" / "bibliotheque.yaml", {"id": "cassee", "type": "fiches", "statut": "experimentale"})
    cat = charger_catalogue(mini, ["ref", "cassee", "../ref", "absente"], "3e")
    assert len(cat.notions) == 2 and cat.contenus == []


def test_experimentale_sans_avertissement_refusee(mini):
    ecrire(mini / "x" / "bibliotheque.yaml", {"id": "x", "type": "fiches", "statut": "experimentale", "licence": "MIT"})
    with pytest.raises(ErreurBibliotheque):
        lire_identite(mini / "x")


def test_niveau_filtre(mini):
    assert charger_catalogue(mini, ["ref", "fiches"], "5e").notions == {}
    assert niveau_du_profil("3ème") == "3e"
    assert niveau_du_profil("troisième B") == "3e"
    assert niveau_du_profil("") is None


def test_candidats_par_mots_cles(mini):
    cat = charger_catalogue(mini, ["ref"], None)
    assert candidats(cat, "je dois calculer l'hypoténuse avec pythagore")[0].id == "pythagore"
    assert candidats(cat, "bonjour") == []


def test_fiches_experimentales_dans_le_prompt_mais_pas_la_direction_exemple():
    """La config publiee charge les fiches experimentales, jamais l'enseignant fictif."""
    config = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))
    reglages = next(m for m in config["modules"] if m["id"] == "notions")["reglages"]
    assert "fiches-3e-experimentales" in reglages["bibliotheques"]
    assert "exemple-direction-enseignant" not in reglages["bibliotheques"]


def test_direction_exemple_publiee(tuteur):
    cat = charger_catalogue(BIBLIOTHEQUES, ["programme", "exemple-direction-enseignant"], "3e")
    notion = cat.notion("parallelisme-triangles-pythagore")
    textes = [texte_direction(d) for _, d in cat.directions(notion)]
    assert "On sait que" in textes[0] and "égalité de Pythagore" in textes[1]
    assert not cat.a_une_fiche(notion.id)  # une direction seule n'est pas une fiche de cours


def test_fiche_tronquee():
    texte = texte_fiche({"essentiel": "a\n" * 5000}, limite=100)
    assert len(texte) < 130 and texte.endswith("[… fiche tronquée]")


# --- module dans le tuteur ------------------------------------------------------


def test_choix_eleve_nourrit_le_prompt(tuteur):
    module = tuteur.module("notions")
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    module.fixer(conv.id, "parallelisme-triangles-pythagore", origine="eleve")
    systeme = tuteur.systeme(tuteur.stockage.conversation(conv.id))
    assert "# Notion travaillée" in systeme
    assert "choisie par l'élève" in systeme
    assert "Ce que le programme attend" in systeme
    # la fiche experimentale est bien la, annoncee comme telle
    assert "EXPÉRIMENTAL" in systeme and "Erreurs fréquentes" in systeme
    # la securite reste en dernier
    assert systeme.index("# Notion travaillée") < systeme.index("# Securite")


def test_detection_automatique_sur_le_premier_message(tuteur):
    def regle(systeme, tours, modele):
        if "UNE notion d'une liste fermée" in systeme:
            assert "racine-carree" in systeme  # la liste est pre-filtree par mots-cles
            return '{"notion": "parallelisme-triangles-pythagore", "confiance": "haute"}'
        return "D'accord."

    tuteur.llm.regle = regle
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "Je dois utiliser Pythagore pour trouver l'hypoténuse, avec une racine carrée")
    tuteur.attendre_fond()
    module = tuteur.module("notions")
    assert module.notion_de(conv.id)["origine"] == "auto"
    appel_principal = next(a for a in tuteur.llm.appels if a["modele"] == "principal")
    assert "reconnue automatiquement" in appel_principal["systeme"]


def test_detection_sur_photo_seule(tuteur):
    vus = {}

    def regle(systeme, tours, modele):
        if "UNE notion d'une liste fermée" in systeme:
            vus["images"] = len(tours[0].images)
            return '{"notion": "fonctions-lineaires-affines", "confiance": "moyenne"}'
        return "Je vois ton exercice."

    tuteur.llm.regle = regle
    nom = tuteur.stockage.enregistrer_image(b"\x89PNG\r\n\x1a\n" + b"0" * 20, "png")
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.echanger(conv.id, "", [nom])
    assert vus["images"] == 1
    assert tuteur.module("notions").notion_de(conv.id)["id"] == "fonctions-lineaires-affines"


def test_detection_rejette_une_notion_inventee(tuteur):
    tuteur.llm.regle = lambda s, t, m: '{"notion": "inventee", "confiance": "haute"}' if "liste fermée" in s else "ok"
    module = tuteur.module("notions")
    assert module.detecter(Message(role="eleve", texte="Pythagore hypoténuse")) is None


def test_choix_eleve_non_ecrase_par_la_detection(tuteur):
    detection = '{"notion": "racine-carree", "confiance": "haute"}'
    tuteur.llm.regle = lambda s, t, m: detection if "liste fermée" in s else "ok"
    module = tuteur.module("notions")
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    module.fixer(conv.id, "ratio")
    tuteur.echanger(conv.id, "racine carrée de 49")
    assert module.notion_de(conv.id)["id"] == "ratio"
    module.retirer(conv.id)
    tuteur.echanger(conv.id, "racine carrée de 49")
    assert module.notion_de(conv.id) is None  # retiree par l'eleve : on ne redevine pas


def test_routes_eleve(tuteur):
    with TestClient(creer_app(tuteur)) as client:
        conv = client.post("/api/conversations", json={"mode": "aide-devoirs"}).json()
        url = f"/api/eleve/notions/conversations/{conv['id']}"
        assert client.get(url).json() == {"notion": None}
        assert client.put(url, json={"notion": "inventee"}).status_code == 400
        r = client.put(url, json={"notion": "racine-carree"}).json()
        assert r["notion"]["titre"] == "Racine carrée" and r["notion"]["origine"] == "eleve"
        assert client.delete(url).json() == {"notion": None}
        assert client.get("/api/eleve/notions/conversations/inconnue").status_code == 404
        infos = client.get("/api/infos").json()["notions"]
        assert any(b["statut"] == "experimentale" and b["avertissement"] for b in infos["bibliotheques"])
        assert sum(len(m["notions"]) for m in infos["matieres"]) == 252


# --- les bibliotheques publiees ---------------------------------------------------


def bibliotheques_publiees() -> list[Path]:
    return sorted(p.parent for p in BIBLIOTHEQUES.glob("*/bibliotheque.yaml"))


@pytest.mark.parametrize("dossier", bibliotheques_publiees(), ids=lambda p: p.name)
def test_bibliotheque_publiee_valide(dossier):
    biblio = lire_identite(dossier)
    if biblio.type == "referentiel":
        return
    assert biblio.licence in LICENCES_LIBRES, "licence non reconnue comme libre"
    if biblio.type == "direction":
        cat = charger_catalogue(BIBLIOTHEQUES, ["programme", biblio.id], None)
        assert all(cat.notion(n) for n in cat.contenus[0].fiches), "direction sur une notion inconnue"
        return
    cat = charger_catalogue(BIBLIOTHEQUES, ["programme", biblio.id], None)
    fichiers = list((dossier / "fiches").rglob("*.yaml"))
    assert len(cat.contenus[0].fiches) == len(fichiers), "une fiche vise une notion inconnue ou en double"
    for fichier in fichiers:
        fiche = yaml.safe_load(fichier.read_text(encoding="utf-8"))
        assert fiche.get("sources"), f"{fichier.name} : sources manquantes"
        for source in fiche["sources"]:
            assert source.get("licence") in LICENCES_LIBRES, f"{fichier.name} : licence de source non libre"
            assert source.get("url", "").startswith("https://"), f"{fichier.name} : lien de source manquant"
        assert fiche.get("relecture", {}).get("statut") in ("a_relire", "relue"), f"{fichier.name} : relecture"


def test_fiches_experimentales_couvrent_les_maths_de_3e():
    """Chaque notion de maths du referentiel 3e a sa fiche, et chaque fiche a exemple et exercices complets."""
    cat = charger_catalogue(BIBLIOTHEQUES, ["programme", "fiches-3e-experimentales"], None)
    maths = [n.id for n in cat.notions.values() if n.matiere == "mathematiques"]
    fiches = cat.contenus[0].fiches
    assert len(maths) == 38 and sorted(maths) == sorted(fiches)
    for identifiant, fiche in fiches.items():
        assert fiche.get("essentiel") and fiche.get("methode") and fiche.get("erreurs_frequentes"), identifiant
        assert fiche.get("exemple", {}).get("solution"), identifiant
        for exercice in fiche.get("exercices", []):
            assert exercice.get("enonce") and exercice.get("indices") and exercice.get("solution"), identifiant
