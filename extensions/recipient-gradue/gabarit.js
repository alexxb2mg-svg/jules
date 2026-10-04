// Jules - gabarit "recipient-gradue" : trois pichets d'un litre gradues tous les 50 mL (grand trait tous les
// 100 mL) ; le curseur v (en mL, 0 a 3 000) verse le liquide, les pichets se remplissent l'un apres l'autre.
// Une echelle en mL a gauche (100 a 1 000), « 1 L » au-dessus de chaque pichet. La quantite versee n'est jamais
// ecrite : l'eleve lit la graduation et compte les pichets pleins (revele false).
// Faits (EX-205) : 1 L = 10 dL = 100 cL = 1 000 mL ; 500 mL = un demi-litre.
// Sources : programme de mathematiques du cycle 3, arrete du 10-4-2025, BO n° 16 du 17/04/2025, p. 16 (unites de
// contenance) ; Eduscol, « Exemples pour la mise en oeuvre du programme de mathematiques en CM1 » (2025), p. 17 ;
// les deux sont deja cites par la fiche cm1-contenances.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["recipient-gradue"] = {
  // dessiner(svg, valeurs) : v de 0 a 3 000 mL, arrondi a 50 mL (une graduation).
  dessiner(svg, valeurs) {
    const brut = Number(valeurs.v ?? 750);
    const v = Math.min(3000, Math.max(0, Math.round((Number.isFinite(brut) ? brut : 750) / 50) * 50));
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 300");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // 1 000 mL = 200 px : 50 mL = 10 px. Fond des pichets a y = 262, trait « 1 L » a y = 62.
    const FOND = 262, PX = 0.2;
    const Y = (ml) => FOND - ml * PX;
    const LARG = 82, X = [62, 156, 250];

    // L'echelle en mL, a gauche, alignee sur les graduations des pichets.
    el("text", { x: 50, y: 34, "font-size": 13, "font-weight": "bold", fill: GRIS, "text-anchor": "end", "font-family": "sans-serif" }, "mL");
    for (let ml = 100; ml <= 1000; ml += 100) {
      el("text", { x: 50, y: f(Y(ml) + 4.5), "font-size": 13, fill: GRIS, "text-anchor": "end", "font-family": "sans-serif" }, ml === 1000 ? "1 000" : String(ml));
    }

    X.forEach((x0, i) => {
      const dedans = Math.min(1000, Math.max(0, v - 1000 * i));
      // Le liquide, puis sa surface d'un trait bleu fonce.
      if (dedans > 0) {
        el("rect", { x: x0, y: f(Y(dedans)), width: LARG, height: f(dedans * PX), fill: "#9CC0E8" });
        el("line", { x1: x0, y1: f(Y(dedans)), x2: x0 + LARG, y2: f(Y(dedans)), stroke: BLEU, "stroke-width": 3 });
      }
      // Les graduations, sur le bord gauche du pichet : grand trait tous les 100 mL, petit tous les 50 mL.
      for (let ml = 50; ml <= 1000; ml += 50) {
        const grand = ml % 100 === 0;
        el("line", { x1: x0, y1: f(Y(ml)), x2: x0 + (grand ? 22 : 12), y2: f(Y(ml)), stroke: ENCRE, "stroke-width": grand ? 2.5 : 2 });
      }
      // Le pichet : parois et fond, un peu plus haut que le trait d'1 L, avec un bec a droite.
      el("path", {
        d: `M ${x0} ${Y(1000) - 14} L ${x0} ${FOND} L ${x0 + LARG} ${FOND} L ${x0 + LARG} ${Y(1000) - 6} L ${x0 + LARG + 6} ${Y(1000) - 16}`,
        fill: "none", stroke: ENCRE, "stroke-width": 3, "stroke-linejoin": "round", "stroke-linecap": "round",
      });
      el("text", { x: x0 + LARG / 2, y: f(Y(1000) - 22), "font-size": 14, "font-weight": "bold", fill: ENCRE, "text-anchor": "middle", "font-family": "sans-serif" }, "1 L");
    });

    el("text", { x: 170, y: 290, "font-size": 13, fill: GRIS, "text-anchor": "middle", "font-family": "sans-serif" }, "un pichet plein : 1 L = 1 000 mL = 100 cL");
    return { v, pleins: Math.floor(v / 1000) };
  },
};
