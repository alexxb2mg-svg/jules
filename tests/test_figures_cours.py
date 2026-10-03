"""Figures et schemas dans le mode COURS (panneau de Jules dans une lecon) ; jamais de dessin en caracteres.

Mesure du 03/10 (conversation de cours, lecon Thales) : sans figure proposee en mode cours, Jules repondait
« Je ne peux faire que des dessins en texte » et dessinait un triangle en ASCII. Desormais :
  - en cours, la notion de la lecon (module 'cours') donne son schema de fiche et les gabarits non `revele` ;
  - une figure ou un schema qui montrerait la reponse de l'exercice actif est ecarte ;
  - la regle « ne dessine jamais en caracteres » part dans le prompt de TOUS les modes ;
  - le panneau de la lecon dessine le bloc ```figure comme la bulle du chat (CDP, 390 et 1280 px).
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import pytest

from jules.lecons import Bloc
from jules.modules.cours import ESPACE
from jules.modules.figures import REGLE_DESSIN
from jules.stockage import Message
from tests.cdp import navigateur, navigateur_cdp
from tests.registre_figures import declarations_du_depot
from tests.test_figures_discussion import CODE, _bloc, _demarrer

THALES = "thales-triangles-semblables-trigonometrie"
FICHE_THALES = Path("bibliotheque/fiches-visuelles-3e-experimentales/fiches/mathematiques") / f"{THALES}.yaml"
# Schema de test (la fiche du depot n'en a pas ; celle de jules-bibliotheques, si) : triangle ABC, (MN) // (BC).
SVG_THALES = (
    '<svg viewBox="0 0 340 250" xmlns="http://www.w3.org/2000/svg">'
    '<polygon points="170,20 30,220 310,220" fill="none" stroke="#1f2937" stroke-width="2"/>'
    '<line x1="100" y1="120" x2="240" y2="120" stroke="#2563eb" stroke-width="3"/>'
    '<text x="170" y="14" text-anchor="middle" font-size="16">A</text>'
    '<text x="22" y="238" font-size="16">B</text><text x="312" y="238" font-size="16">C</text>'
    '<text x="84" y="124" font-size="16">M</text><text x="246" y="124" font-size="16">N</text>'
    '<text x="170" y="245" text-anchor="middle" font-size="13">(MN) parallèle à (BC)</text></svg>'
)
SCHEMA_THALES = f'```figure\n{{"schema":"{THALES}"}}\n```'
FIGURE_THALES = '```figure\n{"gabarit":"triangle-thales","valeurs":{"t":0.5}}\n```'


def _ajouter_schema_thales(projet: Path) -> None:
    """Ajoute un bloc `schema` a la fiche visuelle Thales de la copie jetable du projet."""
    fiche = projet / FICHE_THALES
    fiche.write_text(
        fiche.read_text(encoding="utf-8").rstrip()
        + '\n\n  - id: schema\n    type: schema\n    titre: "La configuration de Thalès"\n'
        + f"    svg: '{SVG_THALES}'\n    jules: \"(MN) est parallèle à (BC) : les rapports sont égaux.\"\n",
        encoding="utf-8",
    )


@pytest.fixture
def tuteur_thales(projet, brut_config):
    from jules.config import depuis_dict
    from jules.llm.factice import Brique as Factice
    from jules.moteur import Tuteur
    from tests.conftest import regle_par_defaut

    _ajouter_schema_thales(projet)
    llm = Factice()
    llm.regle = regle_par_defaut
    t = Tuteur(depuis_dict(brut_config, projet), llm=llm)
    yield t
    t.fermer()


def _conv_lecon(tuteur):
    ouverte = tuteur.module("cours").ouvrir(THALES)
    return tuteur.stockage.conversation(ouverte["conversation"]), ouverte["session"]


def _ecartees(tuteur) -> list[dict]:
    return [
        {k: v for k, v in e["donnees"].items() if k != "source"} for e in tuteur.stockage.evenements("figure_ecartee")
    ]


def test_cours_lecon_thales_schema_et_gabarits_non_revele(tuteur_thales):
    figures = tuteur_thales.module("figures")
    conv, _ = _conv_lecon(tuteur_thales)
    assert conv.mode == "cours"
    assert tuteur_thales.module("notions").etat(conv.id).get("notion") is None  # la notion vient de la lecon
    assert THALES in figures.schemas(conv)
    autorises = figures.autorises(conv)
    assert "triangle-thales" in autorises
    assert "equation-solutions" not in autorises  # revele : jamais en cours
    assert "triangle-rectangle" in autorises  # plus revele depuis la version 2.0 (AB n'est plus ecrit)
    contribution = figures.contribution(conv)
    assert "Tu peux montrer le schéma de la notion" in contribution and "- triangle-thales :" in contribution
    assert "}}" not in tuteur_thales.systeme(conv)


def test_cours_propose_tous_les_gabarits_non_revele_et_aucun_revele(tuteur_thales):
    """Registre LU dans extensions/*/extension.yaml (tests/registre_figures.py) : en cours, exactement les
    gabarits sans `revele`, quel que soit leur nombre (plus de liste a tenir a jour ici)."""
    figures = tuteur_thales.module("figures")
    conv, _ = _conv_lecon(tuteur_thales)
    declarations = declarations_du_depot()
    attendus = {g for g, (revele, _) in declarations.items() if not revele}
    assert attendus and attendus != set(declarations)  # il y a des deux sortes : sinon le test ne prouve rien
    assert set(figures.autorises(conv)) == attendus
    contribution = figures.contribution(conv)
    for gabarit in declarations:
        assert (f"- {gabarit} :" in contribution) is (gabarit in attendus), gabarit


def test_cours_filtre_schema_gabarit_et_revele(tuteur_thales):
    figures = tuteur_thales.module("figures")
    conv, _ = _conv_lecon(tuteur_thales)
    sortie = figures.filtrer_reponse(conv, _bloc(f'{{"schema": "{THALES}"}}'), lambda: "relance interdite")
    assert SCHEMA_THALES in sortie
    sortie = figures.filtrer_reponse(conv, _bloc('{"gabarit": "triangle-thales", "valeurs": {}}'), lambda: "")
    assert FIGURE_THALES in sortie
    sortie = figures.filtrer_reponse(conv, _bloc('{"gabarit": "equation-solutions", "valeurs": {}}'), lambda: "")
    assert "```figure" not in sortie
    assert _ecartees(tuteur_thales) == [{"gabarit": "equation-solutions", "raison": "gabarit non autorise"}]


def test_cours_figure_ou_schema_qui_donnerait_la_reponse_ecarte(tuteur_thales, monkeypatch):
    """Exercice actif de la lecon : un schema dont les textes donnent la reponse n'est pas propose ; une figure
    dont les valeurs (completees apres le filtre de 'cours') donnent la reponse est retiree."""
    figures = tuteur_thales.module("figures")
    cours = tuteur_thales.module("cours")
    conv, session = _conv_lecon(tuteur_thales)
    lecon = cours.lecons[THALES]
    index = next(i for i, b in enumerate(lecon.blocs) if b.type == "exercice")  # AC = ? reponse 7.5
    etat = tuteur_thales.stockage.lire_etat(ESPACE, session)
    etat["bloc_actif"] = index
    tuteur_thales.stockage.ecrire_etat(ESPACE, session, etat)
    assert cours.bloc_protege(conv) is lecon.blocs[index]
    assert THALES in figures.schemas(conv)  # le schema n'ecrit aucune longueur
    fiches = tuteur_thales.module("fiches_visuelles")
    monkeypatch.setattr(fiches, "texte_schema", lambda notion: "AC = 7,5 cm")
    assert THALES not in figures.schemas(conv)

    monkeypatch.setattr(cours, "bloc_protege", lambda c: Bloc("exercice", {"forme": "nombre", "reponse": 0.5}))
    sortie = figures.filtrer_reponse(conv, _bloc('{"gabarit": "triangle-thales", "valeurs": {}}'), lambda: "")
    assert "```figure" not in sortie  # t = 0.5 par defaut : la reponse
    assert _ecartees(tuteur_thales)[0] == {"gabarit": "triangle-thales", "raison": "revelerait la reponse"}
    sortie = figures.filtrer_reponse(conv, _bloc('{"gabarit": "triangle-thales", "valeurs": {"t": 0.3}}'), lambda: "")
    assert "```figure" in sortie


def test_cours_garde_fou_puis_figures_de_bout_en_bout(tuteur_thales):
    """Le filtre de 'cours' (avant 'figures') relance si la reponse fuit ; la relance passe encore par 'figures'."""
    cours = tuteur_thales.module("cours")
    conv, session = _conv_lecon(tuteur_thales)
    index = next(i for i, b in enumerate(cours.lecons[THALES].blocs) if b.type == "exercice")
    etat = tuteur_thales.stockage.lire_etat(ESPACE, session)
    etat["bloc_actif"] = index
    tuteur_thales.stockage.ecrire_etat(ESPACE, session, etat)
    reponses = iter(
        [
            "AC = 7,5 cm.\n\n" + _bloc('{"gabarit": "triangle-thales", "valeurs": {"t": 0.4}}'),
            "Quel rapport connais-tu ?\n\n" + _bloc('{"gabarit": "equation-solutions", "valeurs": {}}'),
        ]
    )
    tuteur_thales.llm.regle = lambda s, t, m: next(reponses) if "Leçon en cours" in s else "Réponse factice."
    bot = tuteur_thales.echanger(conv.id, "montre moi avec une illustration")
    assert "7,5" not in bot.texte and "Quel rapport" in bot.texte
    assert "```figure" not in bot.texte  # equation-solutions (revele) retire meme apres la relance
    assert any(REGLE_DESSIN in a["systeme"] for a in tuteur_thales.llm.appels)


@pytest.mark.parametrize("mode", ["cours", "epreuve", "aide-devoirs", "exercice"])
def test_regle_jamais_de_dessin_en_caracteres_dans_tous_les_modes(tuteur, mode):
    conv = tuteur.stockage.creer_conversation(mode)
    systeme = tuteur.systeme(conv)
    assert REGLE_DESSIN in systeme
    assert "Ne dessine jamais en caractères (traits, barres, schéma ASCII)" in systeme
    assert "}}" not in systeme and "{{" not in systeme


# --- rendu dans le panneau de la lecon (Chromium, tests/cdp.py) ----------------------------------------------------


@pytest.fixture
def serveur_lecon(projet, brut_config):
    _ajouter_schema_thales(projet)
    yield from _demarrer(projet, brut_config)


PANNEAU = "document.querySelector('[data-panneau-jules]')"
MESURE = f"""(() => {{ const p = {PANNEAU}; if (!p) return null;
  const schema = p.querySelector('.bulle-jules [data-schema-notion] .bloc-schema svg');
  const figure = p.querySelector('.bulle-jules [data-figure-bulle] svg');
  const curseur = p.querySelector('[data-figure-bulle] input[type=range]');
  if (!schema || !figure || !curseur) return null;
  const P = p.getBoundingClientRect(), bulle = figure.closest('.bulle-jules').getBoundingClientRect();
  const r = (e) => e.getBoundingClientRect();
  return {{panneau: P.width, bulle: bulle.width, schema: r(schema).width, figure: r(figure).width,
    dedans: [schema, figure, figure.closest('.bulle-jules')].every((e) => r(e).left >= P.left - 0.5
      && r(e).right <= P.right + 0.5),
    t: curseur.getAttribute('aria-valuetext'), elements: schema.querySelectorAll('*').length,
    debord: document.scrollingElement.scrollWidth - innerWidth,
    texte: p.querySelector('.bulle-jules').innerText}}; }})()"""


def _capture(page, nom: str) -> None:
    dossier = os.environ.get("JULES_CAPTURES")
    if dossier:
        Path(dossier).mkdir(parents=True, exist_ok=True)
        (Path(dossier) / nom).write_bytes(base64.b64decode(page.commande("Page.captureScreenshot")["data"]))


@pytest.mark.parametrize("largeur", [390, 1280], ids=["telephone", "ordinateur"])
@pytest.mark.parametrize("sombre", [False, True], ids=["clair", "sombre"])
def test_schema_et_figure_dans_le_panneau_de_la_lecon(serveur_lecon, tmp_path_factory, largeur, sombre):
    url, tuteur = serveur_lecon
    conv_id = tuteur.module("cours").ouvrir(THALES)["conversation"]
    tuteur.stockage.ajouter_message(conv_id, Message(role="eleve", texte="montre moi avec une illustration"))
    texte = (
        f"Regarde le schéma de la leçon :\n\n{SCHEMA_THALES}\n\nEt fais bouger M sur [AB] :\n\n{FIGURE_THALES}\n\n"
        "Que remarques-tu sur les rapports AM/AB et AN/AC ?"
    )
    tuteur.stockage.ajouter_message(conv_id, Message(role="bot", texte=texte))
    mobile = largeur < 768
    theme = "sombre" if sombre else "clair"
    with navigateur_cdp(navigateur(), tmp_path_factory.mktemp("chromium-lecon"), (largeur, 900)) as page:
        page.commande(
            "Emulation.setDeviceMetricsOverride",
            width=largeur,
            height=844 if mobile else 900,
            deviceScaleFactor=2 if mobile else 1,
            mobile=mobile,
        )
        page.commande(
            "Emulation.setEmulatedMedia",
            features=[{"name": "prefers-color-scheme", "value": "dark" if sombre else "light"}],
        )
        page.commande("Page.navigate", url=url + "/static/favicon.ico")
        time.sleep(0.5)
        page.evaluer(
            "fetch('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'},"
            f" body: JSON.stringify({{code: '{CODE}'}})}}).then((r) => r.status)"
        )
        page.commande("Page.navigate", url=url + f"/app#/lecon/{THALES}")
        if mobile:
            bouton = "document.querySelector('button[aria-label=\"Demander à Jules\"]')"
            page.attendre(f"!!{bouton}", delai=20)
            page.evaluer(f"{bouton}.click()")
        mesure = page.attendre(MESURE, delai=20)
        assert page.evaluer("document.documentElement.classList.contains('dark')") is sombre
        assert mesure["elements"] >= 5 and mesure["t"] == "t = 0,5"
        assert 0 < mesure["schema"] <= mesure["panneau"] and 0 < mesure["figure"] <= mesure["panneau"], mesure
        assert mesure["dedans"] and mesure["debord"] <= 0, mesure
        assert mesure["figure"] >= 200, mesure  # la figure garde une taille lisible dans le panneau
        assert '"gabarit"' not in mesure["texte"] and "Que remarques-tu" in mesure["texte"]  # pas de JSON visible

        page.evaluer(f"{PANNEAU}.querySelector('.bulle-jules [data-schema-notion]').scrollIntoView({{block: 'start'}})")
        time.sleep(0.8)
        _capture(page, f"cours-{largeur}-{theme}-schema.png")
        # Curseur t : clavier (fleche droite, pas 0,1) -> t = 0,6
        page.evaluer(f"{PANNEAU}.querySelector('[data-figure-bulle] input[type=range]').focus()")
        page.touche("ArrowRight", "ArrowRight", 39)
        apres = page.attendre(f"(() => {{ const m = {MESURE}; return m && m.t !== 't = 0,5' ? m : null; }})()", delai=5)
        assert apres["t"] == "t = 0,6"
        page.evaluer(f"{PANNEAU}.querySelector('[data-figure-bulle]').scrollIntoView({{block: 'center'}})")
        time.sleep(0.6)
        _capture(page, f"cours-{largeur}-{theme}-figure.png")
        print("mesure panneau", largeur, theme, mesure)
