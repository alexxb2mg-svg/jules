// Jules - gabarit "mots-par-regard" : copier une phrase. La phrase est dessinee en blocs-mots ; des arcs bleus
// regroupent les mots retenus en un seul regard. Curseurs : taille (mots memorises par regard, 1 a 5) et mots
// (longueur de la phrase a copier, 10 a 30). Plus on retient de mots par regard, moins les yeux font
// d'allers-retours entre le modele et le cahier : le compteur et la rangee de points (un point = un regard) le
// montrent.
// Faits : nombre de regards = mots / taille arrondi a l'entier superieur (un dernier groupe incomplet coute un
// regard). Le programme de francais du cycle 3 (arrete du 10-4-2025, CM1, « Écrire à la main de manière fluide et
// efficace ») fixe l'objectif « Acquérir des stratégies de copie » ; la fiche CM1 « L'écriture attachée et la copie »
// (d'apres Eduscol, « Exemples pour la mise en œuvre du programme de français en CM1 », 2025) recommande des groupes
// de 3 a 5 mots qui vont ensemble : c'est la zone verte du curseur. Les largeurs des blocs sont fictives (aucun
// texte reel), les groupes sont de taille fixe : la fiche rappelle de couper aux groupes de sens.
// revele false : le compteur donne un nombre de regards, pas la reponse d'un exercice de copie.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["mots-par-regard"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00", VERT = "#2E7D32";
    const borne = (v, min, max, d) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : d;
    };
    const taille = Math.round(borne(valeurs.taille, 1, 5, 1));
    const mots = Math.round(borne(valeurs.mots, 10, 30, 20));
    const regards = Math.ceil(mots / taille);
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 24, "font-size": 17, "font-weight": "bold", "text-anchor": "middle", fill: BLEU },
      taille === 1 ? "1 mot par regard" : `${taille} mots par regard`);
    el("text", { x: 14, y: 50, "font-size": 13, fill: GRIS }, "le modèle :");

    // Blocs-mots : 10 par ligne, largeurs fictives variees (somme 262 px + 9 espaces de 5 px = 307 px).
    const LARGEURS = [22, 14, 32, 18, 28, 12, 22, 34, 16, 26].map((w) => w * 1.1);
    const pos = [];
    for (let i = 0; i < mots; i++) {
      const lig = Math.floor(i / 10), col = i % 10;
      let x = 16;
      for (let c = 0; c < col; c++) x += LARGEURS[c] + 5;
      pos.push({ x, w: LARGEURS[col], y: 82 + lig * 50, lig });
    }
    for (const p of pos) {
      el("rect", { x: p.x, y: p.y, width: p.w, height: 18, rx: 3, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
    }
    // Un arc par regard (coupe en deux s'il passe a la ligne).
    for (let g = 0; g < regards; g++) {
      const debut = g * taille, fin = Math.min(mots, debut + taille) - 1;
      let i = debut;
      while (i <= fin) {
        let j = i;
        while (j + 1 <= fin && pos[j + 1].lig === pos[i].lig) j++;
        const x1 = pos[i].x + 2, x2 = pos[j].x + pos[j].w - 2, y = pos[i].y - 3;
        el("path", { d: `M${x1},${y} Q${(x1 + x2) / 2},${y - 22} ${x2},${y}`, fill: "none", stroke: BLEU, "stroke-width": 2.5 });
        i = j + 1;
      }
    }

    // Compteur d'allers-retours : un point par regard.
    const couleur = taille >= 3 ? VERT : ORANGE; // 3 a 5 mots par regard : ce que la fiche recommande
    el("text", { x: 14, y: 240, "font-size": 14, fill: ENCRE }, "allers-retours des yeux :");
    el("text", { x: 190, y: 240, "font-size": 17, "font-weight": "bold", fill: couleur }, String(regards));
    for (let r = 0; r < regards; r++) {
      el("circle", { cx: 20 + r * 10, cy: 262, r: 4, fill: couleur });
    }
    return { taille, mots, regards };
  },
};
