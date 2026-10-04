// Jules - gabarit "grille-deplacement" : un robot execute un programme de deplacement sur un quadrillage, une
// instruction a la fois (CM1 mathematiques : coder des deplacements ; CM1 anglais : suivre un chemin).
// Instructions du robot (vu de dessus) : avancer d'une case, tourner a gauche ou a droite d'un quart de tour SUR
// PLACE (le robot ne change pas de case). Le robot porte sa gauche et sa droite (G et D ; L et R pour le
// parcours en anglais) : elles tournent avec lui, ce n'est pas toujours la gauche de l'eleve.
// parcours 1 a 3 : programmes de 5, 7 et 10 instructions. parcours 4 : chemin en anglais (go straight on, turn
// left, turn right), arrivee devant la boulangerie (bakery), « on your right ».
// Sous le quadrillage, le programme en pictogrammes : instructions faites en gris, celle qui vient d'etre
// executee entouree d'orange. Le chemin parcouru est trace en orange.
// Source : programme de mathematiques du cycle 3, arrete du 10-4-2025 (BO n° 16 du 17/04/2025), reperage et
// deplacements, programmation d'un robot ; programme de langues vivantes du cycle 3 (consignes et itineraires).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["grille-deplacement"] = {
  // dessiner(svg, valeurs) : parcours 1 a 4, etape 0 (rien n'est fait) a 10 (borne a la longueur du programme).
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => {
      const n = Math.round(Number(v ?? d));
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const parcours = ent(valeurs.parcours, 1, 1, 4);
    // Programmes : A = avancer d'une case, G = quart de tour a gauche, D = quart de tour a droite.
    // Depart [colonne, ligne] et direction (0 nord, 1 est, 2 sud, 3 ouest) ; tous restent dans la grille 7 x 5.
    const PROGRAMMES = {
      1: { col: 1, lig: 3, dir: 1, code: "AAGAA" },
      2: { col: 0, lig: 4, dir: 0, code: "AADAADA" },
      3: { col: 0, lig: 4, dir: 1, code: "AAGAADAAGA" },
      4: { col: 2, lig: 4, dir: 0, code: "AGADA" },
    };
    const prog = PROGRAMMES[parcours];
    const anglais = parcours === 4;
    const etape = Math.min(prog.code.length, ent(valeurs.etape, 0, 0, 10));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00", VERT = "#2E7D32";
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Le quadrillage : 7 colonnes, 5 lignes, cases de 40 px.
    const CASE = 40, GX = 30, GY = 12, NC = 7, NL = 5;
    const centre = (c, r) => ({ x: GX + c * CASE + CASE / 2, y: GY + r * CASE + CASE / 2 });
    el("rect", { x: GX, y: GY, width: NC * CASE, height: NL * CASE, fill: "#F7F9FC", stroke: GRIS, "stroke-width": 2 });
    for (let i = 1; i < NC; i++) el("line", { x1: GX + i * CASE, y1: GY, x2: GX + i * CASE, y2: GY + NL * CASE, stroke: "#C9D2DE", "stroke-width": 1.5 });
    for (let j = 1; j < NL; j++) el("line", { x1: GX, y1: GY + j * CASE, x2: GX + NC * CASE, y2: GY + j * CASE, stroke: "#C9D2DE", "stroke-width": 1.5 });

    // Execution du programme jusqu'a l'etape choisie.
    const DX = [0, 1, 0, -1], DY = [-1, 0, 1, 0];
    let col = prog.col, lig = prog.lig, dir = prog.dir;
    const chemin = [centre(col, lig)];
    for (let i = 0; i < etape; i++) {
      const ins = prog.code[i];
      if (ins === "A") { col += DX[dir]; lig += DY[dir]; chemin.push(centre(col, lig)); }
      else if (ins === "G") dir = (dir + 3) % 4;
      else dir = (dir + 1) % 4;
    }

    // La boulangerie du parcours en anglais : a droite du personnage a l'arrivee.
    if (anglais) {
      const c22 = centre(2, 2), b = { x: c22.x + 6, y: c22.y }; // decalee : la pastille R reste libre
      el("rect", { x: b.x - 17, y: b.y - 12, width: 34, height: 26, fill: "#FBE3C4", stroke: ORANGE, "stroke-width": 2 });
      el("polygon", { points: `${b.x - 20},${b.y - 12} ${b.x},${b.y - 22} ${b.x + 20},${b.y - 12}`, fill: ORANGE });
      el("text", { x: b.x, y: b.y - 27, "font-size": 13, "font-weight": 700, fill: ORANGE, "text-anchor": "middle", "font-family": "sans-serif" }, "bakery");
    }

    // Le depart (carre gris) et le chemin parcouru (orange).
    const d0 = centre(prog.col, prog.lig);
    el("rect", { x: d0.x - 15, y: d0.y - 15, width: 30, height: 30, rx: 4, fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "4 3" });
    if (chemin.length > 1) {
      el("polyline", { points: chemin.map((p) => `${f(p.x)},${f(p.y)}`).join(" "), fill: "none", stroke: ORANGE, "stroke-width": 5, "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-opacity": 0.85 });
    }

    // Le robot : une fleche bleue qui montre ou il regarde, sa gauche et sa droite marquees.
    const p = centre(col, lig);
    const ux = DX[dir], uy = DY[dir];        // devant
    const gx = uy, gy = -ux;                 // sa gauche (quart de tour a gauche de « devant »)
    const pt = (av, ga) => `${f(p.x + ux * av + gx * ga)},${f(p.y + uy * av + gy * ga)}`;
    el("polygon", { points: `${pt(15, 0)} ${pt(-11, 11)} ${pt(-5, 0)} ${pt(-11, -11)}`, fill: BLEU, stroke: "#FFFFFF", "stroke-width": 2, "stroke-linejoin": "round" });
    const main = (signe, texte, couleur) => {
      const x = p.x + gx * 19 * signe, y = p.y + gy * 19 * signe;
      el("circle", { cx: f(x), cy: f(y), r: 8.5, fill: "#FFFFFF", stroke: couleur, "stroke-width": 2 });
      el("text", { x: f(x), y: f(y + 4.5), "font-size": 13, "font-weight": 700, fill: couleur, "text-anchor": "middle", "font-family": "sans-serif" }, texte);
    };
    main(1, anglais ? "L" : "G", ORANGE);
    main(-1, anglais ? "R" : "D", VERT);

    // Les pictogrammes : fleche droite (avancer), fleche coudee a gauche ou a droite (tourner).
    const picto = (ins, cx, cy, couleur, taille) => {
      const k = taille / 26;
      const P = (x, y) => `${f(cx + x * k)},${f(cy + y * k)}`;
      if (ins === "A") {
        el("line", { x1: f(cx), y1: f(cy + 9 * k), x2: f(cx), y2: f(cy - 4 * k), stroke: couleur, "stroke-width": 3, "stroke-linecap": "round" });
        el("polygon", { points: `${P(0, -11)} ${P(-6, -3)} ${P(6, -3)}`, fill: couleur });
      } else {
        const s = ins === "G" ? -1 : 1;
        el("path", { d: `M${P(-3 * s, 10)} L${P(-3 * s, -1)} L${P(3 * s, -1)}`, fill: "none", stroke: couleur, "stroke-width": 3, "stroke-linecap": "round", "stroke-linejoin": "round" });
        el("polygon", { points: `${P(11 * s, -1)} ${P(3 * s, -7)} ${P(3 * s, 5)}`, fill: couleur });
      }
    };
    const n = prog.code.length, LARGE = 30, X0 = 170 - (n * LARGE) / 2, Y = 230;
    for (let i = 0; i < n; i++) {
      const fait = i < etape, courant = i === etape - 1;
      el("rect", {
        x: X0 + i * LARGE + 2, y: Y, width: LARGE - 4, height: 30, rx: 4,
        fill: courant ? "#FBE3C4" : fait ? "#EEF1F5" : "#FFFFFF",
        stroke: courant ? ORANGE : fait ? "#C9D2DE" : ENCRE, "stroke-width": courant ? 3 : 2,
      });
      picto(prog.code[i], X0 + i * LARGE + LARGE / 2, Y + 15, fait && !courant ? GRIS : ENCRE, 24);
    }

    // Legende des pictogrammes.
    const mots = anglais ? ["straight on", "turn left", "turn right"] : ["avancer", "à gauche", "à droite"];
    ["A", "G", "D"].forEach((ins, i) => {
      const x = 22 + i * 108;
      picto(ins, x + 9, 290, ENCRE, 22);
      el("text", { x: x + 24, y: 295, "font-size": 13, fill: ENCRE, "font-family": "sans-serif" }, mots[i]);
    });
    el("text", { x: 170, y: 326, "font-size": 13, fill: GRIS, "text-anchor": "middle", "font-family": "sans-serif" },
      anglais ? "L : sa gauche (left), R : sa droite (right)" : "G : sa gauche, D : sa droite");
    return { parcours, etape, col, lig, dir };
  },
};
