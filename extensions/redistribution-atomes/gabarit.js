// Jules - gabarit "redistribution-atomes" : combustion du methane, CH4 + 2 O2 -> CO2 + 2 H2O, a l'echelle
// des atomes. Curseur x = avancement (0 = reactifs, 1 = produits), en trois temps :
//   0 a 1/3 : les liaisons des reactifs s'effacent et les H s'ecartent ;
//   1/3 a 2/3 : les atomes changent de place (les H passent au-dessus ou au-dessous, les O glissent) ;
//   2/3 a 1 : les liaisons des produits apparaissent.
// Curseur n = nombre de molecules de methane (1 a 3), donc 2n molecules de dioxygene.
// Le compte des atomes (C : n, H : 4n, O : 4n) ne change jamais.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

// Un « paquet » = 1 CH4 + 2 O2 = 1 CO2 + 2 H2O, dispose « O2  CH4  O2 » puis « H2O  CO2  H2O ».
// Chaque atome : element et 4 positions [abscisse, ecart vertical au centre de la ligne], une par temps
// (debut, fin du 1er temps, fin du 2e, fin). Positions choisies pour qu'aucun atome n'en traverse un autre.
const _REDISTRIBUTION_PAQUET = [
  ["C", [[170, 0], [170, 0], [170, 0], [170, 0]]],
  ["H", [[146, 0], [146, -28], [30, -28], [30, 12]]],
  ["H", [[170, -24], [170, -28], [74, -28], [74, 12]]],
  ["H", [[170, 24], [170, 28], [266, 28], [266, 12]]],
  ["H", [[194, 0], [194, 28], [310, 28], [310, 12]]],
  ["O", [[40, 0], [40, 0], [52, -5], [52, -5]]],
  ["O", [[64, 0], [64, 0], [144, 0], [144, 0]]],
  ["O", [[276, 0], [276, 0], [196, 0], [196, 0]]],
  ["O", [[300, 0], [300, 0], [288, -5], [288, -5]]],
];
const _REDISTRIBUTION_LIAISONS_AVANT = [[0, 1], [0, 2], [0, 3], [0, 4], [5, 6], [7, 8]];
const _REDISTRIBUTION_LIAISONS_APRES = [[0, 6], [0, 7], [5, 1], [5, 2], [8, 3], [8, 4]];

// Position d'un atome a l'avancement x : interpolation lineaire dans le temps en cours.
function _redistributionPosition(points, x) {
  const k = Math.min(2, Math.floor(x * 3));
  const f = Math.max(0, Math.min(1, x * 3 - k));
  const [a, b] = [points[k], points[k + 1]];
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
}

window.GABARITS["redistribution-atomes"] = {
  dessiner(svg, valeurs) {
    const x = Math.max(0, Math.min(1, Number(valeurs.x ?? 0)));
    const n = Math.max(1, Math.min(3, Math.round(Number(valeurs.n ?? 1))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", GRIS = "#6B7686", ROUGE = "#C8102E";
    const STYLE = {
      C: { r: 12, fond: ENCRE, bord: ENCRE, lettre: "#FFFFFF" },
      O: { r: 12, fond: ROUGE, bord: ROUGE, lettre: "#FFFFFF" },
      H: { r: 9, fond: "#FFFFFF", bord: GRIS, lettre: ENCRE },
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // --- equation, coefficients multiplies par n ; le cote « actuel » est en gras.
    const coef = (k, formule) => (k === 1 ? formule : `${k} ${formule}`);
    const avant = `${coef(n, "CH₄")} + ${coef(2 * n, "O₂")}`;
    const apres = `${coef(n, "CO₂")} + ${coef(2 * n, "H₂O")}`;
    const actif = (oui) => (oui ? { fill: ENCRE, "font-weight": "bold" } : { fill: GRIS });
    el("text", { x: 150, y: 28, "font-size": 16, "text-anchor": "end", ...actif(x < 0.5) }, avant);
    el("text", { x: 170, y: 28, "font-size": 16, "text-anchor": "middle", fill: ENCRE }, "→");
    el("text", { x: 190, y: 28, "font-size": 16, "text-anchor": "start", ...actif(x > 0.5) }, apres);
    el("text", { x: 95, y: 46, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "réactifs");
    el("text", { x: 245, y: 46, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "produits");

    // --- atomes et liaisons (celles des reactifs s'effacent, celles des produits apparaissent).
    const opAvant = Math.max(0, Math.min(1, 1 - 3 * x));
    const opApres = Math.max(0, Math.min(1, 3 * x - 2));
    for (let ligne = 0; ligne < n; ligne++) {
      const cy = 173 - (n - 1) * 38 + ligne * 76;
      const pos = _REDISTRIBUTION_PAQUET.map(([, points]) => {
        const [px, py] = _redistributionPosition(points, x);
        return [px, cy + py];
      });
      for (const [liaisons, op] of [[_REDISTRIBUTION_LIAISONS_AVANT, opAvant], [_REDISTRIBUTION_LIAISONS_APRES, opApres]]) {
        if (op <= 0) continue;
        for (const [i, j] of liaisons) {
          el("line", {
            x1: pos[i][0], y1: pos[i][1], x2: pos[j][0], y2: pos[j][1],
            stroke: GRIS, "stroke-width": 4, "stroke-linecap": "round", opacity: op,
          });
        }
      }
      _REDISTRIBUTION_PAQUET.forEach(([elem], i) => {
        const s = STYLE[elem];
        el("circle", { cx: pos[i][0], cy: pos[i][1], r: s.r, fill: s.fond, stroke: s.bord, "stroke-width": 2 });
        el("text", {
          x: pos[i][0], y: pos[i][1] + 4.5, "font-size": 13, "font-weight": "bold",
          "text-anchor": "middle", fill: s.lettre,
        }, elem);
      });
    }

    // --- compteur : le meme au debut, pendant et a la fin.
    el("line", { x1: 20, y1: 296, x2: 320, y2: 296, stroke: GRIS, "stroke-width": 2 });
    el("text", { x: 20, y: 324, "font-size": 14, fill: GRIS }, "atomes :");
    const compte = [["C", n, 110], ["H", 4 * n, 185], ["O", 4 * n, 260]];
    for (const [elem, nombre, cx] of compte) {
      const s = STYLE[elem];
      el("circle", { cx, cy: 319, r: s.r, fill: s.fond, stroke: s.bord, "stroke-width": 2 });
      el("text", { x: cx, y: 323.5, "font-size": 13, "font-weight": "bold", "text-anchor": "middle", fill: s.lettre }, elem);
      el("text", { x: cx + 18, y: 325, "font-size": 16, "font-weight": "bold", fill: ENCRE }, `× ${nombre}`);
    }
    return { x, n, C: n, H: 4 * n, O: 4 * n };
  },
};
