// Jules - gabarit "symetrie-axe" : une figure en L sur quadrillage, un axe rouge (vertical ou horizontal) qu'on
// deplace, et la figure symetrique (verte) de l'autre cote, avec des pointilles de chaque sommet a son image.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["symetrie-axe"] = {
  // dessiner(svg, valeurs) : axe = position de l'axe en carreaux depuis le bord (4 a 8), horizontal 0 = vertical,
  // 1 = horizontal, pointilles 1 = traits sommet-image visibles.
  dessiner(svg, valeurs) {
    const axe = Math.min(8, Math.max(4, Math.round(Number(valeurs.axe ?? 6))));
    const horizontal = Number(valeurs.horizontal ?? 0) === 1;
    const pointilles = Number(valeurs.pointilles ?? 1) === 1;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const N = 16, U = 20, O = 10;             // 16 x 16 carreaux de 20 px
    const px = (c) => O + c * U;

    // Le quadrillage.
    for (let i = 0; i <= N; i++) {
      el("line", { x1: px(i), y1: px(0), x2: px(i), y2: px(N), stroke: "#D5DCE6", "stroke-width": 1.5 });
      el("line", { x1: px(0), y1: px(i), x2: px(N), y2: px(i), stroke: "#D5DCE6", "stroke-width": 1.5 });
    }

    // La figure de depart, en L (colonne, ligne) ; avec l'axe horizontal, la meme figure couchee.
    const L = [[1, 5], [2, 5], [2, 10], [3, 10], [3, 11], [1, 11]];
    const figure = horizontal ? L.map(([c, l]) => [l, c]) : L;
    const image = figure.map(([c, l]) => (horizontal ? [c, 2 * axe - l] : [2 * axe - c, l]));
    const points = (pts) => pts.map(([c, l]) => `${px(c)},${px(l)}`).join(" ");

    // Les pointilles : chaque sommet relie a son image ; ils coupent l'axe a angle droit, en leur milieu.
    if (pointilles) {
      figure.forEach(([c, l], i) => {
        const [c2, l2] = image[i];
        el("line", {
          x1: px(c), y1: px(l), x2: px(c2), y2: px(l2),
          stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "5 4",
        });
      });
    }

    el("polygon", { points: points(figure), fill: "#1F4E8C", "fill-opacity": 0.22, stroke: "#1F4E8C", "stroke-width": 3, "stroke-linejoin": "round" });
    el("polygon", { points: points(image), fill: "#2E7D32", "fill-opacity": 0.22, stroke: "#2E7D32", "stroke-width": 3, "stroke-linejoin": "round" });

    // L'axe rouge, sur toute la feuille.
    if (horizontal) {
      el("line", { x1: px(0) - 4, y1: px(axe), x2: px(N) + 4, y2: px(axe), stroke: "#C8102E", "stroke-width": 4 });
      el("text", { x: px(N) - 4, y: px(axe) - 8, "font-size": 15, "font-weight": 700, fill: "#C8102E", "text-anchor": "end", "font-family": "sans-serif" }, "axe");
    } else {
      el("line", { x1: px(axe), y1: px(0) - 4, x2: px(axe), y2: px(N) + 4, stroke: "#C8102E", "stroke-width": 4 });
      el("text", { x: px(axe) + 6, y: px(N) - 8, "font-size": 15, "font-weight": 700, fill: "#C8102E", "font-family": "sans-serif" }, "axe");
    }

    // Un sommet repere et son image : A (bleu) et A' (vert).
    const [ca, la] = figure[4];
    const [cb, lb] = image[4];
    const lettre = (c, l, t, couleur, dx, dy) => {
      el("circle", { cx: px(c), cy: px(l), r: 4.5, fill: couleur });
      el("text", { x: px(c) + dx, y: px(l) + dy, "font-size": 16, "font-weight": 700, fill: couleur, "text-anchor": "middle", "font-family": "sans-serif" }, t);
    };
    if (horizontal) {
      lettre(ca, la, "A", "#1F4E8C", 14, -6);
      lettre(cb, lb, "A'", "#2E7D32", 16, 18);
    } else {
      lettre(ca, la, "A", "#1F4E8C", 0, 20);
      lettre(cb, lb, "A'", "#2E7D32", 0, 20);
    }
    return { axe, horizontal, pointilles };
  },
};
