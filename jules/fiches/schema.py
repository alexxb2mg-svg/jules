"""Fiches v2 : le contrat qui permet a Jules de servir une fiche sans IA.

Une fiche v2 (`format: 2`) est une fiche dont chaque exercice se corrige par le code
(`jules/fiches/correction.py`), avec une echelle de trois indices et des pieges qui relient une erreur
typique a sa relance. Le contrat complet est dans docs/FICHES-V2.md.

`verifier_fiche()` renvoie la liste des manquements (vide = fiche conforme). Aucun champ inconnu n'est
toleré : une faute de frappe dans un nom de champ est une erreur, pas un champ ignore en silence.

L'`empreinte` scelle le contenu verifie. Une fiche `verifiee` ou `relue` dont le contenu a change depuis
n'est plus servie sans IA tant qu'on ne l'a pas re-verifiee (`jules fiches signer`).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from typing import Any

from jules.bibliotheques import LICENCES_LIBRES, mots, normaliser
from jules.fiches.correction import (
    DIAGNOSTICS,
    FORMES_EXPRESSION,
    FORMES_NOMBRE,
    ILLISIBLE,
    TYPES,
    TYPES_AUTO,
    ReponseIllisible,
    corriger,
    decomposer,
    ecrire_produit,
    ecrire_scientifique,
    lire_expression,
    lire_nombre,
    piege_declenche,
    reponse_de_reference,
)

FORMAT = 2
ETATS = ("generee", "verifiee", "relue")  # generee : ecrite, pas encore passee au verificateur
ETATS_SANS_IA = ("verifiee", "relue")  # seules ces fiches sont servies au niveau 0
STATUTS_RELECTURE = ("a_relire", "relue")
PALIERS = ("relance", "methode", "etape")  # l'echelle d'indices, du plus leger au plus fort
AIDE_PAR_PALIER = {"relance": 1, "methode": 2, "etape": 3}  # meme echelle que le modele de l'eleve

CHAMPS_FICHE = {
    "format",
    "notion",
    "version",
    "etat",
    "declencheurs",
    "prerequis",
    "couverture",
    "essentiel",
    "methode",
    "vocabulaire",
    "erreurs_frequentes",
    "exemple",
    "exercices",
    "sources",
    "relecture",
    "generation",
    "empreinte",
}
CHAMPS_OBLIGATOIRES = (
    "format",
    "notion",
    "version",
    "etat",
    "declencheurs",
    "prerequis",
    "essentiel",
    "methode",
    "erreurs_frequentes",
    "exemple",
    "exercices",
    "sources",
    "relecture",
)
CHAMPS_EXERCICE = {"id", "type", "difficulte", "enonce", "reponse", "criteres", "indices", "pieges", "solution"}
CHAMPS_REPONSE = {
    "nombre": {"valeur", "forme", "tolerance"},
    "expression": {"valeur", "variables", "forme"},
    "choix": {"options", "bonnes"},
    "texte_court": {"acceptees", "fautes_tolerees"},
    "ordre": {"elements"},
    "association": {"gauche", "droite", "paires"},
}
CHAMPS_SOURCE = {"titre", "url", "auteurs", "licence", "consulte_le", "usage"}
# `modele` : l'IA qui a ecrit la fiche ; `paquet` : la version du paquet de generation (`jules chantier paquet`).
CHAMPS_GENERATION = {"par", "le", "a_partir_de", "modele", "paquet"}
# Hors empreinte : ce qui change sans que le contenu change (etat, relecture, empreinte elle-meme).
HORS_EMPREINTE = {"etat", "relecture", "empreinte", "version"}

MIN_DECLENCHEURS = 3
MIN_EXERCICES_AUTO = 3
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def est_v2(fiche: dict[str, Any]) -> bool:
    return fiche.get("format") == FORMAT


def empreinte(fiche: dict[str, Any]) -> str:
    """Empreinte du contenu (sha256 sur un JSON canonique, sans etat ni relecture)."""
    contenu = {k: v for k, v in fiche.items() if k not in HORS_EMPREINTE}
    texte = json.dumps(contenu, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(texte.encode("utf-8")).hexdigest()


def servable_sans_ia(fiche: dict[str, Any]) -> bool:
    """Vraie seulement pour une fiche v2 verifiee (ou relue) dont le contenu n'a pas bouge depuis."""
    return est_v2(fiche) and fiche.get("etat") in ETATS_SANS_IA and fiche.get("empreinte") == empreinte(fiche)


def cle_texte(texte: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", normaliser(str(texte))))


def _texte(valeur: Any) -> bool:
    return isinstance(valeur, str) and bool(valeur.strip())


def _liste_textes(valeur: Any, minimum: int = 1) -> bool:
    return isinstance(valeur, list) and len(valeur) >= minimum and all(_texte(v) for v in valeur)


def _ids_uniques(elements: Any, nom: str, erreurs: list[str], lieu: str, minimum: int) -> list[str]:
    if not isinstance(elements, list) or len(elements) < minimum:
        erreurs.append(f"{lieu} : `{nom}` doit lister au moins {minimum} elements")
        return []
    ids = []
    for e in elements:
        if not isinstance(e, dict) or set(e) != {"id", "texte"} or not _ID.match(str(e.get("id"))):
            erreurs.append(f"{lieu} : chaque element de `{nom}` est {{id, texte}} (id en minuscules)")
            return []
        if not _texte(e["texte"]):
            erreurs.append(f"{lieu} : `{nom}.{e['id']}` sans texte")
        ids.append(str(e["id"]))
    if len(set(ids)) != len(ids):
        erreurs.append(f"{lieu} : identifiants en double dans `{nom}`")
    return ids


# --- la reponse attendue, type par type -----------------------------------------------


def _verifier_reponse(ex: dict[str, Any], lieu: str, erreurs: list[str]) -> bool:
    """Structure de `reponse` ; renvoie False si la suite des verifications n'a pas de sens."""
    type_ = ex["type"]
    rep = ex.get("reponse")
    avant = len(erreurs)
    if type_ == "ouverte":
        if rep is not None:
            erreurs.append(f"{lieu} : un exercice `ouverte` n'a pas de `reponse` (il a des `criteres`)")
        if not _liste_textes(ex.get("criteres"), 2):
            erreurs.append(f"{lieu} : `criteres` doit lister au moins 2 criteres de reussite")
        return False
    if ex.get("criteres") is not None:
        erreurs.append(f"{lieu} : `criteres` est reserve aux exercices `ouverte`")
    if not isinstance(rep, dict):
        erreurs.append(f"{lieu} : `reponse` manquante")
        return False
    inconnus = set(rep) - CHAMPS_REPONSE[type_]
    if inconnus:
        erreurs.append(f"{lieu} : champ(s) inconnu(s) dans `reponse` : {', '.join(sorted(inconnus))}")
    try:
        if type_ == "nombre":
            valeur = lire_nombre(str(rep["valeur"]))
            forme = rep.get("forme", "libre")
            if forme not in FORMES_NOMBRE:
                erreurs.append(f"{lieu} : forme {forme!r} inconnue ({', '.join(FORMES_NOMBRE)})")
            if forme == "produit_premiers" and (valeur.denominator != 1 or valeur < 2):
                erreurs.append(f"{lieu} : `produit_premiers` attend un entier >= 2")
            if lire_nombre(str(rep.get("tolerance", 0))) < 0:
                erreurs.append(f"{lieu} : tolerance negative")
        elif type_ == "expression":
            variables = rep.get("variables") or ["x"]
            if not all(isinstance(v, str) and re.fullmatch(r"[a-z]", v) for v in variables):
                erreurs.append(f"{lieu} : `variables` = lettres minuscules seules")
                return False
            lire_expression(str(rep["valeur"]), variables)
            if rep.get("forme", "libre") not in FORMES_EXPRESSION:
                erreurs.append(f"{lieu} : forme inconnue ({', '.join(FORMES_EXPRESSION)})")
        elif type_ == "choix":
            ids = _ids_uniques(rep.get("options"), "options", erreurs, lieu, 2)
            bonnes = rep.get("bonnes")
            if not isinstance(bonnes, list) or not bonnes or not {str(b) for b in bonnes} <= set(ids):
                erreurs.append(f"{lieu} : `bonnes` doit lister des identifiants de `options`")
                return False
            if len(set(map(str, bonnes))) == len(ids):
                erreurs.append(f"{lieu} : toutes les options sont bonnes, ce n'est pas un choix")
        elif type_ == "texte_court":
            if not _liste_textes(rep.get("acceptees")):
                erreurs.append(f"{lieu} : `acceptees` doit lister au moins une reponse")
                return False
            if rep.get("fautes_tolerees", 0) not in (0, 1, 2):
                erreurs.append(f"{lieu} : `fautes_tolerees` vaut 0, 1 ou 2")
        elif type_ == "ordre":
            if not _ids_uniques(rep.get("elements"), "elements", erreurs, lieu, 3):
                return False
        elif type_ == "association":
            gauche = _ids_uniques(rep.get("gauche"), "gauche", erreurs, lieu, 2)
            droite = _ids_uniques(rep.get("droite"), "droite", erreurs, lieu, 2)
            paires = rep.get("paires")
            if not isinstance(paires, dict) or set(map(str, paires)) != set(gauche):
                erreurs.append(f"{lieu} : `paires` associe chaque element de `gauche` (et eux seuls)")
                return False
            if not {str(v) for v in paires.values()} <= set(droite):
                erreurs.append(f"{lieu} : `paires` vise un element absent de `droite`")
                return False
    except (KeyError, ReponseIllisible, ValueError, ZeroDivisionError) as err:
        erreurs.append(f"{lieu} : reponse attendue illisible ({err})")
        return False
    return len(erreurs) == avant


# --- fuites : un indice ou une relance qui contient la reponse ---------------------------


def _formes_de_la_reponse(ex: dict[str, Any]) -> list[str]:
    """Ecritures de la bonne reponse qu'un indice ne doit jamais contenir (cles normalisees)."""
    rep = ex.get("reponse") or {}
    type_ = ex["type"]
    if type_ == "nombre":
        if rep.get("forme") == "produit_premiers":
            facteurs = decomposer(int(lire_nombre(str(rep["valeur"]))))
            return [cle_texte(ecrire_produit(facteurs)), cle_texte(" × ".join(str(b) for b, _ in facteurs))]
        if rep.get("forme") == "scientifique":
            return [cle_texte(rep["valeur"]), cle_texte(ecrire_scientifique(lire_nombre(str(rep["valeur"]))))]
        return [cle_texte(rep["valeur"])]
    if type_ == "expression":
        return [cle_texte(rep["valeur"])]
    if type_ == "texte_court":
        return [cle_texte(a) for a in rep["acceptees"]]
    return []


def _segments_calcul(ex: dict[str, Any], texte: str) -> list[str]:
    """Morceaux d'un texte qui ressemblent a un calcul (chiffres, operateurs, variables de l'exercice)."""
    variables = "".join((ex.get("reponse") or {}).get("variables") or ["x"]) if ex["type"] == "expression" else ""
    motif = rf"[\d({variables}][\d\s×x*·^⁰¹²³⁴⁵⁶⁷⁸⁹,./()+\-−{variables}]*"
    morceaux = []
    for bloc in re.split(r"[:;!?«»]|\s=\s|\.\s", texte):
        morceaux += [_equilibrer(m) for m in re.findall(motif, bloc)]
    return [m for m in morceaux if m and any(c.isdigit() for c in m + variables)]


def _equilibrer(morceau: str) -> str:
    """Retire la ponctuation et les parentheses orphelines en bordure (« 1914 ( » -> « 1914 »)."""
    m = morceau.strip(" .,")
    while m and (m.count("(") != m.count(")")):
        if m.endswith("(") or (m.count("(") < m.count(")") and m.endswith(")")):
            m = m[:-1].strip(" .,")
        elif m.startswith(")") or (m.count("(") > m.count(")") and m.startswith("(")):
            m = m[1:].strip(" .,")
        else:
            break
    return m


def _fuite(ex: dict[str, Any], texte: str) -> bool:
    cle = f" {cle_texte(texte)} "
    if any(forme and f" {forme} " in cle for forme in _formes_de_la_reponse(ex)):
        return True
    if ex["type"] in ("nombre", "expression"):  # la reponse sous une autre ecriture (2 × 2 × 2 × 3² × 5...)
        return any(corriger(ex, morceau).juste for morceau in _segments_calcul(ex, texte))
    if ex["type"] == "choix":  # une fuite = toutes les bonnes options citees dans le meme texte
        rep = ex["reponse"]
        textes = {str(o["id"]): cle_texte(o["texte"]) for o in rep["options"]}
        return all(f" {textes[str(b)]} " in cle for b in rep["bonnes"])
    return False


# --- un exercice ---------------------------------------------------------------------------


def _verifier_exercice(ex: Any, lieu: str, erreurs: list[str]) -> None:
    if not isinstance(ex, dict):
        erreurs.append(f"{lieu} : un exercice est un objet")
        return
    inconnus = set(ex) - CHAMPS_EXERCICE
    if inconnus:
        erreurs.append(f"{lieu} : champ(s) inconnu(s) : {', '.join(sorted(inconnus))}")
    if ex.get("type") not in TYPES:
        erreurs.append(f"{lieu} : type {ex.get('type')!r} inconnu ({', '.join(TYPES)})")
        return
    if ex.get("difficulte") not in (1, 2, 3):
        erreurs.append(f"{lieu} : `difficulte` vaut 1, 2 ou 3")
    for champ in ("enonce", "solution"):
        if not _texte(ex.get(champ)):
            erreurs.append(f"{lieu} : `{champ}` manquant")
    indices = ex.get("indices")
    if not isinstance(indices, dict) or set(indices) != set(PALIERS) or not all(_texte(v) for v in indices.values()):
        erreurs.append(f"{lieu} : `indices` = exactement {', '.join(PALIERS)}, tous remplis")
        indices = {}
    lisible = _verifier_reponse(ex, lieu, erreurs)
    pieges = ex.get("pieges") or []
    if ex["type"] == "ouverte":
        if pieges:
            erreurs.append(f"{lieu} : pas de `pieges` sur un exercice `ouverte` (rien ne les declencherait)")
        return
    if not lisible:
        return
    # 1. la fiche se corrige elle-meme : sa propre bonne reponse est jugee juste
    verdict = corriger(ex, reponse_de_reference(ex))
    if not verdict.juste:
        erreurs.append(f"{lieu} : la bonne reponse de la fiche est jugee fausse ({verdict.diagnostic})")
    if ex["type"] == "texte_court":
        for acceptee in ex["reponse"]["acceptees"]:
            if not corriger(ex, acceptee).juste:
                erreurs.append(f"{lieu} : reponse acceptee {acceptee!r} jugee fausse")
    # 2. la solution redigee aboutit bien a la reponse attendue (sinon l'une des deux est fausse)
    if ex["type"] in ("nombre", "expression", "texte_court") and not _fuite(ex, str(ex.get("solution", ""))):
        erreurs.append(f"{lieu} : la solution redigee n'aboutit pas a la reponse attendue")
    # 3. aucun indice, aucune relance ne donne la reponse
    for palier, texte in indices.items():
        if _fuite(ex, texte):
            erreurs.append(f"{lieu} : l'indice `{palier}` contient la reponse")
    # 4. chaque piege est une vraie erreur, lisible, qui le declenche lui-meme
    if not isinstance(pieges, list):
        erreurs.append(f"{lieu} : `pieges` est une liste")
        return
    for j, piege in enumerate(pieges, 1):
        ici = f"{lieu}, piege {j}"
        if not isinstance(piege, dict) or set(piege) != {"si", "relance"} or not _texte(piege.get("relance")):
            erreurs.append(f"{ici} : un piege est {{si, relance}}")
            continue
        if _fuite(ex, piege["relance"]):
            erreurs.append(f"{ici} : la relance contient la reponse")
        condition = piege["si"]
        if not isinstance(condition, dict) or len(condition) != 1:
            erreurs.append(f"{ici} : `si` porte une seule condition (valeur, contient ou diagnostic)")
            continue
        ((cle, valeur),) = condition.items()
        if cle == "valeur":
            v = corriger(ex, valeur)
            if v.juste:
                erreurs.append(f"{ici} : la valeur du piege est une bonne reponse")
            elif v.diagnostic == ILLISIBLE:
                erreurs.append(f"{ici} : la valeur du piege ne se lit pas ({valeur!r})")
            elif piege_declenche(ex, valeur, v) != piege:
                erreurs.append(f"{ici} : un piege precedent l'intercepte, il ne sera jamais dit")
        elif cle == "contient":
            if ex["type"] != "choix":
                erreurs.append(f"{ici} : `contient` est reserve aux exercices `choix`")
                continue
            options = {str(o["id"]) for o in ex["reponse"]["options"]}
            bonnes = {str(b) for b in ex["reponse"]["bonnes"]}
            if not isinstance(valeur, list) or not valeur or not {str(c) for c in valeur} <= options - bonnes:
                erreurs.append(f"{ici} : `contient` liste des options fausses")
        elif cle == "diagnostic":
            if valeur not in DIAGNOSTICS[ex["type"]]:
                erreurs.append(
                    f"{ici} : diagnostic {valeur!r} impossible pour `{ex['type']}` "
                    f"({', '.join(DIAGNOSTICS[ex['type']])})"
                )
        else:
            erreurs.append(f"{ici} : condition {cle!r} inconnue (valeur, contient, diagnostic)")


# --- la fiche ------------------------------------------------------------------------------


def verifier_fiche(fiche: Any, notions_connues: set[str] | None = None, controler_empreinte: bool = True) -> list[str]:
    """Manquements au contrat v2 (liste vide = conforme).

    notions_connues : identifiants du referentiel, pour verifier `notion` et `prerequis` (None = ne pas verifier).
    controler_empreinte : faux pendant la signature, qui recalcule justement l'empreinte.
    """
    if not isinstance(fiche, dict):
        return ["la fiche doit etre un objet YAML"]
    nom = str(fiche.get("notion") or "?")
    erreurs: list[str] = []
    inconnus = set(fiche) - CHAMPS_FICHE
    if inconnus:
        erreurs.append(f"{nom} : champ(s) inconnu(s) : {', '.join(sorted(inconnus))}")
    manquants = [c for c in CHAMPS_OBLIGATOIRES if c not in fiche]
    if manquants:
        erreurs.append(f"{nom} : champ(s) obligatoire(s) manquant(s) : {', '.join(manquants)}")
        return erreurs
    if fiche["format"] != FORMAT:
        erreurs.append(f"{nom} : `format` vaut {FORMAT}")
    if not _ID.match(nom) or (notions_connues is not None and nom not in notions_connues):
        erreurs.append(f"{nom} : notion inconnue du referentiel")
    if not isinstance(fiche["version"], int) or isinstance(fiche["version"], bool) or fiche["version"] < 1:
        erreurs.append(f"{nom} : `version` est un entier >= 1")
    if fiche["etat"] not in ETATS:
        erreurs.append(f"{nom} : `etat` vaut {', '.join(ETATS)}")
    # index
    declencheurs = fiche["declencheurs"]
    if not _liste_textes(declencheurs, MIN_DECLENCHEURS):
        erreurs.append(f"{nom} : au moins {MIN_DECLENCHEURS} declencheurs")
    else:
        cles = [cle_texte(d) for d in declencheurs]
        if len(set(cles)) != len(cles):
            erreurs.append(f"{nom} : declencheur en double (une fois normalise)")
        muets = [d for d in declencheurs if not mots(d)]
        if muets:
            erreurs.append(f"{nom} : declencheur(s) invisible(s) pour la detection (mots vides, trop courts) : {muets}")
    prerequis = fiche["prerequis"]
    if not isinstance(prerequis, list) or not all(isinstance(p, str) and _ID.match(p) for p in prerequis):
        erreurs.append(f"{nom} : `prerequis` est une liste d'identifiants de notions (vide si aucun)")
    else:
        if nom in prerequis:
            erreurs.append(f"{nom} : une notion n'est pas son propre prerequis")
        if notions_connues is not None:
            for p in prerequis:
                if p not in notions_connues:
                    erreurs.append(f"{nom} : prerequis {p!r} inconnu du referentiel")
    # contenu de cours
    if not _texte(fiche["essentiel"]):
        erreurs.append(f"{nom} : `essentiel` manquant")
    for champ in ("methode", "erreurs_frequentes"):
        if not _liste_textes(fiche[champ]):
            erreurs.append(f"{nom} : `{champ}` est une liste non vide de textes")
    exemple = fiche["exemple"]
    if (
        not isinstance(exemple, dict)
        or set(exemple) != {"enonce", "solution"}
        or not all(_texte(v) for v in exemple.values())
    ):
        erreurs.append(f"{nom} : `exemple` = {{enonce, solution}}")
    vocabulaire = fiche.get("vocabulaire")
    if vocabulaire is not None and not (
        isinstance(vocabulaire, list)
        and all(isinstance(v, dict) and set(v) == {"terme", "definition"} for v in vocabulaire)
    ):
        erreurs.append(f"{nom} : `vocabulaire` = liste de {{terme, definition}}")
    # exercices
    exercices = fiche["exercices"]
    if not isinstance(exercices, list) or not exercices:
        erreurs.append(f"{nom} : `exercices` manquants")
        exercices = []
    ids = [str(e.get("id")) for e in exercices if isinstance(e, dict)]
    for i, ex in enumerate(exercices, 1):
        identifiant = ex.get("id") if isinstance(ex, dict) else None
        if not isinstance(identifiant, str) or not _ID.match(identifiant):
            erreurs.append(f"{nom}, exercice {i} : `id` manquant ou mal forme (minuscules, tirets)")
        _verifier_exercice(ex, f"{nom}/{identifiant or i}", erreurs)
    if len(set(ids)) != len(ids):
        erreurs.append(f"{nom} : identifiant d'exercice en double")
    auto = [e for e in exercices if isinstance(e, dict) and e.get("type") in TYPES_AUTO]
    if len(auto) < MIN_EXERCICES_AUTO:
        erreurs.append(f"{nom} : au moins {MIN_EXERCICES_AUTO} exercices corriges sans IA (il y en a {len(auto)})")
    if auto and not any(e.get("difficulte") == 1 for e in auto):
        erreurs.append(f"{nom} : au moins un exercice corrige sans IA de difficulte 1 (pour commencer)")
    # sources, relecture, generation
    sources = fiche["sources"]
    if not isinstance(sources, list) or not sources:
        erreurs.append(f"{nom} : au moins une source")
    else:
        for s in sources:
            if not isinstance(s, dict) or set(s) - CHAMPS_SOURCE or not {"titre", "url", "licence"} <= set(s):
                erreurs.append(f"{nom} : source = {{titre, url, licence, auteurs, consulte_le, usage}}")
                continue
            if s["licence"] not in LICENCES_LIBRES:
                erreurs.append(f"{nom} : licence de source {s['licence']!r} non reconnue comme libre")
            if not str(s["url"]).startswith("https://"):
                erreurs.append(f"{nom} : lien de source en https:// obligatoire")
    relecture = fiche["relecture"]
    if not isinstance(relecture, dict) or relecture.get("statut") not in STATUTS_RELECTURE:
        erreurs.append(f"{nom} : `relecture.statut` vaut {', '.join(STATUTS_RELECTURE)}")
    elif relecture["statut"] == "relue" and not (
        _texte(relecture.get("par")) and _DATE.match(str(relecture.get("le")))
    ):
        erreurs.append(f"{nom} : une fiche relue dit par qui (`par`) et quand (`le`, AAAA-MM-JJ)")
    elif fiche["etat"] == "relue" and relecture["statut"] != "relue":
        erreurs.append(f"{nom} : `etat: relue` sans relecture renseignee")
    generation = fiche.get("generation")
    if generation is not None and (not isinstance(generation, dict) or set(generation) - CHAMPS_GENERATION):
        erreurs.append(f"{nom} : `generation` = {{{', '.join(sorted(CHAMPS_GENERATION))}}}")
    # scellé
    if controler_empreinte and fiche["etat"] in ETATS_SANS_IA and fiche.get("empreinte") != empreinte(fiche):
        erreurs.append(f"{nom} : contenu modifie depuis la verification (empreinte) : relancer `jules fiches signer`")
    return erreurs


# --- l'index des declencheurs, sur toute une bibliotheque -------------------------------------


def collisions(fiches: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    """Declencheurs (normalises) revendiques par plusieurs notions : {declencheur: {notions}}."""
    index: dict[str, set[str]] = defaultdict(set)
    for notion, fiche in fiches.items():
        for d in fiche.get("declencheurs") or []:
            index[cle_texte(d)].add(notion)
    return {d: n for d, n in sorted(index.items()) if len(n) > 1}


def signer(fiche: dict[str, Any], notions_connues: set[str] | None = None) -> tuple[dict[str, Any], list[str]]:
    """Verifie la fiche et, si elle est conforme, la scelle : etat `verifiee`, empreinte, version.

    Un contenu modifie apres une relecture repasse `verifiee` et `a_relire` : la relecture portait
    sur l'ancien contenu. La version augmente a chaque changement de contenu deja scelle.
    """
    erreurs = verifier_fiche(fiche, notions_connues, controler_empreinte=False)
    if erreurs:
        return fiche, erreurs
    nouvelle = dict(fiche)
    actuelle = empreinte(fiche)
    ancienne = fiche.get("empreinte")
    relue = fiche["relecture"].get("statut") == "relue"
    if ancienne == actuelle and fiche["etat"] in ETATS_SANS_IA:
        nouvelle["etat"] = "relue" if relue else "verifiee"  # la relecture s'ajoute sans toucher au contenu
        return nouvelle, []
    if ancienne and ancienne != actuelle:
        nouvelle["version"] = int(fiche["version"]) + 1
        if fiche["etat"] == "relue" or relue:
            nouvelle["relecture"] = {"statut": "a_relire", "par": "", "le": ""}
    nouvelle["etat"] = "relue" if nouvelle["relecture"].get("statut") == "relue" else "verifiee"
    nouvelle["empreinte"] = actuelle
    return nouvelle, []
