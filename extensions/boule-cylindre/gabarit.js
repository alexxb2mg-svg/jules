// Jules - gabarit "boule-cylindre" : une boule de rayon r posee dans le cylindre qui l'enveloppe exactement
// (meme diametre, hauteur = 2r), vue de cote, a une echelle fixe (la figure grandit avec r). Deux jauges de meme
// longueur coupees en 3 parts : le cylindre les remplit toutes, la boule en remplit 2, quel que soit r.
// Une petite boule grise de rayon 1 cm sert de repere de taille. Aucun volume ecrit (seul r, la valeur du
// curseur, est ecrit) : revele false.
// Faits (EX-205) : V boule = (4/3) x pi x r^3 ; V cylindre = pi x r^2 x h avec h = 2r, soit 2 x pi x r^3 ; donc
// V boule / V cylindre = (4/3) / 2 = 2/3 (resultat d'Archimede, « De la sphere et du cylindre »). Rayon x k :
// volume x k^3 (r = 2 : x 8 ; r = 10 : x 1 000).
// Sources : programme de mathematiques du cycle 4 (BO n° 31 du 30/07/2020, « Grandeurs et mesures » : volume de
// la boule) ; Wikipedia, « Volume d'une boule » (oldid 239490869, deja cite par la fiche) ; Wikipedia,
// « De la sphère et du cylindre » (Archimede).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["boule-cylindre"] = {
  // dessiner(svg, valeurs) : r de 1 a 10 (cm), entier.
  dessiner(svg, valeurs) {
    const r = Math.min(10, Math.max(1, Math.round(Number(valeurs.r ?? 3) || 3)));
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", ORANGE = "#E07B00";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Echelle fixe : 9 px pour 1 cm, la boule de rayon 10 fait 180 px de diametre.
    const S = 9, SOL = 212, CX = 170;
    const R = r * S;
    const haut = SOL - 2 * R;
    const ry = Math.max(3, R * 0.15); // ellipses du cylindre (perspective legere)

    // Le cylindre : corps, fond (arc avant) et couvercle (ellipse entiere), contour orange.
    el("rect", { x: f(CX - R), y: f(haut), width: f(2 * R), height: f(2 * R), fill: "#FDF0E1", stroke: "none" });
    el("ellipse", { cx: CX, cy: f(SOL), rx: f(R), ry: f(ry), fill: "#FDF0E1", stroke: ORANGE, "stroke-width": 2, "stroke-dasharray": "5 4" });
    el("path", { d: `M ${f(CX - R)} ${f(SOL)} A ${f(R)} ${f(ry)} 0 0 0 ${f(CX + R)} ${f(SOL)}`, fill: "none", stroke: ORANGE, "stroke-width": 3 });
    el("line", { x1: f(CX - R), y1: f(haut), x2: f(CX - R), y2: f(SOL), stroke: ORANGE, "stroke-width": 3 });
    el("line", { x1: f(CX + R), y1: f(haut), x2: f(CX + R), y2: f(SOL), stroke: ORANGE, "stroke-width": 3 });

    // La boule, posee au fond, touche les deux parois et le couvercle.
    el("circle", { cx: CX, cy: f(SOL - R), r: f(R), fill: "#DCE8F6", stroke: BLEU, "stroke-width": 3 });
    el("ellipse", { cx: f(CX - R * 0.35), cy: f(SOL - R * 1.35), rx: f(R * 0.22), ry: f(R * 0.13), fill: "#FFFFFF", opacity: 0.7 });
    el("ellipse", { cx: CX, cy: f(haut), rx: f(R), ry: f(ry), fill: "none", stroke: ORANGE, "stroke-width": 3 });

    // Le rayon, en rouge, du centre a la paroi.
    el("line", { x1: CX, y1: f(SOL - R), x2: f(CX + R), y2: f(SOL - R), stroke: ROUGE, "stroke-width": 3 });
    el("circle", { cx: CX, cy: f(SOL - R), r: 3, fill: ROUGE });
    el("text", { x: CX, y: 246, "font-size": 15, "font-weight": "bold", fill: ROUGE, "text-anchor": "middle", "font-family": "sans-serif" }, `r = ${r} cm`);

    // Repere : la boule de rayon 1 cm, a la meme echelle.
    el("circle", { cx: 312, cy: f(SOL - S), r: S, fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "3 2" });
    el("text", { x: 312, y: 246, "font-size": 13, fill: GRIS, "text-anchor": "middle", "font-family": "sans-serif" }, "r = 1");

    // Deux jauges de meme longueur, coupees en 3 parts egales : cylindre 3 parts, boule 2 parts.
    const X0 = 96, L = 228, part = L / 3;
    const jauge = (y, nom, couleur, fond, pleines) => {
      el("text", { x: 14, y: y + 15, "font-size": 14, fill: couleur, "font-weight": "bold", "font-family": "sans-serif" }, nom);
      for (let i = 0; i < 3; i++) {
        const plein = i < pleines;
        el("rect", {
          x: f(X0 + i * part + 2), y, width: f(part - 4), height: 20, rx: 3,
          fill: plein ? fond : "#FFFFFF", stroke: plein ? couleur : GRIS, "stroke-width": 2,
          "stroke-dasharray": plein ? "none" : "4 3",
        });
      }
    };
    jauge(262, "cylindre", ORANGE, "#F6C58C", 3);
    jauge(296, "boule", BLEU, "#8FB3DE", 2);
    el("text", { x: 14, y: 334, "font-size": 13, fill: GRIS, "font-family": "sans-serif" }, "une part = le même volume dans les deux jauges");
    return { r, R };
  },
};
