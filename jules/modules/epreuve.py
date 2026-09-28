"""Module 'epreuve' : l'epreuve sans aide, quelques jours apres.

Le suivi dit ce qui se passe pendant qu'on utilise Jules, pas ce que l'eleve a retenu. Ce module
reprend, quelques jours plus tard et sans aide, les notions marquees comprises, et regarde ce qui
a tenu :
  - ce qui a tenu devient "acquis" ;
  - ce qui n'a pas tenu repasse "en cours".

Deroulement :
  1. candidates() choisit les notions dont le dernier etat connu est "compris", vieux d'au moins
     `delai_jours` et d'au plus `fenetre_jours` (les plus anciennes d'abord, `notions_max` au plus).
     Une epreuve par jour au plus : l'invitation disparait des le lancement.
  2. L'eleve voit la proposition sur l'ecran d'accueil et la lance (POST /api/eleve/epreuve/commencer).
     La conversation est en mode "epreuve" (consignes/modes/epreuve.md, mode cache de la grille).
  3. Quand Jules ecrit « Épreuve terminée. », le modele rapide lit le bilan et renvoie, notion par
     notion, tenu ou pas. Le module ecrit alors des evenements 'suivi' (acquis / en_cours) et un
     evenement 'epreuve' que le bilan du soir reprend.

Ce n'est pas une etude : une mesure a l'echelle d'un eleve, faite par une IA qui peut se tromper.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException

from jules.lecons import contient_la_reponse
from jules.llm.base import Tour
from jules.modules.base import Module, extraire_json
from jules.modules.suivi import dernier_statut, evenement_suivi
from jules.stockage import Conversation, Message
from jules.texte import remplir

journal = logging.getLogger("jules.epreuve")

ESPACE = "epreuve"
MODE = "epreuve"
TITRE = "Épreuve sans aide"
MARQUE_FIN = "preuve terminée"  # « Épreuve terminée. » (sans le É, pour tolerer « EPREUVE TERMINÉE »)

PRESENTATION = (
    "Petite épreuve sans aide, {prenom} : {nombre} question(s) sur des notions que tu as travaillées "
    "il y a quelques jours ({liste}).\n\n"
    "Je ne t'aide pas pendant l'épreuve, et je corrige tout à la fin. Ce n'est pas noté : "
    "ce qui n'a pas tenu, on le retravaillera, c'est tout.\n\n"
    "Écris « prêt » quand tu veux commencer."
)

CONSIGNE_BILAN = """Tu lis le bilan final d'une épreuve sans aide passée par un élève avec son tuteur IA.
Réponds UNIQUEMENT par un objet JSON, sans texte autour :
{"resultats": [{"notion": "...", "tenu": true}]}
- notion : le libellé EXACT, tel qu'il est écrit dans la liste fournie.
- tenu : true si l'élève a répondu juste sans aide, false sinon (réponse fausse, pas de réponse, abandon).
Une entrée par notion de la liste. Ne juge que d'après la conversation fournie."""

# Heuristique a posteriori, deterministe et volontairement etroite (docs/EPREUVE-PROTOCOLE.md) :
# des formulations qui, dans un message du bot PENDANT l'epreuve (avant le bilan final), donnent
# une aide explicite plutot que de simplement noter la reponse. Le protocole (consignes/modes/epreuve.md)
# demande a Jules de ne jamais aider ; ceci detecte les cas ou le modele n'a pas suivi la consigne.
# Volontairement conservateur : ces phrases suffisent a signaler une aide, mais leur absence ne
# garantit pas qu'il n'y en a pas eu (limite documentee, pas corrigee par du texte libre).
FORMULATIONS_AIDE = (
    "la réponse est",
    "la reponse est",
    "voici la solution",
    "voici la réponse",
    "il faut faire",
    "il faut d'abord",
    "je te donne la réponse",
    "je te donne la reponse",
    "un indice :",
    "un petit indice",
    "astuce :",
)


def aide_detectee_dans(bot_textes: list[str]) -> bool:
    """Vrai si un message du bot (hors bilan final) contient une formulation d'aide explicite.

    Heuristique a posteriori minimale (voir FORMULATIONS_AIDE) : cherche des tournures deterministes.
    Ne detecte ni une aide implicite (question orientee) ni une aide qui evite ces tournures : c'est
    une limite connue, documentee dans docs/EPREUVE-PROTOCOLE.md, pas un bug a corriger ici en
    devinant davantage (mieux vaut rater une aide que declasser 'acquis' a tort).
    """
    for texte in bot_textes:
        bas = texte.casefold()
        if any(formule in bas for formule in FORMULATIONS_AIDE):
            return True
    return False


def libelle(notion: dict[str, str]) -> str:
    return f"{notion['matiere']} : {notion['notion']}"


def candidates(
    evenements: list[dict[str, Any]], aujourdhui: date, delai_jours: int, fenetre_jours: int, maximum: int
) -> list[dict[str, str]]:
    """Notions dont le DERNIER etat connu est "compris", assez ancien pour etre repris sans aide.

    `evenements` : evenements 'suivi', du plus recent au plus ancien (ordre de Stockage.evenements).
    Passe par `dernier_statut` (jules.modules.suivi) comme tout autre lecteur du dernier etat d'une
    notion, pour la meme raison : un 'acquis' recent ne doit pas etre invisible ici a tort si un
    'compris' plus ancien existait, meme si dans ce cas precis 'acquis' n'est de toute facon pas
    candidat (seul 'compris' l'est).
    """
    plus_recent = (aujourdhui - timedelta(days=delai_jours)).isoformat()
    plus_ancien = (aujourdhui - timedelta(days=fenetre_jours)).isoformat()
    retenues: list[tuple[str, dict[str, str]]] = []
    for _cle, ev in dernier_statut(evenements).items():
        d = ev["donnees"]
        if d.get("statut") != "compris":
            continue
        jour = ev["horodatage"][:10]
        if plus_ancien <= jour <= plus_recent:
            notion = {"matiere": str(d.get("matiere") or "Autre"), "notion": str(d["notion"]), "jour": jour}
            retenues.append((ev["horodatage"], notion))
    # les plus anciennes d'abord (les plus exposees a l'oubli) ; a egalite, l'ordre alphabetique du libelle
    retenues.sort(key=lambda r: (r[0], libelle(r[1])))
    return [n for _, n in retenues[:maximum]]


def lire_resultats(brut: str, notions: list[dict[str, str]]) -> dict[str, bool]:
    """Resultats du modele, ramenes aux libelles de l'epreuve (les libelles inconnus sont ignores)."""
    objet = extraire_json(brut) or {}
    par_cle = {libelle(n).casefold(): libelle(n) for n in notions}
    resultats: dict[str, bool] = {}
    for r in objet.get("resultats") or []:
        if not isinstance(r, dict) or not isinstance(r.get("tenu"), bool):
            continue
        cle = par_cle.get(str(r.get("notion") or "").strip().casefold())
        if cle:
            resultats[cle] = r["tenu"]
    return resultats


class Brique(Module):
    id = "epreuve"
    titre = "Épreuve sans aide en cours"

    def aujourdhui(self) -> date:
        return datetime.now().astimezone().date()

    def candidates(self) -> list[dict[str, str]]:
        derniere = self.tuteur.stockage.lire_etat(ESPACE, "derniere") or {}
        if derniere.get("jour") == self.aujourdhui().isoformat():
            return []  # une epreuve par jour au plus
        modele = self.tuteur.module("modele_eleve")
        if modele is not None and hasattr(modele, "notions_a_reviser"):
            # modele de l'eleve actif : l'epreuve arrive quand la retention predite passe sous la cible (§5.4)
            choix: list[dict[str, str]] = modele.notions_a_reviser(int(self.reglages.get("notions_max", 3)))
            return choix
        return candidates(
            self.tuteur.stockage.evenements("suivi", limite=2000),
            self.aujourdhui(),
            int(self.reglages.get("delai_jours", 3)),
            int(self.reglages.get("fenetre_jours", 30)),
            int(self.reglages.get("notions_max", 3)),
        )

    def epreuve(self, conv_id: str) -> dict[str, Any] | None:
        return self.tuteur.stockage.lire_etat(ESPACE, conv_id)

    def commencer(self) -> dict[str, Any]:
        notions = self.candidates()
        if not notions:
            raise ValueError("Aucune notion à reprendre pour l'instant")
        stockage = self.tuteur.stockage
        conv = stockage.creer_conversation(MODE)
        stockage.renommer(conv.id, TITRE)
        stockage.ecrire_etat(ESPACE, conv.id, {"notions": notions, "terminee": False})
        stockage.ecrire_etat(ESPACE, "derniere", {"jour": self.aujourdhui().isoformat(), "conversation": conv.id})
        profil = self.tuteur.profil()
        presentation = remplir(
            PRESENTATION,
            {**profil.variables(), "nombre": str(len(notions)), "liste": ", ".join(n["notion"] for n in notions)},
            profil.genre,
        )
        return {"id": conv.id, "mode": MODE, "titre": TITRE, "presentation": presentation}

    # --- contrat de module ---------------------------------------------------
    def contribution(self, conv: Conversation) -> str | None:
        epreuve = self.epreuve(conv.id) if conv.mode == MODE else None
        if not epreuve:
            return None
        lignes = [f"- {libelle(n)} (marquée comprise le {n['jour']})" for n in epreuve["notions"]]
        return "Notions de l'épreuve, dans l'ordre (reprends ces libellés exacts dans le bilan) :\n" + "\n".join(lignes)

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        if conv.mode != MODE or MARQUE_FIN not in bot.texte.casefold():
            return
        epreuve = self.epreuve(conv.id)
        if not epreuve or epreuve.get("terminee"):
            return
        notions = epreuve["notions"]
        echanges = "\n".join(f"{'ÉLÈVE' if m.role == 'eleve' else 'TUTEUR'} : {m.texte[:1500]}" for m in conv.messages)
        liste = "\n".join(f"- {libelle(n)}" for n in notions)
        tours = [Tour(role="user", texte=f"Notions de l'épreuve :\n{liste}\n\nConversation :\n{echanges}")]
        brut = self.tuteur.llm.repondre(CONSIGNE_BILAN, tours, "rapide")
        resultats = lire_resultats(brut, notions)
        if not resultats:
            journal.warning("Bilan d'epreuve illisible : %s", brut[:200])
            return
        # Le bilan final (le message `bot` qui declenche cet appel) donne la correction : c'est prevu
        # par le protocole (consignes/modes/epreuve.md, etape 3), il ne compte pas comme de l'aide.
        # Seuls les messages du bot AVANT ce dernier comptent pour l'heuristique.
        aide = self._aide_detectee(conv, notions)
        self.enregistrer(conv.id, notions, resultats, aide)

    def _aide_detectee(self, conv: Conversation, notions: list[dict[str, str]]) -> bool:
        """Heuristique a posteriori : Jules a-t-il aide pendant l'epreuve (avant le bilan final) ?

        Deux verifications, toutes deux conservatrices (docs/EPREUVE-PROTOCOLE.md) :
          1. des formulations d'aide explicite dans un message du bot (FORMULATIONS_AIDE) ;
          2. si une lecon (module 'cours') porte le meme titre qu'une notion de l'epreuve et a un
             bloc 'exercice', si un message du bot contient la reponse attendue de ce bloc
             (jules.lecons.contient_la_reponse, le meme garde-fou que jules.modules.cours).
        """
        messages_avant_bilan = [m.texte for m in conv.messages[:-1] if m.role == "bot"]
        if aide_detectee_dans(messages_avant_bilan):
            return True
        cours_lecons = self.tuteur.module("cours")
        if cours_lecons is None:
            return False
        titres = {n["notion"].casefold() for n in notions}
        for lecon in cours_lecons.lecons.values():  # type: ignore[attr-defined]
            if lecon.titre.casefold() not in titres:
                continue
            for bloc in lecon.blocs:
                if bloc.type != "exercice":
                    continue
                if any(contient_la_reponse(texte, bloc) for texte in messages_avant_bilan):
                    return True
        return False

    def enregistrer(
        self, conv_id: str, notions: list[dict[str, str]], resultats: dict[str, bool], aide_detectee: bool = False
    ) -> None:
        stockage = self.tuteur.stockage
        tenues: list[str] = []
        pas_tenues: list[str] = []
        for n in notions:
            cle = libelle(n)
            if cle not in resultats:
                continue
            tenu = resultats[cle] and not aide_detectee
            (tenues if tenu else pas_tenues).append(cle)
            if aide_detectee and resultats[cle]:
                resume = "Épreuve : Jules a aidé, résultat non retenu comme acquis."
            elif tenu:
                resume = "Épreuve sans aide : a tenu."
            else:
                resume = "Épreuve sans aide : n'a pas tenu, à retravailler."
            suivi = evenement_suivi(
                matiere=n["matiere"],
                notion=n["notion"],
                statut="acquis" if tenu else "en_cours",
                resume=resume,
                titre=TITRE,
                origine="epreuve",
            )
            stockage.ajouter_evenement("suivi", suivi, conv_id)
        stockage.ajouter_evenement(
            "epreuve",
            {"notions": len(notions), "tenues": tenues, "pas_tenues": pas_tenues, "aide_detectee": aide_detectee},
            conv_id,
        )
        stockage.ecrire_etat(ESPACE, conv_id, {"notions": notions, "terminee": True})

    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/proposition")
        def proposition() -> dict[str, Any]:
            return {"notions": self.candidates()}

        @routeur.post("/commencer")
        def lancer() -> dict[str, Any]:
            try:
                return self.commencer()
            except ValueError as err:
                raise HTTPException(409, str(err)) from err

        return routeur

    def infos_interface(self) -> dict[str, Any]:
        return {"epreuve": {"active": True}}
