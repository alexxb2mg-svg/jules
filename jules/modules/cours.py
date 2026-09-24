"""Module 'cours' : interface de lecon guidee, notion par notion.

Une lecon (jules/lecons.py) est une suite de blocs (objectifs, texte, exemple, exercice,
question_ouverte, synthese, outil). Ce module :
  - expose le parcours d'une matiere (notions du referentiel, etat estime, lecon dispo ou non) ;
  - ouvre / reprend une session de lecon (une session par notion, reprise si non terminee) ;
  - traite les tentatives de l'eleve (correction automatique quand elle existe, sinon relecture
    par Jules) avec le garde-fou : la reponse attendue ne doit jamais atteindre l'eleve avant
    qu'il ait cherche, et jamais via une reaction de Jules ;
  - a la fin de la lecon, ecrit un evenement 'suivi' pour que l'epreuve sans aide et le bilan du
    soir le voient.

Reglages (config.yaml) :
  bibliotheques: [lecons-3e-experimentales]   # bibliotheques de type 'lecons', par ordre de priorite

Format complet des lecons et de l'API : docs/COURS-CONTRAT.md.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jules.lecons import (
    TENTATIVES_AVANT_CORRECTION,
    Bloc,
    Lecon,
    charger_lecons,
    contient_la_reponse,
    verifier_reponse,
)
from jules.modules.base import Module
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.cours")

ESPACE = "cours"
MODE = "cours"
STATUTS_CONNUS = ("compris", "en_cours", "bloque", "acquis")
BLOCS_SANS_TENTATIVE = ("texte", "objectifs", "exemple", "outil")
BLOCS_AVEC_TENTATIVE = ("exercice", "question_ouverte", "synthese")

ESTIMATION_TEXTE = "Cet état est estimé par l'IA à partir de tes échanges avec Jules : il peut se tromper."
QUESTION_DE_REPLI = "Qu'est-ce qui te fait penser ça ? Reprends l'énoncé étape par étape."
RAPPEL_GARDE_FOU = (
    "Règle absolue : ne donne JAMAIS la réponse ni un calcul qui y mène directement, même partiellement. "
    "Réponds par UNE seule question qui fait avancer l'élève. Tu peux renvoyer à un bloc précédent de "
    "la leçon si utile. Ne rédige jamais la synthèse ou la réponse à sa place."
)


def _texte_bloc(index: int, bloc: Bloc) -> str:
    d = bloc.donnees
    if bloc.type == "exercice":
        lignes = [f"Bloc {index} (exercice, forme {d.get('forme')}) : {d.get('enonce', '')}"]
        lignes.append(
            f"Réponse attendue (à garder pour toi, ne JAMAIS la révéler ni un calcul qui y mène) : {d.get('reponse')!r}"
        )
        if d.get("choix"):
            lignes.append("Choix proposés à l'élève : " + ", ".join(str(c) for c in d["choix"]))
        return "\n".join(lignes)
    if bloc.type == "question_ouverte":
        lignes = [f"Bloc {index} (question ouverte) : {d.get('question', '')}"]
        if d.get("criteres"):
            lignes.append(
                "Critères de relecture (à garder pour toi, ne jamais les citer tels quels) : "
                + "; ".join(str(c) for c in d["criteres"])
            )
        return "\n".join(lignes)
    if bloc.type == "synthese":
        return f"Bloc {index} (synthèse) : consigne donnée à l'élève « {d.get('consigne', '')} »."
    return f"Bloc {index} ({bloc.type})."


class TentativeEntree(BaseModel):
    reponse: Any = None


class Brique(Module):
    id = "cours"
    titre = "Leçon en cours"

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self.ids = [str(i) for i in reglages.get("bibliotheques") or []]
        self._lecons: dict[str, Lecon] | None = None

    # --- catalogue ---------------------------------------------------------
    @property
    def notions_catalogue(self) -> Any:
        module = self.tuteur.module("notions")
        if module is None:
            raise RuntimeError("Le module 'cours' nécessite le module 'notions'")
        return module.catalogue  # type: ignore[attr-defined]  # module 'notions' expose 'catalogue'

    @property
    def lecons(self) -> dict[str, Lecon]:
        """Lecons chargees (une bibliotheque absente ou vide : le module demarre sans lecon)."""
        if self._lecons is None:
            self._lecons = charger_lecons(
                self.tuteur.config.dossier_bibliotheques, self.ids, self.notions_catalogue.notions
            )
        return self._lecons

    def recharger(self) -> None:
        self._lecons = None

    # --- interface -----------------------------------------------------------
    def infos_interface(self) -> dict[str, Any]:
        """Signale a la page eleve qu'un lien vers /cours doit s'afficher (voir eleve.js).

        `bool(self.lecons)` : au moins une lecon chargee et valide, sinon le module est actif
        mais n'a rien a proposer (bibliotheque absente ou toutes les lecons ecartees).
        """
        return {"cours": bool(self.lecons)}

    # --- cles de stockage ----------------------------------------------------
    @staticmethod
    def _cle_notion(notion_id: str) -> str:
        return f"notion:{notion_id}"

    @staticmethod
    def _cle_conv(conv_id: str) -> str:
        return f"conv:{conv_id}"

    def _sauver_session(self, session_id: str, etat: dict[str, Any]) -> None:
        self.tuteur.stockage.ecrire_etat(ESPACE, session_id, etat)

    def _session(self, session_id: str) -> tuple[dict[str, Any], Lecon]:
        """Etat et lecon d'une session. Leve KeyError si la session ou sa lecon est introuvable."""
        etat = self.tuteur.stockage.lire_etat(ESPACE, session_id)
        if etat is None:
            raise KeyError(session_id)
        lecon = self.lecons.get(etat["notion"])
        if lecon is None:
            raise KeyError(session_id)
        return etat, lecon

    @staticmethod
    def _bloc_courant(blocs: list[dict[str, Any]]) -> int:
        """Index du premier bloc pas encore resolu ; len(blocs) si la lecon est terminee."""
        return next((i for i, b in enumerate(blocs) if b["etat"] in ("a_faire", "en_cours")), len(blocs))

    def _progression(self, etat: dict[str, Any]) -> dict[str, Any]:
        blocs = etat["blocs"]
        courant = self._bloc_courant(blocs)
        return {
            "bloc_courant": courant,
            "blocs": [
                {"index": i, "etat": b["etat"], "tentatives": b["tentatives"], "indices_vus": b["indices_vus"]}
                for i, b in enumerate(blocs)
            ],
            "termine": courant >= len(blocs),
        }

    # --- parcours ------------------------------------------------------------
    def _derniers_statuts(self) -> dict[tuple[str, str], str]:
        """(matiere, notion) en casefold -> dernier statut connu (le plus recent d'abord)."""
        statuts: dict[tuple[str, str], str] = {}
        for ev in self.tuteur.stockage.evenements("suivi", limite=2000):
            d = ev["donnees"]
            if not d.get("notion") or not d.get("matiere"):
                continue
            cle = (str(d["matiere"]).casefold(), str(d["notion"]).casefold())
            if cle not in statuts and d.get("statut") in STATUTS_CONNUS:
                statuts[cle] = d["statut"]
        return statuts

    def parcours(self, matiere_id: str | None = None) -> dict[str, Any]:
        cat = self.notions_catalogue
        matieres = cat.matieres()
        if not matieres:
            return {"matieres": [], "matiere": "", "notions": [], "estimation": ESTIMATION_TEXTE}
        ids_dispo = {mid for mid, _, _ in matieres}
        matiere_use = matiere_id if matiere_id in ids_dispo else matieres[0][0]
        _, nom_matiere, notions = next(m for m in matieres if m[0] == matiere_use)
        statuts = self._derniers_statuts()
        resultat_notions = []
        for n in notions:
            cle = (nom_matiere.casefold(), n.titre.casefold())
            resultat_notions.append(
                {
                    "id": n.id,
                    "titre": n.titre,
                    "chapitre": n.chapitre,
                    "etat": statuts.get(cle, "a_venir"),
                    "lecon": n.id in self.lecons,
                }
            )
        return {
            "matieres": [{"id": mid, "nom": nom} for mid, nom, _ in matieres],
            "matiere": matiere_use,
            "notions": resultat_notions,
            "estimation": ESTIMATION_TEXTE,
        }

    # --- ouverture / reprise ---------------------------------------------------
    def ouvrir(self, notion_id: str) -> dict[str, Any]:
        lecon = self.lecons.get(notion_id)
        if lecon is None:
            raise KeyError(notion_id)
        stockage = self.tuteur.stockage
        session_id = stockage.lire_etat(ESPACE, self._cle_notion(notion_id))
        etat = stockage.lire_etat(ESPACE, session_id) if session_id else None
        if not etat or etat.get("termine"):
            conv = stockage.creer_conversation(MODE)
            stockage.renommer(conv.id, lecon.titre)
            session_id = uuid.uuid4().hex[:12]
            etat = {
                "notion": notion_id,
                "conversation": conv.id,
                "blocs": [{"etat": "a_faire", "tentatives": 0, "indices_vus": 0} for _ in lecon.blocs],
                "termine": False,
            }
            self._sauver_session(session_id, etat)
            stockage.ecrire_etat(ESPACE, self._cle_notion(notion_id), session_id)
            stockage.ecrire_etat(ESPACE, self._cle_conv(conv.id), session_id)
        return {
            "session": session_id,
            "conversation": etat["conversation"],
            "lecon": lecon.publique(),
            "progression": self._progression(etat),
        }

    # --- reaction de Jules (garde-fou anti-fuite) ----------------------------
    def _reagir(self, conv_id: str, message_eleve: str, bloc: Bloc) -> str:
        """Fait reagir Jules a une tentative fausse ; garantit qu'aucune reponse fuitee ne devient
        la reponse renvoyee ni la derniere entree de la conversation (voir docs/COURS-CONTRAT.md)."""
        bot1 = self.tuteur.echanger(conv_id, message_eleve)
        if not contient_la_reponse(bot1.texte, bloc):
            return bot1.texte
        journal.warning("Reponse de Jules ecartee (contenait la reponse) : %s", bot1.texte[:200])
        conv = self.tuteur.stockage.conversation(conv_id)
        if conv is None:
            raise KeyError(conv_id)
        systeme = self.tuteur.systeme(conv)
        tours = self.tuteur.tours(conv)[:-1]  # sans la reponse fuitee : un seul nouvel essai
        nouvelle = self.tuteur.llm.repondre(systeme, tours, "principal")
        if contient_la_reponse(nouvelle, bloc):
            nouvelle = QUESTION_DE_REPLI
        bot2 = self.tuteur.stockage.ajouter_message(conv_id, Message(role="bot", texte=nouvelle))
        conv.messages.append(bot2)
        eleve_msg = conv.messages[-3]
        self.tuteur._lancer_apres_echange(conv, eleve_msg, bot2)
        return nouvelle

    def _relire(self, conv_id: str, message_eleve: str) -> str:
        return self.tuteur.echanger(conv_id, message_eleve).texte

    # --- fin de lecon -----------------------------------------------------------
    def _finaliser_si_besoin(self, etat: dict[str, Any], lecon: Lecon) -> None:
        if etat.get("termine"):
            return
        if self._bloc_courant(etat["blocs"]) < len(etat["blocs"]):
            return
        etat["termine"] = True
        a_revoir = any(b["etat"] == "a_revoir" for b in etat["blocs"])
        statut = "en_cours" if a_revoir else "compris"
        notion = self.notions_catalogue.notion(etat["notion"])
        nom_matiere = notion.nom_matiere if notion else lecon.matiere
        titre_notion = notion.titre if notion else lecon.titre
        resume = (
            f"Leçon « {lecon.titre} » terminée, un point à revoir."
            if a_revoir
            else f"Leçon « {lecon.titre} » terminée."
        )
        self.tuteur.stockage.ajouter_evenement(
            "suivi",
            {"matiere": nom_matiere, "notion": titre_notion, "statut": statut, "resume": resume, "titre": lecon.titre},
            etat["conversation"],
        )

    # --- tentative / indice / fait --------------------------------------------
    def tentative(self, session_id: str, index: int, reponse: Any) -> dict[str, Any]:
        etat, lecon = self._session(session_id)
        if not 0 <= index < len(lecon.blocs):
            raise IndexError(index)
        bloc = lecon.blocs[index]
        if bloc.type not in BLOCS_AVEC_TENTATIVE:
            raise ValueError("Ce bloc n'attend pas de réponse")
        etat["bloc_actif"] = index
        bstate = etat["blocs"][index]
        bstate["tentatives"] += 1
        conv_id = etat["conversation"]
        texte_reponse = "" if reponse is None else str(reponse)
        message_eleve = f"📝 Ma réponse (bloc {index}) : {texte_reponse}"
        juste = verifier_reponse(bloc, reponse)
        explication: str | None = None
        jules_texte: str | None = None
        if juste is True:
            self.tuteur.stockage.ajouter_message(conv_id, Message(role="eleve", texte=message_eleve))
            bstate["etat"] = "reussi"
            explication = bloc.donnees.get("explication")
        elif juste is False:
            if bstate["tentatives"] >= TENTATIVES_AVANT_CORRECTION:
                self.tuteur.stockage.ajouter_message(conv_id, Message(role="eleve", texte=message_eleve))
                bstate["etat"] = "a_revoir"
                explication = bloc.donnees.get("explication")
            else:
                bstate["etat"] = "en_cours"
                self._sauver_session(session_id, etat)  # bloc_actif doit etre lu par contribution()
                jules_texte = self._reagir(conv_id, message_eleve, bloc)
        else:  # question_ouverte, synthese : pas de correction automatique
            bstate["etat"] = "fait"
            self._sauver_session(session_id, etat)  # bloc_actif doit etre lu par contribution()
            jules_texte = self._relire(conv_id, message_eleve)
        self._finaliser_si_besoin(etat, lecon)
        self._sauver_session(session_id, etat)
        return {
            "juste": juste,
            "tentatives": bstate["tentatives"],
            "explication": explication,
            "jules": jules_texte,
            "progression": self._progression(etat),
        }

    def indice(self, session_id: str, index: int) -> dict[str, Any]:
        etat, lecon = self._session(session_id)
        if not 0 <= index < len(lecon.blocs):
            raise IndexError(index)
        bloc = lecon.blocs[index]
        bstate = etat["blocs"][index]
        indices = bloc.donnees.get("indices") or []
        if bstate["indices_vus"] < len(indices):
            indice_texte = str(indices[bstate["indices_vus"]])
            bstate["indices_vus"] += 1
            if bstate["etat"] == "a_faire":
                bstate["etat"] = "en_cours"
        else:
            indice_texte = None
        restants = max(0, len(indices) - bstate["indices_vus"])
        self._sauver_session(session_id, etat)
        return {"indice": indice_texte, "restants": restants, "progression": self._progression(etat)}

    def fait(self, session_id: str, index: int) -> dict[str, Any]:
        etat, lecon = self._session(session_id)
        if not 0 <= index < len(lecon.blocs):
            raise IndexError(index)
        bloc = lecon.blocs[index]
        if bloc.type not in BLOCS_SANS_TENTATIVE:
            raise ValueError("Ce bloc attend une tentative, pas seulement une lecture")
        etat["blocs"][index]["etat"] = "fait"
        self._finaliser_si_besoin(etat, lecon)
        self._sauver_session(session_id, etat)
        return {"progression": self._progression(etat)}

    # --- contrat de module -----------------------------------------------------
    def contribution(self, conv: Conversation) -> str | None:
        if conv.mode != MODE:
            return None
        session_id = self.tuteur.stockage.lire_etat(ESPACE, self._cle_conv(conv.id))
        if not session_id:
            return None
        etat = self.tuteur.stockage.lire_etat(ESPACE, session_id)
        if not etat:
            return None
        lecon = self.lecons.get(etat["notion"])
        if lecon is None:
            return None
        idx = etat.get("bloc_actif")
        if idx is None or not 0 <= idx < len(lecon.blocs):
            idx = self._bloc_courant(etat["blocs"])
        if idx >= len(lecon.blocs):
            return f"Leçon « {lecon.titre} » terminée : félicite brièvement l'élève s'il t'écrit encore."
        bloc = lecon.blocs[idx]
        bstate = etat["blocs"][idx]
        return "\n\n".join(
            [
                f"Leçon en cours : « {lecon.titre} » ({lecon.matiere}).",
                _texte_bloc(idx, bloc),
                f"Tentatives déjà faites sur ce bloc : {bstate['tentatives']}. "
                f"Indices déjà donnés : {bstate['indices_vus']}.",
                RAPPEL_GARDE_FOU,
            ]
        )

    # --- routes eleve ---------------------------------------------------------
    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/parcours")
        def parcours_route(matiere: str | None = None) -> dict[str, Any]:
            return self.parcours(matiere)

        @routeur.post("/lecons/{notion_id}/ouvrir")
        def ouvrir_route(notion_id: str) -> dict[str, Any]:
            try:
                return self.ouvrir(notion_id)
            except KeyError as err:
                raise HTTPException(404, "Aucune leçon pour cette notion") from err

        @routeur.get("/sessions/{session_id}")
        def lire_session(session_id: str) -> dict[str, Any]:
            try:
                etat, lecon = self._session(session_id)
            except KeyError as err:
                raise HTTPException(404, "Session introuvable") from err
            return {
                "session": session_id,
                "conversation": etat["conversation"],
                "lecon": lecon.publique(),
                "progression": self._progression(etat),
            }

        @routeur.post("/sessions/{session_id}/blocs/{index}/tentative")
        def tentative_route(session_id: str, index: int, entree: TentativeEntree) -> dict[str, Any]:
            try:
                return self.tentative(session_id, index, entree.reponse)
            except KeyError as err:
                raise HTTPException(404, "Session introuvable") from err
            except IndexError as err:
                raise HTTPException(404, "Bloc introuvable") from err
            except ValueError as err:
                raise HTTPException(400, str(err)) from err

        @routeur.post("/sessions/{session_id}/blocs/{index}/indice")
        def indice_route(session_id: str, index: int) -> dict[str, Any]:
            try:
                return self.indice(session_id, index)
            except KeyError as err:
                raise HTTPException(404, "Session introuvable") from err
            except IndexError as err:
                raise HTTPException(404, "Bloc introuvable") from err

        @routeur.post("/sessions/{session_id}/blocs/{index}/fait")
        def fait_route(session_id: str, index: int) -> dict[str, Any]:
            try:
                return self.fait(session_id, index)
            except KeyError as err:
                raise HTTPException(404, "Session introuvable") from err
            except IndexError as err:
                raise HTTPException(404, "Bloc introuvable") from err
            except ValueError as err:
                raise HTTPException(400, str(err)) from err

        return routeur
