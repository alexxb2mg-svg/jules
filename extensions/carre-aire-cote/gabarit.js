// Jules - gabarit "carre-aire-cote" : un carre d'aire a (en carreaux de 1 x 1) pose sur un quadrillage, avec une
// regle graduee sous son cote. Le cote vaut la racine carree de a : il tombe pile sur une graduation (marque verte)
// seulement quand a est un carre parfait, sinon il s'arrete entre deux graduations (marque orange).
// Seule l'aire (la donnee) est ecrite ; la racine carree se lit sur la regle, elle n'est jamais ecrite.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["carre-aire-cote"] = {
  // dessiner(svg, valeurs) : a = aire du carre, entier de 0 a 144 (cote de 0 a 12 carreaux).
  dessiner(svg, valeurs) {
    const brut = Number(valeurs.a ?? 49);
    const a = Math.min(144, Math.max(0, Math.round(Number.isFinite(brut) ? brut : 49)));
    const cote = Math.sqrt(a);
    const parfait = Number.isInteger(cote);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (x) => x.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", VERT = "#2E7D32", ORANGE = "#E07B00";
    const U = 22, X0 = 40, BAS = 290, N = 12; // 12 carreaux de 22 px : de x = 40 a 304, de y = 26 a 290
    el("text", { x: X0, y: 18, "font-size": 15, "font-weight": "bold", fill: ENCRE, "font-family": "sans-serif" },
      `aire : ${a} carreau${a > 1 ? "x" : ""}`);

    // Le quadrillage en carreaux.
    for (let i = 0; i <= N; i++) {
      el("line", { x1: X0 + i * U, y1: BAS - N * U, x2: X0 + i * U, y2: BAS, stroke: "#E3E8EF", "stroke-width": 1 });
      el("line", { x1: X0, y1: BAS - i * U, x2: X0 + N * U, y2: BAS - i * U, stroke: "#E3E8EF", "stroke-width": 1 });
    }

    // Le carre, pose dans le coin en bas a gauche.
    const c = cote * U;
    if (a > 0) {
      el("rect", { x: X0, y: f(BAS - c), width: f(c), height: f(c), fill: "#DCE8F6", "fill-opacity": 0.85, stroke: BLEU, "stroke-width": 3 });
      // Les carreaux entiers du carre, en traits fins : on peut les compter.
      for (let i = 1; i < cote; i++) {
        el("line", { x1: X0 + i * U, y1: f(BAS - c), x2: X0 + i * U, y2: BAS, stroke: "#8FA6C4", "stroke-width": 1 });
        el("line", { x1: X0, y1: BAS - i * U, x2: f(X0 + c), y2: BAS - i * U, stroke: "#8FA6C4", "stroke-width": 1 });
      }
    }

    // La regle sous le cote du bas : graduations 0 a 12, en carreaux.
    const R = 300;
    el("rect", { x: X0 - 10, y: R, width: N * U + 20, height: 36, rx: 4, fill: "#FFF7E6", stroke: GRIS, "stroke-width": 2 });
    for (let i = 0; i <= N; i++) {
      el("line", { x1: X0 + i * U, y1: R, x2: X0 + i * U, y2: R + 10, stroke: ENCRE, "stroke-width": 2 });
      el("text", { x: X0 + i * U, y: R + 28, "font-size": 13, fill: ENCRE, "text-anchor": "middle", "font-family": "sans-serif" }, String(i));
    }
    // Le bout du cote, reporte sur la regle : vert s'il tombe sur une graduation, orange sinon.
    const repere = parfait ? VERT : ORANGE;
    el("line", { x1: f(X0 + c), y1: BAS, x2: f(X0 + c), y2: R + 12, stroke: repere, "stroke-width": 3 });
    el("circle", { cx: f(X0 + c), cy: R + 4, r: 5, fill: repere });
    return { a, cote, parfait };
  },
};
