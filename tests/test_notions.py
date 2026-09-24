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
    mots,
    texte_direction,
    texte_fiche,
)
from jules.modules.notions import niveau_du_profil, ressemble_a_un_calcul
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
            "declencheurs": ["angle droit", "équerre"],
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


def test_declencheurs_preselectionnent_sans_aller_dans_le_prompt(mini):
    cat = charger_catalogue(mini, ["ref", "fiches"], "3e")
    assert [n.id for n in candidats(cat, "Mon triangle a un angle droit")] == ["pythagore"]
    assert candidats(cat, "Un triangle quelconque") == []
    assert [n.id for n in candidats(cat, "j'ai pris l'équerre")] == ["pythagore"]
    fiche, _ = cat.fiche("pythagore")
    assert "declencheurs" not in fiche and "équerre" not in texte_fiche(fiche)


def test_symboles_et_calculs_sans_mot():
    assert mots("moins 30 %") == {"moins", "pourcent"} and "racine" in mots("√72")
    assert ressemble_a_un_calcul("(2x-6)(x+5) = 0") and ressemble_a_un_calcul("2/3 + 5/6")
    assert not ressemble_a_un_calcul("j'ai une rédaction à faire") and not ressemble_a_un_calcul("")
    assert not ressemble_a_un_calcul("peut-être, quand se retrouvent-ils ? en km/h")


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
    assert niveau_du_profil("CM1") == "CM1"
    assert niveau_du_profil("cm1 B") == "CM1"
    assert niveau_du_profil("Cours moyen première année") == "CM1"
    assert niveau_du_profil("CM2") == "CM2"


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


def test_detection_sur_un_calcul_sans_mot(tuteur):
    vus = {}

    def regle(systeme, tours, modele):
        if "UNE notion d'une liste fermée" in systeme:
            vus["liste_complete"] = "racine-carree" in systeme and "ratio" in systeme
            return '{"notion": "equations-premier-degre-et-produits", "confiance": "haute"}'
        return "ok"

    tuteur.llm.regle = regle
    module = tuteur.module("notions")
    trouvee = module.detecter(Message(role="eleve", texte="(2x-6)(x+5) = 0"))
    assert trouvee == ("equations-premier-degre-et-produits", "haute")
    assert vus["liste_complete"]  # un calcul : toute la liste, comme pour une photo
    vus.clear()
    module.detecter(Message(role="eleve", texte="Pythagore : 3² + 4² = ?"))
    assert vus["liste_complete"]  # meme avec un mot reconnu
    vus.clear()
    assert module.detecter(Message(role="eleve", texte="bonjour")) is None and not vus  # ni mot ni calcul : pas d'appel


def test_detection_liste_complete_mots_reconnus_en_tete(tuteur):
    """Le modele voit toujours toutes les notions ; celles dont un mot-cle est reconnu passent en tete."""
    vus = []

    def regle(systeme, tours, modele):
        if "UNE notion d'une liste fermée" in systeme:
            vus.append(systeme.split("Liste (identifiant | matière | notion) :", 1)[1].strip().splitlines())
            return '{"notion": "", "confiance": "faible"}'
        return "ok"

    tuteur.llm.regle = regle
    module = tuteur.module("notions")
    total = len(module.catalogue.notions)
    module.detecter(Message(role="eleve", texte="Je dois calculer l'hypoténuse avec Pythagore"))
    module.detecter(Message(role="eleve", texte="on étudie la périurbanisation autour de Lyon"))
    assert len(vus[0]) == total and vus[0][0].startswith("parallelisme-triangles-pythagore |")
    assert len(vus[1]) == total  # aucun mot-cle reconnu en entier : le modele juge sur le sens
    assert module.detecter(Message(role="eleve", texte="ok")) is None  # rien a rattacher : pas d'appel
    assert len(vus) == 2


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
        # profil sans classe : tout le programme est propose (CM1, 5e, 4e et 3e)
        tout = charger_catalogue(BIBLIOTHEQUES, ["programme"], None)
        assert sum(len(m["notions"]) for m in infos["matieres"]) == len(tout.notions) > 252


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
    maths = [n.id for n in cat.notions.values() if n.matiere == "mathematiques" and n.niveau == "3e"]
    fiches_maths = {i: f for i, f in cat.contenus[0].fiches.items() if i in maths}
    assert len(maths) == 38 and sorted(maths) == sorted(fiches_maths)
    for identifiant, fiche in fiches_maths.items():
        assert fiche.get("essentiel") and fiche.get("methode") and fiche.get("erreurs_frequentes"), identifiant
        assert fiche.get("exemple", {}).get("solution"), identifiant
        for exercice in fiche.get("exercices", []):
            assert exercice.get("enonce") and exercice.get("indices") and exercice.get("solution"), identifiant


def test_fiches_experimentales_francais_langue_sont_completes():
    """Les fiches de francais deja publiees (etude de la langue) ont exemple et exercices complets."""
    cat = charger_catalogue(BIBLIOTHEQUES, ["programme", "fiches-3e-experimentales"], None)
    francais = {n.id for n in cat.notions.values() if n.matiere == "francais"}
    fiches_francais = {i: f for i, f in cat.contenus[0].fiches.items() if i in francais}
    assert fiches_francais, "aucune fiche de francais trouvee"
    assert set(fiches_francais).issubset(francais)
    for identifiant, fiche in fiches_francais.items():
        assert fiche.get("essentiel") and fiche.get("methode") and fiche.get("erreurs_frequentes"), identifiant
        assert fiche.get("exemple", {}).get("solution"), identifiant
        for exercice in fiche.get("exercices", []):
            assert exercice.get("enonce") and exercice.get("indices") and exercice.get("solution"), identifiant


def test_referentiel_cm1():
    """CM1 2026-2027 : 10 matieres, ids prefixes cm1-, chaque notion a attendus et source, rien de la 3e ne fuit."""
    cat = charger_catalogue(BIBLIOTHEQUES, ["programme", "fiches-3e-experimentales"], "CM1")
    notions = list(cat.notions.values())
    assert len(notions) == 158
    assert {n.matiere for n in notions} == {
        "anglais",
        "arts-plastiques",
        "education-musicale",
        "emc",
        "francais",
        "geographie",
        "histoire",
        "histoire-des-arts",
        "mathematiques",
        "sciences-et-technologie",
    }
    for n in notions:
        assert n.id.startswith("cm1-") and n.niveau == "CM1" and not n.brevet, n.id
        assert n.attendus and n.source, n.id
        assert n.niveau_programme in ("CM1", "cours moyen", "cycle 3"), n.id
    assert candidats(cat, "je dois apprendre les phases de la lune")[0].id == "cm1-phases-de-la-lune"
