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
from jules.modules.figures import REGLE_DESSIN, normaliser, texte_sans_figures
from jules.modules.suivi import extrait
from jules.moteur import Tuteur
from jules.stockage import Message
from jules.web.app import creer_app
from tests.cdp import navigateur, navigateur_cdp
from tests.conftest import RACINE
from tests.registre_figures import declarations_du_depot

NORMALISE = '```figure\n{"gabarit":"droite-affine","valeurs":{"a":2,"b":1}}\n```'


def _bloc(json_brut: str) -> str:
    return f"Regarde la droite :\n\n```figure\n{json_brut}\n```\n\nOù coupe-t-elle l'axe vertical ?"


def _sans_source(donnees: dict) -> dict:
    """L'evenement porte aussi la `source` ecrite par le modele (diagnostic) : les tests comparent le reste."""
    return {k: v for k, v in donnees.items() if k != "source"}


def _filtrer(tuteur, texte: str, mode: str = "aide-devoirs") -> tuple[str, list[dict]]:
    conv = tuteur.stockage.creer_conversation(mode)
    sortie = tuteur.module("figures").filtrer_reponse(conv, texte, lambda: "relance interdite")
    return sortie, [_sans_source(e["donnees"]) for e in tuteur.stockage.evenements("figure_ecartee")]


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
    assert tuteur.module("figures").contribution(conv) == REGLE_DESSIN  # seulement : jamais de dessin en caracteres
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


# --- lot 2 : les gabarits declares, drapeau `revele`, texte sans figures ---------------------------

# Gabarits declares et drapeau `revele` : LUS dans extensions/*/extension.yaml (tests/registre_figures.py) au
# lieu de listes fermees ; chaque nouveau gabarit est ainsi teste (bornes, revele selon le mode) sans retoucher ce
# fichier. Le repere fixe ci-dessous garde les decisions deja prises a la main.
GABARITS_DECLARES = sorted(declarations_du_depot())
REVELENT = {g for g, (revele, _) in declarations_du_depot().items() if revele}
# onde-sonore ecrit le domaine du son (ultrason...), jauge-decibels « juste a la limite » : ils revelent. urne-tirage
# n'ecrit plus de verdict en mots, triangle-rectangle (2.1) met « ? » dans le carre de l'hypotenuse tant que
# reponse = 0 : ils ne revelent pas.
REVELENT_FIXES = {"equation-solutions", "onde-sonore", "jauge-decibels"}
NON_REVELENT_FIXES = {"droite-affine", "triangle-thales", "urne-tirage", "triangle-rectangle"}


def test_registre_decouvert_et_reperes_fixes(tuteur):
    """La decouverte n'est pas vide, ne contredit pas les decisions fixes, et le tuteur (config.yaml du depot)
    propose exactement ces gabarits avec ce drapeau."""
    assert len(GABARITS_DECLARES) >= 5
    assert REVELENT_FIXES <= REVELENT and not (NON_REVELENT_FIXES & REVELENT)
    declarations = figures_pour_discussion(tuteur.extensions)
    assert sorted(declarations) == GABARITS_DECLARES
    assert {g for g, d in declarations.items() if d["revele"]} == REVELENT


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


# --- valeurs_revele : triangle-rectangle `reponse` (carte t_167db9a6, option A de SPEC) -----------------

TRIANGLE_REPONSE_1 = '{"gabarit": "triangle-rectangle", "valeurs": {"ac": 3, "bc": 4, "reponse": 1}}'


@pytest.mark.parametrize(("mode", "attendu"), [("aide-devoirs", 0), ("cours", 0), ("reexplique", 1)])
def test_valeur_revele_forcee_au_defaut_hors_reexplique(tuteur, mode, attendu):
    """`reponse: 1` ecrit par le modele ressort a 0 en aide-devoirs et en cours (bloc garde, figure « ? »), reste a
    1 en reexplique. Aucun evenement figure_ecartee : la figure est montree."""
    sortie, ecartees = _filtrer(tuteur, _bloc(TRIANGLE_REPONSE_1), mode)
    normalise = json.dumps(
        {"gabarit": "triangle-rectangle", "valeurs": {"ac": 3, "bc": 4, "reponse": attendu}},
        sort_keys=True,
        separators=(",", ":"),
    )
    assert f"```figure\n{normalise}\n```" in sortie, sortie
    assert ecartees == []


@pytest.mark.parametrize("ecrit", ["5", "true", '"oui"', "0.5"])
def test_valeur_revele_forcee_quoi_qu_ecrive_le_modele(tuteur, ecrit):
    """Hors reexplique, la valeur forcee n'est meme pas lue : le bloc passe avec reponse = 0."""
    bloc = f'{{"gabarit": "triangle-rectangle", "valeurs": {{"reponse": {ecrit}}}}}'
    sortie, ecartees = _filtrer(tuteur, _bloc(bloc), "aide-devoirs")
    assert '"reponse":0' in sortie and ecartees == []


def test_valeur_revele_absente_de_la_contribution_hors_reexplique(tuteur):
    figures = tuteur.module("figures")
    for mode, propose in (("aide-devoirs", False), ("cours", False), ("reexplique", True)):
        texte = figures.contribution(tuteur.stockage.creer_conversation(mode))
        ligne = next(ligne for ligne in texte.splitlines() if ligne.startswith("- triangle-rectangle :"))
        assert "ac de 1 à 12" in ligne and "bc de 1 à 12" in ligne, mode
        assert ("reponse de 0 à 1" in ligne) is propose, mode


def test_infos_interface_fige_les_valeurs_revele(tuteur):
    """/api/infos : `reponse` figee (min = max = defaut) -> jamais de curseur dans la bulle, quel que soit le mode."""
    triangle = tuteur.infos_interface()["figures"]["triangle-rectangle"]
    assert triangle["reponse"] == {"min": 0, "max": 0, "pas": 1, "defaut": 0}
    assert triangle["ac"] == {"min": 1, "max": 12, "pas": 1, "defaut": 6}
    # les autres gabarits ne sont pas touches
    assert all(
        b["min"] < b["max"]
        for g, valeurs in tuteur.infos_interface()["figures"].items()
        if not figures_pour_discussion(tuteur.extensions)[g]["valeurs_revele"]
        for b in valeurs.values()
    )


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


# Triangle-rectangle dans la bulle : `reponse` figee par /api/infos -> aucun curseur reponse ; textes du SVG.
TRIANGLE = """(() => { const g = document.querySelector('[data-figure-bulle]'); if (!g) return null;
  const s = g.querySelector('svg'); if (!s || !s.querySelectorAll('text').length) return null;
  return {textes: [...s.querySelectorAll('text')].map((t) => t.textContent.trim()),
  curseurs: [...g.querySelectorAll('input[type=range]')].map((i) => i.getAttribute('aria-valuetext')),
  dedans: g.getBoundingClientRect().right <= g.closest('.bulle-jules').getBoundingClientRect().right + 0.5}; })()"""


@pytest.mark.parametrize(
    ("mode", "attendu_orange"), [("aide-devoirs", "?"), ("reexplique", "25")], ids=["aide-devoirs", "reexplique"]
)
def test_triangle_rectangle_dans_la_bulle_sans_curseur_reponse(serveur, tmp_path_factory, mode, attendu_orange):
    """Le modele ecrit `reponse: 1` : en aide-devoirs le serveur le ramene a 0 (carre orange « ? », aucun AB ni AB²),
    en reexplique il reste a 1 (25 ecrit) ; dans les deux cas, seuls les curseurs ac et bc sont affiches."""
    url, tuteur = serveur
    tuteur.llm.regle = lambda s, t, m: _bloc(
        '{"gabarit": "triangle-rectangle", "valeurs": {"ac": 3, "bc": 4, "reponse": 1}}'
    )
    conv = tuteur.stockage.creer_conversation(mode)
    tuteur.stockage.renommer(conv.id, "Pythagore test")
    tuteur.echanger(conv.id, "Montre-moi Pythagore avec une figure")
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-triangle"), (390, 844)) as page:
        _ouvrir_conversation(page, url, "Pythagore test", False, nb_bulles=1)
        etat = page.attendre(TRIANGLE, delai=10)
        assert etat["curseurs"] == ["ac = 3", "bc = 4"], etat
        assert etat["dedans"]
        assert "9" in etat["textes"] and "16" in etat["textes"]
        assert attendu_orange in etat["textes"], etat
        if attendu_orange == "?":
            assert not {"5", "25"} & set(etat["textes"]), etat  # ni AB = 5 ni AB² = 25
        page.evaluer("document.querySelector('[data-figure-bulle]').scrollIntoView({block: 'center'})")
        time.sleep(0.4)
        _capture(page, tmp_path_factory.mktemp("captures-triangle") / f"triangle-{mode}.png")


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


# --- schema de la fiche visuelle de la notion ({"schema": id}) : toutes matieres ------------------------------

PYTHAGORE = "parallelisme-triangles-pythagore"  # notion du depot dont la fiche visuelle a un bloc schema
HORS_CONVERSATION = "guerre-froide-bipolarisation"  # a aussi un schema, mais n'est pas la notion de la conversation
SCHEMA_NORMALISE = '```figure\n{"schema":"parallelisme-triangles-pythagore"}\n```'


def _conv_notion(tuteur, mode: str = "aide-devoirs", notion: str | None = PYTHAGORE):
    conv = tuteur.stockage.creer_conversation(mode)
    if notion:
        tuteur.module("notions").fixer(conv.id, notion)
    return conv


def _filtrer_conv(tuteur, conv, texte: str) -> tuple[str, list[dict]]:
    sortie = tuteur.module("figures").filtrer_reponse(conv, texte, lambda: "relance interdite")
    return sortie, [_sans_source(e["donnees"]) for e in tuteur.stockage.evenements("figure_ecartee")]


def test_schema_de_la_notion_valide_normalise(tuteur):
    conv = _conv_notion(tuteur)
    titre = tuteur.module("fiches_visuelles").fiches[PYTHAGORE].titre
    assert tuteur.module("figures").schemas(conv) == {PYTHAGORE: titre}
    sortie, ecartees = _filtrer_conv(tuteur, conv, _bloc(f'{{ "schema" : "{PYTHAGORE}" }}'))
    assert sortie == f"Regarde la droite :\n\n{SCHEMA_NORMALISE}\n\nOù coupe-t-elle l'axe vertical ?"
    assert ecartees == []


def test_schema_de_bout_en_bout_par_le_moteur(tuteur):
    tuteur.llm.regle = lambda s, t, m: _bloc(f'{{"schema": "{PYTHAGORE}"}}')
    conv = _conv_notion(tuteur)
    bot = tuteur.echanger(conv.id, "Je comprends pas Pythagore")
    assert SCHEMA_NORMALISE in bot.texte
    assert any("Tu peux montrer le schéma de la notion" in a["systeme"] for a in tuteur.llm.appels)


SANS = "schema non autorise"


def test_schema_inconnu_hors_conversation_ou_sans_notion_retire(tuteur):
    cas = [
        (_conv_notion(tuteur), '{"schema": "notion-inventee"}', "schema:notion-inventee", "schema non autorise"),
        (
            _conv_notion(tuteur),
            f'{{"schema": "{HORS_CONVERSATION}"}}',
            f"schema:{HORS_CONVERSATION}",
            "schema non autorise",
        ),
        (_conv_notion(tuteur, notion=None), f'{{"schema": "{PYTHAGORE}"}}', f"schema:{PYTHAGORE}", SANS),
        (_conv_notion(tuteur), f'{{"schema": "{PYTHAGORE}", "svg": "<svg/>"}}', "", "attendu {schema}"),
        (_conv_notion(tuteur), '{"schema": 3}', "schema:", "schema non autorise"),
    ]
    for conv, json_brut, lu, raison in cas:
        sortie, ecartees = _filtrer_conv(tuteur, conv, _bloc(json_brut))
        assert sortie == "Regarde la droite :\n\nOù coupe-t-elle l'axe vertical ?", json_brut
        assert ecartees[0] == {"gabarit": lu, "raison": raison}, json_brut


def test_schema_d_un_prerequis_accepte(tuteur, monkeypatch):
    figures = tuteur.module("figures")
    monkeypatch.setattr(figures, "_prerequis", lambda notion_id: ["notion-sans-fiche", HORS_CONVERSATION])
    conv = _conv_notion(tuteur)
    assert list(figures.schemas(conv)) == [PYTHAGORE, HORS_CONVERSATION]  # sans fiche visuelle : pas propose
    assert f"- {HORS_CONVERSATION} :" in figures.contribution(conv)
    sortie, ecartees = _filtrer_conv(tuteur, conv, _bloc(f'{{"schema": "{HORS_CONVERSATION}"}}'))
    assert f'{{"schema":"{HORS_CONVERSATION}"}}' in sortie and ecartees == []


def test_prerequis_lus_dans_les_fiches_v2(tuteur):
    """nombres-premiers-decomposition (fiches-v2-demonstration) declare un prerequis."""
    prerequis = tuteur.module("figures")._prerequis("nombres-premiers-decomposition")
    assert prerequis == ["multiples-diviseurs-division-euclidienne"]


def test_schema_et_gabarit_une_seule_figure(tuteur):
    conv = _conv_notion(tuteur)
    texte = _bloc(f'{{"schema": "{PYTHAGORE}"}}') + "\n\n" + _bloc('{"gabarit": "droite-affine", "valeurs": {}}')
    sortie, ecartees = _filtrer_conv(tuteur, conv, texte)
    assert sortie.count("```figure") == 1 and SCHEMA_NORMALISE in sortie
    assert ecartees == [{"gabarit": "droite-affine", "raison": "une seule figure par message"}]


@pytest.mark.parametrize("mode", ["aide-devoirs", "reexplique"])
def test_contribution_schema_courte_sans_double_accolade(tuteur, mode):
    conv = _conv_notion(tuteur, mode)
    titre = tuteur.module("fiches_visuelles").fiches[PYTHAGORE].titre
    contribution = tuteur.module("figures").contribution(conv)
    assert f"Tu peux montrer le schéma de la notion « {titre} »" in contribution
    assert f'{{"schema": "{PYTHAGORE}"}}' in contribution
    assert "toujours accompagné de ton explication en mots" in contribution
    assert "}}" not in contribution and "{{" not in contribution
    systeme = tuteur.systeme(conv)
    assert "}}" not in systeme and "{{" not in systeme
    assert HORS_CONVERSATION not in contribution  # jamais les 410 ids : la notion et ses prerequis seulement


def test_sans_notion_pas_de_phrase_schema(tuteur):
    contribution = tuteur.module("figures").contribution(_conv_notion(tuteur, notion=None))
    assert "schéma de la notion" not in contribution and '"schema"' not in contribution


@pytest.mark.parametrize("mode", ["epreuve", "exercice", "controle"])
def test_mode_sans_figure_aucun_schema(tuteur, mode):
    conv = _conv_notion(tuteur, mode)
    figures = tuteur.module("figures")
    assert figures.schemas(conv) == {}
    assert figures.contribution(conv) == REGLE_DESSIN
    sortie, ecartees = _filtrer_conv(tuteur, conv, _bloc(f'{{"schema": "{PYTHAGORE}"}}'))
    assert "figure" not in sortie
    assert ecartees == [{"gabarit": f"schema:{PYTHAGORE}", "raison": "mode sans figure"}]


def test_reglage_schemas_desactivable(tuteur):
    figures = tuteur.module("figures")
    figures.reglages["schemas"] = False
    assert figures.schemas(_conv_notion(tuteur)) == {}


def test_texte_sans_figures_resume_le_schema():
    assert texte_sans_figures(f"Vois :\n{SCHEMA_NORMALISE}\nFin.") == f"Vois :\n[schéma : {PYTHAGORE}]\nFin."


# Schema de la bulle : largeur du svg et de la bulle, elements dessines, feuille, bouton Agrandir, debordement.
SCHEMA_MESURE = """(() => { const f = document.querySelector('.bulle-jules [data-schema-notion] .bloc-schema svg');
  if (!f) return null; const b = f.closest('.bulle-jules'); const z = f.closest('.bloc-schema');
  const bouton = b.querySelector('[data-schema-agrandir]');
  return {svg: f.getBoundingClientRect().width, bulle: b.getBoundingClientRect().width,
  elements: f.querySelectorAll('*').length, fond: getComputedStyle(z).backgroundColor,
  bouton: bouton ? bouton.getBoundingClientRect().width : 0,
  boutonFond: bouton ? getComputedStyle(bouton).backgroundColor : '',
  ecran: document.documentElement.scrollWidth}; })()"""


def _capture(page, nom: str) -> None:
    """Capture d'ecran si JULES_CAPTURES est defini (preuve visuelle a regarder, hors du depot)."""
    dossier = os.environ.get("JULES_CAPTURES")
    if not dossier:
        return
    Path(dossier).mkdir(parents=True, exist_ok=True)
    donnees = page.commande("Page.captureScreenshot", format="png")["data"]
    (Path(dossier) / nom).write_bytes(base64.b64decode(donnees))


def _ouvrir_app(page, url: str, sombre: bool, ancre: str) -> None:
    page.commande("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
    theme = "dark" if sombre else "light"
    page.commande("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": theme}])
    page.commande("Page.navigate", url=url + "/static/favicon.ico")
    time.sleep(0.5)
    page.evaluer(
        "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
        f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
    )
    page.commande("Page.navigate", url=url + "/app" + ancre)


@pytest.mark.parametrize("sombre", [False, True], ids=["clair", "sombre"])
def test_schema_dessine_dans_la_bulle_a_390px(serveur, tmp_path_factory, sombre):
    url, tuteur = serveur
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    tuteur.stockage.renommer(conv.id, "Schema de test")
    tuteur.stockage.ajouter_message(conv.id, Message(role="eleve", texte="Je comprends pas Pythagore"))
    texte = f"Regarde le schéma : les trois côtés.\n\n{SCHEMA_NORMALISE}\n\nLe plus long, c'est l'hypoténuse."
    tuteur.stockage.ajouter_message(conv.id, Message(role="bot", texte=texte))
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-schema"), (390, 844)) as page:
        _ouvrir_app(page, url, sombre, "#/discuter")
        bouton = "[...document.querySelectorAll('aside button')].find((b) => b.innerText.includes('Schema de test'))"
        page.attendre(f"!!{bouton}", delai=20)
        page.evaluer(f"{bouton}.click()")
        attente = f"(() => {{ const m = {SCHEMA_MESURE}; return m && m.elements ? m : null; }})()"
        mesure = page.attendre(attente, delai=15)
        assert mesure["elements"] >= 5
        assert 0 < mesure["svg"] <= mesure["bulle"]
        assert mesure["ecran"] <= 390  # aucun debordement horizontal
        assert mesure["fond"] not in ("rgba(0, 0, 0, 0)", "")  # feuille claire, dans les deux themes
        assert mesure["bouton"] > 0 and mesure["boutonFond"] != "rgba(0, 0, 0, 0)"  # « Agrandir » visible
        assert page.evaluer("document.documentElement.classList.contains('dark')") is sombre
        texte_bulle = page.evaluer("document.querySelector('.bulle-jules').innerText")
        assert "hypoténuse" in texte_bulle and '"schema"' not in texte_bulle  # le texte reste, le JSON non
        page.evaluer("document.querySelector('.bulle-jules [data-schema-notion]').scrollIntoView({block: 'center'})")
        time.sleep(0.8)
        _capture(page, f"schema-bulle-{'sombre' if sombre else 'clair'}.png")
        mesure_jeton = page.attendre(attente, delai=5)
        print("mesure bulle", "sombre" if sombre else "clair", mesure_jeton)


@pytest.mark.parametrize("sombre", [False, True], ids=["clair", "sombre"])
def test_schema_au_dessus_de_l_enonce_des_exercices_a_390px(serveur, tmp_path_factory, sombre):
    url, _ = serveur
    notion = "guerre-totale-1914-1918"  # fiche v2 servable sans IA + fiche visuelle avec un schema
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-schema-ex"), (390, 844)) as page:
        _ouvrir_app(page, url, sombre, f"#/fiche/{notion}")
        bouton_de = (
            "[...document.querySelectorAll('#bloc-entrainement button')].find((b) => b.innerText.includes('{}'))"
        )
        commencer = bouton_de.format("Commencer")
        page.attendre(f"!!{commencer}", delai=20)
        page.evaluer(f"{commencer}.scrollIntoView({{block: 'center'}}); {commencer}.click()")
        # 1er exercice « En quelle annee commence... ? » : la frise ecrit 1914, donc pas de schema (serveur).
        champ = "document.querySelector('#bloc-entrainement input')"
        page.attendre(f"!!{champ}", delai=10)
        assert page.evaluer("!document.querySelector('#bloc-entrainement [data-exercice-schema]')") is True
        page.evaluer(
            f"(() => {{ const c = {champ}; const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"
            " 'value').set; set.call(c, '1914'); c.dispatchEvent(new Event('input', {bubbles: true})); })()"
        )
        page.attendre(f"!!{bouton_de.format('Valider')} && !{bouton_de.format('Valider')}.disabled", delai=5)
        page.evaluer(f"{bouton_de.format('Valider')}.click()")
        page.attendre(f"!!{bouton_de.format('Exercice suivant')}", delai=10)
        page.evaluer(f"{bouton_de.format('Exercice suivant')}.click()")
        # 2e exercice (qui organise le genocide ?) : la reponse n'est pas sur le schema, il s'affiche.
        mesure = page.attendre(
            """(() => { const bloc = document.querySelector('#bloc-entrainement');
              const z = bloc.querySelector('[data-exercice-schema]');
              const s = z && z.querySelector('.bloc-schema svg'); if (!s) return null;
              const enonce = [...bloc.querySelectorAll('p')].find((p) => p.className.includes('text-[1.1rem]'));
              return {svg: s.getBoundingClientRect().width, bloc: bloc.getBoundingClientRect().width,
                avantEnonce: !!enonce && !!(z.compareDocumentPosition(enonce) & Node.DOCUMENT_POSITION_FOLLOWING),
                ecran: document.documentElement.scrollWidth}; })()""",
            delai=15,
        )
        assert 0 < mesure["svg"] <= mesure["bloc"]
        assert mesure["avantEnonce"] is True
        assert mesure["ecran"] <= 390
        page.evaluer("document.querySelector('[data-exercice-schema]').scrollIntoView({block: 'start'})")
        time.sleep(0.8)
        _capture(page, f"schema-exercice-{'sombre' if sombre else 'clair'}.png")
        # « Masquer le schéma » le replie (l'eleve garde la main) ; « Voir le schéma » le rouvre.
        page.evaluer("document.querySelector('[data-exercice-schema] button').click()")
        page.attendre("!document.querySelector('[data-exercice-schema] .bloc-schema')", delai=5)
        assert "Voir le schéma" in page.evaluer("document.querySelector('[data-exercice-schema] button').innerText")
