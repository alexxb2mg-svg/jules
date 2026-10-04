// Jules - gabarit "effet-de-serre" : le Soleil, une couche d'atmosphere et le sol, vus en coupe. La lumiere du
// Soleil (orange) traverse l'atmosphere et chauffe le sol ; le sol renvoie un rayonnement infrarouge (rouge) ;
// les gaz a effet de serre de l'atmosphere en retiennent une partie et la renvoient vers le sol, le reste part
// vers l'espace. Curseur : co2 (concentration de CO2 dans l'air, en ppm = parties par million).
// Le partage du rayonnement infrarouge est un SCHEMA, pas une mesure : la part renvoyee vers le sol vaut
// 0,5 + 0,25 x log2(co2 / 280) (0,34 a 180 ppm, 0,5 a 280 ppm, 0,75 a 560 ppm). Seul le sens de variation est
// physique : le forcage radiatif du CO2 croit comme le logarithme de sa concentration (GIEC, AR6, WG1, ch. 7).
// Le thermometre suit la meme part, sans graduation : la figure n'ecrit aucune temperature, aucune valeur.
// Reperes de concentration retenus pour les fiches (pas ecrits dans la figure) : environ 180 ppm aux maximums
// glaciaires et 280 ppm aux interglaciaires sur 800 000 ans (carottes de glace EPICA Dome C, Luthi et al., Nature
// 2008) ; 280 ppm avant l'ere industrielle ; 424,61 ppm en moyenne annuelle 2024 a Mauna Loa (NOAA GML, repris par
// https://www.climate.gov/news-features/understanding-climate/climate-change-atmospheric-carbon-dioxide).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["effet-de-serre"] = {
  dessiner(svg, valeurs) {
    const co2 = Math.min(560, Math.max(180, Number(valeurs.co2 ?? 280)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const f = (x) => Math.round(x * 10) / 10;
    const ENCRE = "#14243B", GRIS = "#6B7686", BLEU = "#1F4E8C", ROUGE = "#C8102E", ORANGE = "#E07B00", VERT = "#2E7D32";
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    const part = 0.5 + 0.25 * Math.log2(co2 / 280); // part de l'infrarouge renvoyee vers le sol (schema)

    // Bandes : espace (haut, blanc), atmosphere (bleu pale), sol (vert).
    const AT_H = 120, AT_B = 190, SOL = 280;
    el("rect", { x: 0, y: AT_H, width: 300, height: AT_B - AT_H, fill: "#E8EEF7" });
    el("text", { x: 8, y: AT_H + 18, "font-size": 13, fill: BLEU }, "atmosphère");
    // Molecules de gaz a effet de serre : une pour 40 ppm (4 a 14), placees sur une grille fixe.
    const n = Math.round(co2 / 40);
    for (let i = 0; i < n; i++) {
      const col = i % 7, lig = Math.floor(i / 7);
      el("circle", { cx: 114 + col * 26 + (lig % 2) * 13, cy: AT_H + 40 + lig * 18, r: 5, fill: BLEU });
    }
    el("line", { x1: 3, y1: SOL, x2: 297, y2: SOL, stroke: VERT, "stroke-width": 6 });
    el("text", { x: 8, y: SOL + 22, "font-size": 13, fill: VERT }, "sol");
    el("text", { x: 8, y: 20, "font-size": 13, fill: GRIS }, "espace");

    // Soleil et sa lumiere (orange), qui traverse l'atmosphere jusqu'au sol.
    el("circle", { cx: 52, cy: 58, r: 20, fill: ORANGE });
    el("text", { x: 52, y: 98, "font-size": 13, "text-anchor": "middle", fill: ORANGE }, "Soleil");
    const fleche = (x1, y1, x2, y2, larg, couleur) => {
      const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L;
      const P = Math.max(10, larg + 4), bx = x2 - ux * P, by = y2 - uy * P;
      el("line", { x1, y1, x2: f(bx), y2: f(by), stroke: couleur, "stroke-width": f(larg) });
      const demi = larg / 2 + 5;
      el("polygon", {
        points: `${x2},${y2} ${f(bx - uy * demi)},${f(by + ux * demi)} ${f(bx + uy * demi)},${f(by - ux * demi)}`,
        fill: couleur,
      });
    };
    fleche(72, 70, 150, SOL - 4, 8, ORANGE); // a droite des etiquettes « Soleil » et « atmosphère »

    // Infrarouge (rouge) : monte du sol jusqu'a l'atmosphere, puis se partage.
    const W = 24, XM = 200, XR = 250;
    fleche(XM, SOL - 4, XM, AT_B + 2, W, ROUGE);
    const wEsp = Math.max(3, W * (1 - part)), wSol = Math.max(3, W * part);
    fleche(XM, AT_H - 2, XM, 34, wEsp, ROUGE);
    fleche(XR, AT_B - 6, XR, SOL - 4, wSol, ROUGE);
    // Jonction dans l'atmosphere : l'infrarouge absorbe repart vers le bas un peu plus loin.
    el("line", { x1: XM, y1: AT_B + 2, x2: XM, y2: AT_H - 2, stroke: ROUGE, "stroke-width": 3, "stroke-dasharray": "4 4" });
    el("line", { x1: XM, y1: (AT_H + AT_B) / 2 + 20, x2: XR, y2: AT_B - 6, stroke: ROUGE, "stroke-width": 3, "stroke-dasharray": "4 4" });
    el("text", { x: XM + 18, y: 46, "font-size": 13, fill: ROUGE }, "part vers");
    el("text", { x: XM + 18, y: 62, "font-size": 13, fill: ROUGE }, "l'espace");
    el("text", { x: XR - 14, y: SOL + 22, "font-size": 13, "text-anchor": "middle", fill: ROUGE }, "revient au sol");
    el("text", { x: 130, y: SOL + 44, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "orange : lumière · rouge : infrarouge");

    // Thermometre (sans graduation) : le liquide monte avec la part renvoyee vers le sol.
    const TX = 318, TH = 70, TB = 250;
    el("rect", { x: TX - 7, y: TH, width: 14, height: TB - TH, rx: 7, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 2 });
    const niveau = TB - 20 - (TB - TH - 30) * ((part - 0.34) / (0.75 - 0.34));
    el("rect", { x: TX - 3, y: f(niveau), width: 6, height: f(TB + 4 - niveau), fill: ROUGE });
    el("circle", { cx: TX, cy: TB + 10, r: 12, fill: ROUGE, stroke: ENCRE, "stroke-width": 2 });
    return { co2, part };
  },
};
