// Jules - gabarit "caricature-grossissement" : un visage simple dont UN trait (nez, oreilles ou bouche) grossit
// avec le curseur grossissement (1 = portrait fidele, 3 = trait trois fois plus grand) ; le curseur trait choisit
// lequel (1 nez, 2 oreilles, 3 bouche). En bas, une reglette « fidèle → caricature → exagération » montre que la
// satire est une question de degre.
// Faits : le grossissement (l'exageration d'un trait physique ou moral) est le procede de base de la caricature et
// de la satire (programme de francais du cycle 4, 3e, questionnement « Dénoncer les travers de la société » ;
// CNRTL, « caricature » : « portrait en charge [...] mettant exagérément l'accent, dans une intention plaisante ou
// satirique, sur un trait jugé caractéristique du sujet »). Les seuils 1,5 et 2,5 de la reglette sont des reperes
// de lecture, pas une regle.
// Aucun nombre ecrit : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["caricature-grossissement"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const borne = (v, min, max, d) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : d;
    };
    const grossissement = borne(valeurs.grossissement, 1, 3, 1);
    const trait = Math.round(borne(valeurs.trait, 1, 3, 1));
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const etat = grossissement < 1.5 ? ["portrait fidèle", VERT] : grossissement <= 2.5 ? ["caricature", ORANGE]
      : ["exagération extrême", ROUGE];
    // Le trait grossi est dessine en couleur des qu'il depasse sa taille normale ; les autres restent a l'encre.
    const k = (n) => (n === trait ? grossissement : 1);
    const couleur = (n) => (n === trait && grossissement > 1 ? etat[1] : ENCRE);

    svg.setAttribute("viewBox", "0 0 340 330");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 26, "font-size": 17, "font-weight": "bold", "text-anchor": "middle", fill: etat[1] }, etat[0]);

    const CX = 170, CY = 160;
    // Oreilles (dessinees avant la tete pour passer derriere).
    const ko = k(2);
    for (const s of [-1, 1]) {
      el("ellipse", { cx: CX + s * (78 + 8 * ko), cy: CY, rx: 12 * ko, ry: 22 * ko, fill: "#FFFFFF", stroke: couleur(2), "stroke-width": 3 });
    }
    // Tete, cheveux, yeux, sourcils.
    el("ellipse", { cx: CX, cy: CY, rx: 80, ry: 100, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 3 });
    el("path", { d: `M${CX - 72},${CY - 40} Q${CX},${CY - 130} ${CX + 72},${CY - 40}`, fill: "none", stroke: GRIS, "stroke-width": 3 });
    for (const s of [-1, 1]) {
      el("circle", { cx: CX + s * 30, cy: CY - 25, r: 7, fill: ENCRE });
      el("line", { x1: CX + s * 18, y1: CY - 42, x2: CX + s * 42, y2: CY - 44, stroke: ENCRE, "stroke-width": 3 });
    }
    // Nez : triangle dont la longueur et la largeur suivent le grossissement.
    const kn = k(1);
    el("path", { d: `M${CX},${CY - 15} L${CX - 10 * kn},${CY + 18 * kn} L${CX + 10 * kn},${CY + 18 * kn} Z`,
      fill: "#FFFFFF", stroke: couleur(1), "stroke-width": 3, "stroke-linejoin": "round" });
    // Bouche : arc de sourire, place sous le nez.
    const kb = k(3);
    const yb = CY + Math.max(45, 18 * kn + 22);
    el("path", { d: `M${CX - 22 * kb},${yb} Q${CX},${yb + 16 * kb} ${CX + 22 * kb},${yb}`, fill: "none", stroke: couleur(3), "stroke-width": 3,
      "stroke-linecap": "round" });

    // Reglette du degre : fidele (1 a 1,5), caricature (1,5 a 2,5), exageration (2,5 a 3).
    const X = (g) => 50 + (g - 1) * 120;
    const yR = 296;
    for (const [de, a, c] of [[1, 1.5, VERT], [1.5, 2.5, ORANGE], [2.5, 3, ROUGE]]) {
      el("rect", { x: X(de), y: yR, width: X(a) - X(de), height: 10, fill: c, "fill-opacity": 0.35 });
    }
    el("rect", { x: X(1), y: yR, width: X(3) - X(1), height: 10, fill: "none", stroke: ENCRE, "stroke-width": 2 });
    el("path", { d: `M${X(grossissement)},${yR - 2} l-7,-10 l14,0 z`, fill: etat[1] });
    el("text", { x: X(1), y: yR + 26, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "fidèle");
    el("text", { x: X(3), y: yR + 26, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "exagéré");
    return { grossissement, trait };
  },
};
