"""Module 'suivi' : analyse chaque echange (matiere, notion, statut) en tache de fond.

Produit des evenements 'suivi' lus par les modules memoire et rapport.
Donne aussi un titre a la conversation au premier echange.
"""

from __future__ import annotations

import logging
from typing import Any

from jules.llm.base import Tour
from jules.modules.base import Module, extraire_json
from jules.modules.figures import texte_sans_figures
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.suivi")

STATUTS = ("compris", "en_cours", "bloque", "hors_scolaire")
# "acquis" n'est jamais donne par l'analyse : seul le module epreuve l'ecrit, apres une epreuve sans aide.
MODES_IGNORES = ("epreuve", "exercice")

# Chaque evenement 'suivi' porte son origine : qui a decide du statut. Un evenement sans ce champ
# (ecrit avant son introduction) est traite comme 'analyse', l'origine la moins fiable (voir
# dernier_statut ci-dessous et docs/EPREUVE-PROTOCOLE.md).
ORIGINES_SUIVI = ("analyse", "epreuve", "cours", "exercices", "studio", "annales")
ORIGINE_DEFAUT = "analyse"
# 'acquis' n'est retrograde que par une origine qui reprend directement la notion (l'epreuve sans
# aide, une nouvelle lecon ou une nouvelle serie d'exercices sur la meme notion) : jamais par la
# simple analyse du modele rapide sur un echange qui peut etre hors sujet (constat de revue du
# 27/09/2026 : une classification d'un echange ordinaire ecrasait un "acquis" en "en_cours").
ORIGINES_RETROGRADENT_ACQUIS = ("epreuve", "exercices", "cours")


def evenement_suivi(
    matiere: str, notion: str, statut: str, resume: str = "", titre: str = "", origine: str = ORIGINE_DEFAUT
) -> dict[str, str]:
    """Construit les donnees d'un evenement 'suivi', origine incluse.

    Centralise le format pour que tous les producteurs (suivi, epreuve, cours, exercices) restent
    coherents : ne pas construire ce dict a la main ailleurs.
    """
    if origine not in ORIGINES_SUIVI:
        raise ValueError(f"origine de suivi inconnue : {origine!r}")
    return {
        "matiere": matiere,
        "notion": notion,
        "statut": statut,
        "resume": resume,
        "titre": titre,
        "origine": origine,
    }


def dernier_statut(evenements: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    """(matiere, notion) en casefold -> evenement 'suivi' retenu comme etat actuel de la notion.

    `evenements` : du plus recent au plus ancien (ordre de Stockage.evenements ; le champ
    'horodatage' peut manquer dans des donnees de test, il est alors traite comme le plus ancien).
    Ignore les evenements sans notion/matiere et les evenements 'hors_scolaire'.

    Arbitrage (revue du 27/09/2026) : un evenement d'origine 'analyse' (le modele rapide, en tache de
    fond, sur un echange qui peut etre hors sujet) ne retrograde jamais un statut 'acquis' deja
    retenu. Seule une origine de ORIGINES_RETROGRADENT_ACQUIS peut le faire. Les autres statuts
    (compris, en_cours, bloque) sont toujours remplaces par le plus recent, quelle que soit l'origine.
    Usage unique pour tout lecteur qui prend "le dernier evenement suivi" comme etat d'une notion :
    jules.modules.cours._derniers_statuts, jules.modules.memoire.bilan_notions,
    jules.modules.epreuve.candidates, jules.modules.rapport.donnees_du_jour.
    """
    etats: dict[tuple[str, str], dict[str, Any]] = {}
    for ev in reversed(evenements):  # du plus ancien au plus recent
        d = ev["donnees"]
        if not d.get("notion") or not d.get("matiere") or d.get("statut") == "hors_scolaire":
            continue
        cle = (str(d["matiere"]).casefold(), str(d["notion"]).casefold())
        origine = str(d.get("origine") or ORIGINE_DEFAUT)
        actuel = etats.get(cle)
        acquis_protege = actuel is not None and actuel["donnees"].get("statut") == "acquis"
        if acquis_protege and origine not in ORIGINES_RETROGRADENT_ACQUIS:
            continue  # 'acquis' protege : cet evenement d'analyse ne le retrograde pas
        etats[cle] = ev
    return etats


CONSIGNE = """Tu analyses un échange entre un élève de collège et son tuteur IA, pour le suivi scolaire.
Réponds UNIQUEMENT par un objet JSON, sans texte autour :
{"matiere": "...", "notion": "...", "statut": "...", "resume": "...", "titre": "..."}
- matiere : Mathématiques, Français, Anglais, Espagnol, Allemand, Histoire-Géographie, EMC,
  SVT, Physique-Chimie, Technologie, Latin, Musique, Arts plastiques, Autre.
- notion : la notion précise travaillée (ex. "fractions : addition", "passé composé"), 6 mots max.
  Laisse "" tant que l'élève n'a pas encore dit sur quoi il travaille (« j'ai un exo »).
- Une ligne « [Correction automatique] Réponse juste » veut dire que l'élève a trouvé seul la bonne
  réponse à l'exercice : c'est le dernier état de l'exercice, même si la discussion d'avant hésitait.
- statut : "compris" seulement si l'élève a trouvé ou expliqué LUI-MÊME (une réponse donnée ou écrite
  par le tuteur, puis recopiée ou approuvée par l'élève, ne compte pas) ; "bloque" si l'élève bute
  (erreurs répétées, "je comprends pas") ; "en_cours" sinon ; "hors_scolaire" si ce n'est pas scolaire.
  Un exercice scolaire reste scolaire même si l'élève répond par "jsp" ou très court.
- resume : une phrase factuelle pour le parent (ce qui a été fait, où en est l'élève). Distingue ce que
  l'élève a trouvé seul de ce que le tuteur a fourni (« le tuteur a donné la forme went »). Ne dis jamais
  « maîtrise » ni « a construit seul » si le tuteur a fait une partie du travail.
- titre : titre court de la conversation (4 mots max)."""


def normaliser(analyse: dict[str, Any]) -> dict[str, str]:
    statut = str(analyse.get("statut") or "en_cours")
    return {
        "matiere": str(analyse.get("matiere") or "Autre")[:40],
        "notion": str(analyse.get("notion") or "")[:80],
        "statut": statut if statut in STATUTS else "en_cours",
        "resume": str(analyse.get("resume") or "")[:300],
        "titre": str(analyse.get("titre") or "")[:60],
    }


def extrait(conv: Conversation, nb: int = 6) -> str:
    lignes = []
    for m in conv.messages[-nb:]:
        qui = "ÉLÈVE" if m.role == "eleve" else "TUTEUR"
        photo = " [+ photo]" if m.images else ""
        # Un bloc ```figure (JSON) devient « [figure : <gabarit>] » : l'analyse lit le sens, pas le code.
        lignes.append(f"{qui}{photo} : {texte_sans_figures(m.texte)[:1500]}")
    return "\n".join(lignes)


class Brique(Module):
    id = "suivi"

    def notions_connues(self, maximum: int = 40) -> list[str]:
        vues: list[str] = []
        for ev in self.tuteur.stockage.evenements("suivi", limite=300):
            d = ev["donnees"]
            if not d.get("notion") or d.get("statut") == "hors_scolaire":
                continue
            libelle = f"{d.get('matiere', 'Autre')} | {d['notion']}"
            if libelle not in vues:
                vues.append(libelle)
            if len(vues) >= maximum:
                break
        return vues

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        if conv.mode in self.reglages.get("modes_ignores", MODES_IGNORES):
            return  # l'epreuve sans aide tient son propre suivi : pas d'analyse pendant qu'elle se deroule
        connues = self.notions_connues()
        consigne = CONSIGNE
        if connues:
            consigne += (
                "\nNotions déjà suivies (si c'est la même notion, reprends EXACTEMENT le même libellé "
                "et la même matière) :\n" + "\n".join(f"- {n}" for n in connues)
            )
        tours = [Tour(role="user", texte=f"Mode : {conv.mode}\n\n{extrait(conv)}")]
        brut = self.tuteur.llm.repondre(consigne, tours, "rapide")
        analyse = extraire_json(brut)
        if analyse is None:
            journal.warning("Analyse de suivi illisible : %s", brut[:200])
            return
        donnees = normaliser(analyse)
        self.tuteur.stockage.ajouter_evenement("suivi", evenement_suivi(**donnees, origine=ORIGINE_DEFAUT), conv.id)
        if not conv.titre and donnees["titre"]:
            self.tuteur.stockage.renommer(conv.id, donnees["titre"])
            conv.titre = donnees["titre"]
