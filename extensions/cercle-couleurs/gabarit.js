// Jules - gabarit "cercle-couleurs" : cercle chromatique du peintre a 12 secteurs (0 = rouge, 120 = jaune,
// 240 = bleu, tous les 30 degres). teinte = couleur choisie (repere qui tourne, complementaire allumee en face,
// a teinte + 180) ; blanc = part de blanc ajoutee, en % (la valeur) ; surface = taille de l'aplat (1 = petite
// touche ... 5 = grande surface). Revele : le nom de la couleur, son type et sa complementaire sont ecrits.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["cercle-couleurs"] = {
  dessiner(svg, valeurs) {
    const borne = (v, min, max) => Math.min(max, Math.max(min, v));
    const indice = ((Math.round(Number(valeurs.teinte ?? 0) / 30) % 12) + 12) % 12;
    const blanc = borne(Number(valeurs.blanc ?? 0), 0, 100);
    const surface = borne(Math.round(Number(valeurs.surface ?? 3)), 1, 5);
    // Cercle du peintre (primaires rouge, jaune, bleu), couleurs proches du cercle d'Itten.
    const COULEURS = [
      ["rouge", "#E32322"], ["rouge-orangé", "#EA621F"], ["orange", "#F18E1C"], ["jaune-orangé", "#FDC60B"],
      ["jaune", "#F4E500"], ["jaune-vert", "#8CBB26"], ["vert", "#008E5B"], ["bleu-vert", "#0696BB"],
      ["bleu", "#2A71B0"], ["bleu-violet", "#444E99"], ["violet", "#6D398B"], ["rouge-violet", "#C4037D"],
    ];
    const TYPES = ["primaire", "intermédiaire", "secondaire", "intermédiaire"];
    const face = (indice + 6) % 12;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const C = { x: 170, y: 128 };
    const point = (angle, r) => {
      const a = ((angle - 90) * Math.PI) / 180; // 0 degre en haut, sens des aiguilles d'une montre
      return [C.x + r * Math.cos(a), C.y + r * Math.sin(a)];
    };
    const secteur = (i, rIn, rOut) => {
      const [a, b] = [i * 30 - 15, i * 30 + 15];
      const p = [point(a, rOut), point(b, rOut), point(b, rIn), point(a, rIn)].map((q) => q.map((v) => v.toFixed(1)));
      return `M${p[0]} A${rOut},${rOut} 0 0 1 ${p[1]} L${p[2]} A${rIn},${rIn} 0 0 0 ${p[3]} Z`;
    };
    // Melange avec du blanc : chaque composante se rapproche de 255.
    const eclaircir = (hex, part) => "#" + [1, 3, 5].map((k) => {
      const v = parseInt(hex.slice(k, k + 2), 16);
      return Math.round(v + (255 - v) * (part / 100)).toString(16).padStart(2, "0");
    }).join("");

    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    COULEURS.forEach(([, couleur], i) => {
      const choisi = i === indice;
      el("path", { d: secteur(i, 50, choisi ? 106 : 96), fill: couleur, stroke: "#FFFFFF", "stroke-width": 2 });
    });
    // Le trait qui relie la couleur choisie a sa complementaire, en passant par le centre.
    const [xa, ya] = point(indice * 30, 50), [xb, yb] = point(face * 30, 50);
    el("line", { x1: xa, y1: ya, x2: xb, y2: yb, stroke: "#14243B", "stroke-width": 2, "stroke-dasharray": "5 4" });
    el("path", { d: secteur(indice, 50, 106), fill: "none", stroke: "#14243B", "stroke-width": 4 });
    el("path", { d: secteur(face, 50, 96), fill: "none", stroke: "#14243B", "stroke-width": 3, "stroke-dasharray": "6 4" });
    const [xr, yr] = point(indice * 30, 112);
    const [xr1, yr1] = point(indice * 30 - 6, 122), [xr2, yr2] = point(indice * 30 + 6, 122);
    el("polygon", { points: `${xr},${yr} ${xr1},${yr1} ${xr2},${yr2}`, fill: "#14243B" });

    // L'aplat : la couleur choisie, eclaircie par le blanc, sur une feuille ; sa taille suit la surface.
    const F = { x: 14, y: 240, l: 140, h: 92 };
    el("rect", { x: F.x, y: F.y, width: F.l, height: F.h, rx: 4, fill: "#FFFFFF", stroke: "#6B7686", "stroke-width": 2 });
    const cote = [14, 30, 48, 66, 84][surface - 1];
    const hauteur = Math.min(cote, F.h - 8);
    const largeur = Math.min(F.l - 8, cote * 1.4);
    el("rect", {
      x: F.x + (F.l - largeur) / 2, y: F.y + (F.h - hauteur) / 2, width: largeur, height: hauteur,
      fill: eclaircir(COULEURS[indice][1], blanc),
    });

    const [nom] = COULEURS[indice];
    const T = { x: 166 };
    el("text", { x: T.x, y: 258, "font-size": 18, "font-weight": 700, fill: "#14243B" }, nom[0].toUpperCase() + nom.slice(1));
    el("text", { x: T.x, y: 280, "font-size": 14, fill: "#14243B" }, `couleur ${TYPES[indice % 4]}`);
    el("text", { x: T.x, y: 302, "font-size": 14, fill: "#14243B" }, `en face : ${COULEURS[face][0]}`);
    el("text", { x: T.x, y: 324, "font-size": 14, fill: "#6B7686" }, blanc > 0 ? `+ ${blanc} % de blanc` : "couleur pure");
    return { teinte: indice * 30, complementaire: face * 30, blanc, surface };
  },
};
