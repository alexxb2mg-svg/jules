// Jules - gabarit "triangle-thales" : configuration de Thales, curseur t = AM/AB (0<t<1).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["triangle-thales"] = {
  dessiner(svg, valeurs) {
    const t = Number(valeurs.t ?? 0.5);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    // A en haut, B et C en bas : M et N sur [AB] et [AC], a la fraction t.
    const A = { x: 170, y: 20 }, B = { x: 30, y: 300 }, C = { x: 310, y: 300 };
    const M = { x: A.x + (B.x - A.x) * t, y: A.y + (B.y - A.y) * t };
    const N = { x: A.x + (C.x - A.x) * t, y: A.y + (C.y - A.y) * t };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    el("polygon", { points: `${A.x},${A.y} ${B.x},${B.y} ${C.x},${C.y}`, fill: "none", stroke: "#6B7686", "stroke-width": 2 });
    el("line", { x1: M.x, y1: M.y, x2: N.x, y2: N.y, stroke: "#1F4E8C", "stroke-width": 3 });
    for (const [pt, nom, dy] of [[A, "A", -8], [B, "B", 18], [C, "C", 18], [M, "M", -10], [N, "N", -10]]) {
      el("circle", { cx: pt.x, cy: pt.y, r: 4, fill: "#14243B" });
      const texte = el("text", { x: pt.x, y: pt.y + dy, "font-size": 14, "text-anchor": "middle", fill: "#14243B" });
      texte.textContent = nom;
    }
    return { t };
  },
};
