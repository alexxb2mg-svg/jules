// Jules - gabarit "schema-en-barres" : schema en barres des problemes (programme 2025 du cycle 3).
// fois = 1 : parties-tout, une barre faite de la partie a (bleu) et de la partie b (vert) sous une accolade
// « le tout » marquee « ? ». fois >= 2 : comparaison multiplicative, une barre a en haut et, en dessous, fois
// copies de la meme barre sous une accolade « ? ». La quantite cherchee n'est jamais calculee.
// Curseurs a (1 a 100), b (0 a 100), fois (1 a 5). Barres proportionnelles, la plus longue fait 300 px.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["schema-en-barres"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const n = Number(v ?? defaut);
      return Math.min(max, Math.max(min, Math.round(Number.isFinite(n) ? n : defaut)));
    };
    const a = entier(valeurs.a, 30, 1, 100);
    const b = entier(valeurs.b, 20, 0, 100);
    const fois = entier(valeurs.fois, 1, 1, 5);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const G = 20, LARGEUR = 300;
    svg.setAttribute("viewBox", "0 0 340 230");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Accolade horizontale de x1 a x2 ; pointe vers le haut (sens -1) ou vers le bas (sens 1) depuis y.
    const accolade = (x1, x2, y, sens) => {
      const m = (x1 + x2) / 2, h = 12 * sens;
      el("path", {
        d: `M${x1},${y} q0,${h} 12,${h} L${m - 12},${y + h} q12,0 12,${h} q0,${-h} 12,${-h} L${x2 - 12},${y + h} q12,0 12,${-h}`,
        fill: "none", stroke: GRIS, "stroke-width": 2.5, "stroke-linejoin": "round",
      });
      return { x: m, y: y + 2 * h };
    };
    // Morceau de barre avec sa valeur ecrite dedans (ou dessous s'il est trop etroit).
    const morceau = (x, y, w, h, couleur, valeur) => {
      el("rect", { x, y, width: Math.max(w, 2), height: h, fill: couleur, stroke: "#FFFFFF", "stroke-width": 2 });
      if (w >= 34) {
        el("text", { x: x + w / 2, y: y + h / 2 + 7, "font-size": 19, "font-weight": 700, "text-anchor": "middle", fill: "#FFFFFF" }, String(valeur));
      } else {
        const cx = Math.min(Math.max(x + w / 2, G + 8), G + LARGEUR - 8);
        el("line", { x1: x + w / 2, y1: y + h, x2: cx, y2: y + h + 10, stroke: couleur, "stroke-width": 2 });
        el("text", { x: cx, y: y + h + 27, "font-size": 17, "font-weight": 700, "text-anchor": "middle", fill: couleur }, String(valeur));
      }
    };

    if (fois === 1) {
      // Parties-tout : le tout (?) au-dessus, les deux parties dans la barre.
      const total = a + b, wa = (LARGEUR * a) / total, wb = LARGEUR - wa;
      el("text", { x: 170, y: 26, "font-size": 15, "text-anchor": "middle", fill: GRIS }, "le tout");
      const pointe = accolade(G, G + LARGEUR, 88, -1);
      el("text", { x: pointe.x, y: pointe.y - 6, "font-size": 26, "font-weight": 700, "text-anchor": "middle", fill: ROUGE }, "?");
      morceau(G, 96, wa, 48, BLEU, a);
      if (b > 0) morceau(G + wa, 96, wb, 48, VERT, b);
      // « partie » sous chaque morceau assez large ; plus bas si une valeur a du etre ecrite sous la barre
      const yPartie = wa < 34 || (b > 0 && wb < 34) ? 200 : 168;
      if (b === 0 || wa >= 70) el("text", { x: G + wa / 2, y: yPartie, "font-size": 14, "text-anchor": "middle", fill: BLEU }, "partie");
      if (b > 0 && wb >= 70) el("text", { x: G + wa + wb / 2, y: yPartie, "font-size": 14, "text-anchor": "middle", fill: VERT }, "partie");
    } else {
      // Comparaison : la barre du bas est faite de « fois » copies de la barre du haut.
      const w = LARGEUR / fois;
      morceau(G, 20, w, 44, BLEU, a);
      el("text", { x: G + LARGEUR, y: 92, "font-size": 16, "font-weight": 700, "text-anchor": "end", fill: ORANGE }, `${fois} fois plus`);
      el("line", { x1: G + w, y1: 64, x2: G + w, y2: 106, stroke: BLEU, "stroke-width": 2, "stroke-dasharray": "4 4" });
      el("line", { x1: G, y1: 64, x2: G, y2: 106, stroke: BLEU, "stroke-width": 2, "stroke-dasharray": "4 4" });
      for (let i = 0; i < fois; i++) morceau(G + i * w, 106, w, 44, BLEU, a);
      el("rect", { x: G, y: 106, width: LARGEUR, height: 44, fill: "none", stroke: ORANGE, "stroke-width": 2.5 });
      const pointe = accolade(G, G + LARGEUR, 158, 1);
      el("text", { x: pointe.x, y: pointe.y + 24, "font-size": 26, "font-weight": 700, "text-anchor": "middle", fill: ROUGE }, "?");
    }
    return { a, b, fois };
  },
};
