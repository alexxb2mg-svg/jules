// Jules - gabarit "urne-tirage" : un sac de 10 boules, rouges (valeur rouges, 0 a 10) et bleues (les autres),
// et une echelle de probabilite « impossible ... une chance sur deux ... certain » ou une fleche montre la chance
// de tirer une boule rouge. Rien n'est calcule ni ecrit en fraction, et aucun verdict en mots : on voit la
// composition du sac et la fleche.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["urne-tirage"] = {
  dessiner(svg, valeurs) {
    const TOTAL = 10;
    const rouges = Math.min(TOTAL, Math.max(0, Math.round(Number(valeurs.rouges ?? 3))));
    const bleues = TOTAL - rouges;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 314"); // bas = « sur deux », seconde ligne de l'echelle (y 305)
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Le sac : corps arrondi, col resserre et lien.
    el("path", {
      d: "M120,40 C112,58 60,62 46,96 C30,136 34,190 70,206 C110,222 230,222 270,206 C306,190 310,136 294,96 C280,62 228,58 220,40 Z",
      fill: "#F4EFE6", stroke: "#6B7686", "stroke-width": 3, "stroke-linejoin": "round",
    });
    el("path", { d: "M114,40 Q170,30 226,40", fill: "none", stroke: "#6B7686", "stroke-width": 5, "stroke-linecap": "round" });

    // 10 boules en 2 rangees de 5 : d'abord les rouges, puis les bleues (bleues rayees pour ne pas dependre
    // de la seule couleur).
    for (let i = 0; i < TOTAL; i++) {
      const x = 82 + (i % 5) * 44, y = 108 + Math.floor(i / 5) * 48;
      const rouge = i < rouges;
      el("circle", { cx: x, cy: y, r: 18, fill: rouge ? "#C8102E" : "#1F4E8C", stroke: "#14243B", "stroke-width": 2 });
      if (!rouge) el("line", { x1: x - 11, y1: y + 6, x2: x + 11, y2: y - 6, stroke: "#FFFFFF", "stroke-width": 3 });
    }

    // Composition du sac, en mots.
    el("text", { x: 166, y: 236, "font-size": 16, "font-weight": 700, "text-anchor": "end", fill: "#C8102E" }, `${rouges} ${rouges > 1 ? "rouges" : "rouge"}`);
    el("text", { x: 174, y: 236, "font-size": 16, "font-weight": 700, fill: "#1F4E8C" }, `${bleues} ${bleues > 1 ? "bleues" : "bleue"}`);

    // Echelle de probabilite : de 30 (impossible) a 310 (certain).
    const X0 = 30, X1 = 310, Y = 266;
    el("line", { x1: X0, y1: Y, x2: X1, y2: Y, stroke: "#14243B", "stroke-width": 3, "stroke-linecap": "round" });
    // « une chance sur deux » sur deux lignes, pour laisser de la place a « impossible » et « certain ».
    for (const [t, lignes, ancre] of [[0, ["impossible"], "start"], [0.5, ["une chance", "sur deux"], "middle"], [1, ["certain"], "end"]]) {
      const x = X0 + t * (X1 - X0);
      el("line", { x1: x, y1: Y - 7, x2: x, y2: Y + 7, stroke: "#14243B", "stroke-width": 3 });
      lignes.forEach((texte, i) => {
        el("text", { x: x + (ancre === "start" ? -4 : ancre === "end" ? 4 : 0), y: Y + 22 + i * 17, "font-size": 14, "text-anchor": ancre, fill: "#14243B" }, texte);
      });
    }
    // Fleche rouge au-dessus de l'echelle, a la place de rouges ÷ 10.
    const xf = X0 + (rouges / TOTAL) * (X1 - X0);
    el("polygon", { points: `${xf - 9},${Y - 18} ${xf + 9},${Y - 18} ${xf},${Y - 5}`, fill: "#C8102E" });
    el("line", { x1: xf, y1: Y - 26, x2: xf, y2: Y - 16, stroke: "#C8102E", "stroke-width": 4 });
    // Pas de phrase verdict (« peu probable », « probable »...) : qualifier l'evenement en lisant la fleche est
    // l'exercice de l'eleve (fiche CM1), la figure montre sans l'ecrire.
    return { rouges };
  },
};
