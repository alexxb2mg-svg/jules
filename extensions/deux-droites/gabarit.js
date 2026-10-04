// Jules - gabarit "deux-droites" : deux tarifs (ou deux fonctions affines) dans le meme repere.
// Tarif 1 : y = a1 x + b1 (bleu, trait plein) ; tarif 2 : y = a2 x + b2 (orange, tirets). x = la quantite (0 a 10),
// y = le prix (0 a 100, une droite qui sort par le haut est coupee au bord). Le point vert marque le croisement,
// avec des pointilles vers les deux axes : on y LIT la quantite pour laquelle les deux tarifs sont egaux (revele :
// c'est la resolution graphique demandee dans les exercices). A gauche et a droite du croisement, la droite du
// dessous est le tarif le moins cher.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["deux-droites"] = {
  // dessiner(svg, valeurs) : a1, a2 de 0 a 10 (prix par unite), b1, b2 de 0 a 40 (partie fixe).
  dessiner(svg, valeurs) {
    const nb = (v, d, mini, maxi) => {
      const x = Number(v ?? d);
      return Math.min(maxi, Math.max(mini, Number.isFinite(x) ? x : d));
    };
    const a1 = nb(valeurs.a1, 4, 0, 10), b1 = nb(valeurs.b1, 0, 0, 40);
    const a2 = nb(valeurs.a2, 2, 0, 10), b2 = nb(valeurs.b2, 10, 0, 40);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (x) => x.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00", VERT = "#2E7D32";
    const XMAX = 10, YMAX = 100;
    const GX = 50, GD = 316, GB = 282, GH = 52; // cadre du repere : gauche, droite, bas, haut
    const X = (x) => GX + (x / XMAX) * (GD - GX);
    const Y = (y) => GB - (y / YMAX) * (GB - GH);

    // Legende en haut.
    el("line", { x1: 20, y1: 22, x2: 50, y2: 22, stroke: BLEU, "stroke-width": 4 });
    el("text", { x: 56, y: 27, "font-size": 14, fill: ENCRE, "font-family": "sans-serif" }, "tarif 1");
    el("line", { x1: 130, y1: 22, x2: 160, y2: 22, stroke: ORANGE, "stroke-width": 4, "stroke-dasharray": "8 5" });
    el("text", { x: 166, y: 27, "font-size": 14, fill: ENCRE, "font-family": "sans-serif" }, "tarif 2");

    // Quadrillage, axes et graduations.
    for (let x = 1; x <= XMAX; x++) el("line", { x1: f(X(x)), y1: GB, x2: f(X(x)), y2: GH, stroke: "#E3E8EF", "stroke-width": 1 });
    for (let y = 10; y <= YMAX; y += 10) el("line", { x1: GX, y1: f(Y(y)), x2: GD, y2: f(Y(y)), stroke: "#E3E8EF", "stroke-width": 1 });
    el("line", { x1: GX, y1: GB, x2: GD, y2: GB, stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: GX, y1: GB, x2: GX, y2: GH, stroke: GRIS, "stroke-width": 2 });
    for (let x = 0; x <= XMAX; x += 2) {
      el("text", { x: f(X(x)), y: GB + 18, "font-size": 13, fill: ENCRE, "text-anchor": "middle", "font-family": "sans-serif" }, String(x));
    }
    for (let y = 0; y <= YMAX; y += 20) {
      el("text", { x: GX - 6, y: f(Y(y) + 5), "font-size": 13, fill: ENCRE, "text-anchor": "end", "font-family": "sans-serif" }, String(y));
    }
    el("text", { x: GD, y: GB + 40, "font-size": 13, fill: GRIS, "text-anchor": "end", "font-family": "sans-serif" }, "quantité →");
    el("text", { x: 8, y: GH - 10, "font-size": 13, fill: GRIS, "font-family": "sans-serif" }, "prix (€)");

    // Une droite y = a x + b, coupee au bord haut du repere.
    const droite = (a, b, couleur, tirets) => {
      if (b > YMAX) return;
      const xFin = a > 0 ? Math.min(XMAX, (YMAX - b) / a) : XMAX;
      el("line", { x1: f(X(0)), y1: f(Y(b)), x2: f(X(xFin)), y2: f(Y(a * xFin + b)), stroke: couleur, "stroke-width": 4, "stroke-linecap": "round", "stroke-dasharray": tirets ? "8 5" : "none" });
    };
    droite(a1, b1, BLEU, false);
    droite(a2, b2, ORANGE, true);

    // Le croisement, s'il est dans le repere.
    let croisement = null;
    if (a1 !== a2) {
      const xc = (b2 - b1) / (a1 - a2), yc = a1 * xc + b1;
      if (xc >= 0 && xc <= XMAX && yc <= YMAX) {
        croisement = { x: xc, y: yc };
        el("line", { x1: f(X(xc)), y1: f(Y(yc)), x2: f(X(xc)), y2: GB, stroke: VERT, "stroke-width": 2, "stroke-dasharray": "4 4" });
        el("line", { x1: f(X(xc)), y1: f(Y(yc)), x2: GX, y2: f(Y(yc)), stroke: VERT, "stroke-width": 2, "stroke-dasharray": "4 4" });
        el("circle", { cx: f(X(xc)), cy: f(Y(yc)), r: 7, fill: VERT, stroke: "#FFFFFF", "stroke-width": 2 });
      }
    }
    return { a1, b1, a2, b2, croisement };
  },
};
