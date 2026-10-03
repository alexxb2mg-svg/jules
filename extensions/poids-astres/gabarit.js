// Jules - gabarit "poids-astres" : le meme sac sur quatre astres. Curseurs : m (masse, kg) et astre
// (1 Lune, 2 Mars, 3 Terre, 4 Jupiter). La fleche rouge du poids P = m x g est a l'echelle (meme echelle
// pour tous les reglages) ; la fleche grise en pointilles rappelle le poids sur Terre. La valeur de P
// n'est jamais ecrite (la figure ne fait pas le calcul a la place de l'eleve) : seuls m et g le sont.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["poids-astres"] = {
  dessiner(svg, valeurs) {
    const m = Math.min(10, Math.max(1, Math.round(Number(valeurs.m ?? 5))));
    const ASTRES = [
      { nom: "la Lune", g: 1.6 },
      { nom: "Mars", g: 3.7 },
      { nom: "la Terre", g: 9.8 },
      { nom: "Jupiter", g: 24.8 },
    ];
    const n = Math.min(4, Math.max(1, Math.round(Number(valeurs.astre ?? 3))));
    const astre = ASTRES[n - 1];
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const fmt = (x) => String(x).replace(".", ",");
    const ROUGE = "#C8102E", BLEU = "#1F4E8C", VERT = "#2E7D32", GRIS = "#6B7686", ENCRE = "#14243B";
    // Echelle unique : le plus grand poids (10 kg sur Jupiter, 248 N) mesure 225 px. La fleche part du
    // centre du sac (point G, ou s'applique le poids) ; le sac est pale pour qu'on la voie au travers.
    const K = 225 / 248;
    const CX = 110, CY = 100;
    const fleche = (x, longueur, couleur, pointilles) => {
      const bout = CY + longueur;
      const tete = Math.max(6, Math.min(12, longueur * 0.6));
      el("line", {
        x1: x, y1: CY, x2: x, y2: Math.max(CY, bout - tete * 0.8), stroke: couleur, "stroke-width": 4,
        ...(pointilles ? { "stroke-dasharray": "6 5" } : {}),
      });
      el("path", { d: `M${x},${bout} l${-tete * 0.6},${-tete} l${tete * 1.2},0 z`, fill: couleur });
      return bout;
    };

    svg.setAttribute("viewBox", "0 0 340 340");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 26, "font-size": 18, "font-weight": "bold", "text-anchor": "middle", fill: ENCRE }, `Sur ${astre.nom}`);

    // Potence et fil.
    el("line", { x1: 50, y1: 44, x2: 170, y2: 44, stroke: GRIS, "stroke-width": 4 });
    // Sac : sa taille grandit avec la masse, jamais avec l'astre.
    const w = 22 + 2 * m;
    el("line", { x1: CX, y1: 44, x2: CX, y2: CY - w, stroke: GRIS, "stroke-width": 2 });
    el("rect", { x: CX - w, y: CY - w, width: 2 * w, height: 2 * w, rx: 10, fill: BLEU, "fill-opacity": 0.15, stroke: BLEU, "stroke-width": 3 });
    el("text", { x: CX, y: CY - w + 16, "font-size": 13, "font-weight": "bold", "text-anchor": "middle", fill: BLEU }, `${m} kg`);

    // Poids sur Terre (rappel, gris pointille) puis poids sur l'astre choisi (rouge).
    if (n !== 3) {
      const xT = CX + w + 16;
      const boutT = fleche(xT, m * 9.8 * K, GRIS, true);
      el("text", { x: xT, y: boutT + 16, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "Terre");
    }
    const bout = fleche(CX, m * astre.g * K, ROUGE, false);
    el("circle", { cx: CX, cy: CY, r: 4, fill: ROUGE });
    el("text", { x: CX - w - 6, y: Math.max(bout, CY + 6), "font-size": 16, "font-weight": "bold", "text-anchor": "end", fill: ROUGE }, "P");

    // Ce qui est ecrit : m (bleu, ne change pas d'un astre a l'autre) et g (vert, change avec l'astre).
    el("text", { x: 200, y: 80, "font-size": 16, fill: BLEU }, `m = ${m} kg`);
    el("text", { x: 200, y: 108, "font-size": 16, fill: VERT }, `g = ${fmt(astre.g)} N/kg`);
    el("text", { x: 200, y: 148, "font-size": 14, fill: ROUGE }, "rouge : poids P");
    if (n !== 3) el("text", { x: 200, y: 170, "font-size": 14, fill: GRIS }, "gris : poids sur Terre");
    el("text", { x: 200, y: 200, "font-size": 15, fill: ENCRE }, "P = m × g");
    return { m, g: astre.g, astre: n };
  },
};
