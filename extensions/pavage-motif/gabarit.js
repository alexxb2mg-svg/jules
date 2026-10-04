// Jules - gabarit "pavage-motif" : un motif geometrique simple (triangle bleu et pastille orange, volontairement
// dissymetrique pour que le retournement se voie) repete `repetitions` fois sur une rangee, sur `lignes` rangees.
// mode 0 = translation (le motif glisse, toujours dans le meme sens) ; mode 1 = symetrie axiale une fois sur deux
// (chaque motif est le reflet de son voisin dans un miroir vertical, axes en pointilles). 1 rangee = frise ;
// plusieurs rangees = pavement, papier peint, tissu imprime.
// Sources : Eduscol, ressources du cycle 3 « Espace et geometrie » (2016) : la symetrie axiale introduite en lien
// avec l'axe de symetrie ; Eduscol, ressources du cycle 4 « Geometrie plane » : « un pavage est une portion de
// plan dans laquelle un motif se repete regulierement par deux translations [...] Comme pour les frises, un motif
// associe [...] est un motif de base ; celui-ci peut lui-meme etre obtenu a partir d'un motif elementaire,
// reproduit par d'autres transformations (symetries, rotations) ». Aucune donnee chiffree n'est ecrite.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["pavage-motif"] = {
  dessiner(svg, valeurs) {
    const borne = (v, mini, maxi, defaut) => {
      const n = Number(v ?? defaut);
      return Math.round(Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : defaut)));
    };
    const repetitions = borne(valeurs.repetitions, 1, 6, 4);
    const mode = borne(valeurs.mode, 0, 1, 1);
    const lignes = borne(valeurs.lignes, 1, 4, 2);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const C = 48; // cote d'une case : constant, ce qui bouge est le nombre de motifs
    const x0 = (340 - repetitions * C) / 2, y0 = 40;

    svg.setAttribute("viewBox", "0 0 340 320");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Le motif dans une case [x, x + C] : triangle rectangle (angle droit en bas a gauche) et pastille en haut a
    // gauche ; `miroir` le retourne autour de l'axe vertical de la case.
    const motif = (x, y, miroir) => {
      const px = (u) => (miroir ? x + C - u : x + u);
      el("polygon", { points: `${px(6)},${y + C - 6} ${px(6)},${y + 14} ${px(C - 6)},${y + C - 6}`, fill: BLEU });
      el("circle", { cx: px(C - 13), cy: y + 13, r: 6, fill: ORANGE });
    };

    for (let r = 0; r < lignes; r++) {
      for (let i = 0; i < repetitions; i++) {
        const x = x0 + i * C, y = y0 + r * C;
        el("rect", { x, y, width: C, height: C, fill: "none", stroke: "#D5DAE1", "stroke-width": 2 });
        motif(x, y, mode === 1 && i % 2 === 1);
      }
    }
    // Le motif de base (premiere case) entoure en rouge.
    el("rect", { x: x0 + 1, y: y0 + 1, width: C - 2, height: C - 2, fill: "none", stroke: ROUGE, "stroke-width": 3, rx: 3 });

    const yb = y0 + lignes * C;
    if (repetitions >= 2) {
      if (mode === 1) {
        // Axes de symetrie : chaque frontiere entre deux cases est un miroir.
        for (let i = 1; i < repetitions; i++) {
          el("line", { x1: x0 + i * C, y1: y0 - 8, x2: x0 + i * C, y2: yb + 8, stroke: VERT, "stroke-width": 2, "stroke-dasharray": "5 4" });
        }
      } else {
        // Fleche de glissement sous la premiere rangee : du motif de base a son voisin.
        const ya = yb + 14;
        el("line", { x1: x0 + C / 2, y1: ya, x2: x0 + C * 1.5 - 9, y2: ya, stroke: VERT, "stroke-width": 3 });
        el("polygon", { points: `${x0 + C * 1.5},${ya} ${x0 + C * 1.5 - 10},${ya - 5} ${x0 + C * 1.5 - 10},${ya + 5}`, fill: VERT });
      }
    }

    let phrase;
    if (repetitions === 1) phrase = "Le motif de base, seul";
    else if (mode === 1) phrase = "Retourné une fois sur deux : symétrie";
    else phrase = "Le motif glisse : translation";
    el("text", { x: 170, y: 26, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, phrase);
    el("text", { x: 170, y: yb + 48, "font-size": 15, "text-anchor": "middle", fill: ENCRE },
      lignes === 1 ? "1 rangée : une frise" : "plusieurs rangées : un pavement");
    el("text", { x: 170, y: yb + 68, "font-size": 13, "text-anchor": "middle", fill: GRIS },
      mode === 1 && repetitions >= 2 ? "rouge = motif de base · vert = miroir" : "rouge = motif de base");
    return { repetitions, mode, lignes };
  },
};
