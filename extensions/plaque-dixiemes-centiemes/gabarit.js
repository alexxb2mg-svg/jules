// Jules - gabarit "plaque-dixiemes-centiemes" : u carres-unites (bleus, coupes en 10 colonnes), di barres-dixiemes
// (vertes, une colonne d'un carre) et c petits carres-centiemes (orange, une case d'une barre). Les dixiemes se
// rangent dans un cadre de la taille d'une unite (10 barres = 1 unite), les centiemes dans un cadre de la taille
// d'une barre (10 centiemes = 1 dixieme). Aucune ecriture a virgule n'est ecrite : l'eleve la construit.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["plaque-dixiemes-centiemes"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const x = Math.round(Number(v ?? defaut));
      return Math.min(max, Math.max(min, Number.isFinite(x) ? x : defaut));
    };
    const u = entier(valeurs.u, 1, 0, 3);
    const di = entier(valeurs.di, 3, 0, 9);
    const c = entier(valeurs.c, 5, 0, 9);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const noeud = document.createElementNS(NS, nom);
      for (const cle in attrs) noeud.setAttribute(cle, attrs[cle]);
      if (texte !== undefined) noeud.textContent = texte;
      svg.appendChild(noeud);
      return noeud;
    };
    svg.setAttribute("viewBox", "0 0 340 310");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const S = 10, COTE = 10 * S; // une case = 10 px, une unite = 100 px de cote
    const BLEU = "#1F4E8C", VERT = "#2E7D32", ORANGE = "#E07B00";
    const cadre = (x, y, l, h) => el("rect", { x, y, width: l, height: h, fill: "none", stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "5 4" });
    const legende = (x, y, texte, couleur) => el("text", { x, y, "font-size": 15, "font-weight": "bold", "text-anchor": "middle", fill: couleur }, texte);

    // ligne du haut : 3 places d'unite, u remplies (un carre bleu coupe en 10 colonnes = 10 dixiemes)
    const yU = 24;
    for (let i = 0; i < 3; i++) {
      const x = 10 + i * (COTE + 10);
      if (i < u) {
        el("rect", { x, y: yU, width: COTE, height: COTE, fill: BLEU, "fill-opacity": 0.85 });
        // 10 colonnes nettes (les dixiemes) et 10 rangees plus fines : 100 cases (les centiemes)
        for (let j = 1; j < 10; j++) {
          el("line", { x1: x, y1: yU + j * S, x2: x + COTE, y2: yU + j * S, stroke: "#FFFFFF", "stroke-width": 1, "stroke-opacity": 0.6 });
          el("line", { x1: x + j * S, y1: yU, x2: x + j * S, y2: yU + COTE, stroke: "#FFFFFF", "stroke-width": 2, "stroke-opacity": 0.85 });
        }
        el("rect", { x, y: yU, width: COTE, height: COTE, fill: "none", stroke: "#14243B", "stroke-width": 2 });
      } else {
        cadre(x, yU, COTE, COTE);
      }
    }
    legende(170, yU + COTE + 24, "unités", BLEU);

    // ligne du bas, a gauche : cadre d'une unite ou se rangent les barres-dixiemes (chaque barre = 10 cases)
    const yB = 178, xD = 50;
    cadre(xD, yB, COTE, COTE);
    for (let i = 0; i < di; i++) {
      const x = xD + i * S;
      el("rect", { x, y: yB, width: S, height: COTE, fill: VERT, "fill-opacity": 0.9 });
      for (let j = 1; j < 10; j++) {
        el("line", { x1: x, y1: yB + j * S, x2: x + S, y2: yB + j * S, stroke: "#FFFFFF", "stroke-width": 1.5, "stroke-opacity": 0.8 });
      }
      el("rect", { x, y: yB, width: S, height: COTE, fill: "none", stroke: "#14243B", "stroke-width": 1.5 });
    }
    legende(xD + COTE / 2, yB + COTE + 24, "dixièmes", VERT);

    // ligne du bas, a droite : cadre d'une barre ou s'empilent les centiemes, du bas vers le haut
    const xC = 250;
    cadre(xC, yB, S, COTE);
    for (let i = 0; i < c; i++) {
      el("rect", { x: xC, y: yB + COTE - (i + 1) * S, width: S, height: S, fill: ORANGE, stroke: "#14243B", "stroke-width": 1.5 });
    }
    legende(xC + S / 2, yB + COTE + 24, "centièmes", "#14243B");
    // 10 pieces d'une sorte remplissent le cadre de la sorte au-dessus
    el("text", { x: xD + COTE / 2, y: yB - 9, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" }, "10 barres = 1 unité");
    el("text", { x: xC + S / 2, y: yB - 9, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" }, "10 cases = 1 barre");
    return { u, di, c };
  },
};
