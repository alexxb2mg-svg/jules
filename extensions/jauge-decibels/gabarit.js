// Jules - gabarit "jauge-decibels" : a gauche, la jauge du niveau sonore (20 a 130 dB) avec quatre reperes ;
// a droite, la « dose de son » de la journee, qui depend du niveau ET de la duree d'ecoute.
// Curseurs : niveau (dB) et duree (heures). Dose = duree / duree sans risque, avec la regle d'egale energie :
// 85 dB(A) pendant 8 h = la limite (100 %, Code du travail art. R4431-2), et chaque +3 dB divise par deux la duree
// sans risque (8 h a 85 dB, 4 h a 88 dB, 2 h a 91 dB, 1 h a 94 dB). Des 120 dB (seuil de douleur), danger immediat.
// Aucun pourcentage n'est ecrit : la barre se remplit et passe la ligne « limite ».
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["jauge-decibels"] = {
  dessiner(svg, valeurs) {
    const niveau = Math.min(130, Math.max(20, Number(valeurs.niveau ?? 60)));
    const duree = Math.min(8, Math.max(0.5, Number(valeurs.duree ?? 1)));
    const dose = duree / (8 * Math.pow(2, (85 - niveau) / 3));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00", GRIS = "#6B7686", ENCRE = "#14243B";
    const couleurNiveau = (l) => (l >= 120 ? ROUGE : l >= 85 ? ORANGE : VERT);
    const BAS = 290, HAUT = 70;
    const Y = (l) => BAS - ((l - 20) * (BAS - HAUT)) / 110;

    svg.setAttribute("viewBox", "0 0 340 340");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS
    const titre = niveau >= 120 ? "danger immédiat" : niveau >= 85 ? "danger si ça dure" : "sans danger";
    el("text", { x: 170, y: 24, "font-size": 18, "font-weight": "bold", "text-anchor": "middle", fill: couleurNiveau(niveau) },
      `${niveau} dB : ${titre}`);

    // Jauge du niveau : trois zones pales, remplissage plein jusqu'au niveau choisi.
    el("text", { x: 55, y: 50, "font-size": 14, "text-anchor": "middle", fill: ENCRE }, "niveau");
    for (const [de, a, c] of [[20, 85, VERT], [85, 120, ORANGE], [120, 130, ROUGE]]) {
      el("rect", { x: 40, y: Y(a), width: 30, height: Y(de) - Y(a), fill: c, "fill-opacity": 0.18 });
    }
    el("rect", { x: 40, y: Y(niveau), width: 30, height: BAS - Y(niveau), fill: couleurNiveau(niveau) });
    el("rect", { x: 40, y: HAUT, width: 30, height: BAS - HAUT, fill: "none", stroke: ENCRE, "stroke-width": 2 });
    for (const l of [20, 85, 120]) {
      el("line", { x1: 34, y1: Y(l), x2: 40, y2: Y(l), stroke: ENCRE, "stroke-width": 2 });
      el("text", { x: 31, y: Y(l) + 5, "font-size": 13, "text-anchor": "end", fill: ENCRE }, String(l));
    }
    // Reperes (valeurs approchees).
    for (const [l, nom] of [[60, "conversation"], [85, "cantine"], [100, "concert"], [120, "douleur"]]) {
      el("line", { x1: 70, y1: Y(l), x2: 82, y2: Y(l), stroke: GRIS, "stroke-width": 2 });
      el("text", { x: 86, y: Y(l) + 5, "font-size": 13, fill: l >= 120 ? ROUGE : GRIS }, `${nom} ≈ ${l}`);
    }

    // Dose du jour : 0 a 200 % de la limite sur la hauteur de la barre, ligne « limite » a mi-hauteur.
    const X = 255, L = 30;
    el("text", { x: X + L / 2, y: 50, "font-size": 14, "text-anchor": "middle", fill: ENCRE }, "dose du jour");
    const plein = Math.min(dose, 2) / 2;
    const couleurDose = dose > 1 ? ROUGE : dose >= 0.5 ? ORANGE : VERT;
    el("rect", { x: X, y: BAS - plein * (BAS - HAUT), width: L, height: plein * (BAS - HAUT), fill: couleurDose });
    el("rect", { x: X, y: HAUT, width: L, height: BAS - HAUT, fill: "none", stroke: ENCRE, "stroke-width": 2 });
    const yLimite = (BAS + HAUT) / 2;
    el("line", { x1: X - 8, y1: yLimite, x2: X + L + 8, y2: yLimite, stroke: ROUGE, "stroke-width": 3, "stroke-dasharray": "6 4" });
    el("text", { x: X - 12, y: yLimite + 5, "font-size": 13, "text-anchor": "end", fill: ROUGE }, "limite");
    if (dose > 2) el("path", { d: `M${X + L / 2},${HAUT - 9} l-7,8 l14,0 z`, fill: ROUGE }); // la dose sort de la barre
    el("text", { x: X + L / 2, y: 316, "font-size": 14, "text-anchor": "middle", fill: couleurDose },
      Math.abs(dose - 1) < 0.01 ? "juste à la limite" : dose > 1 ? "limite dépassée" : "sous la limite");
    return { niveau, duree, dose: Math.round(dose * 100) / 100 };
  },
};
