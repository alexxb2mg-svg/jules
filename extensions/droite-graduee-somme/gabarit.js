// Jules - gabarit "droite-graduee-somme" : sur une droite graduee de -10 a 10, on part du nombre a (point bleu)
// et on fait un saut de longueur b (fleche orange) : vers la droite si b > 0, vers la gauche si b < 0. Le point
// d'arrivee (rouge) est a + b. La valeur de a + b n'est pas ecrite : l'eleve la lit sur la graduation.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["droite-graduee-somme"] = {
  dessiner(svg, valeurs) {
    const nombre = (v, defaut, min, max) => {
      const x = Math.round(Number(v ?? defaut) * 2) / 2; // au demi pres, comme les curseurs
      return Math.min(max, Math.max(min, Number.isFinite(x) ? x : defaut));
    };
    const a = nombre(valeurs.a, 2, -5, 5);
    const b = nombre(valeurs.b, -3, -5, 5);
    const arrivee = a + b;
    const ecrit = (v) => (v < 0 ? "\u2212" : "") + String(Math.abs(v)).replace(".", ",");
    const X0 = 20, L = 300, Y = 128;
    const X = (v) => X0 + (v + 10) * (L / 20);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const noeud = document.createElementNS(NS, nom);
      for (const cle in attrs) noeud.setAttribute(cle, attrs[cle]);
      if (texte !== undefined) noeud.textContent = texte;
      svg.appendChild(noeud);
      return noeud;
    };
    svg.setAttribute("viewBox", "0 0 340 190");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // legende : une couleur = une idee
    el("circle", { cx: 24, cy: 20, r: 6, fill: "#1F4E8C" });
    el("text", { x: 34, y: 25, "font-size": 14, fill: "#14243B" }, "départ a");
    el("line", { x1: 116, y1: 20, x2: 140, y2: 20, stroke: "#E07B00", "stroke-width": 4 });
    el("polygon", { points: "148,20 139,14 139,26", fill: "#E07B00" });
    el("text", { x: 154, y: 25, "font-size": 14, fill: "#14243B" }, "saut b");
    el("circle", { cx: 228, cy: 20, r: 6, fill: "#C8102E" });
    el("text", { x: 238, y: 25, "font-size": 14, fill: "#14243B" }, "arrivée");

    // la droite graduee de -10 a 10
    el("line", { x1: X0 - 10, y1: Y, x2: X0 + L + 10, y2: Y, stroke: "#14243B", "stroke-width": 2.5 });
    el("polygon", { points: `${X0 + L + 16},${Y} ${X0 + L + 6},${Y - 6} ${X0 + L + 6},${Y + 6}`, fill: "#14243B" });
    el("polygon", { points: `${X0 - 16},${Y} ${X0 - 6},${Y - 6} ${X0 - 6},${Y + 6}`, fill: "#14243B" });
    for (let u = -10; u <= 10; u++) {
      const pair = u % 2 === 0;
      el("line", {
        x1: X(u), y1: Y - (pair ? 10 : 6), x2: X(u), y2: Y + (pair ? 10 : 6),
        stroke: u === 0 ? "#14243B" : pair ? "#14243B" : "#6B7686", "stroke-width": u === 0 ? 3.5 : 2,
      });
      if (pair) {
        el("text", {
          x: X(u), y: Y + 30, "font-size": 14, "text-anchor": "middle", fill: "#14243B",
          "font-weight": u === 0 ? "bold" : "normal",
        }, ecrit(u));
      }
    }

    // le saut : fleche au-dessus de la droite, de a vers a + b
    const yFleche = 82;
    if (b !== 0) {
      const sens = b > 0 ? 1 : -1;
      el("line", { x1: X(a), y1: Y - 8, x2: X(a), y2: yFleche, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "3 3" });
      el("line", { x1: X(arrivee), y1: Y - 8, x2: X(arrivee), y2: yFleche, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "3 3" });
      el("line", { x1: X(a), y1: yFleche, x2: X(arrivee) - sens * 9, y2: yFleche, stroke: "#E07B00", "stroke-width": 4 });
      el("polygon", {
        points: `${X(arrivee)},${yFleche} ${X(arrivee) - sens * 11},${yFleche - 7} ${X(arrivee) - sens * 11},${yFleche + 7}`,
        fill: "#E07B00",
      });
      const milieu = Math.min(300, Math.max(40, (X(a) + X(arrivee)) / 2));
      el("text", { x: milieu, y: yFleche - 12, "font-size": 15, "font-weight": "bold", "text-anchor": "middle", fill: "#14243B" },
        b > 0 ? `+ ${ecrit(b)}` : `+ (${ecrit(b)})`);
    }
    el("circle", { cx: X(a), cy: Y, r: 7, fill: "#1F4E8C", stroke: "#FFFFFF", "stroke-width": 2 });
    if (b !== 0) {
      el("circle", { cx: X(arrivee), cy: Y, r: 7, fill: "#C8102E", stroke: "#FFFFFF", "stroke-width": 2 });
    } else {
      el("circle", { cx: X(a), cy: Y, r: 11, fill: "none", stroke: "#C8102E", "stroke-width": 3 });
    }
    return { a, b, arrivee };
  },
};
