"""Carnet de lecons : ce que Jules retient de ses grosses erreurs de jugement (§8).

Une lecon est une hypothese de travail (« en geometrie, faire refaire une figure seule avant de
conclure »). Elle n'entre qu'apres une surprise, passe un filtre, et n'est gardee que si les epreuves
suivantes dans sa portee lui donnent raison.

Le filtre (§8.2) est ecrit ici et teste : c'est la barriere contre les derives (diagnostic, jugement
de la personne, contournement de la regle « pas de reponse donnee »). Le reste est au lot 6.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from datetime import datetime

from jules.apprentissage.etat import Lecon

TAILLE_MAX = 200
SIMILARITE_DOUBLON = 0.6

# Vocabulaire de diagnostic ou de jugement de la personne : une lecon decrit un comportement de travail
# et la facon dont Jules doit y repondre, jamais ce que l'eleve « est ». Racines, comparees sans accents.
MOTS_INTERDITS: tuple[str, ...] = (
    # diagnostic
    "dys", "tdah", "tda", "hyperactiv", "trouble", "handicap", "autis", "asperger", "haut potentiel",
    "hpi", "surdou", "precoce", "depress", "anxieu", "anxiete", "phobi", "patholog", "diagnost",
    "syndrome", "deficit", "lent d'esprit", "neuro", "psychiatr", "psycholog", "medic",
    "therap", "orthophon",
    # jugement de la personne
    "paresseu", "feignant", "faineant", "bete", "idiot", "stupide", "nul", "incapable",
    "mauvais eleve", "pas doue", "manque d'intelligence", "intelligent", "menteu", "mensong", "trich",
    "capricieu", "immature", "de mauvaise foi",
)  # fmt: skip

# Une lecon ne peut pas pousser Jules a faire le travail a la place de l'eleve (regle 1 de l'essai).
CONTOURNEMENTS: tuple[str, ...] = (
    "donne la reponse", "donner la reponse", "donne directement", "donner directement", "donne-lui la reponse",
    "donne la solution", "donner la solution", "fais-le a sa place", "fais le a sa place", "faire a sa place",
    "ecris-lui", "redige pour", "corrige directement", "ne pas la faire essayer", "ne pas le faire essayer",
    "saute la tentative", "sans la faire essayer", "sans le faire essayer",
)  # fmt: skip

# Personnes tierces : le carnet ne parle que de l'eleve et de Jules.
TIERS: tuple[str, ...] = (
    "sa mere", "son pere", "sa maman", "son papa", "ses parents", "le parent", "la prof", "le prof",
    "professeur", "enseignant", "sa soeur", "son frere", "ses amis", "son ami", "sa copine", "son copain",
    "camarade",
)  # fmt: skip


def sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFD", texte.casefold())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn").replace("’", "'")


def _contient(texte: str, racines: Sequence[str]) -> str | None:
    t = sans_accents(texte)
    for racine in racines:
        # debut de mot : « nul » bloque « nulle » mais pas « annuler »
        if re.search(r"(?<![a-z])" + re.escape(racine), t):
            return racine
    return None


def mots(texte: str) -> set[str]:
    return {m for m in re.findall(r"[a-z0-9']+", sans_accents(texte)) if len(m) > 2}


def similarite(a: str, b: str) -> float:
    """Jaccard sur les mots de plus de 2 lettres, sans accents."""
    ma, mb = mots(a), mots(b)
    if not ma or not mb:
        return 0.0
    return len(ma & mb) / len(ma | mb)


def motif_refus(lecon: Lecon, actives: Sequence[Lecon]) -> str | None:
    """§8.2 : None si la lecon est acceptable, sinon la raison du refus (journalisee)."""
    texte = lecon.texte.strip()
    if not texte:
        return "texte vide"
    if len(texte) > TAILLE_MAX:
        return f"plus de {TAILLE_MAX} caracteres"
    if lecon.portee not in ("notion", "matiere", "global"):
        return f"portee inconnue : {lecon.portee}"
    if lecon.sens not in ("surestimation", "sous_estimation"):
        return f"sens inconnu : {lecon.sens}"
    if racine := _contient(texte, MOTS_INTERDITS):
        return f"vocabulaire de diagnostic ou de jugement : « {racine} »"
    if racine := _contient(texte, CONTOURNEMENTS):
        return f"contourne la regle « l'eleve essaie d'abord » : « {racine} »"
    if racine := _contient(texte, TIERS):
        return f"parle d'une autre personne : « {racine} »"
    for autre in actives:
        if autre.statut == "retiree" or (autre.portee, autre.cle, autre.sens) != (lecon.portee, lecon.cle, lecon.sens):
            continue
        if similarite(texte, autre.texte) >= SIMILARITE_DOUBLON:
            return f"double la lecon {autre.id}"
    return None


# Modele 'principal'. Ne demande qu'une lecon, et laisse le droit de n'en proposer aucune.
CONSIGNE_LECON = """Tu es le tuteur IA d'un élève de collège. Tu t'étais trompé sur lui : tu pensais
qu'une notion {sens_phrase}, et l'épreuve sans aide de quelques jours plus tard a montré le contraire.
On te donne la séance où tu avais porté ce jugement, puis l'épreuve.

Cherche ce qui, dans TA façon de faire pendant la séance, t'a induit en erreur, et écris UNE consigne
pour toi-même qui aurait évité l'erreur. Exemples de bonnes consignes :
- « En géométrie, faire refaire une figure seule avant de conclure qu'elle est comprise. »
- « Quand l'élève dit "ok j'ai compris", demander un exemple avec d'autres nombres avant de valider. »
- « Sur les accords du participe passé, ne pas compter une réussite obtenue après un indice fort. »

Interdits absolus : parler de ce que l'élève « est » (caractère, capacités, troubles, diagnostic) ;
parler d'une autre personne ; proposer de donner une réponse, une solution ou un indice qui la contient.
Si rien dans la séance n'explique l'erreur (l'élève a peut-être juste oublié), n'invente rien.

Réponds UNIQUEMENT par un objet JSON :
{{"lecon": null}}  ou
{{"lecon": {{"portee": "notion|matiere|global", "texte": "... (200 caractères max)"}}}}"""


def evaluer(lecon: Lecon, maintenant: datetime, min_confirmation: int = 3, min_retrait: int = 5) -> Lecon:
    """§8.3 : confirmee, retiree ou toujours active, d'apres les pertes avant et apres. Lot 6.

    - confirmee si len(pertes_apres) >= min_confirmation et moyenne(avant) - moyenne(apres) > 0 ;
    - retiree si len(pertes_apres) >= min_retrait et l'ecart est <= 0 (motif « n'a pas aide ») ;
    - retiree si aucune epreuve dans la portee depuis expiration_jours (motif « expiree »).
    Sans perte « avant » (lecon ecrite des la premiere epreuve de sa portee), la reference est la
    perte de l'epreuve qui l'a declenchee.
    """
    raise NotImplementedError("lot 6 : docs/MODELE-ELEVE.md §8.3")


def elaguer(lecons: Sequence[Lecon], max_lecons: int) -> list[Lecon]:
    """§8.3 budget : au-dela de max_lecons actives, retirer d'abord les non confirmees, les plus anciennes
    en premier. Lot 6."""
    raise NotImplementedError("lot 6 : docs/MODELE-ELEVE.md §8.3")


def pour_le_prompt(lecons: Sequence[Lecon], matiere: str | None, notion: str | None, maximum: int) -> list[Lecon]:
    """§8.4 : lecons actives ou confirmees de portee globale, de la matiere, de la notion ; confirmees
    d'abord, puis les plus recentes ; au plus `maximum`. Lot 6."""
    raise NotImplementedError("lot 6 : docs/MODELE-ELEVE.md §8.4")
