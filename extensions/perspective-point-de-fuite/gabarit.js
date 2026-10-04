// Jules - gabarit "perspective-point-de-fuite" : perspective a un point de fuite sur une feuille.
// Curseurs : horizon (hauteur de la ligne d'horizon sur la feuille, en %, 10 = en bas, 90 = en haut) et fuite
// (position du point de fuite, de -5 a gauche a 5 a droite). Une tour et un cube poses au sol, un cube suspendu
// et une route : toutes les fuyantes (en pointilles) vont au point de fuite, place SUR la ligne d'horizon.
// Regles dessinees (perspective centrale, un point de fuite) : le point de fuite est sur la ligne d'horizon, a
// hauteur des yeux ; un objet dont le dessus est sous l'horizon montre sa face du dessus, un objet tout entier
// au-dessus de l'horizon montre sa face du dessous ; on voit le cote tourne vers le point de fuite.
// Sources : programme d'arts plastiques du cycle 4, « La representation » (dispositifs de representation,
// espace suggere), BO n° 31 du 30 juillet 2020 ; Leon Battista Alberti, De pictura (1435), premier traite de la
// perspective centrale ; Eduscol, ressources arts plastiques cycle 4 « la representation ».
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["perspective-point-de-fuite"] = {
  dessiner(svg, valeurs) {
    const borne = (v, min, max) => Math.min(max, Math.max(min, v));
    const horizon = borne(Number(valeurs.horizon ?? 50), 10, 90);
    const fuite = borne(Number(valeurs.fuite ?? 0), -5, 5);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E";
    const FACE = "#C9D8EE", FUYANTE = "#E8EEF7", ROUTE = "#DADDE2";

    svg.setAttribute("viewBox", "0 0 340 300");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    // Feuille : x 10..330, y 10..290 ; horizon en % de la hauteur de la feuille depuis le bas.
    const HAUT = 10, BAS = 290;
    const vy = BAS - (horizon / 100) * (BAS - HAUT);
    const vx = 170 + fuite * 30;
    const K = 0.72; // profondeur des boites : la face arriere est la face avant ramenee vers le point de fuite
    const vers = ([x, y]) => [vx + (x - vx) * K, vy + (y - vy) * K];
    const pts = (liste) => liste.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");

    el("rect", { x: 10, y: HAUT, width: 320, height: BAS - HAUT, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });

    // Route au sol : ses deux bords partent du bas de la feuille et se rejoignent au point de fuite.
    el("polygon", { points: pts([[118, BAS], [222, BAS], [vx, vy]]), fill: ROUTE, stroke: GRIS, "stroke-width": 2 });

    // Boites : face avant [x1, x2] x [y1, y2].
    const BOITES = [
      [30, 90, 140, 270], // tour posee au sol
      [244, 304, 206, 262], // cube pose au sol
      [232, 282, 40, 84], // cube suspendu
    ];
    // Fuyantes : des coins de la face avant jusqu'au point de fuite.
    for (const [x1, x2, y1, y2] of BOITES) {
      for (const [x, y] of [[x1, y1], [x2, y1], [x1, y2], [x2, y2]]) {
        el("line", { x1: x, y1: y, x2: vx, y2: vy, stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "4 5", opacity: 0.5 });
      }
    }
    // Ligne d'horizon (derriere les objets).
    el("line", { x1: 10, y1: vy, x2: 330, y2: vy, stroke: BLEU, "stroke-width": 3 });

    for (const [x1, x2, y1, y2] of BOITES) {
      const a = [x1, y1], b = [x2, y1], c = [x2, y2], d = [x1, y2];
      const faces = [];
      if (y1 > vy) faces.push([a, b, vers(b), vers(a)]); // dessus visible
      if (y2 < vy) faces.push([d, c, vers(c), vers(d)]); // dessous visible
      if (vx < x1) faces.push([a, d, vers(d), vers(a)]); // cote gauche visible
      if (vx > x2) faces.push([b, c, vers(c), vers(b)]); // cote droit visible
      for (const f of faces) el("polygon", { points: pts(f), fill: FUYANTE, stroke: BLEU, "stroke-width": 2 });
      el("polygon", { points: pts([a, b, c, d]), fill: FACE, stroke: BLEU, "stroke-width": 2 });
    }

    // Point de fuite et legendes (halo blanc pour rester lisibles sur le dessin).
    el("circle", { cx: vx, cy: vy, r: 6, fill: ROUGE });
    const halo = { stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke" };
    const yHorizon = vy - 8 < 30 ? vy + 20 : vy - 8;
    const gauche = vx > 170;
    el("text", { x: gauche ? 16 : 324, y: yHorizon, "font-size": 14, fill: BLEU, "text-anchor": gauche ? "start" : "end", ...halo },
      "ligne d'horizon");
    const yFuite = vy < 60 ? vy + 24 : vy - 14;
    el("text", { x: borne(vx, 62, 278), y: yFuite, "font-size": 14, "font-weight": "bold", fill: ROUGE,
      "text-anchor": "middle", ...halo }, "point de fuite");
    return { horizon, fuite, vx, vy: Math.round(vy) };
  },
};
