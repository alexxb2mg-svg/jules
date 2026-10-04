// Jules - gabarit "vecteur-force" : une force representee par une fleche sur un quadrillage d'echelle
// (1 carreau = 1 N). Curseurs : intensite (valeur de la force, N) et angle (direction et sens, en degres :
// 0 = vers la droite, 90 = vers le haut, 180 = vers la gauche, 270 = vers le bas).
// Ce qui est montre, et rien de plus : le point d'application (point noir), la direction (droite grise en
// pointilles), le sens (pointe de la fleche) et la valeur (longueur : 1 N par carreau, une graduation par newton
// sur la fleche). La valeur n'est jamais ecrite : l'eleve compte (revele: false).
// Source : programme de physique-chimie du cycle 4 (BO n° 31 du 30/07/2020, annexe 3, theme « Mouvement et
// interactions ») : « Modeliser une action exercee sur un objet par une force caracterisee par un point
// d'application, une direction, un sens et une valeur. »
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["vecteur-force"] = {
  dessiner(svg, valeurs) {
    const intensite = Math.min(10, Math.max(1, Math.round(Number(valeurs.intensite ?? 4))));
    const angle = ((Math.round(Number(valeurs.angle ?? 0)) % 360) + 360) % 360;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const f = (x) => Math.round(x * 10) / 10;
    const ENCRE = "#14243B", GRIS = "#6B7686", ROUGE = "#C8102E", BLEU = "#1F4E8C";
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    // Quadrillage : 20 x 20 carreaux de 14 px autour du point d'application (10 carreaux = la plus grande force).
    const C = 14, CX = 170, CY = 165, R = 10 * C;
    // L'objet (une caisse) : la force s'exerce sur lui. Dessine AVANT le quadrillage et en fond pale : les
    // lignes restent visibles a travers, aucun carreau n'est cache autour du point d'application.
    el("rect", { x: CX - 21, y: CY - 21, width: 42, height: 42, rx: 3, fill: "#DCE8F6", "fill-opacity": 0.5 });
    for (let i = -10; i <= 10; i++) {
      el("line", { x1: CX + i * C, y1: CY - R, x2: CX + i * C, y2: CY + R, stroke: "#E3E8EF", "stroke-width": 2 });
      el("line", { x1: CX - R, y1: CY + i * C, x2: CX + R, y2: CY + i * C, stroke: "#E3E8EF", "stroke-width": 2 });
    }

    el("rect", { x: CX - 21, y: CY - 21, width: 42, height: 42, rx: 3, fill: "none", stroke: BLEU, "stroke-width": 2 });

    // Direction : la droite qui porte la fleche, des deux cotes du point (gris, pointilles).
    const rad = (angle * Math.PI) / 180, ux = Math.cos(rad), uy = -Math.sin(rad);
    // jusqu'au bord du quadrillage (carre de demi-cote R) dans les deux sens
    const t = R / Math.max(Math.abs(ux), Math.abs(uy));
    el("line", {
      x1: f(CX - ux * t), y1: f(CY - uy * t), x2: f(CX + ux * t), y2: f(CY + uy * t),
      stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "6 5",
    });

    // La fleche : longueur = valeur carreaux, pointe = sens.
    const L = intensite * C, POINTE = Math.min(12, L * 0.6);
    const bx = CX + ux * (L - POINTE), by = CY + uy * (L - POINTE);
    el("line", { x1: CX, y1: CY, x2: f(bx), y2: f(by), stroke: ROUGE, "stroke-width": 4, "stroke-linecap": "round" });
    const px = -uy, py = ux; // perpendiculaire
    el("polygon", {
      points: `${f(CX + ux * L)},${f(CY + uy * L)} ${f(bx + px * 7)},${f(by + py * 7)} ${f(bx - px * 7)},${f(by - py * 7)}`,
      fill: ROUGE,
    });
    // Graduation : un trait tous les 1 N le long de la fleche (lisible meme en diagonale, ou les carreaux
    // ne mesurent plus la longueur). Le dernier newton est la pointe.
    for (let k = 1; k < intensite; k++) {
      const gx = CX + ux * k * C, gy = CY + uy * k * C;
      el("line", { x1: f(gx + px * 6), y1: f(gy + py * 6), x2: f(gx - px * 6), y2: f(gy - py * 6), stroke: ROUGE, "stroke-width": 2 });
    }
    // Point d'application
    el("circle", { cx: CX, cy: CY, r: 5, fill: ENCRE });

    // Legende courte sous le quadrillage.
    el("circle", { cx: 22, cy: 325, r: 5, fill: ENCRE });
    el("text", { x: 32, y: 330, "font-size": 13, fill: ENCRE }, "point d'application");
    el("text", { x: 318, y: 330, "font-size": 13, "text-anchor": "end", fill: GRIS }, "1 graduation = 1 N");
    return { intensite, angle };
  },
};
