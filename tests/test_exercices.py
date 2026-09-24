"""Tests du module 'exercices' : entrainement sans IA sur les fiches v2 servables sans IA."""

from __future__ import annotations

import yaml
from fastapi.testclient import TestClient

from jules.fiches.schema import empreinte
from jules.web.app import creer_app

NOTION_MATHS = "nombres-premiers-decomposition"
NOTION_HISTOIRE = "guerre-totale-1914-1918"


def _echanger(tuteur, conv_id: str, texte: str) -> str:
    reponse = tuteur.echanger(conv_id, texte)
    tuteur.attendre_fond()
    return reponse.texte


def _nb_appels_principal(tuteur) -> int:
    return sum(1 for a in tuteur.llm.appels if a["modele"] == "principal")


# --- (a) et (i) : aucun appel a l'IA pendant l'exercice, un appel normal ailleurs -----------


def test_le_llm_n_est_jamais_appele_pendant_un_exercice(tuteur):
    module = tuteur.module("exercices")
    lancee = module.commencer(NOTION_MATHS)
    conv_id = lancee["conversation"]
    _echanger(tuteur, conv_id, "8 x 45")
    _echanger(tuteur, conv_id, "2^3 x 3^2 x 5")
    # la vigilance (module de fond) peut toujours regarder l'echange ; seul le modele "principal"
    # (celui qui produirait la reponse) doit rester silencieux.
    assert _nb_appels_principal(tuteur) == 0


def test_une_conversation_normale_appelle_toujours_le_llm(tuteur):
    conv = tuteur.stockage.creer_conversation("aide-devoirs")
    avant = _nb_appels_principal(tuteur)
    _echanger(tuteur, conv.id, "Bonjour Jules")
    assert _nb_appels_principal(tuteur) == avant + 1


# --- (b) : parcours complet sur decomposer-360, piege puis paliers ---------------------------


def test_parcours_maths_decomposer_360_piege_puis_paliers(tuteur):
    module = tuteur.module("exercices")
    lancee = module.commencer(NOTION_MATHS)
    conv_id = lancee["conversation"]
    assert lancee["exercice"]["id"] == "un-est-il-premier"  # difficulte 1, premier de la fiche

    # premier exercice : reponse juste, tout de suite
    texte = _echanger(tuteur, conv_id, "non")
    assert "juste" in texte.casefold()
    assert "décompose 360" in texte.casefold()  # enchaine sur decomposer-360 (meme difficulte, ordre de fiche)

    # piege : le facteur non premier declenche sa relance dediee
    relance = _echanger(tuteur, conv_id, "8 × 45")
    assert "n'est pas premier" in relance.casefold() or "decompos" in relance.casefold()
    assert "360 = 2 × 180" not in relance  # la solution ne fuit pas

    # meme piege ne se redit pas deux fois : premier palier d'indice (relance)
    r2 = _echanger(tuteur, conv_id, "8 × 45")
    assert "quel nombre premier" in r2.casefold() or "commence par le plus petit" in r2.casefold()

    # methode
    r3 = _echanger(tuteur, conv_id, "8 × 45")
    assert "divise par 2" in r3.casefold()

    # reponse finalement juste
    r4 = _echanger(tuteur, conv_id, "2^3 x 3^2 x 5")
    assert "juste" in r4.casefold()
    assert "lesquels sont premiers" in r4.casefold() or "premiers ?" in r4.casefold()


# --- (c) : reponse 'ordre' tapee en texte -----------------------------------------------------


def test_reponse_ordre_tapee_en_texte(tuteur):
    module = tuteur.module("exercices")
    lancee = module.commencer(NOTION_HISTOIRE)
    conv_id = lancee["conversation"]
    # on avance jusqu'a l'exercice 'chronologie' (type ordre) en reussissant les precedents
    for reponse in ("1914", "a", "a-x, b-y, c-x, d-y, e-y"):
        _echanger(tuteur, conv_id, reponse)
    etat = tuteur.stockage.lire_etat("exercices", conv_id)
    assert etat["exercice"] == "chronologie"
    texte = _echanger(tuteur, conv_id, "entree, genocide, bolcheviks, armistice")
    assert "juste" in texte.casefold()


# --- (d) : evenements 'observation' ------------------------------------------------------------


def test_observation_ecrite_avec_le_bon_capteur(tuteur):
    module = tuteur.module("exercices")
    lancee = module.commencer(NOTION_MATHS)
    conv_id = lancee["conversation"]
    _echanger(tuteur, conv_id, "non")  # premier exercice, juste du premier coup
    obs = tuteur.stockage.evenements("observation")
    assert obs[0]["donnees"]["capteur"] == "tentative_aide0"
    assert obs[0]["donnees"]["valeur"] == 1
    assert obs[0]["donnees"]["source"] == "fiche_v2"
    assert obs[0]["donnees"]["notion"] == NOTION_MATHS
    assert obs[0]["donnees"]["exercice"] == "un-est-il-premier"

    _echanger(tuteur, conv_id, "8 × 45")  # piege sur decomposer-360 (reponse partielle) : aide encore 0
    obs2 = tuteur.stockage.evenements("observation")[0]
    assert obs2["donnees"]["capteur"] == "tentative_aide0"
    assert obs2["donnees"]["valeur"] == 1
    assert obs2["donnees"]["poids"] == 0.5

    _echanger(tuteur, conv_id, "8 × 45")  # meme piege redit : palier relance donne -> aide1 au tour suivant
    obs3 = tuteur.stockage.evenements("observation")[0]
    assert obs3["donnees"]["capteur"] == "tentative_aide1"


# --- (e) : evenement 'suivi' a la fin de tous les exercices ------------------------------------


def test_suivi_ecrit_a_la_fin_avec_statut_compris(tuteur):
    module = tuteur.module("exercices")
    lancee = module.commencer(NOTION_MATHS)
    conv_id = lancee["conversation"]
    # toutes les reponses justes du premier coup, dans l'ordre de difficulte de la fiche
    reponses = ["non", "2^3 x 3^2 x 5", "b, d", "7/10"]
    for r in reponses:
        _echanger(tuteur, conv_id, r)
    suivis = tuteur.stockage.evenements("suivi")
    assert len(suivis) == 1
    donnees = suivis[0]["donnees"]
    assert donnees["statut"] == "compris"
    assert donnees["notion"] == "Nombres premiers, décomposition en facteurs premiers"
    assert donnees["matiere"] == "Mathématiques"
    assert donnees["titre"] == donnees["notion"]


def test_suivi_en_cours_si_un_exercice_echoue(tuteur):
    module = tuteur.module("exercices")
    lancee = module.commencer(NOTION_MATHS)
    conv_id = lancee["conversation"]
    # premier exercice : on epuise les tentatives sans jamais trouver
    for _ in range(6):
        _echanger(tuteur, conv_id, "oui")
    for r in ("2^3 x 3^2 x 5", "b, d", "7/10"):
        _echanger(tuteur, conv_id, r)
    suivis = tuteur.stockage.evenements("suivi")
    assert len(suivis) == 1
    assert suivis[0]["donnees"]["statut"] == "en_cours"


# --- (f) : la solution ne fuit jamais avant la fin de l'exercice -------------------------------


def test_solution_jamais_visible_avant_la_fin_de_l_exercice(tuteur):
    module = tuteur.module("exercices")
    lancee = module.commencer(NOTION_MATHS)
    conv_id = lancee["conversation"]
    # piege puis 3 paliers d'indice (relance, methode, etape) : la solution n'apparait qu'apres
    for _ in range(4):
        texte = _echanger(tuteur, conv_id, "oui")
        assert "1 n'a qu'un seul diviseur" not in texte
    dernier = _echanger(tuteur, conv_id, "oui")  # paliers epuises : on s'arrete, la solution apparait
    assert "1 n'a qu'un seul diviseur" in dernier


# --- (g) : une fiche modifiee (empreinte fausse) n'est pas servie ------------------------------


def test_fiche_modifiee_n_est_pas_servie(tuteur, projet):
    chemin = projet / "bibliotheque" / "fiches-v2-demonstration" / "fiches" / "mathematiques" / f"{NOTION_MATHS}.yaml"
    fiche = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    fiche["essentiel"] = fiche["essentiel"] + " Un ajout qui casse l'empreinte."
    assert fiche["empreinte"] != empreinte(fiche)  # empreinte non recalculee : signature invalide
    chemin.write_text(yaml.safe_dump(fiche, allow_unicode=True, sort_keys=False), encoding="utf-8")

    module = tuteur.module("exercices")
    module.recharger()
    assert NOTION_MATHS not in module.fiches
    assert NOTION_HISTOIRE in module.fiches  # l'autre fiche, non touchee, reste servable


# --- (h) : routes web --------------------------------------------------------------------------


def test_routes_notions_et_commencer(tuteur):
    with TestClient(creer_app(tuteur)) as client:
        r = client.get("/api/eleve/exercices/notions")
        assert r.status_code == 200
        ids = {n["id"] for n in r.json()["exercices"]}
        assert ids == {NOTION_MATHS, NOTION_HISTOIRE}
        entree_maths = next(n for n in r.json()["exercices"] if n["id"] == NOTION_MATHS)
        assert entree_maths["matiere"] == "Mathématiques"
        assert entree_maths["nb"] == 4  # 4 exercices auto sur 5 (le dernier est 'ouverte')

        lance = client.post(f"/api/eleve/exercices/{NOTION_MATHS}/commencer")
        assert lance.status_code == 200
        corps = lance.json()
        assert corps["exercice"]["id"] == "un-est-il-premier"
        conv = client.get(f"/api/conversations/{corps['conversation']}").json()
        assert conv["mode"] == "exercice"
        assert conv["messages"][0]["role"] == "bot"

        assert client.post("/api/eleve/exercices/notion-inconnue/commencer").status_code == 404


# --- (j) : mode 'exercice' cache de la grille ----------------------------------------------------


def test_mode_exercice_cache_de_la_grille(tuteur):
    modes = tuteur.infos_interface()["modes"]
    exercice_mode = next(m for m in modes if m["id"] == "exercice")
    assert exercice_mode["cache"] is True
    assert tuteur.module("modes").valider("exercice") == "aide-devoirs"


# --- message apres la fin, sans nouvel appel LLM -------------------------------------------------


def test_message_apres_fin_reste_sans_ia(tuteur):
    module = tuteur.module("exercices")
    lancee = module.commencer(NOTION_MATHS)
    conv_id = lancee["conversation"]
    for r in ("non", "2^3 x 3^2 x 5", "b, d", "7/10"):
        _echanger(tuteur, conv_id, r)
    avant = _nb_appels_principal(tuteur)
    texte = _echanger(tuteur, conv_id, "merci")
    assert _nb_appels_principal(tuteur) == avant
    assert "terminée" in texte.casefold()
