"""Navigation N4 : petites pages de la barre, matiere retenue, liens, cache de MS.api (docs/spec/NAVIGATION.md,
EX-209 et EX-210).

Scenarios Chromium sur le banc de tests/nav_scenario.py (spec section 6), plus quelques tests statiques et un test
API. Les donnees sont celles du depot (`bibliotheque/`), sauf quand un scenario simule une reponse : c'est dit
a chaque fois. Aucune valeur de repli du serveur n'est codee en dur : elle est calculee a partir des reponses.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Any

import pytest
from fastapi.testclient import TestClient

from jules.web.app import STATIQUE, creer_app
from tests.nav_scenario import banc_navigation
from tests.test_navigation import ATTENDRE_BARRE, CODE_ELEVE, SAISIR, _tuteur

PARCOURS = "/api/eleve/cours/parcours"
STUDIO = "/api/eleve/studio/notions"
FICHES = "/api/eleve/fiches_visuelles/notions"

# Jeu du depot, mesure le 27/09/2026 : les fiches visuelles ne couvrent que les mathematiques ; l'anglais n'a
# aucune lecon ; les mathematiques et l'histoire en ont. Les tests relisent ces faits dans les reponses (voir
# `donnees`) au lieu de les supposer.
MATIERE_SANS_LECON = "anglais"
NOTION_THALES = "thales-triangles-semblables-trigonometrie"
NOTION_HISTOIRE = "guerre-froide-bipolarisation"

# Reponse simulee de la liste des fiches pour le cas (a) : deux matieres avec fiche (le depot n'en a qu'une).
FICHES_DEUX_MATIERES = {
    "matieres": [
        {
            "id": "histoire",
            "nom": "Histoire",
            "notions": [
                {"id": NOTION_HISTOIRE, "titre": "La guerre froide", "chapitre": "Un monde bipolaire"},
            ],
        },
        {
            "id": "mathematiques",
            "nom": "Mathématiques",
            "notions": [{"id": NOTION_THALES, "titre": "Théorème de Thalès", "chapitre": "Géométrie"}],
        },
    ]
}


# --- bancs ----------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tuteur_n4(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory, None)
    yield tuteur
    tuteur.fermer()


@pytest.fixture(scope="module")
def banc(tuteur_n4, tmp_path_factory):
    with banc_navigation(creer_app(tuteur_n4), tmp_path_factory.mktemp("chromium-n4")) as b:
        yield b


@pytest.fixture(scope="module")
def banc_codes(tmp_path_factory):
    from jules.acces import empreinte
    from tests.test_navigation import CODE_PARENT

    tuteur = _tuteur(tmp_path_factory, {"code_eleve": empreinte(CODE_ELEVE), "code_parent": empreinte(CODE_PARENT)})
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n4-codes")) as b:
            yield b
    finally:
        tuteur.fermer()


@pytest.fixture(scope="module")
def client(tuteur_n4):
    return TestClient(creer_app(tuteur_n4))


@pytest.fixture(scope="module")
def donnees(client) -> dict[str, Any]:
    """Faits du jeu de test relus dans les reponses de l'API (verifies une fois, utilises par les scenarios)."""
    base = client.get(PARCOURS).json()
    matieres = [m["id"] for m in base["matieres"]]
    par_matiere = {m: client.get(PARCOURS, params={"matiere": m}).json() for m in matieres}
    fiches = client.get(FICHES).json()
    faits = {
        "matieres": matieres,
        "noms": {m["id"]: m["nom"] for m in base["matieres"]},
        "avec_lecon": [m for m in matieres if any(n["lecon"] for n in par_matiere[m]["notions"])],
        "fiches": [m["id"] for m in fiches["matieres"]],
        "fiches_reponse": fiches,
        "par_matiere": par_matiere,
    }
    assert MATIERE_SANS_LECON in matieres and MATIERE_SANS_LECON not in faits["avec_lecon"]
    assert MATIERE_SANS_LECON not in faits["fiches"]
    assert faits["fiches"] == ["geographie", "histoire", "mathematiques"]
    maths = {n["id"]: n for n in par_matiere["mathematiques"]["notions"]}
    assert maths[NOTION_THALES]["lecon"] is True
    assert NOTION_HISTOIRE in {n["id"] for n in par_matiere["histoire"]["notions"]}
    return faits


def memoire(matiere: str | None) -> str:
    """Script `avant` : localStorage vide, puis `jules.matiere` si une matiere est donnee."""
    ecrire = f"localStorage.setItem('jules.matiere', {json.dumps(matiere)});" if matiere else ""
    return "localStorage.clear();" + ecrire


# Lecture de la petite page affichee dans la barre.
LIRE = r"""
  const lirePage = () => {
    const zone = document.querySelector("#barre-jules .barre-sous-page");
    const p = zone && !zone.hidden ? zone.querySelector(".barre-page") : null;
    if (!p) return { etape: 1 };
    const t = p.querySelector("#barre-page-titre");
    return {
      etape: Number(p.dataset.etape) || 0,
      rubrique: p.dataset.rubrique || null,
      titre: t ? t.textContent : null,
      elements: [...p.querySelectorAll("a.barre-element")].map((a) => ({
        texte: a.querySelector(".barre-libelle").textContent, href: a.getAttribute("href"),
        courant: a.getAttribute("aria-current"),
      })),
      matieres: [...p.querySelectorAll("[data-matiere]")].map((b) => b.dataset.matiere),
      chapitres: [...p.querySelectorAll("[data-chapitre]")].map((b) => b.dataset.chapitre),
      retours: [...p.querySelectorAll(".barre-retour")].map((b) => b.textContent),
      vide: (p.querySelector(".barre-vide") || {}).textContent || null,
      erreur: (p.querySelector(".barre-erreur") || {}).textContent || null,
    };
  };
  const attendreEtape = (n) => S.attendre(() => lirePage().etape === n, 5000);
  const rubrique = (r) => S.el('#barre-jules [data-sous-pages="' + r + '"]');
  const matiere = (m) => S.el('#barre-jules [data-matiere="' + m + '"]');
  const retour = () => S.el("#barre-jules .barre-retour");
"""

DEBUT = ATTENDRE_BARRE + LIRE


def jouer(banc, chemin: str, etapes: str, **options: Any) -> Any:
    options.setdefault("budget_ms", 10000)
    return banc.jouer(chemin, DEBUT + etapes, **options)


# --- EX-209 (a) a (k) -------------------------------------------------------------------------------------


def test_ex209a_histoire_choisie_dans_mes_fiches_puis_mes_lecons(banc, donnees):
    # Reponse simulee pour les fiches (deux matieres) ; Mes lecons lit le vrai parcours d'histoire.
    r = jouer(
        banc,
        "/cours",
        r"""
        rubrique("fiches").click();
        await attendreEtape(2);
        const etape2 = lirePage();
        matiere("histoire").click();
        await attendreEtape(3);
        const etape3 = lirePage();
        retour().click(); await attendreEtape(2);
        retour().click(); await attendreEtape(1);
        rubrique("lecons").click();
        await attendreEtape(4);
        return { etape2, etape3, lecons: lirePage(), stockage: S.stockage(), actif: S.actif() };
        """,
        avant=memoire(None),
        simulees={FICHES: FICHES_DEUX_MATIERES},
    )
    assert r["etape2"]["matieres"] == ["histoire", "mathematiques"]
    assert r["etape3"]["titre"] == "Histoire" and r["etape3"]["chapitres"] == ["Un monde bipolaire"]
    assert r["stockage"]["jules.matiere"] == "histoire"
    assert (r["lecons"]["rubrique"], r["lecons"]["titre"]) == ("lecons", donnees["noms"]["histoire"])
    attendues = [n["titre"] for n in donnees["par_matiere"]["histoire"]["notions"] if n["lecon"]]
    assert [e["texte"] for e in r["lecons"]["elements"]] == attendues
    assert all(e["href"].startswith("/cours?matiere=histoire&notion=") for e in r["lecons"]["elements"])
    assert r["lecons"]["retours"] == ["← Matières"]
    assert r["actif"]["id"] == "barre-page-titre"  # focus sur le titre de la petite page ouverte


def test_ex209b_matiere_retenue_sans_fiche_ouvre_l_etape_2_sans_effacer(banc, donnees):
    r = jouer(
        banc,
        "/cours",
        r"""
        rubrique("fiches").click();
        await attendreEtape(2);
        return { page: lirePage(), stockage: S.stockage() };
        """,
        avant=memoire(MATIERE_SANS_LECON),
    )
    assert r["page"]["matieres"] == donnees["fiches"]
    assert r["stockage"]["jules.matiere"] == MATIERE_SANS_LECON


def test_ex209b2_mes_lecons_sans_lecon_dans_la_matiere(banc):
    r = jouer(
        banc,
        "/studio",
        r"""
        rubrique("lecons").click();
        await attendreEtape(4);
        return lirePage();
        """,
        avant=memoire(MATIERE_SANS_LECON),
    )
    assert r["vide"] == "Pas encore de leçon dans cette matière."
    assert r["elements"] == []
    assert r["retours"] == ["← Matières"]


def test_ex209b3_parametres_de_l_adresse_l_emportent_sur_nav(banc, donnees):
    r = jouer(
        banc,
        "/cours?matiere=mathematiques#nav=lecons/histoire",
        r"""
        await attendreEtape(4);
        await S.attendre(() => S.el("#catalogue-titre").textContent.includes(":"), 5000);
        return { barre: lirePage(), page: S.el("#catalogue-titre").textContent, hash: location.hash };
        """,
        avant=memoire("histoire"),
    )
    nom = donnees["noms"]["mathematiques"]
    assert r["barre"]["titre"] == nom
    assert all("matiere=mathematiques" in e["href"] for e in r["barre"]["elements"])
    assert r["page"] == f"Mes leçons : {nom}"
    assert r["hash"] == "#nav=lecons/mathematiques"


def test_ex209c_fragment_de_notion_sur_l_accueil(banc):
    r = jouer(
        banc,
        "/#" + NOTION_THALES,
        r"""
        await attendreEtape(4);
        await S.attendre(() => !S.el("#fiche").classList.contains("cache"), 5000);
        return { barre: lirePage(), fiche: S.el("#fiche-titre").textContent, stockage: S.stockage() };
        """,
        avant=memoire("histoire"),
    )
    assert r["barre"]["rubrique"] == "fiches"
    assert r["stockage"]["jules.matiere"] == "mathematiques"
    courantes = [e for e in r["barre"]["elements"] if e["courant"] == "true"]
    assert [e["href"] for e in courantes] == ["/#" + NOTION_THALES]
    assert r["fiche"]  # la fiche de la notion est ouverte (son titre propre peut differer du libelle de liste)


def test_ex209d_matiere_retenue_inconnue_un_seul_appel(banc, donnees):
    r = jouer(
        banc,
        "/cours",
        r"""
        await S.attendre(() => S.el("#catalogue-titre").textContent.includes(":"), 5000);
        await S.pause(300);
        return { requetes: S.requetes(), page: S.el("#catalogue-titre").textContent, stockage: S.stockage(),
                 erreurs: S.erreurs() };
        """,
        avant=memoire("inconnue"),
    )
    assert [q for q in r["requetes"] if q.startswith(PARCOURS)] == [PARCOURS + "?matiere=inconnue"]
    repli = (donnees["avec_lecon"] or donnees["matieres"])[0]
    assert r["page"] == f"Mes leçons : {donnees['noms'][repli]}"
    assert r["stockage"]["jules.matiere"] == "inconnue"
    assert r["erreurs"] == []


@pytest.mark.parametrize("chemin", [PARCOURS, STUDIO])
def test_ex209e_api_matiere_inconnue_retombe_sur_la_premiere_avec_lecon(client, chemin):
    # Calcul du repli attendu a partir du catalogue (ordre des matieres) et des lecons (champ `lecon`).
    catalogue = client.get(chemin).json()["matieres"]
    avec_lecon = [
        m["id"]
        for m in catalogue
        if any(n["lecon"] for n in client.get(chemin, params={"matiere": m["id"]}).json()["notions"])
    ]
    attendu = (avec_lecon or [catalogue[0]["id"]])[0]
    reponse = client.get(chemin, params={"matiere": "inconnue"})
    assert reponse.status_code == 200
    assert reponse.json()["matiere"] == attendu


def test_ex209f_notion_de_la_matiere_ouvre_la_lecon(banc):
    r = jouer(
        banc,
        f"/cours?matiere=mathematiques&notion={NOTION_THALES}",
        r"""
        await S.attendre(() => !S.el("#lecon").classList.contains("cache"), 6000);
        await S.pause(200);
        return { titre: S.el("#lecon-titre").textContent, catalogue: S.el("#catalogue").classList.contains("cache"),
                 parcours: S.requetes().filter((q) => q.startsWith("/api/eleve/cours/parcours")),
                 erreurs: S.erreurs() };
        """,
    )
    assert r["titre"] and r["catalogue"] is True
    assert r["parcours"] == [PARCOURS + "?matiere=mathematiques"]
    assert r["erreurs"] == []


def test_ex209f_notion_d_une_autre_matiere_laisse_la_liste(banc):
    r = jouer(
        banc,
        f"/cours?matiere=mathematiques&notion={NOTION_HISTOIRE}",
        r"""
        await S.attendre(() => S.el("#parcours-liste").childElementCount > 0, 5000);
        await S.pause(400);
        const cache = (id) => S.el(id).classList.contains("cache");
        return { lecon: cache("#lecon"), catalogue: cache("#catalogue"),
                 parcours: S.requetes().filter((q) => q.startsWith("/api/eleve/cours/parcours")),
                 ouvertures: S.requetes().filter((q) => q.includes("/ouvrir")), erreurs: S.erreurs() };
        """,
    )
    assert r["lecon"] is True and r["catalogue"] is False
    assert r["parcours"] == [PARCOURS + "?matiere=mathematiques"]
    assert r["ouvertures"] == [] and r["erreurs"] == []


def test_ex209g_nav_dans_l_adresse_restaure_le_chapitre(banc, donnees):
    notions = donnees["fiches_reponse"]["matieres"][0]["notions"]
    chapitre = notions[-1]["chapitre"]
    fragment = "nav=fiches/mathematiques/" + urllib.parse.quote(chapitre, safe="")
    r = jouer(
        banc,
        "/?x=1#" + fragment,
        r"""
        await attendreEtape(4);
        await S.pause(300);
        return { barre: lirePage(), hash: location.hash, erreurs: S.erreurs() };
        """,
    )
    assert r["barre"]["titre"] == chapitre
    assert [e["texte"] for e in r["barre"]["elements"]] == [n["titre"] for n in notions if n["chapitre"] == chapitre]
    assert r["barre"]["retours"] == ["← Chapitres"]
    assert r["erreurs"] == []


@pytest.mark.parametrize("fragment", ["nav=%zz", "nav=inconnue/x", "nav=fiches//", "nav="])
def test_ex209g_nav_mal_forme_etape_1_sans_erreur(banc, fragment):
    r = jouer(
        banc,
        "/?x=1#" + fragment,
        "await S.pause(800); return { barre: lirePage(), erreurs: S.erreurs() };",
    )
    assert r["barre"]["etape"] == 1
    assert r["erreurs"] == []


def test_ex209h_retour_rend_le_focus_au_chapitre_ouvert(banc, donnees):
    chapitres = sorted({n["chapitre"] for n in donnees["fiches_reponse"]["matieres"][0]["notions"]})
    r = jouer(
        banc,
        "/cours",
        r"""
        rubrique("fiches").click();
        await attendreEtape(3);
        const boutons = [...document.querySelectorAll("#barre-jules [data-chapitre]")];
        const choisi = boutons[boutons.length - 1];
        const nom = choisi.dataset.chapitre;
        choisi.click();
        await attendreEtape(4);
        const titreFocus = S.actif().id;
        retour().click();
        await attendreEtape(3);
        const a = document.activeElement;
        const retourMenu = [...document.querySelectorAll("#barre-jules .barre-retour")].map((b) => b.textContent);
        retour().click();
        await attendreEtape(2);
        const surMatiere = document.activeElement.dataset.matiere;
        retour().click();
        await attendreEtape(1);
        return { nom, titreFocus, actif: a.dataset.chapitre || null, retourMenu, surMatiere,
                 surRubrique: document.activeElement.dataset.sousPages };
        """,
        avant=memoire("mathematiques"),
    )
    assert r["nom"] in chapitres
    assert r["titreFocus"] == "barre-page-titre"
    assert r["actif"] == r["nom"]
    assert r["retourMenu"] == ["← Matières"]
    assert r["surMatiere"] == "mathematiques"
    assert r["surRubrique"] == "fiches"


def test_ex209i_aucun_selecteur_de_matiere_dans_les_html():
    for nom in ("accueil.html", "cours.html", "studio.html", "eleve.html"):
        html = (STATIQUE / nom).read_text(encoding="utf-8")
        assert "select-matiere" not in html, nom
        assert "<select" not in html, nom
    for nom in ("accueil.js", "cours.js", "studio.js", "eleve.js", "navigation.js"):
        assert "select-matiere" not in (STATIQUE / nom).read_text(encoding="utf-8"), nom


@pytest.mark.parametrize("page", ["/", "/cours", "/studio"])
def test_ex209i_aucun_selecteur_dans_la_page_affichee(banc, page):
    r = jouer(banc, page, "await S.pause(500); return document.querySelectorAll('select, #select-matiere').length;")
    assert r == 0


@pytest.mark.parametrize(("page", "chemin"), [("/cours", PARCOURS), ("/studio", STUDIO)])
def test_ex209j_premiere_visite_aucune_matiere_imposee(banc, donnees, page, chemin):
    repli = (donnees["avec_lecon"] or donnees["matieres"])[0]
    titres_repli = [n["titre"] for n in donnees["par_matiere"][repli]["notions"]]
    r = jouer(
        banc,
        page,
        r"""
        await S.attendre(() => !S.el("#choix-matiere").classList.contains("cache"), 5000);
        await S.pause(200);
        const visibleTexte = document.querySelector("main").innerText;
        const avant = { consigne: S.el(".choix-matiere-consigne").textContent,
                        boutons: [...document.querySelectorAll(".choix-matiere-bouton")].map((b) => b.dataset.matiere),
                        texte: visibleTexte, requetes: S.requetes(), stockage: S.stockage() };
        S.el('.choix-matiere-bouton[data-matiere="histoire"]').click();
        await S.attendre(() => S.el("#catalogue-titre").textContent.includes(":"), 5000);
        await S.pause(200);
        return { avant, apres: { titre: S.el("#catalogue-titre").textContent, stockage: S.stockage(),
                 requetes: S.requetes(), actif: S.actif().id } };
        """,
        avant=memoire(None),
    )
    avant = r["avant"]
    assert avant["consigne"] == "Choisis une matière"
    assert avant["boutons"] == donnees["matieres"]
    assert [q for q in avant["requetes"] if q.startswith(chemin)] == [chemin]
    assert avant["stockage"] == {}
    assert not [t for t in titres_repli if t in avant["texte"]], "notions de la matiere par defaut affichees"
    apres = r["apres"]
    assert apres["stockage"] == {"jules.matiere": "histoire"}
    assert apres["titre"].endswith(": " + donnees["noms"]["histoire"])
    assert [q for q in apres["requetes"] if q.startswith(chemin)] == [chemin, chemin + "?matiere=histoire"]
    assert apres["actif"] == "catalogue-titre"


# (k) : une seule liste de notions visible a la fois, dans la barre ou au centre, jamais les deux.
LISTES_VISIBLES = r"""
  const visible = (e) => !!e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== "hidden";
  const listes = () => {
    const barre = document.querySelector("#barre-jules .barre-page[data-etape='4']");
    const centre = document.querySelector(ZONE);
    return { barre: visible(barre) && barre.querySelectorAll("a.barre-element").length > 0,
             centre: visible(centre) && centre.querySelectorAll(ELEMENT).length > 0 };
  };
"""


@pytest.mark.parametrize(
    ("page", "rubrique_page", "zone", "element"),
    [("/cours", "lecons", "#parcours", ".notion-ligne"), ("/studio", "supports", "#notions", ".notion-bloc")],
)
def test_ex209k_une_seule_liste_de_notions_a_1280(banc, page, rubrique_page, zone, element):
    etapes = LISTES_VISIBLES.replace("ZONE", json.dumps(zone)).replace("ELEMENT", json.dumps(element)) + (
        r"""
        await S.attendre(() => document.querySelector(ELEMENT_SEL), 5000);
        const auChargement = listes();
        rubrique(RUBRIQUE).click();
        await attendreEtape(4);
        await S.pause(100);
        const barreOuverte = listes();
        retour().click(); await attendreEtape(2);
        retour().click(); await attendreEtape(1);
        await S.pause(100);
        return { auChargement, barreOuverte, menu: listes() };
        """.replace("ELEMENT_SEL", json.dumps(zone + " " + element)).replace("RUBRIQUE", json.dumps(rubrique_page))
    )
    r = jouer(banc, page, etapes, avant=memoire("mathematiques"))
    assert r["auChargement"] == {"barre": False, "centre": True}
    assert r["barreOuverte"] == {"barre": True, "centre": False}
    assert r["menu"] == {"barre": False, "centre": True}


# --- EX-210 (b) a (g) : cache de MS.api -------------------------------------------------------------------


def _parcours(requetes: list[str]) -> list[str]:
    return [q for q in requetes if q.startswith(PARCOURS)]


def test_ex210b_mes_lecons_meme_matiere_aucun_appel_autre_matiere_un(banc):
    r = jouer(
        banc,
        "/cours",
        r"""
        await S.attendre(() => S.el("#catalogue-titre").textContent.includes(":"), 5000);
        const chargement = S.requetes();
        rubrique("lecons").click();
        await attendreEtape(4);
        const memeMatiere = S.requetes();
        retour().click();
        await attendreEtape(2);
        const etape2 = S.requetes();
        matiere("histoire").click();
        await attendreEtape(4);
        await S.pause(100);
        return { chargement, memeMatiere, etape2, autre: S.requetes(), titre: lirePage().titre };
        """,
        avant=memoire("mathematiques"),
    )
    base = [PARCOURS + "?matiere=mathematiques"]
    assert _parcours(r["chargement"]) == base
    assert _parcours(r["memeMatiere"]) == base
    assert _parcours(r["etape2"]) == base
    assert _parcours(r["autre"]) == [*base, PARCOURS + "?matiere=histoire"]


def _requete(banc, methode: str, chemin: str, corps: dict[str, Any]) -> dict[str, Any]:
    requete = urllib.request.Request(  # noqa: S310 - serveur local de test
        banc.url + chemin,
        data=json.dumps(corps).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method=methode,
    )
    with urllib.request.urlopen(requete) as reponse:  # noqa: S310 - serveur local de test
        resultat: dict[str, Any] = json.loads(reponse.read())
        return resultat


@pytest.fixture
def banc_studio(tmp_path_factory):
    """Banc a part : la validation d'un support modifie les donnees du tuteur."""
    tuteur = _tuteur(tmp_path_factory, None)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n4-studio")) as b:
            yield b
    finally:
        tuteur.fermer()


def test_ex210c_valider_un_support_rappelle_studio_notions(banc_studio):
    # Support prepare par l'API (fiche de deux sections personnelles : minimum pour valider).
    support = _requete(banc_studio, "POST", f"/api/eleve/studio/notions/{NOTION_THALES}/creer", {"type": "fiche"})
    sid = support["support"]["id"]
    for chemin, valeur in [
        (["sections", 0, "titre"], "Ce que je retiens"),
        (["sections", 0, "contenu"], "Moi je retiens que les longueurs sont proportionnelles."),
        (["sections", 1, "titre"], "Un exemple perso"),
        (["sections", 1, "contenu"], "Avec deux triangles emboites, je trouve le cote qui manque."),
    ]:
        _requete(banc_studio, "POST", f"/api/eleve/studio/supports/{sid}/ecrire", {"chemin": chemin, "valeur": valeur})
    r = banc_studio.jouer(
        "/studio",
        DEBUT
        + r"""
        const ligne = () => document.querySelector('.support-ligne[data-id="SID"]');
        await S.attendre(ligne, 5000);
        const avant = ligne().querySelector(".pastille-statut").textContent;
        const n0 = S.requetes().filter((q) => q.startsWith("/api/eleve/studio/notions?")).length;
        ligne().click();
        const pret = () => !S.el("#support").classList.contains("cache") && !S.el("#bouton-valider").disabled;
        await S.attendre(pret, 5000);
        S.el("#bouton-valider").click();
        await S.attendre(() => ligne() && ligne().querySelector(".pastille-statut").textContent === "validé", 5000);
        return { avant, n0, appels: S.appels().filter((a) => a.chemin.startsWith("/api/eleve/studio/")),
                 n1: S.requetes().filter((q) => q.startsWith("/api/eleve/studio/notions?")).length };
        """.replace("SID", sid),
        avant=memoire("mathematiques"),
        budget_ms=12000,
    )
    assert r["avant"] == "brouillon"
    assert (r["n0"], r["n1"]) == (1, 2)  # le POST de validation a vide le cache : nouvel appel reseau
    assert {"methode": "POST", "chemin": f"/api/eleve/studio/supports/{sid}/valider"} in r["appels"]


def test_ex210d_second_get_session_apres_la_porte_part_vers_le_reseau(banc_codes):
    etapes = SAISIR.replace("CODE", json.dumps(CODE_ELEVE)) + "await S.pause(200); return S.appels();"
    appels = banc_codes.jouer("/cours", etapes, budget_ms=10000)
    assert [a["methode"] for a in appels if a["chemin"] == "/api/session"] == ["GET", "POST", "GET"]


def test_ex210e_une_erreur_n_est_pas_gardee(banc, donnees):
    r = jouer(
        banc,
        "/cours",
        r"""
        await S.attendre(() => document.querySelector(".cours-erreur-ligne"), 5000);
        const erreurPage = S.el(".cours-erreur-ligne").textContent;
        rubrique("lecons").click();
        await attendreEtape(4);
        return { erreurPage, barre: lirePage(), requetes: S.requetes() };
        """,
        avant=memoire("mathematiques"),
        pannes={PARCOURS: 1},
    )
    assert "Impossible de charger" in r["erreurPage"]
    assert _parcours(r["requetes"]) == [PARCOURS + "?matiere=mathematiques"] * 2
    attendues = [n["titre"] for n in donnees["par_matiere"]["mathematiques"]["notions"] if n["lecon"]]
    assert [e["texte"] for e in r["barre"]["elements"]] == attendues


def test_ex210f_page_et_barre_en_meme_temps_un_seul_appel(banc):
    r = jouer(
        banc,
        "/cours?matiere=mathematiques#nav=lecons/mathematiques",
        r"""
        await attendreEtape(4);
        await S.attendre(() => S.el("#catalogue-titre").textContent.includes(":"), 5000);
        await S.pause(300);
        return S.requetes();
        """,
    )
    assert _parcours(r) == [PARCOURS + "?matiere=mathematiques"]


CACHE_COPIE = r"""
  await S.attendre(() => S.el("#catalogue-titre").textContent.includes(":"), 5000);
  const chemin = "/api/eleve/cours/parcours?matiere=mathematiques";
  const a = await MS.api(chemin);
  a.notions.forEach((n) => { n.titre = "MODIFIE PAR LA PAGE"; });
  const b = await MS.api(chemin);
  rubrique("lecons").click();
  await attendreEtape(4);
  return { distincts: a !== b, b: b.notions.map((n) => n.titre).includes("MODIFIE PAR LA PAGE"),
           barre: lirePage().elements.map((e) => e.texte), requetes: S.requetes() };
"""


def test_ex210g_modifier_l_objet_recu_ne_change_pas_la_barre(banc):
    r = jouer(banc, "/cours", CACHE_COPIE, avant=memoire("mathematiques"))
    assert r["distincts"] is True and r["b"] is False
    assert r["barre"] and "MODIFIE PAR LA PAGE" not in r["barre"]
    assert _parcours(r["requetes"]) == [PARCOURS + "?matiere=mathematiques"]


def test_ex210g_mutation_sans_structuredclone_fait_echouer_le_test(banc):
    source = (STATIQUE / "commun.js").read_text(encoding="utf-8")
    ancre = "return structuredClone(await promesse);"
    assert source.count(ancre) == 1
    mutant = source.replace(ancre, "return await promesse;")
    r = jouer(banc, "/cours", CACHE_COPIE, avant=memoire("mathematiques"), remplaces={"/static/commun.js": mutant})
    assert r["b"] is True and "MODIFIE PAR LA PAGE" in r["barre"]


# --- EX-210 : cache, statique -----------------------------------------------------------------------------


def test_ex210_cache_liste_blanche_et_regles_dans_commun_js():
    js = (STATIQUE / "commun.js").read_text(encoding="utf-8")
    bloc = re.search(r"CHEMINS_EN_CACHE: Object\.freeze\(\[(.*?)\]\)", js, re.S)
    assert bloc, "liste blanche nommee absente de commun.js"
    assert re.findall(r'"([^"]+)"', bloc.group(1)) == [FICHES, PARCOURS, STUDIO]
    assert 'String(options.method || "GET").toUpperCase()' in js  # absence de method = GET
    assert "MS._cache.clear()" in js  # tout ce qui n'est pas GET vide le cache
    assert "structuredClone(" in js
    assert "/api/session" not in bloc.group(1)
    # Aucune liste de methodes de mutation (spec : « pas de liste de methodes de mutation »).
    assert not re.search(r'\[\s*"(POST|PUT|PATCH|DELETE)"', js)


def test_ex210_cache_scenario_regles_directes(banc):
    r = jouer(
        banc,
        "/discuter",
        r"""
        const p = "/api/eleve/cours/parcours?matiere=histoire";
        await Promise.all([MS.api(p), MS.api(p)]);          // promesse partagee
        await MS.api(p);                                    // servi par le cache
        await MS.api("/api/infos"); await MS.api("/api/infos");  // hors liste blanche : jamais en cache
        await MS.api("/api/conversations", MS.json({ mode: "libre" })).catch(() => null);  // non GET : vide
        await MS.api(p);
        return S.requetes().filter((q) => q === p || q === "/api/infos");
        """,
    )
    p = PARCOURS + "?matiere=histoire"
    assert r.count(p) == 2
    assert r.count("/api/infos") == 3  # chargement de la page + deux lectures directes
