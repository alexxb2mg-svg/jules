// Jules - gabarit "diagramme-barres" : diagramme en barres de quatre categories A, B, C, D.
// e1 a e4 : valeur (effectif) de chaque categorie, de 0 a 30. grad : pas des graduations de l'axe (1 a 5) ; les
// nombres de l'axe sont ecrits de pas en pas quand la place le permet (sinon tous les 2, 4 ou 5 pas), pour obliger
// a lire le pas avant de lire une barre. frequences = 1 (3e) : sous le diagramme, une bande 100 % partagee selon
// les frequences (effectif / effectif total), chaque categorie a sa couleur dans les barres et dans la bande.
// Aucune valeur de barre ni aucune frequence n'est ecrite : l'eleve lit l'axe ou la bande graduee en quarts.
// Definitions (effectif, effectif total, frequence = effectif / effectif total, diagramme en barres) : programme
// de mathematiques du cycle 4, BO n° 31 du 30/07/2020 ; cycle 3 (CM1), programme 2020 « Organisation et gestion
// de donnees » (lire, interpreter et representer des donnees sous forme de diagrammes en barres).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["diagramme-barres"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const n = Number(v ?? defaut);
      return Math.min(max, Math.max(min, Math.round(Number.isFinite(n) ? n : defaut)));
    };
    const e = [
      entier(valeurs.e1, 12, 0, 30),
      entier(valeurs.e2, 8, 0, 30),
      entier(valeurs.e3, 6, 0, 30),
      entier(valeurs.e4, 4, 0, 30),
    ];
    const grad = entier(valeurs.grad, 5, 1, 5);
    const frequences = entier(valeurs.frequences, 0, 0, 1);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const x = document.createElementNS(NS, nom);
      for (const k in attrs) x.setAttribute(k, attrs[k]);
      if (texte !== undefined) x.textContent = texte;
      svg.appendChild(x);
      return x;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", VERT = "#2E7D32", ORANGE = "#E07B00";
    const COULEURS = frequences ? [BLEU, VERT, ORANGE, GRIS] : [BLEU, BLEU, BLEU, BLEU];
    const NOMS = ["A", "B", "C", "D"];
    const X_AXE = 52, Y_BAS = 222, Y_HAUT = 22, MAXI = 30;
    const ECHELLE = (Y_BAS - Y_HAUT) / MAXI;
    const y = (v) => Y_BAS - v * ECHELLE;
    svg.setAttribute("viewBox", frequences ? "0 0 340 330" : "0 0 340 258");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Axe vertical : un trait a chaque graduation ; nombres ecrits tous les k pas (k = 1, 2, 5 ou 10) des que deux
    // nombres sont a 15 px l'un de l'autre au moins.
    let pasNombres = grad;
    for (const k of [1, 2, 5, 10]) {
      pasNombres = k * grad;
      if (pasNombres * ECHELLE >= 15) break;
    }
    el("line", { x1: X_AXE, y1: Y_HAUT - 8, x2: X_AXE, y2: Y_BAS, stroke: ENCRE, "stroke-width": 2 });
    el("line", { x1: X_AXE, y1: Y_BAS, x2: 328, y2: Y_BAS, stroke: ENCRE, "stroke-width": 2 });
    for (let v = 0; v <= MAXI; v += grad) {
      const nombre = v % pasNombres === 0;
      el("line", { x1: X_AXE - (nombre ? 8 : 5), y1: y(v), x2: X_AXE, y2: y(v), stroke: ENCRE, "stroke-width": 2 });
      if (nombre) el("text", { x: X_AXE - 12, y: y(v) + 5, "font-size": 14, "text-anchor": "end", fill: ENCRE }, String(v));
    }

    // Barres : quatre colonnes de 69 px ; trait pointille du haut de chaque barre jusqu'a l'axe pour aider la lecture.
    // Les pointilles d'abord, les barres ensuite : un pointille ne traverse jamais une barre.
    const COLONNE = (328 - X_AXE) / 4, LARGEUR = 40;
    const centre = (i) => X_AXE + COLONNE * (i + 0.5);
    e.forEach((v, i) => {
      if (v > 0) el("line", { x1: X_AXE, y1: y(v), x2: centre(i) - LARGEUR / 2, y2: y(v), stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "3 5" });
    });
    e.forEach((v, i) => {
      const cx = centre(i);
      if (v > 0) el("rect", { x: cx - LARGEUR / 2, y: y(v), width: LARGEUR, height: v * ECHELLE, fill: COULEURS[i] });
      el("text", { x: cx, y: Y_BAS + 22, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, NOMS[i]);
    });

    if (frequences) {
      // Bande 100 % : une part par categorie, proportionnelle a sa frequence ; graduee en quarts.
      const X0 = 20, L = 300, Y = 266, H = 28, total = e[0] + e[1] + e[2] + e[3];
      el("rect", { x: X0, y: Y, width: L, height: H, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
      let debut = X0;
      if (total > 0) {
        e.forEach((v, i) => {
          const w = (L * v) / total;
          if (w <= 0) return;
          el("rect", { x: debut, y: Y, width: w, height: H, fill: COULEURS[i], stroke: "#FFFFFF", "stroke-width": 2 });
          if (w >= 18) el("text", { x: debut + w / 2, y: Y + 20, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: "#FFFFFF" }, NOMS[i]);
          debut += w;
        });
      }
      for (let q = 0; q <= 4; q++) {
        const xq = X0 + (L * q) / 4;
        el("line", { x1: xq, y1: Y + H, x2: xq, y2: Y + H + 7, stroke: ENCRE, "stroke-width": 2 });
      }
      el("text", { x: X0, y: Y + H + 22, "font-size": 13, "text-anchor": "start", fill: ENCRE }, "0 %");
      el("text", { x: X0 + L / 2, y: Y + H + 22, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "50 %");
      el("text", { x: X0 + L, y: Y + H + 22, "font-size": 13, "text-anchor": "end", fill: ENCRE }, "100 %");
    }
    return { e1: e[0], e2: e[1], e3: e[2], e4: e[3], grad, frequences };
  },
};
