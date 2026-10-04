// Jules - gabarit "photosynthese-facteurs" : une plante chlorophyllienne ne fabrique sa matiere que si TOUS ses
// besoins sont couverts : lumiere (energie), CO2 de l'air (par les feuilles), eau et sels mineraux du sol (par
// les racines). Le besoin le moins bien couvert fixe la production : c'est le facteur limitant.
// Curseurs : lumiere (eclairement en %, 0 a 100), co2 (0 aucun a 3 beaucoup), eau (0 sol sec a 3 bien arrose).
// Modele simplifie (« loi du minimum ») : production = min(lumiere / 100, co2 / 3, eau / 3), de 0 a 1 ; la jauge
// de matiere produite et l'epaisseur de la seve elaboree la suivent. Aucun nombre calcule n'est ecrit.
// Faits (programme de SVT cycle 4, annexe 3, arrete du 17-7-2020, « besoins et transport de matiere chez une plante
// chlorophyllienne » ; Vikidia « Photosynthese » et « Seve ») : la seve brute (eau et sels mineraux) monte des
// racines vers les feuilles ; la seve elaboree (sucres fabriques par les feuilles) part des feuilles vers le
// reste de la plante et les organes de stockage ; sans lumiere, pas de photosynthese.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun code
// evalue.
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["photosynthese-facteurs"] = {
  dessiner(svg, valeurs) {
    const lumiere = Math.min(100, Math.max(0, Number(valeurs.lumiere ?? 60) || 0));
    const co2 = Math.min(3, Math.max(0, Math.round(Number(valeurs.co2 ?? 2)) || 0));
    const eau = Math.min(3, Math.max(0, Math.round(Number(valeurs.eau ?? 2)) || 0));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const VERT = "#2E7D32", ROUGE = "#C8102E", BLEU = "#1F4E8C", GRIS = "#6B7686", TEXTE = "#14243B", ORANGE = "#E07B00";
    const parts = { lumiere: lumiere / 100, co2: co2 / 3, eau: eau / 3 };
    const production = Math.min(parts.lumiere, parts.co2, parts.eau);
    const limitant = (cle) => production < 1 && parts[cle] === production;
    const fleche = (x1, y1, x2, y2, couleur, ep) => {
      const a = Math.atan2(y2 - y1, x2 - x1), t = ep / 2 + 6, L = 12;
      const bx = x2 - L * Math.cos(a), by = y2 - L * Math.sin(a);
      el("line", { x1, y1, x2: bx, y2: by, stroke: couleur, "stroke-width": ep });
      el("path", {
        d: `M ${x2} ${y2} L ${bx + t * Math.sin(a)} ${by - t * Math.cos(a)} L ${bx - t * Math.sin(a)} ${by + t * Math.cos(a)} Z`,
        fill: couleur,
      });
    };

    // --- Sol et racines.
    el("rect", { x: 10, y: 262, width: 240, height: 50, fill: GRIS, "fill-opacity": 0.18 });
    el("line", { x1: 10, y1: 262, x2: 250, y2: 262, stroke: GRIS, "stroke-width": 2 });
    for (const [dx, dy] of [[-34, 34], [0, 42], [32, 30]]) {
      el("line", { x1: 150, y1: 262, x2: 150 + dx, y2: 262 + dy, stroke: VERT, "stroke-width": 3 });
    }
    for (let i = 0; i < eau * 2; i++) { // gouttes d'eau du sol
      el("circle", { cx: 24 + i * 18, cy: 286 + (i % 2) * 12, r: 5, fill: BLEU });
    }
    el("text", { x: 10, y: 332, "font-size": 13, fill: BLEU, "font-weight": "bold" }, "eau + sels minéraux");
    if (limitant("eau")) el("text", { x: 146, y: 332, "font-size": 13, fill: ROUGE, "font-weight": "bold" }, "facteur limitant");

    // --- Tige et feuilles.
    el("line", { x1: 150, y1: 262, x2: 150, y2: 96, stroke: VERT, "stroke-width": 4 });
    el("ellipse", { cx: 190, cy: 104, rx: 38, ry: 15, fill: VERT, "fill-opacity": 0.8, transform: "rotate(-15 190 104)" });
    el("ellipse", { cx: 112, cy: 150, rx: 36, ry: 14, fill: VERT, "fill-opacity": 0.8, transform: "rotate(15 112 150)" });

    // Seve brute (bleue) : monte des racines vers les feuilles, s'il y a de l'eau.
    if (eau > 0) fleche(140, 250, 140, 168, BLEU, 2 + eau * 1.5);
    el("text", { x: 132, y: 228, "font-size": 13, "text-anchor": "end", fill: BLEU }, "sève brute");
    // Seve elaboree (verte) : descend des feuilles vers les reserves, epaisseur = production.
    if (production > 0) fleche(160, 128, 160, 250, VERT, 2 + production * 6);
    el("text", { x: 168, y: 228, "font-size": 13, fill: VERT }, "sève élaborée");

    // --- Lumiere : soleil plus ou moins vif et fleche vers la feuille.
    el("circle", { cx: 34, cy: 34, r: 18, fill: lumiere > 0 ? ORANGE : "none", "fill-opacity": 0.2 + 0.8 * parts.lumiere, stroke: lumiere > 0 ? ORANGE : GRIS, "stroke-width": 2 });
    if (lumiere > 0) fleche(56, 46, 160, 96, ORANGE, 2 + parts.lumiere * 5);
    el("text", { x: 60, y: 24, "font-size": 14, fill: ORANGE, "font-weight": "bold" }, lumiere > 0 ? "lumière" : "noir");
    if (limitant("lumiere")) el("text", { x: 8, y: 96, "font-size": 13, fill: ROUGE, "font-weight": "bold" }, "facteur limitant");

    // --- CO2 de l'air : une fleche grise par cran, vers la feuille.
    for (let i = 0; i < co2; i++) fleche(326, 96 + i * 14, 236, 96 + i * 14, GRIS, 3);
    el("text", { x: 330, y: 52, "font-size": 14, "text-anchor": "end", fill: GRIS, "font-weight": "bold" }, "CO₂ de l'air");
    if (limitant("co2")) el("text", { x: 330, y: 70, "font-size": 13, "text-anchor": "end", fill: ROUGE, "font-weight": "bold" }, "facteur limitant");

    // --- Jauge de matiere produite (et stockee).
    const JX = 272, JL = 44, JH = 150, JB = 250;
    el("rect", { x: JX, y: JH, width: JL, height: JB - JH, fill: "none", stroke: GRIS, "stroke-width": 2 });
    if (production > 0) {
      const h = (JB - JH) * production;
      el("rect", { x: JX, y: JB - h, width: JL, height: h, fill: VERT });
    }
    el("text", { x: JX + JL / 2, y: 276, "font-size": 13, "text-anchor": "middle", fill: VERT, "font-weight": "bold" }, "matière");
    el("text", { x: JX + JL / 2, y: 292, "font-size": 13, "text-anchor": "middle", fill: VERT, "font-weight": "bold" }, "produite");
    if (production === 0) {
      el("text", { x: JX + JL / 2, y: JH - 8, "font-size": 13, "text-anchor": "middle", fill: ROUGE, "font-weight": "bold" }, "arrêt");
    }
    return { lumiere, co2, eau, production };
  },
};
