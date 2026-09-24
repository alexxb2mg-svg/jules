"""Carnet de lecons : ce que Jules retient de ses grosses erreurs de jugement (§8).

Une lecon est une hypothese de travail (« en geometrie, faire refaire une figure seule avant de
conclure »). Elle n'entre qu'apres une surprise, passe un filtre, et n'est gardee que si les epreuves
suivantes dans sa portee lui donnent raison.

Le filtre (§8.2) est ecrit ici et teste : c'est la barriere contre les derives (diagnostic, jugement
de la personne, contournement de la regle « pas de reponse donnee »).

Idees reprises du fonctionnement d'Hermes (agent/background_review.py, agent/curator.py, MIT) :
  - la revue apres coup a le droit de conclure « rien a retenir », et c'est souvent la bonne reponse ;
  - une lecon est une regle generale avec son pourquoi, jamais le recit de l'incident ;
  - la meme lecon apprise deux fois reste UNE lecon (filtre des doublons) ;
  - un budget fixe, et un elagage qui retire sans effacer (statut « retiree », visible du parent) ;
  - l'absence d'usage n'est pas une preuve contre une lecon, mais rien ne reste indefiniment sans
    etre mis a l'epreuve (expiration ancree sur la derniere epreuve, a defaut sur la creation).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import replace
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

# Une lecon entre dans le prompt de toutes les seances suivantes : c'est le meme risque que la memoire
# d'Hermes (tools/memory_tool_store.py, balayage « strict »). Un eleve qui ecrit « ignore tes consignes »
# ne doit pas pouvoir faire recopier sa phrase dans le carnet par la revue apres coup.
INJECTIONS: tuple[str, ...] = (
    # pas de racine seule comme « ignore », « consigne » ou « systeme » : « relire la consigne », « elle ignore
    # la definition » et « systeme d'equations » sont des lecons ou des notions legitimes
    "ignore tes", "ignore les instructions", "ignore les consignes", "ignore ce qui precede", "ignore toutes",
    "oublie tes consignes", "oublie les consignes", "oublie tes instructions", "tes consignes", "tes instructions",
    "prompt", "message systeme", "consigne systeme", "regles de securite", "regle de securite",
    "tu es desormais", "change de role", "nouveau role", "mode developpeur", "sans filtre", "jailbreak",
    "http", "www.", "```", "<!--", "</", "<script",
)  # fmt: skip

# Hermes refuse les « affirmations negatives » dans ses competences (« tel outil ne marche pas ») : elles
# se durcissent en refus que l'agent s'oppose a lui-meme longtemps apres. Ici, l'equivalent est une lecon
# qui fait eviter une notion ou un exercice : elle priverait l'eleve de ce qu'il doit justement travailler.
EVITEMENTS: tuple[str, ...] = (
    "ne plus proposer", "ne plus lui proposer", "ne plus travailler", "eviter la notion", "eviter les exercices",
    "eviter ce type", "ne plus aborder", "laisser tomber", "abandonner la notion", "sauter la notion",
    "ne plus faire de", "ne plus lui donner d'exercice",
)  # fmt: skip

CARACTERES_INVISIBLES = frozenset(
    "\u200b\u200c\u200d\u2060\u2062\u2063\u2064\ufeff\u202a\u202b\u202c\u202d\u202e"
)  # largeur nulle, marques de sens

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
    if any(c in CARACTERES_INVISIBLES for c in texte):
        return "caractere invisible (texte cache)"
    if racine := _contient(texte, INJECTIONS):
        return f"ressemble a une instruction a recopier dans le prompt : « {racine} »"
    if racine := _contient(texte, MOTS_INTERDITS):
        return f"vocabulaire de diagnostic ou de jugement : « {racine} »"
    if racine := _contient(texte, CONTOURNEMENTS):
        return f"contourne la regle « l'eleve essaie d'abord » : « {racine} »"
    if racine := _contient(texte, EVITEMENTS):
        return f"fait eviter une notion au lieu de changer la facon de l'enseigner : « {racine} »"
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


def dans_la_portee(lecon: Lecon, notion: str) -> bool:
    """Une epreuve sur `notion` (« Matiere : notion ») concerne-t-elle cette lecon ?"""
    if lecon.portee == "global":
        return True
    if lecon.portee == "matiere":
        return notion.split(" : ", 1)[0] == lecon.cle
    return notion == lecon.cle


def enregistrer_epreuve(lecons: Sequence[Lecon], notion: str, perte: float, horodatage: str) -> list[Lecon]:
    """Ajoute la perte d'une epreuve a toutes les lecons non retirees dont elle releve (§8.3).

    Une lecon creee apres l'epreuve (meme instant compris) ne la compte pas : c'est cette epreuve qui
    l'a peut-etre declenchee, elle sert de reference « avant », pas de preuve « apres ».
    """
    sortie = []
    for lecon in lecons:
        if lecon.statut != "retiree" and dans_la_portee(lecon, notion) and lecon.creee < horodatage:
            lecon = replace(lecon, pertes_apres=[*lecon.pertes_apres, perte], derniere_epreuve=horodatage)
        sortie.append(lecon)
    return sortie


def _moyenne(valeurs: Sequence[float]) -> float:
    return sum(valeurs) / len(valeurs)


def evaluer(
    lecon: Lecon,
    maintenant: datetime,
    min_confirmation: int = 3,
    min_retrait: int = 5,
    expiration_jours: int = 45,
) -> Lecon:
    """§8.3 : confirmee, retiree ou toujours active, d'apres les pertes avant et apres.

    - confirmee si len(pertes_apres) >= min_confirmation et moyenne(avant) - moyenne(apres) > 0 ;
    - retiree si len(pertes_apres) >= min_retrait et l'ecart est <= 0 (« n'a pas aide ») ; une lecon
      confirmee peut encore etre retiree si les epreuves suivantes la dementent ;
    - retiree si aucune epreuve dans la portee depuis expiration_jours (« expiree »), l'ancre etant la
      derniere epreuve ou, a defaut, la creation : l'absence d'epreuve n'est pas une preuve contre la
      lecon, mais une lecon jamais mise a l'epreuve ne doit pas rester indefiniment dans le prompt.
    Sans perte « avant », la lecon reste active : il n'y a rien a quoi comparer.
    """
    if lecon.statut == "retiree":
        return lecon
    ancre = lecon.derniere_epreuve or lecon.creee
    if (maintenant - datetime.fromisoformat(ancre)).total_seconds() > expiration_jours * 86400:
        return replace(lecon, statut="retiree", motif_retrait="expiree")
    if not lecon.pertes_avant or len(lecon.pertes_apres) < min_confirmation:
        return lecon
    ecart = _moyenne(lecon.pertes_avant) - _moyenne(lecon.pertes_apres)
    if len(lecon.pertes_apres) >= min_retrait and ecart <= 0:
        return replace(lecon, statut="retiree", motif_retrait="n'a pas aide")
    if ecart > 0:
        return replace(lecon, statut="confirmee")
    return replace(lecon, statut="active")


def elaguer(lecons: Sequence[Lecon], max_lecons: int) -> list[Lecon]:
    """§8.3 budget : au-dela de max_lecons non retirees, retirer d'abord les non confirmees, les plus
    anciennes en premier ; puis, s'il le faut, les confirmees les plus anciennes. Ordre conserve."""
    vivantes = [lecon for lecon in lecons if lecon.statut != "retiree"]
    exces = len(vivantes) - max_lecons
    if exces <= 0:
        return list(lecons)
    ordre = sorted(vivantes, key=lambda lecon: (lecon.statut == "confirmee", lecon.creee))
    a_retirer = {lecon.id for lecon in ordre[:exces]}
    return [
        replace(lecon, statut="retiree", motif_retrait="budget") if lecon.id in a_retirer else lecon for lecon in lecons
    ]


def pour_le_prompt(lecons: Sequence[Lecon], matiere: str | None, notion: str | None, maximum: int) -> list[Lecon]:
    """§8.4 : lecons actives ou confirmees de portee globale, de la matiere, de la notion ; confirmees
    d'abord, puis les plus recentes ; au plus `maximum`."""

    def pertinente(lecon: Lecon) -> bool:
        if lecon.statut == "retiree":
            return False
        if lecon.portee == "global":
            return True
        if lecon.portee == "matiere":
            return matiere is not None and lecon.cle == matiere
        return notion is not None and lecon.cle == notion

    choisies = [lecon for lecon in lecons if pertinente(lecon)]
    choisies.sort(key=lambda lecon: (lecon.statut != "confirmee", _rang_inverse(lecon.creee)))
    return choisies[:maximum]


def _rang_inverse(horodatage: str) -> float:
    return -datetime.fromisoformat(horodatage).timestamp()
