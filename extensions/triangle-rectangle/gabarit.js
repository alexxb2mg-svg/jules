// Jules - gabarit "triangle-rectangle" : triangle rectangle en C, cotes ac et bc reglables.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["triangle-rectangle"] = {
  dessiner(svg, valeurs) {
    const ac = Number(valeurs.ac ?? 6);
    const bc = Number(valeurs.bc ?? 8);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    const U = 16; // px par unite, avec cotes plafonnes a 12
    const C = { x: 60, y: 300 };
    const A = { x: 60, y: 300 - ac * U };
    const B = { x: 60 + bc * U, y: 300 };
    const hyp = Math.sqrt(ac * ac + bc * bc);
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    el("polygon", { points: `${A.x},${A.y} ${B.x},${B.y} ${C.x},${C.y}`, fill: "#EAF1FA", stroke: "#1F4E8C", "stroke-width": 2 });
    el("rect", { x: C.x, y: C.y - 14, width: 14, height: 14, fill: "none", stroke: "#6B7686" });
    for (const [pt, nom, dx, dy] of [[A, "A", -14, 4], [B, "B", 8, 4], [C, "C", -14, 18]]) {
      const texte = el("text", { x: pt.x + dx, y: pt.y + dy, "font-size": 14, fill: "#14243B" });
      texte.textContent = nom;
    }
    const milieuAB = { x: (A.x + B.x) / 2, y: (A.y + B.y) / 2 };
    const legende = el("text", { x: milieuAB.x + 10, y: milieuAB.y - 10, "font-size": 13, fill: "#D9480F" });
    legende.textContent = `AB ≈ ${hyp.toFixed(1)}`;
    return { ac, bc, hyp };
  },
};
