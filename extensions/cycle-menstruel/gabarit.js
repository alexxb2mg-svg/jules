// Jules - gabarit "cycle-menstruel" : un cycle de 28 jours (cycle moyen ; la duree varie d'une personne et d'un
// mois a l'autre). Une roue des jours avec un repere qui tourne relie, au meme moment, l'ovaire (un follicule
// murit, ovulation vers le 14e jour), la paroi de l'uterus (eliminee pendant les regles, puis epaissie) et les
// hormones ovariennes (oestrogenes, progesterone).
// Curseur : jour (1 a 28).
// Faits verifies :
// - programme de SVT du cycle 4 (annexe 3, arrete du 17-7-2020, eduscol.education.fr/document/621/download) :
//   puberte, fonctionnement des appareils reproducteurs, controles hormonaux ;
// - Vikidia « Menstruation » : cycle d'environ 28 jours en moyenne, variable ; ovulation aux alentours du 14e jour ;
//   la muqueuse de l'uterus (endometre) s'epaissit et s'enrichit en vaisseaux sanguins ; sans fecondation elle est
//   eliminee : les regles, qui durent en moyenne 3 a 5 jours ;
// - fiche 3e svt appareils-reproducteurs-puberte : oestrogenes et progesterone produits par les ovaires ;
//   l'ovulation a lieu environ 14 jours avant les regles suivantes.
// Formes des courbes hormonales (manuels de 3e) : oestrogenes bas pendant les regles, pic juste avant
// l'ovulation, seconde bosse plus faible vers le 21e jour ; progesterone basse avant l'ovulation, haute vers le
// 21e jour ; les deux chutent en fin de cycle, ce qui declenche les regles. Aucune valeur ecrite : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["cycle-menstruel"] = {
  dessiner(svg, valeurs) {
    const jour = Math.min(28, Math.max(1, Math.round(Number(valeurs.jour ?? 1))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const texte = (x, y, contenu, couleur, attrs = {}) =>
      el("text", Object.assign({ x, y, "font-size": 14, "text-anchor": "middle", fill: couleur }, attrs), contenu);
    svg.setAttribute("viewBox", "0 0 340 330");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const REGLES = "#C8102E", OVULATION = "#E07B00", OESTRO = "#1F4E8C", PROGE = "#2E7D32", GRIS = "#C9D1DC";
    // ---- Roue des 28 jours (jour 1 en haut, sens des aiguilles d'une montre).
    const CX = 92, CY = 112, R = 66;
    const angle = (d) => -Math.PI / 2 + (2 * Math.PI * (d - 1)) / 28;
    const surRoue = (d, r) => ({ x: CX + r * Math.cos(angle(d)), y: CY + r * Math.sin(angle(d)) });
    const arc = (d1, d2, couleur, largeur) => {
      const a = surRoue(d1, R), b = surRoue(d2, R);
      const grand = ((d2 - d1) * 360) / 28 > 180 ? 1 : 0;
      el("path", { d: `M ${a.x.toFixed(1)} ${a.y.toFixed(1)} A ${R} ${R} 0 ${grand} 1 ${b.x.toFixed(1)} ${b.y.toFixed(1)}`,
        fill: "none", stroke: couleur, "stroke-width": largeur, "stroke-linecap": "butt" });
    };
    el("circle", { cx: CX, cy: CY, r: R, fill: "none", stroke: GRIS, "stroke-width": 10 });
    arc(0.5, 5.5, REGLES, 10);                 // regles : jours 1 a 5
    const ov = surRoue(14, R);
    el("circle", { cx: ov.x, cy: ov.y, r: 8, fill: OVULATION, stroke: "#FFFFFF", "stroke-width": 2 });
    for (const d of [1, 7, 14, 21]) {
      const p = surRoue(d, R + 20);
      texte(p.x, p.y + 5, String(d), "#6B7686", { "font-size": 13 });
    }
    const rep = surRoue(jour, R - 2);
    el("line", { x1: CX, y1: CY, x2: rep.x, y2: rep.y, stroke: "#14243B", "stroke-width": 4, "stroke-linecap": "round" });
    el("circle", { cx: rep.x, cy: rep.y, r: 6, fill: "#14243B" });
    el("circle", { cx: CX, cy: CY, r: 5, fill: "#14243B" });
    texte(10, 22, "jour " + jour, "#14243B", { "font-weight": "bold", "text-anchor": "start", "font-size": 16 });

    // ---- Ovaire : un follicule grossit, libere l'ovule vers le jour 14.
    texte(246, 24, "ovaire", "#14243B", { "font-weight": "bold" });
    el("ellipse", { cx: 262, cy: 58, rx: 34, ry: 22, fill: "#FFFFFF", stroke: "#6B7686", "stroke-width": 2 });
    if (jour < 14) {
      el("circle", { cx: 262, cy: 58, r: 4 + (10 * (jour - 1)) / 12, fill: "none", stroke: OVULATION, "stroke-width": 2 });
      el("circle", { cx: 262, cy: 58, r: 3, fill: OVULATION });
    } else if (jour <= 16) {
      el("circle", { cx: 310, cy: 52, r: 5, fill: OVULATION });  // l'ovule libere, vers la trompe
      texte(312, 30, "ovule", OVULATION, { "font-size": 13, "font-weight": "bold" });
    }

    // ---- Paroi de l'uterus : epaisseur selon le jour.
    const epaisseur = jour <= 5 ? 40 - (32 * (jour - 1)) / 4 : jour <= 14 ? 8 + (24 * (jour - 5)) / 9 : 32 + (12 * (jour - 14)) / 14;
    texte(262, 112, "paroi de l'utérus", "#14243B", { "font-weight": "bold" });
    el("rect", { x: 206, y: 176, width: 112, height: 10, fill: "#6B7686" });
    el("rect", { x: 206, y: 176 - epaisseur, width: 112, height: epaisseur, fill: REGLES, "fill-opacity": 0.3,
      stroke: REGLES, "stroke-width": 2 });
    if (jour <= 5) {
      for (const x of [222, 250, 278, 306]) el("circle", { cx: x, cy: 198, r: 4, fill: REGLES });
      texte(262, 220, "règles", REGLES, { "font-weight": "bold" });
    }

    // ---- Hormones ovariennes sur les 28 jours, repere au jour choisi.
    const HX0 = 30, HX1 = 318, HY = 292, HH = 52;
    const hx = (d) => HX0 + ((HX1 - HX0) * (d - 1)) / 27;
    const g = (d, c, l) => Math.exp(-(((d - c) / l) ** 2));
    const oestro = (d) => 0.12 + 0.88 * g(d, 13, 2.6) + 0.42 * g(d, 21, 3.5);
    const proge = (d) => 0.05 + 0.9 * g(d, 21, 3.6);
    el("line", { x1: HX0, y1: HY, x2: HX1, y2: HY, stroke: "#6B7686", "stroke-width": 2 });
    for (const [f, couleur] of [[oestro, OESTRO], [proge, PROGE]]) {
      const pts = [];
      for (let d = 1; d <= 28.001; d += 0.5) pts.push(`${hx(d).toFixed(1)},${(HY - HH * Math.min(1, f(d))).toFixed(1)}`);
      el("polyline", { points: pts.join(" "), fill: "none", stroke: couleur, "stroke-width": 3 });
      el("circle", { cx: hx(jour), cy: HY - HH * Math.min(1, f(jour)), r: 5, fill: couleur, stroke: "#FFFFFF", "stroke-width": 2 });
    }
    el("line", { x1: hx(jour), y1: HY - HH - 6, x2: hx(jour), y2: HY, stroke: "#14243B", "stroke-width": 2, "stroke-dasharray": "2 3" });
    texte(HX0, 316, "œstrogènes", OESTRO, { "text-anchor": "start", "font-weight": "bold" });
    texte(HX1, 316, "progestérone", PROGE, { "text-anchor": "end", "font-weight": "bold" });
    texte(HX0, 232, "hormones de l'ovaire", "#14243B", { "text-anchor": "start", "font-weight": "bold" });
    const phase = jour <= 5 ? "regles" : jour < 13 ? "follicule" : jour <= 15 ? "ovulation" : "paroi epaisse";
    return { jour, phase };
  },
};
