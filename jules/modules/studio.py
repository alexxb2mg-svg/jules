"""Module 'studio' : supports de revision (carte mentale, fiche, quiz, cartes memoire).

L'eleve construit lui-meme un support sur une notion deja vue en cours (le module depend de
'cours', memes principes que 'cours' depend de 'notions'). Jules ne fait jamais que relire ce qui
existe deja : le prompt envoye ne contient jamais mandat d'ecrire a la place de l'eleve
(consignes/modes/studio.md, mode cache, meme famille que consignes/modes/cours.md).

Formats, validation et garde-fous : jules/studio.py (signatures figees par le contrat).
Repetition espacee des cartes memoire : jules/revisions.py.
Format complet de l'API : docs/STUDIO-CONTRAT.md §3.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from jules.lecons import CHAMPS_SERVEUR
from jules.modules.base import Module
from jules.revisions import REPONSES_CARTE, cartes_dues, prochaine_revision, reinitialiser
from jules.stockage import Conversation, maintenant
from jules.studio import (
    ErreurStudio,
    Support,
    pret_a_valider,
    ressemble_a_un_support_redige,
    trame_vide,
    valider_champ,
)

journal = logging.getLogger("jules.studio")

ESPACE = "studio"
MODE = "studio"
_CLE_TOUS = "tous"

LIBELLES_TYPE = {
    "carte_mentale": "carte mentale",
    "fiche": "fiche",
    "quiz": "quiz",
    "cartes_memoire": "cartes mémoire",
}

MESSAGE_PAS_DE_LECON = "Pas encore de leçon sur cette notion, le studio n'est pas encore utilisable ici."
QUESTION_DE_REPLI = "Qu'est-ce que tu retiens de cette partie, avec tes mots ?"
RAPPEL_GARDE_FOU = (
    "Règle absolue : ne rédige JAMAIS de texte de remplacement, ni une section entière, ni une "
    "phrase prête à copier. Réagis uniquement par une question courte ou une remarque courte sur "
    "ce qui existe déjà, section par section ou carte par carte. Si une section ou une carte est "
    "encore vide, n'en parle pas."
)

# Element vide ajoute quand l'eleve ecrit au-dela de la liste actuelle (voir docs/STUDIO-CONTRAT.md §1).
_ELEMENTS_DEFAUT = {
    "carte_mentale": lambda nid: {"id": nid, "texte": "", "parent": None},
    "fiche": lambda nid: {"id": nid, "titre": "", "contenu": ""},
    "quiz": lambda nid: {"id": nid, "question": "", "reponse": "", "forme": "libre"},
    "cartes_memoire": lambda nid: {
        "id": nid,
        "recto": "",
        "verso": "",
        "etat": "nouvelle",
        "prochaine_revision": None,
        "palier": 0,
    },
}


class SupportVerrouille(RuntimeError):
    """Action refusee a cause du statut du support (verrouille ou pas encore valide)."""


def _nouvel_id() -> str:
    return uuid.uuid4().hex[:12]


def _textes_lecon(lecon: Any) -> list[str]:
    """Tous les textes visibles par l'eleve dans une lecon (jamais les champs serveur, voir
    jules.lecons.CHAMPS_SERVEUR), pour le garde-fou anti-copie de `pret_a_valider`."""

    def valeurs(v: Any):
        if isinstance(v, str):
            yield v
        elif isinstance(v, list):
            for item in v:
                yield from valeurs(item)

    textes: list[str] = []
    for bloc in lecon.blocs:
        for cle, valeur in bloc.donnees.items():
            if cle in CHAMPS_SERVEUR:
                continue
            textes.extend(valeurs(valeur))
    return textes


class TypeEntree(BaseModel):
    type: str


class EcrireEntree(BaseModel):
    chemin: list[str | int]
    valeur: str


class ReponseCarteEntree(BaseModel):
    reponse: str


class Brique(Module):
    id = "studio"
    titre = "Studio de révision"

    # --- module dont on depend --------------------------------------------
    @property
    def cours_module(self) -> Any:
        module = self.tuteur.module("cours")
        if module is None:
            raise RuntimeError("Le module 'studio' nécessite le module 'cours'")
        return module

    def _notion(self, notion_id: str) -> Any:
        module = self.tuteur.module("notions")
        if module is None:
            return None
        return module.catalogue.notion(notion_id)  # type: ignore[attr-defined]  # module 'notions' expose 'catalogue'

    def _titre_notion(self, notion_id: str) -> str:
        notion = self._notion(notion_id)
        return notion.titre if notion else notion_id

    def _nom_matiere(self, notion_id: str) -> str:
        notion = self._notion(notion_id)
        return notion.nom_matiere if notion else ""

    def _aujourdhui(self) -> date:
        return date.today()

    # --- cles de stockage ----------------------------------------------------
    @staticmethod
    def _cle_support(support_id: str) -> str:
        return f"support:{support_id}"

    @staticmethod
    def _cle_notion(notion_id: str) -> str:
        return f"notion:{notion_id}"

    @staticmethod
    def _cle_conv(conv_id: str) -> str:
        return f"conv:{conv_id}"

    def _charger(self, support_id: str) -> tuple[Support, str]:
        """Support et conversation de relecture associee. Leve KeyError si introuvable."""
        brut = self.tuteur.stockage.lire_etat(ESPACE, self._cle_support(support_id))
        if brut is None:
            raise KeyError(support_id)
        return Support(**brut["support"]), brut["conversation"]

    def _sauver(self, support: Support, conv_id: str) -> None:
        self.tuteur.stockage.ecrire_etat(
            ESPACE, self._cle_support(support.id), {"support": support.public(), "conversation": conv_id}
        )

    def _index_notion(self, notion_id: str) -> list[str]:
        return list(self.tuteur.stockage.lire_etat(ESPACE, self._cle_notion(notion_id), []) or [])

    def _ajouter_index(self, cle: str, support_id: str) -> None:
        ids = list(self.tuteur.stockage.lire_etat(ESPACE, cle, []) or [])
        ids.append(support_id)
        self.tuteur.stockage.ecrire_etat(ESPACE, cle, ids)

    def _retirer_index(self, cle: str, support_id: str) -> None:
        ids = [i for i in (self.tuteur.stockage.lire_etat(ESPACE, cle, []) or []) if i != support_id]
        self.tuteur.stockage.ecrire_etat(ESPACE, cle, ids)

    def _tous_ids(self) -> list[str]:
        return list(self.tuteur.stockage.lire_etat(ESPACE, _CLE_TOUS, []) or [])

    # --- notions et leurs supports -------------------------------------------
    def _supports_notion(self, notion_id: str) -> list[dict[str, Any]]:
        resultat = []
        for support_id in self._index_notion(notion_id):
            brut = self.tuteur.stockage.lire_etat(ESPACE, self._cle_support(support_id))
            if brut is None:
                continue
            s = brut["support"]
            resultat.append({"id": s["id"], "type": s["type"], "titre": s["titre"], "statut": s["statut"]})
        return resultat

    def notions(self, matiere_id: str | None = None) -> dict[str, Any]:
        base = self.cours_module.parcours(matiere_id)
        return {
            **base,
            "notions": [{**n, "supports": self._supports_notion(n["id"])} for n in base["notions"]],
        }

    # --- creation / lecture / suppression --------------------------------------
    def creer(self, notion_id: str, type_support: str) -> Support:
        if notion_id not in self.cours_module.lecons:
            raise KeyError(notion_id)
        contenu = trame_vide(type_support, notion_id, "")  # ErreurStudio si type inconnu
        maintenant_ = maintenant()
        support = Support(
            id=_nouvel_id(),
            notion=notion_id,
            type=type_support,
            titre="",
            contenu=contenu,
            statut="brouillon",
            cree_le=maintenant_,
            modifie_le=maintenant_,
        )
        conv = self.tuteur.stockage.creer_conversation(MODE)
        self.tuteur.stockage.renommer(conv.id, f"Studio : {self._titre_notion(notion_id)}")
        self._sauver(support, conv.id)
        self._ajouter_index(self._cle_notion(notion_id), support.id)
        self._ajouter_index(_CLE_TOUS, support.id)
        self.tuteur.stockage.ecrire_etat(ESPACE, self._cle_conv(conv.id), support.id)
        return support

    def obtenir(self, support_id: str) -> Support:
        support, _ = self._charger(support_id)
        return support

    def supprimer(self, support_id: str) -> None:
        support, conv_id = self._charger(support_id)
        if support.statut == "valide":
            raise SupportVerrouille("Un support validé ne peut pas être supprimé.")
        self.tuteur.stockage.ecrire_etat(ESPACE, self._cle_support(support_id), None)
        self.tuteur.stockage.ecrire_etat(ESPACE, self._cle_conv(conv_id), None)
        self._retirer_index(self._cle_notion(support.notion), support_id)
        self._retirer_index(_CLE_TOUS, support_id)

    # --- ecriture ---------------------------------------------------------------
    def ecrire(self, support_id: str, chemin: list[str | int], valeur: str) -> Support:
        support, conv_id = self._charger(support_id)
        if support.statut == "valide":
            raise SupportVerrouille("Ce support est validé : dévalide-le d'abord pour le modifier.")
        valider_champ(support.type, chemin, valeur)  # ErreurStudio si chemin ou taille invalide
        if list(chemin) == ["titre"]:
            support.titre = valeur
        else:
            # valider_champ a deja verifie la forme du chemin : [liste, index, champ]
            nom_liste, index, champ = str(chemin[0]), int(chemin[1]), str(chemin[2])
            elements = support.contenu.setdefault(nom_liste, [])
            if index == len(elements):
                elements.append(_ELEMENTS_DEFAUT[support.type](_nouvel_id()[:8]))
            elif index > len(elements):
                raise ErreurStudio("Ajoute les éléments un par un : cet emplacement n'existe pas encore.")
            elements[index][champ] = valeur
        if support.statut == "relu":
            support.statut = "brouillon"
        support.modifie_le = maintenant()
        self._sauver(support, conv_id)
        return support

    # --- relecture par Jules (garde-fou anti-fuite) --------------------------------
    def _texte_support(self, support: Support, lecon: Any) -> str:
        parties = [
            f"Support en cours : {LIBELLES_TYPE.get(support.type, support.type)}"
            + (f", sur la leçon « {lecon.titre} » (référence, ne la récite pas)." if lecon else "."),
            f"Titre écrit par l'élève : {support.titre or '(pas encore écrit)'}",
        ]
        contenu = support.contenu
        if support.type == "carte_mentale":
            noeuds = contenu.get("noeuds") or []
            lignes = [f"- Branche {i} : {n.get('texte') or '(vide)'}" for i, n in enumerate(noeuds, start=1)]
            parties.append("Branches déjà écrites :\n" + ("\n".join(lignes) if lignes else "(aucune pour l'instant)"))
        elif support.type == "fiche":
            sections = contenu.get("sections") or []
            lignes = [
                f"- Section {i} : {s.get('titre') or '(sans titre)'} : {s.get('contenu') or '(vide)'}"
                for i, s in enumerate(sections, start=1)
            ]
            parties.append("Sections déjà écrites :\n" + ("\n".join(lignes) if lignes else "(aucune pour l'instant)"))
        elif support.type == "quiz":
            questions = contenu.get("questions") or []
            lignes = [
                f"- Question {i} : {q.get('question') or '(vide)'} / R : {q.get('reponse') or '(vide)'}"
                for i, q in enumerate(questions, start=1)
            ]
            parties.append(
                "Questions déjà écrites par l'élève :\n" + ("\n".join(lignes) if lignes else "(aucune pour l'instant)")
            )
        elif support.type == "cartes_memoire":
            cartes = contenu.get("cartes") or []
            lignes = [
                f"- Carte {i} : recto {c.get('recto') or '(vide)'} / verso {c.get('verso') or '(vide)'}"
                for i, c in enumerate(cartes, start=1)
            ]
            parties.append("Cartes déjà écrites :\n" + ("\n".join(lignes) if lignes else "(aucune pour l'instant)"))
        parties.append(RAPPEL_GARDE_FOU)
        return "\n\n".join(parties)

    def relire(self, support_id: str) -> dict[str, Any]:
        support, conv_id = self._charger(support_id)
        message_eleve = f"🔎 Relis mon support « {support.titre or LIBELLES_TYPE.get(support.type, support.type)} »."
        texte = self.tuteur.echanger(conv_id, message_eleve).texte
        if ressemble_a_un_support_redige(texte):
            journal.warning("Retour de Jules ecarte (ressemblait a un support redige) : %s", texte[:200])
            texte = QUESTION_DE_REPLI
        if support.statut != "valide":
            support.statut = "relu"
        support.modifie_le = maintenant()
        self._sauver(support, conv_id)
        return {"retours": [{"chemin": [], "message": texte}], "support": support}

    # --- valider / devalider ------------------------------------------------------
    def _evenement_suivi(self, support: Support, statut: str, resume: str, conv_id: str) -> None:
        # Type d'evenement propre au studio, PAS "suivi" : memoire, rapport, epreuve et cours prennent
        # le dernier evenement "suivi" d'une notion comme son etat (compris, bloque...). Un support
        # valide ou devalide ne dit rien de la comprehension : il ne doit pas l'ecraser.
        self.tuteur.stockage.ajouter_evenement(
            "studio",
            {
                "matiere": self._nom_matiere(support.notion),
                "notion": self._titre_notion(support.notion),
                "action": statut,
                "resume": resume,
                "titre": support.titre,
            },
            conv_id,
        )

    def valider(self, support_id: str) -> Support:
        support, conv_id = self._charger(support_id)
        lecon = self.cours_module.lecons.get(support.notion)
        lecon_textes = _textes_lecon(lecon) if lecon else []
        conv = self.tuteur.stockage.conversation(conv_id)
        messages_jules = [m.texte for m in (conv.messages if conv else []) if m.role == "bot"]
        pret_a_valider(support, lecon_textes, messages_jules)  # ErreurStudio si pas pret
        support.statut = "valide"
        if support.type == "cartes_memoire":
            aujourdhui = self._aujourdhui().isoformat()
            support.contenu["cartes"] = [
                {**c, "prochaine_revision": aujourdhui} for c in support.contenu.get("cartes", [])
            ]
        support.modifie_le = maintenant()
        self._sauver(support, conv_id)
        self._evenement_suivi(
            support, "support_cree", f"Support « {support.titre or support.type} » créé et validé.", conv_id
        )
        return support

    def devalider(self, support_id: str) -> Support:
        support, conv_id = self._charger(support_id)
        if support.statut != "valide":
            raise SupportVerrouille("Ce support n'est pas validé.")
        support.statut = "brouillon"
        if support.type == "cartes_memoire":
            support.contenu["cartes"] = [reinitialiser(c) for c in support.contenu.get("cartes", [])]
        support.modifie_le = maintenant()
        self._sauver(support, conv_id)
        self._evenement_suivi(
            support, "support_devalide", f"Support « {support.titre or support.type} » dévalidé.", conv_id
        )
        return support

    # --- revisions (cartes memoire, paliers fixes) ----------------------------------
    def revisions_disponibles(self) -> dict[str, Any]:
        aujourdhui = self._aujourdhui()
        cartes: list[dict[str, Any]] = []
        for support_id in self._tous_ids():
            brut = self.tuteur.stockage.lire_etat(ESPACE, self._cle_support(support_id))
            if brut is None:
                continue
            s = brut["support"]
            if s["type"] != "cartes_memoire" or s["statut"] != "valide":
                continue
            for carte in cartes_dues(s["contenu"].get("cartes") or [], aujourdhui):
                cartes.append(
                    {
                        "support": support_id,
                        "carte_id": carte["id"],
                        "recto": carte["recto"],
                        "notion": self._titre_notion(s["notion"]),
                    }
                )
        return {"cartes": cartes, "nombre_du_jour": len(cartes)}

    def reponse_carte(self, support_id: str, carte_id: str, reponse: str) -> dict[str, Any]:
        support, conv_id = self._charger(support_id)
        if support.type != "cartes_memoire":
            raise ValueError("Ce support n'a pas de cartes mémoire.")
        if support.statut != "valide":
            raise SupportVerrouille("Ce support n'est pas encore validé.")
        cartes = support.contenu.get("cartes") or []
        index = next((i for i, c in enumerate(cartes) if c.get("id") == carte_id), None)
        if index is None:
            raise KeyError(carte_id)
        if reponse not in REPONSES_CARTE:
            raise ValueError(
                f"reponse de carte inconnue : {reponse!r} (attendu l'une de : {', '.join(REPONSES_CARTE)})"
            )
        nouvelle = prochaine_revision(cartes[index], reponse, self._aujourdhui())
        cartes[index] = nouvelle
        support.modifie_le = maintenant()
        self._sauver(support, conv_id)
        restantes = self.revisions_disponibles()["nombre_du_jour"]
        carte_publique = {k: v for k, v in nouvelle.items() if k != "verso"}
        return {"carte": carte_publique, "restantes": restantes}

    # --- contrat de module -----------------------------------------------------
    def contribution(self, conv: Conversation) -> str | None:
        if conv.mode != MODE:
            return None
        support_id = self.tuteur.stockage.lire_etat(ESPACE, self._cle_conv(conv.id))
        if not support_id:
            return None
        brut = self.tuteur.stockage.lire_etat(ESPACE, self._cle_support(support_id))
        if brut is None:
            return None
        support = Support(**brut["support"])
        lecon = self.cours_module.lecons.get(support.notion)
        return self._texte_support(support, lecon)

    def infos_interface(self) -> dict[str, Any]:
        cours = self.tuteur.module("cours")
        return {"studio": bool(cours and cours.lecons)}  # type: ignore[attr-defined]  # module 'cours' expose 'lecons'

    # --- routes eleve ---------------------------------------------------------
    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        @routeur.get("/notions")
        def notions_route(matiere: str | None = None) -> dict[str, Any]:
            return self.notions(matiere)

        @routeur.post("/notions/{notion_id}/creer")
        def creer_route(notion_id: str, entree: TypeEntree) -> dict[str, Any]:
            try:
                support = self.creer(notion_id, entree.type)
            except KeyError as err:
                raise HTTPException(404, MESSAGE_PAS_DE_LECON) from err
            except ErreurStudio as err:
                raise HTTPException(400, str(err)) from err
            return {"support": support.public()}

        @routeur.get("/supports/{support_id}")
        def lire_support(support_id: str) -> dict[str, Any]:
            try:
                support = self.obtenir(support_id)
            except KeyError as err:
                raise HTTPException(404, "Support introuvable") from err
            return {"support": support.public()}

        @routeur.post("/supports/{support_id}/ecrire")
        def ecrire_route(support_id: str, entree: EcrireEntree) -> dict[str, Any]:
            try:
                support = self.ecrire(support_id, entree.chemin, entree.valeur)
            except KeyError as err:
                raise HTTPException(404, "Support introuvable") from err
            except SupportVerrouille as err:
                raise HTTPException(409, str(err)) from err
            except ErreurStudio as err:
                raise HTTPException(400, str(err)) from err
            return {"support": support.public()}

        @routeur.post("/supports/{support_id}/relire")
        def relire_route(support_id: str) -> dict[str, Any]:
            try:
                resultat = self.relire(support_id)
            except KeyError as err:
                raise HTTPException(404, "Support introuvable") from err
            return {"retours": resultat["retours"], "support": resultat["support"].public()}

        @routeur.post("/supports/{support_id}/valider")
        def valider_route(support_id: str) -> dict[str, Any]:
            try:
                support = self.valider(support_id)
            except KeyError as err:
                raise HTTPException(404, "Support introuvable") from err
            except ErreurStudio as err:
                raise HTTPException(422, str(err)) from err
            return {"support": support.public()}

        @routeur.post("/supports/{support_id}/devalider")
        def devalider_route(support_id: str) -> dict[str, Any]:
            try:
                support = self.devalider(support_id)
            except KeyError as err:
                raise HTTPException(404, "Support introuvable") from err
            except SupportVerrouille as err:
                raise HTTPException(409, str(err)) from err
            return {"support": support.public()}

        @routeur.delete("/supports/{support_id}", status_code=204)
        def supprimer_route(support_id: str) -> Response:
            try:
                self.supprimer(support_id)
            except KeyError as err:
                raise HTTPException(404, "Support introuvable") from err
            except SupportVerrouille as err:
                raise HTTPException(409, str(err)) from err
            return Response(status_code=204)

        @routeur.get("/revisions")
        def revisions_route() -> dict[str, Any]:
            return self.revisions_disponibles()

        @routeur.post("/revisions/{support_id}/{carte_id}/reponse")
        def reponse_carte_route(support_id: str, carte_id: str, entree: ReponseCarteEntree) -> dict[str, Any]:
            try:
                return self.reponse_carte(support_id, carte_id, entree.reponse)
            except KeyError as err:
                raise HTTPException(404, "Carte introuvable") from err
            except SupportVerrouille as err:
                raise HTTPException(409, str(err)) from err
            except ValueError as err:
                raise HTTPException(400, str(err)) from err

        return routeur
