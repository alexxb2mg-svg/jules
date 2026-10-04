// Jules - gabarit "echelle-ph" : une echelle de pH de 0 a 14 avec un repere mobile, et un becher ou l'on voit
// les ions H+ (rouges) et HO- (bleus). Curseur : ph (pH de la solution, 0 a 14).
// - pH < 7 : acide, plus d'ions H+ que d'ions HO- ; pH = 7 : neutre, autant ; pH > 7 : basique, plus de HO-.
// - Les nombres d'ions dessines sont SCHEMATIQUES (de 1 a 11, egaux seulement a pH 7, sinon l'ion majoritaire a
//   toujours au moins un ion de plus) : en realite la concentration en
//   ions H+ est multipliee par 10 quand le pH baisse de 1 (le dessin ne peut pas suivre une echelle x 10).
// - pH <= 2 ou >= 12 : solution corrosive, signe d'avertissement et rappel « gants, lunettes ».
// Faits et notations (ions H+ et HO-, echelle 0-14, neutre a 7 a 25 degres) : programme de physique-chimie du
// cycle 4 (BO n° 31 du 30 juillet 2020, « Identifier le caractere acide ou basique d'une solution par mesure de
// pH ; associer le caractere acide ou basique a la presence d'ions H+ et HO- »),
// https://eduscol.education.fr/document/621/download. Le danger est signale par un simple triangle
// d'avertissement « ! » et le mot « corrosif » : ce n'est PAS le pictogramme reglementaire SGH05 (losange rouge,
// mains et surface rongees), trop detaille a cette taille ; le mot et la consigne « gants, lunettes » portent l'info.
// La figure ecrit la valeur du pH (le curseur lui-meme) mais pas « acide / basique » : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["echelle-ph"] = {
  dessiner(svg, valeurs) {
    const ph = Math.min(14, Math.max(0, Number(valeurs.ph ?? 7)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 310");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Echelle : 14 cases de x 26 a 314 (une unite de pH = 20,6 px), de y 46 a 74.
    const X0 = 26, X1 = 314, U = (X1 - X0) / 14, Y = 46, H = 28;
    const xDe = (p) => X0 + p * U;
    for (let i = 0; i < 14; i++) {
      const milieu = i + 0.5;
      let couleur, opacite;
      // Toute case sous 7 est acide (rouge), toute case au-dessus basique (bleu) : seul pH 7 est neutre.
      if (milieu < 7) { couleur = "#C8102E"; opacite = 0.25 + (0.7 * (7 - milieu)) / 7; }
      else { couleur = "#1F4E8C"; opacite = 0.25 + (0.7 * (milieu - 7)) / 7; }
      el("rect", { x: xDe(i), y: Y, width: U + 0.4, height: H, fill: couleur, "fill-opacity": opacite.toFixed(2) });
    }
    // Neutre = le seul point pH 7 : trait vert epais sur l'echelle.
    el("rect", { x: xDe(7) - 3, y: Y, width: 6, height: H, fill: "#2E7D32" });
    el("rect", { x: X0, y: Y, width: X1 - X0, height: H, fill: "none", stroke: "#14243B", "stroke-width": 2 });
    for (const p of [0, 2, 4, 6, 7, 8, 10, 12, 14]) {
      el("line", { x1: xDe(p), y1: Y + H, x2: xDe(p), y2: Y + H + 6, stroke: "#14243B", "stroke-width": 2 });
      if (p !== 6 && p !== 8) {
        el("text", { x: xDe(p), y: Y + H + 21, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, String(p));
      }
    }
    el("text", { x: X0, y: Y + H + 40, "font-size": 14, fill: "#C8102E", "font-weight": "bold" }, "acide");
    el("text", { x: xDe(7), y: Y + H + 40, "font-size": 14, "text-anchor": "middle", fill: "#2E7D32", "font-weight": "bold" }, "neutre");
    el("text", { x: X1, y: Y + H + 40, "font-size": 14, "text-anchor": "end", fill: "#1F4E8C", "font-weight": "bold" }, "basique");

    // Repere mobile : triangle au-dessus de l'echelle et valeur du pH.
    const xp = xDe(ph);
    el("path", { d: `M${xp},${Y - 2} l-8,-12 h16 z`, fill: "#14243B" });
    const txt = `pH = ${String(ph).replace(".", ",")}`;
    const ancre = xp < 50 ? "start" : xp > 290 ? "end" : "middle";
    el("text", { x: xp, y: Y - 18, "font-size": 15, "text-anchor": ancre, fill: "#14243B", "font-weight": "bold" }, txt);

    // Becher (x 30 a 200, y 150 a 290) et ions dans des emplacements fixes melanges.
    const BG = 30, BD = 200, BH = 150, BB = 290;
    el("rect", { x: BG, y: BH + 14, width: BD - BG, height: BB - BH - 14, fill: "#EEF3F8" });
    el("path", { d: `M${BG},${BH} V${BB} H${BD} V${BH}`, fill: "none", stroke: "#6B7686", "stroke-width": 3 });
    // 6 + 6 a pH 7 ; ailleurs un ecart d'au moins 1 (majorite stricte, meme a pH 6,5 ou 7,5), 11 contre 1 aux bouts.
    const ecart = ph === 7 ? 0 : Math.max(1, Math.round((5 * Math.abs(ph - 7)) / 7));
    const nH = ph < 7 ? 6 + ecart : 6 - ecart;
    const nHO = ph < 7 ? 6 - ecart : 6 + ecart;
    // 24 emplacements (grille 6 x 4) parcourus dans un ordre fixe melange.
    const ordre = [7, 16, 2, 21, 11, 4, 18, 9, 0, 14, 23, 5, 12, 19, 3, 8, 22, 15, 1, 10, 17, 6, 20, 13];
    const place = (k) => ({ x: BG + 20 + (k % 6) * 26 + (Math.floor(k / 6) % 2) * 10, y: BH + 34 + Math.floor(k / 6) * 30 });
    // Couleurs alternees tant qu'il y a des deux ions, puis l'ion majoritaire seul : on voit qui domine.
    const couleurs = [];
    for (let i = 0; i < Math.max(nH, nHO); i++) {
      if (i < nH) couleurs.push("#C8102E");
      if (i < nHO) couleurs.push("#1F4E8C");
    }
    couleurs.forEach((c, i) => {
      const { x, y } = place(ordre[i]);
      el("circle", { cx: x, cy: y, r: 8, fill: c });
    });

    // Legende des ions a droite du becher.
    el("circle", { cx: 222, cy: 176, r: 8, fill: "#C8102E" });
    el("text", { x: 236, y: 181, "font-size": 14, fill: "#14243B" }, "ion H⁺");
    el("circle", { cx: 222, cy: 204, r: 8, fill: "#1F4E8C" });
    el("text", { x: 236, y: 209, "font-size": 14, fill: "#14243B" }, "ion HO⁻");

    // Danger pour les solutions tres acides ou tres basiques.
    const corrosif = ph <= 2 || ph >= 12;
    if (corrosif) {
      el("path", { d: "M262,226 l22,38 h-44 z", fill: "#FFFFFF", stroke: "#E07B00", "stroke-width": 3, "stroke-linejoin": "round" });
      el("text", { x: 262, y: 258, "font-size": 18, "text-anchor": "middle", fill: "#E07B00", "font-weight": "bold" }, "!");
      el("text", { x: 262, y: 284, "font-size": 13, "text-anchor": "middle", fill: "#E07B00", "font-weight": "bold" }, "corrosif :");
      el("text", { x: 262, y: 300, "font-size": 13, "text-anchor": "middle", fill: "#E07B00" }, "gants, lunettes");
    }
    return { ph, ions_h: nH, ions_ho: nHO, corrosif };
  },
};
