"""Générateur déterministe pour la notion `pourcentages-coefficient-multiplicateur` (mathématiques, 3e).

Écrit avec le GABARIT et les briques communes, sans rien y ajouter : c'est l'épreuve du patron.

  - coefficient : passer d'un pourcentage d'évolution au coefficient, et inversement   (nombre)
  - appliquer   : nouveau prix après une hausse ou une baisse                           (nombre)
  - taux        : retrouver le pourcentage d'évolution entre deux prix                  (nombre)
  - initial     : retrouver le prix avant l'évolution (diviser par le coefficient)      (nombre)
  - successives : deux évolutions à la suite, taux global (elles ne s'additionnent pas) (nombre)

Les prix sont tirés pour que tout tombe juste (le pas dépend du taux) ; les calculs se font en
fractions exactes ; les pièges sont les erreurs de 3e connues : additionner le pourcentage comme
des euros, inverser le sens, confondre taux et coefficient, retrancher au lieu de diviser.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from fractions import Fraction
from typing import Any

from jules.generateurs.briques import exercice_v2, generer_notion, palier, piege_diagnostic, piege_valeur
from jules.generateurs.briques.format_fr import nombre_fr, nombre_machine, prix_fr
from jules.generateurs.briques.habillage import article
from jules.generateurs.briques.tirage import collision, entier_multiple, tirer

NOTION = "pourcentages-coefficient-multiplicateur"
VARIANTES = ("coefficient", "appliquer", "taux", "initial", "successives")

_PALIERS = {
    # difficulté : (taux possibles, prix minimal, prix maximal)
    1: ((10, 20, 25, 50), 20, 200),
    2: ((5, 15, 30, 40, 60, 75, 80, 90), 40, 500),
    3: ((2, 4, 8, 12, 35, 45, 65, 150), 50, 2000),
}
_MOT = {True: ("augmente", "hausse"), False: ("baisse", "baisse")}


def _coefficient(taux: int, hausse: bool) -> Fraction:
    return Fraction(100 + taux if hausse else 100 - taux, 100)


def _tirer_evolution(rng: random.Random, difficulte: int) -> tuple[int, bool]:
    """(taux, hausse ?). Une baisse de 100 % ou plus n'a pas de sens : au-delà de 99, seulement des hausses."""
    taux_possibles, _, _ = palier(_PALIERS, difficulte)
    taux = rng.choice(taux_possibles)
    hausse = True if taux >= 100 else rng.choice((True, False))
    return taux, hausse


def _tirer_prix(rng: random.Random, difficulte: int, taux: int, accepte: Callable[[int], bool] = lambda p: True) -> int:
    """Un prix « rond » dont le pourcentage tombe juste (pas = 100 / pgcd(100, taux)), filtré par `accepte`.

    Le filtre sert à écarter les tirages où la réponse apparaîtrait dans une valeur citée par les indices
    (prix de 100 €, taux égal au prix...) : voir `collision` dans briques/tirage.py.
    """
    _, minimum, maximum = palier(_PALIERS, difficulte)
    pas = 100 // math.gcd(100, taux)
    return tirer(rng, lambda: entier_multiple(rng, pas, minimum, maximum), accepte)


# --- variante 1 : taux <-> coefficient --------------------------------------------------------------------


def _coefficient_variante(rng: random.Random, difficulte: int) -> dict[str, Any]:
    taux, hausse = _tirer_evolution(rng, difficulte)
    coef = _coefficient(taux, hausse)
    verbe, nom = _MOT[hausse]
    sens_inverse = _coefficient(taux, not hausse) if taux < 100 else None
    if rng.random() < 0.5:  # du pourcentage au coefficient
        enonce = rng.choice(
            (
                f"Un prix {verbe} de {taux} %. Par quel nombre faut-il le multiplier pour obtenir le nouveau prix ?",
                f"Quel est le coefficient multiplicateur associé à une {nom} de {taux} % ?",
            )
        )
        pieges = [
            piege_valeur(
                taux, f"{taux} est le pourcentage. On cherche le nombre par lequel on multiplie l'ancien prix."
            ),
            piege_valeur(
                nombre_machine(Fraction(taux, 100)),
                f"{nombre_fr(Fraction(taux, 100))}, c'est {taux} % tout seul. Le nouveau prix, c'est l'ancien prix "
                f"EN ENTIER {'plus' if hausse else 'moins'} {taux} % de l'ancien prix.",
            ),
            piege_valeur(
                100 + taux if hausse else 100 - taux,
                "Tu as trouvé le pourcentage final par rapport à l'ancien prix. Le coefficient, c'est ce nombre "
                "divisé par 100.",
            ),
        ]
        if sens_inverse is not None:
            pieges.append(
                piege_valeur(
                    nombre_machine(sens_inverse),
                    f"C'est le coefficient d'une {_MOT[not hausse][1]} de {taux} %. Ici, le prix {verbe}.",
                )
            )
        pieges.append(
            piege_diagnostic("valeur_fausse", "Écris le pourcentage final par rapport à 100, puis divise par 100.")
        )
        return exercice_v2(
            id=f"coefficient-{nom}-{taux}",
            type="nombre",
            difficulte=difficulte,
            enonce=enonce,
            reponse={"valeur": nombre_machine(coef), "forme": "libre"},
            indices={
                "relance": "Si l'ancien prix vaut 100 %, combien vaut le nouveau prix, en pourcentage ?",
                "methode": "Le nouveau prix représente 100 % de l'ancien, plus ou moins le pourcentage d'évolution. "
                "Le coefficient multiplicateur, c'est ce pourcentage final divisé par 100.",
                "etape": f"Le nouveau prix vaut 100 % {'+' if hausse else '−'} {taux} % de l'ancien. "
                "Écris ce pourcentage, puis divise-le par 100.",
            },
            pieges=pieges,
            solution=f"Le nouveau prix vaut (100 {'+' if hausse else '−'} {taux}) % = "
            f"{100 + taux if hausse else 100 - taux} % de l'ancien. Le coefficient multiplicateur est "
            f"{100 + taux if hausse else 100 - taux} ÷ 100 = {nombre_fr(coef)}.",
            lieu=f"{NOTION}/coefficient/{nom}-{taux}",
        )
    # du coefficient au pourcentage d'évolution
    # réponse signée, même convention que `successives` : un seul nombre dit la valeur ET le sens
    taux_signe = taux if hausse else -taux
    enonce = (
        f"Un prix est multiplié par {nombre_fr(coef)}. Quel est le pourcentage d'évolution ? "
        "(Réponds par un nombre négatif si le prix baisse.)"
    )
    pieges = []
    if coef * 100 != -taux_signe:  # baisse de 50 % : 50 est aussi l'erreur de sens, c'est ce piège-là qui parle
        pieges.append(
            piege_valeur(
                nombre_machine(coef * 100),
                f"{nombre_fr(coef * 100)} %, c'est ce que vaut le nouveau prix par rapport à l'ancien. "
                "Le pourcentage d'évolution, c'est ce qui a changé par rapport à 100 %.",
            )
        )
    pieges += [
        piege_valeur(
            nombre_machine(coef),
            "C'est le coefficient, pas un pourcentage. Compare-le à 1 : de combien de centièmes s'en éloigne-t-il ?",
        ),
        piege_valeur(
            -taux_signe,
            "Le nombre est bon, mais pas le sens. Le coefficient est-il plus grand ou plus petit que 1 ?",
        ),
        piege_diagnostic("valeur_fausse", "Écris le coefficient en pourcentage (× 100), puis compare à 100 %."),
    ]
    return exercice_v2(
        id=f"coefficient-inverse-{nom}-{taux}",
        type="nombre",
        difficulte=difficulte,
        enonce=enonce,
        reponse={"valeur": taux_signe, "forme": "libre"},
        indices={
            "relance": "Ce coefficient est-il plus grand ou plus petit que 1 ? Que dit cela sur le prix ?",
            "methode": "Un coefficient multiplicateur, c'est un pourcentage divisé par 100. Remultiplie-le par 100 "
            "pour retrouver ce que vaut le nouveau prix, puis regarde l'écart avec 100 %.",
            "etape": "Multiplie le coefficient par 100 : tu obtiens le nouveau prix en pourcentage de l'ancien. "
            f"Il est {'plus grand' if hausse else 'plus petit'} que 100 : de combien ?",
        },
        pieges=pieges,
        solution=f"{nombre_fr(coef)} = {nombre_fr(coef * 100)} ÷ 100 : le nouveau prix vaut {nombre_fr(coef * 100)} % "
        f"de l'ancien, soit une {nom} de {taux} % (réponse : {nombre_fr(taux_signe)}).",
        lieu=f"{NOTION}/coefficient-inverse/{nom}-{taux}",
    )


# --- variante 2 : appliquer une évolution ----------------------------------------------------------------


def _appliquer(rng: random.Random, difficulte: int) -> dict[str, Any]:
    taux, hausse = _tirer_evolution(rng, difficulte)
    coef = _coefficient(taux, hausse)
    # la réponse (nouveau prix) ne doit apparaître ni dans le taux, ni dans le prix, ni dans le coefficient cités
    # (à 50 % de baisse, la variation vaut la réponse : ce piège-là est simplement écarté par exercice_v2)
    prix = _tirer_prix(rng, difficulte, taux, lambda p: not collision(p * coef, taux, p, coef))
    variation = Fraction(prix * taux, 100)
    nouveau = prix * coef
    verbe, nom = _MOT[hausse]
    art = article(rng)
    pieges = [
        piege_valeur(
            nombre_machine(variation),
            f"{prix_fr(variation)}, c'est de combien le prix change. On demande le nouveau prix.",
        ),
    ]
    # le sens inverse n'existe pas au-delà de 100 % (une baisse de 150 % n'a pas de sens) : pas de piège
    if taux < 100:
        pieges.append(
            piege_valeur(
                nombre_machine(prix * _coefficient(taux, not hausse)),
                f"Tu as fait une {_MOT[not hausse][1]}. Ici, le prix {verbe} de {taux} %.",
            )
        )
    en_euros = prix + taux if hausse else prix - taux
    if en_euros > 0:  # un prix négatif ou nul n'est pas une erreur qu'un élève écrit
        pieges.append(
            piege_valeur(
                en_euros,
                f"{taux} %, ce n'est pas {taux} €. Un pourcentage se calcule par rapport au prix de départ.",
            )
        )
    pieges.append(
        piege_diagnostic("valeur_fausse", f"Calcule d'abord {taux} % de {prix_fr(prix)}, puis applique le bon sens.")
    )
    return exercice_v2(
        id=f"appliquer-{nom}-{taux}-{prix}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"{art.Nom} coûte {prix_fr(prix)}. Son prix {verbe} de {taux} %. Quel est le nouveau prix de {art.le} ?",
        reponse={"valeur": nombre_machine(nouveau), "forme": "libre"},
        indices={
            "relance": f"Combien font {taux} % de {prix_fr(prix)} ? Ensuite, faut-il l'ajouter ou le retirer ?",
            "methode": f"Méthode directe : multiplie le prix par le coefficient multiplicateur d'une {nom} "
            f"de {taux} %. Méthode en deux temps : calcule {taux} % du prix, puis "
            f"{'ajoute-le' if hausse else 'retire-le'}.",
            "etape": f"Le coefficient d'une {nom} de {taux} % est {nombre_fr(coef)}. "
            f"Multiplie {prix_fr(prix)} par ce coefficient.",
        },
        pieges=pieges,
        solution=f"Coefficient d'une {nom} de {taux} % : {nombre_fr(coef)}. Nouveau prix : "
        f"{nombre_fr(prix)} × {nombre_fr(coef)} = {nombre_fr(nouveau)} €. (Vérification : {taux} % de "
        f"{nombre_fr(prix)} € font {nombre_fr(variation)} €, et {nombre_fr(prix)} {'+' if hausse else '−'} "
        f"{nombre_fr(variation)} = {nombre_fr(nouveau)}.)",
        lieu=f"{NOTION}/appliquer/{nom}-{taux}-{prix}",
    )


# --- variante 3 : retrouver le taux ---------------------------------------------------------------------------


def _taux(rng: random.Random, difficulte: int) -> dict[str, Any]:
    taux, hausse = _tirer_evolution(rng, difficulte)
    coef = _coefficient(taux, hausse)
    # la réponse (le taux) ne doit apparaître dans aucune valeur citée par les indices : prix, variation
    # (le coefficient d'une hausse s'écrit 1,<taux> : il n'est cité que dans la solution, jamais dans un indice)
    prix = _tirer_prix(rng, difficulte, taux, lambda p: not collision(taux, p, abs(p * coef - p)))
    nouveau = prix * coef
    variation = abs(nouveau - prix)
    _, nom = _MOT[hausse]
    art = article(rng)
    pieges = [
        piege_valeur(
            nombre_machine(variation),
            f"{prix_fr(variation)}, c'est la variation en euros. "
            "Un pourcentage compare cette variation au prix de départ.",
        ),
        piege_valeur(
            nombre_machine(coef),
            "C'est le coefficient multiplicateur, pas le pourcentage d'évolution. Que vaut-il en pourcentage, "
            "et à combien de 100 % cela correspond-il ?",
        ),
    ]
    sur_final = variation / nouveau * 100
    if sur_final.denominator == 1:  # sinon l'erreur ne donne pas un nombre « propre » : pas de piège dédié
        pieges.append(
            piege_valeur(
                nombre_machine(sur_final),
                "Tu as comparé la variation au nouveau prix. Un pourcentage d'évolution se calcule "
                "par rapport au prix de DÉPART.",
            )
        )
    pieges.append(piege_diagnostic("valeur_fausse", "Variation ÷ prix de départ, puis × 100."))
    return exercice_v2(
        id=f"taux-{nom}-{taux}-{prix}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Le prix {art.du} passe de {prix_fr(prix)} à {prix_fr(nouveau)}. "
        f"De quel pourcentage a-t-il {'augmenté' if hausse else 'baissé'} ?",
        reponse={"valeur": taux, "forme": "libre"},
        indices={
            "relance": "De combien d'euros le prix a-t-il changé ? Et par rapport à quel prix faut-il comparer ?",
            "methode": "Pourcentage d'évolution = variation ÷ prix de départ, puis × 100. "
            "Autre chemin : nouveau prix ÷ prix de départ donne le coefficient, à lire en pourcentage.",
            "etape": f"La variation est de {prix_fr(variation)}. "
            f"Quelle fraction de {prix_fr(prix)} cela représente-t-il ?",
        },
        pieges=pieges,
        solution=f"Variation : {nombre_fr(variation)} €. "
        f"{nombre_fr(variation)} ÷ {nombre_fr(prix)} = {nombre_fr(variation / prix)}, soit {taux} % : "
        f"le prix a {'augmenté' if hausse else 'baissé'} de {taux} %. "
        f"(Coefficient : {nombre_fr(nouveau)} ÷ {nombre_fr(prix)} = {nombre_fr(coef)}.)",
        lieu=f"{NOTION}/taux/{nom}-{taux}-{prix}",
    )


# --- variante 4 : retrouver le prix initial -------------------------------------------------------------------


def _initial(rng: random.Random, difficulte: int) -> dict[str, Any]:
    taux, hausse = _tirer_evolution(rng, difficulte)
    coef = _coefficient(taux, hausse)
    # la réponse (l'ancien prix) ne doit apparaître ni dans le taux, ni dans le nouveau prix, ni dans le coefficient
    prix = _tirer_prix(rng, difficulte, taux, lambda p: not collision(p, taux, p * coef, coef))
    nouveau = prix * coef
    _, nom = _MOT[hausse]
    art = article(rng)
    pieges = []
    if taux < 100:  # au-delà, le sens inverse n'a pas de sens : pas de piège
        pieges.append(
            piege_valeur(
                nombre_machine(nouveau * _coefficient(taux, not hausse)),
                f"Tu as appliqué une {_MOT[not hausse][1]} de {taux} % au nouveau prix. Mais {taux} % du nouveau "
                f"prix, ce n'est pas {taux} % de l'ancien : pour revenir en arrière, on divise par le coefficient.",
            )
        )
    pieges += [
        piege_valeur(
            nombre_machine(nouveau - taux if hausse else nouveau + taux),
            f"{taux} %, ce n'est pas {taux} €.",
        ),
        piege_valeur(
            nombre_machine(nouveau * coef),
            f"Tu as appliqué la {nom} une deuxième fois. On cherche le prix d'AVANT.",
        ),
        piege_diagnostic(
            "valeur_fausse", "Ancien prix × coefficient = nouveau prix. Quelle opération isole l'ancien prix ?"
        ),
    ]
    return exercice_v2(
        id=f"initial-{nom}-{taux}-{prix}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Après une {nom} de {taux} %, {art.nom} coûte {prix_fr(nouveau)}. "
        f"Quel était le prix de {art.le} avant cette {nom} ?",
        reponse={"valeur": prix, "forme": "libre"},
        indices={
            "relance": f"Par quel coefficient l'ancien prix a-t-il été multiplié pour arriver à {prix_fr(nouveau)} ?",
            "methode": "Pour revenir au prix de départ, on divise le nouveau prix par le coefficient multiplicateur. "
            "On ne retranche pas le pourcentage : il portait sur l'ancien prix, pas sur le nouveau.",
            "etape": f"Ancien prix × {nombre_fr(coef)} = {nombre_fr(nouveau)}. Quelle opération donne l'ancien prix ?",
        },
        pieges=pieges,
        solution=f"Coefficient d'une {nom} de {taux} % : {nombre_fr(coef)}. Ancien prix : "
        f"{nombre_fr(nouveau)} ÷ {nombre_fr(coef)} = {nombre_fr(prix)} €. (Vérification : {nombre_fr(prix)} × "
        f"{nombre_fr(coef)} = "
        f"{nombre_fr(nouveau)}.)",
        lieu=f"{NOTION}/initial/{nom}-{taux}-{prix}",
    )


# --- variante 5 : deux évolutions successives -------------------------------------------------------------------


def _successives(rng: random.Random, difficulte: int) -> dict[str, Any]:
    def deux() -> tuple[tuple[int, bool], tuple[int, bool]]:
        return _tirer_evolution(rng, difficulte), _tirer_evolution(rng, difficulte)

    def acceptable(paire: tuple[tuple[int, bool], tuple[int, bool]]) -> bool:
        (t1, h1), (t2, h2) = paire
        c1, c2 = _coefficient(t1, h1), _coefficient(t2, h2)
        global_ = c1 * c2
        if difficulte == 1 and (global_ * 100).denominator != 1:  # en difficulté 1, un taux global entier
            return False
        if global_ == 1:  # un retour exact au prix de départ : joli, mais la réponse 0 déroute plus qu'elle n'apprend
            return False
        # la réponse (taux global) ne doit apparaître dans aucune valeur citée par les indices : les coefficients
        return not collision(abs((global_ - 1) * 100), c1, c2)

    (t1, h1), (t2, h2) = tirer(rng, deux, acceptable)
    c1, c2 = _coefficient(t1, h1), _coefficient(t2, h2)
    global_ = c1 * c2
    taux_global = (global_ - 1) * 100  # signé : négatif pour une baisse
    somme = (t1 if h1 else -t1) + (t2 if h2 else -t2)
    pieges = [
        piege_valeur(
            somme,
            "Tu as additionné les deux pourcentages. Ils ne portent pas sur le même prix : le deuxième "
            "s'applique au prix déjà modifié. Passe par les coefficients.",
        ),
        piege_valeur(
            nombre_machine(global_),
            "C'est le coefficient global. Convertis-le en pourcentage d'évolution (compare-le à 1).",
        ),
        piege_valeur(
            nombre_machine(-taux_global),
            "Le nombre est bon, mais pas le sens. Le coefficient global est-il plus grand ou plus petit que 1 ?",
        ),
        piege_diagnostic("valeur_fausse", "Multiplie les deux coefficients, puis lis le résultat en pourcentage."),
    ]
    return exercice_v2(
        id=f"successives-{'h' if h1 else 'b'}{t1}-{'h' if h2 else 'b'}{t2}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Le prix d'un article {_MOT[h1][0]} de {t1} %, puis {_MOT[h2][0]} de {t2} %. "
        "Quel est le pourcentage d'évolution global ? (Réponds par un nombre négatif si le prix a baissé au total.)",
        reponse={"valeur": nombre_machine(taux_global), "forme": "libre"},
        indices={
            "relance": "Peut-on additionner deux pourcentages qui ne portent pas sur le même prix ?",
            "methode": "Trouve le coefficient multiplicateur de chaque évolution, puis multiplie-les : le produit est "
            "le coefficient global. Lis-le ensuite en pourcentage d'évolution.",
            "etape": f"Les coefficients sont {nombre_fr(c1)} et {nombre_fr(c2)}. Multiplie-les, puis compare le "
            "résultat à 1.",
        },
        pieges=pieges,
        solution=f"Coefficients : {nombre_fr(c1)} et {nombre_fr(c2)}. Coefficient global : "
        f"{nombre_fr(c1)} × {nombre_fr(c2)} = {nombre_fr(global_)}, "
        f"soit {nombre_fr(global_ * 100)} % de l'ancien prix : "
        f"une {'hausse' if taux_global > 0 else 'baisse'} de {nombre_fr(abs(taux_global))} % "
        f"(taux global : {nombre_fr(taux_global)} %).",
        lieu=f"{NOTION}/successives/{t1}-{t2}",
    )


# --- point d'entrée ---------------------------------------------------------------------------------------------

_VARIANTES = {
    "coefficient": _coefficient_variante,
    "appliquer": _appliquer,
    "taux": _taux,
    "initial": _initial,
    "successives": _successives,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
