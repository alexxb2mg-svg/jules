// Jules - gabarit "angle" : un angle ABC de sommet B qu'on ouvre ou ferme, et dont on allonge les cotes.
// Coin d'equerre en pointilles pour comparer a l'angle droit. Aucun degre affiche (hors programme de CM1).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["angle"] = {
  // dessiner(svg, valeurs) : ouverture de 10 a 170 (interne), longueur de 1 a 5 (longueur des cotes dessines).
  dessiner(svg, valeurs) {
    const ouverture = Math.min(170, Math.max(10, Number(valeurs.ouverture ?? 60)));
    const longueur = Math.min(5, Math.max(1, Number(valeurs.longueur ?? 3)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const borne = (v, mini, maxi) => Math.min(maxi, Math.max(mini, v));
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const B = { x: 170, y: 225 };             // le sommet
    const lg = 40 + longueur * 22;              // 62 a 150 px : la longueur ne change jamais l'ouverture
    const rad = (ouverture * Math.PI) / 180;
    const C = { x: B.x + lg, y: B.y };      // cote horizontal
    const A = { x: B.x + lg * Math.cos(rad), y: B.y - lg * Math.sin(rad) };
    const droit = ouverture === 90;

    // Le coin de l'equerre (angle droit de reference), en pointilles gris : un bord le long de [BC].
    el("polygon", {
      points: `${B.x},${B.y} ${B.x + 85},${B.y} ${B.x},${B.y - 150}`,
      fill: "#6B7686", "fill-opacity": 0.08, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "6 5",
    });

    // L'ouverture : un arc de rayon fixe (il reste le meme quand on allonge les cotes), ou le petit carre.
    const r = 34;
    if (droit) {
      el("path", {
        d: `M${B.x + 18},${B.y} L${B.x + 18},${B.y - 18} L${B.x},${B.y - 18}`,
        fill: "none", stroke: "#C8102E", "stroke-width": 3,
      });
    } else {
      const fin = { x: B.x + r * Math.cos(rad), y: B.y - r * Math.sin(rad) };
      el("path", {
        d: `M${B.x},${B.y} L${B.x + r},${B.y} A${r},${r} 0 0 0 ${fin.x.toFixed(1)},${fin.y.toFixed(1)} Z`,
        fill: "#C8102E", "fill-opacity": 0.15, stroke: "#C8102E", "stroke-width": 3,
      });
    }

    // Les deux cotes, en bleu.
    el("line", { x1: B.x, y1: B.y, x2: C.x, y2: C.y, stroke: "#1F4E8C", "stroke-width": 4, "stroke-linecap": "round" });
    el("line", { x1: B.x, y1: B.y, x2: A.x.toFixed(1), y2: A.y.toFixed(1), stroke: "#1F4E8C", "stroke-width": 4, "stroke-linecap": "round" });
    el("circle", { cx: B.x, cy: B.y, r: 5, fill: "#E07B00" });

    // Les lettres : B, le sommet, en orange (comme dans la fiche) ; A et C au bout des cotes.
    const lettre = (x, y, t, couleur) => el("text", {
      x: borne(x, 12, 328).toFixed(1), y: borne(y, 20, 330).toFixed(1), "font-size": 18, "font-weight": 700,
      fill: couleur, "text-anchor": "middle", "font-family": "sans-serif",
    }, t);
    lettre(B.x - 6, B.y + 26, "B", "#E07B00");
    lettre(C.x + 4, C.y + 26, "C", "#14243B");
    lettre(A.x + 20 * Math.cos(rad), A.y - 20 * Math.sin(rad) + 6, "A", "#14243B");

    // Legende fixe du coin d'equerre.
    el("text", { x: 20, y: 320, "font-size": 14, fill: "#6B7686", "font-family": "sans-serif" }, "pointillés : le coin de l'équerre");
    return { ouverture, longueur, droit };
  },
};
