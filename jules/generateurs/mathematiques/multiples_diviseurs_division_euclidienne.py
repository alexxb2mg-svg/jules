"""Générateur déterministe pour la notion `multiples-diviseurs-division-euclidienne` (mathématiques, 3e).

  - division             : quotient ou reste d'une division euclidienne (en situation au palier 3) (nombre entier)
  - criteres             : divisible par 2, 3, 5, 9, 10 ?                                      (choix multiple)
  - nb_diviseurs         : combien de diviseurs a un nombre ?                                  (nombre entier)
  - completer            : plus petit entier à ajouter pour obtenir un multiple de 3, 5 ou 9   (nombre entier)
  - multiple_ou_diviseur : « 7 est un diviseur de 91 », « 91 est un multiple de 7 »…           (choix multiple)

Pièges de la fiche v2 : lire le reste dans les décimales du quotient (187 ÷ 12 ≈ 15,58, reste « 58 »),
confondre multiple et diviseur, appliquer le critère de 3 ou 9 au dernier chiffre, oublier 1 et le
nombre lui-même dans les diviseurs, compter deux fois la racine d'un carré (6 × 6 = 36).
"""

from __future__ import annotations

import random
from typing import Any

from jules.generateurs.briques import (
    exercice_v2,
    generer_notion,
    palier,
    piege_contient,
    piege_diagnostic,
    piege_valeur,
)
from jules.generateurs.briques.format_fr import nombre_fr
from jules.generateurs.briques.habillage import personnage
from jules.generateurs.briques.tirage import collision, tirer

NOTION = "multiples-diviseurs-division-euclidienne"
VARIANTES = ("division", "criteres", "nb_diviseurs", "completer", "multiple_ou_diviseur")

_LETTRES = "abcdef"


def _diviseurs(n: int) -> list[int]:
    return [d for d in range(1, n + 1) if n % d == 0]


def _somme_chiffres(n: int) -> int:
    return sum(int(c) for c in str(n))


# --- variante 1 : division euclidienne -------------------------------------------------------------------

_PALIERS_DIVISION = {
    # difficulté : (diviseurs possibles, dividende minimal, dividende maximal)
    1: (range(2, 10), 20, 99),
    2: (range(11, 26), 100, 500),
    3: (range(6, 31), 50, 400),
}
_BOITES = (
    # (objets, contenants, les contenants sont féminins ?)
    ("œufs", "boîtes", True),
    ("photos", "pages d'album", True),
    ("biscuits", "sachets", False),
    ("passagers", "minibus", False),
    ("élèves", "équipes", True),
    ("crayons", "pots", False),
)


def _division(rng: random.Random, difficulte: int) -> dict[str, Any]:
    diviseurs, bas, haut = palier(_PALIERS_DIVISION, difficulte)
    demande_reste = rng.random() < 0.5

    def fabrique() -> tuple[int, int]:
        return rng.randint(bas, haut), rng.choice(diviseurs)

    def accepte(t: tuple[int, int]) -> bool:
        a, b = t
        q, r = divmod(a, b)
        reponse = r if demande_reste else q
        return q >= 2 and r != 0 and not collision(reponse, a, b)

    a, b = tirer(rng, fabrique, accepte)
    q, r = divmod(a, b)
    approx = a * 100 // b  # 15,58 -> 1558
    chiffres_apres = approx % 100
    reponse = r if demande_reste else q
    contexte = ""
    if difficulte == 3:
        objets, lots, feminin = rng.choice(_BOITES)
        completes = "complètes" if feminin else "complets"
        de = "d'" if objets[0] in "aeiouyéèœ" else "de "
        p = personnage(rng)
        question = (
            f"Combien {de}{objets} restera-t-il à la fin ?"
            if demande_reste
            else f"Combien de {lots} {completes} peut-{p.pronom} remplir ?"
        )
        enonce = f"{p.prenom} doit ranger {a} {objets} dans des {lots} de {b}. {question}"
        contexte = f" {p.prenom} remplit {q} {lots} {completes}, et il reste {r} {objets}."
    else:
        enonce = (
            f"Dans la division euclidienne de {a} par {b}, quel est le {'reste' if demande_reste else 'quotient'} ?"
        )
    pieges = [
        piege_valeur(
            str(q if demande_reste else r),
            f"C'est le {'quotient' if demande_reste else 'reste'}. "
            f"On demande le {'reste' if demande_reste else 'quotient'}.",
        ),
        piege_valeur(
            str(chiffres_apres),
            "Les chiffres après la virgule du quotient décimal ne sont pas le reste : "
            "le reste est un nombre entier plus petit que le diviseur.",
        ),
    ]
    if not demande_reste:
        pieges.append(
            piege_valeur(str(q + 1), "Vérifie : le diviseur multiplié par ta réponse dépasse-t-il le dividende ?")
        )
    else:
        pieges.append(
            piege_valeur(
                str(b - r),
                "Tu as trouvé ce qui manque pour atteindre le multiple suivant. "
                "Le reste, c'est ce qui dépasse le multiple d'avant.",
            )
        )
    pieges.append(
        piege_diagnostic("valeur_fausse", "Cherche le plus grand multiple du diviseur qui ne dépasse pas le dividende.")
    )
    return exercice_v2(
        id=f"division-{a}-{b}-{'reste' if demande_reste else 'quotient'}",
        type="nombre",
        difficulte=difficulte,
        enonce=enonce,
        reponse={"valeur": reponse, "forme": "entier"},
        indices={
            "relance": "Combien de fois le diviseur tient-il entièrement dans le dividende ?",
            "methode": "Division euclidienne : dividende = diviseur × quotient + reste, "
            "avec un reste plus petit que le "
            "diviseur.",
            "etape": f"Cherche le plus grand multiple de {b} qui ne dépasse pas {a}.",
        },
        pieges=pieges,
        solution=f"{a} = {b} × {q} + {r}, avec {r} < {b}. Le quotient est {q} et le reste est {r}." + contexte,
        lieu=f"{NOTION}/division/{a}-{b}",
    )


# --- variante 2 : critères de divisibilité ------------------------------------------------------------------

_PALIERS_CRITERES = {1: (100, 999), 2: (1000, 9999), 3: (10000, 99999)}
_DIVISEURS_CRITERES = (2, 3, 5, 9, 10)


def _criteres(rng: random.Random, difficulte: int) -> dict[str, Any]:
    bas, haut = palier(_PALIERS_CRITERES, difficulte)

    def accepte(n: int) -> bool:
        vrais = [d for d in _DIVISEURS_CRITERES if n % d == 0]
        # au moins une affirmation vraie et une fausse ; un piège « dernier chiffre » possible pour 3 ou 9
        dernier = n % 10
        piege_chiffre = (dernier in (3, 6, 9) and n % 3 != 0) or (dernier == 9 and n % 9 != 0)
        return 1 <= len(vrais) <= 4 and (piege_chiffre or n % 3 == 0 or rng.random() < 0.3)

    n = tirer(rng, lambda: rng.randint(bas, haut), accepte)
    somme = _somme_chiffres(n)
    options = [{"id": _LETTRES[i], "texte": f"divisible par {d}"} for i, d in enumerate(_DIVISEURS_CRITERES)]
    bonnes = [_LETTRES[i] for i, d in enumerate(_DIVISEURS_CRITERES) if n % d == 0]
    raisons = {
        2: "Le critère de 2 regarde le chiffre des unités : il doit être pair.",
        3: "Le critère de 3 ne regarde pas le dernier chiffre : on additionne TOUS les chiffres.",
        5: "Le critère de 5 regarde le chiffre des unités : il doit être 0 ou cinq.",
        9: "Le critère de 9 ne regarde pas le dernier chiffre : on additionne TOUS les chiffres.",
        10: "Le critère de 10 regarde le chiffre des unités : il doit être 0, pas cinq.",
    }
    pieges = [piege_contient([_LETTRES[i]], raisons[d]) for i, d in enumerate(_DIVISEURS_CRITERES) if n % d != 0]
    pieges.append(piege_diagnostic("incomplet", "Il en manque : teste chaque critère, un par un."))
    nombre = nombre_fr(n)
    return exercice_v2(
        id=f"criteres-{n}",
        type="choix",
        difficulte=difficulte,
        enonce=f"Le nombre {nombre} est-il divisible par 2, 3, 5, 9, 10 ? Choisis toutes les affirmations vraies.",
        reponse={"options": options, "bonnes": bonnes},
        indices={
            "relance": "Quels critères regardent le dernier chiffre ? Lesquels regardent la somme des chiffres ?",
            "methode": "Pour 2, 5 et 10, on regarde le chiffre des unités. Pour 3 et 9, on additionne tous les "
            "chiffres et on regarde si cette somme est dans la table de 3, ou dans celle de 9.",
            "etape": f"Le chiffre des unités de {nombre} est {n % 10}. Additionne maintenant tous ses chiffres.",
        },
        pieges=pieges,
        solution=f"Chiffre des unités : {n % 10} ; somme des chiffres : "
        f"{' + '.join(str(n))} = {somme}. "
        + (f"{nombre} est divisible par " + ", ".join(str(d) for d in _DIVISEURS_CRITERES if n % d == 0) + "."),
        lieu=f"{NOTION}/criteres/{n}",
    )


# --- variante 3 : nombre de diviseurs ------------------------------------------------------------------------

_PALIERS_NB = {1: (6, 48), 2: (24, 150), 3: (60, 200)}


def _nb_diviseurs(rng: random.Random, difficulte: int) -> dict[str, Any]:
    bas, haut = palier(_PALIERS_NB, difficulte)
    carre = difficulte == 3 and rng.random() < 0.5

    def fabrique() -> int:
        if carre:
            k = rng.randint(6, 10)
            return k * k
        return rng.randint(bas, haut)

    def accepte(n: int) -> bool:
        d = len(_diviseurs(n))
        return d >= 4 and not collision(d, n)

    n = tirer(rng, fabrique, accepte)
    liste = _diviseurs(n)
    d = len(liste)
    est_carre = int(n**0.5) ** 2 == n
    pieges = [
        piege_valeur(str(d - 2), "N'oublie pas 1 et le nombre lui-même : ce sont aussi des diviseurs."),
        piege_valeur(str(d - 1), "Vérifie les deux extrémités de ta liste : 1 et le nombre lui-même y sont-ils ?"),
    ]
    if est_carre:
        pieges.append(
            piege_valeur(str(d + 1), f"{int(n**0.5)} × {int(n**0.5)} = {n} : ce diviseur ne compte qu'une seule fois.")
        )
    pieges.append(
        piege_diagnostic(
            "valeur_fausse",
            "Cherche les diviseurs par paires, du plus petit au plus grand, jusqu'à ce que les paires se rejoignent.",
        )
    )
    paires = [(x, n // x) for x in liste if x * x <= n]
    return exercice_v2(
        id=f"nb_diviseurs-{n}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Combien le nombre {n} a-t-il de diviseurs ?",
        reponse={"valeur": d, "forme": "entier"},
        indices={
            "relance": "Deux diviseurs vont souvent par paire : lesquels ?",
            "methode": "Cherche les diviseurs par paires dont le produit vaut le nombre, en partant du plus petit, "
            "et arrête-toi quand les paires se croisent.",
            "etape": f"Commence par la paire évidente : le nombre lui-même et un. Teste ensuite les entiers "
            f"suivants, un par un : divisent-ils {n} ?",
        },
        pieges=pieges,
        solution="Les paires : " + " ; ".join(f"{x} × {y}" for x, y in paires) + ". Les diviseurs de "
        f"{n} sont {', '.join(map(str, liste))} : il y en a {d}.",
        lieu=f"{NOTION}/nb_diviseurs/{n}",
    )


# --- variante 4 : compléter pour obtenir un multiple -----------------------------------------------------------

_PALIERS_COMPLETER = {1: ((5, 10, 2), 20, 200), 2: ((3, 9), 100, 999), 3: ((3, 9), 1000, 9999)}


def _completer(rng: random.Random, difficulte: int) -> dict[str, Any]:
    diviseurs, bas, haut = palier(_PALIERS_COMPLETER, difficulte)
    b = rng.choice(diviseurs)

    def accepte(n: int) -> bool:
        r = n % b
        manque = (b - r) % b
        return r != 0 and not collision(manque, n, b, _somme_chiffres(n), n % 10)

    n = tirer(rng, lambda: rng.randint(bas, haut), accepte)
    r = n % b
    manque = b - r
    somme_critere = b in (3, 9)
    pieges = [
        piege_valeur(
            str(r),
            f"{r}, c'est ce qui dépasse le multiple d'avant. On cherche ce qui MANQUE pour atteindre "
            "le multiple suivant.",
        ),
        piege_valeur(str(b), f"Ajouter {b} ne change pas le reste de la division par {b}."),
        piege_diagnostic(
            "valeur_fausse",
            "Ajoute un petit nombre à la fois, en commençant par le plus petit, et teste le critère à chaque fois.",
        ),
    ]
    critere = (
        "la somme des chiffres doit devenir un multiple de " + str(b)
        if somme_critere
        else f"le chiffre des unités doit devenir {'0' if b == 10 else '0 ou 5' if b == 5 else 'pair'}"
    )
    return exercice_v2(
        id=f"completer-{n}-{b}",
        type="nombre",
        difficulte=difficulte,
        enonce=f"Quel est le plus petit entier (non nul) qu'il faut ajouter à {nombre_fr(n)} pour obtenir un multiple "
        f"de {b} ?",
        reponse={"valeur": manque, "forme": "entier"},
        indices={
            "relance": f"Quel est le critère de divisibilité par {b} ?",
            "methode": f"Pour être un multiple de {b}, {critere}. Ajoute le plus petit nombre qui le permet.",
            "etape": f"La somme des chiffres de {nombre_fr(n)} vaut {_somme_chiffres(n)}. Quel est le multiple de {b} "
            "suivant ?"
            if somme_critere
            else f"Le chiffre des unités de {nombre_fr(n)} est {n % 10}. Que faut-il ajouter pour obtenir le bon ?",
        },
        pieges=pieges,
        solution=f"{nombre_fr(n)} = {b} × {n // b} + {r}. En ajoutant {manque}, on obtient {nombre_fr(n + manque)} "
        f"= {b} × {(n + manque) // b}, un multiple de {b}. Il faut ajouter {manque}.",
        lieu=f"{NOTION}/completer/{n}-{b}",
    )


# --- variante 5 : multiple ou diviseur ? ----------------------------------------------------------------------------


def _multiple_ou_diviseur(rng: random.Random, difficulte: int) -> dict[str, Any]:
    haut = {1: 9, 2: 15, 3: 25}[difficulte]
    affirmations: list[tuple[str, bool, str]] = []
    vus: set[str] = set()
    while len(affirmations) < 4:
        p = rng.randint(3, haut)
        k = rng.randint(3, 12)
        m = p * k
        vraie = rng.random() < 0.5
        forme = rng.choice(("diviseur", "multiple", "inverse", "faux"))
        if forme == "diviseur":
            texte, juste, raison = f"{p} est un diviseur de {m}", True, ""
        elif forme == "multiple":
            texte, juste, raison = f"{m} est un multiple de {p}", True, ""
        elif forme == "inverse":  # multiple et diviseur inversés
            texte, juste = (f"{m} est un diviseur de {p}", False) if vraie else (f"{p} est un multiple de {m}", False)
            raison = f"C'est l'inverse : {p} est un diviseur de {m}, et {m} est un multiple de {p}."
        else:  # nombre qui ne divise pas
            m2 = m + rng.choice((1, 2))
            texte, juste = f"{p} est un diviseur de {m2}", False
            raison = f"{m2} ÷ {p} ne tombe pas juste : il reste {m2 % p}."
        if texte not in vus:
            vus.add(texte)
            affirmations.append((texte, juste, raison))
    if all(j for _, j, _ in affirmations):  # il faut au moins une affirmation fausse
        p, k = rng.randint(3, haut), rng.randint(3, 12)
        affirmations[-1] = (
            f"{p * k} est un diviseur de {p}",
            False,
            f"C'est l'inverse : {p} est un diviseur de {p * k}, et {p * k} est un multiple de {p}.",
        )
    if not any(j for _, j, _ in affirmations):
        texte = f"{affirmations[0][0].split()[0]} est un diviseur de {int(affirmations[0][0].split()[0]) * 4}"
        affirmations[0] = (texte, True, "")
    options = [{"id": _LETTRES[i], "texte": t} for i, (t, _, _) in enumerate(affirmations)]
    bonnes = [_LETTRES[i] for i, (_, j, _) in enumerate(affirmations) if j]
    pieges = [piege_contient([_LETTRES[i]], r) for i, (_, j, r) in enumerate(affirmations) if not j]
    pieges.append(piege_diagnostic("incomplet", "Il en manque : vérifie chaque affirmation par une division."))
    return exercice_v2(
        id=f"multiple_ou_diviseur-{'-'.join(t.split()[0] + t.split()[-1] for t, _, _ in affirmations)}",
        type="choix",
        difficulte=difficulte,
        enonce="Quelles affirmations sont vraies ? (Il peut y en avoir plusieurs.)",
        reponse={"options": options, "bonnes": bonnes},
        indices={
            "relance": "« a est un diviseur de b » : lequel des deux nombres est le plus petit, en général ?",
            "methode": "a est un diviseur de b, et b est un multiple de a, quand la division de b par a tombe juste "
            "(reste nul).",
            "etape": "Pour chaque affirmation, fais la division du plus grand nombre par le plus petit et regarde le "
            "reste.",
        },
        pieges=pieges,
        solution="Vraies : "
        + " ; ".join(t for t, j, _ in affirmations if j)
        + ". "
        + " ".join(r for _, j, r in affirmations if not j and r),
        lieu=f"{NOTION}/multiple_ou_diviseur/{difficulte}",
    )


_VARIANTES = {
    "division": _division,
    "criteres": _criteres,
    "nb_diviseurs": _nb_diviseurs,
    "completer": _completer,
    "multiple_ou_diviseur": _multiple_ou_diviseur,
}


def generer(graine: int, difficulte: int = 1, variante: str | None = None) -> dict[str, Any]:
    """Un exercice v2 sur la notion : même graine et mêmes paramètres, même exercice."""
    return generer_notion(NOTION, _VARIANTES, graine, difficulte, variante)
