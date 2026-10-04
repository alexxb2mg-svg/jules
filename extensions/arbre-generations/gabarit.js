// Jules - gabarit "arbre-generations" : reproduction asexuee ou sexuee, generation apres generation.
// Curseurs : gen (generations affichees sous les parents, 1 a 4), mode (0 = asexuee : un parent, des clones ;
// 1 = sexuee : deux parents, des descendants tous differents).
// Chaque individu est une petite carte de 4 bandes : une bande = un gene, sa couleur = la version du gene (l'allele,
// bleu ou orange). Asexuee : chaque descendant a UN parent (un trait vers le haut) et recopie ses 4 bandes.
// Sexuee : chaque descendant a DEUX parents (deux traits vers le haut) et recoit, pour chaque gene, la version de
// l'un ou de l'autre, au hasard. Simplification assumee (un seul allele dessine par gene, 4 genes, 4 individus
// montres par generation) : on ne montre que l'idee clones / melange.
// Faits : programme de SVT cycle 4 (annexe 3, arrete du 17-7-2020, theme « Le vivant et son evolution » :
// reproduction sexuee et asexuee, gametes, fecondation) ; Eduscol, ressources SVT cycle 4 « diversite et
// stabilite genetique ». Aucune valeur numerique ecrite par la figure.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["arbre-generations"] = {
  dessiner(svg, valeurs) {
    const gen = Math.min(4, Math.max(1, Math.round(Number(valeurs.gen ?? 2))));
    const mode = Number(valeurs.mode ?? 0) >= 1 ? 1 : 0;
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

    const COULEURS = ["#1F4E8C", "#E07B00"]; // 0 = version bleue du gene, 1 = version orange
    const L = 44, H = 26; // taille d'un individu
    const Y0 = 52, PAS_Y = 56;
    const XS = [50, 130, 210, 290];

    // Sexuee : descendants fixes a la main (le meme dessin a chaque affichage). Un tirage au hasard peut tomber
    // sur un couple qui ne differe que d'un gene : ses seuls descendants possibles sont alors les parents eux-memes
    // (des clones). La table garantit, pour chaque generation : chaque gene vient de l'un des deux parents ;
    // 4 individus differents ; aucun identique a un individu de la ligne du dessus ; chaque couple de la ligne
    // differe d'au moins 2 genes (il peut donc avoir 2 descendants differents de lui-meme).
    const PARENTS_SEXUES = [[0, 0, 1, 0], [1, 1, 0, 1]];
    const DESCENDANTS_SEXUES = [
      [[0, 1, 1, 1], [1, 0, 0, 1], [1, 1, 1, 0], [0, 1, 0, 0]],
      [[1, 0, 1, 1], [0, 1, 0, 1], [0, 1, 1, 0], [1, 1, 0, 0]],
      [[1, 1, 1, 1], [0, 0, 1, 1], [0, 1, 0, 0], [1, 1, 1, 0]],
      [[0, 1, 1, 1], [1, 0, 1, 1], [0, 1, 1, 0], [1, 1, 0, 0]],
    ];

    const individu = (cx, cy, bandes) => {
      bandes.forEach((b, i) => {
        el("rect", { x: cx - L / 2 + (L / 4) * i, y: cy - H / 2, width: L / 4, height: H, fill: COULEURS[b] });
      });
      el("rect", { x: cx - L / 2, y: cy - H / 2, width: L, height: H, rx: 4, fill: "none", stroke: "#14243B", "stroke-width": 2 });
    };
    const trait = (x1, y1, x2, y2) =>
      el("line", { x1, y1: y1 + H / 2, x2, y2: y2 - H / 2, stroke: "#6B7686", "stroke-width": 2 });

    el("text", { x: 170, y: 22, "font-size": 15, "text-anchor": "middle", fill: "#14243B", "font-weight": "bold" },
      mode ? "sexuée : deux parents" : "asexuée : un seul parent");

    // Ligne 0 : les parents.
    let rangee;
    if (mode === 0) {
      rangee = [{ x: 170, bandes: [0, 1, 1, 0] }];
    } else {
      rangee = [{ x: 120, bandes: PARENTS_SEXUES[0] }, { x: 220, bandes: PARENTS_SEXUES[1] }];
      el("text", { x: 170, y: Y0 + 6, "font-size": 18, "text-anchor": "middle", fill: "#14243B", "font-weight": "bold" }, "+");
    }
    const dessines = [];
    rangee.forEach((p) => dessines.push([p.x, Y0, p.bandes]));

    for (let g = 1; g <= gen; g++) {
      const y = Y0 + PAS_Y * g, yh = y - PAS_Y;
      const suivante = [];
      XS.forEach((x, i) => {
        let bandes;
        if (mode === 0) {
          // Un parent : le seul parent de depart, puis le parent juste au-dessus.
          const parent = g === 1 ? rangee[0] : rangee[i];
          trait(parent.x, yh, x, y);
          bandes = parent.bandes.slice();
        } else {
          // Deux parents : le couple de depart, puis les paires (0,1) et (2,3) de la ligne du dessus.
          const couple = g === 1 ? rangee : (i < 2 ? [rangee[0], rangee[1]] : [rangee[2], rangee[3]]);
          couple.forEach((p) => trait(p.x, yh, x, y));
          // Pour chaque gene, la version de l'un des deux parents (table DESCENDANTS_SEXUES ci-dessus).
          bandes = DESCENDANTS_SEXUES[g - 1][i].slice();
        }
        suivante.push({ x, bandes });
      });
      rangee = suivante;
      rangee.forEach((p) => dessines.push([p.x, y, p.bandes]));
    }
    for (const [x, y, bandes] of dessines) individu(x, y, bandes);

    // Legende : une bande = un gene, et la conclusion visible.
    el("text", { x: 170, y: 318, "font-size": 14, "text-anchor": "middle", fill: "#14243B" },
      mode ? "chaque descendant est un mélange unique" : "tous identiques au parent : des clones");
    el("text", { x: 170, y: 336, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" },
      "une bande = un gène, sa couleur = sa version");
    return { gen, mode };
  },
};
