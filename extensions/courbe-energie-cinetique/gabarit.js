// Jules - gabarit "courbe-energie-cinetique" : la courbe Ec = 1/2 x m x v^2 (une demi-parabole) avec un point
// mobile, et une voiture au-dessus dont la taille suit la masse. Curseurs : v (vitesse, m/s) et m (masse du
// vehicule, kg). Quand m n'est pas 1 000 kg, la courbe d'une voiture de 1 000 kg reste en gris pointille pour
// comparer : changer m etire la courbe (Ec proportionnelle a m), changer v fait monter le point de plus en
// plus vite (Ec proportionnelle a v^2).
// Valeurs ecrites : graduations des axes (v en m/s, Ec en kJ) et deux reperes de vitesse :
// 50 km/h = 13,9 m/s (vitesse maximale en agglomeration, Code de la route art. R413-3) et
// 130 km/h = 36,1 m/s (vitesse maximale sur autoroute, art. R413-2) ; conversion km/h -> m/s : diviser par 3,6.
// Ec n'est jamais ecrite : l'eleve la lit sur l'axe (revele: false).
// Source de la relation : programme de physique-chimie du cycle 4 (BO n° 31 du 30/07/2020, annexe 3, theme
// « L'energie et ses conversions » : relation liant l'energie cinetique, la masse et la vitesse, Ec = 1/2 m v^2).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["courbe-energie-cinetique"] = {
  dessiner(svg, valeurs) {
    const v = Math.min(40, Math.max(0, Number(valeurs.v ?? 10)));
    const m = Math.min(2000, Math.max(500, Number(valeurs.m ?? 1000)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const f = (x) => Math.round(x * 10) / 10;
    const ENCRE = "#14243B", GRIS = "#6B7686", BLEU = "#1F4E8C", ROUGE = "#C8102E";
    svg.setAttribute("viewBox", "0 0 340 306");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    // Repere : v de 0 a 40 m/s (x de 55 a 315), Ec de 0 a 1 600 kJ (y de 262 a 72).
    const X0 = 55, X1 = 315, Y0 = 262, Y1 = 72, EMAX = 1600;
    const X = (vv) => X0 + (vv / 40) * (X1 - X0);
    const Y = (kj) => Y0 - (kj / EMAX) * (Y0 - Y1);
    const ec = (mm, vv) => (0.5 * mm * vv * vv) / 1000; // en kJ

    // Graduations et quadrillage leger.
    for (const kj of [400, 800, 1200, 1600]) {
      el("line", { x1: X0, y1: Y(kj), x2: X1, y2: Y(kj), stroke: "#E3E8EF", "stroke-width": 2 });
    }
    for (const kj of [0, 400, 800, 1200, 1600]) {
      el("text", { x: X0 - 6, y: f(Y(kj) + 5), "font-size": 13, "text-anchor": "end", fill: GRIS }, String(kj));
    }
    for (const vv of [0, 10, 20, 30, 40]) {
      el("line", { x1: f(X(vv)), y1: Y0, x2: f(X(vv)), y2: Y0 + 6, stroke: GRIS, "stroke-width": 2 });
      el("text", { x: f(X(vv)), y: Y0 + 21, "font-size": 13, "text-anchor": "middle", fill: GRIS }, String(vv));
    }
    // Reperes de vitesse en km/h (lignes grises fines, etiquette en haut du repere).
    for (const [vv, nom] of [[50 / 3.6, "50 km/h"], [130 / 3.6, "130 km/h"]]) {
      el("line", { x1: f(X(vv)), y1: Y1, x2: f(X(vv)), y2: Y0, stroke: "#D5DAE1", "stroke-width": 2, "stroke-dasharray": "4 4" });
      el("text", { x: f(X(vv)), y: Y1 - 14, "font-size": 13, "text-anchor": "middle", fill: GRIS }, nom);
    }
    el("line", { x1: X0, y1: Y0, x2: X1 + 4, y2: Y0, stroke: ENCRE, "stroke-width": 2 });
    el("line", { x1: X0, y1: Y0, x2: X0, y2: Y1 - 4, stroke: ENCRE, "stroke-width": 2 });
    el("text", { x: X1, y: Y0 + 36, "font-size": 13, "text-anchor": "end", fill: ENCRE }, "vitesse v (m/s)");
    el("text", { x: 8, y: 56, "font-size": 13, fill: ENCRE }, "Ec (kJ)");

    // Courbes : reference 1 000 kg (gris) si m differe, puis la courbe de la masse choisie (bleu), coupee en haut.
    const courbe = (mm) => {
      const pts = [];
      for (let i = 0; i <= 80; i++) {
        const vv = i / 2;
        if (ec(mm, vv) > EMAX) {
          pts.push(`${f(X(Math.sqrt((2000 * EMAX) / mm)))},${Y1}`);
          break;
        }
        pts.push(`${f(X(vv))},${f(Y(ec(mm, vv)))}`);
      }
      return pts.join(" ");
    };
    if (m !== 1000) {
      el("polyline", { points: courbe(1000), fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "6 5" });
    }
    el("polyline", { points: courbe(m), fill: "none", stroke: BLEU, "stroke-width": 3 });

    // Point mobile et ses reperes vers les axes.
    const px = X(v), py = Y(ec(m, v));
    el("line", { x1: f(px), y1: f(py), x2: f(px), y2: Y0, stroke: ROUGE, "stroke-width": 2, "stroke-dasharray": "3 4" });
    el("line", { x1: X0, y1: f(py), x2: f(px), y2: f(py), stroke: ROUGE, "stroke-width": 2, "stroke-dasharray": "3 4" });
    el("circle", { cx: f(px), cy: f(py), r: 6, fill: ROUGE });

    // La voiture, au-dessus du repere, a l'abscisse de la vitesse ; sa longueur suit la masse.
    const lg = 26 + ((m - 500) / 1500) * 18, xc = Math.min(330 - lg / 2, Math.max(8 + lg / 2, px));
    el("rect", { x: f(xc - lg / 2), y: 18, width: f(lg), height: 12, rx: 3, fill: BLEU });
    el("rect", { x: f(xc - lg / 4), y: 10, width: f(lg / 2), height: 10, rx: 3, fill: BLEU });
    el("circle", { cx: f(xc - lg / 3), cy: 32, r: 4, fill: ENCRE });
    el("circle", { cx: f(xc + lg / 3), cy: 32, r: 4, fill: ENCRE });
    return { v, m, ec: ec(m, v) };
  },
};
