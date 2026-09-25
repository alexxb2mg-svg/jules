// Jules - gabarit "equation-solutions" : x² = a sur une droite graduee, 0/1/2 solutions selon a.
// Contrat : jules/fiches_visuelles.py (GABARITS_CONNUS). Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["equation-solutions"] = {
  dessiner(svg, valeurs) {
    const a = Number(valeurs.a ?? 0);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    const U = 16, O = 170; // 1 unite = 16 px, origine au centre d'une droite -9..9
    const X = (x) => O + x * U;
    svg.setAttribute("viewBox", "0 0 340 80");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    el("line", { x1: X(-10), y1: 40, x2: X(10), y2: 40, stroke: "#6B7686", "stroke-width": 1.5 });
    for (let i = -9; i <= 9; i += 3) {
      el("line", { x1: X(i), y1: 34, x2: X(i), y2: 46, stroke: "#6B7686" });
      const texte = el("text", { x: X(i), y: 62, "font-size": 12, "text-anchor": "middle", fill: "#6B7686" });
      texte.textContent = i;
    }
    if (a > 0) {
      const racine = Math.sqrt(a);
      for (const x of [racine, -racine]) el("circle", { cx: X(x), cy: 40, r: 7, fill: "#1F4E8C" });
    } else if (a === 0) {
      el("circle", { cx: X(0), cy: 40, r: 7, fill: "#1F4E8C" });
    }
    // a < 0 : aucun point trace, la droite reste vide.
    return { a };
  },
};
