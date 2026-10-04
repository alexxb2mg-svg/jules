// Jules - gabarit "pixellisation" : une meme image simple (soleil, ciel, colline) recomposee en grille de
// pixels. pixels = nombre de pixels par cote (4 a 64), couleurs = nombre de couleurs de la palette (2 a 16).
// Peu de pixels : on voit les carres ; peu de couleurs : aplats tranches. Une jauge montre le poids du fichier
// (image non compressee), sans aucun chiffre.
// Faits (EX-205) : une image matricielle est une grille de pixels ; son poids non compresse vaut
// (nombre de pixels) x (bits par pixel), et une palette de k couleurs demande log2(k) bits par pixel, arrondi
// au-dessus (2 couleurs = 1 bit, 16 couleurs = 4 bits). Sources : Wikipedia « Image matricielle » et
// « Profondeur de couleur » ; Eduscol, programme de technologie cycle 4 (representation numerique de l'information).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["pixellisation"] = {
  dessiner(svg, valeurs) {
    const borne = (v, mini, maxi, defaut) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(maxi, Math.max(mini, Math.round(n))) : defaut;
    };
    const pixels = borne(valeurs.pixels, 4, 64, 16);
    const couleurs = borne(valeurs.couleurs, 2, 16, 8);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Palette : rampe sombre -> bleu -> orange -> clair, echantillonnee en `couleurs` teintes.
    // Avec 2 couleurs il reste le bleu nuit et le clair : presque du noir et blanc.
    const ARRETS = [[0, [20, 36, 59]], [0.35, [31, 78, 140]], [0.7, [224, 123, 0]], [1, [251, 232, 190]]];
    const teinte = (t) => {
      for (let i = 1; i < ARRETS.length; i++) {
        const [t1, c1] = ARRETS[i];
        const [t0, c0] = ARRETS[i - 1];
        if (t <= t1) {
          const f = (t - t0) / (t1 - t0);
          return `rgb(${c0.map((c, j) => Math.round(c + (c1[j] - c) * f)).join(",")})`;
        }
      }
      return "rgb(251,232,190)";
    };
    // L'image « vraie » : une valeur entre 0 et 1 en chaque point (u, v) du carre.
    const scene = (u, v) => {
      const colline = 0.66 + 0.32 * (u - 0.2) * (u - 0.2);
      if (v > colline) return Math.min(0.3, 0.1 + 0.4 * (v - colline)); // colline sombre
      const d = Math.hypot(u - 0.66, v - 0.32);
      if (d < 0.15) return 1; // soleil
      if (d < 0.26) return 0.62 + (0.38 * (0.26 - d)) / 0.11; // halo
      return 0.3 + 0.32 * v; // ciel, plus clair vers l'horizon
    };

    // L'image : un carre de 236 de cote, decoupe en pixels x pixels carres d'une seule couleur chacun.
    const X0 = 12, Y0 = 12, COTE = 236, c = COTE / pixels;
    for (let j = 0; j < pixels; j++) {
      for (let i = 0; i < pixels; i++) {
        const t = scene((i + 0.5) / pixels, (j + 0.5) / pixels);
        const niveau = Math.round(t * (couleurs - 1)) / (couleurs - 1);
        el("rect", {
          x: (X0 + i * c).toFixed(2), y: (Y0 + j * c).toFixed(2),
          width: Math.min(c + 0.3, COTE - i * c).toFixed(2),
          height: Math.min(c + 0.3, COTE - j * c).toFixed(2),
          fill: teinte(niveau),
        });
      }
    }
    // Avec tres peu de pixels, on trace la grille pour bien voir que l'image est faite de carres.
    if (pixels <= 12) {
      for (let k = 1; k < pixels; k++) {
        const p = X0 + k * c;
        el("line", { x1: p, y1: Y0, x2: p, y2: Y0 + COTE, stroke: "#FFFFFF", "stroke-width": 2, "stroke-opacity": 0.35 });
        el("line", { x1: X0, y1: Y0 + k * c, x2: X0 + COTE, y2: Y0 + k * c, stroke: "#FFFFFF", "stroke-width": 2, "stroke-opacity": 0.35 });
      }
    }
    el("rect", { x: X0, y: Y0, width: COTE, height: COTE, fill: "none", stroke: "#6B7686", "stroke-width": 2 });

    // Les reglages, en mots, sous l'image.
    el("text", { x: X0, y: 270, "font-size": 15, fill: "#14243B" }, `${pixels} pixels par côté`);
    el("text", { x: X0, y: 290, "font-size": 15, fill: "#14243B" }, `${couleurs} couleurs`);

    // Jauge du poids du fichier, proportionnelle a pixels^2 x bits par pixel (maximum : 64 x 64 x 4 bits).
    // Le haut de la jauge correspond au plus gros fichier possible ici ; rien n'est chiffre.
    const bits = Math.ceil(Math.log2(couleurs));
    const part = (pixels * pixels * bits) / (64 * 64 * 4);
    const JX = 274, JY0 = 48, JH = 190, JL = 40, MX = JX + JL / 2;
    el("text", { x: MX, y: 18, "font-size": 14, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, "poids");
    el("text", { x: MX, y: 38, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" }, "lourd");
    el("rect", { x: JX, y: JY0, width: JL, height: JH, fill: "#FFFFFF", stroke: "#6B7686", "stroke-width": 2 });
    const h = Math.max(3, part * (JH - 4));
    el("rect", { x: JX + 2, y: JY0 + JH - 2 - h, width: JL - 4, height: h, fill: "#E07B00" });
    el("text", { x: MX, y: JY0 + JH + 18, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" }, "léger");
    return { pixels, couleurs };
  },
};
