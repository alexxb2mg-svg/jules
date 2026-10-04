// Jules - gabarit "tube-digestif" : un aliment suit le tube digestif deroule, de la bouche a l'anus.
// Curseur : position (0 = bouche, 1 = anus). Etapes (memes bornes que les lectures de la fiche) :
//   0 - 0,2 bouche et oesophage : les dents broient, la salive commence la digestion ;
//   0,2 - 0,4 estomac : brassage avec le suc gastrique, bouillie ;
//   0,4 - 0,7 intestin grele : fin de la digestion, les nutriments traversent la paroi et passent dans le sang
//             (absorption) ;
//   0,7 - 1 gros intestin : ce qui n'a pas ete digere (fibres) forme les selles, evacuees par l'anus.
// Faits verifies :
// - programme de SVT du cycle 4 (annexe 3, arrete du 17-7-2020, eduscol.education.fr/document/621/download) :
//   « relier la nature des aliments et leurs apports qualitatifs et quantitatifs pour comprendre l'importance de
//   l'alimentation pour l'organisme » ; digestion, absorption des nutriments ;
// - Vikidia « Appareil digestif » : bouche, pharynx, oesophage, estomac, intestin grele, gros intestin (colon),
//   rectum, anus ; l'estomac brasse avec des sucs gastriques acides ;
// - fiche 3e svt devenir-aliments-tube-digestif (l'absorption se fait surtout dans l'intestin grele, pas dans
//   l'estomac ; les glandes annexes ne sont pas traversees par les aliments).
// Proportions des organes non respectees (l'intestin grele mesure environ 6 m) : schema, pas plan. revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["tube-digestif"] = {
  dessiner(svg, valeurs) {
    const position = Math.min(1, Math.max(0, Number(valeurs.position ?? 0)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const TUBE = "#DCE4EE", BORD = "#6B7686", ALIMENT = "#E07B00", NUTRIMENT = "#2E7D32", SANG = "#C8102E";
    const RESTE = "#6B7686"; // gris : ce qui n'est pas digere (fibres)
    // Trajet (ligne centrale du tube), par troncon, avec la plage du curseur qui lui correspond.
    const troncons = [
      { de: 0, a: 0.2, points: [[24, 62], [186, 62]] },
      { de: 0.2, a: 0.4, points: [[186, 62], [262, 64]] },
      { de: 0.4, a: 0.7, points: [[290, 70], [302, 80], [302, 128], [44, 128]] },
      { de: 0.7, a: 1, points: [[44, 128], [30, 128], [30, 222], [300, 222]] },
    ];
    const longueur = (pts) => pts.slice(1).reduce((s, p, i) => s + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);
    const surTrajet = (pts, f) => {
      let reste = f * longueur(pts);
      for (let i = 1; i < pts.length; i++) {
        const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
        if (reste <= l || i === pts.length - 1) {
          const g = l === 0 ? 0 : Math.min(1, reste / l);
          return { x: pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * g, y: pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * g };
        }
        reste -= l;
      }
      return { x: pts[0][0], y: pts[0][1] };
    };
    const trajet = troncons.flatMap((tr, i) => (i === 0 ? tr.points : tr.points.slice(1)));
    el("polyline", { points: trajet.map((p) => p.join(",")).join(" "), fill: "none", stroke: TUBE,
      "stroke-width": 20, "stroke-linejoin": "round", "stroke-linecap": "round" });
    // Estomac : une poche ; intestin grele : paroi plissee (villosites) ; gros intestin : tube plus large.
    el("ellipse", { cx: 230, cy: 66, rx: 46, ry: 26, fill: TUBE, stroke: BORD, "stroke-width": 2 });
    let plis = "";
    for (let x = 292; x >= 52; x -= 8) plis += `${x},${(x / 8) % 2 < 1 ? 134 : 140} `; // villosites, paroi du bas
    el("polyline", { points: plis.trim(), fill: "none", stroke: BORD, "stroke-width": 2 });
    el("polyline", { points: "30,140 30,222 300,222", fill: "none", stroke: TUBE, "stroke-width": 30,
      "stroke-linejoin": "round" });
    el("circle", { cx: 306, cy: 222, r: 5, fill: BORD });
    // Le sang, le long de l'intestin grele (en dehors du tube).
    el("line", { x1: 66, y1: 168, x2: 280, y2: 168, stroke: SANG, "stroke-width": 4 });
    el("text", { x: 288, y: 173, "font-size": 13, fill: SANG }, "sang");

    // Organe ou se trouve l'aliment : en gras ; les autres en gris.
    const etape = position < 0.2 ? 0 : position < 0.4 ? 1 : position < 0.7 ? 2 : 3;
    const noms = [
      [16, 34, "bouche", 0, "start"], [136, 34, "œsophage", 0, "middle"], [236, 26, "estomac", 1, "middle"],
      [160, 106, "intestin grêle", 2, "middle"], [165, 262, "gros intestin", 3, "middle"], [316, 262, "anus", 3, "end"],
    ];
    for (const [x, y, nom, k, ancre] of noms) {
      el("text", { x, y, "font-size": 14, "text-anchor": ancre, fill: k === etape ? "#14243B" : "#6B7686",
        "font-weight": k === etape ? "bold" : "normal" }, nom);
    }

    // Position de l'aliment sur le trajet.
    const tr = troncons[etape];
    const p = surTrajet(tr.points, (position - tr.de) / (tr.a - tr.de));
    const morceaux = (n, taille, couleur, rayon) => {
      for (let i = 0; i < n; i++) {
        const a = (2 * Math.PI * i) / n;
        const x = n === 1 ? p.x : p.x + rayon * Math.cos(a), y = n === 1 ? p.y : p.y + rayon * Math.sin(a);
        el("rect", { x: x - taille / 2, y: y - taille / 2, width: taille, height: taille, rx: 2, fill: couleur });
      }
    };
    if (position === 0) morceaux(1, 18, ALIMENT, 0);               // l'aliment entier
    else if (etape === 0) morceaux(3, 10, ALIMENT, 7);             // broye par les dents
    else if (etape === 1) morceaux(6, 6, ALIMENT, 9);              // brasse : bouillie
    else if (etape === 2) {
      // Les nutriments (verts) passent dans le sang : de moins en moins dans le tube, fleches vers le sang.
      // Avancement le long de la partie horizontale (la ou sont les villosites).
      const f = p.y >= 127 ? Math.min(1, Math.max(0, (292 - p.x) / 248)) : 0;
      const restants = Math.round(6 * (1 - f));
      for (let i = 0; i < restants; i++) {
        const a = (2 * Math.PI * i) / 6;
        el("circle", { cx: p.x + 8 * Math.cos(a), cy: p.y + 6 * Math.sin(a), r: 4, fill: NUTRIMENT });
      }
      el("circle", { cx: p.x + 2, cy: p.y, r: 5, fill: RESTE });
      if (p.y >= 127 && p.x > 60 && p.x < 284) {
        el("line", { x1: p.x, y1: 144, x2: p.x, y2: 156, stroke: NUTRIMENT, "stroke-width": 3 });
        el("polygon", { points: `${p.x - 6},154 ${p.x + 6},154 ${p.x},164`, fill: NUTRIMENT });
      }
      // Nutriments deja passes : points verts dans le sang, en arriere de l'aliment.
      const passes = Math.min(10, Math.round(10 * f));
      for (let i = 0; i < passes; i++) {
        el("circle", { cx: 270 - i * 21, cy: 168, r: 4, fill: NUTRIMENT, stroke: "#FFFFFF", "stroke-width": 2 });
      }
    } else {
      el("ellipse", { cx: p.x, cy: p.y, rx: 10, ry: 7, fill: RESTE });  // les restes non digeres : les selles
      for (let i = 0; i < 10; i++) {
        el("circle", { cx: 270 - i * 21, cy: 168, r: 4, fill: NUTRIMENT, stroke: "#FFFFFF", "stroke-width": 2 });
      }
    }
    const phrase = etape < 2 ? "digestion : l'aliment est découpé"
      : etape === 2 ? "absorption : les nutriments vont dans le sang" : "les restes forment les selles";
    el("text", { x: 170, y: 294, "font-size": 14, "text-anchor": "middle", fill: "#14243B", "font-weight": "bold" }, phrase);
    return { position, etape };
  },
};
