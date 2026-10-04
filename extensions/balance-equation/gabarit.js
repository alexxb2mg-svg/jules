// Jules - gabarit "balance-equation" : balance de l'equation ax + b = c, curseur x = valeur essayee.
// Curseurs : paquets (a, nombre de boites « x »), gauche (b, jetons a gauche), droite (c, jetons a droite), x.
// Noms en mots et non a, b, c : dans les fiches, a designe deja le nombre connu de x² = a.
// A gauche a boites « x » et b jetons, a droite c jetons ; la balance penche du cote le plus lourd et
// devient horizontale (fleau vert, signe =) quand ax + b = c. La solution n'est jamais ecrite.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["balance-equation"] = {
  dessiner(svg, valeurs) {
    const borne = (v, defaut, min, max) => {
      const n = Number(v ?? defaut);
      return Math.min(max, Math.max(min, Number.isFinite(n) ? n : defaut));
    };
    const a = Math.round(borne(valeurs.paquets, 3, 1, 5));
    const b = Math.round(borne(valeurs.gauche, 2, 0, 10));
    const c = Math.round(borne(valeurs.droite, 17, 0, 30));
    const x = borne(valeurs.x, 3, 0, 10);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const fmt = (n) => String(Math.round(n * 100) / 100).replace(".", ",").replace("-", "\u2212");
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";

    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // L'equation, ecrite avec les lettres (jamais la solution).
    const gauche = (a === 1 ? "x" : `${a}x`) + (b > 0 ? ` + ${b}` : "");
    el("text", { x: 170, y: 30, "font-size": 20, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, `${gauche} = ${c}`);

    // Poids des deux plateaux : une boite pese x, un jeton pese 1.
    const poidsG = a * x + b, poidsD = c;
    const ecart = Math.round((poidsG - poidsD) * 100) / 100;
    const equilibre = ecart === 0;
    const degres = equilibre ? 0 : Math.sign(ecart) * Math.min(10, 3 + Math.abs(ecart) * 0.7);
    const t = (degres * Math.PI) / 180;
    const P = { x: 170, y: 222 }, L = 104;
    const finG = { x: P.x - L * Math.cos(t), y: P.y + L * Math.sin(t) }; // cote lourd = plus bas
    const finD = { x: P.x + L * Math.cos(t), y: P.y - L * Math.sin(t) };

    // Pied (gris) puis fleau (vert a l'equilibre).
    el("polygon", { points: `${P.x},${P.y} ${P.x - 22},264 ${P.x + 22},264`, fill: "#DDE2E9", stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: 116, y1: 264, x2: 224, y2: 264, stroke: GRIS, "stroke-width": 3, "stroke-linecap": "round" });
    el("line", { x1: finG.x, y1: finG.y, x2: finD.x, y2: finD.y, stroke: equilibre ? VERT : ENCRE, "stroke-width": 5, "stroke-linecap": "round" });
    el("circle", { cx: P.x, cy: P.y, r: 5, fill: equilibre ? VERT : ENCRE });

    // Plateau (reste horizontal, pose sur un montant) ; renvoie le haut du plateau.
    const plateau = (fin) => {
      const haut = fin.y - 20;
      el("line", { x1: fin.x, y1: fin.y, x2: fin.x, y2: haut, stroke: GRIS, "stroke-width": 3 });
      el("rect", { x: fin.x - 58, y: haut - 3, width: 116, height: 6, rx: 3, fill: GRIS });
      return haut - 3;
    };
    const jetons = (n, cx, bas) => {
      const parLigne = 7;
      for (let i = 0; i < n; i++) {
        const ligne = Math.floor(i / parLigne), rang = i % parLigne;
        const dansLigne = Math.min(parLigne, n - ligne * parLigne);
        el("circle", { cx: cx + (rang - (dansLigne - 1) / 2) * 16, cy: bas - 8 - ligne * 16, r: 6.5, fill: ORANGE, stroke: "#FFFFFF", "stroke-width": 1 });
      }
    };

    // Gauche : a boites « x » (bleu) posees sur le plateau, b jetons (orange) au-dessus.
    const hautG = plateau(finG);
    for (let i = 0; i < a; i++) {
      const bx = finG.x + (i - (a - 1) / 2) * 23 - 10;
      el("rect", { x: bx, y: hautG - 25, width: 20, height: 24, rx: 3, fill: BLEU });
      el("text", { x: bx + 10, y: hautG - 8, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: "#FFFFFF" }, "x");
    }
    jetons(b, finG.x, hautG - 26);

    // Droite : c jetons.
    const hautD = plateau(finD);
    jetons(c, finD.x, hautD);

    // Comparaison des poids, avec la valeur essayee (pas la solution).
    const calcul = a === 1 && b === 0 ? `x = ${fmt(x)}`
      : (a === 1 ? fmt(x) : `${a} \u00d7 ${fmt(x)}`) + (b > 0 ? ` + ${b}` : "") + ` = ${fmt(poidsG)}`;
    el("text", { x: 76, y: 290, "font-size": 15, "text-anchor": "middle", fill: BLEU }, calcul);
    el("text", { x: 170, y: 292, "font-size": 24, "font-weight": 700, "text-anchor": "middle", fill: equilibre ? VERT : ROUGE },
      equilibre ? "=" : ecart < 0 ? "<" : ">");
    el("text", { x: 266, y: 290, "font-size": 15, "text-anchor": "middle", fill: ORANGE }, fmt(poidsD));
    return { paquets: a, gauche: b, droite: c, x };
  },
};
