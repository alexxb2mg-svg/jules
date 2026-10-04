// Jules - gabarit "jetons-en-rangees" : `jetons` jetons ranges par rangees de `rangee`. Les rangees pleines sont
// bleues (leur nombre = le quotient), les jetons qui restent sont orange (leur nombre = le reste) et les places
// vides de la derniere rangee sont en pointilles : on voit que le reste est toujours plus petit que la rangee.
// Aucun jeton orange = la division tombe juste (rangee est un diviseur de jetons). Seules les deux donnees sont
// ecrites ; quotient et reste se comptent, ils ne sont jamais ecrits.
// Quand il y a beaucoup de rangees, elles sont empilees en plusieurs colonnes (de gauche a droite).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["jetons-en-rangees"] = {
  // dessiner(svg, valeurs) : jetons de 1 a 100, rangee (taille d'une rangee, le diviseur) de 1 a 12.
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => {
      const x = Number(v ?? d);
      return Math.min(maxi, Math.max(mini, Math.round(Number.isFinite(x) ? x : d)));
    };
    const jetons = ent(valeurs.jetons, 36, 1, 100);
    const rangee = ent(valeurs.rangee, 5, 1, 12);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (x) => x.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00";
    const pleines = Math.floor(jetons / rangee);
    const reste = jetons % rangee;
    const total = pleines + (reste > 0 ? 1 : 0);

    el("text", { x: 170, y: 22, "font-size": 15, "font-weight": "bold", fill: ENCRE, "text-anchor": "middle", "font-family": "sans-serif" },
      `${jetons} jeton${jetons > 1 ? "s" : ""}, rangées de ${rangee}`);

    // Disposition : `piles` colonnes de rangees empilees ; on garde celle qui donne les plus gros jetons.
    const L = 316, H = 258, ECART = 0.9, PAS_V = 1.3; // ECART entre colonnes et PAS_V entre rangees, en jetons
    let meilleur = { piles: 1, parPile: total, s: 0 };
    for (let piles = 1; piles <= total; piles++) {
      const parPile = Math.ceil(total / piles);
      const s = Math.min(34, L / (piles * rangee + (piles - 1) * ECART), H / (parPile * PAS_V));
      if (s > meilleur.s + 1e-9) meilleur = { piles, parPile, s };
    }
    const { piles, parPile, s } = meilleur;
    const largeur = piles * rangee * s + (piles - 1) * ECART * s;
    const X0 = (340 - largeur) / 2, Y0 = 40;
    const rayon = s * 0.36;

    for (let k = 0; k < total; k++) {
      const pile = Math.floor(k / parPile), ligne = k % parPile;
      const x = X0 + pile * (rangee + ECART) * s;
      const y = Y0 + ligne * PAS_V * s;
      const pleine = k < pleines;
      // Le fond de la rangee : plein et bleu pale pour une rangee pleine, en pointilles pour la derniere.
      el("rect", {
        x: f(x + 1), y: f(y + 1), width: f(rangee * s - 2), height: f(s - 2), rx: f(Math.min(8, s / 3)),
        fill: pleine ? "#DCE8F6" : "#FFF7E6", stroke: pleine ? "#8FA6C4" : GRIS, "stroke-width": 2,
        "stroke-dasharray": pleine ? "none" : "4 3",
      });
      for (let i = 0; i < rangee; i++) {
        const cx = x + (i + 0.5) * s, cy = y + s / 2;
        if (pleine) el("circle", { cx: f(cx), cy: f(cy), r: f(rayon), fill: BLEU });
        else if (i < reste) el("circle", { cx: f(cx), cy: f(cy), r: f(rayon), fill: ORANGE });
        else el("circle", { cx: f(cx), cy: f(cy), r: f(rayon), fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "3 3" });
      }
    }

    // Legende : une couleur = une idee.
    el("circle", { cx: 26, cy: 322, r: 7, fill: BLEU });
    el("text", { x: 38, y: 327, "font-size": 13, fill: ENCRE, "font-family": "sans-serif" }, "rangée pleine");
    el("circle", { cx: 160, cy: 322, r: 7, fill: ORANGE });
    el("text", { x: 172, y: 327, "font-size": 13, fill: ENCRE, "font-family": "sans-serif" }, "jeton qui reste");
    return { jetons, rangee, pleines, reste, piles, s };
  },
};
