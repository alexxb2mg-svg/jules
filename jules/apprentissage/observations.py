"""Observations : ce qu'un echange montre, en faits verifiables (docs/MODELE-ELEVE.md, §2 et §3).

Le modele de langage CONSTATE (tentative, justesse, aide recue, ton) ; il ne donne jamais de nombre.
La conversion en observations elementaires (capteur, valeur, poids) est deterministe et testee ici.
L'appel au modele et la lecture de la conversation vivent dans la brique jules/modules/modele_eleve.py.
"""

from __future__ import annotations

from typing import Any

from jules.apprentissage.etat import Observation, cle_notion
from jules.apprentissage.parametres import Parametres
from jules.modules.base import extraire_json

RESULTATS = ("juste", "partiel", "faux", "sans_objet")
AFFECTS = ("neutre", "hesitant", "frustre", "decourage", "enthousiaste")
CERTITUDES = ("haute", "moyenne", "basse")

# Modele 'principal' obligatoire (§2). Les exemples sont volontairement des cas limites : c'est la
# ou un extracteur se trompe (aide donnee dans le meme message, « ok j'ai compris » sans preuve...).
CONSIGNE = """Tu observes un échange entre un élève de collège et son tuteur IA. Tu ne juges pas l'élève
et tu ne donnes aucune note : tu CONSTATES des faits, pour un modèle statistique qui fera les calculs.

On te donne les derniers messages. Le DERNIER message de l'élève est celui à analyser ; les messages
précédents servent seulement à savoir quelle aide il avait reçue avant.

Réponds UNIQUEMENT par un objet JSON, sans texte autour :
{"tentatives": [ {...}, ... ]}

Une entrée par tentative distincte dans le dernier message de l'élève (souvent une seule, parfois
zéro, parfois deux si l'élève répond à deux questions). Chaque entrée :
{"matiere": "...", "notion": "...", "tentative": true, "resultat": "juste", "aide": 0,
 "premier_essai": true, "auto_correction": false, "explique_methode": false,
 "declare_compris": false, "affect": "neutre", "certitude": "haute"}

Définitions (lis-les en entier, c'est là que se jouent les erreurs) :
- tentative : l'élève PRODUIT quelque chose à juger (un résultat, un calcul, une phrase, une réponse
  à une question du tuteur). Une question de l'élève, « je sais pas », « attends » ou « ok » ne sont
  PAS des tentatives. S'il n'y a aucune tentative mais que l'élève dit avoir compris ou exprime une
  émotion, fais une seule entrée avec "tentative": false et "resultat": "sans_objet".
- resultat : juge le FOND, pas la forme. "juste" : correct et complet pour la question posée.
  "partiel" : démarche correcte avec une erreur mineure (étourderie de calcul, accord oublié),
  ou réponse correcte mais incomplète. "faux" : erreur de méthode ou de notion. "sans_objet" : pas de
  tentative. Si tu ne peux pas vérifier (photo illisible, énoncé inconnu), mets "sans_objet" et
  "certitude": "basse" : ne devine jamais.
- aide : l'aide que le tuteur a donnée SUR CETTE MARCHE avant la tentative. 0 : aucune (ou seulement
  « essaie », « à toi »). 1 : relance par une question ouverte (« qu'est-ce que l'énoncé demande ? »).
  2 : indice qui oriente (rappel de la règle, « pense au dénominateur commun »). 3 : indice fort, qui
  contient presque la réponse, ou exemple résolu très proche. Compte l'aide la plus forte reçue sur
  cette marche, pas seulement celle du dernier message.
- premier_essai : true si c'est la première tentative de l'élève sur cette marche précise.
- auto_correction : true seulement si l'élève repère ET corrige lui-même une erreur qu'on ne lui a
  pas montrée (« ah non, j'ai oublié de simplifier : 3/4 »). Une correction après que le tuteur a
  pointé l'erreur n'en est pas une.
- explique_methode : true si l'élève formule correctement, avec ses mots, la méthode ou la règle
  (pas seulement le résultat).
- declare_compris : true si l'élève dit avoir compris (« ok j'ai compris », « c'est bon je vois »),
  qu'il le prouve ou non dans le même message.
- affect : d'après les mots seulement, sans psychologie. "frustre" : agacement explicite (« j'en ai
  marre », « c'est nul »). "decourage" : abandon (« je suis nul », « j'y arriverai jamais »).
  "hesitant" : doute exprimé (« je crois que… ? », « peut-être »). "enthousiaste" : joie explicite.
  "neutre" sinon, et en cas de doute.
- certitude : ta confiance dans TA lecture. "basse" si la photo est floue, si l'énoncé n'est pas
  visible, ou si la justesse dépend d'une information que tu n'as pas.
- matiere : Mathématiques, Français, Anglais, Espagnol, Allemand, Histoire-Géographie, EMC, SVT,
  Physique-Chimie, Technologie, Latin, Musique, Arts plastiques, Autre.
- notion : la notion précise (6 mots max). Si une liste de notions déjà suivies est fournie et que
  c'est la même notion, reprends EXACTEMENT son libellé.

Exemples de cas limites :
- Tuteur : « Pense à mettre au même dénominateur. » Élève : « 1/2 + 1/3 = 5/6 » → juste, aide 2.
- Tuteur : « Qu'est-ce que tu as essayé ? » Élève : « 2/5 » (pour 1/2 + 1/3) → faux, aide 1.
- Élève : « ok j'ai compris merci » (sans rien produire) → tentative false, sans_objet,
  declare_compris true.
- Élève : « 3x = 12 donc x = 36… non attends, x = 4 » → juste, auto_correction true.
- Élève : « J'ai trouvé 12,5 cm » (photo de figure illisible) → sans_objet, certitude basse."""


def _choix(valeur: Any, permis: tuple[str, ...], defaut: str) -> str:
    v = str(valeur or "").strip().lower()
    return v if v in permis else defaut


def _bool(valeur: Any) -> bool:
    return valeur is True or str(valeur).strip().lower() in ("true", "vrai", "oui", "1")


def normaliser_tentative(brut: dict[str, Any]) -> dict[str, Any] | None:
    """Ramene une entree du modele a des valeurs permises ; None si elle est inutilisable."""
    notion = str(brut.get("notion") or "").strip()[:80]
    if not notion:
        return None
    try:
        aide = int(brut.get("aide", 0))
    except (TypeError, ValueError):
        aide = 0
    tentative = _bool(brut.get("tentative"))
    resultat = _choix(brut.get("resultat"), RESULTATS, "sans_objet")
    if not tentative:
        resultat = "sans_objet"
    return {
        "matiere": str(brut.get("matiere") or "Autre").strip()[:40],
        "notion": notion,
        "tentative": tentative and resultat != "sans_objet",
        "resultat": resultat,
        "aide": min(3, max(0, aide)),
        "premier_essai": _bool(brut.get("premier_essai", True)),
        "auto_correction": _bool(brut.get("auto_correction")),
        "explique_methode": _bool(brut.get("explique_methode")),
        "declare_compris": _bool(brut.get("declare_compris")),
        "affect": _choix(brut.get("affect"), AFFECTS, "neutre"),
        "certitude": _choix(brut.get("certitude"), CERTITUDES, "basse"),
    }


def lire_extraction(brut: str) -> list[dict[str, Any]]:
    """Reponse brute du modele -> tentatives normalisees (liste vide si illisible)."""
    objet = extraire_json(brut) or {}
    tentatives = objet.get("tentatives")
    if not isinstance(tentatives, list):
        return []
    lues = (normaliser_tentative(t) for t in tentatives if isinstance(t, dict))
    return [t for t in lues if t is not None]


def vers_observations(
    tentative: dict[str, Any], seance: str, horodatage: str, parametres: Parametres
) -> list[Observation]:
    """§3 : une tentative normalisee -> observations elementaires (capteur binaire + poids)."""
    notion = cle_notion(tentative["matiere"], tentative["notion"])
    poids_lecture = parametres.poids_certitude.get(tentative["certitude"], 0.4)
    commun = {"notion": notion, "seance": seance, "horodatage": horodatage, "affect": tentative["affect"]}
    sortie: list[Observation] = []
    if tentative["tentative"] and tentative["resultat"] in ("juste", "partiel", "faux"):
        valeur = 0 if tentative["resultat"] == "faux" else 1
        poids = poids_lecture * (parametres.poids_partiel if tentative["resultat"] == "partiel" else 1.0)
        sortie.append(
            Observation(
                capteur=f"tentative_aide{tentative['aide']}",
                valeur=valeur,
                poids=poids,
                aide=tentative["aide"],
                partiel=tentative["resultat"] == "partiel",
                **commun,
            )
        )
    for drapeau, capteur in (
        ("auto_correction", "auto_correction"),
        ("explique_methode", "explication"),
        ("declare_compris", "declaration"),
    ):
        if tentative[drapeau]:
            sortie.append(Observation(capteur=capteur, valeur=1, poids=poids_lecture, **commun))
    return sortie


def depuis_statut_suivi(donnees: dict[str, Any], seance: str, horodatage: str) -> Observation | None:
    """Le verdict du module suivi devient le capteur `jugement_ia` (compris -> 1, bloque -> 0)."""
    statut = donnees.get("statut")
    if statut not in ("compris", "bloque") or not donnees.get("notion"):
        return None
    return Observation(
        notion=cle_notion(str(donnees.get("matiere") or "Autre"), str(donnees["notion"])),
        capteur="jugement_ia",
        valeur=1 if statut == "compris" else 0,
        poids=1.0,
        seance=seance,
        horodatage=horodatage,
    )
