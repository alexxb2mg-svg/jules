// Jules - gabarit "figuratif-abstrait" : un meme motif dessine en 4 etats, du plus proche du reel au plus
// eloigne. Curseurs : ecart (0 = imiter / figuratif, 1 = accentuer / simplifie, 2 = interpreter / geometrise,
// 3 = s'eloigner / abstrait) et motif (1 = visage, 2 = arbre, 3 = pomme), en general fige par la fiche.
// Dessins schematiques faits pour Jules : aucune oeuvre reelle n'est reproduite. Le motif « arbre » suit
// seulement l'idee de la serie des arbres de Piet Mondrian (1908-1913 : L'Arbre rouge, L'Arbre gris, Pommier en
// fleurs, puis compositions de lignes et de plans), sans en copier aucun.
// Sources : programme d'arts plastiques du cycle 4, « La representation ; images, realite et fiction »
// (ressemblance, ecart, autonomie de l'oeuvre), BO n° 31 du 30 juillet 2020 ; programme du cycle 3
// (« la ressemblance », « l'ecart dans la representation ») ; Kunstmuseum Den Haag, collection Mondrian
// (dates de la serie des arbres).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["figuratif-abstrait"] = {
  dessiner(svg, valeurs) {
    const borne = (v, min, max) => Math.min(max, Math.max(min, v));
    const ecart = borne(Math.round(Number(valeurs.ecart ?? 0)), 0, 3);
    const motif = borne(Math.round(Number(valeurs.motif ?? 1)), 1, 3);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32",
      ORANGE = "#E07B00", JAUNE = "#F2C200", PEAU = "#F3D2B3", OMBRE = "#D9DDE3";

    svg.setAttribute("viewBox", "0 0 340 300");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    const MOTS = motif === 2
      ? ["figuratif", "simplifié", "géométrisé", "abstrait"]
      : ["imiter", "accentuer", "interpréter", "s'éloigner"];

    // Le dessin (zone 40..250 en hauteur, centre 170,145).
    if (motif === 1) {
      if (ecart === 0) {
        // Visage proche du reel : proportions justes, ombre douce sur un cote.
        el("path", { d: "M110,120 Q112,52 170,50 Q228,52 230,120 L222,104 Q200,78 170,80 Q140,78 118,104 Z", fill: GRIS });
        el("ellipse", { cx: 170, cy: 145, rx: 58, ry: 75, fill: PEAU, stroke: ENCRE, "stroke-width": 2 });
        el("path", { d: "M198,85 Q228,120 210,205 Q195,218 180,219 Q214,170 198,85 Z", fill: OMBRE, opacity: 0.8 });
        for (const x of [148, 192]) {
          el("ellipse", { cx: x, cy: 135, rx: 11, ry: 6, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 2 });
          el("circle", { cx: x, cy: 135, r: 4, fill: ENCRE });
          el("path", { d: `M${x - 13},120 Q${x},113 ${x + 13},120`, fill: "none", stroke: ENCRE, "stroke-width": 2 });
        }
        el("path", { d: "M170,140 L163,170 Q170,175 177,170", fill: "none", stroke: ENCRE, "stroke-width": 2 });
        el("path", { d: "M150,190 Q170,200 190,190", fill: "none", stroke: ENCRE, "stroke-width": 2 });
      } else if (ecart === 1) {
        // Caricature : meme visage, nez, menton et sourcils exageres (en rouge : ce qui est accentue).
        el("path", { d: "M110,120 Q112,52 170,50 Q228,52 230,120 L222,104 Q200,78 170,80 Q140,78 118,104 Z", fill: GRIS });
        el("path", { d: "M112,140 Q112,70 170,70 Q228,70 228,140 Q226,200 200,232 Q170,256 140,232 Q114,200 112,140 Z",
          fill: PEAU, stroke: ENCRE, "stroke-width": 2 });
        for (const x of [146, 194]) {
          el("ellipse", { cx: x, cy: 130, rx: 9, ry: 5, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 2 });
          el("circle", { cx: x, cy: 130, r: 3, fill: ENCRE });
          el("path", { d: `M${x - 18},110 Q${x},96 ${x + 18},110`, fill: "none", stroke: ROUGE, "stroke-width": 5 });
        }
        el("path", { d: "M170,132 Q150,170 138,182 Q160,198 186,184", fill: PEAU, stroke: ROUGE, "stroke-width": 3 });
        el("path", { d: "M152,212 Q170,222 188,212", fill: "none", stroke: ENCRE, "stroke-width": 2 });
      } else if (ecart === 2) {
        // Interpretation : memes proportions, couleurs et contours libres.
        el("path", { d: "M110,120 Q112,52 170,50 Q228,52 230,120 L222,104 Q200,78 170,80 Q140,78 118,104 Z", fill: VERT });
        el("ellipse", { cx: 170, cy: 145, rx: 58, ry: 75, fill: BLEU, stroke: ORANGE, "stroke-width": 5 });
        el("circle", { cx: 140, cy: 175, r: 14, fill: ORANGE });
        for (const x of [148, 192]) {
          el("ellipse", { cx: x, cy: 135, rx: 11, ry: 6, fill: JAUNE, stroke: ENCRE, "stroke-width": 2 });
          el("circle", { cx: x, cy: 135, r: 4, fill: ENCRE });
        }
        el("path", { d: "M170,140 L163,170 L177,170", fill: "none", stroke: JAUNE, "stroke-width": 4 });
        el("path", { d: "M150,190 Q170,200 190,190", fill: "none", stroke: ROUGE, "stroke-width": 4 });
      } else {
        // S'eloigner : il ne reste que des formes et des couleurs.
        el("rect", { x: 118, y: 66, width: 104, height: 34, fill: VERT });
        el("circle", { cx: 170, cy: 150, r: 62, fill: "none", stroke: BLEU, "stroke-width": 8 });
        el("rect", { x: 134, y: 124, width: 20, height: 20, fill: ENCRE });
        el("rect", { x: 196, y: 132, width: 14, height: 14, fill: ROUGE });
        el("path", { d: "M166,150 L182,182 L158,182 Z", fill: JAUNE });
        el("line", { x1: 140, y1: 204, x2: 208, y2: 196, stroke: ORANGE, "stroke-width": 6 });
      }
    } else if (motif === 2) {
      const SOL = 245;
      if (ecart === 0) {
        // Arbre vu comme dans la nature : tronc, branches, feuillage.
        el("line", { x1: 40, y1: SOL, x2: 300, y2: SOL, stroke: GRIS, "stroke-width": 2 });
        el("path", { d: "M160,245 Q164,190 158,150 L182,150 Q176,190 182,245 Z", fill: "#7A5230" });
        el("path", { d: "M166,170 Q140,140 116,128 M174,165 Q204,138 226,124 M170,150 Q170,112 168,88",
          fill: "none", stroke: "#7A5230", "stroke-width": 6, "stroke-linecap": "round" });
        for (const [x, y, r] of [[120, 118, 30], [170, 84, 38], [222, 114, 32], [146, 130, 28], [196, 128, 28]]) {
          el("circle", { cx: x, cy: y, r, fill: VERT, opacity: 0.85 });
        }
      } else if (ecart === 1) {
        // Simplifie : plus de feuilles, des branches en lignes souples.
        el("line", { x1: 40, y1: SOL, x2: 300, y2: SOL, stroke: GRIS, "stroke-width": 2 });
        el("path", {
          d: "M170,245 L170,150 M170,180 Q130,150 100,140 M170,175 Q212,148 244,138 M170,150 Q140,110 110,96 " +
            "M170,150 Q202,108 232,96 M170,150 L170,70 M140,120 Q120,100 96,100 M200,118 Q222,100 246,102",
          fill: "none", stroke: GRIS, "stroke-width": 5, "stroke-linecap": "round",
        });
      } else if (ecart === 2) {
        // Geometrise : des arcs et des traits presque horizontaux et verticaux, l'arbre se devine encore.
        el("path", {
          d: "M170,245 L170,120 M80,150 Q170,95 260,150 M100,118 Q170,70 240,118 M120,90 Q170,56 220,90 " +
            "M130,170 L210,170 M150,200 L190,200 M110,135 L110,165 M230,135 L230,165",
          fill: "none", stroke: ENCRE, "stroke-width": 4, "stroke-linecap": "round",
        });
        el("rect", { x: 182, y: 128, width: 26, height: 22, fill: BLEU, opacity: 0.7 });
        el("rect", { x: 132, y: 104, width: 22, height: 18, fill: ORANGE, opacity: 0.7 });
      } else {
        // Abstrait : lignes et plans de couleur, plus aucun arbre.
        el("rect", { x: 70, y: 50, width: 200, height: 200, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 3 });
        el("rect", { x: 70, y: 50, width: 80, height: 90, fill: ROUGE });
        el("rect", { x: 210, y: 190, width: 60, height: 60, fill: BLEU });
        el("rect", { x: 150, y: 190, width: 60, height: 30, fill: JAUNE });
        for (const [x1, y1, x2, y2] of [[150, 50, 150, 250], [210, 140, 210, 250], [70, 140, 270, 140],
          [150, 190, 270, 190], [150, 220, 210, 220]]) {
          el("line", { x1, y1, x2, y2, stroke: ENCRE, "stroke-width": 6 });
        }
      }
    } else {
      const pomme = (d, fill, stroke, sw) => el("path", { d, fill, stroke, "stroke-width": sw });
      const FORME = "M170,95 Q200,72 228,96 Q256,124 244,172 Q230,228 194,232 Q182,226 170,230 Q158,226 146,232 " +
        "Q110,228 96,172 Q84,124 112,96 Q140,72 170,95 Z";
      if (ecart === 0) {
        // Imiter : forme, couleur, reflet et ombre portee.
        el("ellipse", { cx: 180, cy: 238, rx: 78, ry: 10, fill: OMBRE });
        pomme(FORME, ROUGE, ENCRE, 2);
        el("path", { d: "M214,104 Q246,140 232,196 Q222,220 200,228 Q230,180 214,104 Z", fill: "#8E0B20", opacity: 0.6 });
        el("ellipse", { cx: 132, cy: 128, rx: 12, ry: 20, fill: "#FFFFFF", opacity: 0.7 });
        el("path", { d: "M170,96 Q168,76 176,62", fill: "none", stroke: "#7A5230", "stroke-width": 4 });
        el("path", { d: "M176,72 Q200,56 214,70 Q196,84 176,72 Z", fill: VERT });
      } else if (ecart === 1) {
        // Accentuer : la queue et la feuille deviennent enormes (en rouge vif : ce qui est exagere).
        pomme(FORME, ROUGE, ENCRE, 2);
        el("path", { d: "M170,96 Q160,62 180,40", fill: "none", stroke: "#7A5230", "stroke-width": 7 });
        el("path", { d: "M180,58 Q240,20 280,58 Q232,96 180,58 Z", fill: VERT, stroke: ENCRE, "stroke-width": 2 });
        el("ellipse", { cx: 132, cy: 128, rx: 14, ry: 24, fill: "#FFFFFF" });
      } else if (ecart === 2) {
        // Interpreter : la pomme reste une pomme, mais avec les couleurs et les contours de l'artiste.
        pomme(FORME, BLEU, ORANGE, 7);
        el("path", { d: "M170,96 Q168,76 176,62", fill: "none", stroke: ROUGE, "stroke-width": 5 });
        el("path", { d: "M176,72 Q200,56 214,70 Q196,84 176,72 Z", fill: ROUGE });
        el("circle", { cx: 140, cy: 140, r: 12, fill: JAUNE });
      } else {
        // S'eloigner : un disque, un triangle, un trait.
        el("circle", { cx: 160, cy: 160, r: 66, fill: ROUGE });
        el("path", { d: "M206,64 L250,84 L212,108 Z", fill: VERT });
        el("line", { x1: 176, y1: 70, x2: 168, y2: 104, stroke: ENCRE, "stroke-width": 6 });
      }
    }

    // Les 4 etapes, la case allumee = l'etat montre.
    const L = 76, X0 = 18, Y = 262;
    MOTS.forEach((mot, i) => {
      const actif = i === ecart;
      el("rect", { x: X0 + i * L + 2, y: Y, width: L - 4, height: 30, rx: 6,
        fill: actif ? BLEU : "#FFFFFF", stroke: actif ? BLEU : GRIS, "stroke-width": 2 });
      el("text", { x: X0 + i * L + L / 2, y: Y + 20, "font-size": 13, "text-anchor": "middle",
        "font-weight": actif ? "bold" : "normal", fill: actif ? "#FFFFFF" : GRIS }, mot);
    });
    el("text", { x: 22, y: 22, "font-size": 14, fill: GRIS }, "réel");
    el("text", { x: 318, y: 22, "font-size": 14, "text-anchor": "end", fill: GRIS }, "loin du réel");
    el("line", { x1: 60, y1: 18, x2: 228, y2: 18, stroke: GRIS, "stroke-width": 2 });
    el("path", { d: "M234,18 l-9,-5 l0,10 z", fill: GRIS });
    return { ecart, motif, etat: MOTS[ecart] };
  },
};
