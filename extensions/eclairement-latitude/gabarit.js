// Jules - gabarit "eclairement-latitude" : la Terre vue de cote, eclairee par le Soleil (a gauche) a midi.
// Deux faisceaux de rayons de MEME largeur arrivent sur deux lieux a la meme distance de l'equateur, l'un au nord
// (latitude lat), l'autre au sud (latitude -lat). Plus les rayons arrivent inclines, plus le faisceau s'etale
// sur le sol et plus la tache est pale (energie recue par m2 proportionnelle au cosinus de l'angle d'incidence).
// Curseurs : lat (0 a 90 degres), mois (1 a 12 : la Terre est dessinee le 21 du mois ; son axe penche vers le
// Soleil en juin, a l'oppose en decembre). Les zones climatiques (chaude, temperee, polaire) sont reperees au
// bord droit de la Terre, limites aux tropiques (23,5 degres) et aux cercles polaires (66,5 degres), comme le
// schema de la fiche « meteo, climat et zones climatiques ».
// Faits verifies (EX-205) :
// - Declinaison du Soleil (latitude ou il est a la verticale a midi) : formule de Cooper (1969, « The absorption
//   of radiation in solar stills », Solar Energy 12), d = 23,45 x sin(360 x (284 + N) / 365), N = numero du jour ;
//   l'amplitude est prise ici egale a l'obliquite actuelle de l'axe, 23,44 degres. Elle vaut ~+23,4 le 21 juin,
//   ~-23,4 le 21 decembre, ~0 aux equinoxes (21 mars, 21 septembre, a moins d'un degre pres).
// - Programme de SVT cycle 4 (Eduscol, annexe 3, arrete du 17-7-2020) : « meteorologie et climatologie, grandes
//   zones climatiques » ; inegale repartition de l'energie solaire selon la latitude.
// - Saisons opposees des deux hemispheres : consequence de l'inclinaison de l'axe (23,44 degres).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["eclairement-latitude"] = {
  dessiner(svg, valeurs) {
    const lat = Math.min(90, Math.max(0, Number(valeurs.lat ?? 40)));
    const mois = Math.min(12, Math.max(1, Math.round(Number(valeurs.mois ?? 3))));
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

    const RAD = Math.PI / 180;
    const JOURS_AVANT = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
    const N = JOURS_AVANT[mois - 1] + 21; // le 21 du mois
    const decl = 23.44 * Math.sin((360 * (284 + N) / 365) * RAD);
    const NOMS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];

    const CX = 170, CY = 158, R = 100;
    // Point de latitude phi : cote jour (midi) ou cote nuit (minuit), dans le repere ou le Soleil est a gauche.
    const midi = (phi) => [CX - R * Math.cos((phi - decl) * RAD), CY - R * Math.sin((phi - decl) * RAD)];
    const minuit = (phi) => [CX + R * Math.cos((phi + decl) * RAD), CY - R * Math.sin((phi + decl) * RAD)];

    el("text", { x: 12, y: 22, "font-size": 15, "font-weight": "bold", fill: "#14243B" }, `le 21 ${NOMS[mois - 1]}`);
    el("text", { x: 12, y: 290, "font-size": 13, fill: "#E07B00" }, "rayons du Soleil");

    // Terre, moitie nuit a droite.
    el("circle", { cx: CX, cy: CY, r: R, fill: "#EEF3F9", stroke: "#1F4E8C", "stroke-width": 2 });
    el("path", { d: `M ${CX} ${CY - R} A ${R} ${R} 0 0 1 ${CX} ${CY + R} Z`, fill: "#14243B", "fill-opacity": 0.18 });

    // Zones climatiques reperees sur le bord droit (hemisphere nord etiquete, sud colorie de meme).
    const ZONES = [
      { de: 0, a: 23.5, couleur: "#C8102E", nom: "chaude" },
      { de: 23.5, a: 66.5, couleur: "#2E7D32", nom: "tempérée" },
      { de: 66.5, a: 90, couleur: "#1F4E8C", nom: "polaire" },
    ];
    const arc = (f, p0, p1) => {
      const pts = [];
      for (let i = 0; i <= 12; i++) pts.push(f(p0 + ((p1 - p0) * i) / 12).map((c) => c.toFixed(1)).join(","));
      return pts.join(" ");
    };
    const etiquettes = [];
    for (const z of ZONES) {
      for (const s of [1, -1]) {
        el("polyline", { points: arc(minuit, s * z.de, s * z.a), fill: "none", stroke: z.couleur, "stroke-width": 6 });
      }
      etiquettes.push({ y: minuit((z.de + z.a) / 2)[1] + 5, z });
    }
    // Etiquettes du nord, de haut en bas (polaire, temperee, chaude), ecartees d'au moins 17 px.
    etiquettes.reverse();
    for (let i = 0; i < etiquettes.length; i++) {
      if (i > 0) etiquettes[i].y = Math.max(etiquettes[i].y, etiquettes[i - 1].y + 17);
      const { y, z } = etiquettes[i];
      el("text", { x: 336, y: Math.min(y, 296), "font-size": 13, fill: z.couleur, "text-anchor": "end" }, z.nom);
    }

    // Axe des poles et equateur.
    const [xn, yn] = [CX - (R + 16) * Math.sin(decl * RAD), CY - (R + 16) * Math.cos(decl * RAD)];
    const [xs, ys] = [CX + (R + 16) * Math.sin(decl * RAD), CY + (R + 16) * Math.cos(decl * RAD)];
    el("line", { x1: xn, y1: yn, x2: xs, y2: ys, stroke: "#6B7686", "stroke-width": 2 });
    el("text", { x: xn, y: yn - 4, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, "N");
    el("text", { x: xs, y: ys + 15, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, "S");
    const [xe1, ye1] = midi(0), [xe2, ye2] = minuit(0);
    el("line", { x1: xe1, y1: ye1, x2: xe2, y2: ye2, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "5 4" });

    // Deux faisceaux de meme largeur (nord et sud) ; un seul a l'equateur.
    const LARGEUR = 34;
    const lieux = lat === 0 ? [0] : [lat, -lat];
    for (const phi of lieux) {
      const incidence = phi - decl;
      const [px, py] = midi(phi);
      if (Math.cos(incidence * RAD) <= 0.02) { // lieu dans la nuit a midi (nuit polaire)
        el("circle", { cx: px, cy: py, r: 5, fill: "#6B7686" });
        continue;
      }
      const y1 = Math.max(CY - R + 0.5, py - LARGEUR / 2), y2 = Math.min(CY + R - 0.5, py + LARGEUR / 2);
      const surCercle = (y) => [CX - Math.sqrt(R * R - (y - CY) * (y - CY)), y];
      for (const y of [py - LARGEUR / 2, py, py + LARGEUR / 2]) {
        if (y <= CY - R || y >= CY + R) continue;
        const [hx] = surCercle(y);
        el("line", { x1: 8, y1: y, x2: hx, y2: y, stroke: "#E07B00", "stroke-width": 2 });
      }
      // Tache eclairee : arc du sol touche par le faisceau, d'autant plus pale que les rayons sont inclines.
      const b1 = Math.asin((CY - y1) / R) / RAD, b2 = Math.asin((CY - y2) / R) / RAD;
      const tache = [];
      for (let i = 0; i <= 12; i++) {
        const b = (b1 + ((b2 - b1) * i) / 12) * RAD;
        tache.push(`${(CX - R * Math.cos(b)).toFixed(1)},${(CY - R * Math.sin(b)).toFixed(1)}`);
      }
      const energie = Math.cos(incidence * RAD);
      el("polyline", { points: tache.join(" "), fill: "none", stroke: "#E07B00", "stroke-width": 9, "stroke-opacity": (0.15 + 0.85 * energie).toFixed(2) });
      el("circle", { cx: px, cy: py, r: 4, fill: "#14243B" });
    }
    return { lat, mois, declinaison: decl };
  },
};
