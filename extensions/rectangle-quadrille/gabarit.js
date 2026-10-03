// Jules - gabarit "rectangle-quadrille" : un rectangle pave de carreaux de 1 cm, longueur L et largeur l.
// deroule = 1 : le contour se deroule en un seul trait sur une regle graduee (le perimetre se lit, il n'est pas ecrit).
// forme = 1 : les memes carreaux glissent en escalier (meme aire, autre forme) ; la regle ne sert qu'au
// rectangle (forme = 0). Ni aire ni perimetre ecrits.
// Les longueurs (L) sont en bleu, les largeurs (l) en orange, sur le rectangle comme sur la regle.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["rectangle-quadrille"] = {
  // dessiner(svg, valeurs) : longueur L de 1 a 12, largeur l de 1 a 8 (en cm), deroule 0 ou 1, forme 0 ou 1.
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => Math.min(maxi, Math.max(mini, Math.round(Number(v ?? d))));
    const L = ent(valeurs.longueur, 5, 1, 12);
    const l = ent(valeurs.largeur, 3, 1, 8);
    const deroule = ent(valeurs.deroule, 0, 0, 1) === 1;
    const escalier = ent(valeurs.forme, 0, 0, 1) === 1;
    const NS = "http://www.w3.org/2000/svg";
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

    // Une seule echelle pour le quadrillage et la regle : elle ne depend que de L et l (basculer deroule ou
    // forme ne change jamais la taille d'un carreau). Le tour deplie doit tenir sur la regle (300 px).
    const P = 2 * (L + l);
    // Largeur de l'escalier : rangee k (k = 0 en bas) decalee de k carreaux si L >= 2 ; une colonne seule
    // (L = 1) se replie en equerre (moitie debout, moitie couchee), pour que les carreaux restent colles.
    const largeurEscalier = L >= 2 ? L + l - 1 : 1 + Math.floor(l / 2);
    // Une fiche sans curseur « deroule » (aires) n'a pas de regle, une fiche sans curseur « forme » (longueurs)
    // pas d'escalier : leurs contraintes ne retrecissent alors pas les carreaux. Dans la discussion, toutes les
    // valeurs sont presentes (normalisees), l'echelle est donc fixe quand on bascule.
    const avecRegle = valeurs.deroule !== undefined;
    const avecEscalier = valeurs.forme !== undefined;
    const hauteurMax = avecRegle ? 190 : 270;
    const u = Math.min(28, 300 / (avecEscalier ? largeurEscalier : L), hauteurMax / l, avecRegle ? 300 / P : 28);
    const X0 = 20, HAUT = 24;
    const BLEU = "#1F4E8C", ORANGE = "#E07B00", GRIS = "#6B7686";

    // Le papier quadrille en centimetres.
    const colonnes = Math.floor(300 / u), lignes = Math.floor(hauteurMax / u);
    for (let i = 0; i <= colonnes; i++) el("line", { x1: f(X0 + i * u), y1: HAUT, x2: f(X0 + i * u), y2: f(HAUT + lignes * u), stroke: "#E3E8EF", "stroke-width": 1 });
    for (let j = 0; j <= lignes; j++) el("line", { x1: X0, y1: f(HAUT + j * u), x2: f(X0 + colonnes * u), y2: f(HAUT + j * u), stroke: "#E3E8EF", "stroke-width": 1 });

    // Les carreaux [colonne, rangee depuis le bas] : toujours L x l carreaux, quelle que soit la forme.
    const carreaux = [];
    if (!escalier) {
      for (let k = 0; k < l; k++) for (let i = 0; i < L; i++) carreaux.push([i, k]);
    } else if (L >= 2) {
      for (let k = 0; k < l; k++) for (let i = 0; i < L; i++) carreaux.push([i + k, k]);
    } else {
      const debout = Math.ceil(l / 2);
      for (let k = 0; k < debout; k++) carreaux.push([0, k]);
      for (let i = 1; i <= l - debout; i++) carreaux.push([i, 0]);
    }
    const bas = HAUT + l * u;
    const X = (c) => X0 + c * u, Y = (r) => bas - r * u;
    for (const [c, r] of carreaux) {
      el("rect", { x: f(X(c)), y: f(Y(r + 1)), width: f(u), height: f(u), fill: "#DCE8F6", stroke: "#8FA6C4", "stroke-width": 1.5 });
    }

    if (escalier) {
      // Le contour de la nouvelle forme, d'un trait sombre : chaque bord de carreau qui n'a pas de voisin.
      const pris = new Set(carreaux.map(([c, r]) => `${c},${r}`));
      const libre = (c, r) => !pris.has(`${c},${r}`);
      const bord = (x1, y1, x2, y2) => el("line", { x1: f(x1), y1: f(y1), x2: f(x2), y2: f(y2), stroke: "#14243B", "stroke-width": 3, "stroke-linecap": "round" });
      for (const [c, r] of carreaux) {
        if (libre(c, r - 1)) bord(X(c), Y(r), X(c + 1), Y(r));
        if (libre(c, r + 1)) bord(X(c), Y(r + 1), X(c + 1), Y(r + 1));
        if (libre(c - 1, r)) bord(X(c), Y(r), X(c), Y(r + 1));
        if (libre(c + 1, r)) bord(X(c + 1), Y(r), X(c + 1), Y(r + 1));
      }
    } else {
      // Les quatre cotes : 2 longueurs (bleu) et 2 largeurs (orange) ; en pointilles gris quand le tour est deroule.
      const droite = X0 + L * u;
      const cote = (x1, y1, x2, y2, couleur) => el("line", {
        x1: f(x1), y1: f(y1), x2: f(x2), y2: f(y2), "stroke-linecap": "round",
        stroke: deroule ? GRIS : couleur, "stroke-width": deroule ? 2 : 4, "stroke-dasharray": deroule ? "5 4" : "none",
      });
      cote(X0, HAUT, droite, HAUT, BLEU);
      cote(X0, bas, droite, bas, BLEU);
      cote(X0, HAUT, X0, bas, ORANGE);
      cote(droite, HAUT, droite, bas, ORANGE);
    }

    if (deroule && !escalier) {
      // La regle graduee en cm (meme echelle que le quadrillage), et le tour deplie juste au-dessus.
      const R = 252, cm = Math.floor(300 / u);
      el("rect", { x: X0 - 8, y: R, width: f(cm * u + 16), height: 40, rx: 4, fill: "#FFF7E6", stroke: GRIS, "stroke-width": 2 });
      const tous = u >= 22 ? 1 : u >= 13 ? 2 : 5;
      for (let c = 0; c <= cm; c++) {
        const x = X0 + c * u;
        el("line", { x1: f(x), y1: R, x2: f(x), y2: R + (c % 5 === 0 ? 14 : 8), stroke: "#14243B", "stroke-width": c % 5 === 0 ? 2 : 1.5 });
        if (c % tous === 0) el("text", { x: f(x), y: R + 32, "font-size": 13, fill: "#14243B", "text-anchor": "middle", "font-family": "sans-serif" }, String(c));
      }
      let x = X0;
      [[L, BLEU], [l, ORANGE], [L, BLEU], [l, ORANGE]].forEach(([n, couleur]) => {
        el("line", { x1: f(x), y1: R - 10, x2: f(x + n * u), y2: R - 10, stroke: couleur, "stroke-width": 6 });
        x += n * u;
      });
      for (let i = 0, xs = X0, morceaux = [L, l, L, l]; i <= 4; i++) {
        el("line", { x1: f(xs), y1: R - 18, x2: f(xs), y2: R - 2, stroke: "#14243B", "stroke-width": 2 });
        if (i < 4) xs += morceaux[i] * u;
      }
    }

    el("text", { x: 20, y: 328, "font-size": 14, fill: GRIS, "font-family": "sans-serif" }, "un carreau : 1 cm de côté");
    return { L, l, deroule, escalier, u };
  },
};
