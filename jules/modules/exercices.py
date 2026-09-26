"""Module 'exercices' : entrainement sans IA sur les fiches v2 servables sans IA.

Une fiche v2 conforme (docs/FICHES-V2.md, `servable_sans_ia`) se corrige entierement par le code
(jules/fiches/). Ce module la relie a une conversation :
  - infos_interface() liste les notions qui ont une telle fiche, pour l'ecran d'accueil ;
  - POST /api/eleve/exercices/{notion}/commencer ouvre une conversation en mode cache 'exercice' et
    presente le premier exercice ;
  - repondre_a_la_place() (hook du moteur, jules/modules/base.py) corrige chaque reponse, donne le
    piege ou l'indice suivant, enchaine les exercices et ecrit la correction finale. Aucun appel au
    modele de langage n'a lieu tant que la conversation est en mode 'exercice' : le moteur ne recoit
    jamais la main (jules/moteur.py, Tuteur.echanger).

A la fin du dernier exercice, un evenement 'suivi' est ecrit (meme forme que jules/modules/cours.py
`_finaliser_si_besoin`) : l'epreuve sans aide et le bilan du soir le voient comme n'importe quelle
autre notion travaillee.

Reglages (config.yaml) :
  bibliotheques: [fiches-v2-demonstration]   # dossiers de bibliotheque/ contenant des fiches v2
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException

from jules.bibliotheques import dossier_bibliotheque
from jules.fiches.correction import TYPES_AUTO
from jules.fiches.parcours import Etat, choisir, presenter, repondre
from jules.fiches.schema import est_v2, servable_sans_ia
from jules.modules.base import Module
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.exercices")

ESPACE = "exercices"
MODE = "exercice"
REPONSE_MAX = 300  # au-dela, la reponse est coupee avant meme d'etre lue par le correcteur

TRANSITION_REUSSI = "\n\nOn continue.\n\n"
TRANSITION_ECHEC = "\n\nOn passe au suivant.\n\n"
MESSAGE_FIN_TOUT_REUSSI = "Bravo, tu as trouvé tous les exercices de cette série !"
MESSAGE_FIN_PARTIEL = "C'est fini pour cette série : ce qui n'a pas tenu, on le retravaillera."
MESSAGE_APRES_FIN = "Cette série d'exercices est terminée. Lance-en une nouvelle depuis l'écran d'accueil."


def _rendre_exercice(vue: dict[str, Any]) -> str:
    """L'exercice en texte : l'enonce, puis ce qu'il faut manipuler (jamais la reponse)."""
    parties = [str(vue["enonce"]).strip()]
    if "options" in vue:
        parties.append("\n".join(f"{o['id']}) {o['texte']}" for o in vue["options"]))
    if "elements" in vue:
        elements = "\n".join(f"{e['id']}) {e['texte']}" for e in vue["elements"])
        parties.append("À ranger dans le bon ordre :\n" + elements)
    if "gauche" in vue:
        parties.append("À gauche :\n" + "\n".join(f"{e['id']}) {e['texte']}" for e in vue["gauche"]))
        parties.append("À droite :\n" + "\n".join(f"{e['id']}) {e['texte']}" for e in vue["droite"]))
    if vue.get("aide_format"):
        parties.append(str(vue["aide_format"]))
    return "\n\n".join(parties)


class Brique(Module):
    id = "exercices"
    titre = "Exercices sans IA en cours"

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self.ids = [str(i) for i in reglages.get("bibliotheques") or []]
        self._fiches: dict[str, dict[str, Any]] | None = None

    # --- catalogue de notions (module 'notions', pour les titres et le referentiel) ------------
    @property
    def notions_catalogue(self) -> Any:
        module = self.tuteur.module("notions")
        if module is None:
            raise RuntimeError("Le module 'exercices' nécessite le module 'notions'")
        return module.catalogue  # type: ignore[attr-defined]  # module 'notions' expose 'catalogue'

    # --- fiches v2 servables sans IA, chargees une fois -----------------------------------------
    @property
    def fiches(self) -> dict[str, dict[str, Any]]:
        if self._fiches is None:
            self._fiches = self._charger()
        return self._fiches

    def recharger(self) -> None:
        self._fiches = None

    def _charger(self) -> dict[str, dict[str, Any]]:
        notions = self.notions_catalogue.notions
        trouvees: dict[str, dict[str, Any]] = {}
        racines = self.tuteur.config.dossiers_bibliotheques
        for identifiant in self.ids:
            dossier = dossier_bibliotheque(racines, identifiant) / "fiches"
            if not dossier.is_dir():
                continue
            for chemin in sorted(dossier.rglob("*.yaml")):
                try:
                    fiche = yaml.safe_load(chemin.read_text(encoding="utf-8"))
                except (OSError, yaml.YAMLError) as err:
                    journal.error("Fiche %s illisible : %s", chemin, err)
                    continue
                if not isinstance(fiche, dict) or not est_v2(fiche):
                    continue
                notion_id = str(fiche.get("notion") or "")
                if notion_id not in notions:
                    journal.error("Fiche %s : notion %r inconnue du referentiel", chemin.name, notion_id)
                    continue
                if not servable_sans_ia(fiche):
                    journal.error("Fiche %s : pas servable sans IA (etat ou empreinte)", chemin.name)
                    continue
                if notion_id not in trouvees:  # la premiere bibliotheque de la liste l'emporte
                    trouvees[notion_id] = fiche
        return trouvees

    # --- stockage par conversation ---------------------------------------------------------------
    def _lire(self, conv_id: str) -> dict[str, Any] | None:
        return self.tuteur.stockage.lire_etat(ESPACE, conv_id)

    def _sauver(self, conv_id: str, donnees: dict[str, Any]) -> None:
        self.tuteur.stockage.ecrire_etat(ESPACE, conv_id, donnees)

    def _observer(self, conv_id: str, notion_id: str, exercice_id: str, observation: dict[str, Any]) -> None:
        self.tuteur.stockage.ajouter_evenement(
            "observation",
            {
                "notion": notion_id,
                "exercice": exercice_id,
                "capteur": observation["capteur"],
                "valeur": observation["valeur"],
                "poids": observation.get("poids", 1),
                "source": "fiche_v2",
            },
            conv_id,
        )

    def _finaliser(self, conv_id: str, donnees: dict[str, Any]) -> None:
        notion = self.notions_catalogue.notion(donnees["notion"])
        nom_matiere = notion.nom_matiere if notion else ""
        titre_notion = notion.titre if notion else donnees["notion"]
        tout_reussi = bool(donnees["faits"]) and len(donnees["reussis"]) == len(donnees["faits"])
        statut = "compris" if tout_reussi else "en_cours"
        resume = (
            f"Exercices sans IA sur « {titre_notion} » : tous trouvés (avec ou sans indice)."
            if tout_reussi
            else f"Exercices sans IA sur « {titre_notion} » : une partie n'a pas été trouvée, à retravailler."
        )
        self.tuteur.stockage.ajouter_evenement(
            "suivi",
            {"matiere": nom_matiere, "notion": titre_notion, "statut": statut, "resume": resume, "titre": titre_notion},
            conv_id,
        )

    # --- ouverture ---------------------------------------------------------------------------------
    def commencer(self, notion_id: str) -> dict[str, Any]:
        fiche = self.fiches.get(notion_id)
        if fiche is None:
            raise KeyError(notion_id)
        premier = choisir(fiche)
        if premier is None:
            raise ValueError(f"Aucun exercice corrigé sans IA pour {notion_id!r}")
        notion = self.notions_catalogue.notion(notion_id)
        titre = notion.titre if notion else notion_id
        stockage = self.tuteur.stockage
        conv = stockage.creer_conversation(MODE)
        stockage.renommer(conv.id, titre)
        donnees = {
            "notion": notion_id,
            "exercice": premier["id"],
            "etat": asdict(Etat(premier["id"])),
            "faits": [],
            "reussis": [],
            "fini": False,
        }
        self._sauver(conv.id, donnees)
        vue = presenter(premier)
        stockage.ajouter_message(conv.id, Message(role="bot", texte=_rendre_exercice(vue)))
        return {"conversation": conv.id, "exercice": vue}

    # --- contrat de module : reponse decidee par le code, jamais par le modele ---------------------
    def repondre_a_la_place(self, conv: Conversation, eleve: Message) -> str | None:
        if conv.mode != MODE:
            return None
        donnees = self._lire(conv.id)
        if donnees is None:
            return None
        if donnees.get("fini"):
            return MESSAGE_APRES_FIN
        fiche = self.fiches.get(donnees["notion"])
        if fiche is None:
            journal.error("Fiche %s introuvable pour la conversation %s", donnees["notion"], conv.id)
            return None
        etat = Etat(**donnees["etat"])
        reponse_texte = (eleve.texte or "")[:REPONSE_MAX]
        retour = repondre(fiche, etat, reponse_texte)
        donnees["etat"] = asdict(etat)
        if retour.observation:
            self._observer(conv.id, donnees["notion"], etat.exercice, retour.observation)
        message = retour.message
        if retour.termine:
            donnees["faits"].append(etat.exercice)
            if etat.reussi:
                donnees["reussis"].append(etat.exercice)
            elif retour.prerequis:
                titres = [n.titre for i in retour.prerequis if (n := self.notions_catalogue.notion(i))]
                if titres:
                    message += "\n\nÀ revoir avant de continuer : " + ", ".join(titres) + "."
            suivant = choisir(fiche, set(donnees["faits"]))
            if suivant is None:
                donnees["fini"] = True
                self._finaliser(conv.id, donnees)
                message += "\n\n" + (
                    MESSAGE_FIN_TOUT_REUSSI if len(donnees["reussis"]) == len(donnees["faits"]) else MESSAGE_FIN_PARTIEL
                )
            else:
                donnees["exercice"] = suivant["id"]
                donnees["etat"] = asdict(Etat(suivant["id"]))
                transition = TRANSITION_REUSSI if etat.reussi else TRANSITION_ECHEC
                message += transition + _rendre_exercice(presenter(suivant))
        self._sauver(conv.id, donnees)
        return message

    # --- routes eleve ---------------------------------------------------------------------------
    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/notions")
        def notions() -> dict[str, Any]:
            return {"exercices": self._notions_disponibles()}

        @routeur.post("/{notion_id}/commencer")
        def lancer(notion_id: str) -> dict[str, Any]:
            try:
                return self.commencer(notion_id)
            except KeyError as err:
                raise HTTPException(404, "Aucun exercice sans IA pour cette notion") from err
            except ValueError as err:
                raise HTTPException(409, str(err)) from err

        return routeur

    # --- interface ---------------------------------------------------------------------------------
    def _notions_disponibles(self) -> list[dict[str, Any]]:
        resultat = []
        for notion_id, fiche in self.fiches.items():
            notion = self.notions_catalogue.notion(notion_id)
            if notion is None:
                continue
            nb = sum(1 for e in fiche.get("exercices") or [] if e.get("type") in TYPES_AUTO)
            resultat.append({"id": notion_id, "titre": notion.titre, "matiere": notion.nom_matiere, "nb": nb})
        return resultat

    def infos_interface(self) -> dict[str, Any]:
        return {"exercices": self._notions_disponibles()}
