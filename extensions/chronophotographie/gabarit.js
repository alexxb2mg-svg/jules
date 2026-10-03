// Jules - gabarit "chronophotographie" : positions successives d'un passager de train, une par seconde.
// Curseurs : v (vitesse de depart, m/s), e (evolution : -1 ralenti, 0 uniforme, 1 accelere),
// r (referentiel : 0 = vu du sol, 1 = vu du train). Vu du train, le passager reste au meme endroit et
// c'est l'arbre (lie au sol) qui recule, avec les memes ecarts.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["chronophotographie"] = {
  dessiner(svg, valeurs) {
    const v = Math.min(10, Math.max(1, Number(valeurs.v ?? 5)));
    const e = Math.sign(Number(valeurs.e ?? 0));
    const r = Number(valeurs.r ?? 0) >= 0.5 ? 1 : 0;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const BLEU = "#1F4E8C", VERT = "#2E7D32", GRIS = "#6B7686", ENCRE = "#14243B";
    // 6 positions, 1 par seconde : la vitesse pendant la seconde k vaut v x (1 + 0,15 k) si accelere,
    // v x (1 - 0,15 k) si ralenti (toujours > 0). Echelle fixe (on compare d'un reglage a l'autre) :
    // le plus long trajet (v = 10, accelere : 10 x 6,5 = 65 m) occupe 292,5 px, soit 4,5 px par metre.
    const ECHELLE = 4.5, X0 = 25;
    const ecarts = [0, 1, 2, 3, 4].map((k) => v * (1 + 0.15 * e * k));
    const cumul = [0];
    for (const d of ecarts) cumul.push(cumul[cumul.length - 1] + d);

    svg.setAttribute("viewBox", "0 0 340 250");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 26, "font-size": 17, "font-weight": "bold", "text-anchor": "middle", fill: ENCRE },
      r === 0 ? "Vu du sol" : "Vu du train");

    // Rangee du passager (bleu).
    el("text", { x: X0 - 8, y: 64, "font-size": 14, fill: BLEU }, "passager");
    if (r === 0) {
      cumul.forEach((d, k) => {
        el("circle", { cx: X0 + d * ECHELLE, cy: 92, r: 5, fill: k === 0 ? "#FFFFFF" : BLEU, stroke: BLEU, "stroke-width": 2 });
      });
    } else {
      el("circle", { cx: X0, cy: 92, r: 5, fill: BLEU, stroke: BLEU, "stroke-width": 2 });
      el("text", { x: X0 + 16, y: 97, "font-size": 14, fill: BLEU }, "reste au même endroit");
    }

    // Sol et arbre (vert) : fixe vu du sol, recule vu du train (meme ecarts, sens oppose).
    el("line", { x1: 10, y1: 190, x2: 330, y2: 190, stroke: GRIS, "stroke-width": 3 });
    const arbre = (x, plein) => {
      el("line", { x1: x, y1: 190, x2: x, y2: 166, stroke: VERT, "stroke-width": 3 });
      el("circle", { cx: x, cy: 160, r: plein ? 9 : 6, fill: plein ? VERT : "#FFFFFF", stroke: VERT, "stroke-width": 2 });
    };
    if (r === 0) {
      arbre(300, true);
      el("text", { x: 300, y: 140, "font-size": 14, "text-anchor": "middle", fill: VERT }, "arbre");
    } else {
      const XA = 315;
      cumul.forEach((d, k) => arbre(XA - d * ECHELLE, k === 5));
      el("text", { x: XA - cumul[5] * ECHELLE, y: 140, "font-size": 14, "text-anchor": "middle", fill: VERT }, "arbre");
      // fleche : l'arbre recule
      const xb = XA - cumul[5] * ECHELLE;
      el("line", { x1: XA, y1: 205, x2: xb + 8, y2: 205, stroke: VERT, "stroke-width": 2 });
      el("path", { d: `M${xb},205 l9,-5 l0,10 z`, fill: VERT });
    }
    el("text", { x: 170, y: 238, "font-size": 14, "text-anchor": "middle", fill: GRIS },
      "1 point par seconde · le blanc = départ");
    return { v, e, r, distance: Math.round(cumul[5] * 10) / 10 };
  },
};
