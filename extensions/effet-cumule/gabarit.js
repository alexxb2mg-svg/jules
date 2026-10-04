// Jules - gabarit "effet-cumule" : une cour d'ecole vue de dessus ; chaque jour, chaque eleve qui jette un papier
// en ajoute un par terre. personnes (1 a 25) = eleves qui jettent un papier chaque jour ; jours (1 a 5) = jours
// d'ecole qui passent. Il y a personnes x jours papiers dans la cour, poses a des places fixes (un papier deja
// tombe ne bouge plus quand on avance d'un jour). Le total n'est jamais ecrit : on voit la cour se salir.
// Une rangee de cinq cases montre les jours deja passes.
// Faits (EX-205) : rien n'est chiffre ; notions du programme d'EMC cycle 3 (respect des regles de vie collective,
// civilite et incivilites), Eduscol, programme d'EMC 2024. Les cases disent « jour 1 a 5 » et non « lundi a
// vendredi » : beaucoup d'ecoles elementaires ont une semaine de quatre jours.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["effet-cumule"] = {
  dessiner(svg, valeurs) {
    const borne = (v, mini, maxi, defaut) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(maxi, Math.max(mini, Math.round(n))) : defaut;
    };
    const personnes = borne(valeurs.personnes, 1, 25, 1);
    const jours = borne(valeurs.jours, 1, 5, 1);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 320");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Les jours : cinq cases, bleues pour les jours passes.
    for (let j = 0; j < 5; j++) {
      const x = 20 + j * 62;
      const passe = j < jours;
      el("rect", { x, y: 8, width: 52, height: 34, rx: 5, fill: passe ? "#1F4E8C" : "#FFFFFF", stroke: "#1F4E8C", "stroke-width": 2 });
      el("text", { x: x + 26, y: 30, "font-size": 14, "font-weight": 700, "text-anchor": "middle", fill: passe ? "#FFFFFF" : "#1F4E8C" }, `jour ${j + 1}`);
    }

    // La cour : sol clair, un arbre dans son carre de terre et un banc, dessines avant les papiers.
    const C = { x: 14, y: 54, l: 312, h: 258 };
    el("rect", { x: C.x, y: C.y, width: C.l, height: C.h, rx: 6, fill: "#E9E4DA", stroke: "#6B7686", "stroke-width": 2 });
    el("rect", { x: 254, y: 70, width: 56, height: 56, fill: "#D8CDB8", stroke: "#6B7686", "stroke-width": 2 });
    el("circle", { cx: 282, cy: 98, r: 22, fill: "#2E7D32" });
    el("rect", { x: 30, y: 280, width: 90, height: 16, rx: 3, fill: "#B5895A", stroke: "#6B7686", "stroke-width": 2 });

    // Les papiers : 125 places tirees une fois pour toutes (generateur congruentiel a graine fixe), hors de l'arbre
    // et du banc ; on en montre personnes x jours, dans l'ordre (jour 1 d'abord).
    let graine = 2026;
    const tirage = () => {
      graine = (graine * 1103515245 + 12345) % 2147483648;
      return graine / 2147483648;
    };
    const places = [];
    while (places.length < 125) {
      const x = C.x + 14 + tirage() * (C.l - 28);
      const y = C.y + 12 + tirage() * (C.h - 24);
      const angle = Math.round(tirage() * 80 - 40);
      const surArbre = x > 246 && x < 318 && y < 134;
      const surBanc = x > 22 && x < 128 && y > 272;
      if (!surArbre && !surBanc) places.push([x, y, angle]);
    }
    const papiers = personnes * jours;
    for (let k = 0; k < papiers; k++) {
      const [x, y, angle] = places[k];
      el("rect", {
        x: (x - 7).toFixed(1), y: (y - 5).toFixed(1), width: 14, height: 10, rx: 1.5,
        fill: "#FFFFFF", stroke: "#C8102E", "stroke-width": 2,
        transform: `rotate(${angle} ${x.toFixed(1)} ${y.toFixed(1)})`,
      });
    }
    return { personnes, jours };
  },
};
