// Jules - gabarit "serie-statistique" : une serie de sept notes sur un axe gradue de 0 a 20 ; six notes sont
// fixes (8, 9, 10, 11, 12, 13), la septieme v se deplace.
// vue = 0 : la mediane (trait vert, valeur du milieu de la serie rangee) et la moyenne (triangle bleu, point
// d'equilibre) ; quand v s'eloigne, la moyenne suit, la mediane reste entre 10 et 11.
// vue = 1 : l'etendue (accolade orange du minimum au maximum) ; elle ne change que si v sort de [8 ; 13].
// Aucune valeur calculee n'est ecrite (ni moyenne, ni mediane, ni etendue) : l'eleve lit l'axe gradue.
// Definitions (moyenne = somme / effectif ; mediane d'un effectif impair n = valeur de rang (n + 1) / 2 de la
// serie rangee ; etendue = maximum - minimum) : programme de mathematiques du cycle 4, BO n° 31 du 30/07/2020,
// theme « Organisation et gestion de donnees » ; attendus de fin de 3e, eduscol 2019.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["serie-statistique"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const n = Number(v ?? defaut);
      return Math.min(max, Math.max(min, Math.round(Number.isFinite(n) ? n : defaut)));
    };
    const v = entier(valeurs.v, 14, 0, 20);
    const vue = entier(valeurs.vue, 0, 0, 1);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", VERT = "#2E7D32", ORANGE = "#E07B00";
    const X0 = 20, ECHELLE = 15, Y_AXE = 112; // 0 a 20 sur 300 px
    const x = (note) => X0 + note * ECHELLE;
    svg.setAttribute("viewBox", "0 0 340 180");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const fixes = [8, 9, 10, 11, 12, 13];
    const serie = [...fixes, v].sort((a, b) => a - b);
    const moyenne = serie.reduce((s, n) => s + n, 0) / serie.length;
    const mediane = serie[3]; // 7 valeurs : rang (7 + 1) / 2 = 4
    const mini = serie[0], maxi = serie[serie.length - 1];

    // Axe gradue : un trait par point, nombres tous les 5.
    el("line", { x1: X0 - 4, y1: Y_AXE, x2: x(20) + 4, y2: Y_AXE, stroke: ENCRE, "stroke-width": 2 });
    for (let n = 0; n <= 20; n++) {
      const grand = n % 5 === 0;
      el("line", { x1: x(n), y1: Y_AXE - (grand ? 7 : 4), x2: x(n), y2: Y_AXE + (grand ? 7 : 4), stroke: ENCRE, "stroke-width": 2 });
      if (grand) el("text", { x: x(n), y: Y_AXE + 24, "font-size": 14, "text-anchor": "middle", fill: ENCRE }, String(n));
    }

    // Les sept notes : pastilles empilees quand deux notes sont egales ; v en encre, plus grosse, marquee « v ».
    const hauteurs = {};
    const pastille = (note, mobile) => {
      const rang = hauteurs[note] || 0;
      hauteurs[note] = rang + 1;
      const cy = Y_AXE - 14 - rang * 17;
      el("circle", { cx: x(note), cy, r: mobile ? 8 : 7, fill: mobile ? ENCRE : GRIS, stroke: "#FFFFFF", "stroke-width": 2 });
      return cy;
    };
    for (const n of fixes) pastille(n, false);
    const yV = pastille(v, true);
    el("text", { x: x(v), y: yV - 13, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, "v");

    const etiquette = (cx) => Math.min(300, Math.max(40, cx));
    if (vue === 0) {
      // Mediane : trait vertical vert au-dessus de l'axe, mot en haut.
      el("line", { x1: x(mediane), y1: 34, x2: x(mediane), y2: Y_AXE + 8, stroke: VERT, "stroke-width": 3, "stroke-dasharray": "6 4" });
      el("text", { x: etiquette(x(mediane)), y: 24, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: VERT }, "médiane");
      // Moyenne : triangle bleu sous l'axe (point d'equilibre), mot dessous.
      const xm = x(moyenne);
      el("polygon", { points: `${xm},${Y_AXE + 30} ${xm - 9},${Y_AXE + 46} ${xm + 9},${Y_AXE + 46}`, fill: BLEU });
      el("text", { x: etiquette(xm), y: Y_AXE + 64, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: BLEU }, "moyenne");
    } else {
      // Etendue : barre orange du minimum au maximum, sous l'axe, avec deux butees.
      const y = Y_AXE + 38;
      el("line", { x1: x(mini), y1: y, x2: x(maxi), y2: y, stroke: ORANGE, "stroke-width": 4 });
      for (const n of [mini, maxi]) {
        el("line", { x1: x(n), y1: y - 9, x2: x(n), y2: y + 9, stroke: ORANGE, "stroke-width": 3 });
      }
      el("text", { x: etiquette((x(mini) + x(maxi)) / 2), y: y + 26, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: ORANGE }, "étendue");
    }
    return { v, vue, moyenne, mediane, etendue: maxi - mini };
  },
};
