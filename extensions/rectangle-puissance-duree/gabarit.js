// Jules - gabarit "rectangle-puissance-duree" : l'energie consommee par un appareil est l'aire d'un rectangle
// dont la hauteur est la puissance (W) et la largeur la duree de fonctionnement (h) : E = P x t.
// Curseurs : puissance (W) et t (duree de fonctionnement, h). Le quadrillage gris compte des carreaux de 1 000 W x 1 h = 1 kWh ;
// l'energie n'est jamais ecrite (revele: false) : l'eleve compte ou estime les carreaux colores.
// Au-dessus du repere, un exemple d'appareil de cette puissance, d'apres les gammes du « Memo des couts annuels
// de consommation des appareils electriques » (formation ADEME-CNFPT, mars 2016) : lampe basse consommation
// 5 a 25 W, chargeur de telephone 6 a 8 W ; televiseur LCD 60 a 90 W, ordinateur 100 a 160 W ; micro-ondes 750 a 1 500 W ; bouilloire 1 000 a
// 2 000 W ; mini-four 2 000 a 2 500 W, table a induction 2 000 a 3 000 W. Hors de ces gammes, aucun exemple.
// (https://www.precarite-energie.org/IMG/pdf/memo_conso_equipements_electriques_mars_2016.pdf, verifie le 04/10/2026)
// Source de la relation : programme de physique-chimie du cycle 4 (BO n° 31 du 30/07/2020, annexe 3) :
// « Relation liant l'energie, la puissance electrique et la duree. »
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["rectangle-puissance-duree"] = {
  dessiner(svg, valeurs) {
    const P = Math.min(3000, Math.max(10, Number(valeurs.puissance ?? 1000)));
    const t = Math.min(10, Math.max(0.5, Number(valeurs.t ?? 1)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const f = (x) => Math.round(x * 10) / 10;
    const ENCRE = "#14243B", GRIS = "#6B7686", BLEU = "#1F4E8C", ORANGE = "#E07B00";
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    // Repere : duree 0 a 10 h (x de 60 a 320, 26 px par heure), puissance 0 a 3 000 W (y de 250 a 70, 60 px
    // par 1 000 W). Un carreau = 1 h x 1 000 W = 1 kWh.
    const X0 = 60, Y0 = 250, PXH = 26, PXKW = 60;
    const X = (h) => X0 + h * PXH, Y = (w) => Y0 - (w / 1000) * PXKW;

    // Rectangle de l'energie (sous le quadrillage pour que les carreaux restent visibles par-dessus).
    // Une puissance tres faible (10 W = 0,6 px) garde 3 px de haut pour que le rectangle se voie.
    const haut = Math.max(3, (P / 1000) * PXKW);
    el("rect", { x: X0, y: f(Y0 - haut), width: f(t * PXH), height: f(haut), fill: ORANGE, "fill-opacity": 0.55 });
    for (let h = 1; h <= 10; h++) el("line", { x1: X(h), y1: Y(3000), x2: X(h), y2: Y0, stroke: "#D5DAE1", "stroke-width": 2 });
    for (const w of [1000, 2000, 3000]) el("line", { x1: X0, y1: Y(w), x2: X(10), y2: Y(w), stroke: "#D5DAE1", "stroke-width": 2 });
    el("rect", { x: X0, y: f(Y0 - haut), width: f(t * PXH), height: f(haut), fill: "none", stroke: ORANGE, "stroke-width": 3 });

    // Hauteur = puissance (bleu, sur l'axe vertical) ; largeur = duree (bleu, sur l'axe horizontal).
    el("line", { x1: X0, y1: Y0, x2: X0, y2: f(Y0 - haut), stroke: BLEU, "stroke-width": 5 });
    el("line", { x1: X0, y1: Y0, x2: f(X(t)), y2: Y0, stroke: BLEU, "stroke-width": 5 });

    // Axes et graduations.
    el("line", { x1: X0, y1: Y0, x2: X(10) + 4, y2: Y0, stroke: ENCRE, "stroke-width": 2 });
    el("line", { x1: X0, y1: Y0, x2: X0, y2: Y(3000) - 6, stroke: ENCRE, "stroke-width": 2 });
    for (const w of [0, 1000, 2000, 3000]) {
      el("text", { x: X0 - 6, y: f(Y(w) + 5), "font-size": 13, "text-anchor": "end", fill: GRIS }, String(w));
    }
    for (const h of [0, 2, 4, 6, 8, 10]) {
      el("text", { x: X(h), y: Y0 + 19, "font-size": 13, "text-anchor": "middle", fill: GRIS }, String(h));
    }
    el("text", { x: X(10), y: Y0 + 38, "font-size": 13, "text-anchor": "end", fill: ENCRE }, "durée (h)");
    el("text", { x: 8, y: 56, "font-size": 13, fill: ENCRE }, "puissance (W)");
    el("text", { x: 8, y: 294, "font-size": 13, fill: GRIS }, "1 carreau = 1 kWh");

    // Exemple d'appareil (gammes ADEME, voir l'en-tete).
    let exemple = "";
    if (P <= 25) exemple = "lampe";
    else if (P >= 60 && P <= 160) exemple = "télé, ordinateur";
    else if (P >= 750 && P < 1000) exemple = "micro-ondes";
    else if (P >= 1000 && P < 2000) exemple = "bouilloire";
    else if (P >= 2000 && P <= 2500) exemple = "mini-four, plaque";
    else if (P > 2500) exemple = "plaque à induction";
    if (exemple) {
      el("text", { x: 330, y: 24, "font-size": 14, "text-anchor": "end", fill: BLEU }, "ex. : " + exemple);
    }
    return { puissance: P, t, kwh: (P * t) / 1000 };
  },
};
