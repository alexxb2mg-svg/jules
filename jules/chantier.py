"""Commande `jules chantier` : l'appel a contributions pour ecrire les fiches v2 de tout le programme.

  jules chantier etat DOSSIER... [--reservations FICHIER.json] [--depot PROPRIETAIRE/DEPOT] [--sortie FICHIER.md]
      Tableau de bord : pour chaque notion du referentiel, l'etat de sa fiche v2 dans les bibliotheques DOSSIER
      (a faire, reservee, generee, verifiee, relue), les reservations en cours et les propositions en attente.
      `--reservations` : liste JSON des tickets de reservation ouverts (`gh issue list --json ...`).

  jules chantier paquet NOTION [NOTION...] [--par PSEUDO] [--sortie FICHIER.md]
      Le paquet de generation : un texte a coller tel quel dans une IA (Claude, Mistral, ChatGPT, Albert...),
      qui contient le contrat v2, une fiche modele, les attendus officiels de chaque notion demandee et les
      regles. Le meme paquet pour tout le monde : c'est lui qui normalise les contributions.

La filiere complete (reserver, generer, verifier, proposer) est decrite dans docs/CHANTIER.md.
Fiches visuelles : `jules chantier visuel` et `jules chantier apercu`
(jules/chantier_visuel.py, charte : docs/FICHES-VISUELLES.md).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from jules.bibliotheques import (
    LICENCES_LIBRES,
    Notion,
    Racines,
    charger_catalogue,
    dossier_bibliotheque,
    liste_racines,
)
from jules.config import RACINE
from jules.fiches.commande import est_proposition, fiches_v2
from jules.fiches.schema import servable_sans_ia

EXPIRATION_JOURS = 21  # une reservation sans activite depuis 3 semaines libere ses notions
ORDRE_NIVEAUX = ("CM1", "CM2", "6e", "5e", "4e", "3e")  # du plus petit au plus grand, pour les prerequis
ETATS = ("a faire", "reservee", "generee", "a reverifier", "verifiee", "relue")
LIBELLES = {
    "a faire": "à faire",
    "reservee": "réservée",
    "generee": "générée",
    "a reverifier": "à re-vérifier",
    "verifiee": "vérifiée",
    "relue": "relue",
}
CONTRAT = RACINE / "docs" / "FICHES-V2.md"
DEMONSTRATION = "fiches-v2-demonstration"
# Fiche modele montree dans le paquet selon la matiere : la plus proche par la forme des exercices.
MODELE_CALCUL = "nombres-premiers-decomposition"
MODELE_TEXTE = "guerre-totale-1914-1918"
MATIERES_CALCUL = ("mathematiques", "physique-chimie", "technologie", "sciences-et-technologie", "svt")


# --- etat du chantier ---------------------------------------------------------------------------


@dataclass
class EtatNotion:
    notion: Notion
    etat: str = "a faire"
    fiche: str = ""  # chemin relatif de la fiche servie, s'il y en a une
    propositions: int = 0
    reservations: list[tuple[int, str]] = field(default_factory=list)  # (numero du ticket, auteur)


def etat_fiche(fiche: dict[str, Any]) -> str:
    if fiche.get("etat") in ("verifiee", "relue") and not servable_sans_ia(fiche):
        return "a reverifier"  # contenu modifie depuis la signature
    return {"relue": "relue", "verifiee": "verifiee"}.get(str(fiche.get("etat")), "generee")


def notions_citees(texte: str, notions: set[str]) -> list[str]:
    """Identifiants de notions cites dans un ticket : seules comptent les lignes faites uniquement
    d'identifiants (« racine-carree, ratio », « - `ratio` »), pour qu'une phrase qui contient le mot
    « ratio » ne reserve rien."""
    trouvees: list[str] = []
    for ligne in texte.splitlines():
        mots = [m.strip("`*") for m in re.split(r"[\s,;]+", ligne.strip().lstrip("-*").strip()) if m.strip("`*")]
        if mots and all(m in notions for m in mots):
            trouvees += [m for m in mots if m not in trouvees]
    return trouvees


def lire_reservations(
    chemin: Path, notions: set[str], jour: date | None = None, expiration: int = EXPIRATION_JOURS
) -> dict[str, list[tuple[int, str]]]:
    """Tickets de reservation ouverts -> notions reservees. Un ticket peut reserver plusieurs notions.

    Un ticket sans activite depuis `expiration` jours ne reserve plus rien : la notion redevient « a faire »
    (le ticket reste ouvert, son auteur peut le relancer d'un commentaire).
    """
    tickets = json.loads(chemin.read_text(encoding="utf-8")) or []
    limite = (jour or date.today()) - timedelta(days=expiration)
    reservees: dict[str, list[tuple[int, str]]] = {}
    for ticket in tickets:
        activite = str(ticket.get("updatedAt") or "")[:10]
        if activite and date.fromisoformat(activite) < limite:
            continue
        auteur = (ticket.get("author") or {}).get("login") or "?"
        for identifiant in notions_citees(str(ticket.get("body") or ""), notions):
            reservees.setdefault(identifiant, []).append((int(ticket.get("number") or 0), str(auteur)))
    return reservees


def etat_du_chantier(
    racines: Racines, dossiers: list[Path], reservations: dict[str, list[tuple[int, str]]] | None = None
) -> list[EtatNotion]:
    catalogue = charger_catalogue(racines, ["programme"], None)
    etats = {i: EtatNotion(notion=n) for i, n in catalogue.notions.items()}
    rang = {e: i for i, e in enumerate(ETATS)}
    for dossier in dossiers:
        for chemin, fiche in fiches_v2(dossier).items():
            suivi = etats.get(str(fiche.get("notion")))
            if suivi is None:
                continue  # notion inconnue : `jules fiches verifier` la signale
            if est_proposition(dossier, chemin):
                suivi.propositions += 1
                continue
            etat = etat_fiche(fiche)
            if rang[etat] > rang[suivi.etat]:
                suivi.etat = etat
                suivi.fiche = f"{dossier.name}/{chemin.relative_to(dossier).as_posix()}"
    for identifiant, tickets in (reservations or {}).items():
        suivi = etats[identifiant]
        suivi.reservations = tickets
        if suivi.etat == "a faire":
            suivi.etat = "reservee"
    return list(etats.values())


def _lien_ticket(numero: int, auteur: str, depot: str) -> str:
    cible = f"[#{numero}](https://github.com/{depot}/issues/{numero})" if depot else f"#{numero}"
    return f"@{auteur} ({cible})"


def _pourcent(partie: int, total: int) -> str:
    return f"{round(100 * partie / total)} %" if total else "—"


def rendre_etat(etats: list[EtatNotion], depot: str = "", jour: str = "") -> str:
    faites = ("verifiee", "relue")
    lignes = [
        "# Chantier des fiches v2",
        "",
        f"*Page générée le {jour or date.today().isoformat()} par `jules chantier etat` : "
        "ne pas la modifier à la main.*",
        "",
        "Chaque notion du programme attend sa fiche v2 (exercices corrigés par le code, voir "
        "[CONTRIBUER.md](CONTRIBUER.md)). Choisissez une ou plusieurs notions **à faire**, réservez-les par un "
        "ticket « Je réserve des notions », générez, vérifiez, proposez.",
        "",
        "| État | Sens |",
        "|---|---|",
        "| à faire | personne n'y travaille |",
        f"| réservée | un ticket de réservation est actif (moins de {EXPIRATION_JOURS} jours sans nouvelles) : "
        "d'autres générations restent bienvenues, en proposition |",
        "| générée | une fiche est déposée, pas encore conforme ou pas encore signée |",
        "| à re-vérifier | la fiche a changé depuis sa signature |",
        "| vérifiée | conforme au contrat et scellée : servie sans IA, marquée expérimentale |",
        "| relue | relue par un enseignant |",
        "",
        "## Vue d'ensemble",
        "",
        "| Niveau | Notions | " + " | ".join(LIBELLES[e] for e in ETATS) + " | Avancement |",
        "|---|---:|" + "---:|" * len(ETATS) + "---:|",
    ]
    niveaux = [n for n in ORDRE_NIVEAUX if any(e.notion.niveau == n for e in etats)]
    niveaux += sorted({e.notion.niveau for e in etats} - set(niveaux))
    for niveau in niveaux:
        du_niveau = [e for e in etats if e.notion.niveau == niveau]
        compte = Counter(e.etat for e in du_niveau)
        avance = sum(compte[e] for e in faites)
        cellules = " | ".join(str(compte[e]) for e in ETATS)
        lignes.append(f"| {niveau} | {len(du_niveau)} | {cellules} | {_pourcent(avance, len(du_niveau))} |")
    total = Counter(e.etat for e in etats)
    avance_totale = sum(total[e] for e in faites)
    lignes.append(
        f"| **Total** | **{len(etats)}** | "
        + " | ".join(f"**{total[e]}**" for e in ETATS)
        + f" | **{_pourcent(avance_totale, len(etats))}** |"
    )
    for niveau in niveaux:
        lignes += ["", f"## {niveau}", ""]
        matieres: dict[str, list[EtatNotion]] = {}
        for e in etats:
            if e.notion.niveau == niveau:
                matieres.setdefault(e.notion.nom_matiere, []).append(e)
        for nom, liste in matieres.items():
            compte = Counter(e.etat for e in liste)
            resume = ", ".join(f"{compte[e]} {LIBELLES[e]}" for e in ETATS if compte[e])
            lignes += [
                "<details>",
                f"<summary><b>{nom}</b> — {len(liste)} notions : {resume}</summary>",
                "",
                "| Notion (identifiant) | Chapitre | État | Réservée par | Propositions |",
                "|---|---|---|---|---:|",
            ]
            for e in liste:
                reserve = ", ".join(_lien_ticket(n, a, depot) for n, a in e.reservations) or ""
                lignes.append(
                    f"| {e.notion.titre} (`{e.notion.id}`) | {e.notion.chapitre} | {LIBELLES[e.etat]} "
                    f"| {reserve} | {e.propositions or ''} |"
                )
            lignes += ["", "</details>", ""]
    return "\n".join(lignes).rstrip() + "\n"


# --- paquet de generation -----------------------------------------------------------------------

CONSIGNES = """\
# Paquet de génération Jules — fiches v2

Tu vas écrire {nombre} fiche(s) de révision pour Jules, un tuteur libre pour les élèves (du CM1 à la 3e).
Une fiche v2 est un fichier YAML au contrat strict : ses exercices sont corrigés par un programme, sans IA.
Un programme vérifiera chaque fiche (`jules fiches verifier`) ; un enseignant la relira ensuite.

## Règles non négociables

1. **Une fiche par notion ci-dessous**, au format exact décrit dans « Le contrat ». Aucun champ inventé :
   un champ inconnu fait refuser la fiche.
2. **Tu pars des attendus officiels donnés pour chaque notion**, et de sources libres. Tu ne recopies rien
   d'un manuel, d'un site d'enseignant ou de toute source qui n'est pas sous licence libre. Licences acceptées
   dans `sources[].licence` : {licences}.
3. **N'invente jamais une source ni une URL.** Si tu ne peux pas consulter le web, cite uniquement les textes
   officiels listés avec la notion (URL fournies, licence `etalab-2.0`) et écris `usage: "rédigé à partir des
   attendus officiels"`. Une URL inventée fait rejeter la contribution.
4. **Reste dans le niveau.** Rien au-delà des attendus et des limites de la notion. Vocabulaire d'un élève de
   ce niveau, phrases courtes.
5. **Refais chaque calcul, deux fois.** Un corrigé faux est pire que pas de corrigé.
6. **Aucun indice ni aucune relance de piège ne contient la réponse**, même écrite autrement.
7. **Au moins 3 exercices corrigés par le code** (tout type sauf `ouverte`), dont un de difficulté 1 ; trois
   indices par exercice (`relance`, puis `methode`, puis `etape`) ; au moins 3 `declencheurs` (mots qu'un élève
   emploie sans nommer la notion, de 3 lettres ou plus, sans doublon) ; `prerequis` choisis dans la liste
   fournie (liste vide si aucun).
8. **Champs imposés** pour chaque fiche : `format: 2`, `version: 1`, `etat: generee`,
   `relecture: {{statut: a_relire, par: "", le: ""}}`, pas de champ `empreinte`, et :
   ```yaml
   generation:
     par: "{par}"
     le: "{jour}"
     modele: "<ton nom de modèle, exact>"
     a_partir_de: "référentiel Jules (attendus officiels) et sources citées"
     paquet: "{version}"
   ```

9. **YAML valide** : mets entre guillemets tout texte qui contient « : » (un ratio 2 : 3, « Attention : »), un
   « # », ou qui commence par un signe (`-`, `*`, `[`, `{{`, `>`, `|`, `@`, `%`, `!`, `&`, `'`, `"`).

## Ce que tu rends

Pour chaque notion, un bloc de code YAML précédé de la ligne `Fichier : fiches/<matiere>/<notion>.yaml`, rien
d'autre (pas de commentaire entre les blocs). Si une notion ne se prête pas à 3 exercices corrigés par le code,
dis-le en une phrase au lieu d'inventer des exercices artificiels.

Si on te renvoie ensuite la sortie de `jules fiches verifier`, corrige **seulement** les manquements signalés et
rends la fiche entière corrigée.
"""


def _texte_contrat() -> str:
    """Les sections « Le format » et « Les types d'exercice » de docs/FICHES-V2.md : une seule source de verite."""
    if not CONTRAT.is_file():
        return "(docs/FICHES-V2.md introuvable : lancer la commande depuis un clone du depot jules)"
    texte = CONTRAT.read_text(encoding="utf-8")
    debut, fin = texte.find("## Le format"), texte.find("## Le parcours sans IA")
    return texte[debut:fin].strip() if debut >= 0 and fin > debut else texte


def _fiche_modele(racines: Racines, notions: list[Notion]) -> tuple[str, str]:
    """(id, texte) de la fiche de demonstration la plus proche, jamais celle d'une notion demandee."""
    demandees = {n.id for n in notions}
    calcul = sum(n.matiere in MATIERES_CALCUL for n in notions) * 2 >= len(notions)
    ordre = [MODELE_CALCUL, MODELE_TEXTE] if calcul else [MODELE_TEXTE, MODELE_CALCUL]
    dossier = dossier_bibliotheque(racines, DEMONSTRATION) / "fiches"
    for identifiant in ordre:
        if identifiant in demandees:
            continue
        for chemin in dossier.rglob(f"{identifiant}.yaml"):
            fiche = yaml.safe_load(chemin.read_text(encoding="utf-8"))
            fiche.pop("empreinte", None)
            fiche["etat"] = "generee"
            return identifiant, yaml.safe_dump(fiche, allow_unicode=True, sort_keys=False, width=110)
    return "", ""


def _textes_officiels(racines: Racines, notion: Notion) -> list[dict[str, Any]]:
    fichier = dossier_bibliotheque(racines, "programme") / notion.niveau / f"{notion.matiere}.yaml"
    brut = yaml.safe_load(fichier.read_text(encoding="utf-8")) or {}
    return [t for t in brut.get("textes_officiels") or [] if isinstance(t, dict)]


def _prerequis_possibles(tous: dict[str, Notion], notion: Notion) -> list[Notion]:
    """Notions de la meme matiere, au meme niveau ou au niveau d'avant."""
    niveaux = {notion.niveau}
    if notion.niveau in ORDRE_NIVEAUX:
        rang = ORDRE_NIVEAUX.index(notion.niveau)
        presents = [n for n in ORDRE_NIVEAUX[:rang] if any(x.niveau == n for x in tous.values())]
        niveaux.update(presents[-1:])
    return [n for n in tous.values() if n.matiere == notion.matiere and n.niveau in niveaux and n.id != notion.id]


def _section_notion(racines: Racines, tous: dict[str, Notion], notion: Notion) -> str:
    lignes = [
        f"### {notion.titre}",
        "",
        f"- Identifiant (champ `notion`) : `{notion.id}`",
        f"- Fichier : `fiches/{notion.matiere}/{notion.id}.yaml`",
        f"- Niveau : {notion.niveau} ({notion.niveau_programme or 'non précisé'}) — {notion.nom_matiere}",
        f"- Thème : {notion.theme} ; chapitre : {notion.chapitre}",
    ]
    if notion.source:
        lignes.append(f"- Où c'est dans le texte officiel : {notion.source}")
    lignes += ["", "Attendus officiels :"] + [f"- {a}" for a in notion.attendus]
    if notion.limites:
        lignes += ["", "Limites posées par le texte officiel (ne pas aller au-delà) :"]
        lignes += [f"- {li}" for li in notion.limites]
    if notion.mots_cles:
        lignes += ["", "Mots-clés du référentiel (ne pas les reprendre tels quels comme déclencheurs) : "]
        lignes[-1] += ", ".join(notion.mots_cles)
    textes = _textes_officiels(racines, notion)
    if textes:
        lignes += ["", "Textes officiels (licence etalab-2.0, citables tels quels dans `sources`) :"]
        for t in textes:
            lignes.append(
                f"- {t.get('intitule', '')} — {t.get('reference', '')} — {t.get('url', '')} "
                f"(consulté le {t.get('consulte_le', '')})"
            )
    possibles = _prerequis_possibles(tous, notion)
    lignes += ["", "Prérequis possibles (identifiants exacts ; n'en retenir que 0 à 3 vraiment nécessaires) :"]
    lignes += [f"- `{p.id}` : {p.titre} ({p.niveau})" for p in possibles] or ["- (aucun)"]
    return "\n".join(lignes)


def version_paquet() -> str:
    """Change quand les consignes ou le contrat changent : une fiche dit de quel paquet elle vient."""
    empreinte = hashlib.sha256((CONSIGNES + _texte_contrat()).encode("utf-8")).hexdigest()
    return f"fiche-v2/{empreinte[:10]}"


def paquet(racines: Racines, ids: list[str], par: str = "", jour: str = "") -> str:
    catalogue = charger_catalogue(racines, ["programme"], None)
    inconnues = [i for i in ids if i not in catalogue.notions]
    if inconnues:
        raise ValueError(f"notion(s) inconnue(s) du referentiel : {', '.join(inconnues)}")
    notions = [catalogue.notions[i] for i in dict.fromkeys(ids)]
    modele_id, modele = _fiche_modele(racines, notions)
    parties = [
        CONSIGNES.format(
            nombre=len(notions),
            licences=", ".join(LICENCES_LIBRES),
            par=par or "<ton pseudo>",
            jour=jour or date.today().isoformat(),
            version=version_paquet(),
        ).rstrip(),
        "## Le contrat (extrait de docs/FICHES-V2.md)\n\n" + _texte_contrat(),
    ]
    if modele:
        parties.append(
            f"## Une fiche conforme, pour la forme seulement (`{modele_id}`)\n\n"
            "Ne reprends ni son contenu ni ses exercices : elle montre la structure attendue et le niveau de soin.\n\n"
            f"```yaml\n{modele.rstrip()}\n```"
        )
    parties.append(
        "## Les notions à traiter\n\n" + "\n\n".join(_section_notion(racines, catalogue.notions, n) for n in notions)
    )
    return "\n\n".join(parties) + "\n"


# --- ligne de commande ----------------------------------------------------------------------------


def _options(args: list[str], connues: tuple[str, ...]) -> tuple[list[str], dict[str, str]]:
    positionnels: list[str] = []
    options: dict[str, str] = {}
    i = 0
    while i < len(args):
        if args[i] in connues:
            if i + 1 >= len(args):
                sys.exit(f"{args[i]} attend une valeur")
            options[args[i]] = args[i + 1]
            i += 2
        elif args[i].startswith("--"):
            sys.exit(f"Option inconnue : {args[i]} (connues : {', '.join(connues)})")
        else:
            positionnels.append(args[i])
            i += 1
    return positionnels, options


def _ecrire(texte: str, sortie: str | None) -> None:
    if sortie:
        Path(sortie).write_text(texte, encoding="utf-8")
        print(f"Ecrit : {sortie}")
    else:
        print(texte, end="")


def main(args: list[str], racines: Racines) -> None:
    if args and args[0] in ("visuel", "apercu"):  # le patron des fiches visuelles : jules/chantier_visuel.py
        from jules import chantier_visuel

        (chantier_visuel.main_visuel if args[0] == "visuel" else chantier_visuel.main_apercu)(args[1:], racines)
        return
    if not args or args[0] not in ("etat", "paquet"):
        print(__doc__)
        return
    if args[0] == "etat":
        dossiers, options = _options(args[1:], ("--reservations", "--depot", "--sortie"))
        chemins = [Path(d).resolve() for d in dossiers]
        manquants = [str(c) for c in chemins if not (c / "bibliotheque.yaml").is_file()]
        if manquants:
            sys.exit(f"Pas une bibliotheque (bibliotheque.yaml manquant) : {', '.join(manquants)}")
        reservations = None
        if "--reservations" in options:
            notions = set(charger_catalogue(racines, ["programme"], None).notions)
            reservations = lire_reservations(Path(options["--reservations"]), notions)
        etats = etat_du_chantier(liste_racines(racines), chemins, reservations)
        _ecrire(rendre_etat(etats, options.get("--depot", "")), options.get("--sortie"))
        return
    ids, options = _options(args[1:], ("--par", "--sortie"))
    if not ids:
        sys.exit("Indiquer au moins une notion (identifiant du referentiel, voir CHANTIER.md)")
    try:
        texte = paquet(racines, ids, par=options.get("--par", ""))
    except ValueError as err:
        sys.exit(str(err))
    _ecrire(texte, options.get("--sortie"))
