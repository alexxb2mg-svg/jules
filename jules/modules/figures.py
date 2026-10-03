"""Module 'figures' : Jules peut montrer une figure dans la discussion, jamais la dessiner lui-meme.

Le modele n'ecrit qu'un bloc de code markdown de langage `figure` contenant du JSON :
    ```figure
    {"gabarit": "droite-affine", "valeurs": {"a": 2, "b": 1}}
    ```
Le dessin est fait par le gabarit de l'extension (gabarit.js, dans la page de l'eleve). Ce module :
  - dit au modele quelles figures existent (contribution), seulement dans les modes autorises ;
  - relit la reponse (filtrer_reponse) : un bloc valide est recrit sous forme normalisee (JSON compact,
    cles triees, valeurs absentes = defaut) ; un bloc invalide, en trop ou hors mode est retire sans bruit
    et l'evenement `figure_ecartee` est journalise. Il n'appelle jamais `relancer()`.
Liste blanche et bornes : cle `discussion` des extension.yaml (jules/extensions.py, docs/EXTENSIONS.md).

Doit etre place APRES 'notions' et 'cours' dans config.yaml : leurs filtres peuvent remplacer la reponse
par une relance (texte brut du modele), qui doit encore passer ici.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from typing import Any

from jules.extensions import figures_pour_discussion
from jules.modules.base import Module
from jules.stockage import Conversation

MODES_PAR_DEFAUT = ("aide-devoirs", "reexplique")
# Gabarits `revele: true` (la figure montre la reponse : solutions placees, longueur ecrite) : proposes et
# acceptes seulement dans ces modes. Jamais 'aide-devoirs' : la figure ferait l'exercice a la place de l'eleve.
MODES_REVELE_PAR_DEFAUT = ("reexplique",)

# Bloc de code cloture (``` ou ~~~, 3 espaces d'indentation au plus) de langage `figure`. Sans cloture,
# le bloc va jusqu'a la fin du message, comme le fait le rendu markdown.
_BLOC = re.compile(
    r"^ {0,3}(?P<cloture>(?P<c>[`~])(?P=c){2,})[ \t]*figure(?:[ \t][^\n]*)?\n"
    r"(?P<json>.*?)(?:\n {0,3}(?P=cloture)(?P=c)*[ \t]*(?=\n|\Z)|\Z)",
    re.MULTILINE | re.DOTALL,
)
# Ouverture `figure` qui n'est pas en debut de ligne (citation « > », liste...) : le rendu markdown en ferait
# quand meme une figure. ponytail: on la neutralise en bloc de code ordinaire (JSON visible) plutot que de
# la valider ; a traiter comme _BLOC si le modele en ecrit vraiment (evenement figure_ecartee, raison "imbrique").
_IMBRIQUE = re.compile(
    r"^(?P<avant>[ \t]*[^ \t\n`~][^\n]*?)(?P<cloture>`{3,}|~{3,})(?P<espace>[ \t]*)figure\b", re.MULTILINE
)


def _valeur(nombre: float) -> int | float:
    arrondi = round(nombre, 9)
    return int(arrondi) if arrondi == int(arrondi) else arrondi


def normaliser(source: str, autorises: dict[str, dict[str, Any]]) -> tuple[str | None, str, str]:
    """(JSON normalise ou None, id du gabarit lu, raison du rejet). Toute erreur rejette le bloc entier."""
    try:
        objet = json.loads(source)
    except (json.JSONDecodeError, RecursionError):
        return None, "", "json illisible"
    if not isinstance(objet, dict) or set(objet) != {"gabarit", "valeurs"}:
        return None, "", "attendu {gabarit, valeurs}"
    gabarit = objet["gabarit"] if isinstance(objet["gabarit"], str) else ""
    declaration = autorises.get(gabarit)
    if declaration is None:
        return None, gabarit[:60], "gabarit non autorise"
    valeurs = objet["valeurs"]
    if not isinstance(valeurs, dict):
        return None, gabarit, "valeurs : objet attendu"
    inconnues = set(valeurs) - set(declaration["valeurs"])
    if inconnues:
        return None, gabarit, f"valeur inconnue ({', '.join(sorted(map(str, inconnues)))[:60]})"
    resultat: dict[str, int | float] = {}
    for nom, bornes in declaration["valeurs"].items():
        v = valeurs.get(nom, bornes["defaut"])
        if isinstance(v, bool) or not isinstance(v, int | float) or not math.isfinite(v):
            return None, gabarit, f"{nom} : nombre attendu"
        if not bornes["min"] <= v <= bornes["max"]:
            return None, gabarit, f"{nom} hors bornes"
        crans = (v - bornes["min"]) / bornes["pas"]
        if abs(crans - round(crans)) > 1e-9:
            return None, gabarit, f"{nom} hors pas"
        resultat[nom] = _valeur(bornes["min"] + round(crans) * bornes["pas"])
    normalise = json.dumps({"gabarit": gabarit, "valeurs": resultat}, sort_keys=True, separators=(",", ":"))
    return normalise, gabarit, ""


def _exemple(autorises: dict[str, Any]) -> dict[str, Any]:
    """Exemple montre au modele : le premier gabarit avec ses valeurs par defaut."""
    gabarit, declaration = next(iter(autorises.items()))
    return {"gabarit": gabarit, "valeurs": {nom: b["defaut"] for nom, b in declaration["valeurs"].items()}}


class Brique(Module):
    id = "figures"
    titre = "Figures dans la discussion"

    @property
    def modes(self) -> tuple[str, ...]:
        return tuple(self.reglages.get("modes") or MODES_PAR_DEFAUT)

    @property
    def modes_revele(self) -> tuple[str, ...]:
        return tuple(self.reglages.get("modes_revele") or MODES_REVELE_PAR_DEFAUT)

    def autorises(self, conv: Conversation) -> dict[str, dict[str, Any]]:
        """Gabarits que Jules peut montrer dans cette conversation : aucun hors des modes autorises, et
        ceux qui revelent la reponse seulement dans les modes `modes_revele` (proposes ET acceptes)."""
        if conv.mode not in self.modes:
            return {}
        revele_permis = conv.mode in self.modes_revele
        return {
            gabarit: declaration
            for gabarit, declaration in figures_pour_discussion(self.tuteur.extensions).items()
            if revele_permis or not declaration.get("revele")
        }

    def contribution(self, conv: Conversation) -> str | None:
        autorises = self.autorises(conv)
        if not autorises:
            return None
        lignes = [
            "Tu peux montrer UNE figure dans ta réponse, si elle aide vraiment l'élève à comprendre. "
            "Écris pour cela, à l'endroit voulu, un bloc de code de langage figure qui contient seulement "
            "un objet JSON, par exemple :",
            "```figure",
            # indent=2 : accolades fermantes sur des lignes séparées, jamais « }} » (test_prompt_complet_sans_balise)
            json.dumps(_exemple(autorises), ensure_ascii=False, indent=2),
            "```",
            "Figures disponibles (les valeurs absentes prennent leur valeur par défaut) :",
        ]
        for gabarit, declaration in autorises.items():
            valeurs = " ; ".join(
                f"{nom} de {_valeur(b['min'])} à {_valeur(b['max'])} par pas de {_valeur(b['pas'])} "
                f"(défaut {_valeur(b['defaut'])})"
                for nom, b in declaration["valeurs"].items()
            )
            lignes.append(f"- {gabarit} : {declaration['quand']} Valeurs : {valeurs}.")
        lignes.append(
            "Règles : une figure au plus par réponse ; seulement si elle aide vraiment ; jamais de SVG, de code "
            "de dessin ni de dessin en caractères. Un bloc hors de ces règles est retiré avant que l'élève le voie."
        )
        return "\n".join(lignes)

    def filtrer_reponse(self, conv: Conversation, texte: str, relancer: Callable[[], str]) -> str:
        if "figure" not in texte:
            return texte
        autorises = self.autorises(conv)
        ecartees: list[dict[str, str]] = []
        gardee = False

        def remplacer(m: re.Match[str]) -> str:
            nonlocal gardee
            normalise, gabarit, raison = normaliser(m.group("json"), autorises)
            if normalise is not None and gardee:
                normalise, raison = None, "une seule figure par message"
            if normalise is None:
                ecartees.append({"gabarit": gabarit, "raison": raison if autorises else "mode sans figure"})
                return ""
            gardee = True
            return f"```figure\n{normalise}\n```"

        def neutraliser(m: re.Match[str]) -> str:
            ecartees.append({"gabarit": "", "raison": "imbrique"})
            return f"{m['avant']}{m['cloture']}{m['espace']}texte"

        resultat = _BLOC.sub(remplacer, _IMBRIQUE.sub(neutraliser, texte))
        for ecartee in ecartees:
            self.tuteur.stockage.ajouter_evenement("figure_ecartee", ecartee, conv.id)
        if not ecartees:
            return resultat
        return re.sub(r"\n{3,}", "\n\n", resultat).strip()
