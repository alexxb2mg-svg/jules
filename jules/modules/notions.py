"""Module 'notions' : relie chaque conversation a une notion du programme et nourrit Jules avec.

Comment une conversation trouve sa notion :
  1. l'eleve la choisit (bouton « Choisir une notion ») : c'est prioritaire et ne change plus ;
  2. sinon, avant de repondre aux premiers messages, un appel court au modele 'rapide' lit le
     texte et la photo de l'exercice et propose une notion du referentiel (ou aucune).

Une fois la notion connue, le prompt de Jules recoit :
  - ce que le programme attend (referentiel) ;
  - la direction pedagogique de l'enseignant, s'il y en a une (prioritaire) ;
  - les reperes des fiches (essentiel, methode, erreurs frequentes, exercices), avec le statut de
    la bibliotheque d'ou ils viennent (une bibliotheque experimentale est annoncee comme telle).

Reglages (config.yaml) :
  bibliotheques: [programme, fiches-3e-experimentales]   # ordre = priorite
  detection: true            # detection automatique sur texte et photo
  essais_detection: 2        # nombre de messages de l'eleve examines avant d'abandonner
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jules.bibliotheques import (
    SCORE_FORT,
    Catalogue,
    Notion,
    candidats_notes,
    charger_catalogue,
    texte_direction,
    texte_fiche,
)
from jules.llm.base import TEXTE_PHOTO_SEULE, Tour
from jules.modules.base import Module, extraire_json
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.notions")

ESPACE = "notions"
ORIGINES = ("eleve", "auto")
# Pendant l'epreuve sans aide, Jules ne recoit ni fiche ni attendus : ce serait une aide.
MODES_SANS_NOTION = ("epreuve",)
# Un calcul tape par l'eleve (« (2x-6)(x+5) = 0 », « 2/3 + 5/6 ») : un operateur colle a un nombre ou a une
# parenthese. « peut-être » ou « m/s » n'en sont pas.
_CALCUL = re.compile(r"[0-9)²³]\s*[-+*/×÷=^]|[-+*/×÷=^]\s*[0-9(√]")


def ressemble_a_un_calcul(texte: str) -> bool:
    return bool(_CALCUL.search(texte or ""))


CONSIGNE_DETECTION = """Tu rattaches le travail d'un élève à UNE notion d'une liste fermée.
Lis son message (et la photo de son exercice s'il y en a une), puis réponds UNIQUEMENT par un objet JSON :
{"notion": "<identifiant de la liste, ou vide>", "confiance": "haute|moyenne|faible"}
- Choisis l'identifiant tel quel dans la liste, sans l'inventer ni le modifier.
- Une question de cours ou de curiosité sur un sujet du programme compte comme du travail scolaire
  (« c'est quoi le mur de Berlin » -> la notion d'histoire qui en parle) : choisis la notion la plus proche.
- "notion": "" seulement si le message n'a aucun lien avec le programme (vie personnelle, bavardage).
Liste (identifiant | matière | notion) :
"""


def niveau_du_profil(classe: str) -> str | None:
    """'3e', '3ème', 'troisième' -> '3e' ; 'CM1', 'cours moyen 1' -> 'CM1' ; None si la classe est inconnue."""
    c = classe.lower().replace("è", "e").replace("é", "e").strip()
    ecole = re.match(r"^(?:cm|cours moyen)\s*(1|2|premiere|deuxieme)\b", c)
    if ecole:
        return "CM1" if ecole.group(1) in ("1", "premiere") else "CM2"
    correspondances = {"6": "6e", "5": "5e", "4": "4e", "3": "3e"}
    m = re.match(r"^(\d)\s*(?:e|eme|ieme)?\b", c)
    if m and m.group(1) in correspondances:
        return correspondances[m.group(1)]
    for mot, niveau in (("sixieme", "6e"), ("cinquieme", "5e"), ("quatrieme", "4e"), ("troisieme", "3e")):
        if mot in c:
            return niveau
    return None


class ChoixNotion(BaseModel):
    notion: str


class Brique(Module):
    id = "notions"
    titre = "Notion travaillée"

    def __init__(self, tuteur: Any, reglages: dict[str, Any]) -> None:
        super().__init__(tuteur, reglages)
        self.ids = [str(i) for i in reglages.get("bibliotheques") or ["programme"]]
        self.detection = bool(reglages.get("detection", True))
        self.essais = int(reglages.get("essais_detection", 2))
        self._catalogue: Catalogue | None = None

    # --- catalogue ---------------------------------------------------------
    @property
    def catalogue(self) -> Catalogue:
        if self._catalogue is None:
            niveau = niveau_du_profil(self.tuteur.profil().classe)
            self._catalogue = charger_catalogue(self.tuteur.config.dossier_bibliotheques, self.ids, niveau)
            journal.info(
                "Bibliotheques : %s notions (niveau %s), contenus : %s",
                len(self._catalogue.notions),
                niveau or "tous",
                ", ".join(b.id for b in self._catalogue.contenus) or "aucun",
            )
        return self._catalogue

    def recharger(self) -> None:
        self._catalogue = None

    # --- etat par conversation ---------------------------------------------
    def etat(self, conv_id: str) -> dict[str, Any]:
        return dict(self.tuteur.stockage.lire_etat(ESPACE, conv_id, {}) or {})

    def fixer(self, conv_id: str, notion_id: str, origine: str = "eleve", confiance: str = "") -> Notion:
        notion = self.catalogue.notion(notion_id)
        if notion is None:
            raise KeyError(notion_id)
        etat = self.etat(conv_id)
        etat.update({"notion": notion.id, "origine": origine if origine in ORIGINES else "eleve"})
        if confiance:
            etat["confiance"] = confiance
        self.tuteur.stockage.ecrire_etat(ESPACE, conv_id, etat)
        evenement = {"notion": notion.id, "titre": notion.titre, "matiere": notion.nom_matiere, "origine": origine}
        self.tuteur.stockage.ajouter_evenement("notion", evenement, conv_id)
        return notion

    def retirer(self, conv_id: str) -> None:
        etat = self.etat(conv_id)
        etat.pop("notion", None)
        etat.pop("confiance", None)
        etat["origine"] = "eleve"  # l'eleve a retire la notion : on ne la redevine pas
        self.tuteur.stockage.ecrire_etat(ESPACE, conv_id, etat)

    def notion_de(self, conv_id: str) -> dict[str, Any] | None:
        etat = self.etat(conv_id)
        notion = self.catalogue.notion(etat.get("notion", ""))
        if notion is None:
            return None
        return {
            "id": notion.id,
            "titre": notion.titre,
            "matiere": notion.nom_matiere,
            "origine": etat.get("origine", "eleve"),
            "fiche": self.catalogue.a_une_fiche(notion.id),
        }

    # --- detection automatique ------------------------------------------------
    def avant_echange(self, conv: Conversation, eleve: Message) -> None:
        if conv.mode in MODES_SANS_NOTION or not self.detection or not self.catalogue.notions:
            return
        etat = self.etat(conv.id)
        if etat.get("notion") or etat.get("origine") == "eleve":
            return
        essais = int(etat.get("essais", 0))
        if essais >= self.essais:
            return
        etat["essais"] = essais + 1
        self.tuteur.stockage.ecrire_etat(ESPACE, conv.id, etat)
        trouvee = self.detecter(eleve)
        if trouvee:
            self.fixer(conv.id, trouvee[0], origine="auto", confiance=trouvee[1])

    def detecter(self, eleve: Message) -> tuple[str, str] | None:
        """Propose (id de notion, confiance) pour un message de l'eleve, ou None."""
        notes = candidats_notes(self.catalogue, eleve.texte) if eleve.texte else []
        calcul = ressemble_a_un_calcul(eleve.texte)
        if not notes and not eleve.images and not calcul:
            return None  # ni mot reconnu, ni photo, ni calcul : rien a rattacher
        # Le modele voit toujours toute la liste (le vocabulaire des eleves deborde toujours des mots-cles :
        # « periurbanisation », « il faut mettre un e et un s ? ») ; les notions dont un mot-cle est reconnu
        # en entier passent en tete. Le prefiltre ne sert plus qu'a decider s'il faut appeler le modele.
        fortes = [n for score, n in notes if score >= SCORE_FORT and not calcul]
        vues = {n.id for n in fortes}
        liste = fortes + [n for n in self.catalogue.notions.values() if n.id not in vues]
        catalogue = "\n".join(f"{n.id} | {n.nom_matiere} | {n.titre}" for n in liste)
        images = [p for nom in eleve.images if (p := self.tuteur.stockage.chemin_image(nom))]
        tour = Tour(role="user", texte=eleve.texte or TEXTE_PHOTO_SEULE, images=images)
        brut = self.tuteur.llm.repondre(CONSIGNE_DETECTION + catalogue, [tour], "rapide")
        reponse = extraire_json(brut) or {}
        identifiant = str(reponse.get("notion") or "").strip()
        confiance = str(reponse.get("confiance") or "").strip()
        if identifiant not in {n.id for n in liste} or confiance == "faible":
            return None
        return identifiant, confiance or "moyenne"

    # --- prompt -----------------------------------------------------------------
    def contribution(self, conv: Conversation) -> str | None:
        if conv.mode in MODES_SANS_NOTION:
            return None
        etat = self.etat(conv.id)
        notion = self.catalogue.notion(etat.get("notion", ""))
        if notion is None:
            return None
        return self.texte_notion(notion, etat.get("origine", "eleve"))

    def texte_notion(self, notion: Notion, origine: str) -> str:
        comment = "choisie par l'élève" if origine == "eleve" else "reconnue automatiquement dans son message"
        parties = [
            f"Notion {comment} : {notion.titre} ({notion.nom_matiere}, {notion.niveau}).",
        ]
        if origine == "auto":
            parties.append(
                "Si l'échange montre qu'il s'agit d'autre chose, suis l'élève et ignore ce qui suit sur la notion."
            )
        if notion.attendus:
            referentiel = self.catalogue.referentiel
            nom_ref = f" (bibliothèque « {referentiel.titre} »)" if referentiel else ""
            parties.append(f"Ce que le programme attend{nom_ref} :\n" + "\n".join(f"- {a}" for a in notion.attendus))
        directions = self.catalogue.directions(notion)
        if directions:
            lignes = [
                "Direction pédagogique de l'enseignant (PRIORITAIRE : suis-la quand elle diffère des repères "
                "ci-dessous, sans jamais enfreindre tes règles de pédagogie et de sécurité) :"
            ]
            for biblio, direction in directions:
                lignes.append(f"[{biblio.titre}{self._mention(biblio.statut)}]")
                lignes.append(texte_direction(direction))
            parties.append("\n".join(lignes))
        fiche, origines = self.catalogue.fiche(notion.id)
        if fiche:
            noms = " ; ".join(f"« {b.titre} »{self._mention(b.statut)}" for b in origines)
            entete = f"Repères pour guider l'élève, tirés de : {noms}."
            if any(b.statut in ("experimentale", "exemple") for b in origines):
                entete += (
                    " Contenu EXPÉRIMENTAL, non validé par un enseignant : sers-t'en comme appui, "
                    "pas comme vérité. Si le cours de l'élève dit autrement, c'est son cours qui fait foi."
                )
            parties.append(entete + "\n\n" + texte_fiche(fiche))
        return "\n\n".join(parties)

    @staticmethod
    def _mention(statut: str) -> str:
        return {
            "experimentale": " (expérimentale)",
            "exemple": " (exemple fictif)",
            "certifiee": " (certifiée)",
            "enseignant": " (de l'enseignant)",
        }.get(statut, "")

    # --- routes eleve ---------------------------------------------------------------
    def routes_eleve(self) -> APIRouter:
        routeur = APIRouter()

        def conversation(conv_id: str) -> Conversation:
            conv = self.tuteur.stockage.conversation(conv_id)
            if conv is None:
                raise HTTPException(404, "Conversation introuvable")
            return conv

        @routeur.get("/conversations/{conv_id}")
        def lire(conv_id: str) -> dict[str, Any]:
            conversation(conv_id)
            return {"notion": self.notion_de(conv_id)}

        @routeur.put("/conversations/{conv_id}")
        def choisir(conv_id: str, choix: ChoixNotion) -> dict[str, Any]:
            conversation(conv_id)
            try:
                self.fixer(conv_id, choix.notion, origine="eleve")
            except KeyError as err:
                raise HTTPException(400, "Notion inconnue") from err
            return {"notion": self.notion_de(conv_id)}

        @routeur.delete("/conversations/{conv_id}")
        def retirer(conv_id: str) -> dict[str, Any]:
            conversation(conv_id)
            self.retirer(conv_id)
            return {"notion": None}

        return routeur

    # --- interface ----------------------------------------------------------------
    def infos_interface(self) -> dict[str, Any]:
        cat = self.catalogue
        return {
            "notions": {
                "bibliotheques": [b.publique() for b in ([cat.referentiel] if cat.referentiel else []) + cat.contenus],
                "matieres": [
                    {
                        "id": mid,
                        "nom": nom,
                        "notions": [
                            {"id": n.id, "titre": n.titre, "chapitre": n.chapitre, "fiche": cat.a_une_fiche(n.id)}
                            for n in notions
                        ],
                    }
                    for mid, nom, notions in cat.matieres()
                ],
            }
        }
