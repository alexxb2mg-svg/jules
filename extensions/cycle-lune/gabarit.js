// Jules - gabarit "cycle-lune" : phases de la Lune. En haut, la Lune tourne autour de la Terre, eclairee par
// le Soleil (a droite) ; en bas, la Lune telle qu'on la voit depuis la Terre. Curseur jour (0 a 29) depuis
// la nouvelle lune, lunaison de 29,5 jours.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["cycle-lune"] = {
  dessiner(svg, valeurs) {
    const jour = Math.min(29, Math.max(0, Number(valeurs.jour ?? 7)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ECLAIRE = "#FFE08A", SOMBRE = "#6B7686", LUMIERE = "#E07B00";
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Angle de la Lune sur son orbite : 0 = entre la Terre et le Soleil (nouvelle lune), sens inverse des
    // aiguilles d'une montre vu depuis le pole Nord (en haut au premier quartier).
    const theta = (2 * Math.PI * jour) / 29.5;

    // --- Vue de dessus : Soleil a droite, Terre, orbite, Lune ---
    const T = { x: 135, y: 106 }, R = 70;
    el("text", { x: 300, y: 24, "font-size": 14, "text-anchor": "middle", fill: LUMIERE, "font-weight": "bold" }, "Soleil");
    for (const y of [50, 106, 162]) {
      el("line", { x1: 330, y1: y, x2: 262, y2: y, stroke: LUMIERE, "stroke-width": 2.5 });
      el("path", { d: `M262,${y} l9,-5 v10 z`, fill: LUMIERE });
    }
    el("circle", { cx: T.x, cy: T.y, r: R, fill: "none", stroke: SOMBRE, "stroke-width": 2, "stroke-dasharray": "4 5" });
    const L = { x: T.x + R * Math.cos(theta), y: T.y - R * Math.sin(theta) };
    el("line", { x1: T.x, y1: T.y, x2: L.x, y2: L.y, stroke: "#1F4E8C", "stroke-width": 2, "stroke-dasharray": "3 4" });
    el("circle", { cx: T.x, cy: T.y, r: 22, fill: "#1F4E8C" });
    el("text", { x: T.x, y: T.y + 4.5, "font-size": 13, "text-anchor": "middle", fill: "#FFFFFF", "font-weight": "bold" }, "Terre");
    // La Lune vue de dessus : toujours eclairee du cote du Soleil (moitie droite).
    const r = 13;
    el("circle", { cx: L.x, cy: L.y, r, fill: SOMBRE });
    el("path", { d: `M${L.x},${L.y - r} A${r},${r} 0 0 1 ${L.x},${L.y + r} Z`, fill: ECLAIRE });
    el("circle", { cx: L.x, cy: L.y, r, fill: "none", stroke: "#14243B", "stroke-width": 2 });
    const ex = L.x + 27 * Math.cos(theta), ey = L.y - 27 * Math.sin(theta) + 5;
    el("text", { x: ex, y: ey, "font-size": 13, "text-anchor": "middle", fill: "#14243B", stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke" }, "Lune");

    // --- Vue depuis la Terre ---
    el("line", { x1: 10, y1: 220, x2: 330, y2: 220, stroke: "#C9D1DC", "stroke-width": 2 });
    el("text", { x: 14, y: 256, "font-size": 14, fill: "#14243B" }, "Vue depuis");
    el("text", { x: 14, y: 274, "font-size": 14, fill: "#14243B" }, "la Terre");
    const C = { x: 190, y: 276 }, RV = 50;
    el("circle", { cx: C.x, cy: C.y, r: RV, fill: SOMBRE });
    // Partie eclairee visible : bord eclaire (droite en lune croissante, gauche en decroissante) puis le
    // terminateur, demi-ellipse de demi-axe horizontal RV*|cos(theta)|.
    const c = Math.cos(theta), croissante = theta <= Math.PI;
    const visible = (1 - c) / 2;
    if (visible > 0.01) {
      const rx = Math.abs(c) * RV;
      const bord = croissante ? 1 : 0; // haut -> bas par la droite (1) ou par la gauche (0)
      const terminateur = croissante ? (c > 0 ? 0 : 1) : (c < 0 ? 0 : 1);
      el("path", {
        d: `M${C.x},${C.y - RV} A${RV},${RV} 0 0 ${bord} ${C.x},${C.y + RV} A${rx},${RV} 0 0 ${terminateur} ${C.x},${C.y - RV} Z`,
        fill: ECLAIRE,
      });
    }
    el("circle", { cx: C.x, cy: C.y, r: RV, fill: "none", stroke: "#14243B", "stroke-width": 2 });
    el("text", { x: 326, y: 256, "font-size": 14, "text-anchor": "end", fill: "#14243B" }, "jour");
    el("text", { x: 326, y: 276, "font-size": 16, "text-anchor": "end", fill: "#14243B", "font-weight": "bold" }, String(jour));
    return { jour, visible };
  },
};
