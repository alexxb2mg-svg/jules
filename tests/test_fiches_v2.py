"""Fiches v2 : correction sans IA, contrat, signature, parcours d'exercice, et les deux fiches de demonstration."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from jules.bibliotheques import charger_catalogue, texte_fiche
from jules.fiches.commande import fiches_v2, signer_dossiers, verifier
from jules.fiches.correction import (
    ILLISIBLE,
    ReponseIllisible,
    corriger,
    decomposer,
    est_premier,
    lire_expression,
    lire_nombre,
    lire_produit,
    reponse_de_reference,
)
from jules.fiches.parcours import Etat, aide_format, choisir, presenter, repondre
from jules.fiches.schema import collisions, empreinte, servable_sans_ia, signer, verifier_fiche

RACINE = Path(__file__).resolve().parents[1]
BIBLIOTHEQUES = RACINE / "bibliotheque"
DEMO = BIBLIOTHEQUES / "fiches-v2-demonstration"


def charger(nom: str) -> dict:
    chemin = next((DEMO / "fiches").rglob(f"{nom}.yaml"))
    return yaml.safe_load(chemin.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def notions() -> set[str]:
    return set(charger_catalogue(BIBLIOTHEQUES, ["programme"], None).notions)


@pytest.fixture
def maths() -> dict:
    return charger("nombres-premiers-decomposition")


@pytest.fixture
def histoire() -> dict:
    return charger("guerre-totale-1914-1918")


def exo(fiche: dict, identifiant: str) -> dict:
    return next(e for e in fiche["exercices"] if e["id"] == identifiant)


# --- lecture des reponses -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texte", "attendu"),
    [
        ("7/10", "7/10"),
        ("7 / 10", "7/10"),
        ("0,7", "7/10"),
        ("1 848", "1848"),
        ("252/360 = 7/10", "7/10"),
        ("en 1914", "1914"),
        ("c'est 7/10 !", "7/10"),
        ("−3", "-3"),
        # unite recopiee apres le nombre : elle ne change pas la valeur (le % non plus, comme dans les enonces)
        ("42 €", "42"),
        ("27,5 %", "55/2"),
        ("12 cm²", "12"),
        ("20 m/s", "20"),
        ("30 km/h", "30"),
        ("65°", "65"),
        ("6,5 kWh", "13/2"),
        # notation scientifique et puissances de 10
        ("7,2 × 10^-4", "9/12500"),
        ("7.2*10^(-4)", "9/12500"),
        ("7,2 × 10⁻⁴", "9/12500"),
        ("3 x 10⁵", "300000"),
        ("10⁻³", "1/1000"),
    ],
)
def test_lire_nombre(texte, attendu):
    from fractions import Fraction

    assert lire_nombre(texte) == Fraction(attendu)


@pytest.mark.parametrize("texte", ["quatorze", "1914 ou 1918", "3/0", "", "2 + 3", "5 fois 3", "10^999", "12 3"])
def test_nombre_illisible(texte):
    with pytest.raises(ReponseIllisible):
        lire_nombre(texte)


def test_produit_et_premiers():
    assert lire_produit("2^3 x 3² * 5") == [(2, 3), (3, 2), (5, 1)]
    assert lire_produit("2 × 2 × 2 × 3 × 3 × 5") == [(2, 1)] * 3 + [(3, 1)] * 2 + [(5, 1)]  # lu tel qu'ecrit
    assert decomposer(1848) == [(2, 3), (3, 1), (7, 1), (11, 1)]
    assert [n for n in range(30) if est_premier(n)] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    with pytest.raises(ReponseIllisible):
        lire_produit("2^999999")  # un exposant demesure est refuse, pas calcule


@pytest.mark.parametrize("texte", ["__import__('os')", "x.real", "[x]", "x if x else 1", "y + 1", "a" * 400])
def test_expression_refuse_ce_qui_n_est_pas_un_calcul(texte):
    with pytest.raises(ReponseIllisible):
        lire_expression(texte, ["x"])


@pytest.mark.parametrize("texte", ["9^9^9", "((10^64)^64)^64", "(x^64)^64^64"])
def test_expression_geante_refusee_sans_etre_calculee(texte):
    exercice = {"type": "expression", "reponse": {"valeur": "x^2", "variables": ["x"]}}
    assert corriger(exercice, texte).diagnostic == ILLISIBLE


# --- correction, type par type ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("reponse", "juste", "diagnostic"),
    [
        ("2^3 x 3^2 x 5", True, ""),
        ("2³×3²×5", True, ""),
        ("2*2*2*3*3*5", True, ""),
        ("8 × 45", False, "facteur_non_premier"),
        ("2^3*3*5", False, "produit_faux"),
        ("bof", False, ILLISIBLE),
    ],
)
def test_corriger_produit_premiers(maths, reponse, juste, diagnostic):
    verdict = corriger(exo(maths, "decomposer-360"), reponse)
    assert (verdict.juste, verdict.diagnostic) == (juste, diagnostic)


@pytest.mark.parametrize(
    ("reponse", "juste", "diagnostic"),
    [
        ("7/10", True, ""),
        ("14/20", False, "non_irreductible"),
        ("0,7", False, "pas_une_fraction"),
        ("3/4", False, "valeur_fausse"),
    ],
)
def test_corriger_fraction(maths, reponse, juste, diagnostic):
    verdict = corriger(exo(maths, "irreductible-252-360"), reponse)
    assert (verdict.juste, verdict.diagnostic) == (juste, diagnostic)


def test_corriger_expression():
    exercice = {
        "type": "expression",
        "reponse": {"valeur": "(x+3)(x-3)", "variables": ["x"], "forme": "factorisee"},
    }
    assert corriger(exercice, "(x-3)(x+3)").juste
    assert corriger(exercice, "(x - 3) × (x + 3)").juste
    developpe = corriger(exercice, "x^2 - 9")
    assert not developpe.juste and developpe.partiel and developpe.diagnostic == "pas_factorisee"
    assert corriger(exercice, "(x+3)^2").diagnostic == "non_equivalente"
    exercice["reponse"] = {"valeur": "2x^2 + 3x", "variables": ["x"], "forme": "developpee"}
    assert corriger(exercice, "3x + 2x²").juste
    assert corriger(exercice, "x(2x+3)").diagnostic == "pas_developpee"


def test_factorisation_incomplete():
    exercice = {"type": "expression", "reponse": {"valeur": "x(x-2)(x+2)", "forme": "factorisee"}}
    assert corriger(exercice, "x(x - 2)(x + 2)").juste
    assert corriger(exercice, "-x(2 - x)(x + 2)").juste
    for incomplet in ("x(x² - 4)", "(x² - 2x)(x + 2)"):
        verdict = corriger(exercice, incomplet)
        assert not verdict.juste and verdict.partiel and verdict.diagnostic == "factorisation_incomplete"
    assert corriger(exercice, "x³ - 4x").diagnostic == "pas_factorisee"
    # un facteur numerique non sorti n'est pas une factorisation incomplete au sens du college
    exercice["reponse"] = {"valeur": "4(x + 2)(x + 1)", "forme": "factorisee"}
    assert corriger(exercice, "(x + 2)(4x + 4)").juste
    exercice["reponse"] = {"valeur": "(x - 3)^2", "forme": "factorisee"}
    assert corriger(exercice, "(x - 3)(x - 3)").juste


def test_notation_scientifique():
    exercice = {"type": "nombre", "reponse": {"valeur": 0.00072, "forme": "scientifique"}}
    assert corriger(exercice, "7,2 × 10^-4").juste
    assert corriger(exercice, "7,2 × 10⁻⁴").juste
    for mal_ecrit in ("0,00072", "72 × 10^-5"):
        verdict = corriger(exercice, mal_ecrit)
        assert not verdict.juste and verdict.partiel and verdict.diagnostic == "pas_scientifique"
    assert corriger(exercice, "7,2 × 10^-3").diagnostic == "valeur_fausse"
    assert reponse_de_reference(exercice) == "7,2 × 10^-4"
    assert aide_format(exercice).startswith("Écris le nombre en notation scientifique")


def test_une_fuite_en_notation_scientifique_est_vue(maths, notions):
    fiche = copy.deepcopy(maths)
    ex = fiche["exercices"][0]
    ex.update(
        type="nombre",
        reponse={"valeur": 500, "forme": "libre"},
        indices={"relance": "Quelle opération ?", "methode": "Divise.", "etape": "Écris 0,5 × 10³ en décimal."},
    )
    ex.pop("pieges", None)
    assert any("contient la reponse" in e for e in verifier_fiche(fiche, notions, controler_empreinte=False))


def test_corriger_choix_texte_ordre_association(maths, histoire):
    choix = exo(maths, "lesquels-sont-premiers")
    assert corriger(choix, ["b", "d"]).juste
    assert corriger(choix, "97 et 53").juste  # l'eleve peut ecrire les textes des options
    assert corriger(choix, ["b"]).diagnostic == "incomplet"
    assert corriger(choix, ["a", "b", "d"]).diagnostic == "mauvais_choix"
    mot = exo(histoire, "mot-genocide")
    assert corriger(mot, "Génocide").juste and corriger(mot, "genocide").juste
    faute = corriger(mot, "génocyde")
    assert faute.juste and faute.diagnostic == "orthographe"
    assert not corriger(mot, "massacre").juste
    ordre = exo(histoire, "chronologie")
    assert corriger(ordre, ["entree", "genocide", "bolcheviks", "armistice"]).juste
    assert corriger(ordre, ["entree", "bolcheviks", "genocide", "armistice"]).diagnostic == "inversion_voisine"
    assert corriger(ordre, "1 2 3").diagnostic == ILLISIBLE
    camps = exo(histoire, "camps")
    assert corriger(camps, {"a": "x", "b": "y", "c": "x", "d": "y", "e": "y"}).juste
    assert corriger(camps, "a-x, b-y, c-x, d-y, e-x").diagnostic == "une_erreur"


def test_ouverte_jamais_corrigee_par_le_code(histoire):
    verdict = corriger(exo(histoire, "developpement-guerre-totale"), "n'importe quoi")
    assert not verdict.auto and not verdict.juste


# --- le contrat -----------------------------------------------------------------------------


def test_fiches_de_demonstration_conformes_et_signees(notions):
    fiches = fiches_v2(DEMO)
    assert len(fiches) == 2
    for chemin, fiche in fiches.items():
        assert verifier_fiche(fiche, notions) == [], chemin.name
        assert chemin.stem == fiche["notion"]
        assert servable_sans_ia(fiche), f"{chemin.name} : a re-signer (`jules fiches signer`)"
    assert collisions({f["notion"]: f for f in fiches.values()}) == {}


MUTATIONS = [
    ("champ inconnu", lambda f: f.__setitem__("bonus", 1), "champ(s) inconnu(s)"),
    ("reponse fausse", lambda f: exo(f, "decomposer-360")["reponse"].__setitem__("valeur", 361), "n'aboutit pas"),
    (
        "indice qui donne la reponse",
        lambda f: exo(f, "decomposer-360")["indices"].__setitem__("etape", "Tu dois trouver 2 × 2 × 2 × 3² × 5."),
        "contient la reponse",
    ),
    (
        "relance qui donne la reponse",
        lambda f: exo(f, "irreductible-252-360")["pieges"][0].__setitem__("relance", "Non, c'est 7/10."),
        "relance contient la reponse",
    ),
    (
        "piege = bonne reponse",
        lambda f: exo(f, "un-est-il-premier")["pieges"][0]["si"].__setitem__("valeur", "non"),
        "bonne reponse",
    ),
    ("prerequis inconnu", lambda f: f.__setitem__("prerequis", ["notion-bidon"]), "inconnu du referentiel"),
    ("prerequis circulaire", lambda f: f.__setitem__("prerequis", [f["notion"]]), "son propre prerequis"),
    ("palier manquant", lambda f: exo(f, "decomposer-360")["indices"].pop("methode"), "exactement relance"),
    ("id en double", lambda f: exo(f, "decomposer-360").__setitem__("id", "un-est-il-premier"), "en double"),
    (
        "bonne option absente",
        lambda f: exo(f, "lesquels-sont-premiers")["reponse"].__setitem__("bonnes", ["z"]),
        "`bonnes`",
    ),
    ("licence non libre", lambda f: f["sources"][0].__setitem__("licence", "CC-BY-NC-4.0"), "non reconnue"),
    ("contenu modifie apres signature", lambda f: f.__setitem__("essentiel", "autre"), "empreinte"),
    ("declencheur muet", lambda f: f["declencheurs"].append("de la"), "invisible"),
    ("difficulte hors echelle", lambda f: exo(f, "decomposer-360").__setitem__("difficulte", 5), "difficulte"),
    (
        "diagnostic impossible",
        lambda f: exo(f, "decomposer-360")["pieges"][0]["si"].__setitem__("diagnostic", "incomplet"),
        "impossible",
    ),
    (
        "trop peu d'exercices sans IA",
        lambda f: f.__setitem__("exercices", [e for e in f["exercices"] if e["type"] == "ouverte"]),
        "au moins 3",
    ),
    ("relue sans relecteur", lambda f: f["relecture"].__setitem__("statut", "relue"), "par qui"),
]


@pytest.mark.parametrize(("nom", "mutation", "attendu"), MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_le_verificateur_attrape_chaque_defaut(maths, notions, nom, mutation, attendu):
    fiche = copy.deepcopy(maths)
    mutation(fiche)
    erreurs = verifier_fiche(fiche, notions)
    assert any(attendu in e for e in erreurs), (nom, erreurs)


def test_piege_masque_par_un_autre(histoire, notions):
    exo(histoire, "annee-debut")["pieges"].append({"si": {"valeur": "1918"}, "relance": "Doublon."})
    assert any("jamais dit" in e for e in verifier_fiche(histoire, notions, controler_empreinte=False))


def test_collisions_de_declencheurs(maths, histoire):
    histoire["declencheurs"].append("Nombres premiers")
    assert collisions({"a": maths, "b": histoire}) == {"nombres premiers": {"a", "b"}}


# --- la signature -----------------------------------------------------------------------------


def test_signature_et_nouvelle_version(maths, notions):
    assert servable_sans_ia(maths)
    modifiee = copy.deepcopy(maths)
    modifiee["essentiel"] += "\nUne phrase de plus."
    assert not servable_sans_ia(modifiee)  # plus servie sans IA tant qu'on n'a pas re-verifie
    signee, erreurs = signer(modifiee, notions)
    assert erreurs == [] and signee["version"] == maths["version"] + 1 and servable_sans_ia(signee)
    relue = copy.deepcopy(signee)
    relue["relecture"] = {"statut": "relue", "par": "professeur de mathématiques", "le": "2026-10-01"}
    relue, _ = signer(relue, notions)
    assert relue["etat"] == "relue"
    relue["methode"].append("Encore une étape.")
    reprise, _ = signer(relue, notions)
    # la relecture portait sur l'ancien contenu : elle est a refaire
    assert reprise["etat"] == "verifiee" and reprise["relecture"]["statut"] == "a_relire"


def test_empreinte_ignore_etat_et_relecture(maths):
    autre = copy.deepcopy(maths)
    autre["etat"] = "relue"
    autre["relecture"] = {"statut": "relue", "par": "x", "le": "2026-10-01"}
    assert empreinte(autre) == empreinte(maths)


def test_commande_verifier_et_signer(tmp_path, maths, capsys):
    dossier = tmp_path / "biblio"
    (dossier / "fiches" / "mathematiques").mkdir(parents=True)
    brouillon = copy.deepcopy(maths)
    brouillon.update(etat="generee", version=1)
    brouillon.pop("empreinte")
    chemin = dossier / "fiches" / "mathematiques" / "nombres-premiers-decomposition.yaml"
    chemin.write_text(yaml.safe_dump(brouillon, allow_unicode=True), encoding="utf-8")
    assert verifier(BIBLIOTHEQUES, [dossier]) == 0
    assert signer_dossiers(BIBLIOTHEQUES, [dossier]) == 0
    assert servable_sans_ia(yaml.safe_load(chemin.read_text(encoding="utf-8")))
    exo(brouillon, "decomposer-360")["indices"]["etape"] = "C'est 2³ × 3² × 5."
    chemin.write_text(yaml.safe_dump(brouillon, allow_unicode=True), encoding="utf-8")
    assert verifier(BIBLIOTHEQUES, [dossier]) == 1
    assert signer_dossiers(BIBLIOTHEQUES, [dossier]) == 1
    assert "contient la reponse" in capsys.readouterr().out


# --- le parcours sans IA ------------------------------------------------------------------------


def test_presentation_ne_montre_jamais_la_reponse(maths, histoire):
    for fiche in (maths, histoire):
        for ex in fiche["exercices"]:
            vue = presenter(ex)
            assert "solution" not in vue and "reponse" not in vue and "indices" not in vue and "pieges" not in vue
    vue = presenter(exo(histoire, "chronologie"))
    bon_ordre = [e["id"] for e in exo(histoire, "chronologie")["reponse"]["elements"]]
    assert [e["id"] for e in vue["elements"]] != bon_ordre
    assert presenter(exo(histoire, "chronologie")) == vue  # meme melange a chaque fois


def test_parcours_piege_puis_echelle_puis_reussite(maths):
    etat = Etat("decomposer-360")
    premier = repondre(maths, etat, "8 × 45")
    assert "pas premier" in premier.message and premier.observation == {
        "capteur": "tentative_aide0",
        "valeur": 1,
        "poids": 0.5,
    }
    deuxieme = repondre(maths, etat, "8 × 45")  # meme piege : il n'est pas redit, on passe a l'echelle
    assert deuxieme.message == exo(maths, "decomposer-360")["indices"]["relance"]
    assert repondre(maths, etat, "n'importe quoi").verdict.diagnostic == ILLISIBLE  # illisible : ni tentative ni palier
    assert etat.tentatives == 2
    fin = repondre(maths, etat, "2^3 x 3^2 x 5")
    assert fin.termine and etat.reussi and fin.observation == {"capteur": "tentative_aide1", "valeur": 1}


def test_parcours_qui_n_aboutit_pas_donne_la_correction_et_les_prerequis(maths):
    etat = Etat("irreductible-252-360")
    retours = [repondre(maths, etat, r) for r in ["3/4", "1/2", "2/3", "5/6", "4/5"]]
    assert retours[-1].termine and not etat.reussi
    assert "7/10" in retours[-1].message
    assert retours[-1].prerequis == ["multiples-diviseurs-division-euclidienne"]
    assert [r.observation["capteur"] for r in retours] == [
        "tentative_aide0",
        "tentative_aide1",
        "tentative_aide1",
        "tentative_aide2",
        "tentative_aide3",
    ]
    with pytest.raises(ValueError):
        repondre(maths, etat, "7/10")


def test_parcours_ouverte_renvoie_a_un_adulte(histoire):
    retour = repondre(histoire, Etat("developpement-guerre-totale"), "Ma réponse.")
    assert not retour.termine and retour.observation is None


def test_choisir_commence_par_le_plus_facile(maths):
    premier = choisir(maths)
    assert premier and premier["difficulte"] == 1
    faits = {e["id"] for e in maths["exercices"] if e["type"] != "ouverte"}
    assert choisir(maths, faits) is None  # l'exercice ouvert n'est pas propose sans IA


def test_fiche_v2_dans_le_prompt(maths):
    texte = texte_fiche(maths, limite=20000)
    assert "Indice 1 : " + exo(maths, "decomposer-360")["indices"]["relance"] in texte
    assert "Critère de réussite" in texte and "piège fréquent" in texte
    assert "{'relance'" not in texte


def test_fiche_v2_ne_transmet_pas_la_solution_des_exercices_corriges_par_le_code(maths):
    """Le modele ne doit jamais voir la solution ni la reponse d'un exercice que le code corrige."""
    texte = texte_fiche(maths, limite=20000)
    exercice = exo(maths, "irreductible-252-360")
    assert exercice["type"] == "nombre"
    assert exercice["solution"] not in texte
    assert exercice["reponse"]["valeur"] not in texte  # "7/10" : la reponse attendue
    assert "corrigé par le code" in texte
    # l'exercice ouvert, lui, garde sa solution : personne d'autre que l'adulte/le modele ne corrige
    ouverte = exo(maths, "justifier-97")
    assert ouverte["type"] == "ouverte"
    assert ouverte["solution"] in texte


def test_fiche_v2_histoire_ne_transmet_pas_non_plus_les_solutions_corrigees(histoire):
    texte = texte_fiche(histoire, limite=20000)
    for exercice in histoire["exercices"]:
        if exercice["type"] != "ouverte":
            assert exercice["solution"] not in texte
