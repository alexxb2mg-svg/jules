"""Navigation N6 : sur telephone, Jules ne masque pas la fiche (docs/spec/NAVIGATION.md, EX-213, audit NAV-05).

Sous 600 px de large, la bulle d'aide (`#jules-bulles`) et le bouton J (`#avatar-jules`) de `/` sont places hors de
la zone de lecture, en bas de l'ecran : la zone de la fiche s'arrete au-dessus d'eux, a tout instant (bulle
d'accueil, bulle longue d'un bloc, bulle effacee). Pas de fermeture temporisee.

Mesure (banc de tests/nav_scenario.py, spec section 6) a 390 x 844 : fiche « parallelisme-triangles-pythagore »
(elle a un bloc schema), defilement jusqu'au schema, puis intersection des `getBoundingClientRect()` de
`#jules-bulles` et `#avatar-jules` avec la partie visible de chaque bloc de `#fiche`. Partie visible = rectangle du
bloc coupe par la zone qui defile (`.fiche-zone`, qui masque ce qui deborde) et par la fenetre.
"""

from __future__ import annotations

from typing import Any

import pytest

from jules.web.app import creer_app
from tests.nav_scenario import banc_navigation
from tests.test_navigation import ATTENDRE_BARRE, _tuteur

NOTION = "parallelisme-triangles-pythagore"
TELEPHONE = (390, 844)

MESURER = r"""
  const zone = S.el(".fiche-zone");
  const coupe = (a, b) => {
    const gauche = Math.max(a.left, b.left), droite = Math.min(a.right, b.right);
    const haut = Math.max(a.top, b.top), bas = Math.min(a.bottom, b.bottom);
    return droite > gauche && bas > haut ? { left: gauche, right: droite, top: haut, bottom: bas } : null;
  };
  const fenetre = { left: 0, top: 0, right: innerWidth, bottom: innerHeight };
  // Blocs de #fiche : chaque enfant affiche de l'article, et chaque bloc de #fiche-blocs a la place du conteneur.
  const blocs = () => {
    const liste = [];
    for (const e of S.el("#fiche").children) {
      if (e.id === "fiche-blocs") liste.push(...e.querySelectorAll(":scope > .fiche-bloc"));
      else liste.push(e);
    }
    return liste.filter((e) => getComputedStyle(e).display !== "none" && e.getBoundingClientRect().height > 0);
  };
  const releve = (nom) => {
    const cadre = coupe(zone.getBoundingClientRect(), fenetre);
    const jules = { bulles: S.el("#jules-bulles").getBoundingClientRect(),
                    avatar: S.el("#avatar-jules").getBoundingClientRect() };
    const visibles = [];
    const chevauchements = [];
    for (const b of blocs()) {
      const visible = cadre && coupe(b.getBoundingClientRect(), cadre);
      if (!visible) continue;
      const nomBloc = b.id || b.dataset.adresse || b.className;
      visibles.push(nomBloc);
      for (const [qui, r] of Object.entries(jules)) {
        const c = coupe(visible, r);
        if (c) chevauchements.push({ bloc: nomBloc, qui, aire: (c.right - c.left) * (c.bottom - c.top) });
      }
    }
    const schema = S.el("#fiche-blocs .bloc-schema").closest(".fiche-bloc").getBoundingClientRect();
    return {
      nom, visibles, chevauchements,
      bulles: { haut: jules.bulles.top, bas: jules.bulles.bottom, hauteur: jules.bulles.height },
      avatar: { haut: jules.avatar.top, bas: jules.avatar.bottom, hauteur: jules.avatar.height },
      zone: { haut: cadre ? cadre.top : null, bas: cadre ? cadre.bottom : null, defile: zone.scrollTop },
      schema: { haut: schema.top, bas: schema.bottom },
      texteBulle: (S.el("#bulles").textContent || "").trim().slice(0, 60),
    };
  };
"""

SCENARIO = (
    ATTENDRE_BARRE
    + MESURER
    + r"""
  await S.attendre(() => !S.el("#fiche").classList.contains("cache") && S.el("#fiche-titre").textContent, 8000);
  await S.attendre(() => document.querySelector("#fiche-blocs .bloc-schema"), 4000);
  await S.attendre(() => document.querySelector("#bulles .bulle-jules"), 2000);
  const schema = S.el("#fiche-blocs .bloc-schema").closest(".fiche-bloc");
  const releves = [];
  // 1. defilement jusqu'au schema, bulle d'accueil affichee ; schema en bas de la zone (la ou Jules se trouve).
  schema.scrollIntoView({ block: "end" });
  await S.pause(50);
  releves.push(releve("schema en bas, bulle d'accueil"));
  schema.scrollIntoView({ block: "center" });
  await S.pause(50);
  releves.push(releve("schema au centre, bulle d'accueil"));
  // 2. clic sur le schema : la bulle de Jules du bloc remplace la premiere (texte plus long).
  S.clic(schema);
  await S.attendre(() => S.el("#bulles").textContent.indexOf("réciproque") >= 0, 2000);
  schema.scrollIntoView({ block: "end" });
  await S.pause(50);
  releves.push(releve("schema en bas, bulle du schema"));
  // 3. fin de la fiche : dernier bloc et sources.
  zone.scrollTop = zone.scrollHeight;
  await S.pause(50);
  releves.push(releve("fin de fiche, bulle du schema"));
  // 4. bulle fermee (clic) : il ne reste que le bouton J.
  S.clic("#bulles .bulle-jules");
  await S.attendre(() => !document.querySelector("#bulles .bulle-jules"), 3000);
  schema.scrollIntoView({ block: "end" });
  await S.pause(50);
  releves.push(releve("schema en bas, bulle fermee"));
  return { releves, erreurs: S.erreurs(), api: S.api() };
"""
)


@pytest.fixture(scope="module")
def banc(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory, None)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-n6")) as b:
            yield b
    finally:
        tuteur.fermer()


@pytest.fixture(scope="module")
def telephone(banc) -> dict[str, Any]:
    r = banc.jouer(f"/#{NOTION}", SCENARIO, taille=TELEPHONE, budget_ms=15000)
    for rel in r["releves"]:  # lisible avec `pytest -s` (a coller dans la revue)
        print("\nEX-213", rel["nom"], {k: rel[k] for k in ("bulles", "avatar", "zone", "schema", "chevauchements")})
    return r


def test_ex213_scenario_sans_erreur(telephone):
    assert telephone["erreurs"] == []


def test_ex213_le_schema_est_visible_a_chaque_releve(telephone):
    # Sans quoi l'absence de chevauchement ne prouverait rien sur le schema.
    for rel in telephone["releves"][:3] + telephone["releves"][4:]:
        assert any("schema" in v for v in rel["visibles"]), rel
        assert rel["schema"]["bas"] > rel["zone"]["haut"] and rel["schema"]["haut"] < rel["zone"]["bas"], rel


def test_ex213_la_bulle_et_le_bouton_j_sont_affiches(telephone):
    for rel in telephone["releves"]:
        assert rel["avatar"]["hauteur"] >= 44, rel  # zone de clic (EX-208)
        assert rel["bulles"]["bas"] <= TELEPHONE[1] + 0.5, rel  # dans l'ecran
    assert "réciproque" in telephone["releves"][2]["texteBulle"]


def test_ex213_aucun_chevauchement_avec_les_blocs_visibles(telephone):
    for rel in telephone["releves"]:
        assert rel["visibles"], rel
        assert rel["chevauchements"] == [], (rel["nom"], rel["chevauchements"])


def test_ex213_jules_en_bas_sous_la_zone_de_lecture(telephone):
    # « bas de l'ecran, la fiche garde une marge basse au moins egale a leur hauteur » : la zone de lecture
    # s'arrete au-dessus de la bulle et du bouton, quelle que soit la hauteur de la bulle.
    for rel in telephone["releves"]:
        assert rel["zone"]["bas"] <= rel["bulles"]["haut"] + 0.5, rel
        assert rel["zone"]["bas"] <= rel["avatar"]["haut"] + 0.5, rel
        assert TELEPHONE[1] - rel["zone"]["bas"] >= rel["avatar"]["hauteur"], rel


def test_ex213_ex210_aucun_appel_nouveau(telephone):
    # Correctif de mise en page seulement : aucun appel d'API propre a la carte.
    assert all(c.startswith("/api/") for c in telephone["api"])
    assert "/api/seance/bloc_consulte" in telephone["api"]  # le clic sur le schema, deja present avant la carte


def test_ex213_au_dela_de_600_px_rien_ne_change(banc):
    # A 768 px (tablette), la bulle reste flottante en bas a droite, comme avant la carte.
    r = banc.jouer(
        f"/#{NOTION}",
        ATTENDRE_BARRE
        + r"""
        await S.attendre(() => !S.el("#fiche").classList.contains("cache"), 8000);
        return S.style("#jules-bulles", ["position"]);
        """,
        taille=(768, 1024),
        budget_ms=10000,
    )
    assert r["position"] == "fixed"
