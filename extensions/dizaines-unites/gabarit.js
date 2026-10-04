// Jules - gabarit "dizaines-unites" : un nombre de 0 a 99 dessine en barres de dix (bleues) et en cubes seuls
// (orange), avec ses chiffres de la meme couleur. Valeur : n. Sert a dire les nombres en anglais : une barre de
// plus a chaque dizaine, ce qui distingue thirteen (1 barre et 3 cubes) de thirty (3 barres).
// La figure n'ecrit jamais le nombre en lettres (ni en francais ni en anglais) : l'eleve le dit, les lectures de
// la fiche donnent la regle (-teen, -ty, trait d'union).
// Faits : thirteen a nineteen en -teen, twenty a ninety en -ty ; de 21 a 99, si l'unite n'est pas zero, deux mots
// relies par un trait d'union (twenty-three) : Wikipedia anglais, « English numerals », consulte le 04/10/2026.
// Accent : thirteen /ˌθɜːˈtiːn/ (fort sur -teen) contre thirty /ˈθɜːti/ (fort au debut), Wiktionary anglais.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["dizaines-unites"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00";
    const brut = Number(valeurs.n ?? 23);
    const n = Math.min(99, Math.max(0, Math.round(Number.isFinite(brut) ? brut : 23)));
    const dizaines = Math.floor(n / 10), unites = n % 10;
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 310");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Les chiffres : dizaines en bleu, unites en orange (rien en bleu sous 10).
    if (dizaines > 0) {
      el("text", { x: 168, y: 52, "font-size": 42, "font-weight": 700, "text-anchor": "end", fill: BLEU }, String(dizaines));
      el("text", { x: 172, y: 52, "font-size": 42, "font-weight": 700, "text-anchor": "start", fill: ORANGE }, String(unites));
    } else {
      el("text", { x: 170, y: 52, "font-size": 42, "font-weight": 700, "text-anchor": "middle", fill: ORANGE }, String(unites));
    }

    const BAS = 280, H = 18, L = 22;
    // Barres de dix : 10 cubes empiles, de gauche a droite.
    for (let i = 0; i < dizaines; i++) {
      const x = 14 + i * 28;
      el("rect", { x, y: BAS - 10 * H, width: L, height: 10 * H, fill: "#C9D6EA", stroke: BLEU, "stroke-width": 2 });
      for (let k = 1; k < 10; k++) {
        el("line", { x1: x, y1: BAS - k * H, x2: x + L, y2: BAS - k * H, stroke: BLEU, "stroke-width": 1 });
      }
    }
    // Separation entre les dizaines et les unites.
    el("line", { x1: 280, y1: 88, x2: 280, y2: BAS, stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "6 5" });
    // Cubes seuls (unites), empiles a droite.
    for (let k = 0; k < unites; k++) {
      el("rect", { x: 298, y: BAS - (k + 1) * H, width: L, height: H, fill: "#F6D9B5", stroke: ORANGE, "stroke-width": 2 });
    }
    el("text", { x: 140, y: 302, "font-size": 14, "text-anchor": "middle", fill: BLEU }, "dizaines");
    el("text", { x: 309, y: 302, "font-size": 14, "text-anchor": "middle", fill: ORANGE }, "unités");
    return { n, dizaines, unites };
  },
};
