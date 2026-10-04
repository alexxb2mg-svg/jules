// Jules - gabarit "trace-geste" : une trace de peinture sur une feuille, vue de face.
// amplitude (1 a 5) = taille du geste : la trace s'allonge et ondule davantage ;
// pression (1 a 5) = force d'appui : la trace s'epaissit et se fonce ;
// hasard (0 a 5) = part d'imprevu : la trace tremble, des coulures et des projections apparaissent.
// Le « hasard » est un tirage fixe (meme graine a chaque dessin) : la meme position des curseurs donne toujours
// la meme trace, et augmenter le hasard ajoute des taches sans deplacer les precedentes.
// Faits (EX-205) : rien n'est chiffre. Vocabulaire du programme d'arts plastiques (cycle 3 : « les effets du geste
// et de l'instrument » ; cycle 4 : « la relation du corps a la production artistique », geste, trace, dripping de
// Pollock), Eduscol, programmes 2020 cycles 3 et 4.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["trace-geste"] = {
  dessiner(svg, valeurs) {
    const borne = (v, mini, maxi, defaut) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(maxi, Math.max(mini, Math.round(n))) : defaut;
    };
    const amplitude = borne(valeurs.amplitude, 1, 5, 3);
    const pression = borne(valeurs.pression, 1, 5, 3);
    const hasard = borne(valeurs.hasard, 0, 5, 1);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 280");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Tirage pseudo-aleatoire fixe (generateur congruentiel), valeurs dans [0, 1[.
    let graine = 12345;
    const tirage = () => {
      graine = (graine * 1103515245 + 12345) % 2147483648;
      return graine / 2147483648;
    };
    const bruit = Array.from({ length: 41 }, () => tirage() * 2 - 1);
    const taches = Array.from({ length: 40 }, () => [tirage(), tirage() * 2 - 1, tirage()]);
    const coulures = Array.from({ length: 10 }, () => [tirage(), tirage()]);

    // La feuille.
    const F = { x: 14, y: 14, l: 312, h: 252 };
    el("rect", { x: F.x, y: F.y, width: F.l, height: F.h, rx: 4, fill: "#FBF8F2", stroke: "#6B7686", "stroke-width": 2 });

    // Le trace : de 70 (poignet) a 270 (tout le corps) de long, centre sur la feuille, une vague plus ou moins ample.
    const longueur = 20 + 50 * amplitude;
    const vague = 6 + 9 * amplitude;
    const tremble = 4 * hasard;
    const CX = 170, CY = 130, N = 40;
    const points = [];
    for (let i = 0; i <= N; i++) {
      const s = i / N;
      const x = CX - longueur / 2 + longueur * s;
      const y = CY + vague * Math.sin(Math.PI * 1.5 * s - 0.4) + tremble * bruit[i];
      points.push([x, y]);
    }
    const chemin = points.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
    const epaisseur = 2 + 3.5 * pression;
    const opacite = (0.45 + 0.11 * pression).toFixed(2);
    el("path", {
      d: chemin, fill: "none", stroke: "#1F4E8C", "stroke-width": epaisseur, "stroke-opacity": opacite,
      "stroke-linecap": "round", "stroke-linejoin": "round",
    });

    // Coulures : la peinture descend sous le trace (une par cran de hasard, plus longues si on appuie fort).
    for (let k = 0; k < Math.min(hasard * 2, coulures.length); k++) {
      const [ou, lg] = coulures[k];
      const [x, y] = points[Math.round(ou * N)];
      const bas = Math.min(F.y + F.h - 12, y + epaisseur / 2 + 12 + lg * (18 + 6 * pression));
      el("line", { x1: x, y1: y, x2: x, y2: bas, stroke: "#1F4E8C", "stroke-width": Math.max(2, epaisseur / 3), "stroke-opacity": opacite, "stroke-linecap": "round" });
      el("circle", { cx: x, cy: bas, r: Math.max(2, epaisseur / 4), fill: "#1F4E8C", "fill-opacity": opacite });
    }
    // Projections : des gouttes autour du trace, de plus en plus loin quand le geste est libre.
    for (let k = 0; k < Math.min(hasard * 8, taches.length); k++) {
      const [ou, ecart, taille] = taches[k];
      const [x, y] = points[Math.round(ou * N)];
      const ty = Math.min(F.y + F.h - 10, Math.max(F.y + 10, y + ecart * (epaisseur + 10 + 9 * hasard)));
      el("circle", { cx: x.toFixed(1), cy: ty.toFixed(1), r: (2 + taille * (1 + pression)).toFixed(1), fill: "#1F4E8C", "fill-opacity": opacite });
    }
    return { amplitude, pression, hasard };
  },
};
