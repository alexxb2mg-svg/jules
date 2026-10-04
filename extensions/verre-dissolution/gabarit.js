// Jules - gabarit "verre-dissolution" : un verre d'eau dans lequel on verse du sel. Tant que l'eau n'est pas
// saturee, le sel dissous ne se voit plus (melange homogene) ; au-dela, le surplus reste au fond (heterogene).
// Curseurs : sel (masse de sel versee, g), volume (volume d'eau, mL).
// CM1 : la fiche fige volume a 100 mL et fait avancer sel de 6 g en 6 g (une cuillere a cafe rase de sel pese
// environ 5 a 6 g) : 6 cuilleres se dissolvent (36 g), la 7e sature, comme l'exemple de la fiche CM1.
// Fait : solubilite du sel (chlorure de sodium) dans l'eau a 20 degres : 358,5 g/L, arrondie ici a 36 g pour
// 100 mL d'eau (0,36 g/mL), valeur reprise par la fiche 3e « melanges-solubilite » (360 g/L vers 20 degres).
// Source : Wikipedia, « Chlorure de sodium », tableau des proprietes (solubilite 358,5 g/L a 20 degres, d'apres le
// CRC Handbook of Chemistry and Physics) ; notion de saturation et de solubilite : programme de physique-chimie
// du cycle 4 (BO n° 31 du 30 juillet 2020), https://eduscol.education.fr/document/621/download ; CM1 : programme
// de sciences et technologie du cycle 3 (melanges, dissolution).
// Le sel dissous n'est pas dessine (il ne se voit plus) ; le depot est dessine en grains (1 grain = 2 g), sans
// ecrire de masse maximale : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["verre-dissolution"] = {
  dessiner(svg, valeurs) {
    const sel = Math.min(80, Math.max(0, Number(valeurs.sel ?? 20)));
    const eau = Math.min(200, Math.max(50, Number(valeurs.volume ?? 100)));
    const SOLUBILITE = 0.36; // g de sel par mL d'eau, vers 20 degres
    const dissous = Math.min(sel, SOLUBILITE * eau);
    const surplus = Math.max(0, sel - dissous);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 320");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Verre : de x 110 a 250, fond a y 270, bord a y 40 ; 1 mL = 1 px de hauteur (200 mL = 200 px).
    const G = 110, D = 250, FOND = 270;
    const surface = FOND - eau;
    el("rect", { x: G, y: surface, width: D - G, height: eau, fill: "#D6E6F5" });
    el("line", { x1: G, y1: surface, x2: D, y2: surface, stroke: "#1F4E8C", "stroke-width": 2.5 });
    el("path", { d: `M${G},40 V${FOND} H${D} V40`, fill: "none", stroke: "#6B7686", "stroke-width": 3 });

    // Graduations a gauche du verre : 50, 100, 150, 200 mL.
    for (const v of [50, 100, 150, 200]) {
      const y = FOND - v;
      el("line", { x1: G - 10, y1: y, x2: G, y2: y, stroke: "#6B7686", "stroke-width": 2 });
      el("text", { x: G - 14, y: y + 5, "font-size": 13, "text-anchor": "end", fill: "#6B7686" }, `${v} mL`);
    }

    // Depot au fond : un grain (cercle blanc) pour 2 g de surplus, rangees de 8 grains, une rangee sur deux
    // decalee d'un demi-grain (empilement). 80 g au plus -> 40 grains -> 5 rangees.
    const grains = Math.ceil(surplus / 2 - 1e-9);
    const PAR_RANG = 8, R = 7;
    for (let i = 0; i < grains; i++) {
      const rang = Math.floor(i / PAR_RANG), col = i % PAR_RANG;
      const x = G + 14 + (rang % 2 ? R : 0) + col * 2 * R;
      const y = FOND - 1.5 - R - rang * (2 * R - 3);
      el("circle", { cx: x, cy: y, r: R, fill: "#FFFFFF", stroke: "#6B7686", "stroke-width": 2 });
    }
    if (grains > 0) {
      const yd = FOND - 12 - Math.floor((grains - 1) / PAR_RANG) * (2 * R - 3);
      el("line", { x1: D + 10, y1: yd - 18, x2: D - 6, y2: yd - 4, stroke: "#14243B", "stroke-width": 2 });
      el("text", { x: D + 12, y: yd - 22, "font-size": 15, fill: "#14243B", "font-weight": "bold" }, "dépôt");
    }

    // Sel verse (valeur du curseur) et volume d'eau.
    el("text", { x: 20, y: 300, "font-size": 15, fill: "#14243B", "font-weight": "bold" }, `sel versé : ${sel} g`);
    el("text", { x: 200, y: 300, "font-size": 15, fill: "#1F4E8C" }, `eau : ${eau} mL`);
    return { sel, volume: eau, sature: surplus > 0, grains };
  },
};
