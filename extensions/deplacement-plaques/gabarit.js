// Jules - gabarit "deplacement-plaques" : coupe d'un ocean qui s'ouvre de part et d'autre d'une dorsale.
// Curseurs : v (vitesse d'ecartement des deux plaques, en cm par an), duree (temps ecoule, en millions d'annees).
// Largeur de l'ocean = v x duree x 10 km (1 cm/an pendant 1 million d'annees = 1 000 000 cm = 10 km).
// La largeur n'est jamais ecrite : une echelle « 1 000 km » permet de la mesurer. Chaque bande de croute
// oceanique correspond a 10 millions d'annees : la plus jeune est contre la dorsale.
// Faits verifies (EX-205) :
// - USGS, « This Dynamic Earth », chap. « Understanding plate motions » (pubs.usgs.gov/gip/dynamic/understanding.html) :
//   la dorsale medio-atlantique s'ecarte d'environ 2,5 cm par an (25 km par million d'annees) ; l'Atlantique est
//   ne d'un mince bras de mer en 100 a 200 millions d'annees ; la dorsale arctique est la plus lente (< 2,5 cm/an),
//   la dorsale du Pacifique est pres de l'ile de Paques la plus rapide (> 15 cm/an).
// - USGS FAQ « How fast do tectonic plates move? » (usgs.gov/faqs/how-fast-do-tectonic-plates-move) : les plaques
//   bougent a peu pres a la vitesse de pousse des ongles.
// - Programme de SVT cycle 4 (Eduscol, annexe 3, arrete du 17-7-2020) : mobilite des plaques, dorsales, subductions.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["deplacement-plaques"] = {
  dessiner(svg, valeurs) {
    const v = Math.min(10, Math.max(1, Number(valeurs.v ?? 3)));
    const duree = Math.min(100, Math.max(0, Number(valeurs.duree ?? 60)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 280");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Echelle horizontale : 10 000 km (maximum v = 10, duree = 100) = 290 px.
    const PX_KM = 290 / 10000;
    const largeurKm = v * duree * 10;
    const XD = 170; // dorsale
    const demi = (largeurKm * PX_KM) / 2;
    const xG = XD - demi, xD = XD + demi; // cotes des deux continents
    const MER = 100, FOND = 140, CROUTE = 162, BAS = 214;

    // Manteau (solide mais chaud) sous les plaques.
    el("rect", { x: 10, y: CROUTE, width: 320, height: BAS - CROUTE, fill: "#F6E3CC" });
    el("text", { x: 18, y: BAS - 10, "font-size": 13, fill: "#6B7686" }, "manteau");

    // Eau de l'ocean puis croute oceanique en bandes de 10 millions d'annees (symetriques).
    if (demi > 0) {
      el("rect", { x: xG, y: MER, width: xD - xG, height: FOND - MER, fill: "#CFE0F3" });
      const nb = Math.round(duree / 10);
      for (let i = 0; i < nb; i++) {
        const a = (i * demi) / nb, b = ((i + 1) * demi) / nb;
        const couleur = i % 2 === 0 ? "#1F4E8C" : "#7FA3CF";
        el("rect", { x: XD + a, y: FOND, width: b - a, height: CROUTE - FOND, fill: couleur });
        el("rect", { x: XD - b, y: FOND, width: b - a, height: CROUTE - FOND, fill: couleur });
      }
    }

    // Continents (croute continentale, plus epaisse et plus haute que le fond de l'ocean).
    for (const [x0, x1] of [[10, xG], [xD, 330]]) {
      el("rect", { x: x0, y: MER - 14, width: x1 - x0, height: CROUTE - (MER - 14), fill: "#B9A58A", stroke: "#6B7686", "stroke-width": 2 });
    }
    el("text", { x: 14, y: MER - 22, "font-size": 13, fill: "#14243B" }, "continent");
    el("text", { x: 326, y: MER - 22, "font-size": 13, "text-anchor": "end", fill: "#14243B" }, "continent");
    if (demi >= 30) el("text", { x: XD, y: MER + 18, "font-size": 13, "text-anchor": "middle", fill: "#1F4E8C" }, "océan");

    // Dorsale : le magma remonte et fabrique la croute neuve.
    el("line", { x1: XD, y1: BAS - 4, x2: XD, y2: FOND - 2, stroke: "#C8102E", "stroke-width": 4 });
    el("polygon", { points: `${XD - 7},${FOND + 6} ${XD + 7},${FOND + 6} ${XD},${FOND - 6}`, fill: "#C8102E" });
    el("text", { x: XD, y: 30, "font-size": 13, "text-anchor": "middle", fill: "#C8102E" }, duree === 0 ? "le continent se fend" : "dorsale");
    el("line", { x1: XD, y1: 36, x2: XD, y2: MER - 18, stroke: "#C8102E", "stroke-width": 2, "stroke-dasharray": "3 3" });

    // Fleches : les deux plaques s'eloignent de la dorsale.
    for (const s of [-1, 1]) {
      const x0 = XD + s * 14, x1 = XD + s * 66;
      el("line", { x1: x0, y1: 56, x2: x1, y2: 56, stroke: "#1F4E8C", "stroke-width": 3 });
      el("polygon", { points: `${x1},${51} ${x1},${61} ${x1 + s * 10},56`, fill: "#1F4E8C" });
    }

    // Echelle (comme sur une carte) : pas de largeur ecrite, l'eleve la mesure.
    const E = 1000 * PX_KM;
    el("line", { x1: 20, y1: 244, x2: 20 + E, y2: 244, stroke: "#14243B", "stroke-width": 3 });
    for (const x of [20, 20 + E]) el("line", { x1: x, y1: 238, x2: x, y2: 250, stroke: "#14243B", "stroke-width": 2 });
    el("text", { x: 28 + E, y: 249, "font-size": 13, fill: "#14243B" }, "1 000 km");
    el("rect", { x: 20, y: 256, width: 14, height: 14, fill: "#1F4E8C" });
    el("rect", { x: 34, y: 256, width: 14, height: 14, fill: "#7FA3CF" });
    el("text", { x: 56, y: 268, "font-size": 13, fill: "#14243B" }, "une bande = 10 millions d'années");
    return { v, duree, largeur_km: largeurKm };
  },
};
