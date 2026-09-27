"""EX-215 (docs/spec/NAVIGATION.md) : couleurs par matiere, contrastes mesures, l'accent jamais en texte.

La table de reference est `docs/spec/matieres-couleurs.json` (tenue par SPEC, jamais modifiee par DEV).
`jules/web/static/matieres-couleurs.css` en est la recopie : variables seulement, un seul bloc `:root`.
Contrastes : formule WCAG 2.x (luminance relative), seuils 4,5:1 pour le texte (1.4.3) et 3:1 pour un
element d'interface (1.4.11).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from jules.bibliotheques import charger_catalogue

RACINE = Path(__file__).resolve().parents[1]
STATIQUE = RACINE / "jules" / "web" / "static"
TABLE = RACINE / "docs" / "spec" / "matieres-couleurs.json"
CSS = STATIQUE / "matieres-couleurs.css"
BLANC = "#FFFFFF"
HEXA = re.compile(r"#[0-9A-Fa-f]{6}")

# Une declaration `color` (ou `-webkit-text-fill-color`) dont la valeur cite `--matiere-...-accent`,
# en CSS (`color: var(...)`) comme en JS (`.color = "..."`, `setProperty("color", "...")`).
# `background-color`, `border-color`, `outline-color`... ne sont pas des couleurs de texte : exclus par
# le `(?<![\w-])` devant `color`. La valeur s'arrete a `;`, `{`, `}` (fin de declaration ou de regle CSS),
# sauf a l'interieur d'une interpolation JS `${...}`. Elle peut s'etendre sur plusieurs lignes : la recherche
# porte sur le fichier entier, commentaires retires (voir `_accents_en_texte`).
_VALEUR = r"(?:\$\{[^{}]*\}|[^;{}])*?"
ACCENT_EN_TEXTE = re.compile(
    r"(?:(?<![\w-])-webkit-text-fill-color|(?<![\w-])color)[\"']?\s*[:=,]\s*"
    + _VALEUR
    + "--matiere-"
    + _VALEUR
    + "-accent",
    re.IGNORECASE,
)


# Commentaires `/* ... */` (CSS et JS) et `// ...` (JS seulement ; pas apres `:` pour epargner `https://`).
_COMMENTAIRE_BLOC = re.compile(r"/\*.*?\*/", re.DOTALL)
_COMMENTAIRE_LIGNE = re.compile(r"(?<![:\\])//[^\n]*")


def _sans_commentaires(texte: str, js: bool) -> str:
    """Retire les commentaires en gardant leurs sauts de ligne, pour des numeros de ligne exacts."""
    propre = _COMMENTAIRE_BLOC.sub(lambda m: "\n" * m.group(0).count("\n") or " ", texte)
    return _COMMENTAIRE_LIGNE.sub("", propre) if js else propre


def _accents_en_texte(texte: str, js: bool = False) -> list[tuple[int, str]]:
    """(ligne de debut, extrait) de chaque accent employe en couleur de texte, recherche sur le texte entier."""
    propre = _sans_commentaires(texte, js)
    return [
        (propre.count("\n", 0, m.start()) + 1, " ".join(m.group(0).split())) for m in ACCENT_EN_TEXTE.finditer(propre)
    ]


def _table() -> dict:
    return json.loads(TABLE.read_text(encoding="utf-8"))


def _luminance(hexa: str) -> float:
    def canal(c: int) -> float:
        v = c / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hexa[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(a: str, b: str) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _p_principale() -> str:
    trouve = re.search(r"--p-principale\s*:\s*(#[0-9A-Fa-f]{6})", (STATIQUE / "style.css").read_text(encoding="utf-8"))
    assert trouve, "--p-principale introuvable dans style.css"
    return trouve.group(1)


def _variables_css(texte: str) -> dict[str, str]:
    return dict(re.findall(r"(--matiere-[\w-]+)\s*:\s*([^;]+);", texte))


def _variables_attendues(table: dict) -> dict[str, str]:
    attendues = {f"--matiere-{m}-{k}": c[k] for m, c in table["matieres"].items() for k in ("fond", "texte", "accent")}
    attendues["--matiere-chevron"] = table["chevron"]
    return attendues


# --- formule --------------------------------------------------------------------------------------


def test_formule_de_contraste_sur_des_valeurs_connues():
    assert contraste("#000000", BLANC) == pytest.approx(21.0)
    assert contraste(BLANC, BLANC) == pytest.approx(1.0)
    assert contraste("#777777", BLANC) == pytest.approx(4.48, abs=0.01)
    # valeurs citees par la spec (EX-215)
    assert contraste("#7A7562", "#FBF8F1") == pytest.approx(4.35, abs=0.01)
    assert contraste(BLANC, "#C2521F") == pytest.approx(4.65, abs=0.01)


# --- table de reference ---------------------------------------------------------------------------


def test_table_bien_formee():
    table = _table()
    assert HEXA.fullmatch(table["fond_barre"]) and HEXA.fullmatch(table["chevron"])
    assert "_neutre" in table["matieres"]
    for m, c in table["matieres"].items():
        assert set(c) == {"fond", "texte", "accent"}, m
        assert all(HEXA.fullmatch(v) for v in c.values()), m


def test_chaque_matiere_du_catalogue_3e_a_ses_couleurs():
    matieres = {n.matiere for n in charger_catalogue(RACINE / "bibliotheque", ["programme"], "3e").notions.values()}
    assert len(matieres) >= 12
    manquantes = sorted(matieres - set(_table()["matieres"]))
    assert not manquantes, f"matieres du catalogue 3e sans couleurs : {manquantes}"


def test_seuils_de_contraste_ex215():
    table = _table()
    papier = table["fond_barre"]
    fautes = []
    for m, c in table["matieres"].items():  # _neutre compris
        mesures = [
            ("texte/fond", contraste(c["texte"], c["fond"]), 4.5),
            ("texte/papier", contraste(c["texte"], papier), 4.5),
            ("blanc/accent", contraste(BLANC, c["accent"]), 4.5),
            ("accent/fond", contraste(c["accent"], c["fond"]), 3.0),
            ("accent/papier", contraste(c["accent"], papier), 3.0),
        ]
        fautes += [f"{m} {nom} {v:.2f} < {seuil}" for nom, v, seuil in mesures if v < seuil]
    assert not fautes, "\n".join(fautes)


def test_chevron_sur_chacun_de_ses_fonds():
    """Chevron `chevron` sur le papier ; `texte` de la matiere sur sa tuile ; blanc sur l'accent et sur
    --p-principale (entree active ou selectionnee). Seuil 3:1 partout (element d'interface)."""
    table = _table()
    principale = _p_principale()
    mesures = [("chevron/papier", contraste(table["chevron"], table["fond_barre"]))]
    mesures.append(("blanc/--p-principale", contraste(BLANC, principale)))
    for m, c in table["matieres"].items():
        mesures.append((f"{m} texte/fond", contraste(c["texte"], c["fond"])))
        mesures.append((f"{m} blanc/accent", contraste(BLANC, c["accent"])))
    fautes = [f"{nom} {v:.2f} < 3" for nom, v in mesures if v < 3.0]
    assert not fautes, "\n".join(fautes)


# --- fichier CSS ----------------------------------------------------------------------------------


def test_css_egal_a_la_table():
    obtenues = _variables_css(CSS.read_text(encoding="utf-8"))
    attendues = _variables_attendues(_table())
    assert obtenues == attendues


def test_css_une_teinte_modifiee_est_detectee():
    """Mutation : changer une seule teinte dans le CSS fait diverger la comparaison."""
    texte = CSS.read_text(encoding="utf-8")
    mute = texte.replace("--matiere-arts-plastiques-accent: #C2521F;", "--matiere-arts-plastiques-accent: #C2521E;")
    assert mute != texte
    assert _variables_css(mute) != _variables_attendues(_table())


def test_css_variables_seulement_dans_un_bloc_root():
    texte = re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.DOTALL).strip()
    bloc = re.fullmatch(r":root\s*\{([^{}]*)\}", texte)
    assert bloc, "un seul bloc :root, aucun autre selecteur"
    declarations = [d.strip() for d in bloc.group(1).split(";") if d.strip()]
    assert declarations
    for d in declarations:
        assert re.fullmatch(r"--matiere-[\w-]+\s*:\s*#[0-9A-Fa-f]{6}", d), f"declaration interdite : {d}"


# --- l'accent n'est jamais une couleur de texte ---------------------------------------------------


@pytest.mark.parametrize(
    "extrait",
    [
        ".x { color: var(--matiere-svt-accent); }",
        ".x{color:var(--matiere-_neutre-accent)}",
        ".x { -webkit-text-fill-color: var(--matiere-svt-accent); }",
        'el.style.color = "var(--matiere-" + id + "-accent)";',
        'el.style.setProperty("color", `var(--matiere-${id}-accent)`);',
        # declarations coupees sur plusieurs lignes
        ".zz-test {\n  color:\n    var(--matiere-svt-accent);\n}",
        ".x {\n  color\n  :\n  var(\n    --matiere-histoire-accent\n  );\n}",
        ".x { color: /* teinte */\n  var(--matiere-svt-accent); }",
        'el.style.color =\n  "var(--matiere-" + id +\n  "-accent)";',
        'el.style.setProperty(\n  "color",\n  `var(--matiere-${\n    id\n  }-accent)`\n);',
    ],
)
def test_temoin_negatif_accent_en_texte_detecte(extrait):
    assert _accents_en_texte(extrait, js=extrait.startswith("el."))


def test_faute_multiligne_signalee_a_sa_premiere_ligne():
    texte = (
        ".a { color: #FFF; }\n"
        "/* color: var(--matiere-svt-accent) */\n"
        ".zz {\n"
        "  color:\n"
        "    var(--matiere-svt-accent);\n"
        "}\n"
    )
    assert _accents_en_texte(texte) == [(4, "color: var(--matiere-svt-accent")]


@pytest.mark.parametrize(
    "extrait",
    [
        ".x { background: var(--matiere-svt-accent); color: #FFFFFF; }",
        ".x { background-color: var(--matiere-svt-accent); }",
        ".x { border-left: 4px solid var(--matiere-svt-accent); }",
        ".x { border-color: var(--matiere-svt-accent); }",
        ".x { color: var(--matiere-svt-texte); }",
        ".x{color:#FFF} .y{background:var(--matiere-svt-accent)}",
        # sur plusieurs lignes, ou accent cite seulement en commentaire
        ".x {\n  color: #FFFFFF;\n  background:\n    var(--matiere-svt-accent);\n}",
        ".x {\n  color: var(--matiere-svt-texte);\n}\n.y {\n  border-color:\n    var(--matiere-svt-accent);\n}",
        "/* ne jamais ecrire color: var(--matiere-svt-accent) */\n.x { color: #1F1F1F; }",
        '// el.style.color = "var(--matiere-svt-accent)"\nel.style.background = "var(--matiere-svt-accent)";',
    ],
)
def test_usages_permis_de_l_accent_non_signales(extrait):
    assert not _accents_en_texte(extrait, js=extrait.startswith(("el.", "//")))


def test_aucun_accent_en_couleur_de_texte_dans_les_statiques():
    fichiers = sorted([*STATIQUE.glob("*.css"), *STATIQUE.glob("*.js")])
    assert CSS in fichiers
    fautes = [
        f"{f.name}:{n}: {extrait}"
        for f in fichiers
        for n, extrait in _accents_en_texte(f.read_text(encoding="utf-8"), js=f.suffix == ".js")
    ]
    assert not fautes, "accent utilise comme couleur de texte (EX-215) :\n" + "\n".join(fautes)
