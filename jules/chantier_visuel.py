"""Le patron de generation des fiches visuelles : paquet pour l'IA, puis controle et apercu.

jules chantier visuel NOTION [NOTION...] [--par PSEUDO] [--sortie FICHIER.md]
    Le paquet de generation d'une fiche visuelle : la charte (docs/FICHES-VISUELLES.md), le format
    (bibliotheque/SCHEMA-FICHE-VISUELLE.md), une fiche modele avec son schema, et pour chaque notion
    ses attendus officiels et le contenu de sa fiche v2. Le meme paquet pour toutes les matieres :
    c'est lui qui rend les fiches reproductibles.

jules chantier apercu DOSSIER [NOTION...] [--sortie DOSSIER_APERCU] [--captures]
    Controle les fiches visuelles de la bibliotheque DOSSIER (motif de chaque fiche ecartee), puis
    construit un apercu hors ligne : la vraie page « Mes fiches », avec des reponses d'API simulees,
    a ouvrir dans un navigateur (index.html). `--captures` : une capture PNG par fiche (Chromium
    requis : variable JULES_CHROMIUM, ou chromium / google-chrome dans le PATH). Code de sortie 1
    si une fiche est ecartee.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from jules.bibliotheques import (
    Notion,
    Racines,
    charger_catalogue,
    lire_identite,
    liste_racines,
)
from jules.config import RACINE
from jules.extensions import charger_extensions, code_des_figures, code_des_rappels, figures_fournies
from jules.fiches_visuelles import ErreurFicheVisuelle, FicheVisuelle, lire_fiche_visuelle

CHARTE = RACINE / "docs" / "FICHES-VISUELLES.md"
FORMAT = RACINE / "bibliotheque" / "SCHEMA-FICHE-VISUELLE.md"
STATIQUE = RACINE / "jules" / "web" / "static"
MODELE_PAR_DEFAUT = "parallelisme-triangles-pythagore"

CONSIGNES = """\
# Paquet de génération Jules — fiches visuelles

Tu vas écrire {nombre} fiche(s) visuelle(s) pour Jules, un tuteur libre pour les élèves (du CM1 à la 3e).
Une fiche visuelle est une fiche de RÉVISION illustrée : elle explique et donne les réponses. Elle est affichée
telle quelle, sans IA ; un programme la contrôle (`jules chantier apercu`), un adulte la relit ensuite.

Ce que tu rends, pour chaque notion :
- `fiches/<matiere>/<notion>.yaml` (le chemin exact est donné plus bas), au format décrit ci-dessous ;
- un fichier `.svg` à côté pour chaque bloc `schema` (champ `svg: <nom>.svg`).

En-tête de chaque fiche : `auteurs: ["{par}"]`, `licence: CC-BY-SA-4.0`, `relecture: {{statut: a_relire}}`,
`generation: {{par: "{par}", le: "{jour}", paquet: "{version}"}}`. Sources : uniquement celles de la fiche v2
de la notion ou les textes officiels listés (même titre, même URL, même licence). N'invente jamais une source.

Règles d'écriture YAML : guillemets doubles autour de toute chaîne qui contient « : », « # » ou des `**`.

Suis la charte à la lettre : elle résume tout ce qui a été validé sur les premières fiches.
"""


def version_paquet() -> str:
    """Change des que la charte, le format ou les consignes changent."""
    texte = CONSIGNES + CHARTE.read_text(encoding="utf-8") + FORMAT.read_text(encoding="utf-8")
    return f"fiche-visuelle/{hashlib.sha256(texte.encode('utf-8')).hexdigest()[:10]}"


def _bibliotheques(racines: Racines, type_: str) -> list[Path]:
    trouvees = []
    for racine in liste_racines(racines):
        for identite in sorted(Path(racine).glob("*/bibliotheque.yaml")):
            try:
                if lire_identite(identite.parent).type == type_:
                    trouvees.append(identite.parent)
            except (OSError, ValueError, yaml.YAMLError):  # illisible : elle n'empeche pas le paquet
                continue
    return trouvees


def _fiche_v2(racines: Racines, notion: Notion) -> str:
    for dossier in _bibliotheques(racines, "fiches"):
        for chemin in sorted((dossier / "fiches").glob(f"*/{notion.id}.yaml")):
            return chemin.read_text(encoding="utf-8").rstrip()
    return ""


def _modele(racines: Racines, notions: list[Notion]) -> tuple[str, str, list[tuple[str, str]]]:
    """(id, yaml, [(nom, svg)]) : une fiche visuelle existante, de la meme matiere si possible,
    jamais celle d'une notion demandee."""
    demandees = {n.id for n in notions}
    matieres = {n.matiere for n in notions}
    candidats: list[Path] = []
    for dossier in _bibliotheques(racines, "fiches-visuelles"):
        candidats += sorted((dossier / "fiches").rglob("*.yaml"))
    candidats.sort(key=lambda c: (c.parent.name not in matieres, c.stem != MODELE_PAR_DEFAUT, str(c)))
    for chemin in candidats:
        if chemin.stem in demandees:
            continue
        texte = chemin.read_text(encoding="utf-8")
        schemas = re.findall(r"svg:\s*\"?([\w.-]+\.svg)\"?", texte)
        svgs = [(n, (chemin.parent / n).read_text(encoding="utf-8")) for n in schemas if (chemin.parent / n).is_file()]
        return chemin.stem, texte.rstrip(), svgs
    return "", "", []


def _textes_officiels(racines: Racines, notion: Notion) -> list[dict[str, Any]]:
    for racine in liste_racines(racines):
        fichier = Path(racine) / "programme" / notion.niveau / f"{notion.matiere}.yaml"
        if fichier.is_file():
            brut = yaml.safe_load(fichier.read_text(encoding="utf-8")) or {}
            return [t for t in brut.get("textes_officiels") or [] if isinstance(t, dict)]
    return []


def _section_notion(racines: Racines, notion: Notion) -> str:
    lignes = [
        f"### {notion.titre}",
        "",
        f"- Identifiant (champ `notion`) : `{notion.id}`",
        f"- Fichier : `fiches/{notion.matiere}/{notion.id}.yaml` (champ `matiere: {notion.matiere}`)",
        f"- Niveau : {notion.niveau} — {notion.nom_matiere} ; chapitre : {notion.chapitre}",
        "",
        "Attendus officiels (affichés automatiquement en tête de fiche, ne pas les recopier) :",
        *[f"- {a}" for a in notion.attendus],
    ]
    if notion.limites:
        lignes += [
            "",
            "Limites posées par le texte officiel (ne pas aller au-delà) :",
            *[f"- {x}" for x in notion.limites],
        ]
    textes = _textes_officiels(racines, notion)
    if textes:
        lignes += ["", "Textes officiels (licence etalab-2.0) :"]
        lignes += [f"- {t.get('intitule', '')} — {t.get('url', '')}" for t in textes]
    v2 = _fiche_v2(racines, notion)
    if v2:
        lignes += [
            "",
            "Fiche v2 de la notion (source du contenu : mêmes définitions, même piège, mêmes notations ; "
            "ne recopie pas ses exercices tels quels) :",
            "",
            f"```yaml\n{v2}\n```",
        ]
    else:
        lignes += [
            "",
            "Pas encore de fiche v2 pour cette notion : appuie-toi sur les attendus et les textes officiels.",
        ]
    return "\n".join(lignes)


def _document(chemin: Path) -> str:
    """Un document du depot, sans son titre, ses intertitres descendus d'un niveau (il devient une partie)."""
    corps = chemin.read_text(encoding="utf-8").split("\n", 1)[1].strip()
    morceaux = corps.split("```")  # les morceaux impairs sont des blocs de code : on n'y touche pas
    return "```".join(m if i % 2 else re.sub(r"^(#+) ", r"#\1 ", m, flags=re.M) for i, m in enumerate(morceaux))


def paquet(racines: Racines, ids: list[str], par: str = "", jour: str = "") -> str:
    catalogue = charger_catalogue(racines, ["programme"], None)
    inconnues = [i for i in ids if i not in catalogue.notions]
    if inconnues:
        raise ValueError(f"notion(s) inconnue(s) du referentiel : {', '.join(inconnues)}")
    notions = [catalogue.notions[i] for i in dict.fromkeys(ids)]
    parties = [
        CONSIGNES.format(
            nombre=len(notions),
            par=par or "<ton pseudo>",
            jour=jour or date.today().isoformat(),
            version=version_paquet(),
        ).rstrip(),
        "## La charte (docs/FICHES-VISUELLES.md)\n\n" + _document(CHARTE),
        "## Le format (bibliotheque/SCHEMA-FICHE-VISUELLE.md)\n\n" + _document(FORMAT),
    ]
    modele_id, modele, svgs = _modele(racines, notions)
    if modele:
        bloc = [
            f"## Une fiche conforme, pour la forme et le niveau de soin (`{modele_id}`)",
            "",
            "Ne reprends pas son contenu : elle montre la structure, le ton et la facture attendus.",
            "",
            f"```yaml\n{modele}\n```",
        ]
        for nom, svg in svgs:
            bloc += ["", f"Son schéma `{nom}` :", "", f"```svg\n{svg.rstrip()}\n```"]
        parties.append("\n".join(bloc))
    parties.append("## Les notions à traiter\n\n" + "\n\n".join(_section_notion(racines, n) for n in notions))
    return "\n\n".join(parties) + "\n"


# --- controle et apercu ---------------------------------------------------------------------------


def _gabarits_et_extensions() -> tuple[frozenset[str], dict[str, Any]]:
    config = yaml.safe_load((RACINE / "config.yaml").read_text(encoding="utf-8")) or {}
    extensions = charger_extensions(RACINE / "extensions", config.get("extensions") or [])
    return frozenset(figures_fournies(extensions)), extensions


def controler(
    racines: Racines, dossier: Path, ids: list[str] | None = None
) -> tuple[dict[str, FicheVisuelle], list[str]]:
    """Fiches visuelles valides de la bibliotheque `dossier`, et le motif de chaque fiche ecartee."""
    catalogue = charger_catalogue([*liste_racines(racines), dossier.parent], ["programme"], None)
    gabarits, _ = _gabarits_et_extensions()
    biblio = lire_identite(dossier)
    fiches: dict[str, FicheVisuelle] = {}
    ecartees: list[str] = []
    for chemin in sorted((dossier / "fiches").rglob("*.yaml")):
        if ids and chemin.stem not in ids:
            continue
        try:
            fiche = lire_fiche_visuelle(chemin, catalogue.notions, biblio, gabarits)
        except (ErreurFicheVisuelle, OSError) as err:
            ecartees.append(f"{chemin.relative_to(dossier)} : {err}")
            continue
        fiches[fiche.notion] = fiche
    return fiches, ecartees


def _donnees_simulees(racines: Racines, fiches: dict[str, FicheVisuelle]) -> dict[str, Any]:
    catalogue = charger_catalogue(racines, ["programme"], None)
    donnees: dict[str, Any] = {
        "/api/session": {"eleve": True},
        "/api/infos": {"persona": {"nom": "Jules", "couleurs": {"principale": "#1F4E8C", "secondaire": "#C8102E"}}},
    }
    matieres: dict[str, dict[str, Any]] = {}
    for notion_id in [n for n in catalogue.notions if n in fiches]:
        notion, fiche = catalogue.notions[notion_id], fiches[notion_id]
        publique = fiche.publique(notion.attendus)
        publique.update(
            licence=fiche.licence, nom_matiere=notion.nom_matiere, relecture_a_relire=fiche.relecture == "a_relire"
        )
        donnees[f"/api/eleve/fiches_visuelles/notions/{notion_id}"] = publique
        donnees[f"/api/eleve/fiches_visuelles/notions/{notion_id}/rappels"] = {
            "matiere": notion.matiere,
            "variables": fiche.toutes_les_variables(),
            "abreviations": dict(fiche.abreviations),
        }
        entree = matieres.setdefault(notion.matiere, {"id": notion.matiere, "nom": notion.nom_matiere, "notions": []})
        entree["notions"].append({"id": notion_id, "titre": notion.titre, "chapitre": notion.chapitre})
    donnees["/api/eleve/fiches_visuelles/notions"] = {"matieres": list(matieres.values())}
    return donnees


def construire_apercu(racines: Racines, fiches: dict[str, FicheVisuelle], sortie: Path) -> Path:
    """La page « Mes fiches » en fichiers statiques, l'API remplacee par des reponses simulees."""
    _, extensions = _gabarits_et_extensions()
    shutil.rmtree(sortie, ignore_errors=True)
    shutil.copytree(STATIQUE, sortie / "static")
    (sortie / "gabarits.js").write_text(code_des_figures(extensions), encoding="utf-8")
    (sortie / "rappels.js").write_text(code_des_rappels(extensions), encoding="utf-8")
    donnees = json.dumps(_donnees_simulees(racines, fiches), ensure_ascii=False)
    (sortie / "simulation.js").write_text(
        "// Apercu hors serveur : reponses de l'API de Jules simulees, aucune donnee d'eleve.\n"
        f"const DONNEES = {donnees};\n"
        "window.fetch = async (chemin) => { const c = DONNEES[decodeURIComponent(String(chemin)).split('?')[0]];\n"
        "  return { status: c ? 200 : 404, ok: !!c, json: async () => c || {} }; };\n"
        "navigator.sendBeacon = () => true;\n",
        encoding="utf-8",
    )
    html = (STATIQUE / "accueil.html").read_text(encoding="utf-8")
    html = html.replace("/api/persona/avatar", "static/icone-192.png").replace('"/static/', '"static/')
    html = html.replace('"/gabarits.js"', '"gabarits.js"').replace('"/rappels.js"', '"rappels.js"')
    html = re.sub(r'href="/(discuter|studio|parent)?"', 'href="#"', html)
    html = html.replace(
        '<script src="static/commun.js">', '<script src="simulation.js"></script>\n  <script src="static/commun.js">'
    )
    (sortie / "index.html").write_text(html, encoding="utf-8")
    return sortie / "index.html"


def _chromium() -> str | None:
    for candidat in [os.environ.get("JULES_CHROMIUM"), "chromium", "chromium-browser", "google-chrome"]:
        if candidat and shutil.which(candidat):
            return shutil.which(candidat)
    installes = sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    return str(installes[-1]) if installes else None


def capturer(index: Path, notions: list[str], dossier: Path) -> list[Path]:
    """Une capture PNG par fiche (page ouverte sur la notion avec #notion)."""
    navigateur = _chromium()
    if not navigateur:
        sys.exit("Chromium introuvable : definir JULES_CHROMIUM, ou lancer sans --captures")
    dossier.mkdir(parents=True, exist_ok=True)
    captures = []
    for notion in notions:
        capture = dossier / f"{notion}.png"
        options = [
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            "--allow-file-access-from-files",
        ]
        options += ["--virtual-time-budget=4000", "--window-size=1280,3200", f"--screenshot={capture}"]
        commande = [navigateur, *options, f"{index.as_uri()}#{notion}"]  # navigateur local, arguments fixes
        subprocess.run(commande, check=True, capture_output=True, timeout=120)  # noqa: S603
        captures.append(capture)
    return captures


# --- ligne de commande ----------------------------------------------------------------------------


def main_visuel(args: list[str], racines: Racines) -> None:
    from jules.chantier import _ecrire, _options

    ids, options = _options(args, ("--par", "--sortie"))
    if not ids:
        sys.exit("Indiquer au moins une notion (identifiant du referentiel)")
    try:
        texte = paquet(racines, ids, par=options.get("--par", ""))
    except ValueError as err:
        sys.exit(str(err))
    _ecrire(texte, options.get("--sortie"))


def main_apercu(args: list[str], racines: Racines) -> None:
    from jules.chantier import _options

    captures = "--captures" in args
    positionnels, options = _options([a for a in args if a != "--captures"], ("--sortie",))
    if not positionnels:
        sys.exit("Indiquer le dossier d'une bibliotheque de fiches visuelles")
    dossier = Path(positionnels[0]).resolve()
    if not (dossier / "bibliotheque.yaml").is_file():
        sys.exit(f"Pas une bibliotheque (bibliotheque.yaml manquant) : {dossier}")
    racines = [*liste_racines(racines), dossier.parent]
    fiches, ecartees = controler(racines, dossier, positionnels[1:] or None)
    for motif in ecartees:
        print(f"ECARTEE {motif}")
    print(f"{len(fiches)} fiche(s) conforme(s), {len(ecartees)} ecartee(s)")
    sortie = Path(options.get("--sortie", "apercu-fiches-visuelles")).resolve()
    index = construire_apercu(racines, fiches, sortie)
    print(f"Apercu : {index}")
    if captures:
        for capture in capturer(index, list(fiches), sortie / "captures"):
            print(f"Capture : {capture}")
    if ecartees:
        sys.exit(1)
