// Jules - gabarit d'exemple fourni par l'extension "exemple-figure" (voir extensions/exemple-figure/
// extension.yaml et docs/EXTENSIONS.md). Un cercle dont le rayon depend d'un curseur "r".
// Meme contrat que les autres gabarits (extensions/<id>/gabarit.js, voir docs/EXTENSIONS.md) : rendu SVG
// pur, aucun eval(), aucun reseau.
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["exemple-cercle"] = {
  dessiner(svg, valeurs) {
    const r = Number(valeurs.r ?? 5);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    const U = 10; // px par unite
    svg.setAttribute("viewBox", "0 0 200 200");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    el("circle", { cx: 100, cy: 100, r: r * U, fill: "#EAF1FA", stroke: "#1F4E8C", "stroke-width": 2 });
    const texte = el("text", { x: 100, y: 100, "font-size": 14, "text-anchor": "middle", fill: "#14243B" });
    texte.textContent = `r = ${r}`;
    return { r };
  },
};
