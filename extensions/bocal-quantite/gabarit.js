// Jules - gabarit "bocal-quantite" : un bocal qui se remplit de pommes (nom denombrable : on peut les compter)
// ou d'eau (nom indenombrable : on ne peut pas la compter). Valeurs : n (quantite, 0 a 20 : nombre de pommes, ou
// niveau d'eau en vingtiemes du bocal) et compt (1 = pommes, denombrable ; 0 = eau, indenombrable).
// La figure n'ecrit pas le quantifieur (a few, a little, many, much, a lot of) : c'est l'eleve qui le choisit,
// les lectures de la fiche le confirment. Elle ecrit seulement le nom et s'il se compte.
// Faits : a few / many + denombrable pluriel, a little / much + indenombrable, a lot of avec les deux ; much et
// many surtout en question et negation (Cambridge Grammar, « Little, a little, few, a few » et « Much, many, a lot
// of, lots of », dictionary.cambridge.org/grammar/british-grammar/, consulte le 04/10/2026) ; water et apple :
// Wiktionary (water « uncountable » au sens de la substance, apple « countable »).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["bocal-quantite"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32";
    const brut = Number(valeurs.n ?? 3);
    const n = Math.min(20, Math.max(0, Math.round(Number.isFinite(brut) ? brut : 3)));
    const compt = Number(valeurs.compt ?? 1) >= 1 ? 1 : 0;
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 310");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Bocal : interieur de x 92 a 248, du haut (y 64) au fond (y 268) ; couvercle gris au-dessus.
    const G = 92, D = 248, HAUT = 64, FOND = 268;
    el("rect", { x: 110, y: 40, width: 120, height: 18, rx: 4, fill: "#D5DAE1", stroke: GRIS, "stroke-width": 2 });

    if (compt === 0 && n > 0) {
      // Eau : un niveau qui monte, sans graduation (on ne compte pas l'eau).
      const h = ((FOND - HAUT - 8) * n) / 20;
      el("rect", { x: G + 2, y: (FOND - h).toFixed(1), width: D - G - 4, height: h.toFixed(1), rx: 10, fill: "#BFD7EF" });
      el("line", { x1: G + 4, y1: (FOND - h).toFixed(1), x2: D - 4, y2: (FOND - h).toFixed(1), stroke: BLEU, "stroke-width": 3, "stroke-linecap": "round" });
    }

    // Paroi du bocal (dessinee apres l'eau pour rester nette).
    el("path", { d: `M${G + 18},${HAUT - 6} L${G + 18},${HAUT} Q${G},${HAUT} ${G},${HAUT + 22} L${G},${FOND - 12} Q${G},${FOND} ${G + 14},${FOND} L${D - 14},${FOND} Q${D},${FOND} ${D},${FOND - 12} L${D},${HAUT + 22} Q${D},${HAUT} ${D - 18},${HAUT} L${D - 18},${HAUT - 6}`,
      fill: "none", stroke: BLEU, "stroke-width": 3, "stroke-linejoin": "round" });

    if (compt === 1) {
      // Pommes : rangees de 5, du fond vers le haut ; chacune se voit et se compte.
      for (let i = 0; i < n; i++) {
        const cx = 112 + (i % 5) * 29, cy = FOND - 18 - Math.floor(i / 5) * 29;
        el("circle", { cx, cy, r: 12, fill: ROUGE, stroke: ENCRE, "stroke-width": 2 });
        el("line", { x1: cx, y1: cy - 11, x2: cx + 2, y2: cy - 17, stroke: ENCRE, "stroke-width": 2, "stroke-linecap": "round" });
        el("ellipse", { cx: cx + 6, cy: cy - 15, rx: 4, ry: 2.5, fill: VERT });
      }
    }

    // Le nom et sa nature (jamais le quantifieur).
    el("text", { x: 170, y: 296, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: compt ? ROUGE : BLEU },
      compt ? "apples : on peut les compter" : "water : on ne la compte pas");
    return { n, compt };
  },
};
