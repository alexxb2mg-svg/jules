// Jules - gabarit "assemblage-cubes" : un pave fait de petits cubes, en perspective cavaliere (CM1).
// longueur, profondeur, hauteur = nombre de cubes dans chaque direction ; etages = etages gardes, en partant du
// bas : les etages du dessus enleves restent en pointilles, et l'on voit alors le dessus de l'etage du dessous,
// avec ses rangees de cubes qui etaient cachees. Le nombre total de cubes n'est jamais ecrit (l'eleve compte).
// Perspective cavaliere : fuyantes a 45 degres, coefficient de reduction 0,5 (convention du cycle 3).
// Source (notion) : programme de mathematiques du cycle 3, arrete du 10-4-2025 (BO n° 16 du 17/04/2025), espace
// et geometrie ; Eduscol, « Exemples de reussite » CM1 (2025), p. 22 (denombrer les cubes d'un assemblage).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["assemblage-cubes"] = {
  // dessiner(svg, valeurs) : longueur 1 a 5, profondeur 1 a 4, hauteur 1 a 4, etages 1 a 4 (cubes).
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => {
      const n = Math.round(Number(v ?? d));
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const lo = ent(valeurs.longueur, 3, 1, 5);
    const pr = ent(valeurs.profondeur, 2, 1, 4);
    const ha = ent(valeurs.hauteur, 2, 1, 4);
    const garde = Math.min(ha, ent(valeurs.etages, 4, 1, 4));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    const BLEU = "#1F4E8C", GRIS = "#6B7686";
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Echelle fixe (un cube a toujours la meme taille) ; le pave est centre d'apres ses trois dimensions,
    // jamais d'apres « etages » : enlever un etage ne deplace rien.
    const s = 44, K = 0.5 * Math.SQRT1_2; // fuyante : 0,5 x cos 45 = 0,5 x sin 45
    const largeur = lo * s + pr * s * K, haut = ha * s + pr * s * K;
    const X0 = 170 - largeur / 2, Y0 = 170 + haut / 2 - 6;
    const P = (x, y, z) => [X0 + x * s + y * s * K, Y0 - z * s - y * s * K];
    const poly = (pts, attrs) => el("polygon", { points: pts.map(([a, b]) => `${f(a)},${f(b)}`).join(" "), ...attrs });

    // Les etages enleves : les aretes visibles du pave entier au-dessus des etages gardes, en pointilles gris
    // (chaque arete tracee une seule fois, sinon deux pointilles superposes paraissent pleins).
    if (garde < ha) {
      const pointilles = { stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "6 5", "stroke-linecap": "round" };
      const arete = (p, q) => el("line", { x1: f(p[0]), y1: f(p[1]), x2: f(q[0]), y2: f(q[1]), ...pointilles });
      for (const [x, y] of [[0, 0], [lo, 0], [lo, pr]]) arete(P(x, y, garde), P(x, y, ha));
      arete(P(0, 0, ha), P(lo, 0, ha)); arete(P(lo, 0, ha), P(lo, pr, ha));
      arete(P(lo, pr, ha), P(0, pr, ha)); arete(P(0, pr, ha), P(0, 0, ha));
    }

    // Les cubes gardes, du fond vers l'avant, du bas vers le haut, de gauche a droite (peintre) :
    // chaque cube cache ce qui est derriere lui. Dessus clair, face avant moyenne, cote droit fonce.
    const trait = { stroke: BLEU, "stroke-width": 2, "stroke-linejoin": "round" };
    for (let y = pr - 1; y >= 0; y--) {
      for (let z = 0; z < garde; z++) {
        for (let x = 0; x < lo; x++) {
          poly([P(x + 1, y, z), P(x + 1, y + 1, z), P(x + 1, y + 1, z + 1), P(x + 1, y, z + 1)], { fill: "#7FA0CB", ...trait });
          poly([P(x, y, z + 1), P(x + 1, y, z + 1), P(x + 1, y + 1, z + 1), P(x, y + 1, z + 1)], { fill: "#E3ECF7", ...trait });
          poly([P(x, y, z), P(x + 1, y, z), P(x + 1, y, z + 1), P(x, y, z + 1)], { fill: "#B5CBE6", ...trait });
        }
      }
    }
    if (garde < ha) {
      el("text", { x: 170, y: 330, "font-size": 14, fill: GRIS, "text-anchor": "middle", "font-family": "sans-serif" }, "pointillés : les étages enlevés");
    }
    return { longueur: lo, profondeur: pr, hauteur: ha, etages: garde };
  },
};
