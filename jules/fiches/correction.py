"""Correction sans IA d'une reponse d'eleve, selon le type d'exercice d'une fiche v2.

Chaque type a un correcteur pur : (reponse attendue, reponse de l'eleve) -> Verdict. Aucun appel au
modele et aucune evaluation de code : les expressions sont lues par un petit analyseur qui n'accepte
que les nombres, les lettres declarees, + - * / ^ et les parentheses.

Le verdict porte un `diagnostic` court (« facteur_non_premier », « inversion_voisine »...) : c'est lui
que les pieges d'une fiche reprennent pour choisir la relance adaptee a l'erreur.
"""

from __future__ import annotations

import ast
import math
import random
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from jules.bibliotheques import normaliser

TYPES_AUTO = ("nombre", "expression", "choix", "texte_court", "ordre", "association")
TYPES = (*TYPES_AUTO, "ouverte")
FORMES_NOMBRE = ("libre", "entier", "fraction_irreductible", "produit_premiers", "scientifique")
FORMES_EXPRESSION = ("libre", "developpee", "factorisee")

# Diagnostics que chaque correcteur peut rendre sur une reponse fausse ou partielle.
DIAGNOSTICS = {
    "nombre": (
        "valeur_fausse",
        "produit_faux",
        "facteur_non_premier",
        "non_irreductible",
        "pas_une_fraction",
        "pas_scientifique",
    ),
    "expression": ("non_equivalente", "pas_developpee", "pas_factorisee", "factorisation_incomplete"),
    "choix": ("incomplet", "mauvais_choix"),
    "texte_court": ("mauvaise_reponse",),
    "ordre": ("inversion_voisine", "ordre_faux"),
    "association": ("une_erreur", "associations_fausses"),
    "ouverte": (),
}

# Ce que Jules dit quand il ne sait pas lire la reponse : la forme attendue, jamais la reponse.
AIDE_FORMAT = {
    "nombre": "Écris un nombre, par exemple 12, 3,5 ou 7/4.",
    "produit_premiers": "Écris un produit, par exemple 2^2 × 3 × 5 (ou 2² × 3 × 5).",
    "scientifique": "Écris le nombre en notation scientifique, par exemple 7,2 × 10^-4 (ou 7,2 × 10⁻⁴).",
    "expression": "Écris une expression, par exemple 3x^2 - 2x + 1 (× ou * pour multiplier).",
    "choix": "Donne la ou les lettres choisies, par exemple « b » ou « a, c ».",
    "texte_court": "Réponds en un mot ou une courte expression.",
    "ordre": "Donne les lettres dans l'ordre, par exemple « c, a, d, b ».",
    "association": "Donne les paires, par exemple « a-x, b-y, c-x ».",
}

EXPOSANT_MAX = 64
BASE_MAX = 10**12
TAILLE_REPONSE_MAX = 300
BITS_MAX = 4096  # taille maximale d'un resultat intermediaire (un collegien n'en a jamais besoin)


class ReponseIllisible(ValueError):
    pass


@dataclass
class Verdict:
    juste: bool
    partiel: bool = False
    auto: bool = True  # False : la correction demande un humain (ou un modele)
    diagnostic: str = ""  # vide si juste ; « illisible » si la reponse ne se lit pas
    lu: str = ""  # ce que Jules a compris de la reponse, ou la bonne ecriture (orthographe)


ILLISIBLE = "illisible"


# --- nombres -------------------------------------------------------------------------

_EXPOSANTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_NOMBRE = re.compile(r"[+-]?\d+(?:\.\d+)?")
_FRACTION = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*/\s*([+-]?\d+(?:\.\d+)?)")
# Notation scientifique ou puissance de 10 : « 7,2 × 10^-4 », « 7.2*10^(-4) », « 7,2 × 10⁻⁴ », « 10⁻³ ».
_PUISSANCE_DIX = r"10\s*(?:\^\s*\(?\s*([+-]?\d+)\s*\)?|([⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+))"
_SCIENTIFIQUE = re.compile(rf"(?:([+-]?\d+(?:\.\d+)?)\s*[×x*·]\s*)?{_PUISSANCE_DIX}", re.IGNORECASE)
# Unite recopiee apres le nombre (« 42 € », « 27,5 % », « 12 cm² », « 20 m/s ») : elle ne change pas la valeur.
# Le pourcentage est traite comme une unite : « 27,5 % » vaut 27,5, comme le demandent les enonces.
_UNITE = re.compile(
    r"(?<=[\d)⁰¹²³⁴⁵⁶⁷⁸⁹])\s*(?:€|euros?|%|°\s*[cf]?|degrés?|km/h|m/s|k?wh|k?w|[kcdm]?m[²³23]?|m?m[²³23]|"
    r"[kcdm]?l|[km]?g|t|min|h|s)$",
    re.IGNORECASE,
)


def _nettoyer_nombre(texte: str) -> str:
    t = str(texte).strip().replace("\u202f", " ").replace("\xa0", " ").replace("−", "-")
    t = re.sub(r"(?<=\d) (?=\d{3}(?:\D|$))", "", t)  # espaces de milliers : 1 848 -> 1848
    t = t.replace(",", ".")
    if "=" in t:  # « 252/360 = 7/10 » : on garde le dernier membre
        t = t.rsplit("=", 1)[1].strip()
    t = t.rstrip(".!? ").strip()
    return _UNITE.sub("", t).strip()


def _exposant(m: re.Match[str]) -> int:
    exposant = int(m.group(2) if m.group(2) is not None else m.group(3).translate(_EXPOSANTS))
    if abs(exposant) > EXPOSANT_MAX:
        raise ReponseIllisible("exposant")
    return exposant


def lire_nombre(texte: str) -> Fraction:
    t = _nettoyer_nombre(texte)
    scientifique = _SCIENTIFIQUE.fullmatch(t)
    if scientifique:
        mantisse = Fraction(scientifique.group(1)) if scientifique.group(1) else Fraction(1)
        return mantisse * Fraction(10) ** _exposant(scientifique)
    fraction = _FRACTION.fullmatch(t)
    if fraction:
        denominateur = Fraction(fraction.group(2))
        if denominateur == 0:
            raise ReponseIllisible("division par zéro")
        return Fraction(fraction.group(1)) / denominateur
    if _NOMBRE.fullmatch(t):
        return Fraction(t)
    # « en 1914 », « c'est 7/10 » : un seul nombre au milieu de mots, sans autre chiffre ni calcul
    jetons = _FRACTION.findall(t) or _NOMBRE.findall(t)
    reste = _FRACTION.sub(" ", t) if _FRACTION.search(t) else _NOMBRE.sub(" ", t)
    if len(jetons) == 1 and re.fullmatch(r"[^\W\d_]*(?:[\s'’][^\W\d_]*)*", reste.strip()):
        return lire_nombre(jetons[0] if isinstance(jetons[0], str) else "/".join(jetons[0]))
    raise ReponseIllisible(t)


_FACTEUR = re.compile(r"(\d+)\s*(?:\^\s*(\d+)|([⁰¹²³⁴⁵⁶⁷⁸⁹]+))?")


def lire_produit(texte: str) -> list[tuple[int, int]]:
    """« 2^3 × 3² × 5 » -> [(2, 3), (3, 2), (5, 1)]."""
    t = str(texte).strip().replace("\xa0", " ").replace("\u202f", " ")
    if "=" in t:
        t = t.rsplit("=", 1)[1]
    facteurs = []
    for morceau in re.split(r"[×x*·]", t.lower()):
        m = _FACTEUR.fullmatch(morceau.strip())
        if not m:
            raise ReponseIllisible(morceau)
        base = int(m.group(1))
        exposant = int(m.group(2) or (m.group(3) or "1").translate(_EXPOSANTS))
        if base > BASE_MAX or exposant > EXPOSANT_MAX or exposant < 1:
            raise ReponseIllisible(morceau)
        facteurs.append((base, exposant))
    return facteurs


def est_premier(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def decomposer(n: int) -> list[tuple[int, int]]:
    facteurs: list[tuple[int, int]] = []
    d = 2
    while d * d <= n:
        k = 0
        while n % d == 0:
            n //= d
            k += 1
        if k:
            facteurs.append((d, k))
        d += 1
    if n > 1:
        facteurs.append((n, 1))
    return facteurs


def ecrire_produit(facteurs: list[tuple[int, int]]) -> str:
    return " × ".join(f"{b}^{e}" if e > 1 else str(b) for b, e in facteurs)


def ecrire_scientifique(x: Fraction) -> str:
    """0,00072 -> « 7,2 × 10^-4 » (mantisse entre 1 et 10, ecriture decimale)."""
    if x == 0:
        return "0"
    n = 0
    a = abs(x)
    while a >= 10:
        a /= 10
        n += 1
    while a < 1:
        a *= 10
        n -= 1
    decimal = _ecrire_decimal(a)
    signe = "-" if x < 0 else ""
    return f"{signe}{decimal} × 10^{n}"


def _ecrire_decimal(x: Fraction) -> str:
    entier, reste = divmod(x.numerator, x.denominator)
    chiffres = ""
    while reste and len(chiffres) < 12:
        reste *= 10
        chiffre, reste = divmod(reste, x.denominator)
        chiffres += str(chiffre)
    return f"{entier},{chiffres}" if chiffres else str(entier)


def est_scientifique(texte: str) -> bool:
    """« 7,2 × 10^-4 » et « 10^-3 » oui ; « 72 × 10^-5 » et « 0,00072 » non."""
    m = _SCIENTIFIQUE.fullmatch(_nettoyer_nombre(texte))
    if m is None:
        return False
    return not m.group(1) or 1 <= abs(Fraction(m.group(1))) < 10


def _ecrire_nombre(x: Fraction) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def corriger_nombre(attendu: dict[str, Any], reponse: str) -> Verdict:
    forme = attendu.get("forme", "libre")
    valeur = lire_nombre(str(attendu["valeur"]))
    if forme == "produit_premiers":
        try:
            facteurs = lire_produit(reponse)
        except ReponseIllisible:
            return Verdict(False, diagnostic=ILLISIBLE)
        lu = ecrire_produit(facteurs)
        if math.prod(b**e for b, e in facteurs) != valeur:
            return Verdict(False, diagnostic="produit_faux", lu=lu)
        if not all(est_premier(b) for b, _ in facteurs):
            return Verdict(False, partiel=True, diagnostic="facteur_non_premier", lu=lu)
        return Verdict(True, lu=lu)
    try:
        nombre = lire_nombre(reponse)
    except ReponseIllisible:
        return Verdict(False, diagnostic=ILLISIBLE)
    tolerance = Fraction(str(attendu.get("tolerance", 0)))
    if abs(nombre - valeur) > tolerance:
        return Verdict(False, diagnostic="valeur_fausse", lu=_ecrire_nombre(nombre))
    if forme == "scientifique" and not est_scientifique(reponse):
        return Verdict(False, partiel=True, diagnostic="pas_scientifique", lu=_ecrire_nombre(nombre))
    if forme == "fraction_irreductible" and valeur.denominator != 1:
        fractions = list(_FRACTION.finditer(_nettoyer_nombre(reponse)))
        m = fractions[0] if len(fractions) == 1 else None
        if not m or "." in m.group(0):
            return Verdict(False, partiel=True, diagnostic="pas_une_fraction", lu=_ecrire_nombre(nombre))
        if math.gcd(int(m.group(1)), int(m.group(2))) != 1:
            return Verdict(False, partiel=True, diagnostic="non_irreductible", lu=m.group(0))
    return Verdict(True, lu=_ecrire_nombre(nombre))


# --- expressions -------------------------------------------------------------------

_NOEUDS_PERMIS = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.USub,
    ast.UAdd,
)


def preparer_expression(texte: str) -> str:
    """Ecriture d'eleve -> syntaxe Python : 3x² - 2(x+1) -> 3*x**2 - 2*(x+1)."""
    t = str(texte).strip().lower()
    if len(t) > TAILLE_REPONSE_MAX:
        raise ReponseIllisible("trop long")
    if "=" in t:  # « Ec = 1/2 m v² » : on garde le dernier membre, sans l'espace qui le precede
        t = t.rsplit("=", 1)[1].strip()
    for avant, apres in (("×", "*"), ("·", "*"), ("÷", "/"), ("−", "-"), (",", "."), ("^", "**")):
        t = t.replace(avant, apres)
    t = re.sub(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: "**" + m.group(1).translate(_EXPOSANTS), t)
    t = re.sub(r"(?<=\d)\s*(?=[a-z(])", "*", t)  # 2x, 2(
    t = re.sub(r"(?<=\))\s*(?=[a-z0-9(])", "*", t)  # )(, )x
    for _ in range(2):  # xy, x(  (deux passes pour xyz)
        t = re.sub(r"(?<=[a-z])\s*(?=[a-z(])", "*", t)
    return t


def lire_expression(texte: str, variables: list[str]) -> ast.Expression:
    try:
        arbre = ast.parse(preparer_expression(texte), mode="eval")
    except SyntaxError as err:
        raise ReponseIllisible(str(texte)) from err
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, _NOEUDS_PERMIS):
            raise ReponseIllisible(type(noeud).__name__)
        if isinstance(noeud, ast.Name) and noeud.id not in variables:
            raise ReponseIllisible(noeud.id)
        if isinstance(noeud, ast.Constant) and (
            isinstance(noeud.value, bool) or not isinstance(noeud.value, int | float)
        ):
            raise ReponseIllisible(repr(noeud.value))
    return arbre


def _evaluer(noeud: ast.AST, valeurs: dict[str, Fraction]) -> Fraction:
    if isinstance(noeud, ast.Expression):
        return _evaluer(noeud.body, valeurs)
    if isinstance(noeud, ast.Constant):
        return Fraction(str(noeud.value))
    if isinstance(noeud, ast.Name):
        return valeurs[noeud.id]
    if isinstance(noeud, ast.UnaryOp):
        v = _evaluer(noeud.operand, valeurs)
        return -v if isinstance(noeud.op, ast.USub) else v
    if isinstance(noeud, ast.BinOp):
        a = _evaluer(noeud.left, valeurs)
        b = _evaluer(noeud.right, valeurs)
        if isinstance(noeud.op, ast.Add):
            return a + b
        if isinstance(noeud.op, ast.Sub):
            return a - b
        if isinstance(noeud.op, ast.Mult):
            return a * b
        if isinstance(noeud.op, ast.Div):
            return a / b  # ZeroDivisionError geree par l'appelant
        if b.denominator != 1 or abs(b) > EXPOSANT_MAX:
            raise ReponseIllisible("exposant")
        taille = max(a.numerator.bit_length(), a.denominator.bit_length()) * abs(int(b))
        if taille > BITS_MAX:  # (10^64)^64^64... : refuse avant de calculer un nombre geant
            raise ReponseIllisible("nombre trop grand")
        return Fraction(a) ** int(b)
    raise ReponseIllisible(type(noeud).__name__)


def equivalentes(a: ast.Expression, b: ast.Expression, variables: list[str], essais: int = 8) -> bool:
    """Egalite sur des points tires au hasard (graine fixe : le resultat est toujours le meme)."""
    tirage = random.Random(1905)  # noqa: S311 - pas de cryptographie ici, juste des points de test
    compares = 0
    for _ in range(essais * 4):
        valeurs = {v: Fraction(tirage.randint(-9, 9), tirage.choice((1, 1, 2, 3))) for v in variables}
        try:
            if _evaluer(a, valeurs) != _evaluer(b, valeurs):
                return False
        except ZeroDivisionError:
            continue
        compares += 1
        if compares >= essais:
            return True
    return compares > 0


def corriger_expression(attendu: dict[str, Any], reponse: str) -> Verdict:
    variables = [str(v) for v in attendu.get("variables") or ["x"]]
    reference = lire_expression(str(attendu["valeur"]), variables)
    try:
        eleve = lire_expression(reponse, variables)
    except ReponseIllisible:
        return Verdict(False, diagnostic=ILLISIBLE)
    lu = ast.unparse(eleve)
    try:
        egales = equivalentes(reference, eleve, variables)
    except ReponseIllisible:
        return Verdict(False, diagnostic=ILLISIBLE)
    if not egales:
        return Verdict(False, diagnostic="non_equivalente", lu=lu)
    forme = attendu.get("forme", "libre")
    if forme == "developpee" and "(" in preparer_expression(reponse):
        return Verdict(False, partiel=True, diagnostic="pas_developpee", lu=lu)
    if forme == "factorisee" and not est_produit(eleve):
        return Verdict(False, partiel=True, diagnostic="pas_factorisee", lu=lu)
    if forme == "factorisee" and facteurs_variables(eleve.body) < facteurs_variables(reference.body):
        # x(x² − 4) au lieu de x(x − 2)(x + 2) : un produit, mais un facteur se factorise encore
        return Verdict(False, partiel=True, diagnostic="factorisation_incomplete", lu=lu)
    return Verdict(True, lu=lu)


def facteurs_variables(noeud: ast.AST) -> int:
    """Nombre de facteurs qui contiennent une variable (une puissance entiere compte autant de fois)."""
    if isinstance(noeud, ast.UnaryOp):
        return facteurs_variables(noeud.operand)
    if isinstance(noeud, ast.BinOp) and isinstance(noeud.op, ast.Mult):
        return facteurs_variables(noeud.left) + facteurs_variables(noeud.right)
    if isinstance(noeud, ast.BinOp) and isinstance(noeud.op, ast.Div):
        return facteurs_variables(noeud.left)
    if (
        isinstance(noeud, ast.BinOp)
        and isinstance(noeud.op, ast.Pow)
        and isinstance(noeud.right, ast.Constant)
        and isinstance(noeud.right.value, int)
        and 0 < noeud.right.value <= EXPOSANT_MAX
    ):
        return facteurs_variables(noeud.left) * noeud.right.value
    return 1 if any(isinstance(n, ast.Name) for n in ast.walk(noeud)) else 0


def est_produit(arbre: ast.Expression) -> bool:
    corps = arbre.body
    if isinstance(corps, ast.UnaryOp):
        corps = corps.operand
    return isinstance(corps, ast.BinOp) and isinstance(corps.op, ast.Mult | ast.Pow)


# --- choix, texte court, ordre, association -------------------------------------------


def _cle(texte: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", normaliser(str(texte))))


def _options(attendu: dict[str, Any], champ: str = "options") -> dict[str, str]:
    return {str(o["id"]): str(o["texte"]) for o in attendu.get(champ) or []}


def _reconnaitre(morceau: str, options: dict[str, str]) -> str:
    cle = _cle(morceau)
    for identifiant, texte in options.items():
        if cle in (_cle(identifiant), _cle(texte)):
            return identifiant
    raise ReponseIllisible(morceau)


def _morceaux(reponse: Any) -> list[str]:
    if isinstance(reponse, list | tuple):
        return [str(r) for r in reponse]
    texte = str(reponse)
    if len(texte) > TAILLE_REPONSE_MAX:
        raise ReponseIllisible("trop long")
    return [m for m in re.split(r"\s*(?:[,;/]|\bet\b|\s-\s|\s>\s|\s)\s*", texte.strip()) if m.strip()]


def lire_choix(attendu: dict[str, Any], reponse: Any) -> set[str]:
    options = _options(attendu)
    if not isinstance(reponse, list | tuple):
        try:  # une option entiere (« Le gouvernement ottoman »), avant de decouper
            return {_reconnaitre(str(reponse), options)}
        except ReponseIllisible:
            pass
    return {_reconnaitre(m, options) for m in _morceaux(reponse)}


def corriger_choix(attendu: dict[str, Any], reponse: Any) -> Verdict:
    try:
        choisis = lire_choix(attendu, reponse)
    except ReponseIllisible:
        return Verdict(False, diagnostic=ILLISIBLE)
    bonnes = {str(b) for b in attendu["bonnes"]}
    lu = ", ".join(sorted(choisis))
    if choisis == bonnes:
        return Verdict(True, lu=lu)
    if choisis < bonnes:
        return Verdict(False, partiel=True, diagnostic="incomplet", lu=lu)
    return Verdict(False, diagnostic="mauvais_choix", lu=lu)


_ARTICLES = frozenset(["le", "la", "les", "l", "un", "une", "des", "du", "de", "d"])


def _cle_texte(texte: Any) -> str:
    mots = _cle(texte).split()
    while mots and mots[0] in _ARTICLES:
        mots = mots[1:]
    return " ".join(mots)


def distance(a: str, b: str) -> int:
    """Distance d'edition (Levenshtein)."""
    precedente = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        courante = [i]
        for j, cb in enumerate(b, 1):
            courante.append(min(precedente[j] + 1, courante[j - 1] + 1, precedente[j - 1] + (ca != cb)))
        precedente = courante
    return precedente[-1]


def corriger_texte_court(attendu: dict[str, Any], reponse: Any) -> Verdict:
    texte = str(reponse)
    if len(texte) > TAILLE_REPONSE_MAX:
        return Verdict(False, diagnostic=ILLISIBLE)
    cle = _cle_texte(texte)
    if not cle:
        return Verdict(False, diagnostic=ILLISIBLE)
    acceptees = [str(a) for a in attendu["acceptees"]]
    for a in acceptees:
        if cle == _cle_texte(a):
            return Verdict(True, lu=a)
    tolerees = int(attendu.get("fautes_tolerees", 0))
    for a in acceptees:
        # Au plus une faute par tranche de 4 lettres : sur « UV » ou « oui », une faute tolérée accepterait
        # presque n'importe quoi (« u », « ux », « non »).
        permises = min(tolerees, len(_cle_texte(a)) // 4)
        if permises and distance(cle, _cle_texte(a)) <= permises:
            return Verdict(True, diagnostic="orthographe", lu=a)
    return Verdict(False, diagnostic="mauvaise_reponse", lu=texte.strip())


def lire_ordre(attendu: dict[str, Any], reponse: Any) -> list[str]:
    options = _options(attendu, "elements")
    lu = [_reconnaitre(m, options) for m in _morceaux(reponse)]
    if sorted(lu) != sorted(options):
        raise ReponseIllisible("il faut chaque élément une fois")
    return lu


def corriger_ordre(attendu: dict[str, Any], reponse: Any) -> Verdict:
    try:
        lu = lire_ordre(attendu, reponse)
    except ReponseIllisible:
        return Verdict(False, diagnostic=ILLISIBLE)
    juste = [str(e["id"]) for e in attendu["elements"]]
    texte = ", ".join(lu)
    if lu == juste:
        return Verdict(True, lu=texte)
    differences = [i for i, (a, b) in enumerate(zip(lu, juste, strict=True)) if a != b]
    if len(differences) == 2 and differences[1] == differences[0] + 1:
        return Verdict(False, partiel=True, diagnostic="inversion_voisine", lu=texte)
    return Verdict(False, diagnostic="ordre_faux", lu=texte)


def lire_association(attendu: dict[str, Any], reponse: Any) -> dict[str, str]:
    gauche = _options(attendu, "gauche")
    droite = _options(attendu, "droite")
    if isinstance(reponse, dict):
        paires = {str(k): str(v) for k, v in reponse.items()}
    else:
        paires = {}
        for morceau in re.split(r"\s*[,;]\s*", str(reponse).strip()):
            if not morceau:
                continue
            m = re.fullmatch(r"(.+?)\s*(?:-|:|→|->|=)\s*(.+)", morceau)
            if not m:
                raise ReponseIllisible(morceau)
            paires[_reconnaitre(m.group(1), gauche)] = _reconnaitre(m.group(2), droite)
    if set(paires) != set(gauche) or not set(paires.values()) <= set(droite):
        raise ReponseIllisible("il faut une paire pour chaque élément de gauche")
    return paires


def corriger_association(attendu: dict[str, Any], reponse: Any) -> Verdict:
    try:
        paires = lire_association(attendu, reponse)
    except ReponseIllisible:
        return Verdict(False, diagnostic=ILLISIBLE)
    justes = {str(k): str(v) for k, v in attendu["paires"].items()}
    erreurs = sum(paires[k] != v for k, v in justes.items())
    lu = ", ".join(f"{k}-{v}" for k, v in sorted(paires.items()))
    if not erreurs:
        return Verdict(True, lu=lu)
    if erreurs == 1:
        return Verdict(False, partiel=True, diagnostic="une_erreur", lu=lu)
    return Verdict(False, diagnostic="associations_fausses", lu=lu)


# --- aiguillage ------------------------------------------------------------------------

_CORRECTEURS = {
    "nombre": corriger_nombre,
    "expression": corriger_expression,
    "choix": corriger_choix,
    "texte_court": corriger_texte_court,
    "ordre": corriger_ordre,
    "association": corriger_association,
}


def corriger(exercice: dict[str, Any], reponse: Any) -> Verdict:
    type_ = exercice["type"]
    if type_ == "ouverte":
        return Verdict(False, auto=False, diagnostic="correction_humaine")
    return _CORRECTEURS[type_](exercice["reponse"], reponse)


def meme_reponse(exercice: dict[str, Any], a: Any, b: Any) -> bool:
    """Deux reponses disent-elles la meme chose ? (sert a reconnaitre la valeur d'un piege)"""
    attendu = exercice["reponse"]
    type_ = exercice["type"]
    try:
        if type_ == "nombre":
            if attendu.get("forme") == "produit_premiers":
                return sorted(lire_produit(str(a))) == sorted(lire_produit(str(b)))
            return lire_nombre(str(a)) == lire_nombre(str(b))
        if type_ == "expression":
            variables = [str(v) for v in attendu.get("variables") or ["x"]]
            return equivalentes(lire_expression(str(a), variables), lire_expression(str(b), variables), variables)
        if type_ == "texte_court":
            return _cle_texte(a) == _cle_texte(b)
        if type_ == "choix":
            return lire_choix(attendu, a) == lire_choix(attendu, b)
        if type_ == "ordre":
            return lire_ordre(attendu, a) == lire_ordre(attendu, b)
        if type_ == "association":
            return lire_association(attendu, a) == lire_association(attendu, b)
    except (ReponseIllisible, ZeroDivisionError):
        return False
    return False


def piege_declenche(exercice: dict[str, Any], reponse: Any, verdict: Verdict) -> dict[str, Any] | None:
    """Premier piege de la fiche qui correspond a cette reponse fausse (valeur, choix ou diagnostic)."""
    if verdict.juste or verdict.diagnostic == ILLISIBLE:
        return None
    for piege in exercice.get("pieges") or []:
        condition = piege.get("si") or {}
        if "valeur" in condition and meme_reponse(exercice, condition["valeur"], reponse):
            return dict(piege)
        if "contient" in condition:
            try:
                choisis = lire_choix(exercice["reponse"], reponse)
            except ReponseIllisible:
                continue
            if choisis & {str(c) for c in condition["contient"]}:
                return dict(piege)
        if "diagnostic" in condition and condition["diagnostic"] == verdict.diagnostic:
            return dict(piege)
    return None


def reponse_de_reference(exercice: dict[str, Any]) -> Any:
    """La bonne reponse ecrite comme un eleve l'ecrirait : sert a verifier que la fiche se corrige elle-meme."""
    attendu = exercice["reponse"]
    type_ = exercice["type"]
    if type_ == "nombre":
        if attendu.get("forme") == "produit_premiers":
            return ecrire_produit(decomposer(int(lire_nombre(str(attendu["valeur"])))))
        if attendu.get("forme") == "scientifique":
            return ecrire_scientifique(lire_nombre(str(attendu["valeur"])))
        return str(attendu["valeur"])
    if type_ == "expression":
        return str(attendu["valeur"])
    if type_ == "choix":
        return [str(b) for b in attendu["bonnes"]]
    if type_ == "texte_court":
        return str(attendu["acceptees"][0])
    if type_ == "ordre":
        return [str(e["id"]) for e in attendu["elements"]]
    if type_ == "association":
        return {str(k): str(v) for k, v in attendu["paires"].items()}
    return None
