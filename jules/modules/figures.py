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

Schema d'une fiche visuelle : le modele peut aussi CITER le schema (SVG deja verifie, jamais ecrit par lui)
de la fiche visuelle d'une notion :
    ```figure
    {"schema": "theoreme-pythagore"}
    ```
Liste blanche par conversation : la notion de la conversation (module 'notions') et ses prerequis, s'ils ont
une fiche visuelle chargee avec un bloc `schema` (module 'fiches_visuelles'). Jamais les 410 ids dans le prompt.

Mode 'cours' (panneau de Jules dans une lecon) : la notion est celle de la lecon (module 'cours'), et une
figure ou un schema qui montrerait la reponse de l'exercice actif est ecarte (raison « revelerait la reponse ») :
les valeurs d'un gabarit ne sont completees qu'ici, apres le garde-fou du module 'cours'.

Dans TOUS les modes (meme sans figure), la contribution interdit le dessin en caracteres (REGLE_DESSIN) :
mesure du 03/10, en cours sans figure le modele dessinait un triangle en ASCII.

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
from jules.lecons import contient_la_reponse
from jules.modules.base import Module
from jules.stockage import Conversation

MODES_PAR_DEFAUT = ("aide-devoirs", "reexplique")
# Gabarits `revele: true` (la figure montre la reponse : solutions placees, longueur ecrite) : proposes et
# acceptes seulement dans ces modes. Jamais 'aide-devoirs' : la figure ferait l'exercice a la place de l'eleve.
MODES_REVELE_PAR_DEFAUT = ("reexplique",)
# Envoyee dans tous les modes, meme sans figure disponible (epreuve comprise).
REGLE_DESSIN = (
    "Ne dessine jamais en caractères (traits, barres, schéma ASCII) : si une image aiderait et qu'aucune figure "
    "n'est disponible ici, dis-le en une phrase et explique avec des mots, ou propose d'ouvrir la fiche visuelle "
    "de la notion."
)
PREREQUIS_MAX = 4  # schemas de prerequis proposes au modele, au-dela de celui de la notion

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
    forcees = declaration.get("forcees") or ()
    for nom, bornes in declaration["valeurs"].items():
        if nom in forcees:
            # valeur qui montrerait la reponse (valeurs_revele) hors modes_revele : toujours son defaut, quoi
            # qu'ait ecrit le modele ; le bloc reste (figure « ? »).
            resultat[nom] = _valeur(bornes["defaut"])
            continue
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


def normaliser_schema(objet: dict[str, Any], schemas: dict[str, str]) -> tuple[str | None, str, str]:
    """Bloc {"schema": id} : (JSON normalise ou None, id lu, raison du rejet). `schemas` : id -> titre."""
    if set(objet) != {"schema"}:
        return None, "", "attendu {schema}"
    notion = objet["schema"] if isinstance(objet["schema"], str) else ""
    if notion not in schemas:
        return None, f"schema:{notion[:60]}", "schema non autorise"
    return json.dumps({"schema": notion}, separators=(",", ":")), f"schema:{notion}", ""


def normaliser_bloc(
    source: str, autorises: dict[str, dict[str, Any]], schemas: dict[str, str]
) -> tuple[str | None, str, str]:
    """Un bloc ```figure : schema de fiche ({"schema": id}) ou gabarit ({gabarit, valeurs})."""
    try:
        objet = json.loads(source)
    except (json.JSONDecodeError, RecursionError):
        objet = None
    if isinstance(objet, dict) and "schema" in objet:
        return normaliser_schema(objet, schemas)
    return normaliser(source, autorises)


def _revele(normalise: str, bloc: Any) -> bool:
    """Vrai si les valeurs d'un gabarit normalise (« t = 0.5 ») donnent la reponse de l'exercice `bloc`
    (garde-fou du module 'cours', applique ici car les valeurs absentes ne sont completees qu'ici)."""
    valeurs = json.loads(normalise).get("valeurs") or {}
    return bool(valeurs) and contient_la_reponse(" ; ".join(f"{n} = {v}" for n, v in valeurs.items()), bloc)


def _exemple(autorises: dict[str, Any]) -> dict[str, Any]:
    """Exemple montre au modele : le premier gabarit avec ses valeurs par defaut (sans les valeurs forcees)."""
    gabarit, declaration = next(iter(autorises.items()))
    return {
        "gabarit": gabarit,
        "valeurs": {nom: b["defaut"] for nom, b in _proposees(declaration).items()},
    }


def _proposees(declaration: dict[str, Any]) -> dict[str, Any]:
    """Valeurs donnees au modele : toutes, sauf celles forcees a leur defaut dans ce mode (valeurs_revele)."""
    forcees = declaration.get("forcees") or ()
    return {nom: b for nom, b in declaration["valeurs"].items() if nom not in forcees}


def texte_sans_figures(texte: str) -> str:
    """Le texte d'un message avec chaque bloc ```figure remplace par « [figure : <gabarit>] » : pour ce qui
    lit les messages sans les dessiner (analyse de suivi...). Un bloc illisible devient « [figure] »."""

    def resume(m: re.Match[str]) -> str:
        try:
            objet = json.loads(m.group("json"))
        except (json.JSONDecodeError, RecursionError):
            objet = None
        gabarit = objet.get("gabarit") if isinstance(objet, dict) else None
        schema = objet.get("schema") if isinstance(objet, dict) else None
        if isinstance(schema, str) and schema:
            return f"[schéma : {schema[:60]}]"
        return f"[figure : {gabarit[:60]}]" if isinstance(gabarit, str) and gabarit else "[figure]"

    return _BLOC.sub(resume, texte) if "figure" in texte else texte


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
        ceux qui revelent la reponse seulement dans les modes `modes_revele` (proposes ET acceptes). Hors de
        ces modes, les `valeurs_revele` d'un gabarit sont marquees `forcees` : normaliser() les ramene a leur
        defaut et la contribution ne les donne pas au modele (la regle tient par le code, pas par `quand`)."""
        if conv.mode not in self.modes:
            return {}
        revele_permis = conv.mode in self.modes_revele
        resultat: dict[str, dict[str, Any]] = {}
        for gabarit, declaration in figures_pour_discussion(self.tuteur.extensions).items():
            if declaration.get("revele") and not revele_permis:
                continue
            forcees = () if revele_permis else tuple(declaration.get("valeurs_revele") or ())
            resultat[gabarit] = {**declaration, "forcees": forcees} if forcees else declaration
        return resultat

    def infos_interface(self) -> dict[str, Any]:
        """Bornes des curseurs sous une figure de la bulle (lot 3) : {gabarit -> {nom -> {min, max, pas,
        defaut}}}, pour tous les gabarits declares. Le serveur a deja choisi quelles figures un message
        peut porter (filtrer_reponse) ; ici l'eleve fait seulement bouger, dans les bornes, celle qu'il a.
        Une `valeurs_revele` est figee (min = max = defaut) : jamais de curseur, dans aucun mode ; la bulle
        garde la valeur ecrite (et deja verifiee) dans le bloc."""

        def bornes(nom: str, b: dict[str, float], figees: list[str]) -> dict[str, float]:
            if nom in figees:
                return {"min": b["defaut"], "max": b["defaut"], "pas": b["pas"], "defaut": b["defaut"]}
            return {cle: b[cle] for cle in ("min", "max", "pas", "defaut")}

        return {
            "figures": {
                gabarit: {
                    nom: bornes(nom, b, declaration.get("valeurs_revele") or [])
                    for nom, b in declaration["valeurs"].items()
                }
                for gabarit, declaration in figures_pour_discussion(self.tuteur.extensions).items()
            }
        }

    # --- schemas des fiches visuelles -------------------------------------------------------------
    def _prerequis(self, notion_id: str) -> list[str]:
        """Prerequis declares par les fiches de la notion (module 'notions', puis fiches v2 de 'exercices')."""
        trouves: list[str] = []
        notions = self.tuteur.module("notions")
        if notions is not None:
            fiche, _ = notions.catalogue.fiche(notion_id)  # type: ignore[attr-defined]
            trouves.extend(str(p) for p in fiche.get("prerequis") or [])
        exercices = self.tuteur.module("exercices")
        if exercices is not None:
            fiche_v2 = exercices.fiches.get(notion_id) or {}  # type: ignore[attr-defined]
            trouves.extend(str(p) for p in fiche_v2.get("prerequis") or [])
        return list(dict.fromkeys(p for p in trouves if p != notion_id))

    def _bloc_protege(self, conv: Conversation) -> Any:
        """Exercice actif non resolu de la lecon (mode cours), dont la reponse ne doit pas etre montree."""
        cours = self.tuteur.module("cours")
        return cours.bloc_protege(conv) if cours is not None else None  # type: ignore[attr-defined]

    def _notion(self, conv: Conversation) -> str:
        """Notion de la conversation : celle de la lecon en mode cours, sinon celle du module 'notions'."""
        cours = self.tuteur.module("cours")
        notion_id = cours.notion_de(conv) if cours is not None else None  # type: ignore[attr-defined]
        if notion_id:
            return str(notion_id)
        notions = self.tuteur.module("notions")
        if notions is None:
            return ""
        return str(notions.etat(conv.id).get("notion") or "")  # type: ignore[attr-defined]

    def schemas(self, conv: Conversation) -> dict[str, str]:
        """Schemas de fiche que Jules peut montrer ici (id de notion -> titre de la notion) : la notion de la
        conversation (ou de la lecon) puis ses prerequis, s'ils ont un schema. Rien hors des modes autorises ni
        sans notion ; en lecon, jamais un schema dont les textes donnent la reponse de l'exercice actif."""
        if conv.mode not in self.modes or not self.reglages.get("schemas", True):
            return {}
        fiches = self.tuteur.module("fiches_visuelles")
        if fiches is None:
            return {}
        notion_id = self._notion(conv)
        if not notion_id:
            return {}
        protege = self._bloc_protege(conv)
        resultat: dict[str, str] = {}
        for candidat in [notion_id, *self._prerequis(notion_id)]:
            if len(resultat) > PREREQUIS_MAX:
                break
            schema = fiches.schema(candidat)  # type: ignore[attr-defined]
            if schema is None:
                continue
            textes = fiches.texte_schema(candidat)  # type: ignore[attr-defined]
            if protege is not None and contient_la_reponse(textes, protege):
                continue
            resultat[candidat] = schema["titre"]
        return resultat

    def _contribution_schemas(self, schemas: dict[str, str]) -> list[str]:
        ids = list(schemas)
        lignes = [
            f"Tu peux montrer le schéma de la notion « {schemas[ids[0]]} » avec ce bloc, quand une image aide "
            "(toujours accompagné de ton explication en mots) :",
            "```figure",
            json.dumps({"schema": ids[0]}, ensure_ascii=False),
            "```",
        ]
        if len(ids) > 1:
            lignes.append("Schémas des notions à revoir avant celle-ci (même bloc, autre identifiant) :")
            lignes.extend(f"- {i} : {schemas[i]}" for i in ids[1:])
        return lignes

    def contribution(self, conv: Conversation) -> str | None:
        autorises = self.autorises(conv)
        schemas = self.schemas(conv)
        if not autorises and not schemas:
            return REGLE_DESSIN  # tous les modes, meme epreuve : jamais de dessin en caracteres
        lignes = self._contribution_schemas(schemas) if schemas else []
        if not autorises:
            lignes += [
                "Règles : une figure au plus par réponse ; jamais de SVG, de code de dessin ni de dessin en "
                "caractères. Un bloc hors de ces règles est retiré avant que l'élève le voie.",
                REGLE_DESSIN,
            ]
            return "\n".join(lignes)
        lignes += [
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
                for nom, b in _proposees(declaration).items()
            )
            lignes.append(f"- {gabarit} : {declaration['quand']} Valeurs : {valeurs}.")
        lignes.append(
            "Règles : une figure au plus par réponse ; seulement si elle aide vraiment ; jamais de SVG, de code "
            "de dessin ni de dessin en caractères. Un bloc hors de ces règles est retiré avant que l'élève le voie."
        )
        lignes.append(REGLE_DESSIN)
        return "\n".join(lignes)

    def filtrer_reponse(self, conv: Conversation, texte: str, relancer: Callable[[], str]) -> str:
        if "figure" not in texte:
            return texte
        autorises = self.autorises(conv)
        schemas = self.schemas(conv)
        permis = bool(autorises or schemas)
        protege = self._bloc_protege(conv) if permis else None
        ecartees: list[dict[str, str]] = []
        gardee = False

        def remplacer(m: re.Match[str]) -> str:
            nonlocal gardee
            normalise, gabarit, raison = normaliser_bloc(m.group("json"), autorises, schemas)
            if normalise is not None and protege is not None and _revele(normalise, protege):
                normalise, raison = None, "revelerait la reponse"
            if normalise is not None and gardee:
                normalise, raison = None, "une seule figure par message"
            if normalise is None:
                # `source` : ce que le modele a ecrit (tronque), pour comprendre les rejets en conditions reelles
                ecartees.append(
                    {
                        "gabarit": gabarit,
                        "raison": raison if permis else "mode sans figure",
                        "source": m.group("json").strip()[:200],
                    }
                )
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
