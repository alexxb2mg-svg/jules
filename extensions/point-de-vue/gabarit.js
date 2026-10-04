// Jules - gabarit "point-de-vue" : ce que voit l'oeil (ou la camera) selon sa place, et le meme lieu vu de cote.
// Curseurs : distance (1 = tout pres, gros plan ; 5 = loin, plan d'ensemble), hauteur (place de l'oeil :
// -2 = tres bas, contre-plongee ; 0 = a hauteur du sujet ; 2 = tres haut, plongee) et taille (hauteur en metres
// d'une oeuvre posee a cote du personnage de 1,5 m ; 0 = pas d'oeuvre, le personnage est le sujet).
// En haut : l'image vue (cadre bleu) ; vu d'en bas, le haut du sujet se resserre (il parait grand et puissant),
// vu d'en haut, c'est le bas qui se resserre (il parait petit). En bas : le meme lieu vu de cote, l'oeil (rouge)
// et ce qu'il regarde. Les noms des plans ne sont pas ecrits (c'est ce que l'eleve doit nommer) : revele false.
// Les fiches d'arts plastiques qui ne parlent que d'echelle et de point de vue figent distance = 5 (min = max) :
// tout le lieu est visible, l'oeuvre a cote du personnage (valeur prise aussi si distance manque).
// Dessins schematiques faits pour Jules : aucune oeuvre reelle n'est reproduite (la sculpture est un robot simple).
// Echelle des plans (vocabulaire du cinema enseigne en francais et en arts plastiques au cycle 4) : plan
// d'ensemble (le lieu), plan moyen (personnage en pied), plan americain (coupe a mi-cuisse), plan rapproche
// (coupe a la poitrine), gros plan (le visage) ; plongee = vue d'en haut, contre-plongee = vue d'en bas.
// Sources : programme de francais cycle 4 (« lire des images, des documents composites ») et programme d'arts
// plastiques cycle 4 (« la presence materielle de l'oeuvre dans l'espace », « l'experience sensible de l'espace
// de l'oeuvre ») et cycle 3 (« la prise en compte du spectateur »), BO n° 31 du 30 juillet 2020 ; CNC, education
// a l'image, lexique « echelle des plans », « plongee », « contre-plongee ».
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["point-de-vue"] = {
  dessiner(svg, valeurs) {
    const borne = (v, min, max) => Math.min(max, Math.max(min, v));
    const distance = borne(Math.round(Number(valeurs.distance ?? 5)), 1, 5);
    const hauteur = borne(Math.round(Number(valeurs.hauteur ?? 0)), -2, 2);
    const taille = borne(Number(valeurs.taille ?? 0), 0, 20);
    const NS = "http://www.w3.org/2000/svg";
    const cree = (parent, nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      parent.appendChild(n);
      return n;
    };
    const el = (nom, attrs, texte) => cree(svg, nom, attrs, texte);
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32",
      ORANGE = "#E07B00", PEAU = "#F3D2B3", CIEL = "#EAF1FA", SOL = "#DCE6D2";

    svg.setAttribute("viewBox", "0 0 340 300");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    // --- La scene, en metres (sol y = 0, vers le haut). Personnage de 1,5 m en x = 0, arbre a gauche (sans oeuvre),
    // oeuvre (robot) a droite si taille > 0.
    const L = taille > 0 ? Math.max(0.4, taille * 0.5) : 0; // largeur de l'oeuvre
    const XO = 0.9; // bord gauche de l'oeuvre
    const formes = []; // {pts: [[x, y]...], fill, stroke, sw}
    const poly = (pts, fill, stroke = ENCRE, sw = 2) => formes.push({ pts, fill, stroke, sw });
    const rect = (x0, y0, x1, y1, fill, stroke, sw) => poly([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], fill, stroke, sw);
    const disque = (cx, cy, r, fill, stroke, sw) =>
      poly(Array.from({ length: 20 }, (_, i) => [cx + r * Math.cos((i * Math.PI) / 10), cy + r * Math.sin((i * Math.PI) / 10)]),
        fill, stroke, sw);
    // Arbre (decor, 3 m), seulement quand le personnage est le sujet : avec une oeuvre, on compare l'oeuvre au corps.
    if (taille === 0) {
      rect(-2.45, 0, -2.25, 1.6, "#7A5230", "#7A5230", 2);
      disque(-2.35, 2.2, 0.8, VERT, VERT, 2);
    }
    // Personnage (1,5 m) : jambes, corps, bras, tete, yeux, bouche.
    rect(-0.17, 0, -0.04, 0.75, BLEU, ENCRE, 2);
    rect(0.04, 0, 0.17, 0.75, BLEU, ENCRE, 2);
    rect(-0.22, 0.72, 0.22, 1.27, ORANGE, ENCRE, 2);
    rect(-0.32, 0.8, -0.22, 1.24, ORANGE, ENCRE, 2);
    rect(0.22, 0.8, 0.32, 1.24, ORANGE, ENCRE, 2);
    disque(0, 1.39, 0.12, PEAU, ENCRE, 2);
    disque(-0.045, 1.41, 0.017, ENCRE, "none", 0);
    disque(0.045, 1.41, 0.017, ENCRE, "none", 0);
    poly([[-0.045, 1.345], [0.045, 1.345], [0, 1.325]], ROUGE, "none", 0);
    // Oeuvre : un robot simple (socle, corps, tete, yeux), hauteur = taille.
    if (taille > 0) {
      const H = taille;
      rect(XO, 0, XO + L, 0.12 * H, GRIS, ENCRE, 2);
      rect(XO + 0.1 * L, 0.12 * H, XO + 0.9 * L, 0.7 * H, "#C9D8EE", BLEU, 3);
      rect(XO + 0.25 * L, 0.72 * H, XO + 0.75 * L, H, "#C9D8EE", BLEU, 3);
      disque(XO + 0.4 * L, 0.87 * H, 0.05 * L, ROUGE, "none", 0);
      disque(XO + 0.6 * L, 0.87 * H, 0.05 * L, ROUGE, "none", 0);
    }

    // --- Le sujet : l'oeuvre s'il y en a une, sinon le personnage.
    const HS = taille > 0 ? Math.max(taille, 1.5) : 1.5;
    const xs = taille > 0 ? XO + L / 2 : 0;

    // --- Fenetre vue par l'oeil (en metres). distance 5 : tout le lieu ; 4 a 1 : de plus en plus serre sur le
    // personnage (en pied, mi-cuisse, poitrine, visage), ou sur le haut de l'oeuvre s'il y en a une.
    const FX0 = 20, FY0 = 30, FW = 300, FH = 170; // cadre de l'image
    const RAPPORT = FW / FH;
    let wy0, wy1, wxc;
    if (distance === 5) {
      const xmin = taille > 0 ? -0.8 : -3.4, xmax = taille > 0 ? XO + L + 0.6 : 1.2;
      const haut = Math.max(3.4, HS * 1.15);
      const larg = Math.max(xmax - xmin, haut * RAPPORT);
      wxc = (xmin + xmax) / 2;
      wy0 = -0.1 * (larg / RAPPORT);
      wy1 = wy0 + larg / RAPPORT;
    } else {
      const fen = taille > 0
        ? [[0, 0], [-0.05 * HS, 1.1 * HS], [0.25 * HS, 1.08 * HS], [0.5 * HS, 1.05 * HS], [0.68 * HS, 1.04 * HS]][distance]
        : [[0, 0], [1.16, 1.6], [0.88, 1.62], [0.45, 1.66], [-0.1, 1.7]][distance];
      [wy0, wy1] = fen;
      wxc = xs;
    }
    const wh = wy1 - wy0, ww = wh * RAPPORT;
    // Deformation : contre-plongee (hauteur < 0) = le haut se resserre ; plongee (hauteur > 0) = le bas.
    const s = hauteur / 2;
    const proj = ([x, y]) => {
      const yr = (y - wy0) / wh;
      const f = 1 + 0.3 * s * (2 * yr - 1);
      // le sujet reste droit : on resserre autour de sa verticale (xs)
      return [FX0 + FW / 2 + ((xs - wxc) + (x - xs) * f) / ww * FW, FY0 + FH - yr * FH];
    };
    // Image vue : SVG imbrique de la taille du cadre, qui coupe tout ce qui sort du cadre (le hors-champ).
    const image = el("svg", { x: FX0, y: FY0, width: FW, height: FH, viewBox: `${FX0} ${FY0} ${FW} ${FH}` });
    cree(image, "rect", { x: FX0, y: FY0, width: FW, height: FH, fill: CIEL });
    // Sol vu : sous l'horizon du regard ; plus l'oeil est haut, plus l'horizon monte et plus on voit de sol.
    const ySol = proj([0, 0])[1];
    const yHorizon = Math.min(ySol, FY0 + FH * (0.5 - 0.45 * s));
    cree(image, "rect", { x: FX0, y: yHorizon, width: FW, height: FY0 + FH - yHorizon, fill: SOL });
    for (const f of formes) {
      const p = f.pts.map(proj).map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
      cree(image, "polygon", { points: p, fill: f.fill, stroke: f.stroke, "stroke-width": f.sw, "stroke-linejoin": "round" });
    }
    el("rect", { x: FX0, y: FY0, width: FW, height: FH, fill: "none", stroke: BLEU, "stroke-width": 4 });
    el("text", { x: FX0, y: 21, "font-size": 14, "font-weight": "bold", fill: BLEU }, "ce que voit l'œil");

    // --- Vu de cote : sol, personnage, oeuvre, oeil a sa hauteur et a sa distance, rayon de regard.
    const VY = 288, VH = 62; // sol et hauteur dispo
    const hOeil = HS * [0.08, 0.45, 0.85, 1.45, 2.1][hauteur + 2];
    const echelle = VH / Math.max(HS * 1.05, hOeil);
    const xSujet = 250, xOeil = [0, 175, 140, 105, 70, 35][distance];
    el("text", { x: FX0, y: 228, "font-size": 13, fill: GRIS }, "vu de côté");
    el("line", { x1: 20, y1: VY, x2: 320, y2: VY, stroke: GRIS, "stroke-width": 2 });
    const hp = 1.5 * echelle;
    el("line", { x1: xSujet - 22, y1: VY, x2: xSujet - 22, y2: VY - hp + 6, stroke: ORANGE, "stroke-width": 4 });
    el("circle", { cx: xSujet - 22, cy: VY - hp + 4, r: Math.max(3, 0.12 * echelle), fill: PEAU, stroke: ENCRE, "stroke-width": 2 });
    if (taille > 0) {
      const ho = taille * echelle;
      el("rect", { x: xSujet, y: VY - ho, width: Math.max(8, Math.min(40, L * echelle)), height: ho,
        fill: "#C9D8EE", stroke: BLEU, "stroke-width": 2 });
    }
    const yOeil = VY - hOeil * echelle;
    const yVise = VY - (distance === 5 ? HS * 0.5 : ((wy0 + wy1) / 2)) * echelle;
    el("line", { x1: xOeil + 8, y1: yOeil, x2: xSujet - 30, y2: yVise, stroke: ROUGE, "stroke-width": 2, "stroke-dasharray": "5 4" });
    el("ellipse", { cx: xOeil, cy: yOeil, rx: 9, ry: 6, fill: "#FFFFFF", stroke: ROUGE, "stroke-width": 2 });
    el("circle", { cx: xOeil + 2, cy: yOeil, r: 3, fill: ROUGE });
    return { distance, hauteur, taille };
  },
};
