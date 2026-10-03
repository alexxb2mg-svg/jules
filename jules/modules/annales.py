"""Module 'annales' : s'entrainer sur les sujets du brevet (et a terme du bac).

L'eleve choisit un sujet d'annale (session, centre, matiere). Le sujet est affiche a gauche,
Jules accompagne a droite. Apres chaque exercice ou en fin de sujet, le module enregistre les
notions travaillees et la note estimee.

Donnees : les sujets sont des fichiers YAML dans bibliotheque/annales/<session>/<matiere>/<centre>.yaml
Structure definie dans docs/ANNALES-FORMAT.md (a venir).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from jules.modules.base import Module, extraire_json
from jules.modules.suivi import evenement_suivi
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.annales")

ESPACE = "annales"
MODE = "annale"
MARQUE_FIN = "nnale terminée"  # « Annale terminée. » (sans le A, pour tolerer « ANNALE TERMINÉE »)


def _charger_sujets(dossiers: list[str], racines: list[Any]) -> dict[str, dict[str, Any]]:
    """Charge les sujets d'annales depuis les dossiers de bibliotheque.

    Retourne un dict {id_sujet: sujet} ou chaque sujet contient les metadonnees
    et les exercices structures.
    """
    from pathlib import Path

    import yaml

    sujets: dict[str, dict[str, Any]] = {}
    for racine in racines:
        dossier_annales = Path(racine) / "annales"
        if not dossier_annales.is_dir():
            continue
        for chemin in sorted(dossier_annales.rglob("*.yaml")):
            try:
                brut = yaml.safe_load(chemin.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as err:
                journal.error("Sujet d'annale %s illisible : %s", chemin, err)
                continue
            if not isinstance(brut, dict) or "sujet" not in brut:
                continue
            sujet = brut["sujet"]
            sid = str(sujet.get("id") or chemin.stem)
            if sid not in sujets:
                sujets[sid] = sujet
    return sujets


CONSIGNE_BILAN = """Tu lis la conversation d'une séance d'annales du brevet passée par un élève avec son tuteur IA.
L'élève a travaillé sur le sujet suivant : {sujet}.
Réponds UNIQUEMENT par un objet JSON, sans texte autour :
{{"resultats": [{{"exercice": "...", "points_obtenus": 0, "points_total": 0,
"notions": ["..."], "commentaire": "..."}}]}}
- exercice : le numéro ou titre de l'exercice tel qu'il apparaît dans le sujet.
- points_obtenus : estimation de la note de l'élève sur cet exercice.
- points_total : barème de l'exercice.
- notions : les identifiants exacts des notions du référentiel concernées.
- commentaire : une phrase sur ce qui est acquis ou à retravailler.
Un objet par exercice traité. Ne juge que d'après la conversation fournie."""


class Brique(Module):
    id = "annales"
    titre = "Annale du brevet en cours"
    dependances = ("notions",)

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self._sujets: dict[str, dict[str, Any]] | None = None

    @property
    def notions_catalogue(self) -> Any:
        module = self.tuteur.module("notions")
        if module is None:
            raise RuntimeError("Le module 'annales' nécessite le module 'notions'")
        return module.catalogue

    @property
    def sujets(self) -> dict[str, dict[str, Any]]:
        if self._sujets is None:
            self._sujets = _charger_sujets(
                [str(i) for i in self.reglages.get("bibliotheques") or []],
                self.tuteur.config.dossiers_bibliotheques,
            )
        return self._sujets

    def recharger(self) -> None:
        self._sujets = None

    def _lire(self, conv_id: str) -> dict[str, Any] | None:
        return self.tuteur.stockage.lire_etat(ESPACE, conv_id)

    def _sauver(self, conv_id: str, donnees: dict[str, Any]) -> None:
        self.tuteur.stockage.ecrire_etat(ESPACE, conv_id, donnees)

    # --- catalogue de sujets disponibles ---
    def sujets_disponibles(self) -> list[dict[str, Any]]:
        """Liste les sujets d'annales disponibles, groupes par session et matiere."""
        result: list[dict[str, Any]] = []
        for sid, sujet in self.sujets.items():
            result.append(
                {
                    "id": sid,
                    "session": str(sujet.get("session") or ""),
                    "matiere": str(sujet.get("matiere") or ""),
                    "centre": str(sujet.get("centre") or ""),
                    "titre": str(sujet.get("titre") or f"{sujet.get('matiere', '')} — {sujet.get('session', '')}"),
                    "duree": str(sujet.get("duree") or ""),
                    "nb_exercices": len(sujet.get("exercices") or []),
                }
            )
        result.sort(key=lambda s: (s["session"], s["matiere"], s["centre"]))
        return result

    def notions_brevet(self) -> list[dict[str, str]]:
        """Notions du referentiel marquees brevet: true, par matiere."""
        notions = self.notions_catalogue.notions
        result: list[dict[str, str]] = []
        for n in notions.values():
            if n.brevet:
                result.append(
                    {
                        "id": n.id,
                        "titre": n.titre,
                        "matiere": n.nom_matiere,
                        "theme": n.theme,
                    }
                )
        return result

    # --- demarrage d'une session d'annales ---
    def commencer(self, sujet_id: str) -> dict[str, Any]:
        sujet = self.sujets.get(sujet_id)
        if sujet is None:
            raise KeyError(sujet_id)
        stockage = self.tuteur.stockage
        conv = stockage.creer_conversation(MODE)
        titre = str(sujet.get("titre") or f"Annale — {sujet.get('matiere', '')} {sujet.get('session', '')}")
        stockage.renommer(conv.id, titre)
        donnees: dict[str, Any] = {
            "sujet_id": sujet_id,
            "sujet": sujet,
            "exercice_courant": 0,
            "resultats": [],
            "terminee": False,
        }
        self._sauver(conv.id, donnees)
        presentation = self._presenter_sujet(sujet)
        stockage.ajouter_message(conv.id, Message(role="bot", texte=presentation))
        return {
            "conversation": conv.id,
            "mode": MODE,
            "titre": titre,
            "sujet": self._vue_sujet(sujet),
        }

    def _presenter_sujet(self, sujet: dict[str, Any]) -> str:
        matiere = sujet.get("matiere", "")
        session = sujet.get("session", "")
        centre = sujet.get("centre", "")
        duree = sujet.get("duree", "")
        exercices = sujet.get("exercices") or []
        nb = len(exercices)
        lignes = [f"**{matiere} — Session {session}**"]
        if centre:
            lignes[0] += f" ({centre})"
        if duree:
            lignes.append(f"Durée : {duree}")
        lignes.append(f"{nb} exercice{'s' if nb > 1 else ''}.")
        total = sum(e.get("bareme", 0) for e in exercices)
        if total:
            lignes.append(f"Total : {total} points.")
        lignes.append("\nPar quel exercice veux-tu commencer ?")
        return "\n".join(lignes)

    def _vue_sujet(self, sujet: dict[str, Any]) -> dict[str, Any]:
        """Vue du sujet envoyee au frontend (pas les reponses)."""
        exercices_vue: list[dict[str, Any]] = []
        for ex in sujet.get("exercices") or []:
            vue: dict[str, Any] = {
                "numero": ex.get("numero", ""),
                "titre": ex.get("titre", ""),
                "bareme": ex.get("bareme", 0),
                "enonce": ex.get("enonce", ""),
                "partie": ex.get("partie", ""),
            }
            if "sous_questions" in ex:
                vue["sous_questions"] = [
                    {"id": sq.get("id", ""), "enonce": sq.get("enonce", ""), "bareme": sq.get("bareme", 0)}
                    for sq in ex["sous_questions"]
                ]
            if "figure" in ex:
                vue["figure"] = ex["figure"]
            if "tableau" in ex:
                vue["tableau"] = ex["tableau"]
            exercices_vue.append(vue)
        return {
            "session": sujet.get("session", ""),
            "matiere": sujet.get("matiere", ""),
            "centre": sujet.get("centre", ""),
            "duree": sujet.get("duree", ""),
            "consignes_generales": sujet.get("consignes_generales", ""),
            "exercices": exercices_vue,
        }

    # --- contribution au prompt systeme ---
    def contribution(self, conv: Conversation) -> str | None:
        if conv.mode != MODE:
            return None
        donnees = self._lire(conv.id)
        if not donnees:
            return None
        sujet = donnees.get("sujet") or {}
        exercices = sujet.get("exercices") or []
        lignes: list[str] = []
        lignes.append(f"Sujet d'annale : {sujet.get('matiere', '')} — session {sujet.get('session', '')}")
        if sujet.get("centre"):
            lignes.append(f"Centre : {sujet['centre']}")
        lignes.append(f"Durée : {sujet.get('duree', '')}")
        for ex in exercices:
            points = f" ({ex.get('bareme', '?')} points)" if ex.get("bareme") else ""
            lignes.append(f"- Exercice {ex.get('numero', '?')}{points} : {ex.get('titre', '')}")
        return "\n".join(lignes)

    # --- analyse du bilan apres la marque de fin ---
    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        if conv.mode != MODE or MARQUE_FIN not in bot.texte.casefold():
            return
        donnees = self._lire(conv.id)
        if not donnees or donnees.get("terminee"):
            return
        sujet = donnees.get("sujet") or {}
        titre_sujet = str(sujet.get("titre") or f"{sujet.get('matiere', '')} {sujet.get('session', '')}")
        from jules.llm.base import Tour

        echanges = "\n".join(f"{'ÉLÈVE' if m.role == 'eleve' else 'TUTEUR'} : {m.texte[:1500]}" for m in conv.messages)
        tours = [Tour(role="user", texte=f"Conversation :\n{echanges}")]
        consigne = CONSIGNE_BILAN.format(sujet=titre_sujet)
        brut = self.tuteur.llm.repondre(consigne, tours, "rapide")
        resultats_bruts = extraire_json(brut)
        if not resultats_bruts:
            journal.warning("Bilan d'annale illisible : %s", brut[:200])
            donnees["terminee"] = True
            self._sauver(conv.id, donnees)
            return
        self._enregistrer_bilan(conv.id, donnees, resultats_bruts, titre_sujet)

    def _enregistrer_bilan(
        self, conv_id: str, donnees: dict[str, Any], resultats_bruts: dict[str, Any], titre_sujet: str
    ) -> None:
        stockage = self.tuteur.stockage
        resultats = resultats_bruts.get("resultats") or []
        points_total = 0
        points_obtenus = 0
        notions_vues: set[str] = set()
        for r in resultats:
            if not isinstance(r, dict):
                continue
            pts = r.get("points_obtenus", 0)
            total = r.get("points_total", 0)
            points_obtenus += pts if isinstance(pts, (int, float)) else 0
            points_total += total if isinstance(total, (int, float)) else 0
            for notion_id in r.get("notions") or []:
                notion_id = str(notion_id).strip()
                if notion_id in notions_vues:
                    continue
                notions_vues.add(notion_id)
                notion = self.notions_catalogue.notion(notion_id)
                if notion is None:
                    continue
                reussi = (
                    isinstance(pts, (int, float))
                    and isinstance(total, (int, float))
                    and total > 0
                    and pts >= total * 0.5
                )
                statut = "compris" if reussi else "en_cours"
                resume = (
                    f"Annale ({titre_sujet}) : exercice réussi."
                    if reussi
                    else f"Annale ({titre_sujet}) : à retravailler."
                )
                stockage.ajouter_evenement(
                    "suivi",
                    evenement_suivi(
                        matiere=notion.nom_matiere,
                        notion=notion.titre,
                        statut=statut,
                        resume=resume,
                        titre=titre_sujet,
                        origine="annales",
                    ),
                    conv_id,
                )
        donnees["resultats"] = resultats
        donnees["terminee"] = True
        donnees["bilan"] = {
            "points_obtenus": points_obtenus,
            "points_total": points_total,
            "nb_exercices": len(resultats),
        }
        self._sauver(conv_id, donnees)
        stockage.ajouter_evenement(
            "annale",
            {
                "sujet": donnees.get("sujet_id", ""),
                "points_obtenus": points_obtenus,
                "points_total": points_total,
                "nb_exercices": len(resultats),
            },
            conv_id,
        )

    # --- routes eleve ---
    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/sujets")
        def lister_sujets() -> dict[str, Any]:
            return {"sujets": self.sujets_disponibles()}

        @routeur.get("/notions-brevet")
        def lister_notions_brevet() -> dict[str, Any]:
            return {"notions": self.notions_brevet()}

        @routeur.post("/{sujet_id}/commencer")
        def lancer(sujet_id: str) -> dict[str, Any]:
            try:
                return self.commencer(sujet_id)
            except KeyError as err:
                raise HTTPException(404, "Sujet d'annale introuvable") from err

        @routeur.get("/{conv_id}/etat")
        def etat(conv_id: str) -> dict[str, Any]:
            donnees = self._lire(conv_id)
            if donnees is None:
                raise HTTPException(404, "Pas de session d'annale en cours ici")
            sujet = donnees.get("sujet") or {}
            return {
                "sujet": self._vue_sujet(sujet),
                "exercice_courant": donnees.get("exercice_courant", 0),
                "terminee": donnees.get("terminee", False),
                "bilan": donnees.get("bilan"),
            }

        return routeur

    def infos_interface(self) -> dict[str, Any]:
        return {"annales": {"active": True, "nb_sujets": len(self.sujets)}}
