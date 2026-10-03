"""Module 'vigilance' : repere les signaux inquietants et previent le parent tout de suite.

Chaque message de l'eleve passe d'abord par un plancher deterministe, puis est relu par le modele
rapide. Niveau 'moyen' ou plus (reglage `seuil_alerte`) : alerte via les notifieurs. Tous les
signaux sont journalises (evenements 'vigilance').
La conduite du bot face a ces situations est dans consignes/securite.md.

Le plancher (consignes/vigilance_plancher.yaml) repere une liste etroite d'expressions (idees
suicidaires, auto-agression, violence subie, harcelement, adulte inconnu inquietant). S'il trouve
quelque chose, l'evenement et l'alerte partent tout de suite, AVANT l'appel au modele : en cas de
panne d'API, cet appel peut durer jusqu'a `delai_s` (120 a 180 s) avant d'echouer, et l'alerte ne
l'attend pas. Le plancher alerte donc meme si le modele d'analyse est en panne ou repond n'importe
quoi, et meme si le moteur principal a echoue : jules/moteur.py previent les modules aussi dans ce
cas, avec le message de panne en guise de reponse.
Ensuite seulement, le modele relit le message :
  - s'il voit STRICTEMENT plus grave que le plancher, c'est une escalade : nouvel evenement, et
    nouvelle alerte si le seuil est franchi ;
  - s'il confirme le niveau du plancher, ou voit moins grave, rien de plus : pas de doublon ;
  - s'il echoue (ou repond un JSON illisible) et que le plancher n'a rien trouve, un evenement de
    repli est enregistre (niveau 'faible', motif 'analyse indisponible') sans notifier le parent :
    ce n'est pas une alerte, seulement une trace que l'analyse n'a pas pu avoir lieu.

Les modules font leur `apres_echange` l'un apres l'autre, sur un seul fil de fond, dans l'ordre de
config.yaml : 'vigilance' y passe avant 'memoire' et 'suivi', pour que l'alerte du plancher
n'attende pas non plus l'appel au modele du suivi.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from jules.llm.base import Tour
from jules.modules.base import Module, extraire_json
from jules.stockage import Conversation, Message

journal = logging.getLogger("jules.vigilance")

NIVEAUX = ("aucun", "faible", "moyen", "eleve")

FICHIER_PLANCHER = Path(__file__).resolve().parents[2] / "consignes" / "vigilance_plancher.yaml"

CONSIGNE = """Tu protèges un élève de collège qui utilise un tuteur scolaire IA. Lis SON message
(et la réponse du tuteur) et détecte un signal qui mérite l'attention de ses parents :
tristesse profonde, idées noires, auto-agression, harcèlement (école ou en ligne), violence subie,
contact inquiétant avec un adulte ou un inconnu, mise en danger, détresse forte, ou demande d'aide.
Ne signale PAS : le stress normal des contrôles, l'agacement contre un exercice, les blagues évidentes,
les gros mots isolés.
Ne signale PAS non plus les expressions courantes (« je vais mourir mdr », « ma mère va me tuer »,
« ce contrôle va me tuer ») quand le contexte est clairement celui du travail scolaire.
Réponds UNIQUEMENT par un objet JSON :
{"niveau": "aucun|faible|moyen|eleve", "motif": "une phrase factuelle, vide si aucun"}
Le motif dit exactement qui a dit ou demandé quoi (« un adulte de 24 ans lui propose un rendez-vous
et lui demande de le cacher à sa mère »), sans l'attribuer à l'élève par erreur."""


def doit_alerter(niveau: str, seuil: str) -> bool:
    if niveau not in NIVEAUX or seuil not in NIVEAUX:
        return False
    return NIVEAUX.index(niveau) >= NIVEAUX.index(seuil)


@lru_cache(maxsize=1)
def charger_plancher(chemin: Path = FICHIER_PLANCHER) -> dict[str, Any]:
    """consignes/vigilance_plancher.yaml : motifs d'alerte par niveau, plus les exclusions."""
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    return {
        "niveaux": dict(brut.get("niveaux") or {}),
        "exclusions": [str(m) for m in brut.get("exclusions") or []],
    }


def _sans_exclusions(texte: str, exclusions: list[str]) -> str:
    """Retire du texte les portions qui correspondent a une exclusion (faux positifs connus)."""
    for motif in exclusions:
        texte = re.sub(motif, " ", texte, flags=re.IGNORECASE)
    return texte


def evaluer_plancher(texte: str, plancher: dict[str, Any] | None = None) -> tuple[str, str]:
    """Cherche les motifs du plancher dans `texte`. Renvoie (niveau, motif), ('aucun', '') si rien.

    Le niveau le plus eleve est retourne si plusieurs niveaux correspondent."""
    plancher = plancher if plancher is not None else charger_plancher()
    nettoye = _sans_exclusions(texte, plancher["exclusions"])
    for niveau in reversed(NIVEAUX):
        regles = plancher["niveaux"].get(niveau)
        if not regles:
            continue
        motifs = regles.get("motifs") or []
        if any(re.search(motif, nettoye, re.IGNORECASE) for motif in motifs):
            return niveau, str(regles.get("motif_du_niveau") or "")
    return "aucun", ""


def _strictement_plus_haut(niveau: str, reference: str) -> bool:
    """Vrai si `niveau` est un niveau connu, strictement au-dessus de `reference` (inconnue = 'aucun')."""
    if niveau not in NIVEAUX:
        return False
    rang_reference = NIVEAUX.index(reference) if reference in NIVEAUX else 0
    return NIVEAUX.index(niveau) > rang_reference


class Brique(Module):
    id = "vigilance"

    def apres_echange(self, conv: Conversation, eleve: Message, bot: Message) -> None:
        # 1. Plancher deterministe : evenement et alerte tout de suite, sans attendre le modele.
        niveau_plancher, motif_plancher = evaluer_plancher(eleve.texte)
        self._traiter(conv, eleve, niveau_plancher, motif_plancher)

        # 2. Modele : il ne peut qu'aggraver le niveau du plancher (escalade), jamais le doublonner.
        niveau_modele, motif_modele = self._analyser_avec_le_modele(eleve, bot)
        if niveau_modele is None:
            if niveau_plancher == "aucun":
                self._enregistrer_repli(conv)
            return
        if _strictement_plus_haut(niveau_modele, niveau_plancher):
            self._traiter(conv, eleve, niveau_modele, motif_modele)

    def _analyser_avec_le_modele(self, eleve: Message, bot: Message) -> tuple[str | None, str]:
        """Renvoie (niveau, motif). niveau vaut None si le modele a echoue ou est illisible."""
        texte = f"MESSAGE DE L'ÉLÈVE :\n{eleve.texte[:3000]}\n\nRÉPONSE DU TUTEUR :\n{bot.texte[:1500]}"
        try:
            brut = self.tuteur.llm.repondre(CONSIGNE, [Tour(role="user", texte=texte)], "rapide")
        except Exception:
            journal.warning("Analyse de vigilance : le modele a echoue", exc_info=True)
            return None, ""
        analyse = extraire_json(brut)
        if analyse is None:
            journal.warning("Analyse de vigilance illisible : %s", brut[:200])
            return None, ""
        return str(analyse.get("niveau") or "aucun"), str(analyse.get("motif") or "")[:300]

    def _enregistrer_repli(self, conv: Conversation) -> None:
        self.tuteur.stockage.ajouter_evenement(
            "vigilance", {"niveau": "faible", "motif": "analyse indisponible"}, conv.id
        )

    def _traiter(self, conv: Conversation, eleve: Message, niveau: str, motif: str) -> None:
        if niveau == "aucun":
            return
        donnees: dict[str, Any] = {"niveau": niveau, "motif": motif[:300]}
        self.tuteur.stockage.ajouter_evenement("vigilance", donnees, conv.id)
        if doit_alerter(niveau, str(self.reglages.get("seuil_alerte", "moyen"))):
            prenom = self.tuteur.profil().prenom
            self.tuteur.notifier(
                f"Jules : attention ({niveau})",
                f"{prenom} a écrit quelque chose qui mérite ton attention.\n"
                f"Motif : {donnees['motif']}\n"
                f"Message : « {eleve.texte[:400]} »\n"
                f"Conversation : {conv.id} (page parent).",
                urgent=True,
            )
