// Jules - gabarit "reservoir-flux" : un stock (ressource naturelle, effectif d'une population) est un reservoir
// rempli par une entree (renouvellement, naissances et arrivees) et vide par une sortie (prelevement, deces et
// departs). Il monte si l'entree depasse la sortie, reste stable si elles sont egales, baisse sinon.
// Curseurs : entree, sortie (en % du stock de depart, par an, 0 a 20).
// Modele simplifie, volontairement lineaire : stock(t) = 100 + (entree - sortie) x t, en % du stock de depart,
// sur 20 ans, borne a 0 (stock epuise) et a 200 (maximum que le milieu peut porter : une ressource ou une
// population ne grandit pas sans limite, voir la fiche « dynamique des populations », bloc courbe).
// Aucune valeur de reponse n'est ecrite : seuls les curseurs (« +10 % par an ») et le sens de variation le sont.
// Sources des idees : programme de SVT cycle 4 (annexe 3, arrete du 17-7-2020), themes « exploitation des
// ressources naturelles » (gestion durable : prelever moins vite que le renouvellement) et « dynamique des
// populations » (l'effectif varie avec naissances, deces et migrations).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun code
// evalue.
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["reservoir-flux"] = {
  dessiner(svg, valeurs) {
    const borne = (v, d) => Math.min(20, Math.max(0, Math.round(Number(v ?? d)) || 0));
    const entree = borne(valeurs.entree, 10);
    const sortie = borne(valeurs.sortie, 12);
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

    const VERT = "#2E7D32", ROUGE = "#C8102E", BLEU = "#1F4E8C", GRIS = "#6B7686", TEXTE = "#14243B";
    const ANNEES = 20, MAXI = 200;
    const solde = entree - sortie;
    const stock = (t) => Math.min(MAXI, Math.max(0, 100 + solde * t));

    // --- Reservoir (a gauche) : niveau apres 20 ans, trait pointille au niveau de depart.
    const RX = 30, RL = 100, RH = 70, RB = 230; // bord gauche, largeur, haut, bas
    const yNiveau = (s) => RB - ((RB - RH) * s) / MAXI;
    const fin = stock(ANNEES);
    if (fin > 0) {
      el("rect", { x: RX, y: yNiveau(fin), width: RL, height: RB - yNiveau(fin), fill: BLEU, "fill-opacity": 0.35 });
    }
    el("path", { d: `M ${RX} ${RH} V ${RB} H ${RX + RL} V ${RH}`, fill: "none", stroke: GRIS, "stroke-width": 3 });
    el("line", { x1: RX - 6, y1: yNiveau(100), x2: RX + RL + 6, y2: yNiveau(100), stroke: TEXTE, "stroke-width": 2, "stroke-dasharray": "5 4" });
    el("text", { x: RX + RL / 2, y: yNiveau(100) - 6, "font-size": 13, "text-anchor": "middle", fill: TEXTE }, "départ");
    el("text", { x: RX + RL / 2, y: RB + 20, "font-size": 13, "text-anchor": "middle", fill: BLEU, "font-weight": "bold" }, "stock dans 20 ans");

    // Entree : fleche verte qui tombe dans le reservoir, epaisseur proportionnelle au curseur.
    const xE = RX + 30;
    el("text", { x: 8, y: 22, "font-size": 14, fill: VERT, "font-weight": "bold" }, "entrée");
    el("text", { x: 8, y: 40, "font-size": 13, fill: VERT }, `+${entree} % par an`);
    if (entree > 0) {
      const ep = 2 + entree * 0.6;
      el("line", { x1: xE, y1: 48, x2: xE, y2: RH + 22, stroke: VERT, "stroke-width": ep });
      el("path", { d: `M ${xE - ep / 2 - 6} ${RH + 18} L ${xE + ep / 2 + 6} ${RH + 18} L ${xE} ${RH + 32} Z`, fill: VERT });
    }

    // Sortie : fleche rouge qui part du bas du reservoir vers la droite.
    const yS = RB - 14;
    el("text", { x: 8, y: 276, "font-size": 14, fill: ROUGE, "font-weight": "bold" }, "sortie");
    el("text", { x: 8, y: 294, "font-size": 13, fill: ROUGE }, `−${sortie} % par an`);
    if (sortie > 0) {
      const ep = 2 + sortie * 0.6;
      el("line", { x1: RX + RL - 20, y1: yS, x2: RX + RL + 22, y2: yS, stroke: ROUGE, "stroke-width": ep });
      el("path", { d: `M ${RX + RL + 18} ${yS - ep / 2 - 6} L ${RX + RL + 18} ${yS + ep / 2 + 6} L ${RX + RL + 32} ${yS} Z`, fill: ROUGE });
    }

    // --- Courbe du stock sur 20 ans (a droite).
    const GX = 190, GD = 326, GH = 70, GB = 230;
    const gx = (t) => GX + ((GD - GX) * t) / ANNEES;
    const gy = (s) => GB - ((GB - GH) * s) / MAXI;
    el("line", { x1: GX, y1: GB, x2: GD, y2: GB, stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: GX, y1: GB, x2: GX, y2: GH - 6, stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: GX, y1: gy(MAXI), x2: GD, y2: gy(MAXI), stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "2 4" });
    el("text", { x: GD, y: gy(MAXI) - 6, "font-size": 13, "text-anchor": "end", fill: GRIS }, "maximum du milieu");
    el("line", { x1: GX, y1: gy(100), x2: GD, y2: gy(100), stroke: TEXTE, "stroke-width": 2, "stroke-dasharray": "5 4" });
    el("text", { x: GX + 4, y: GB + 18, "font-size": 13, fill: TEXTE }, "0");
    el("text", { x: GD, y: GB + 18, "font-size": 13, "text-anchor": "end", fill: TEXTE }, "20 ans");
    el("text", { x: (GX + GD) / 2, y: 36, "font-size": 14, "text-anchor": "middle", fill: BLEU, "font-weight": "bold" }, "le stock");
    const points = [];
    for (let t = 0; t <= ANNEES; t += 0.5) points.push(`${gx(t).toFixed(1)},${gy(stock(t)).toFixed(1)}`);
    el("polyline", { points: points.join(" "), fill: "none", stroke: BLEU, "stroke-width": 4, "stroke-linejoin": "round" });

    // Sens de variation, en mots (pas de nombre calcule).
    let message, couleur;
    if (solde > 0) { message = "entrée > sortie : le stock augmente"; couleur = VERT; }
    else if (solde === 0) { message = "entrée = sortie : le stock reste stable"; couleur = TEXTE; }
    else if (fin === 0) { message = "sortie > entrée : le stock s'épuise"; couleur = ROUGE; }
    else { message = "sortie > entrée : le stock diminue"; couleur = ROUGE; }
    el("text", { x: 170, y: 326, "font-size": 14, "text-anchor": "middle", fill: couleur, "font-weight": "bold" }, message);
    return { entree, sortie, solde, stock_final: fin };
  },
};
