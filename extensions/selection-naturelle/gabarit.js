// Jules - gabarit "selection-naturelle" : la phalene du bouleau, papillons clairs et sombres sur des troncs.
// Curseurs : gen (generations ecoulees, 0 a 20), pression (avantage de la forme sombre : 0 aucun, troncs clairs ;
// 1 a 3 troncs de plus en plus noircis par la suie, les papillons clairs se voient et sont plus manges).
// Modele simplifie (selection sur une population, ordres de grandeur) : part de sombres p0 = 0,10 au depart
// (forme rare, apparue par mutation) ; a chaque generation les clairs ont une survie relative 1 - s avec
// s = 0,15 x pression ; p' = p / (p + (1 - p)(1 - s)). Avec s = 0,30 (pression 2), les sombres sont
// 1 / 0,7 ≈ 1,4 fois plus « aptes » et deviennent majoritaires en moins de 10 generations : ordre de grandeur de
// l'estimation de J.B.S. Haldane (1924, « A mathematical theory of natural and artificial selection », Part I) pour
// la phalene a Manchester, environ 1,5 fois plus apte pour passer de 2 % (1848) a 95 % (1895), une generation par
// an ; frequence relevee de 98 % en 1895 (Wikipedia en, « Peppered moth evolution », section History).
// Mutation unique d'origine de la forme sombre (carbonaria) : A.E. van't Hof et al., 2011, Science 332, 958-960 ;
// element transposable insere dans le gene cortex : van't Hof et al., 2016, Nature 534, 102-105.
// Fiche : Vikidia « Selection naturelle ».
// La figure ne fait que dessiner 20 papillons (part arrondie au papillon pres) et une barre : aucune valeur
// ecrite hormis le numero de generation.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["selection-naturelle"] = {
  dessiner(svg, valeurs) {
    const gen = Math.min(20, Math.max(0, Math.round(Number(valeurs.gen ?? 0))));
    const pression = Math.min(3, Math.max(0, Math.round(Number(valeurs.pression ?? 2))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Part de papillons sombres apres `gen` generations.
    const s = 0.15 * pression;
    let p = 0.1;
    for (let g = 0; g < gen; g++) p = p / (p + (1 - p) * (1 - s));
    const N = 20;
    const sombres = Math.round(N * p);

    const SOMBRE = "#14243B", CLAIR = "#F4EFE2";
    const TRONCS = ["#E6E0D2", "#B5AFA3", "#87827A", "#5F5B55"];

    el("text", { x: 170, y: 22, "font-size": 15, "text-anchor": "middle", fill: "#14243B", "font-weight": "bold" },
      gen === 0 ? "au départ" : `génération ${gen}`);

    // Le tronc (l'ecorce), plus ou moins noircie.
    el("rect", { x: 30, y: 34, width: 280, height: 210, rx: 10, fill: TRONCS[pression], stroke: "#6B7686", "stroke-width": 2 });
    for (const x of [80, 150, 220, 270]) {
      el("line", { x1: x, y1: 40, x2: x - 6, y2: 238, stroke: "#6B7686", "stroke-width": 2, opacity: 0.35 });
    }

    // 20 papillons ; un ordre fixe disperse les sombres sur le tronc.
    const ORDRE = [7, 13, 2, 18, 10, 4, 16, 0, 11, 6, 19, 3, 14, 9, 1, 17, 5, 12, 8, 15];
    const estSombre = new Array(N).fill(false);
    for (let k = 0; k < sombres; k++) estSombre[ORDRE[k]] = true;
    for (let i = 0; i < N; i++) {
      const cx = 66 + 52 * (i % 5), cy = 64 + 50 * Math.floor(i / 5);
      const fill = estSombre[i] ? SOMBRE : CLAIR;
      el("ellipse", { cx: cx - 10, cy, rx: 11, ry: 9, fill, stroke: "#6B7686", "stroke-width": 2 });
      el("ellipse", { cx: cx + 10, cy, rx: 11, ry: 9, fill, stroke: "#6B7686", "stroke-width": 2 });
      el("line", { x1: cx, y1: cy - 9, x2: cx, y2: cy + 9, stroke: "#14243B", "stroke-width": 3 });
    }

    // Barre : part de chaque forme dans la population.
    const BX = 30, BL = 280, BY = 260, BH = 26;
    const part = (BL * sombres) / N;
    if (sombres > 0) el("rect", { x: BX, y: BY, width: part, height: BH, fill: SOMBRE });
    if (sombres < N) el("rect", { x: BX + part, y: BY, width: BL - part, height: BH, fill: CLAIR });
    el("rect", { x: BX, y: BY, width: BL, height: BH, fill: "none", stroke: "#6B7686", "stroke-width": 2 });
    el("text", { x: BX, y: BY + 46, "font-size": 14, fill: "#14243B", "font-weight": "bold" }, "◀ sombres");
    el("text", { x: BX + BL, y: BY + 46, "font-size": 14, "text-anchor": "end", fill: "#6B7686", "font-weight": "bold" }, "clairs ▶");
    el("text", { x: 170, y: 334, "font-size": 13, "text-anchor": "middle", fill: "#14243B" },
      pression === 0 ? "troncs clairs : aucune forme avantagée" : "troncs noircis : les clairs se voient");
    return { gen, pression, sombres };
  },
};
