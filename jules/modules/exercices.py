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
import random
from dataclasses import asdict
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jules.bibliotheques import dossier_bibliotheque
from jules.fiches.correction import ILLISIBLE, TYPES_AUTO
from jules.fiches.parcours import Etat, choisir, indice_demande, presenter, repondre
from jules.fiches.parcours import exercice as exercice_de
from jules.fiches.schema import est_v2, servable_sans_ia
from jules.generateurs import GENERATEURS, serie_generee
from jules.modules.base import Module
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.exercices")

ESPACE = "exercices"
MODE = "exercice"
REPONSE_MAX = 300  # au-dela, la reponse est coupee avant meme d'etre lue par le correcteur
GRAINE_MAX = 10**9

TRANSITION_REUSSI = "\n\nOn continue.\n\n"
TRANSITION_ECHEC = "\n\nOn passe au suivant.\n\n"
MESSAGE_FIN_TOUT_REUSSI = "Bravo, tu as trouvé tous les exercices de cette série !"
MESSAGE_FIN_PARTIEL = "C'est fini pour cette série : ce qui n'a pas tenu, on le retravaillera."
MESSAGE_APRES_FIN = "Cette série d'exercices est terminée. Lance-en une nouvelle depuis l'écran d'accueil."
DEMANDE_INDICE = "Je voudrais un indice."
PLUS_D_INDICE = "Tu as déjà tous mes indices : essaie une réponse, même incomplète, je te dirai ce qui va."


ELEMENTS_MAX = 20  # une liste ou des paires plus longues ne viennent pas d'un exercice de fiche
ELEMENT_MAX = 100


class ReponseEntree(BaseModel):
    reponse: str | list[str] | dict[str, str]


def lire_reponse_structuree(reponse: Any) -> tuple[Any, str]:
    """(reponse telle que le correcteur la lit, texte ecrit dans l'historique). Tailles bornees."""
    if isinstance(reponse, str):
        texte = reponse[:REPONSE_MAX]
        return texte, texte
    if isinstance(reponse, list):
        if len(reponse) > ELEMENTS_MAX or any(len(x) > ELEMENT_MAX for x in reponse):
            raise HTTPException(422, "réponse trop longue")
        return list(reponse), ", ".join(reponse)
    if len(reponse) > ELEMENTS_MAX or any(len(k) > ELEMENT_MAX or len(v) > ELEMENT_MAX for k, v in reponse.items()):
        raise HTTPException(422, "réponse trop longue")
    return dict(reponse), ", ".join(f"{k}-{v}" for k, v in reponse.items())


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
        # Reponse structuree (liste, paires) deposee par la route /repondre juste avant Tuteur.echanger :
        # repondre_a_la_place la corrige telle quelle au lieu du texte affiche dans l'historique.
        self._reponses_structurees: dict[str, Any] = {}

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
        return self._ouvrir(notion_id, fiche, {})

    def commencer_generee(self, notion_id: str, graine: int | None = None) -> dict[str, Any]:
        """Une serie d'exercices fabriques par le generateur de la notion : autres nombres a chaque serie."""
        if notion_id not in GENERATEURS:
            raise KeyError(notion_id)
        if graine is None:
            graine = random.randrange(GRAINE_MAX)  # noqa: S311 - pas de cryptographie, juste une serie differente
        connue = self.fiches.get(notion_id) or {}
        fiche = serie_generee(notion_id, graine, prerequis=list(connue.get("prerequis") or []))
        return self._ouvrir(notion_id, fiche, {"graine": graine, "fiche": fiche})

    def _ouvrir(self, notion_id: str, fiche: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
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
            **extra,
        }
        self._sauver(conv.id, donnees)
        vue = presenter(premier)
        stockage.ajouter_message(conv.id, Message(role="bot", texte=_rendre_exercice(vue)))
        total = sum(1 for e in fiche.get("exercices") or [] if e.get("type") in TYPES_AUTO)
        return {"conversation": conv.id, "exercice": vue, "total": total}

    def _fiche_de(self, donnees: dict[str, Any]) -> dict[str, Any] | None:
        """La serie generee rangee avec la conversation, sinon la fiche figee de la notion."""
        return donnees.get("fiche") or self.fiches.get(donnees["notion"])

    # --- contrat de module : reponse decidee par le code, jamais par le modele ---------------------
    def repondre_a_la_place(self, conv: Conversation, eleve: Message) -> str | None:
        if conv.mode != MODE:
            return None
        donnees = self._lire(conv.id)
        if donnees is None:
            return None
        if donnees.get("fini"):
            return MESSAGE_APRES_FIN
        fiche = self._fiche_de(donnees)
        if fiche is None:
            journal.error("Fiche %s introuvable pour la conversation %s", donnees["notion"], conv.id)
            return None
        etat = Etat(**donnees["etat"])
        if conv.id in self._reponses_structurees:
            reponse: Any = self._reponses_structurees.pop(conv.id)
        else:
            reponse = (eleve.texte or "")[:REPONSE_MAX]
        pieges_avant, paliers_avant = len(etat.pieges_dits), etat.paliers_donnes
        retour = repondre(fiche, etat, reponse)
        donnees["etat"] = asdict(etat)
        if retour.observation:
            self._observer(conv.id, donnees["notion"], etat.exercice, retour.observation)
        message = retour.message
        # Vue structuree du meme tour, pour la fiche (route /repondre) : decidee ici, par le code seul.
        if not retour.verdict.auto:
            verdict = "relire"
        elif retour.verdict.diagnostic == ILLISIBLE:
            verdict = "illisible"
        elif retour.verdict.juste:
            verdict = "juste"
        elif not retour.termine and etat.paliers_donnes > paliers_avant:
            verdict = "indice"
        else:
            verdict = "faux"
        dernier: dict[str, Any] = {
            "verdict": verdict,
            "message": retour.message,
            "palier": etat.paliers_donnes,
            "indice": retour.message if verdict == "indice" else None,
            "piege": retour.message if len(etat.pieges_dits) > pieges_avant else None,
            "correction": None,
            # « Pourquoi ? » apres une reponse juste : la solution redigee de la fiche (plus un secret une
            # fois l'exercice reussi). Jamais avant le verdict.
            "pourquoi": (str(exercice_de(fiche, etat.exercice).get("solution") or "").strip() or None)
            if verdict == "juste"
            else None,
            "termine": retour.termine,
            "a_revoir": [],
            "suivant": None,
            "bilan": None,
        }
        if retour.termine:
            donnees["faits"].append(etat.exercice)
            if etat.reussi:
                donnees["reussis"].append(etat.exercice)
                if etat.paliers_donnes or etat.pieges_dits:
                    donnees.setdefault("avec_aide", []).append(etat.exercice)
            else:
                dernier["correction"] = str(exercice_de(fiche, etat.exercice).get("solution") or "").strip() or None
                if retour.prerequis:
                    titres = [n.titre for i in retour.prerequis if (n := self.notions_catalogue.notion(i))]
                    if titres:
                        dernier["a_revoir"] = titres
                        message += "\n\nÀ revoir avant de continuer : " + ", ".join(titres) + "."
            suivant = choisir(fiche, set(donnees["faits"]))
            if suivant is None:
                donnees["fini"] = True
                self._finaliser(conv.id, donnees)
                tout = len(donnees["reussis"]) == len(donnees["faits"])
                message += "\n\n" + (MESSAGE_FIN_TOUT_REUSSI if tout else MESSAGE_FIN_PARTIEL)
                avec = len(donnees.get("avec_aide", []))
                dernier["bilan"] = {
                    "faits": len(donnees["faits"]),
                    "reussis": len(donnees["reussis"]),
                    "avec_indice": avec,
                    "sans_indice": len(donnees["reussis"]) - avec,
                    "message": MESSAGE_FIN_TOUT_REUSSI if tout else MESSAGE_FIN_PARTIEL,
                }
            else:
                donnees["exercice"] = suivant["id"]
                donnees["etat"] = asdict(Etat(suivant["id"]))
                transition = TRANSITION_REUSSI if etat.reussi else TRANSITION_ECHEC
                vue = presenter(suivant)
                dernier["suivant"] = vue
                message += transition + _rendre_exercice(vue)
        donnees["dernier"] = dernier
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

        @routeur.post("/{conv_id}/repondre")
        def repondre_structure(conv_id: str, entree: ReponseEntree) -> dict[str, Any]:
            """Une reponse donnee dans la fiche (boutons, ordre, paires) : corrigee par le code comme dans le
            chat, par le meme Tuteur.echanger (historique, suivi), puis rendue en donnees. Ni la reponse
            attendue ni la solution ne partent avant le verdict ; aucun appel au modele de langage."""
            conv = self.tuteur.stockage.conversation(conv_id)
            donnees = self._lire(conv_id) if conv is not None else None
            if conv is None or conv.mode != MODE or donnees is None:
                raise HTTPException(404, "Pas de série d'exercices en cours ici")
            if donnees.get("fini"):
                return {"verdict": "fini", "message": MESSAGE_APRES_FIN, "palier": 0, "indice": None, "piege": None,
                        "correction": None, "pourquoi": None, "termine": True, "a_revoir": [], "suivant": None,
                        "bilan": None}
            if self._fiche_de(donnees) is None:
                raise HTTPException(409, "Fiche de la série introuvable")
            reponse, texte = lire_reponse_structuree(entree.reponse)
            self._reponses_structurees[conv_id] = reponse
            try:
                self.tuteur.echanger(conv_id, texte)
            finally:
                self._reponses_structurees.pop(conv_id, None)
            apres = self._lire(conv_id) or {}
            dernier = apres.get("dernier")
            if not dernier:
                raise HTTPException(500, "Réponse non corrigée")
            return dict(dernier)

        @routeur.post("/{conv_id}/indice")
        def demander_indice(conv_id: str) -> dict[str, Any]:
            """Coup de pouce demande avant de repondre (idee D, docs/veille/synthese-ui-dinobot-marche.md) :
            le palier suivant de l'echelle de la fiche, decide par le code, sans IA. Ecrit dans la
            conversation (Jules voit la meme chose que l'eleve) et compte comme une aide dans le bilan."""
            conv = self.tuteur.stockage.conversation(conv_id)
            donnees = self._lire(conv_id) if conv is not None else None
            if conv is None or conv.mode != MODE or donnees is None or donnees.get("fini"):
                raise HTTPException(404, "Pas d'exercice en cours ici")
            fiche = self._fiche_de(donnees)
            if fiche is None:
                raise HTTPException(409, "Fiche de la série introuvable")
            etat = Etat(**donnees["etat"])
            texte = indice_demande(fiche, etat)
            donnees["etat"] = asdict(etat)
            self._sauver(conv_id, donnees)
            stockage = self.tuteur.stockage
            stockage.ajouter_message(conv_id, Message("eleve", DEMANDE_INDICE))
            stockage.ajouter_message(conv_id, Message("bot", texte or PLUS_D_INDICE))
            return {"indice": texte, "palier": etat.paliers_donnes, "message": texte or PLUS_D_INDICE}

        @routeur.get("/{conv_id}/etat")
        def etat_serie(conv_id: str) -> dict[str, Any]:
            """Reprise d'une serie dans la fiche : l'exercice en cours (sans la reponse) et l'avancee."""
            conv = self.tuteur.stockage.conversation(conv_id)
            donnees = self._lire(conv_id) if conv is not None else None
            if conv is None or conv.mode != MODE or donnees is None:
                raise HTTPException(404, "Pas de série d'exercices en cours ici")
            fiche = self._fiche_de(donnees)
            en_cours = None
            if fiche is not None and not donnees.get("fini"):
                en_cours = presenter(exercice_de(fiche, donnees["exercice"]))
            total = sum(1 for e in (fiche or {}).get("exercices") or [] if e.get("type") in TYPES_AUTO)
            return {"notion": donnees["notion"], "exercice": en_cours, "faits": len(donnees["faits"]),
                    "reussis": len(donnees["reussis"]), "total": total, "fini": bool(donnees.get("fini")),
                    "palier": int((donnees.get("etat") or {}).get("paliers_donnes", 0))}

        @routeur.post("/{notion_id}/generer")
        def lancer_generee(notion_id: str, graine: int | None = None) -> dict[str, Any]:
            if graine is not None and not 0 <= graine < GRAINE_MAX:
                raise HTTPException(422, "graine hors limites")
            try:
                return self.commencer_generee(notion_id, graine)
            except KeyError as err:
                raise HTTPException(404, "Pas de générateur d'exercices pour cette notion") from err

        return routeur

    # --- interface ---------------------------------------------------------------------------------
    def _notions_disponibles(self) -> list[dict[str, Any]]:
        resultat = []
        for notion_id in sorted(set(self.fiches) | set(GENERATEURS)):
            notion = self.notions_catalogue.notion(notion_id)
            if notion is None:
                continue
            fiche = self.fiches.get(notion_id)
            nb = sum(1 for e in (fiche or {}).get("exercices") or [] if e.get("type") in TYPES_AUTO)
            resultat.append(
                {
                    "id": notion_id,
                    "titre": notion.titre,
                    "matiere": notion.nom_matiere,
                    "nb": nb,
                    "generateur": notion_id in GENERATEURS,
                }
            )
        return resultat

    def infos_interface(self) -> dict[str, Any]:
        return {"exercices": self._notions_disponibles()}
