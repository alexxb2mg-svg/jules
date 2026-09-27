"""EX-207 : le tiroir (sous 900 px) reste ouvert pendant tout le parcours des petites pages.

Chaque clic sur un bouton de petite page (matiere, chapitre, retour) remplace le contenu de la barre : le bouton
clique est retire du DOM avant que le clic n'atteigne `document`. Le tiroir ne doit se fermer que sur Echap,
clic en dehors, entree feuille (lien) ou re-clic sur le bouton ☰.
"""

from __future__ import annotations

from typing import Any

import pytest

from jules.web.app import creer_app
from tests.nav_scenario import banc_navigation
from tests.test_navigation import ATTENDRE_BARRE, _tuteur
from tests.test_navigation_n4 import LIRE
from tests.test_navigation_tiroir import TAILLES_TIROIR, _ferme, _ouvert


@pytest.fixture(scope="module")
def banc(tmp_path_factory):
    tuteur = _tuteur(tmp_path_factory, None)
    try:
        with banc_navigation(creer_app(tuteur), tmp_path_factory.mktemp("chromium-tiroir-parcours")) as b:
            yield b
    finally:
        tuteur.fermer()


PARCOURS = r"""
  const barre = S.el("#barre-jules");
  const bouton = S.el("#barre-jules-bouton");
  barre.style.transition = "none";
  const etat = (nom) => {
    const r = barre.getBoundingClientRect();
    return {
      nom, etape: lirePage().etape, expanded: bouton.getAttribute("aria-expanded"),
      classe: barre.classList.contains("ouverte"), visibilite: getComputedStyle(barre).visibility,
      gauche: r.left, droite: r.right, focusDansTiroir: barre.contains(document.activeElement),
      focusBouton: document.activeElement === bouton,
    };
  };
  // Ordre reel d'un clic souris : le navigateur execute les microtaches entre deux ecouteurs, donc afficher()
  // a deja remplace la petite page quand le clic arrive a `document`. element.click() (S.clic) ne le fait pas :
  // on reproduit ce detachement a la main, dans la barre, avant que l'evenement ne remonte a `document`.
  const detaches = [];
  barre.addEventListener("click", (ev) => {
    const b = ev.target.closest(".barre-matiere, .barre-chapitre, .barre-retour");
    if (b && b.isConnected) { b.remove(); detaches.push(b.className); }
  });
  const etapes = [];
  S.clic(bouton);
  await S.pause(50);
  etapes.push(etat("ouverture"));

  rubrique("fiches").click();
  await attendreEtape(3);                       // matiere retenue : chapitres de la matiere
  etapes.push(etat("rubrique"));
  const chapitres = [...barre.querySelectorAll("[data-chapitre]")];
  chapitres[chapitres.length - 1].click();
  await attendreEtape(4);
  etapes.push(etat("chapitre"));
  retour().click();
  await attendreEtape(3);
  etapes.push(etat("retour chapitres"));
  retour().click();
  await attendreEtape(2);
  etapes.push(etat("retour matieres"));
  matiere("mathematiques").click();
  await attendreEtape(3);
  etapes.push(etat("matiere"));
  retour().click();
  await attendreEtape(2);
  retour().click();
  await attendreEtape(1);
  etapes.push(etat("retour menu"));

  // Une fois le parcours fini, les fermetures prevues fonctionnent toujours.
  S.echap();
  await S.pause(50);
  return { etapes, apresEchap: etat("echap"), detaches: detaches.length, erreurs: S.erreurs() };
"""


def _parcours(banc, taille: tuple[int, int]) -> dict[str, Any]:
    avant = "localStorage.clear(); localStorage.setItem('jules.matiere', 'mathematiques');"
    return banc.jouer("/cours", ATTENDRE_BARRE + LIRE + PARCOURS, taille=taille, budget_ms=10000, avant=avant)


@pytest.mark.parametrize("taille", TAILLES_TIROIR, ids=lambda t: f"{t[0]}x{t[1]}")
def test_ex207_tiroir_reste_ouvert_pendant_le_parcours_des_petites_pages(banc, taille):
    r = _parcours(banc, taille)
    noms = [e["nom"] for e in r["etapes"]]
    assert noms == [
        "ouverture",
        "rubrique",
        "chapitre",
        "retour chapitres",
        "retour matieres",
        "matiere",
        "retour menu",
    ]
    assert [e["etape"] for e in r["etapes"]] == [1, 3, 4, 3, 2, 3, 1]
    assert r["detaches"] == 6  # chapitre, matiere et les 4 retours : chaque clic a bien ete detache
    for e in r["etapes"]:
        _ouvert(e, taille[0])
    for e in r["etapes"][1:]:
        assert e["focusDansTiroir"] is True, e  # le focus suit la petite page, il ne sort pas du tiroir
    _ferme(r["apresEchap"])
    assert r["apresEchap"]["focusBouton"] is True
    assert r["erreurs"] == []
