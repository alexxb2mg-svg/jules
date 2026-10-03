// Jules - gabarit "effort-frequences" : pendant un effort, les besoins du muscle en dioxygene et en glucose
// augmentent ; le coeur et la respiration accelerent pour les apporter, jusqu'a un plafond.
// Curseurs : activite (intensite de l'effort, 0 = repos, 100 = effort maximal d'une personne non entrainee :
// le meme effort pour les deux personnes), entraine (0 non, 1 oui).
// Modele simplifie (valeurs d'ordre de grandeur pour un adolescent, frequence cardiaque maximale environ
// 220 - 15 = 205) : non entraine FC = 70 + 1,5 x activite (plafond 205), FR = 15 + 0,4 x activite (plafond 50) ;
// entraine FC = 60 + 1,2 x activite, FR = 12 + 0,3 x activite (coeur plus efficace : moins de battements
// pour le meme effort).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["effort-frequences"] = {
  dessiner(svg, valeurs) {
    const activite = Math.min(100, Math.max(0, Number(valeurs.activite ?? 0)));
    const entraine = Number(valeurs.entraine ?? 0) >= 1 ? 1 : 0;
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

    const FC_MAX = 205, FR_MAX = 50;
    const fc = (a) => (entraine ? 60 + 1.2 * a : Math.min(FC_MAX, 70 + 1.5 * a));
    const fr = (a) => (entraine ? 12 + 0.3 * a : Math.min(FR_MAX, 15 + 0.4 * a));
    const besoin = (a) => 8 + 0.92 * a; // part de la jauge, en %
    const BAS = 250, HAUT = 60, H = BAS - HAUT;
    const barres = [
      { x: 60, couleur: "#E07B00", part: (a) => besoin(a) / 100, lignes: ["muscle", "besoins O₂", "et glucose"], valeur: null },
      { x: 170, couleur: "#C8102E", part: (a) => fc(a) / 220, lignes: ["cœur", "battements", "par minute"], valeur: fc },
      { x: 280, couleur: "#1F4E8C", part: (a) => fr(a) / 60, lignes: ["respiration", "mouvements", "par minute"], valeur: fr },
    ];

    // Titre seulement si le curseur « entraine » existe (une fiche peut ne proposer que l'activite).
    if (valeurs.entraine !== undefined) {
      el("text", { x: 170, y: 26, "font-size": 14, "text-anchor": "middle", fill: "#14243B", "font-weight": "bold" },
        entraine ? "personne entraînée" : "personne non entraînée");
    }
    el("line", { x1: 14, y1: BAS, x2: 326, y2: BAS, stroke: "#6B7686", "stroke-width": 2 });
    for (const b of barres) {
      const haut = BAS - H * b.part(activite);
      el("rect", { x: b.x - 23, y: HAUT, width: 46, height: H, fill: "none", stroke: "#C9D1DC", "stroke-width": 2 });
      el("rect", { x: b.x - 23, y: haut, width: 46, height: BAS - haut, fill: b.couleur });
      const repos = BAS - H * b.part(0);
      el("line", { x1: b.x - 30, y1: repos, x2: b.x + 30, y2: repos, stroke: "#14243B", "stroke-width": 2, "stroke-dasharray": "4 3" });
      if (b.valeur) {
        el("text", { x: b.x, y: haut - 7, "font-size": 15, "text-anchor": "middle", fill: b.couleur, "font-weight": "bold" },
          String(Math.round(b.valeur(activite))));
      }
      b.lignes.forEach((t, i) => {
        el("text", {
          x: b.x, y: 272 + 17 * i, "font-size": 13, "text-anchor": "middle",
          fill: i === 0 ? b.couleur : "#14243B", "font-weight": i === 0 ? "bold" : "normal",
        }, t);
      });
    }
    // Plafond de la frequence cardiaque (environ 220 - age).
    const yMax = BAS - (H * FC_MAX) / 220;
    el("line", { x1: 140, y1: yMax, x2: 200, y2: yMax, stroke: "#C8102E", "stroke-width": 2, "stroke-dasharray": "2 3" });
    el("text", { x: 204, y: yMax + 5, "font-size": 13, fill: "#C8102E" }, "max");
    el("line", { x1: 74, y1: 330, x2: 98, y2: 330, stroke: "#14243B", "stroke-width": 2, "stroke-dasharray": "4 3" });
    el("text", { x: 104, y: 335, "font-size": 13, fill: "#14243B" }, "niveau au repos");
    return { activite, entraine, fc: Math.round(fc(activite)), fr: Math.round(fr(activite)) };
  },
};
