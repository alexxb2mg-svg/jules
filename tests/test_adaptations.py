"""Adaptations, donnees de l'eleve (docs/spec/ADAPTATIONS.md : EX-004, EX-005, EX-008).

- EX-004 : les identifiants d'amenagement ne partent jamais chez le fournisseur du modele.
- EX-005 : le modele recoit seulement les consignes d'expression des amenagements actifs.
- EX-008 : aucun nom de trouble ni prenom d'eleve reel dans les donnees versionnees.
- EX-011 : le champ libre `remarques` porte un avertissement (exemple et profil genere).

Les termes sont lus dans docs/spec/termes-interdits.txt ; seul le cas temoin impose par la spec les
ecrit en clair (le code Python des tests est hors du champ d'EX-008).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from jules.composition import (
    TITRE_EXPRESSION,
    assembler,
    charger_profil,
    consignes_amenagements,
    corps_sans_entete,
    effacer_ids,
)
from jules.config import depuis_dict
from jules.installation import profil_yaml
from jules.llm.factice import Brique as Factice
from jules.moteur import Tuteur
from jules.persona import charger_persona
from tests.conftest import regle_par_defaut
from tests.termes_interdits import normaliser, termes_interdits, trouver_terme
from tests.test_hygiene import fichiers_publies

RACINE = Path(__file__).resolve().parents[1]
PROFIL_CUMUL = RACINE / "profils" / "test-cumul.yaml"
CONSIGNES = RACINE / "consignes"
DOSSIERS_EX008 = ("profils", "adaptations", "consignes", "tests")
EXTENSIONS_DONNEES = {".yaml", ".yml", ".json", ".md"}  # README.md exclus (documentation du perimetre)
# Jeux de donnees qui testent justement le filtrage de ces termes : liste nominative fixee par la spec.
EXEMPTIONS_EX008 = {"tests/cas/modele_eleve/lecons_filtre.yaml"}
# EX-008b (prenoms reels) porte sur tout le depot publie ; exemptions nommees seulement (aucune a ce jour).
EXEMPTIONS_EX008B: set[str] = set()
PROFILS_FICTIFS = {"exemple.yaml", "test-cumul.yaml"}
VARIABLE_SURCOUCHE = "JULES_SURCOUCHE"  # racine d'une installation privee (profils/<prenom>.yaml)


def ids_du_profil_cumul() -> list[str]:
    return list(yaml.safe_load(PROFIL_CUMUL.read_text(encoding="utf-8"))["amenagements"])


def corps_attendus() -> list[str]:
    """Corps des consignes des amenagements connus de test-cumul (ceux qui ont un fichier)."""
    fichiers = [CONSIGNES / "amenagements" / f"{i}.md" for i in ids_du_profil_cumul()]
    return [corps_sans_entete(f.read_text(encoding="utf-8")) for f in fichiers if f.is_file()]


@pytest.fixture
def tuteur_cumul(projet: Path, brut_config: dict):
    brut_config["profil"] = "test-cumul"
    t = Tuteur(depuis_dict(brut_config, projet), llm=Factice())
    t.llm.regle = regle_par_defaut  # type: ignore[attr-defined]
    yield t
    t.fermer()


# --- EX-004 / EX-005 : prompt ------------------------------------------------------
def test_le_profil_cumul_couvre_les_cas_utiles():
    ids = ids_du_profil_cumul()
    assert len(corps_attendus()) >= 2, "au moins deux amenagements connus cumules"
    assert any(not (CONSIGNES / "amenagements" / f"{i}.md").is_file() for i in ids), "un identifiant inconnu"
    brut = PROFIL_CUMUL.read_text(encoding="utf-8").split("amenagements:", 1)[1]
    assert all(brut.count(i) >= 2 for i in ids[:2]), "les identifiants reapparaissent dans des champs libres"


def test_amenagements_reconnus_et_retires_des_details():
    profil = charger_profil(PROFIL_CUMUL)
    assert profil.amenagements == ids_du_profil_cumul()
    assert "amenagements" not in profil.details
    texte = profil.texte()
    for ident in profil.amenagements:
        assert ident not in texte.lower()
    assert "astronomie" in texte and "exemples concrets" in texte  # le reste des champs libres est garde


def test_ex004_ex005_prompt_complet_avec_test_cumul(tuteur_cumul):
    conv = tuteur_cumul.stockage.creer_conversation("aide-devoirs")
    systeme = tuteur_cumul.systeme(conv)

    # EX-005 : un bloc de consignes, au titre neutre, avec chaque consigne attendue
    assert systeme.count(f"# {TITRE_EXPRESSION}") == 1
    bloc = systeme.split(f"# {TITRE_EXPRESSION}\n", 1)[1].split("\n# ", 1)[0]
    for corps in corps_attendus():
        assert corps in bloc
    # ordre : apres les consignes communes, avant la securite
    assert systeme.index("# Format") < systeme.index(f"# {TITRE_EXPRESSION}") < systeme.index("# Securite")

    # EX-004 : aucun identifiant (ni connu, ni inconnu), ni le nom du champ
    bas = systeme.lower()
    for ident in ids_du_profil_cumul():
        assert ident not in bas, ident
    assert "amenagement" not in normaliser(systeme)
    # EX-005 : aucun nom de trouble
    assert trouver_terme(systeme, termes_interdits()) is None


def test_sans_amenagement_pas_de_bloc(tuteur):
    systeme = tuteur.systeme(tuteur.stockage.creer_conversation("aide-devoirs"))
    assert f"# {TITRE_EXPRESSION}" not in systeme


def test_identifiant_inconnu_ou_malforme_ignore(tmp_path: Path, caplog):
    (tmp_path / "securite.md").write_text("SECRET", encoding="utf-8")
    profil = charger_profil(PROFIL_CUMUL)
    profil.amenagements = ["../securite", "inexistant", "Majuscule"]
    with caplog.at_level("WARNING", logger="jules"):
        assert consignes_amenagements(tmp_path, profil) == []
    assert len(caplog.records) == 3
    assert all("securite" not in r.getMessage() and "inexistant" not in r.getMessage() for r in caplog.records)


def test_ids_effaces_des_champs_libres_imbriques():
    ids = ["amenagement-test-a"]
    valeur = {
        "remarques": "Suivi AMENAGEMENT-TEST-A ; relecture amenagement-test-a-bis",
        "liste": ["amenagement-test-a", "maths"],
        "amenagement_test_a": "cle retiree",
        "sous": {"x": ["a amenagement-test-a b"]},
    }
    assert effacer_ids(valeur, ids) == {
        "remarques": "Suivi ; relecture amenagement-test-a-bis",
        "liste": ["maths"],
        "sous": {"x": ["a b"]},
    }
    assert effacer_ids("rien", []) == "rien"


def test_assembler_directement(projet: Path):
    profil = charger_profil(PROFIL_CUMUL)
    persona = charger_persona(projet / "persona" / "jules", profil.variables(), profil.genre)
    systeme = assembler(persona, profil, projet / "consignes", [])
    assert f"# {TITRE_EXPRESSION}" in systeme
    assert not any(i in systeme.lower() for i in profil.amenagements)


# --- EX-008 : hygiene des donnees versionnees ---------------------------------------
def fichiers_ex008() -> list[Path]:
    """Fichiers de donnees que git publierait sous les dossiers d'EX-008, hors README et exemptions."""
    return [
        p
        for p in fichiers_publies()
        if (rel := p.relative_to(RACINE).as_posix()).startswith(tuple(f"{d}/" for d in DOSSIERS_EX008))
        and p.suffix in EXTENSIONS_DONNEES
        and p.name != "README.md"
        and rel not in EXEMPTIONS_EX008
    ]


def test_regles_de_recherche_cas_temoin():
    # cas temoin impose par la spec (EX-005) : casse, accents, radicaux, mots entiers
    termes = termes_interdits()
    assert termes, "docs/spec/termes-interdits.txt est vide"
    assert trouver_terme("Elle est Dyslexique.", termes) is not None
    assert trouver_terme("DYSPRAXIE", termes) is not None
    assert trouver_terme("dÉficit de l’attention", termes) is not None  # accents + apostrophe typographique
    assert trouver_terme("Des déficiences visuelles.", termes) is not None  # radical
    assert trouver_terme("Il est handicapé.", termes) is not None  # radical, accent final
    for apostrophe in ("\u2018", "\u02bc", "'"):  # les trois apostrophes de la regle, et la droite
        assert trouver_terme(f"deficit d{apostrophe}attention", termes) is not None, hex(ord(apostrophe))
    assert trouver_terme("deficit  de\tl'attention", termes) is not None  # suite d'espaces entre les mots
    sigles = [t for t in termes if t.mot_entier]
    assert sigles, "aucun terme « mot: » dans la liste"
    for sigle in sigles:
        assert trouver_terme(f"({sigle.texte.upper()})", termes) == sigle.texte
        assert trouver_terme(f"x{sigle.texte}x", [sigle]) is None  # mot entier : pas de sous-chaine
    # rien de faux sur un texte ordinaire : « surdite » et « sourd » sont en mot entier
    assert trouver_terme("Quelle absurdité ! Joue en sourdine, avec de l'attention.", termes) is None
    assert trouver_terme("absurdité", termes) is None
    assert trouver_terme("sourdine", termes) is None


def test_ex008_perimetre():
    fichiers = {p.relative_to(RACINE).as_posix() for p in fichiers_ex008()}
    assert "profils/test-cumul.yaml" in fichiers and "consignes/amenagements/amenagement-test-a.md" in fichiers
    assert not {f for f in fichiers if f.endswith((".py", "README.md"))}
    assert not fichiers & EXEMPTIONS_EX008
    for exemption in EXEMPTIONS_EX008:
        assert (RACINE / exemption).is_file(), f"exemption qui ne pointe plus sur rien : {exemption}"


def test_ex008_a_aucun_nom_de_trouble():
    termes = termes_interdits()
    fautifs = []
    for p in fichiers_ex008():
        texte = p.read_text(encoding="utf-8", errors="replace")
        if terme := trouver_terme(texte, termes):
            fautifs.append(f"{p.relative_to(RACINE).as_posix()}: {terme}")
    assert not fautifs, f"nom de trouble dans des donnees versionnees : {fautifs}"


def prenoms_reels() -> tuple[set[str], list[str]]:
    """Prenoms des profils prives : profils/ non publies de ce depot + surcouche designee par la variable."""
    sources = [RACINE / "profils"]
    if os.environ.get(VARIABLE_SURCOUCHE):
        sources.append(Path(os.environ[VARIABLE_SURCOUCHE]) / "profils")
    prenoms: set[str] = set()
    lus: list[str] = []
    fictifs = {
        str((yaml.safe_load((RACINE / "profils" / nom).read_text(encoding="utf-8")) or {}).get("prenom") or "")
        for nom in PROFILS_FICTIFS
    }  # un profil local de test peut reprendre un prenom fictif (ex. celui de l'exemple)
    for dossier in sources:
        for chemin in sorted(dossier.glob("*.yaml")) if dossier.is_dir() else []:
            if dossier == RACINE / "profils" and chemin.name in PROFILS_FICTIFS:
                continue
            prenom = str((yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}).get("prenom") or "").strip()
            if prenom and prenom not in fictifs:
                prenoms.add(prenom)
                lus.append(chemin.name)
    return prenoms, lus


def fichiers_ex008b() -> list[Path]:
    """Tout ce que git publierait (suivis + nouveaux non ignores), quels que soient dossier et extension.

    Le prenom d'un eleve reel n'a sa place nulle part dans le depot public : ni dans le code Python des
    tests, ni dans le contenu pedagogique (bibliotheque/), contrairement aux noms de troubles (partie a).
    Seules les exemptions nommees d'EXEMPTIONS_EX008B sont retirees.
    """
    try:
        sortie = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
            cwd=RACINE,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        chemins = [RACINE / ligne for ligne in sortie.splitlines() if ligne]
    except (OSError, subprocess.CalledProcessError):
        chemins = [p for p in RACINE.rglob("*") if ".git" not in p.parts]
    return [p for p in chemins if p.is_file() and p.relative_to(RACINE).as_posix() not in EXEMPTIONS_EX008B]


def test_ex008_b_perimetre():
    fichiers = {p.relative_to(RACINE).as_posix() for p in fichiers_ex008b()}
    # au-dela des quatre dossiers de la partie (a) : code des tests, contenu pedagogique, code, docs
    for attendu in (
        "tests/test_lecture_vocale_eleve.py",
        "bibliotheque/programme/CM1/anglais.yaml",
        "jules/web/static/eleve.js",
        "docs/spec/ADAPTATIONS.md",
        "profils/test-cumul.yaml",
    ):
        assert attendu in fichiers, attendu
    for exemption in EXEMPTIONS_EX008B:
        assert (RACINE / exemption).is_file(), f"exemption qui ne pointe plus sur rien : {exemption}"


def test_ex008_b_aucun_prenom_reel():
    prenoms, lus = prenoms_reels()
    if not prenoms:
        pytest.skip(
            "surcouche privee absente : aucun profil reel dans profils/ ni dans $"
            f"{VARIABLE_SURCOUCHE}/profils, les prenoms reels ne peuvent pas etre verifies"
        )
    motifs = {p: re.compile(rf"(?<![a-z0-9]){re.escape(normaliser(p))}(?![a-z0-9])") for p in prenoms}
    fautifs = [
        f"{f.relative_to(RACINE).as_posix()} ({len(lus)} profil(s) prive(s) lu(s))"
        for f in fichiers_ex008b()
        if any(m.search(normaliser(f.read_text(encoding="utf-8", errors="replace"))) for m in motifs.values())
    ]  # le prenom n'est pas recopie dans le message : il ne doit pas finir dans un journal de CI
    assert not fautifs, f"prenom d'un eleve reel dans : {fautifs}"


# --- EX-011 : avertissement sur le champ libre `remarques` ---------------------------
def avertissement_remarques(texte: str) -> str | None:
    """Commentaire d'avertissement porte par la ligne `remarques:` ou par le commentaire juste au-dessus."""
    lignes = texte.splitlines()
    index = next((i for i, ligne in enumerate(lignes) if ligne.startswith("remarques:")), None)
    assert index is not None, "champ `remarques` absent"
    candidats = [lignes[index].partition("#")[2]]
    if index > 0 and lignes[index - 1].lstrip().startswith("#"):
        candidats.append(lignes[index - 1])
    for candidat in candidats:
        n = normaliser(candidat)
        if "moteur" in n and "en ligne" in n and "aucune information medicale" in n:
            return candidat
    return None


@pytest.mark.parametrize("source", ["profils/exemple.yaml", "jules/installation.py"])
def test_ex011_avertissement_sur_remarques(source: str):
    if source == "profils/exemple.yaml":
        texte = (RACINE / source).read_text(encoding="utf-8")
    else:
        texte = profil_yaml("Sam", "garcon", "4e", "son oncle")
        assert yaml.safe_load(texte)["remarques"] == ""  # le champ reste transmis, le YAML reste lisible
    avertissement = avertissement_remarques(texte)
    assert avertissement, f"{source} : pas d'avertissement au-dessus ou sur la ligne `remarques`"
    assert trouver_terme(avertissement, termes_interdits()) is None  # sinon EX-008 echouerait
