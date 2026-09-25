"""Parcours sans IA : derouler un exercice d'une fiche v2 avec la seule logique du code.

C'est le niveau 0 de Jules : aucun modele n'intervient. Le code presente l'exercice (sans la reponse),
corrige, choisit la relance d'un piege ou l'indice suivant, et s'arrete apres le dernier palier. Un
modele, s'il y en a un, ne fait que reformuler ce que ce parcours a decide.

Chaque tentative produit une observation pour le modele de l'eleve : le capteur `tentative_aide<n>`,
ou n est l'aide deja recue sur l'exercice (0 aucune, 1 relance, 2 methode, 3 etape).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from jules.fiches.correction import AIDE_FORMAT, ILLISIBLE, TYPES_AUTO, Verdict, corriger, piege_declenche
from jules.fiches.schema import PALIERS

TENTATIVES_MAX = 6  # au-dela, on arrete meme si des pieges restent a dire


@dataclass
class Etat:
    """Ce que le parcours retient d'un exercice en cours (a garder entre deux reponses)."""

    exercice: str
    paliers_donnes: int = 0  # 0 a 3 : combien d'indices de l'echelle ont ete donnes
    pieges_dits: list[int] = field(default_factory=list)  # un piege n'est dit qu'une fois par exercice
    tentatives: int = 0
    termine: bool = False
    reussi: bool = False


@dataclass
class Retour:
    message: str
    verdict: Verdict
    termine: bool = False
    observation: dict[str, Any] | None = None  # pour le modele de l'eleve (None : rien d'observe)
    prerequis: list[str] = field(default_factory=list)  # a revoir si l'exercice n'a pas tenu


def exercice(fiche: dict[str, Any], identifiant: str) -> dict[str, Any]:
    for ex in fiche.get("exercices") or []:
        if ex.get("id") == identifiant:
            return dict(ex)
    raise KeyError(f"{fiche.get('notion')} : exercice {identifiant!r} inconnu")


def presenter(ex: dict[str, Any]) -> dict[str, Any]:
    """Ce que l'eleve voit : l'enonce et les elements a manipuler, jamais la reponse ni la solution."""
    vue: dict[str, Any] = {"id": ex["id"], "type": ex["type"], "difficulte": ex["difficulte"], "enonce": ex["enonce"]}
    rep = ex.get("reponse") or {}
    if ex["type"] == "choix":
        vue["options"] = [dict(o) for o in rep["options"]]
        vue["plusieurs"] = len(rep["bonnes"]) > 1
    elif ex["type"] == "ordre":
        vue["elements"] = melanger(rep["elements"], ex["id"])
    elif ex["type"] == "association":
        vue["gauche"] = [dict(e) for e in rep["gauche"]]
        vue["droite"] = [dict(e) for e in rep["droite"]]
    if ex["type"] in AIDE_FORMAT:
        vue["aide_format"] = aide_format(ex)
    return vue


def melanger(elements: list[dict[str, Any]], graine: str) -> list[dict[str, Any]]:
    """L'ordre de la fiche EST la reponse : on presente un ordre melange, stable, et jamais le bon."""
    vue = [dict(e) for e in elements]
    random.Random(graine).shuffle(vue)  # noqa: S311 - pas de cryptographie, juste un ordre de presentation
    if [e["id"] for e in vue] == [e["id"] for e in elements]:
        vue = vue[1:] + vue[:1]
    return vue


def aide_format(ex: dict[str, Any]) -> str:
    if ex["type"] == "nombre" and (ex.get("reponse") or {}).get("forme") == "produit_premiers":
        return AIDE_FORMAT["produit_premiers"]
    return AIDE_FORMAT.get(ex["type"], "")


def choisir(fiche: dict[str, Any], faits: set[str] | None = None) -> dict[str, Any] | None:
    """Prochain exercice corrige sans IA : le plus facile pas encore fait, dans l'ordre de la fiche."""
    faits = faits or set()
    restants = [e for e in fiche.get("exercices") or [] if e.get("type") in TYPES_AUTO and e["id"] not in faits]
    return min(restants, key=lambda e: e["difficulte"]) if restants else None


def repondre(fiche: dict[str, Any], etat: Etat, reponse: Any) -> Retour:
    """Une reponse de l'eleve -> ce que Jules dit, et l'etat mis a jour (modifie en place)."""
    ex = exercice(fiche, etat.exercice)
    if etat.termine:
        raise ValueError("exercice deja termine")
    verdict = corriger(ex, reponse)
    if not verdict.auto:
        return Retour("Cette réponse se relit à deux : montre-la à un adulte, ou demande-moi de la relire.", verdict)
    if verdict.diagnostic == ILLISIBLE:
        return Retour(f"Je n'arrive pas à lire ta réponse. {aide_format(ex)}", verdict)
    # aide deja recue : le palier atteint (1 relance, 2 methode, 3 etape) ; une relance de piege vaut 1
    aide = max(etat.paliers_donnes, 1 if etat.pieges_dits else 0)
    etat.tentatives += 1
    observation: dict[str, Any] = {
        "capteur": f"tentative_aide{aide}",
        "valeur": 1 if verdict.juste or verdict.partiel else 0,
    }
    if verdict.partiel:
        observation["poids"] = 0.5
    if verdict.juste:
        etat.termine = etat.reussi = True
        message = "C'est juste."
        if verdict.diagnostic == "orthographe":
            message += f" Attention à l'orthographe : on écrit « {verdict.lu} »."
        return Retour(message, verdict, termine=True, observation=observation)
    piege = piege_declenche(ex, reponse, verdict)
    rang = (ex.get("pieges") or []).index(piege) if piege else -1
    if piege and rang not in etat.pieges_dits and etat.tentatives < TENTATIVES_MAX:
        etat.pieges_dits.append(rang)
        return Retour(str(piege["relance"]).strip(), verdict, observation=observation)
    if etat.paliers_donnes < len(PALIERS) and etat.tentatives < TENTATIVES_MAX:
        palier = PALIERS[etat.paliers_donnes]
        etat.paliers_donnes += 1
        return Retour(str(ex["indices"][palier]).strip(), verdict, observation=observation)
    etat.termine = True
    message = (
        "On s'arrête là pour cet exercice, tu as bien cherché. Voici la correction, lis-la calmement :\n"
        + str(ex["solution"]).strip()
    )
    prerequis = [str(p) for p in fiche.get("prerequis") or []]
    return Retour(message, verdict, termine=True, observation=observation, prerequis=prerequis)
