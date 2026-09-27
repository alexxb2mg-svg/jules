"""Navigation N5 : petites pages courtes (docs/spec/NAVIGATION.md, EX-212) et mention « pas encore de leçon »
de la rubrique Exercices (EX-209, tag spec-nav-fige-2).

Le jeu de EX-212 est **genere par le test** et dimensionne sur le pire cas de la spec : 16 matieres, dont une de
30 chapitres de 10 notions, titres de chapitres et de notions de 140 caracteres, chaque notion avec sa fiche
visuelle (`fiches_visuelles.liste()` ecarte les notions sans fiche). Les effectifs sont d'abord relus dans la
reponse de `/api/eleve/fiches_visuelles/notions`, puis les hauteurs sont mesurees a 1280 x 800 dans Chromium
(banc de tests/nav_scenario.py, spec section 6).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from jules.config import depuis_dict
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.web.app import creer_app
from tests.conftest import regle_par_defaut
from tests.nav_scenario import banc_navigation
from tests.test_navigation import ATTENDRE_BARRE, RACINE, _tuteur
from tests.test_navigation_n4 import LIRE, STUDIO, memoire

FICHES = "/api/eleve/fiches_visuelles/notions"

# --- jeu genere : pire cas de EX-212 ----------------------------------------------------------------------

NB_CHAPITRES_LOURDE = 30
NB_NOTIONS_PAR_CHAPITRE = 10
LONGUEUR_TITRE = 140
MATIERE_LOURDE = "francais"
# 16 matieres : les 12 du referentiel 3e et 4 de plus, avec leurs vrais noms (certains tiennent sur deux lignes).
MATIERES = [
    ("francais", "Français"),
    ("mathematiques", "Mathématiques"),
    ("histoire", "Histoire"),
    ("geographie", "Géographie"),
    ("emc", "Enseignement moral et civique"),
    ("physique-chimie", "Physique-chimie"),
    ("svt", "Sciences de la vie et de la Terre"),
    ("technologie", "Technologie"),
    ("anglais", "Anglais"),
    ("arts-plastiques", "Arts plastiques"),
    ("education-musicale", "Éducation musicale"),
    ("histoire-des-arts", "Histoire des arts"),
    ("espagnol", "Espagnol"),
    ("allemand", "Allemand"),
    ("latin", "Langues et cultures de l'Antiquité"),
    ("eps", "Éducation physique et sportive"),
]
NB_CHAPITRES_AUTRES = 2
NB_NOTIONS_AUTRES = 3
PHRASE = (
    "étude des textes et des œuvres du programme avec leurs contextes historiques littéraires "
    "artistiques et les méthodes de lecture analytique attendues en classe de troisième au collège"
)
MOTS = PHRASE.split(" ")


def titre_long(prefixe: str) -> str:
    """Titre d'exactement LONGUEUR_TITRE caracteres, sans barre de division, qui commence par `prefixe`."""
    texte = prefixe
    i = 0
    while len(texte) < LONGUEUR_TITRE + 20:
        texte += " " + MOTS[i % len(MOTS)]
        i += 1
    texte = texte[:LONGUEUR_TITRE]
    if texte.endswith(" "):
        texte = texte[:-1] + "e"
    assert len(texte) == LONGUEUR_TITRE
    return texte


def _ecrire(chemin: Path, contenu: dict[str, Any]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(yaml.safe_dump(contenu, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _fiche(notion: str) -> dict[str, Any]:
    etape = "Relire la consigne, repérer les mots importants et vérifier chaque étape avant de conclure."
    return {
        "notion": notion,
        "licence": "CC-BY-SA-4.0",
        "sources": [{"titre": "Source de test", "url": "https://example.org/jeu-n5", "licence": "CC-BY-SA-4.0"}],
        "relecture": {"statut": "a_relire"},
        # Fiche longue : la page centrale defile, sa position doit survivre a la navigation dans la barre.
        "blocs": [{"id": f"methode-{i}", "type": "methode", "etapes": [etape] * 6} for i in range(8)],
    }


def generer_jeu(racine: Path) -> dict[str, Any]:
    """Referentiel `ref-n5` et bibliotheque de fiches `fv-n5` sous `racine/bibliotheque`. Rend l'attendu."""
    biblio = racine / "bibliotheque"
    commun = {"statut": "experimentale", "licence": "CC-BY-SA-4.0", "niveaux": ["3e"], "avertissement": "Jeu de test."}
    _ecrire(biblio / "ref-n5" / "bibliotheque.yaml", {"id": "ref-n5", "type": "referentiel", **commun})
    _ecrire(biblio / "fv-n5" / "bibliotheque.yaml", {"id": "fv-n5", "type": "fiches-visuelles", **commun})
    attendu: dict[str, Any] = {}
    for mid, nom in MATIERES:
        lourde = mid == MATIERE_LOURDE
        n_chap = NB_CHAPITRES_LOURDE if lourde else NB_CHAPITRES_AUTRES
        n_not = NB_NOTIONS_PAR_CHAPITRE if lourde else NB_NOTIONS_AUTRES
        chapitres = []
        for c in range(n_chap):
            titre_chap = titre_long(f"Chapitre {c + 1} {nom}") if lourde else f"Chapitre {c + 1} de {nom}"
            notions = []
            for k in range(n_not):
                nid = f"{mid}-c{c + 1}-n{k + 1}"
                titre = titre_long(f"Notion {c + 1}.{k + 1} {nom}") if lourde else f"Notion {c + 1}.{k + 1} de {nom}"
                notions.append({"id": nid, "titre": titre})
                _ecrire(biblio / "fv-n5" / "fiches" / mid / f"{nid}.yaml", _fiche(nid))
            chapitres.append({"titre": titre_chap, "notions": notions})
        _ecrire(
            biblio / "ref-n5" / "3e" / f"{mid}.yaml",
            {"matiere": nom, "id": mid, "themes": [{"titre": "Programme", "chapitres": chapitres}]},
        )
        attendu[mid] = {"nom": nom, "chapitres": {c["titre"]: [n["id"] for n in c["notions"]] for c in chapitres}}
    return attendu


@pytest.fixture(scope="module")
def jeu(tmp_path_factory):
    projet = tmp_path_factory.mktemp("projet-n5")
    for dossier in ("persona", "consignes", "profils", "extensions"):
        shutil.copytree(RACINE / dossier, projet / dossier)
    attendu = generer_jeu(projet)
    brut = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))
    brut["llm"] = {"backend": "factice", "historique_max": 30}
    brut["modules"] = [
        {"id": "notions", "reglages": {"bibliotheques": ["ref-n5"], "detection": False}},
        {"id": "fiches_visuelles", "reglages": {"bibliotheques": ["fv-n5"]}},
        {"id": "cours", "reglages": {"bibliotheques": []}},
        {"id": "studio"},
    ]
    llm = Factice()
    llm.regle = regle_par_defaut
    tuteur = Tuteur(depuis_dict(brut, projet), llm=llm)
    try:
        yield tuteur, attendu
    finally:
        tuteur.fermer()


@pytest.fixture(scope="module")
def reponse_fiches(jeu) -> dict[str, Any]:
    tuteur, _ = jeu
    return TestClient(creer_app(tuteur)).get(FICHES).json()


@pytest.fixture(scope="module")
def banc_n5(jeu, tmp_path_factory):
    tuteur, _ = jeu
    with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n5")) as b:
        yield b


def test_ex212_effectifs_du_jeu_dans_la_reponse(jeu, reponse_fiches):
    """Avant toute mesure : la reponse porte bien le pire cas (sinon les hauteurs ne prouvent rien)."""
    _, attendu = jeu
    matieres = reponse_fiches["matieres"]
    assert sorted(m["id"] for m in matieres) == sorted(mid for mid, _ in MATIERES)  # ordre : celui des fichiers
    assert len(matieres) == 16
    lourde = next(m for m in matieres if m["id"] == MATIERE_LOURDE)
    chapitres: dict[str, list[dict[str, Any]]] = {}
    for n in lourde["notions"]:
        chapitres.setdefault(n["chapitre"], []).append(n)
    assert len(chapitres) == NB_CHAPITRES_LOURDE
    assert {len(v) for v in chapitres.values()} == {NB_NOTIONS_PAR_CHAPITRE}
    assert {len(c) for c in chapitres} == {LONGUEUR_TITRE}
    assert {len(n["titre"]) for n in lourde["notions"]} == {LONGUEUR_TITRE}
    for m in matieres:  # chaque notion du referentiel genere a sa fiche
        assert {n["id"] for n in m["notions"]} == {i for ids in attendu[m["id"]]["chapitres"].values() for i in ids}


# --- scenario : etapes 2, 3, 4 de Mes fiches sur / ---------------------------------------------------------

MESURER = r"""
  const page = () => document.querySelector("#barre-jules .barre-sous-page .barre-page");
  const mesure = () => {
    const p = page();
    const barre = S.el("#barre-jules");
    return {
      etape: Number(p.dataset.etape),
      hauteur: p.scrollHeight,
      titre: S.el("#barre-page-titre").textContent,
      matieres: [...p.querySelectorAll("[data-matiere]")].map((b) => ({
        id: b.dataset.matiere, effectif: (b.querySelector(".barre-effectif") || {}).textContent || null,
        hauteur: b.getBoundingClientRect().height })),
      chapitres: [...p.querySelectorAll("[data-chapitre]")].map((b) => ({
        titre: b.dataset.chapitre, texte: b.querySelector(".barre-libelle").textContent,
        effectif: (b.querySelector(".barre-effectif") || {}).textContent || null,
        hauteur: b.getBoundingClientRect().height })),
      elements: [...p.querySelectorAll("a.barre-element")].map((a) => ({
        href: a.getAttribute("href"), texte: a.querySelector(".barre-libelle").textContent,
        hauteur: a.getBoundingClientRect().height })),
      barre: { scrollHeight: barre.scrollHeight, clientHeight: barre.clientHeight,
               overflowY: getComputedStyle(barre).overflowY },
      centre: { zone: S.el(".fiche-zone").scrollTop, fenetre: scrollY },
    };
  };
"""


@pytest.fixture(scope="module")
def parcours_fiches(banc_n5, reponse_fiches) -> dict[str, Any]:
    lourde = next(m for m in reponse_fiches["matieres"] if m["id"] == MATIERE_LOURDE)
    chapitre = lourde["notions"][0]["chapitre"]
    etapes = (
        ATTENDRE_BARRE
        + LIRE
        + MESURER
        + r"""
        await S.attendre(() => !S.el("#fiche").classList.contains("cache"), 8000);
        const zone = S.el(".fiche-zone");
        zone.scrollTop = 600;
        await S.pause(50);
        const centreAvant = { zone: zone.scrollTop, fenetre: scrollY, max: zone.scrollHeight - zone.clientHeight };
        rubrique("fiches").click();
        await attendreEtape(2);
        const etape2 = mesure();
        matiere(LOURDE).click();
        await attendreEtape(3);
        const etape3 = mesure();
        // La petite page defile dans la barre ; la page centrale ne bouge pas.
        const barre = S.el("#barre-jules");
        barre.scrollTop = 900;
        await S.pause(50);
        const defilement = { barre: barre.scrollTop, zone: zone.scrollTop, fenetre: scrollY };
        const chapitres = [...document.querySelectorAll("#barre-jules [data-chapitre]")];
        chapitres.find((b) => b.dataset.chapitre === CHAPITRE).click();
        await attendreEtape(4);
        const etape4 = mesure();
        return { centreAvant, etape2, etape3, defilement, etape4, api: S.api(), erreurs: S.erreurs() };
        """.replace("LOURDE", json.dumps(MATIERE_LOURDE)).replace("CHAPITRE", json.dumps(chapitre))
    )
    r = banc_n5.jouer("/", etapes, avant=memoire(None), budget_ms=15000)
    r["chapitre"] = chapitre
    # Mesures lisibles avec `pytest -s` (a coller dans la revue).
    print("\nEX-212 hauteurs (px) :", {k: r[k]["hauteur"] for k in ("etape2", "etape3", "etape4")})
    return r


def test_ex212_page_centrale_assez_longue_pour_defiler(parcours_fiches):
    # Sans quoi « la page centrale garde sa position » ne prouverait rien.
    assert parcours_fiches["centreAvant"]["max"] > 600
    assert parcours_fiches["centreAvant"]["zone"] == 600


def test_ex212_etape2_seize_matieres_900px_au_plus(parcours_fiches, reponse_fiches):
    e = parcours_fiches["etape2"]
    assert e["etape"] == 2
    assert [m["id"] for m in e["matieres"]] == [m["id"] for m in reponse_fiches["matieres"]]
    assert [m["effectif"] for m in e["matieres"]] == [str(len(m["notions"])) for m in reponse_fiches["matieres"]]
    assert e["chapitres"] == [] and e["elements"] == []  # un seul niveau
    assert e["hauteur"] <= 900, e["hauteur"]
    assert min(m["hauteur"] for m in e["matieres"]) >= 44


def test_ex212_etape3_matiere_lourde_2000px_au_plus(parcours_fiches, jeu):
    _, attendu = jeu
    e = parcours_fiches["etape3"]
    assert e["etape"] == 3
    assert e["titre"] == attendu[MATIERE_LOURDE]["nom"]
    assert [c["titre"] for c in e["chapitres"]] == list(attendu[MATIERE_LOURDE]["chapitres"])
    # texte complet dans le DOM (l'affichage est limite a deux lignes)
    assert {c["texte"] for c in e["chapitres"]} == set(attendu[MATIERE_LOURDE]["chapitres"])
    assert {c["effectif"] for c in e["chapitres"]} == {str(NB_NOTIONS_PAR_CHAPITRE)}
    assert e["matieres"] == [] and e["elements"] == []  # ni matieres ni notions : les chapitres de cette matiere seuls
    assert e["hauteur"] <= 2000, e["hauteur"]
    assert min(c["hauteur"] for c in e["chapitres"]) >= 44


def test_ex212_etape4_chapitre_de_dix_notions_900px_au_plus(parcours_fiches, jeu):
    _, attendu = jeu
    e = parcours_fiches["etape4"]
    assert e["etape"] == 4
    ids = attendu[MATIERE_LOURDE]["chapitres"][parcours_fiches["chapitre"]]
    # rien d'un autre chapitre ni d'une autre matiere
    assert [a["href"] for a in e["elements"]] == [f"/#{i}" for i in ids]
    assert e["matieres"] == [] and e["chapitres"] == []
    assert e["hauteur"] <= 900, e["hauteur"]
    assert min(a["hauteur"] for a in e["elements"]) >= 44


def test_ex212_la_barre_defile_la_page_centrale_ne_bouge_pas(parcours_fiches):
    r = parcours_fiches
    e3 = r["etape3"]
    assert e3["barre"]["overflowY"] == "auto"
    assert e3["barre"]["scrollHeight"] > e3["barre"]["clientHeight"]  # la petite page depasse : la barre defile
    assert r["defilement"]["barre"] > 0
    for cle in ("etape2", "etape3", "etape4"):
        assert r[cle]["centre"] == {"zone": 600, "fenetre": 0}, cle
    assert (r["defilement"]["zone"], r["defilement"]["fenetre"]) == (600, 0)


def test_ex212_aucun_chemin_api_hors_ex210(parcours_fiches):
    api = parcours_fiches["api"]
    permis = {"/api/session", "/api/infos", FICHES}
    fiche_ouverte = [c for c in api if c.startswith(FICHES + "/")]
    assert len(set(fiche_ouverte)) == 1  # la fiche ouverte au chargement (deja le cas avant la carte)
    assert set(api) - set(fiche_ouverte) <= permis
    assert api.count(FICHES) == 1  # la barre reprend la reponse de la page (cache de MS.api)
    assert parcours_fiches["erreurs"] == []


# --- Mes lecons / Exercices : chapitres en intertitres avec leur effectif -----------------------------------


def test_ex212_exercices_intertitres_avec_effectif(banc_n5, jeu):
    _, attendu = jeu
    r = banc_n5.jouer(
        "/studio",
        ATTENDRE_BARRE
        + LIRE
        + r"""
        rubrique("supports").click();
        await attendreEtape(4);
        const p = document.querySelector("#barre-jules .barre-sous-page .barre-page");
        return [...p.querySelectorAll(".barre-intertitre")].map((h) => ({
          titre: h.querySelector(".barre-libelle").textContent,
          effectif: h.querySelector(".barre-effectif").textContent,
          notions: h.parentElement.querySelectorAll("a.barre-element").length }));
        """,
        avant=memoire("mathematiques"),
        budget_ms=10000,
    )
    chapitres = attendu["mathematiques"]["chapitres"]
    assert [i["titre"] for i in r] == list(chapitres)
    assert [i["effectif"] for i in r] == [str(len(v)) for v in chapitres.values()]
    assert [i["notions"] for i in r] == [len(v) for v in chapitres.values()]


# --- EX-209 (spec-nav-fige-2) : Exercices liste toutes les notions, mention et lien sans notion ------------------


@pytest.fixture(scope="module")
def banc_depot(tmp_path_factory):
    """Donnees du depot (bibliotheque/) : l'anglais n'a aucune lecon, les mathematiques en ont (voir N4)."""
    tuteur = _tuteur(tmp_path_factory, None)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n5-depot")) as b:
            b.client = TestClient(creer_app(tuteur))  # type: ignore[attr-defined]
            yield b
    finally:
        tuteur.fermer()


ELEMENTS_EXERCICES = (
    ATTENDRE_BARRE
    + LIRE
    + r"""
    rubrique("supports").click();
    await attendreEtape(4);
    const p = document.querySelector("#barre-jules .barre-sous-page .barre-page");
    return [...p.querySelectorAll("a.barre-element")].map((a) => ({
      href: a.getAttribute("href"), mention: (a.querySelector(".barre-mention") || {}).textContent || null }));
    """
)


@pytest.mark.parametrize("matiere", ["anglais", "mathematiques"])
def test_ex209_exercices_toutes_les_notions_mention_et_lien(banc_depot, matiere):
    reponse = banc_depot.client.get(STUDIO, params={"matiere": matiere}).json()
    assert reponse["matiere"] == matiere
    notions = reponse["notions"]
    assert any(not n["lecon"] for n in notions)  # le cas a verifier existe dans le jeu du depot
    r = banc_depot.jouer("/studio", ELEMENTS_EXERCICES, avant=memoire(matiere), budget_ms=10000)
    assert len(r) == len(notions)  # toutes les notions, pas seulement celles qui ont une lecon
    # La barre regroupe par chapitre (ordre possiblement different de la reponse) : comparaison en multiensemble.
    attendus = [
        {"href": f"/studio?matiere={matiere}&notion={n['id']}", "mention": None}
        if n["lecon"]
        else {"href": f"/studio?matiere={matiere}", "mention": "pas encore de leçon"}
        for n in notions
    ]
    cle = lambda e: (e["href"], e["mention"] or "")  # noqa: E731
    assert sorted(r, key=cle) == sorted(attendus, key=cle)


def test_ex209_lien_sans_lecon_ouvre_studio_sans_notion_ni_erreur(banc_depot):
    reponse = banc_depot.client.get(STUDIO, params={"matiere": "mathematiques"}).json()
    avec_lecon = [n["titre"] for n in reponse["notions"] if n["lecon"]]
    sans_lecon = [n["titre"] for n in reponse["notions"] if not n["lecon"]]
    assert avec_lecon and sans_lecon
    r = banc_depot.jouer(
        "/studio?matiere=mathematiques",
        r"""
        await S.attendre(() => document.querySelector("#notions .notion-bloc"), 8000);
        await S.pause(300);
        const centre = S.el("#notions");
        return { requetes: S.requetes(), erreurs: S.erreurs(),
                 courants: centre.querySelectorAll("[aria-current]").length,
                 titres: [...centre.querySelectorAll(".notion-bloc .nom")].map((e) => e.textContent) };
        """,
        avant=memoire(None),
        budget_ms=10000,
    )
    assert r["erreurs"] == []
    assert [q for q in r["requetes"] if q.startswith(STUDIO)] == [STUDIO + "?matiere=mathematiques"]
    assert r["courants"] == 0  # aucune notion designee
    assert r["titres"] == avec_lecon  # la zone centrale garde le filtre lecon: true
    assert not set(sans_lecon) & set(r["titres"])
