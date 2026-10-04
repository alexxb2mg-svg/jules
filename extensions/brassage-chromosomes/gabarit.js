// Jules - gabarit "brassage-chromosomes" : meiose et gametes, le brassage des chromosomes.
// Curseurs : paires (paires de chromosomes de la cellule, 1 a 4), tirage (numero du gamete entoure en rouge,
// 1 a 16 ; au-dela du nombre de gametes possibles, on repart du premier).
// En haut, une cellule avec ses paires : dans chaque paire, un chromosome venu du pere (bleu) et un venu de la mere
// (orange) ; les paires ont des longueurs differentes pour les reconnaitre. En dessous, TOUS les gametes possibles
// apres la meiose : chacun garde un seul chromosome de chaque paire, bleu ou orange. Le nombre de gametes n'est pas
// ecrit (l'eleve les compte : 2, 4, 8, 16) : la figure ne donne pas la reponse 2^n.
// Simplification du programme de college : le brassage intrachromosomique (crossing-over) n'est pas dessine.
// Faits : programme de SVT cycle 4 (annexe 3, arrete du 17-7-2020 : « relier, comme le montrent les experiences de
// brassage, la diversite genetique a la meiose et a la fecondation ») ; espece humaine 23 paires de chromosomes,
// 2^23 = 8 388 608 combinaisons de chromosomes par gamete (Vikidia « Meiose », manuels SVT 3e).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["brassage-chromosomes"] = {
  dessiner(svg, valeurs) {
    const paires = Math.min(4, Math.max(1, Math.round(Number(valeurs.paires ?? 2))));
    const tirage = Math.max(1, Math.round(Number(valeurs.tirage ?? 1)));
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

    const PERE = "#1F4E8C", MERE = "#E07B00";
    const LONGUEURS = [56, 44, 34, 24]; // une longueur par paire

    // Legende des couleurs.
    el("rect", { x: 40, y: 8, width: 14, height: 14, rx: 3, fill: PERE });
    el("text", { x: 60, y: 20, "font-size": 14, fill: "#14243B" }, "venu du père");
    el("rect", { x: 190, y: 8, width: 14, height: 14, rx: 3, fill: MERE });
    el("text", { x: 210, y: 20, "font-size": 14, fill: "#14243B" }, "venu de la mère");

    // La cellule et ses paires de chromosomes.
    const CY = 84;
    el("ellipse", { cx: 170, cy: CY, rx: 140, ry: 48, fill: "none", stroke: "#6B7686", "stroke-width": 2 });
    const largeurPaire = 56;
    const x0 = 170 - (paires * largeurPaire) / 2 + largeurPaire / 2;
    const chromosome = (cx, cy, h, w, couleur) =>
      el("rect", { x: cx - w / 2, y: cy - h / 2, width: w, height: h, rx: w / 2, fill: couleur });
    for (let p = 0; p < paires; p++) {
      const cx = x0 + p * largeurPaire;
      chromosome(cx - 8, CY, LONGUEURS[p], 10, PERE);
      chromosome(cx + 8, CY, LONGUEURS[p], 10, MERE);
    }

    // Fleche « meiose ».
    el("line", { x1: 170, y1: 136, x2: 170, y2: 160, stroke: "#14243B", "stroke-width": 2 });
    el("polygon", { points: "163,156 177,156 170,166", fill: "#14243B" });
    el("text", { x: 182, y: 154, "font-size": 14, fill: "#14243B" }, "méiose");
    el("text", { x: 170, y: 186, "font-size": 14, "text-anchor": "middle", fill: "#14243B", "font-weight": "bold" },
      "les gamètes possibles");

    // Tous les gametes : le gamete g prend, pour la paire p, le chromosome du pere si le bit p de g vaut 0.
    const nombre = 2 ** paires;
    const parLigne = Math.min(nombre, 8);
    const PAS_X = 41, R = 18;
    const choisi = (tirage - 1) % nombre;
    for (let g = 0; g < nombre; g++) {
      const ligne = Math.floor(g / parLigne), col = g % parLigne;
      const gx = 170 + (col - (parLigne - 1) / 2) * PAS_X;
      const gy = 218 + ligne * 44;
      el("circle", { cx: gx, cy: gy, r: R, fill: "#FFFFFF", stroke: "#6B7686", "stroke-width": 2 });
      const pas = 7; // 4 chromosomes de 5 px espaces de 7 px : 26 px, dans le cercle de 36 px
      const debut = gx - ((paires - 1) * pas) / 2;
      for (let p = 0; p < paires; p++) {
        const couleur = (g >> p) & 1 ? MERE : PERE;
        chromosome(debut + p * pas, gy, LONGUEURS[p] * 0.42, 5, couleur);
      }
      if (g === choisi) {
        el("circle", { cx: gx, cy: gy, r: R + 1, fill: "none", stroke: "#C8102E", "stroke-width": 3 });
      }
    }
    el("text", { x: 170, y: 294, "font-size": 13, "text-anchor": "middle", fill: "#C8102E" },
      "entouré en rouge : un gamète tiré au hasard");
    return { paires, tirage: choisi + 1 };
  },
};
