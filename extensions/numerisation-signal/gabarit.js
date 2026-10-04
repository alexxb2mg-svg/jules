// Jules - gabarit "numerisation-signal" : un signal continu (celui d'un capteur ou d'un micro) et sa version
// numerisee en marches d'escalier. Curseurs : points (nombre de mesures sur la duree affichee, echantillonnage) et
// bits (nombre de bits par mesure : 2^bits niveaux possibles, soit 2, 4, 8 ou 16).
// Numeriser = mesurer le signal a intervalles reguliers (echantillonner) puis arrondir chaque mesure au niveau permis
// le plus proche (quantifier) ; chaque mesure est gardee jusqu'a la suivante, d'ou l'escalier. Plus de mesures et plus
// de bits : l'escalier colle a la courbe, mais il y a plus de bits a stocker (mesures x bits par mesure).
// Faits : Wikipedia, articles « Numerisation », « Echantillonnage (signal) » et « Quantification (signal) » ; avec n bits
// on distingue 2^n niveaux (programme de technologie du cycle 4). Les niveaux sont des lignes a compter, la taille des
// donnees une barre sans nombre : la figure n'ecrit aucun resultat de calcul, revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["numerisation-signal"] = {
  dessiner(svg, valeurs) {
    const points = Math.min(40, Math.max(4, Math.round(Number(valeurs.points ?? 10))));
    const bits = Math.min(4, Math.max(1, Math.round(Number(valeurs.bits ?? 2))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const ENCRE = "#14243B", GRIS = "#6B7686", BLEU = "#1F4E8C", ORANGE = "#E07B00";

    // Signal de depart (entre 0,08 et 0,92) : une onde lente et une plus rapide, pour qu'il y ait des details a perdre.
    const s = (t) => 0.5 + 0.28 * Math.sin(2 * Math.PI * t) + 0.14 * Math.sin(2 * Math.PI * 4 * t + 0.8);
    const GX = 30, GD = 326, GH = 34, GB = 198; // zone du graphique (niveau 0 en GB, axe 10 px plus bas)
    const X = (t) => GX + t * (GD - GX);
    const Y = (v) => GB - v * (GB - GH);

    // Niveaux permis : lignes grises fines (a compter)
    const niveaux = 2 ** bits;
    for (let k = 0; k < niveaux; k++) {
      const y = Y(k / (niveaux - 1));
      el("line", { x1: GX, y1: y, x2: GD, y2: y, stroke: "#C9CED6", "stroke-width": 2 });
    }
    // Axes
    el("line", { x1: GX, y1: GB + 10, x2: GD, y2: GB + 10, stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: GX - 4, y1: GH - 6, x2: GX - 4, y2: GB + 10, stroke: GRIS, "stroke-width": 2 });
    el("text", { x: GD, y: GB + 28, "font-size": 13, "text-anchor": "end", fill: GRIS }, "temps");

    // Signal d'origine : courbe bleue
    let d = "";
    for (let i = 0; i <= 200; i++) {
      const t = i / 200;
      d += `${i ? "L" : "M"}${X(t).toFixed(1)},${Y(s(t)).toFixed(1)} `;
    }
    el("path", { d, fill: "none", stroke: BLEU, "stroke-width": 3 });

    // Signal numerise : mesure au debut de chaque intervalle, arrondie au niveau le plus proche, gardee jusqu'a la suivante
    let e = "";
    const mesures = [];
    for (let i = 0; i < points; i++) {
      const t0 = i / points, t1 = (i + 1) / points;
      const q = Math.round(s(t0) * (niveaux - 1)) / (niveaux - 1);
      mesures.push([t0, s(t0)]);
      e += `${i ? "L" : "M"}${X(t0).toFixed(1)},${Y(q).toFixed(1)} L${X(t1).toFixed(1)},${Y(q).toFixed(1)} `;
    }
    el("path", { d: e, fill: "none", stroke: ORANGE, "stroke-width": 4, "stroke-linejoin": "miter" });
    const r = points > 24 ? 2.5 : 4;
    for (const [t, v] of mesures) el("circle", { cx: X(t), cy: Y(v), r, fill: ENCRE });

    // Legende
    el("line", { x1: 30, y1: 14, x2: 52, y2: 14, stroke: BLEU, "stroke-width": 3 });
    el("text", { x: 58, y: 19, "font-size": 13, fill: BLEU, "font-weight": "bold" }, "signal réel");
    el("line", { x1: 160, y1: 14, x2: 182, y2: 14, stroke: ORANGE, "stroke-width": 4 });
    el("text", { x: 188, y: 19, "font-size": 13, fill: ORANGE, "font-weight": "bold" }, "signal numérisé");

    el("circle", { cx: 36, cy: 236, r: 4, fill: ENCRE });
    el("text", { x: 46, y: 241, "font-size": 13, fill: ENCRE }, "mesures");
    el("line", { x1: 124, y1: 236, x2: 146, y2: 236, stroke: "#C9CED6", "stroke-width": 2 });
    el("text", { x: 152, y: 241, "font-size": 13, fill: GRIS }, "niveaux permis (à compter)");

    // Taille des donnees : barre proportionnelle a points x bits (max 40 x 4 = 160), sans nombre
    const part = (points * bits) / 160;
    el("text", { x: 30, y: 274, "font-size": 13, fill: ENCRE, "font-weight": "bold" }, "données");
    el("rect", { x: 96, y: 262, width: 230, height: 16, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
    el("rect", { x: 96, y: 262, width: Math.max(3, 230 * part), height: 16, fill: ORANGE });
    el("text", { x: 96, y: 296, "font-size": 13, fill: GRIS }, "plus de mesures × plus de bits");
    return { points, bits, niveaux };
  },
};
