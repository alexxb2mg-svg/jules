// Jules - gabarit "droite-affine" : trace f(x) = ax + b dans un repere, curseurs a et b.
// Contrat : jules/fiches_visuelles.py (GABARITS_CONNUS). Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["droite-affine"] = {
  // dessine(svg, valeurs) : (re)dessine la figure dans le <svg> pour ces valeurs de curseurs.
  dessiner(svg, valeurs) {
    const a = Number(valeurs.a ?? 1);
    const b = Number(valeurs.b ?? 0);
    const NS = "http://www.w3.org/2000/svg";
    const U = 30, O = 170; // 1 unite = 30 px, origine au centre d'un cadre 340x340
    const X = (x) => O + x * U;
    const Y = (y) => O - y * U;
    const el = (nom, attrs) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    const fmt = (n) => String(n).replace(".", "-").replace("-", "−").replace("−", n < 0 ? "−" : "");
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    for (let i = -5; i <= 5; i++) {
      el("line", { x1: X(i), y1: Y(-5.5), x2: X(i), y2: Y(5.5), stroke: "#EEF1F5" });
      el("line", { x1: X(-5.5), y1: Y(i), x2: X(5.5), y2: Y(i), stroke: "#EEF1F5" });
    }
    el("line", { x1: X(-5.5), y1: O, x2: X(5.5), y2: O, stroke: "#6B7686", "stroke-width": 1.5 });
    el("line", { x1: O, y1: Y(-5.5), x2: O, y2: Y(5.5), stroke: "#6B7686", "stroke-width": 1.5 });
    el("line", { x1: X(-6), y1: Y(a * -6 + b), x2: X(6), y2: Y(a * 6 + b), stroke: "#1F4E8C", "stroke-width": 3 });
    if (a !== 0) {
      el("path", {
        d: `M${X(0)},${Y(b)} L${X(1)},${Y(b)} L${X(1)},${Y(b + a)}`,
        fill: "none", stroke: "#D9480F", "stroke-width": 2, "stroke-dasharray": "5 4",
      });
    }
    const point = el("circle", { cx: X(0), cy: Y(b), r: 6, fill: "#2B8A3E" });
    point.setAttribute("data-adresse", "graphe/point-b");
    return { a, b };
  },
};
