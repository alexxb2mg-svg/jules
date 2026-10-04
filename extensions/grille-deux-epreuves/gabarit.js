// Jules - gabarit "grille-deux-epreuves" : tableau a double entree des issues de deux des (p faces et q faces).
// Chaque case est un couple (1er de ; 2e de), equiprobable si les des sont equilibres ; on y ecrit la somme des
// deux faces. Les cases dont la somme vaut s sont coloriees en bleu : l'eleve compte les cases favorables et
// le total p × q. Ni le nombre de cases favorables ni la probabilite ne sont ecrits, mais la figure fait le
// denombrement (revele: true).
// Fait verifie : deux des a 6 faces donnent 36 couples equiprobables ; somme 7 : 6 couples (la plus frequente),
// sommes 2 et 12 : 1 couple chacune. Programme de mathematiques du cycle 4 (BO n° 31 du 30/07/2020), theme
// « probabilites » : experiences aleatoires a deux epreuves, arbre ou tableau ; attendus de fin de 3e, eduscol.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["grille-deux-epreuves"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const n = Number(v ?? defaut);
      return Math.min(max, Math.max(min, Math.round(Number.isFinite(n) ? n : defaut)));
    };
    const p = entier(valeurs.p, 6, 2, 6);
    const q = entier(valeurs.q, 6, 2, 6);
    const s = entier(valeurs.s, 7, 2, 12);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686";
    const C = 40, X0 = 70, Y0 = 72; // coin haut gauche de la premiere case
    svg.setAttribute("viewBox", "0 0 340 320");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Titres des deux epreuves.
    el("text", { x: X0 + (q * C) / 2, y: 22, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, "2e dé");
    const titre1 = el("text", { x: 20, y: Y0 + (p * C) / 2, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, "1er dé");
    titre1.setAttribute("transform", `rotate(-90 20 ${Y0 + (p * C) / 2})`);

    // En-tetes : faces de chaque de, et « + » dans le coin.
    el("text", { x: X0 - C / 2, y: Y0 - 14, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: GRIS }, "+");
    for (let j = 1; j <= q; j++) {
      el("text", { x: X0 + (j - 0.5) * C, y: Y0 - 14, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, String(j));
    }
    for (let i = 1; i <= p; i++) {
      el("text", { x: X0 - C / 2, y: Y0 + (i - 0.5) * C + 6, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, String(i));
    }

    // Cases : une par couple (i ; j), somme ecrite, coloriee si i + j = s.
    for (let i = 1; i <= p; i++) {
      for (let j = 1; j <= q; j++) {
        const x = X0 + (j - 1) * C, y = Y0 + (i - 1) * C, favorable = i + j === s;
        el("rect", { x, y, width: C, height: C, fill: favorable ? BLEU : "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
        el("text", { x: x + C / 2, y: y + C / 2 + 6, "font-size": 16, "font-weight": favorable ? 700 : 400, "text-anchor": "middle", fill: favorable ? "#FFFFFF" : ENCRE }, String(i + j));
      }
    }
    el("rect", { x: X0, y: Y0, width: q * C, height: p * C, fill: "none", stroke: ENCRE, "stroke-width": 2 });
    return { p, q, s };
  },
};
