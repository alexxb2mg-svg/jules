"""Figures dans la discussion (jules/modules/figures.py, lot 1 : droite-affine).

Le modele n'ecrit qu'un bloc ```figure {gabarit, valeurs} ; le module le normalise ou le retire sans bruit,
selon la liste blanche et les bornes declarees dans extensions/droite-affine/extension.yaml (cle `discussion`).
"""

from __future__ import annotations

import base64
import json
import os
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
import yaml

from jules.acces import empreinte
from jules.config import depuis_dict
from jules.extensions import figures_pour_discussion
from jules.llm.factice import Brique as Factice
from jules.modules.base import Module
from jules.modules.figures import normaliser, texte_sans_figures
from jules.modules.suivi import extrait
from jules.moteur import Tuteur
from jules.stockage import Message
from jules.web.app import creer_app
from tests.cdp import navigateur, navigateur_cdp
from tests.conftest import RACINE

NORMALISE = '```figure\n{"gabarit":"droite-affine","valeurs":{"a":2,"b":1}}\n```'


def _bloc(json_brut: str) -> str:
    return f"Regarde la droite :\n\n```figure\n{json_brut}\n```\n\nOù coupe-t-elle l'axe vertical ?"


def _filtrer(tuteur, texte: str, mode: str = "aide-devoirs") -> tuple[str, list[dict]]:
    conv = tuteur.stockage.creer_conversation(mode)
    sortie = tuteur.module("figures").filtrer_reponse(conv, texte, lambda: "relance interdite")
    return sortie, [e["donnees"] for e in tuteur.stockage.evenements("figure_ecartee")]


def test_bloc_valide_normalise_de_bout_en_bout(tuteur):
    tuteur.llm.regle = lambda s, t, m: _bloc('{ "valeurs": {"b": 1, "a": 2.0}, "gabarit": "droite-affine" }')
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    bot = tuteur.echanger(conv.id, "Comment on trace f(x) = 2x + 1 ?")
    assert bot.texte == f"Regarde la droite :\n\n{NORMALISE}\n\nOù coupe-t-elle l'axe vertical ?"
    assert tuteur.stockage.conversation(conv.id).messages[-1].texte == bot.texte  # stocke tel quel
    assert any("Figures disponibles" in a["systeme"] for a in tuteur.llm.appels)  # le modele sait qu'elle existe
    assert tuteur.stockage.evenements("figure_ecartee") == []


def test_valeurs_absentes_prennent_le_defaut_et_le_pas_decimal_passe(tuteur):
    sortie, ecartees = _filtrer(tuteur, _bloc('{"gabarit": "droite-affine", "valeurs": {"a": -2.5}}'))
    assert '{"gabarit":"droite-affine","valeurs":{"a":-2.5,"b":0}}' in sortie
    assert ecartees == []


def test_bloc_invalide_retire_texte_garde(tuteur):
    cas = {
        '{"gabarit": "inconnu", "valeurs": {}}': "gabarit non autorise",
        '{"gabarit": "droite-affine", "valeurs": {"a": 99}}': "a hors bornes",
        '{"gabarit": "droite-affine", "valeurs": {"b": 0.5}}': "b hors pas",
        '{"gabarit": "droite-affine", "valeurs": {"a": 1,': "json illisible",
        '{"gabarit": "droite-affine", "valeurs": {}, "svg": "<svg/>"}': "attendu {gabarit, valeurs}",
        '{"gabarit": "droite-affine", "valeurs": {"c": 1}}': "valeur inconnue (c)",
        '{"gabarit": "droite-affine", "valeurs": {"a": true}}': "a : nombre attendu",
        '{"gabarit": "droite-affine", "valeurs": {"a": NaN}}': "a : nombre attendu",
    }
    for json_brut, raison in cas.items():
        sortie, ecartees = _filtrer(tuteur, _bloc(json_brut))
        assert sortie == "Regarde la droite :\n\nOù coupe-t-elle l'axe vertical ?", json_brut
        assert ecartees[0]["raison"] == raison, json_brut


def test_deux_blocs_un_seul_garde(tuteur):
    valide = _bloc('{"gabarit": "droite-affine", "valeurs": {"a": 2, "b": 1}}')
    sortie, ecartees = _filtrer(tuteur, valide + "\n\n" + valide)
    assert sortie.count("```figure") == 1
    assert ecartees == [{"gabarit": "droite-affine", "raison": "une seule figure par message"}]


def test_mode_epreuve_sans_contribution_et_bloc_retire(tuteur):
    conv = tuteur.stockage.creer_conversation("epreuve")
    assert tuteur.module("figures").contribution(conv) is None
    sortie, ecartees = _filtrer(tuteur, _bloc('{"gabarit": "droite-affine", "valeurs": {"a": 2}}'), "epreuve")
    assert "figure" not in sortie
    assert ecartees == [{"gabarit": "droite-affine", "raison": "mode sans figure"}]


def test_contribution_donne_bornes_et_regles_dans_les_modes_autorises(tuteur):
    for mode in ("aide-devoirs", "reexplique"):
        texte = tuteur.module("figures").contribution(tuteur.stockage.creer_conversation(mode))
        assert "droite-affine" in texte
        assert "a de -3 à 3 par pas de 0.5 (défaut 1)" in texte
        assert "jamais de SVG" in texte


def test_svg_ecrit_dans_le_texte_reste_du_texte(tuteur):
    texte = 'Voici un dessin : <svg><circle r="5"/></svg> et une figure de style.'
    assert _filtrer(tuteur, texte) == (texte, [])


def test_bloc_sans_cloture_ou_en_tildes_est_quand_meme_verifie(tuteur):
    sortie, _ = _filtrer(tuteur, 'Vois :\n~~~~figure\n{"gabarit": "droite-affine", "valeurs": {"a": 2, "b": 1}}')
    assert sortie == f"Vois :\n{NORMALISE}"
    sortie, ecartees = _filtrer(tuteur, 'Vois :\n```figure\n{"gabarit": "droite-affine", "valeurs": {"a": 50}}')
    assert sortie == "Vois :"
    assert ecartees[-1]["raison"] == "a hors bornes"


def test_bloc_dans_une_citation_neutralise(tuteur):
    texte = '> ```figure\n> {"gabarit": "droite-affine", "valeurs": {"a": 50}}\n> ```'
    sortie, ecartees = _filtrer(tuteur, texte)
    assert "figure" not in sortie  # le rendu markdown n'en fera jamais une figure
    assert ecartees == [{"gabarit": "", "raison": "imbrique"}]


def test_figures_apres_notions_et_cours_dans_config():
    ids = [m["id"] for m in yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8"))["modules"]]
    assert ids.index("figures") > ids.index("notions")
    assert ids.index("figures") > ids.index("cours")


def test_aucun_module_ne_filtre_la_reponse_apres_figures(tuteur):
    """Un filtre place apres 'figures' pourrait relancer le modele et laisser passer un bloc non verifie."""
    ids = [m.id for m in tuteur.modules]
    apres = tuteur.modules[ids.index("figures") + 1 :]
    assert [m.id for m in apres if type(m).filtrer_reponse is not Module.filtrer_reponse] == []


# --- lot 2 : les cinq gabarits declares, drapeau `revele`, texte sans figures ---------------------------

GABARITS_DECLARES = [
    "droite-affine",
    "triangle-thales",
    "triangle-rectangle",
    "equation-solutions",
    "probabilites-frequences",
]
REVELENT = {"triangle-rectangle", "equation-solutions"}


def _bornes(tuteur, gabarit: str) -> dict[str, dict[str, float]]:
    return figures_pour_discussion(tuteur.extensions)[gabarit]["valeurs"]


def _json(gabarit: str, valeurs: dict, compact: bool = False) -> str:
    objet = {"gabarit": gabarit, "valeurs": valeurs}
    return json.dumps(objet, sort_keys=True, separators=(",", ":")) if compact else json.dumps(objet)


@pytest.mark.parametrize("gabarit", GABARITS_DECLARES)
def test_bornes_de_chaque_gabarit(tuteur, gabarit):
    """En reexplique (tout est permis) : min et max acceptes et normalises ; min - pas et une valeur entre
    deux crans refuses, valeur par valeur."""
    bornes = _bornes(tuteur, gabarit)
    autorises = figures_pour_discussion(tuteur.extensions)
    for cle in ("min", "max"):
        valeurs = {nom: b[cle] for nom, b in bornes.items()}
        normalise, lu, raison = normaliser(_json(gabarit, valeurs), autorises)
        assert (lu, raison) == (gabarit, ""), cle
        attendu = {nom: int(v) if v == int(v) else v for nom, v in valeurs.items()}
        assert normalise == _json(gabarit, attendu, compact=True), cle
        sortie, ecartees = _filtrer(tuteur, _bloc(_json(gabarit, valeurs)), "reexplique")
        assert f"```figure\n{normalise}\n```" in sortie and ecartees == [], cle
    for nom, b in bornes.items():
        _, _, raison = normaliser(_json(gabarit, {nom: b["min"] - b["pas"]}), autorises)
        assert raison == f"{nom} hors bornes"
        _, _, raison = normaliser(_json(gabarit, {nom: b["min"] + b["pas"] / 2}), autorises)
        assert raison == f"{nom} hors pas"
        sortie, ecartees = _filtrer(tuteur, _bloc(_json(gabarit, {nom: b["max"] + b["pas"]})), "reexplique")
        assert "```figure" not in sortie and ecartees[0]["raison"] == f"{nom} hors bornes"  # le plus recent d'abord


def test_valeurs_decimales_normalisees_sans_bruit_flottant(tuteur):
    sortie, _ = _filtrer(tuteur, _bloc('{"gabarit": "triangle-thales", "valeurs": {"t": 0.7}}'))
    assert '{"gabarit":"triangle-thales","valeurs":{"t":0.7}}' in sortie


@pytest.mark.parametrize("gabarit", GABARITS_DECLARES)
def test_drapeau_revele_selon_le_mode(tuteur, gabarit):
    """Une figure qui montre la reponse : proposee et acceptee en reexplique, absente et retiree en aide-devoirs."""
    figures = tuteur.module("figures")
    bloc = _bloc(_json(gabarit, {}))
    for mode, permis in (("reexplique", True), ("aide-devoirs", gabarit not in REVELENT)):
        conv = tuteur.stockage.creer_conversation(mode)
        assert (gabarit in figures.autorises(conv)) is permis, mode
        assert (f"- {gabarit} :" in figures.contribution(conv)) is permis, mode
        sortie, ecartees = _filtrer(tuteur, bloc, mode)
        assert ("```figure" in sortie) is permis, mode
        if not permis:
            assert ecartees[0] == {"gabarit": gabarit, "raison": "gabarit non autorise"}


def test_modes_revele_reglable(tuteur):
    figures = tuteur.module("figures")
    assert figures.modes_revele == ("reexplique",)  # config.yaml du depot
    figures.reglages["modes_revele"] = ["aide-devoirs"]
    assert "equation-solutions" in figures.autorises(tuteur.stockage.creer_conversation("aide-devoirs"))
    assert "equation-solutions" not in figures.autorises(tuteur.stockage.creer_conversation("reexplique"))


@pytest.mark.parametrize("mode", ["aide-devoirs", "reexplique"])
def test_contribution_et_prompt_complet_sans_double_accolade(tuteur, mode):
    """Voir test_prompt_complet_sans_balise_restante (tests/test_texte.py) : « }} » ne doit jamais arriver au modele."""
    conv = tuteur.stockage.creer_conversation(mode)
    contribution = tuteur.module("figures").contribution(conv)
    assert contribution and "}}" not in contribution and "{{" not in contribution
    systeme = tuteur.systeme(conv)
    assert "}}" not in systeme and "{{" not in systeme
    assert ("equation-solutions" in contribution) is (mode == "reexplique")


def test_texte_sans_figures():
    texte = (
        "Regarde :\n\n```figure\n" + '{"gabarit":"triangle-thales","valeurs":{"t":0.5}}' + "\n```\n\nEt alors ?\n"
        "~~~figure\n{pas du json\n~~~\nFin."
    )
    assert texte_sans_figures(texte) == "Regarde :\n\n[figure : triangle-thales]\n\nEt alors ?\n[figure]\nFin."
    assert texte_sans_figures("Une figure de style, sans bloc.") == "Une figure de style, sans bloc."


def test_analyse_de_suivi_ne_voit_pas_le_json_des_figures(tuteur):
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.stockage.ajouter_message(conv.id, Message(role="eleve", texte="Thalès ?"))
    tuteur.stockage.ajouter_message(conv.id, Message(role="bot", texte=f"Regarde :\n\n{NORMALISE}\n\nEt b ?"))
    lu = extrait(tuteur.stockage.conversation(conv.id))
    assert "[figure : droite-affine]" in lu
    assert "gabarit" not in lu and "{" not in lu


# --- rendu dans la bulle, dans un vrai Chromium (tests/cdp.py) ; ignore sans Chromium ou sans npm run build ---

INTERFACE = RACINE / "jules" / "web" / "static" / "app" / "index.html"
CODE = "1234"
# Figure de la bulle : largeur du svg et de la bulle, nombre d'elements dessines, lignes.
MESURE = """(() => { const s = document.querySelector('.bulle-jules svg[viewBox="0 0 340 340"]'); if (!s) return null;
  const b = s.closest('.bulle-jules');
  return {svg: s.getBoundingClientRect().width, bulle: b.getBoundingClientRect().width,
  elements: s.querySelectorAll('*').length, lignes: s.querySelectorAll('line').length,
  fond: getComputedStyle(s.parentElement).backgroundColor}; })()"""


def _demarrer(projet, brut_config):
    if not INTERFACE.is_file():
        pytest.skip("interface React non construite (npm run build dans front/)")
    brut_config["acces"] = {"code_eleve": empreinte(CODE), "code_parent": empreinte("parent67")}
    tuteur = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(creer_app(tuteur), host="127.0.0.1", port=port, log_level="error"))
    fil = threading.Thread(target=srv.run, daemon=True)
    fil.start()
    limite = time.monotonic() + 15
    while not srv.started and time.monotonic() < limite:
        time.sleep(0.05)
    assert srv.started, "serveur de test non demarre"
    yield f"http://127.0.0.1:{port}", tuteur
    srv.should_exit = True
    fil.join(timeout=10)
    tuteur.fermer()


@pytest.fixture
def serveur(projet, brut_config):
    yield from _demarrer(projet, brut_config)


def _ouvrir_conversation(page, url: str, titre: str, sombre: bool, nb_bulles: int) -> None:
    """390x844 mobile, theme du systeme clair ou sombre, code eleve, puis #/discuter -> la conversation `titre`."""
    page.commande("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
    theme = "dark" if sombre else "light"
    page.commande("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": theme}])
    page.commande("Page.navigate", url=url + "/static/favicon.ico")
    time.sleep(0.5)
    page.evaluer(
        "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
    )
    page.commande("Page.navigate", url=url + "/app#/discuter")
    bouton = f"[...document.querySelectorAll('aside button')].find((b) => b.innerText.includes('{titre}'))"
    page.attendre(f"!!{bouton}", delai=20)
    page.evaluer(f"{bouton}.click()")
    page.attendre(f"document.querySelectorAll('.bulle-jules').length === {nb_bulles}", delai=10)


@pytest.mark.parametrize("sombre", [False, True], ids=["clair", "sombre"])
def test_figure_dessinee_dans_la_bulle_a_390px(serveur, tmp_path_factory, sombre):
    url, tuteur = serveur
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.stockage.renommer(conv.id, "Droite de test")
    tuteur.stockage.ajouter_message(conv.id, Message(role="eleve", texte="Comment on trace f(x) = 2x + 1 ?"))
    tuteur.stockage.ajouter_message(conv.id, Message(role="bot", texte=f"Regarde :\n\n{NORMALISE}\n\nEt b ?"))
    tuteur.stockage.ajouter_message(conv.id, Message(role="bot", texte='Dessin : <svg><circle r="5"/></svg>'))
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-figure"), (390, 844)) as page:
        _ouvrir_conversation(page, url, "Droite de test", sombre, nb_bulles=2)
        mesure = page.attendre(f"(() => {{ const m = {MESURE}; return m && m.lignes ? m : null; }})()", delai=10)
        assert mesure["lignes"] >= 1
        assert 0 < mesure["svg"] <= mesure["bulle"]
        assert mesure["fond"] != "rgba(0, 0, 0, 0)"  # surface papier, claire dans les deux themes
        assert page.evaluer("document.documentElement.classList.contains('dark')") is sombre
        derniere = "[...document.querySelectorAll('.bulle-jules')].at(-1)"
        assert page.evaluer(f"{derniere}.querySelector('svg')") is None  # un <svg> ecrit reste du texte
        assert "<svg>" in page.evaluer(f"{derniere}.innerText")


# --- lot 3 : figure dynamique dans la bulle (curseurs sous la figure, meme composant Graphe que les fiches) ---


def test_infos_interface_donne_les_bornes_des_curseurs(tuteur):
    """Le front recoit les bornes de chaque valeur (cle `discussion` des extensions), rien d'autre."""
    figures = tuteur.infos_interface()["figures"]
    assert figures["droite-affine"] == {
        "a": {"min": -3, "max": 3, "pas": 0.5, "defaut": 1},
        "b": {"min": -4, "max": 4, "pas": 1, "defaut": 0},
    }
    assert set(figures) == set(figures_pour_discussion(tuteur.extensions))


# Droite tracee par le gabarit droite-affine (trait epais) et curseurs de la bulle.
DROITE = "document.querySelector('[data-figure-bulle] svg line[stroke-width=\"3\"]')"
CURSEURS = "[...document.querySelectorAll('[data-figure-bulle] input[type=range]')]"
ETAT = f"""(() => {{ const c = {CURSEURS}; const d = {DROITE}; const g = document.querySelector('[data-figure-bulle]');
  const bulle = g.closest('.bulle-jules').getBoundingClientRect(), r = g.getBoundingClientRect();
  return {{y2: d && d.getAttribute('y2'), textes: c.map((i) => i.getAttribute('aria-valuetext')),
  svg: g.querySelector('svg').getBoundingClientRect().width, bulle: bulle.width,
  noms: c.map((i) => i.labels[0] && i.labels[0].firstElementChild.firstElementChild.innerText),
  hauteurs: c.map((i) => i.getBoundingClientRect().height),
  dedans: r.left >= bulle.left - 0.5 && r.right <= bulle.right + 0.5,
  debord: document.scrollingElement.scrollWidth - innerWidth}}; }})()"""


def _capture(page, chemin: Path) -> None:
    donnees = base64.b64decode(page.commande("Page.captureScreenshot", format="png")["data"])
    chemin.write_bytes(donnees)
    if dossier := os.environ.get("JULES_CAPTURES"):  # preuve visuelle a regarder (lot 3 de la spec)
        Path(dossier).mkdir(parents=True, exist_ok=True)
        (Path(dossier) / chemin.name).write_bytes(donnees)


@pytest.mark.parametrize("sombre", [False, True], ids=["clair", "sombre"])
def test_curseurs_sous_la_figure_de_la_bulle_a_390px(serveur, tmp_path_factory, sombre):
    url, tuteur = serveur
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.stockage.renommer(conv.id, "Droite mobile")
    tuteur.stockage.ajouter_message(conv.id, Message(role="eleve", texte="Comment on trace f(x) = 2x + 1 ?"))
    tuteur.stockage.ajouter_message(conv.id, Message(role="bot", texte=f"Regarde :\n\n{NORMALISE}\n\nEt b ?"))
    dossier = tmp_path_factory.mktemp("captures-lot3")
    theme = "sombre" if sombre else "clair"
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-curseurs"), (390, 844)) as page:
        _ouvrir_conversation(page, url, "Droite mobile", sombre, nb_bulles=1)
        page.attendre(f"{CURSEURS}.length === 2 && !!{DROITE}", delai=10)
        avant = page.evaluer(ETAT)
        # depart = valeurs de Jules (a = 2, b = 1), lues « a = 2 » ; libelles a et b ; y2 = 170 - (2*6 + 1)*30
        assert avant["textes"] == ["a = 2", "b = 1"] and avant["noms"] == ["a", "b"]
        assert avant["y2"] == "-220"
        assert avant["dedans"] and avant["debord"] <= 0  # dans la bulle, rien ne deborde a 390 px
        assert avant["svg"] >= 240 and avant["bulle"] >= 280, avant  # la bulle s'elargit pour la figure (~304 px)
        assert min(avant["hauteurs"]) >= 24  # cible tactile
        page.evaluer("document.querySelector('[data-figure-bulle]').scrollIntoView({block: 'center'})")
        time.sleep(0.4)
        _capture(page, dossier / f"lot3-{theme}-avant.png")

        # Clavier : focus sur le curseur a, fleche droite -> a = 2,5 (pas 0,5)
        page.evaluer(f"{CURSEURS}[0].focus()")
        page.touche("ArrowRight", "ArrowRight", 39)
        apres_clavier = page.attendre(f"(() => {{ const e = {ETAT}; return e.y2 !== '-220' ? e : null; }})()", delai=5)
        assert apres_clavier["textes"][0] == "a = 2,5" and apres_clavier["y2"] == "-310"

        # Souris : vrai clic pres du debut du curseur a -> pente negative, la droite change encore
        boite = page.evaluer(
            f"(() => {{ const r = {CURSEURS}[0].getBoundingClientRect(); return [r.left, r.top, r.height]; }})()"
        )
        page.cliquer(boite[0] + 6, boite[1] + boite[2] / 2)
        apres = page.attendre(f"(() => {{ const e = {ETAT}; return e.y2 !== '-310' ? e : null; }})()", delai=5)
        a = float(apres["textes"][0].split("= ")[1].replace(",", "."))
        assert a < 0 and apres["textes"][1] == "b = 1"
        assert float(apres["y2"]) == 170 - (a * 6 + 1) * 30
        time.sleep(0.4)
        _capture(page, dossier / f"lot3-{theme}-apres.png")


@pytest.fixture
def serveur_fiches(projet, brut_config):
    """Comme `serveur`, avec les fiches visuelles 3e (bloc graphe de fonctions-lineaires-affines)."""
    brut_config["modules"] = [
        *(brut_config.get("modules") or []),
        {"id": "fiches_visuelles", "reglages": {"bibliotheques": ["fiches-visuelles-3e-experimentales"]}},
    ]
    yield from _demarrer(projet, brut_config)


GRILLE = """(() => { const g = document.querySelector('[data-graphe]'); if (!g) return null;
  const f = g.querySelector('svg').getBoundingClientRect();
  const c = g.querySelector('input[type=range]').getBoundingClientRect();
  return {cote_a_cote: c.left >= f.right, dessous: c.top >= f.bottom}; })()"""


@pytest.mark.parametrize(("largeur", "cote_a_cote"), [(1280, True), (390, False)], ids=["ordinateur", "telephone"])
def test_graphe_de_fiche_garde_sa_grille_avec_la_requete_de_conteneur(
    serveur_fiches, tmp_path_factory, largeur, cote_a_cote
):
    """Graphe passe de `md:` (ecran) a `@container` (son bloc) : la fiche garde figure et curseurs cote a cote sur
    ordinateur, empiles sur telephone."""
    url, _ = serveur_fiches
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-grille"), (largeur, 900)) as page:
        page.commande("Page.navigate", url=url + "/static/favicon.ico")
        time.sleep(0.5)
        page.evaluer(
            "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
            f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
        )
        page.commande("Page.navigate", url=url + "/app#/fiche/fonctions-lineaires-affines")
        grille = page.attendre(GRILLE, delai=20)
        assert grille == {"cote_a_cote": cote_a_cote, "dessous": not cote_a_cote}
