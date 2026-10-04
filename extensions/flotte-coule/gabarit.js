// Jules - gabarit "flotte-coule" : un bloc pose dans un becher d'eau, avec une jauge de sa masse.
// Curseurs : masse_volumique (g/cm3 du bloc), volume (cm3 du bloc).
// - masse_volumique < 1 : le bloc flotte ; la part immergee vaut masse_volumique / 1 (equilibre de flottaison,
//   poussee d'Archimede = poids : rho_bloc x V = rho_eau x V_immerge) ;
// - masse_volumique = 1 : le bloc reste entre deux eaux ; > 1 : il coule et repose au fond.
// - volume : le cote du cube est proportionnel a la racine cubique du volume ; la jauge de masse (sans nombre ecrit)
//   monte avec m = masse_volumique x volume, mais flotter ou couler ne depend que de la masse volumique.
// Faits : masse volumique de l'eau 1 g/cm3 (0,998 g/cm3 a 20 degres, arrondie a 1 au college), relation
// m = rho x V et comparaison a la masse volumique du liquide pour flotter / couler : programme de physique-chimie
// du cycle 4 (BO n° 31 du 30 juillet 2020, « Caracteriser les etats de la matiere », masse volumique),
// https://eduscol.education.fr/document/621/download ; flottaison : principe d'Archimede (manuels de 3e).
// La masse m n'est jamais ecrite (m = rho x V est un calcul d'exercice) : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["flotte-coule"] = {
  dessiner(svg, valeurs) {
    // arrondi au dixieme (pas du curseur) : 1 doit valoir exactement 1 pour « entre deux eaux »
    const rho = Math.round(10 * Math.min(8, Math.max(0.2, Number(valeurs.masse_volumique ?? 0.9)))) / 10;
    const volume = Math.min(100, Math.max(10, Number(valeurs.volume ?? 30)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const fr = (x) => String(Math.round(x * 10) / 10).replace(".", ",");
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Becher : parois de x 30 a 230, fond a y 250 ; surface de l'eau a y 100.
    const G = 30, D = 230, FOND = 250, SURFACE = 100;
    el("rect", { x: G, y: SURFACE, width: D - G, height: FOND - SURFACE, fill: "#D6E6F5" });
    el("path", { d: `M${G},40 V${FOND} H${D} V40`, fill: "none", stroke: "#6B7686", "stroke-width": 3 });
    el("text", { x: D - 8, y: SURFACE + 22, "font-size": 14, "text-anchor": "end", fill: "#1F4E8C" }, "eau : 1 g/cm³");

    // Bloc : cube de cote proportionnel a la racine cubique du volume (30 a 65 px).
    const cote = 14 * Math.cbrt(volume);
    let bas;
    if (rho < 1) bas = SURFACE + rho * cote; // flotte : la part immergee est rho / 1
    else if (rho === 1) bas = (SURFACE + FOND) / 2 + cote / 2; // entre deux eaux
    else bas = FOND - 1.5; // coule : repose au fond
    const xb = 100 - cote / 2;
    el("rect", {
      x: xb, y: bas - cote, width: cote, height: cote, rx: 3,
      fill: "#E07B00", "fill-opacity": 0.85, stroke: "#14243B", "stroke-width": 2,
    });
    // Ligne de la surface redessinee par-dessus le bloc (on voit ce qui depasse de l'eau).
    el("line", { x1: G, y1: SURFACE, x2: D, y2: SURFACE, stroke: "#1F4E8C", "stroke-width": 2.5 });

    // Jauge de masse (sans nombre) : m = rho x V, de 2 g a 800 g -> hauteur de 0 a 180 px.
    const m = rho * volume;
    const HJ = 180, BJ = FOND;
    el("rect", { x: 270, y: BJ - HJ, width: 34, height: HJ, rx: 4, fill: "none", stroke: "#6B7686", "stroke-width": 2 });
    const h = Math.max(3, (HJ * m) / 800);
    el("rect", { x: 272, y: BJ - h, width: 30, height: h, rx: 3, fill: "#E07B00" });
    el("text", { x: 287, y: BJ - HJ - 10, "font-size": 14, "text-anchor": "middle", fill: "#14243B" }, "masse");
    el("text", { x: 287, y: BJ + 20, "font-size": 13, "text-anchor": "middle", fill: "#6B7686" }, "du bloc");

    // Valeurs des curseurs, dans la couleur du bloc.
    el("text", { x: 30, y: 280, "font-size": 15, fill: "#E07B00", "font-weight": "bold" }, `ρ = ${fr(rho)} g/cm³`);
    el("text", { x: 160, y: 280, "font-size": 15, fill: "#14243B" }, `V = ${fr(volume)} cm³`);
    return { masse_volumique: rho, volume, etat: rho < 1 ? "flotte" : rho === 1 ? "entre-deux-eaux" : "coule" };
  },
};
