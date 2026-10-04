// Jules - gabarit "balance-plateaux" : balance a deux plateaux, un objet a gauche, une masse marquee de
// 500 g a droite. Le fleau penche du cote le plus lourd ; la taille de l'objet ne change rien.
// Curseurs : masse (masse de l'objet, g), taille (taille de l'objet, 1 petit a 5 tres gros).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["balance-plateaux"] = {
  dessiner(svg, valeurs) {
    const masse = Math.min(1000, Math.max(0, Number(valeurs.masse ?? 300)));
    const taille = Math.min(5, Math.max(1, Math.round(Number(valeurs.taille ?? 4))));
    const MASSE_MARQUEE = 500;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Inclinaison du fleau : positive = cote gauche plus bas ; proportionnelle a l'ecart, plafonnee a 14 degres.
    const ecart = Math.max(-1, Math.min(1, (masse - MASSE_MARQUEE) / 300));
    const alpha = (14 * ecart * Math.PI) / 180;
    const P = { x: 170, y: 214 }, BRAS = 112;
    const G = { x: P.x - BRAS * Math.cos(alpha), y: P.y + BRAS * Math.sin(alpha) };
    const D = { x: P.x + BRAS * Math.cos(alpha), y: P.y - BRAS * Math.sin(alpha) };

    // Pied et socle
    el("line", { x1: P.x, y1: P.y, x2: P.x, y2: 286, stroke: "#6B7686", "stroke-width": 6 });
    el("rect", { x: 110, y: 286, width: 120, height: 12, rx: 4, fill: "#6B7686" });
    // Repere fixe et aiguille (perpendiculaire au fleau) : alignes a l'equilibre.
    el("line", { x1: P.x, y1: P.y - 58, x2: P.x, y2: P.y - 48, stroke: "#6B7686", "stroke-width": 3 });
    el("line", {
      x1: P.x, y1: P.y, x2: P.x - 46 * Math.sin(alpha), y2: P.y - 46 * Math.cos(alpha),
      stroke: "#C8102E", "stroke-width": 3,
    });
    // Fleau
    el("line", { x1: G.x, y1: G.y, x2: D.x, y2: D.y, stroke: "#14243B", "stroke-width": 5, "stroke-linecap": "round" });
    el("circle", { cx: P.x, cy: P.y, r: 6, fill: "#14243B" });

    // Plateaux (au-dessus du fleau, tiges verticales) : y = haut du plateau.
    const plateau = (pt) => {
      const y = pt.y - 26;
      el("line", { x1: pt.x, y1: pt.y, x2: pt.x, y2: y, stroke: "#14243B", "stroke-width": 3 });
      el("rect", { x: pt.x - 46, y: y - 3, width: 92, height: 6, rx: 3, fill: "#14243B" });
      return y - 3;
    };
    const yg = plateau(G), yd = plateau(D);

    // Objet de gauche : un carton dont le cote grandit avec taille (sa masse ne depend que de masse).
    const cote = 22 + 12 * taille;
    el("rect", {
      x: G.x - cote / 2, y: yg - cote, width: cote, height: cote, rx: 3,
      fill: "#DCE6F3", stroke: "#1F4E8C", "stroke-width": 2.5,
    });
    // Masse marquee de droite : petit poids avec anneau.
    el("circle", { cx: D.x, cy: yd - 44, r: 6, fill: "none", stroke: "#6B7686", "stroke-width": 3 });
    el("path", { d: `M${D.x - 16},${yd - 38} h32 l8,38 h-48 z`, fill: "#6B7686" });

    // Etiquettes, sous le socle, dans la couleur de leur objet.
    el("text", { x: 60, y: 318, "font-size": 14, "text-anchor": "middle", fill: "#1F4E8C" }, "objet");
    el("text", { x: 60, y: 335, "font-size": 14, "text-anchor": "middle", fill: "#1F4E8C", "font-weight": "bold" }, `${masse} g`);
    el("text", { x: 280, y: 318, "font-size": 14, "text-anchor": "middle", fill: "#6B7686" }, "masse marquée");
    el("text", { x: 280, y: 335, "font-size": 14, "text-anchor": "middle", fill: "#6B7686", "font-weight": "bold" }, `${MASSE_MARQUEE} g`);
    return { masse, taille, penche: masse > MASSE_MARQUEE ? "gauche" : masse < MASSE_MARQUEE ? "droite" : "equilibre" };
  },
};
