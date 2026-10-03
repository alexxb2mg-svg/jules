// Jules - gabarit "droite-graduee" : droite graduee dont chaque unite est coupee en d parts egales ; le point
// n/d est a n petites parts de 0 (a droite si n > 0, a gauche si n < 0). Le segment bleu de 0 au point montre
// les n parts comptees. Seules les graduations entieres sont ecrites ; le point porte l'ecriture n/d (les
// valeurs des curseurs), jamais son ecriture decimale.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["droite-graduee"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const x = Math.round(Number(v ?? defaut));
      return Math.min(max, Math.max(min, Number.isFinite(x) ? x : defaut));
    };
    const n = entier(valeurs.n, 3, -24, 24);
    const d = entier(valeurs.d, 4, 1, 12);
    const x = n / d;
    const moins = (v) => (v < 0 ? "\u2212" + String(-v) : String(v));
    // fenetre : de -3 a 3, elargie si le point en sort (0 et le point restent visibles)
    let bas = -3, haut = 3;
    if (Math.abs(x) > 3) {
      bas = Math.min(0, Math.floor(x)) - 1;
      haut = Math.max(0, Math.ceil(x)) + 1;
    }
    const X0 = 22, L = 296;
    const unite = L / (haut - bas);
    const X = (v) => X0 + (v - bas) * unite;
    const Y = 96;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const noeud = document.createElementNS(NS, nom);
      for (const cle in attrs) noeud.setAttribute(cle, attrs[cle]);
      if (texte !== undefined) noeud.textContent = texte;
      svg.appendChild(noeud);
      return noeud;
    };
    svg.setAttribute("viewBox", "0 0 340 150");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    el("text", { x: 170, y: 24, "font-size": 14, "text-anchor": "middle", fill: "#6B7686" },
      d === 1 ? "graduée de 1 en 1" : `chaque unité coupée en ${d} parts`);
    // la droite et ses deux fleches
    el("line", { x1: X0 - 12, y1: Y, x2: X0 + L + 12, y2: Y, stroke: "#14243B", "stroke-width": 2.5 });
    el("polygon", { points: `${X0 + L + 16},${Y} ${X0 + L + 6},${Y - 6} ${X0 + L + 6},${Y + 6}`, fill: "#14243B" });
    el("polygon", { points: `${X0 - 16},${Y} ${X0 - 6},${Y - 6} ${X0 - 6},${Y + 6}`, fill: "#14243B" });
    // petites parts (si elles restent assez espacees pour etre vues)
    if (d > 1 && unite / d >= 4) {
      for (let i = bas * d; i <= haut * d; i++) {
        if (i % d === 0) continue;
        el("line", { x1: X(i / d), y1: Y - 7, x2: X(i / d), y2: Y + 7, stroke: "#6B7686", "stroke-width": 2 });
      }
    }
    // segment de 0 au point : les n parts comptees depuis 0
    if (n !== 0) {
      el("line", { x1: X(0), y1: Y, x2: X(x), y2: Y, stroke: "#1F4E8C", "stroke-width": 7, "stroke-linecap": "round", "stroke-opacity": 0.85 });
    }
    // graduations entieres, ecrites (une sur deux si la place manque)
    const saut = unite >= 26 ? 1 : 2;
    for (let u = bas; u <= haut; u++) {
      el("line", { x1: X(u), y1: Y - 13, x2: X(u), y2: Y + 13, stroke: "#14243B", "stroke-width": u === 0 ? 3.5 : 2.5 });
      if (u % saut === 0 || u === 0) {
        el("text", {
          x: X(u), y: Y + 34, "font-size": 15, "text-anchor": "middle", fill: "#14243B",
          "font-weight": u === 0 ? "bold" : "normal",
        }, moins(u));
      }
    }
    // le point n/d et son ecriture fractionnaire
    el("circle", { cx: X(x), cy: Y, r: 7, fill: "#C8102E", stroke: "#FFFFFF", "stroke-width": 2 });
    const etiquette = d === 1 ? moins(n) : `${moins(n)}/${d}`;
    const ancre = X(x) < 50 ? "start" : X(x) > 290 ? "end" : "middle";
    el("text", { x: X(x), y: Y - 22, "font-size": 16, "font-weight": "bold", "text-anchor": ancre, fill: "#C8102E" }, etiquette);
    return { n, d, x, bas, haut };
  },
};
