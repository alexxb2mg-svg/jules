// Jules - gabarit "globe-latitude-longitude" : deux vues simples du globe cote a cote.
// A gauche, de profil : l'angle de latitude s'ouvre depuis l'equateur (vers le Nord au-dessus, vers le Sud
// en dessous), le parallele du point est trace. A droite, vu du dessus du pole Nord : l'angle de longitude tourne
// depuis le meridien de Greenwich (vers l'Est dans le sens inverse des aiguilles d'une montre) ; le point est a la
// distance R x cos(latitude) du pole ; un point de l'hemisphere Sud, cache derriere, est dessine en creux.
// Faits (programme de mathematiques du cycle 4, BO n° 31 du 30/07/2020, « se reperer sur une sphere » ; IGN,
// « latitude, longitude ») : latitude de 0° (equateur) a 90° Nord ou Sud (poles) ; longitude de 0° (meridien de
// Greenwich) a 180° Est ou Ouest ; vue du dessus du pole Nord, la Terre tourne dans le sens inverse des aiguilles
// d'une montre, l'Est est donc dans ce sens ; aux poles, la longitude n'a plus de sens.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["globe-latitude-longitude"] = {
  // dessiner(svg, valeurs) : lat = latitude en degres (Nord positif, -90 a 90), lon = longitude en degres (Est
  // positif, -180 a 180).
  dessiner(svg, valeurs) {
    const borne = (v, defaut, mini, maxi) => {
      const x = Number(v ?? defaut);
      return Math.min(maxi, Math.max(mini, Number.isFinite(x) ? x : defaut));
    };
    const lat = borne(valeurs.lat, 45, -90, 90);
    const lon = borne(valeurs.lon, 30, -180, 180);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const texte = (x, y, t, attrs = {}) =>
      el("text", { x, y, "font-size": 14, fill: "#14243B", "text-anchor": "middle", "font-family": "sans-serif", ...attrs }, t);
    svg.setAttribute("viewBox", "0 0 340 262");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const R = 66, cy = 118;
    const rad = (d) => (d * Math.PI) / 180;
    const f = (v) => v.toFixed(1);
    // Arc oriente du point (cx, cy) : angles en radians, repere ecran (y vers le bas), de a0 a a1.
    const arc = (cx, cyy, r, a0, a1, couleur) => {
      if (Math.abs(a1 - a0) < 1e-9) return;
      const p = (a) => [cx + r * Math.cos(a), cyy + r * Math.sin(a)];
      const [x0, y0] = p(a0), [x1, y1] = p(a1);
      const grand = Math.abs(a1 - a0) > Math.PI ? 1 : 0;
      el("path", { d: `M ${f(x0)} ${f(y0)} A ${r} ${r} 0 ${grand} ${a1 > a0 ? 1 : 0} ${f(x1)} ${f(y1)}`, fill: "none", stroke: couleur, "stroke-width": 3 });
    };
    const nomLat = lat === 0 ? "0°" : `${Math.abs(lat)}° ${lat > 0 ? "N" : "S"}`;
    const nomLon = lon === 0 ? "0°" : Math.abs(lon) === 180 ? "180°" : `${Math.abs(lon)}° ${lon > 0 ? "E" : "O"}`;

    // --- Vue de profil (latitude) ---
    const g = { x: 88, y: cy };
    texte(g.x, 20, "de profil", { "font-weight": 700 });
    el("line", { x1: g.x, y1: g.y - R - 12, x2: g.x, y2: g.y + R + 12, stroke: "#6B7686", "stroke-width": 2 });
    el("circle", { cx: g.x, cy: g.y, r: R, fill: "#1F4E8C", "fill-opacity": 0.08, stroke: "#1F4E8C", "stroke-width": 3 });
    el("line", { x1: g.x - R, y1: g.y, x2: g.x + R, y2: g.y, stroke: "#1F4E8C", "stroke-width": 2, "stroke-dasharray": "6 5" });
    texte(g.x, g.y - R - 16, "N", { "font-weight": 700 });
    texte(g.x, g.y + R + 28, "S", { "font-weight": 700 });
    texte(g.x - R / 2, g.y + 18, "équateur", { "font-size": 13, fill: "#1F4E8C" });
    const pl = [g.x + R * Math.cos(rad(lat)), g.y - R * Math.sin(rad(lat))];
    // le parallele du point : une corde horizontale vue de profil
    if (Math.abs(lat) < 90) {
      el("line", { x1: f(2 * g.x - pl[0]), y1: f(pl[1]), x2: f(pl[0]), y2: f(pl[1]), stroke: "#C8102E", "stroke-width": 2, "stroke-dasharray": "4 4" });
    }
    el("line", { x1: g.x, y1: g.y, x2: f(pl[0]), y2: f(pl[1]), stroke: "#E07B00", "stroke-width": 3 });
    arc(g.x, g.y, 26, 0, -rad(lat), "#E07B00");
    texte(g.x, 252, `latitude ${nomLat}`, { fill: "#E07B00", "font-weight": 700 });
    el("circle", { cx: f(pl[0]), cy: f(pl[1]), r: 6, fill: "#C8102E" });

    // --- Vue du dessus du pole Nord (longitude) ---
    const d = { x: 252, y: cy };
    texte(d.x, 20, "vu du pôle Nord", { "font-weight": 700 });
    el("circle", { cx: d.x, cy: d.y, r: R, fill: "#1F4E8C", "fill-opacity": 0.08, stroke: "#1F4E8C", "stroke-width": 3 });
    texte(d.x - R - 10, d.y + 5, "O", { "font-weight": 700 });
    texte(d.x + R + 10, d.y + 5, "E", { "font-weight": 700 });
    // Greenwich vers le bas (vers l'observateur) ; direction d'une longitude : (sin lon, cos lon) a l'ecran.
    el("line", { x1: d.x, y1: d.y, x2: d.x, y2: d.y + R, stroke: "#2E7D32", "stroke-width": 3 });
    texte(d.x, d.y + R + 28, "Greenwich", { "font-size": 13, fill: "#2E7D32", "font-weight": 700 });
    const dir = [Math.sin(rad(lon)), Math.cos(rad(lon))];
    // Aux poles la longitude n'a pas de sens : ni meridien du point ni angle de longitude (le point est au centre).
    if (Math.abs(lat) < 90) {
      el("line", { x1: d.x, y1: d.y, x2: f(d.x + R * dir[0]), y2: f(d.y + R * dir[1]), stroke: "#C8102E", "stroke-width": 2, "stroke-dasharray": "4 4" });
      // angle ecran de Greenwich = pi/2 (vers le bas) ; l'Est tourne dans le sens inverse des aiguilles (angle ecran decroissant)
      arc(d.x, d.y, 24, Math.PI / 2, Math.PI / 2 - rad(lon), "#E07B00");
    }
    texte(d.x, 252, `longitude ${Math.abs(lat) === 90 ? "sans objet" : nomLon}`, { fill: "#E07B00", "font-weight": 700 });
    el("circle", { cx: d.x, cy: d.y, r: 4, fill: "#14243B" });
    const r = R * Math.cos(rad(lat));
    const pd = [d.x + r * dir[0], d.y + r * dir[1]];
    if (lat >= 0) {
      el("circle", { cx: f(pd[0]), cy: f(pd[1]), r: 6, fill: "#C8102E" });
    } else {
      el("circle", { cx: f(pd[0]), cy: f(pd[1]), r: 6, fill: "#FFFFFF", stroke: "#C8102E", "stroke-width": 3 });
    }
    return { lat, lon };
  },
};
