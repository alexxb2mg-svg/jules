"""Typographie des titres dans la barre (regression #46 reperee a la revue de la PR #47).

#46 a introduit `typo()` : l'espace devant « ? ! : ; » et apres « « » devient une espace fine insecable (U+202F),
pour qu'un signe ne commence jamais une ligne. Les titres affiches dans l'ancienne liste de l'accueil y passaient.
La barre (N2 a N8), seule liste restante, affiche des titres entiers sur plusieurs lignes (EX-212, EX-216) : elle
doit appliquer la meme regle a ses titres de page, de chapitre et de notion. `typo()` est desormais `MS.typo`
(commun.js), partagee par l'accueil et la barre.

Mesure dans Chromium (banc de tests/nav_scenario.py) sur le referentiel reel, matiere arts plastiques : chapitre
« La representation ; images, realite et fiction », notions « S'exprimer, analyser sa pratique ... ; ... ».
"""

from __future__ import annotations

import json
import re

import pytest

from jules.web.app import STATIQUE, creer_app
from tests.nav_scenario import banc_navigation
from tests.test_navigation import ATTENDRE_BARRE, _tuteur

MATIERE = "arts-plastiques"
CHAPITRE = "La représentation ; images, réalité et fiction"
FINE = "\u202f"
# Espace ordinaire (ou insecable U+00A0) devant une ponctuation haute, ou apres « : ce que typo() interdit.
MAUVAISE_ESPACE = r"[ \u00a0][?!:;»]|«[ \u00a0]"


@pytest.fixture(scope="module")
def banc_typo(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory, None)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-typo")) as b:
            yield b
    finally:
        tuteur.fermer()


# Exercices > Arts plastiques (etape 4 : intertitres de chapitre + notions), puis Mes fiches > Arts plastiques
# (etape 3 : boutons de chapitre).
SCENARIO = (
    ATTENDRE_BARRE
    + """
  const B = () => S.el("#barre-jules");
  const textes = (sel) => [...B().querySelectorAll(sel)].map((e) => e.textContent);
  const ouvrir = async (rubrique) => {
    const bouton = [...B().querySelectorAll("button")].find((b) => b.textContent.includes(rubrique));
    bouton.click();
    const sel = "[data-matiere='" + MATIERE + "']";
    await S.attendre(() => B().querySelector(sel), 8000);
    B().querySelector(sel).click();
    await S.pause(300);
  };
  // Exercices : toutes les notions de la matiere, avec ou sans lecon (Mes leçons n'en montre aucune en arts
  // plastiques, faute de lecon).
  await ouvrir("Exercices");
  const etape4 = {
    page: S.el("#barre-page-titre").textContent,
    intertitres: textes(".barre-intertitre .barre-libelle"),
    notions: textes(".barre-element .barre-libelle"),
    titles: [...B().querySelectorAll(".barre-intertitre")].map((e) => e.title),
  };
  return { etape4 };
""".replace("MATIERE", json.dumps(MATIERE))
)


# Mes fiches > Mathematiques (etape 3 : boutons de chapitre). Le jeu de test n'a de fiches qu'en mathematiques,
# sans ponctuation haute dans les chapitres : la reponse de l'API est servie modifiee (un chapitre avec « : » et « ; »).
CHAPITRE_FICHES = "Géométrie plane : démonstration ; essai"
SCENARIO_FICHES = (
    ATTENDRE_BARRE
    + """
  const B = () => S.el("#barre-jules");
  [...B().querySelectorAll("button")].find((b) => b.textContent.includes("Mes fiches")).click();
  await S.attendre(() => B().querySelector("[data-matiere='mathematiques'], [data-chapitre]"), 8000);
  const m = B().querySelector("[data-matiere='mathematiques']");
  if (m) m.click();
  await S.attendre(() => B().querySelector("[data-chapitre]"), 8000);
  return {
    chapitres: [...B().querySelectorAll(".barre-chapitre .barre-libelle")].map((e) => e.textContent),
    donnees: [...B().querySelectorAll("[data-chapitre]")].map((b) => b.dataset.chapitre),
  };
"""
)


def _fiches_modifiees(banc) -> str:
    import urllib.request

    with urllib.request.urlopen(banc.url + "/api/eleve/fiches_visuelles/notions") as r:  # noqa: S310 - banc local
        donnees = json.loads(r.read().decode("utf-8"))
    notions = [n for m in donnees["matieres"] for n in m["notions"]]
    notions[0]["chapitre"] = CHAPITRE_FICHES
    return json.dumps(donnees, ensure_ascii=False)


def _mal_espaces(textes: list[str]) -> list[str]:
    return [t for t in textes if re.search(MAUVAISE_ESPACE, t)]


def test_typo_des_titres_dans_la_barre(banc_typo):
    r = banc_typo.jouer("/studio", SCENARIO, taille=(1280, 800), budget_ms=15000)
    e4 = r["etape4"]
    # Le cas vise est bien servi (sinon le test ne prouverait rien).
    assert CHAPITRE.replace(" ;", FINE + ";") in e4["intertitres"], e4["intertitres"]
    assert any(FINE + ";" in n for n in e4["notions"]), e4["notions"][:5]
    # Aucune espace ordinaire devant ; : ? ! » (ni apres «) dans les libelles affiches.
    for nom, liste in (("intertitres", e4["intertitres"]), ("notions", e4["notions"])):
        assert _mal_espaces(liste) == [], (nom, _mal_espaces(liste)[:3])
    assert not re.search(MAUVAISE_ESPACE, e4["page"]), e4["page"]
    # L'info-bulle garde le texte d'origine : la typo n'est qu'affichage.
    assert CHAPITRE in e4["titles"]


def test_typo_des_boutons_de_chapitre(banc_typo):
    api = "/api/eleve/fiches_visuelles/notions"
    r = banc_typo.jouer(
        "/cours", SCENARIO_FICHES, taille=(1280, 800), remplaces={api: _fiches_modifiees(banc_typo)}, budget_ms=15000
    )
    assert CHAPITRE_FICHES.replace(" :", FINE + ":").replace(" ;", FINE + ";") in r["chapitres"], r
    assert _mal_espaces(r["chapitres"]) == [], r
    assert CHAPITRE_FICHES in r["donnees"], r  # la cle de chapitre reste le texte d'origine


def test_typo_temoin_sans_ms_typo_le_test_echoue(banc_typo):
    """Mutation : navigation.js servi sans MS.typo -> les titres gardent l'espace ordinaire devant « ; »."""
    js = (STATIQUE / "navigation.js").read_text(encoding="utf-8")
    assert js.count("MS.typo(") >= 4
    mute = js.replace("MS.typo(", "String(")
    remplaces = {"/static/navigation.js": mute}
    r = banc_typo.jouer("/studio", SCENARIO, taille=(1280, 800), remplaces=remplaces, budget_ms=15000)
    assert CHAPITRE in r["etape4"]["intertitres"]
    assert _mal_espaces(r["etape4"]["intertitres"])


def test_typo_une_seule_definition():
    """typo() est definie une fois (MS.typo dans commun.js) ; accueil.js et navigation.js l'utilisent."""
    commun = (STATIQUE / "commun.js").read_text(encoding="utf-8")
    assert re.search(r"^\s*typo\(texte\) \{", commun, re.M)
    accueil = (STATIQUE / "accueil.js").read_text(encoding="utf-8")
    assert "const typo = (texte) => MS.typo(texte);" in accueil
    assert len(re.findall(r"typo\s*[=(]\s*\(?texte\)?\s*(=>|\{)", accueil + commun)) == 2  # alias + definition
