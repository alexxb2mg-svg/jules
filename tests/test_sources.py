"""Tests des sources personnelles (docs/SOURCES-CONTRAT.md §11), avec le moteur factice : aucune IA.

La « reponse du modele » est une vraie fiche visuelle native du depot (guerre totale 1914-1918), privee
de ce que le modele ne doit pas ecrire (sources, licence, relecture, schemas en fichier, renfort) : si
le format des fiches evolue, ces tests suivent sans rien recopier.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from jules import sources as src
from jules.config import depuis_dict
from jules.fiches_visuelles import (
    ErreurFicheVisuelle,
    lire_fiche_personnelle,
    lire_fiche_visuelle,
)
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import RACINE, regle_par_defaut

NOTION = "guerre-totale-1914-1918"
FICHE_NATIVE = RACINE / "bibliotheque" / "fiches-visuelles-3e-experimentales" / "fiches" / "histoire" / f"{NOTION}.yaml"
COURS = (
    "La Première Guerre mondiale (1914-1918) est une guerre totale : toute la société est mobilisée. "
    "Les soldats vivent dans les tranchées, à Verdun en 1916 la bataille dure dix mois. "
    "À l'arrière, les femmes remplacent les hommes dans les usines. Le génocide des Arméniens a lieu en 1915."
)


def fiche_du_modele(notion: str | None = NOTION) -> dict:
    brut = yaml.safe_load(FICHE_NATIVE.read_text(encoding="utf-8"))
    for cle in ("sources", "licence", "relecture", "auteurs", "generation"):
        brut.pop(cle, None)
    brut["blocs"] = [b for b in brut["blocs"] if b["type"] not in ("schema", "renfort")]
    if notion is None:
        brut.pop("notion", None)
    else:
        brut["notion"] = notion
    return brut


def en_yaml(brut: dict) -> str:
    return "Voici la fiche.\n```yaml\n" + yaml.safe_dump(brut, allow_unicode=True, sort_keys=False) + "```\n"


class Modele:
    """Regle du factice : rattachement puis generation, reponses programmables et comptees."""

    def __init__(self, notion: str | None = NOTION, fiches: list[str] | None = None, matiere: str = "histoire") -> None:
        self.notion = notion
        self.matiere = matiere
        self.fiches = list(fiches or [en_yaml(fiche_du_modele())])
        self.generations = 0
        self.dernier_systeme = ""
        self.derniers_tours: list = []

    def __call__(self, systeme, tours, modele):
        if "RATTACHEMENT_SOURCE" in systeme:
            return json.dumps({"notion": self.notion, "matiere": self.matiere, "raison": "Le cours parle de 14-18."})
        if "GENERATION_FICHE_PERSONNELLE" in systeme:
            self.generations += 1
            self.dernier_systeme = systeme
            self.derniers_tours = list(tours)
            return self.fiches[min(self.generations - 1, len(self.fiches) - 1)]
        return regle_par_defaut(systeme, tours, modele)


@pytest.fixture
def brut_config_sources(brut_config: dict) -> dict:
    brut_config["modules"] = [*brut_config["modules"], {"id": "sources", "reglages": {"generations_par_jour": 3}}]
    return brut_config


@pytest.fixture
def modele() -> Modele:
    return Modele()


@pytest.fixture
def tuteur(projet: Path, brut_config_sources: dict, modele: Modele):
    llm = Factice()
    llm.regle = modele
    t = Tuteur(depuis_dict(brut_config_sources, projet), llm=llm)
    yield t
    t.fermer()


@pytest.fixture
def client(tuteur):
    with TestClient(creer_app(tuteur)) as c:
        yield c


def deposer(client, **donnees) -> list[dict]:
    fichiers = donnees.pop("files", None)
    r = client.post("/api/eleve/sources/deposer", data=donnees, files=fichiers)
    assert r.status_code == 200, r.text
    return [json.loads(ligne) for ligne in r.text.splitlines() if ligne.strip()]


def fin(etapes: list[dict]) -> dict:
    assert etapes[-1]["etape"] == "fin", etapes
    return etapes[-1]["fiche"]


def notions_et_matieres(tuteur):
    catalogue = tuteur.module("notions").catalogue
    return catalogue.notions, {mid: nom for mid, nom, _ in catalogue.matieres()}


# --- validateur : mode personnel, sans toucher au natif --------------------------------------------


def test_fiche_personnelle_valide_avec_les_ecarts_du_contrat(tuteur):
    notions, matieres = notions_et_matieres(tuteur)
    fiche = lire_fiche_personnelle(
        fiche_du_modele(), notions, matieres, "3e", {"id": "s1", "titre": "Mes photos"}, frozenset()
    )
    assert fiche.origine == "personnelle" and fiche.licence == "personnel" and fiche.relecture == "a_relire"
    assert fiche.sources == [{"titre": "Mes photos", "personnelle": "s1"}]
    publique = fiche.publique([])
    assert publique["origine"] == "personnelle"
    assert all(b["type"] != "attendus" for b in publique["blocs"])


def test_fiche_personnelle_sans_notion_garde_sa_matiere(tuteur):
    notions, matieres = notions_et_matieres(tuteur)
    brut = fiche_du_modele(notion=None)
    brut["matiere"] = "histoire"
    fiche = lire_fiche_personnelle(brut, notions, matieres, "3e", {"id": "s1"}, frozenset())
    assert fiche.notion == "" and fiche.matiere == "histoire"
    brut["matiere"] = "astrologie"  # matiere inventee : ramenee a aucune
    assert lire_fiche_personnelle(brut, notions, matieres, "3e", {"id": "s1"}, frozenset()).matiere == ""


def test_fiche_personnelle_refuse_notion_inventee_et_svg_en_fichier(tuteur):
    notions, matieres = notions_et_matieres(tuteur)
    with pytest.raises(ErreurFicheVisuelle, match="inconnue"):
        lire_fiche_personnelle(fiche_du_modele("notion-inventee"), notions, matieres, "3e", {"id": "s"}, frozenset())
    brut = fiche_du_modele()
    brut["blocs"].append(
        {"id": "dessin", "type": "schema", "titre": "Un dessin", "svg": "dessin.svg", "jules": "Regarde le dessin."}
    )
    with pytest.raises(ErreurFicheVisuelle, match="en ligne"):
        lire_fiche_personnelle(brut, notions, matieres, "3e", {"id": "s"}, frozenset())


def test_fiche_native_exige_toujours_url_et_licence(tuteur, tmp_path):
    """Non-regression : le mode personnel n'assouplit rien pour les fiches natives."""
    notions, _ = notions_et_matieres(tuteur)
    biblio = tuteur.module("fiches_visuelles")
    native = biblio.fiches[NOTION]
    assert native.origine == "native" and "origine" not in native.publique([])
    brut = fiche_du_modele()
    brut.update({"licence": "CC-BY-SA-4.0", "relecture": {"statut": "a_relire"}, "sources": [{"titre": "Mon cours"}]})
    chemin = tmp_path / f"{NOTION}.yaml"
    chemin.write_text(yaml.safe_dump(brut, allow_unicode=True), encoding="utf-8")
    from jules.bibliotheques import lire_identite

    identite = lire_identite(RACINE / "bibliotheque" / "fiches-visuelles-3e-experimentales")
    with pytest.raises(ErreurFicheVisuelle, match="url https"):
        lire_fiche_visuelle(chemin, notions, identite, frozenset())


# --- parcours ------------------------------------------------------------------------------------


def test_texte_colle_donne_une_fiche_a_ranger_dans_la_notion_suggeree(client, modele):
    etapes = deposer(client, texte=COURS, matiere="histoire")
    assert [e["etape"] for e in etapes] == ["notion", "ecriture", "verification", "fin"]
    entree = fin(etapes)
    assert entree["etat"] == "a_ranger" and entree["notion"] is None
    assert entree["suggestion"]["notion"] == NOTION and entree["suggestion"]["avertissement"] == ""
    # la generation recoit la meme charte et le meme format que le patron, et le document de l'eleve
    assert "## La charte" in modele.dernier_systeme and "## Le format" in modele.dernier_systeme
    assert COURS in modele.derniers_tours[0].texte
    fiche = client.get(f"/api/eleve/sources/fiches/{entree['id']}").json()
    assert fiche["origine"] == "personnelle" and fiche["matiere"] == "histoire"
    assert fiche["rangement"]["etat"] == "a_ranger"
    assert [f["id"] for f in client.get("/api/eleve/sources/a_ranger").json()] == [entree["id"]]


def test_matiere_differente_de_celle_choisie_est_signalee(client):
    entree = fin(deposer(client, texte=COURS, matiere="physique-chimie"))
    assert "histoire" in entree["suggestion"]["avertissement"].lower()


def test_notion_inventee_par_le_modele_vaut_aucune(tuteur, client, modele):
    modele.notion = "notion-qui-n-existe-pas"
    modele.fiches = [en_yaml(fiche_du_modele(notion=None))]
    entree = fin(deposer(client, texte=COURS))
    assert entree["suggestion"]["notion"] is None
    r = client.post(f"/api/eleve/sources/fiches/{entree['id']}/ranger", json={"mode": "notion"})
    assert r.status_code == 400
    rangee = client.post(f"/api/eleve/sources/fiches/{entree['id']}/ranger", json={"mode": "non_classe"}).json()
    assert rangee["etat"] == "rangee" and rangee["notion"] is None and rangee["dossier"] is None


def test_fiche_refusee_un_seul_nouvel_essai_avec_le_motif(client, modele):
    mauvaise = fiche_du_modele()
    mauvaise["blocs"] = mauvaise["blocs"][:1]  # moins de 3 blocs
    modele.fiches = [en_yaml(mauvaise), en_yaml(fiche_du_modele())]
    fin(deposer(client, texte=COURS))
    assert modele.generations == 2
    assert "Le contrôle a refusé" in modele.derniers_tours[-1].texte and "blocs" in modele.derniers_tours[-1].texte


def test_deux_refus_donnent_une_erreur_claire_sans_fiche(client, modele):
    mauvaise = fiche_du_modele()
    mauvaise["blocs"] = mauvaise["blocs"][:1]
    modele.fiches = [en_yaml(mauvaise)]
    etapes = deposer(client, texte=COURS)
    assert modele.generations == 2
    assert etapes[-1]["etape"] == "erreur" and "fiche propre" in etapes[-1]["message"]
    assert client.get("/api/eleve/sources/fiches").json()["fiches"] == []


def test_ranger_dans_un_dossier_garde_la_notion_suggeree(client):
    entree = fin(deposer(client, texte=COURS))
    dossier = client.post("/api/eleve/sources/dossiers", json={"nom": "Brevet blanc"}).json()
    rangee = client.post(
        f"/api/eleve/sources/fiches/{entree['id']}/ranger", json={"mode": "dossier", "dossier": dossier["id"]}
    ).json()
    assert rangee["dossier"] == dossier["id"] and rangee["notion"] == NOTION
    assert client.get("/api/eleve/sources/a_ranger").json() == []
    # supprimer le dossier : la fiche reste, dans sa notion
    assert client.delete(f"/api/eleve/sources/dossiers/{dossier['id']}").json() == {"deplacees": 1}
    liste = client.get("/api/eleve/sources/fiches").json()
    assert liste["dossiers"] == [] and liste["fiches"][0]["dossier"] is None and liste["fiches"][0]["notion"] == NOTION


def test_ne_pas_garder_supprime_fiche_et_source(tuteur, client):
    etapes = deposer(client, files=[("photos", ("cours.png", PNG, "image/png"))])
    entree = fin(etapes)
    nom = entree["source"]["fichiers"][0]
    assert tuteur.stockage.chemin_image(nom) is not None
    assert client.delete(f"/api/eleve/sources/fiches/{entree['id']}").json() == {"ok": True}
    assert tuteur.stockage.chemin_image(nom) is None
    assert client.get(f"/api/eleve/sources/fiches/{entree['id']}").status_code == 404


def test_photos_envoyees_au_modele_et_image_invalide_refusee(client, modele):
    fin(deposer(client, files=[("photos", ("a.png", PNG, "image/png")), ("photos", ("b.png", PNG, "image/png"))]))
    assert len(modele.derniers_tours[0].images) == 2
    r = client.post("/api/eleve/sources/deposer", files=[("photos", ("x.png", b"pas une image", "image/png"))])
    assert r.status_code == 400 and "image" in r.json()["detail"]


def test_entrees_invalides_messages_clairs(client):
    assert "trop court" in client.post("/api/eleve/sources/deposer", data={"texte": "Trop court."}).json()["detail"]
    assert client.post("/api/eleve/sources/deposer", data={}).status_code == 400
    r = client.post("/api/eleve/sources/deposer", files=[("pdf", ("c.pdf", b"pas un pdf", "application/pdf"))])
    assert r.status_code == 400 and "PDF" in r.json()["detail"]


def test_pdf_avec_texte_et_pdf_scanne(client, modele):
    pytest.importorskip("pypdfium2")
    fin(deposer(client, files=[("pdf", ("cours.pdf", pdf_de_test(texte=True), "application/pdf"))]))
    assert "Verdun" in modele.derniers_tours[0].texte and modele.derniers_tours[0].images == []
    fin(deposer(client, files=[("pdf", ("scan.pdf", pdf_de_test(texte=False), "application/pdf"))]))
    assert len(modele.derniers_tours[0].images) == 1


def test_quota_journalier(client):
    for _ in range(3):
        fin(deposer(client, texte=COURS))
    r = client.post("/api/eleve/sources/deposer", data={"texte": COURS})
    assert r.status_code == 429 and "demain" in r.json()["detail"]
    assert client.get("/api/eleve/sources/fiches").json()["quota"] == {"par_jour": 3, "utilisees": 3}


def test_rien_sous_bibliotheque_et_rien_dans_le_suivi(tuteur, client, projet):
    avant = sorted(p.relative_to(projet) for p in (projet / "bibliotheque").rglob("*"))
    fin(deposer(client, texte=COURS))
    assert sorted(p.relative_to(projet) for p in (projet / "bibliotheque").rglob("*")) == avant
    assert tuteur.stockage.evenements("suivi") == []


def test_parent_voit_et_supprime(client):
    entree = fin(deposer(client, texte=COURS))
    liste = client.get("/api/modules/sources/fiches").json()
    assert [f["id"] for f in liste] == [entree["id"]] and liste[0]["titre_notion"]
    assert client.delete(f"/api/modules/sources/fiches/{entree['id']}").json() == {"ok": True}
    assert client.get("/api/eleve/sources/fiches").json()["fiches"] == []


def test_dossiers_noms_controles(client):
    assert client.post("/api/eleve/sources/dossiers", json={"nom": "  "}).status_code == 400
    assert client.post("/api/eleve/sources/dossiers", json={"nom": "x" * 41}).status_code == 400
    client.post("/api/eleve/sources/dossiers", json={"nom": "Brevet"})
    assert client.post("/api/eleve/sources/dossiers", json={"nom": "brevet"}).status_code == 400


# --- fichiers de test -------------------------------------------------------------------------------


def _png() -> bytes:
    import struct
    import zlib

    def morceau(genre: bytes, donnees: bytes) -> bytes:
        return (
            struct.pack(">I", len(donnees))
            + genre
            + donnees
            + struct.pack(">I", zlib.crc32(genre + donnees) & 0xFFFFFFFF)
        )

    brut = b"".join(b"\x00" + b"\xff\xff\xff" * 4 for _ in range(4))
    return (
        b"\x89PNG\r\n\x1a\n"
        + morceau(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
        + morceau(b"IDAT", zlib.compress(brut))
        + morceau(b"IEND", b"")
    )


PNG = _png()


def pdf_de_test(texte: bool) -> bytes:
    """Un PDF d'une page ecrit a la main : avec le cours en texte, ou sans texte (comme un scan)."""
    contenu = (
        b"BT /F1 9 Tf 20 800 Td (" + COURS.encode("latin-1", "replace") + b") Tj ET"
        if texte
        else b"0 0 1 rg 10 10 100 100 re f"
    )
    objets = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1400 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(contenu)).encode() + b" >>\nstream\n" + contenu + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    sortie = io.BytesIO()
    sortie.write(b"%PDF-1.4\n")
    positions = []
    for i, objet in enumerate(objets, 1):
        positions.append(sortie.tell())
        sortie.write(f"{i} 0 obj\n".encode() + objet + b"\nendobj\n")
    xref = sortie.tell()
    sortie.write(f"xref\n0 {len(objets) + 1}\n0000000000 65535 f \n".encode())
    for p in positions:
        sortie.write(f"{p:010d} 00000 n \n".encode())
    sortie.write(f"trailer\n<< /Size {len(objets) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return sortie.getvalue()


def test_constantes_du_contrat():
    assert (src.PHOTOS_MAX, src.PDF_PAGES_MAX, src.ESSAIS_GENERATION) == (5, 20, 2)
