// Jules - gabarit "barre-vote" : inscrits, votants et voix, en petits bonshommes puis en une barre.
// inscrits = nombre de bonshommes (10 a 100) ; votants = ceux qui votent (ramene au nombre d'inscrits), les
// autres sont gris (abstention) ; voix = votants qui choisissent le candidat A (ramene au nombre de votants),
// en orange ; les autres votants sont en bleu. La barre du bas reprend les memes parts, avec un repere a la moitie
// des votants : la part orange depasse le repere = majorite absolue.
// Aucun nombre n'est ecrit (on compte les bonshommes) : la figure ne fait pas le calcul a la place de l'eleve.
// Faits (EX-205) : abstention = inscrits qui ne votent pas ; majorite absolue = plus de la moitie des suffrages
// exprimes (ici tous les votants, sans bulletin blanc ni nul) ; election presidentielle et legislatives au scrutin
// majoritaire a deux tours : Constitution, art. 7 (president : majorite absolue des suffrages exprimes au premier
// tour, sinon second tour) ; Code electoral, art. L126 (deputes : au premier tour, majorite absolue des exprimes ET
// un quart des inscrits ; au second tour, la majorite relative suffit).
// Sources relues le 04/10/2026 : texte de l'article 7 cite dans Wikipedia « Article 7 de la Constitution de la
// Cinquieme Republique francaise » ; regle des 25 % d'inscrits dans Wikipedia « Elections legislatives en France »
// (le numero L126 n'y figure pas : a recouper sur Legifrance, inaccessible en script) ; Eduscol, programme d'EMC
// cycles 3 et 4 (2024).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["barre-vote"] = {
  dessiner(svg, valeurs) {
    const borne = (v, mini, maxi, defaut) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(maxi, Math.max(mini, Math.round(n))) : defaut;
    };
    const inscrits = borne(valeurs.inscrits, 10, 100, 100);
    const votants = Math.min(inscrits, borne(valeurs.votants, 0, 100, 70));
    const voix = Math.min(votants, borne(valeurs.voix, 0, 100, 30));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const ORANGE = "#E07B00", BLEU = "#1F4E8C", GRIS = "#C9CED6";
    // Grille de bonshommes : 6 colonnes jusqu'a 30 inscrits, 10 au-dela ; ordre de lecture : voix, autres votants,
    // abstention.
    const colonnes = inscrits <= 30 ? 6 : 10;
    const rangees = Math.ceil(inscrits / colonnes);
    const cellule = Math.min(320 / colonnes, 200 / rangees);
    const X0 = 170 - (colonnes * cellule) / 2, Y0 = 8;
    const echelle = cellule / 30;
    for (let i = 0; i < inscrits; i++) {
      const cx = X0 + (i % colonnes + 0.5) * cellule;
      const cy = Y0 + (Math.floor(i / colonnes) + 0.5) * cellule;
      const couleur = i < voix ? ORANGE : i < votants ? BLEU : GRIS;
      el("circle", { cx: cx.toFixed(1), cy: (cy - 7 * echelle).toFixed(1), r: (5.5 * echelle).toFixed(1), fill: couleur });
      el("path", {
        d: `M${(cx - 9 * echelle).toFixed(1)},${(cy + 12 * echelle).toFixed(1)} Q${cx.toFixed(1)},${(cy - 6 * echelle).toFixed(1)} ${(cx + 9 * echelle).toFixed(1)},${(cy + 12 * echelle).toFixed(1)} Z`,
        fill: couleur,
      });
    }

    // La barre : toute la largeur = les inscrits ; orange = voix de A, bleu = autres votants, gris = abstention.
    const BX = 20, BL = 300, BY = 230, BHt = 30;
    const largeur = (n) => (n / inscrits) * BL;
    el("rect", { x: BX, y: BY, width: BL, height: BHt, fill: GRIS });
    if (votants > 0) el("rect", { x: BX, y: BY, width: largeur(votants).toFixed(1), height: BHt, fill: BLEU });
    if (voix > 0) el("rect", { x: BX, y: BY, width: largeur(voix).toFixed(1), height: BHt, fill: ORANGE });
    el("rect", { x: BX, y: BY, width: BL, height: BHt, fill: "none", stroke: "#14243B", "stroke-width": 2 });
    // Repere a la moitie des votants (rouge), dessine des qu'il y a des votants.
    if (votants > 0) {
      const xm = BX + largeur(votants / 2);
      el("line", { x1: xm, y1: BY - 8, x2: xm, y2: BY + BHt + 8, stroke: "#C8102E", "stroke-width": 3 });
      const ancre = xm < 80 ? "start" : xm > 260 ? "end" : "middle";
      el("text", { x: xm.toFixed(1), y: BY + BHt + 24, "font-size": 14, "text-anchor": ancre, fill: "#C8102E" }, "moitié des votants");
    }

    // Legende : seulement les couleurs presentes.
    const legende = [[ORANGE, "voix pour A"], [BLEU, "autres voix"]];
    if (votants < inscrits) legende.push([GRIS, "ne vote pas"]);
    // Trois cases de 110 de large : « ne vote pas » finit avant le bord droit, meme a 240 px de large.
    legende.forEach(([couleur, mot], k) => {
      const x = 12 + k * 110;
      el("rect", { x, y: 314, width: 14, height: 14, fill: couleur });
      el("text", { x: x + 19, y: 326, "font-size": 14, fill: "#14243B" }, mot);
    });
    return { inscrits, votants, voix };
  },
};
