// Jules - gabarit "carre-densite" : un carre d'un kilometre de cote, un point = un habitant. Le curseur densite
// (habitants par km², 5 a 500) remplit le carre : presque vide en espace de faible densite, tres rempli a 500.
// Les points ont des places fixes (tirage pseudo-aleatoire a graine fixe) : bouger le curseur ajoute ou retire
// des points sans faire sauter les autres. Le nombre ecrit est la valeur du curseur (une donnee, pas une reponse) :
// revele false.
// Faits (EX-205) : espace de faible densite = moins de 30 habitants par km² (definition des manuels de geographie
// de 3e, theme 1 « Dynamiques territoriales de la France contemporaine ») ; France metropolitaine : 120,1 hab./km²
// en 2022 (Insee, recensement, population municipale / superficie IGN, jeu « Densite de population »,
// data.gouv.fr) ; Paris : environ 19 900 hab./km² (Insee Flash Ile-de-France n° 95, 2024). Ces chiffres servent
// aux lectures de la fiche ; la figure ne dessine que la densite choisie et le seuil des 30 hab./km².
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["carre-densite"] = {
  // dessiner(svg, valeurs) : densite de 5 a 500 habitants par km², entiere.
  dessiner(svg, valeurs) {
    const brut = Number(valeurs.densite ?? 20);
    const densite = Math.min(500, Math.max(5, Math.round(Number.isFinite(brut) ? brut : 20)));
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", VERT = "#2E7D32", ORANGE = "#E07B00";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 330");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Le carre de 1 km sur 1 km : vert pale en faible densite (moins de 30 hab./km²), orange pale au-dela.
    const X0 = 50, Y0 = 12, C = 240;
    const faible = densite < 30;
    el("rect", { x: X0, y: Y0, width: C, height: C, fill: faible ? "#E3F1E4" : "#FBEBD6", stroke: faible ? VERT : ORANGE, "stroke-width": 3 });

    // 500 places fixes (generateur mulberry32, graine fixe), tirees une fois ; on dessine les « densite » premieres.
    let graine = 20261004;
    const hasard = () => {
      graine = (graine + 0x6d2b79f5) | 0;
      let t = Math.imul(graine ^ (graine >>> 15), 1 | graine);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const marge = 6;
    for (let i = 0; i < densite; i++) {
      const x = X0 + marge + hasard() * (C - 2 * marge);
      const y = Y0 + marge + hasard() * (C - 2 * marge);
      el("circle", { cx: f(x), cy: f(y), r: 3, fill: BLEU });
    }

    // Les cotes : 1 km.
    el("line", { x1: X0, y1: Y0 + C + 14, x2: X0 + C, y2: Y0 + C + 14, stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: X0, y1: Y0 + C + 8, x2: X0, y2: Y0 + C + 20, stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: X0 + C, y1: Y0 + C + 8, x2: X0 + C, y2: Y0 + C + 20, stroke: GRIS, "stroke-width": 2 });
    el("rect", { x: X0 + C / 2 - 24, y: Y0 + C + 6, width: 48, height: 17, fill: "#FFFFFF" });
    el("text", { x: X0 + C / 2, y: Y0 + C + 19, "font-size": 13, fill: GRIS, "text-anchor": "middle", "font-family": "sans-serif" }, "1 km");

    // Legende : un point = un habitant ; le nombre de points ; faible densite ou non.
    el("circle", { cx: 54, cy: 290, r: 4, fill: BLEU });
    el("text", { x: 64, y: 295, "font-size": 14, fill: ENCRE, "font-family": "sans-serif" }, `= 1 habitant ; ici ${densite} habitants`);
    el("text", { x: 170, y: 320, "font-size": 14, "font-weight": "bold", fill: faible ? VERT : ORANGE, "text-anchor": "middle", "font-family": "sans-serif" },
      faible ? "faible densité (moins de 30)" : "30 ou plus : pas faible densité");
    return { densite, faible };
  },
};
