// Jules - gabarit "parcours-message-nerveux" : le message nerveux suit un trajet, etape par etape.
// vue 0 (organisme) : oeil (organe des sens) -> nerf sensitif -> cerveau (centre nerveux) -> nerf moteur -> muscle.
// vue 1 (cellules) : neurone 1 (message electrique) -> synapse (neurotransmetteur, message chimique) -> neurone 2.
// Curseurs : t (avancement du message, 0 = stimulus, 1 = reponse), perturbation (0 normal, 1 ralenti : fatigue,
// alcool, certaines drogues ; 2 trajet coupe ou transmission bloquee), vue (0 ou 1, figee par la fiche).
// Faits verifies :
// - programme de SVT du cycle 4 (annexe 3, arrete du 17-7-2020, eduscol.education.fr/document/621/download) :
//   « relier quelques comportements a leurs effets sur le fonctionnement du systeme nerveux » ; message nerveux,
//   centres nerveux, nerfs, cellules nerveuses ;
// - Vikidia « Synapse » : le message passe dans un seul sens, du neurone presynaptique au neurone postsynaptique,
//   par des neurotransmetteurs relaches dans la fente synaptique ;
// - fiches 3e svt role-cerveau-message-nerveux et mecanismes-nerveux-cellulaire (electrique dans le neurone,
//   chimique a la synapse ; un nerf coupe ne transmet plus).
// Le ralentissement (message a 70 % du trajet normal) est une illustration, pas une mesure : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["parcours-message-nerveux"] = {
  dessiner(svg, valeurs) {
    const t = Math.min(1, Math.max(0, Number(valeurs.t ?? 0)));
    const perturbation = Math.min(2, Math.max(0, Math.round(Number(valeurs.perturbation ?? 0))));
    const vue = Number(valeurs.vue ?? 0) >= 1 ? 1 : 0;
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
    const croix = (x, y) => {
      el("line", { x1: x - 9, y1: y - 9, x2: x + 9, y2: y + 9, stroke: "#C8102E", "stroke-width": 4 });
      el("line", { x1: x - 9, y1: y + 9, x2: x + 9, y2: y - 9, stroke: "#C8102E", "stroke-width": 4 });
    };
    const entre = (a, b, f) => ({ x: a.x + (b.x - a.x) * f, y: a.y + (b.y - a.y) * f });
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const GRIS = "#C9D1DC", MESSAGE = "#E07B00";
    // Avancement reel du message : ralenti (70 %) ou arrete a l'endroit de la coupure.
    const COUPURE = vue === 0 ? 0.75 : 0.6;
    let e = perturbation === 1 ? t * 0.7 : t;
    if (perturbation === 2) e = Math.min(e, COUPURE);

    let etape;
    if (vue === 0) {
      // ---- Vue organisme : oeil -> cerveau -> muscle.
      const P0 = { x: 64, y: 200 }, P1 = { x: 122, y: 92 }, C = { x: 170, y: 74 }, P2 = { x: 218, y: 92 };
      const P3 = { x: 278, y: 190 };
      const sensitif = e > 0 ? "#1F4E8C" : GRIS, moteur = e > 0.6 ? "#2E7D32" : GRIS;
      // Nerf moteur en deux troncons : apres la coupure (perturbation 2), il reste gris, le message n'y passe pas.
      const PC = entre(P2, P3, (COUPURE - 0.6) / 0.3);
      const apresCoupure = perturbation === 2 ? GRIS : moteur;
      el("line", { x1: P0.x, y1: P0.y, x2: P1.x, y2: P1.y, stroke: sensitif, "stroke-width": 5, "stroke-linecap": "round" });
      el("line", { x1: P2.x, y1: P2.y, x2: PC.x, y2: PC.y, stroke: moteur, "stroke-width": 5, "stroke-linecap": "round" });
      el("line", { x1: PC.x, y1: PC.y, x2: P3.x, y2: P3.y, stroke: apresCoupure, "stroke-width": 5, "stroke-linecap": "round" });
      texte(46, 130, "nerf", "#1F4E8C", { "font-size": 13 });
      texte(46, 146, "sensitif", "#1F4E8C", { "font-size": 13 });
      texte(296, 130, "nerf", "#2E7D32", { "font-size": 13 });
      texte(296, 146, "moteur", "#2E7D32", { "font-size": 13 });
      // Cerveau : allume pendant l'integration (e entre 0,3 et 0,6), puis reste marque.
      const auCerveau = e >= 0.3;
      el("ellipse", { cx: C.x, cy: C.y, rx: 62, ry: 40, fill: auCerveau ? "#E6EEF8" : "#FFFFFF",
        stroke: auCerveau ? "#1F4E8C" : "#6B7686", "stroke-width": auCerveau && e < 0.6 ? 4 : 2 });
      texte(C.x, C.y + 5, "cerveau", "#14243B", { "font-weight": "bold" });
      // Oeil (organe des sens) et la balle vue (le stimulus).
      el("circle", { cx: 52, cy: 214, r: 18, fill: "#FFFFFF", stroke: "#1F4E8C", "stroke-width": 3 });
      el("circle", { cx: 44, cy: 214, r: 7, fill: "#1F4E8C" });
      texte(62, 256, "œil", "#14243B", { "text-anchor": "start" });
      // Muscle : s'epaissit et raccourcit quand il se contracte (fin du trajet, e > 0,9).
      const c = Math.max(0, Math.min(1, (e - 0.9) / 0.1));
      el("ellipse", { cx: 290, cy: 220, rx: 18 + 10 * c, ry: 34 - 12 * c, fill: c > 0 ? "#2E7D32" : "#FFFFFF",
        "fill-opacity": c > 0 ? 0.35 + 0.4 * c : 1, stroke: "#2E7D32", "stroke-width": 3 });
      texte(290, 276, "muscle", "#14243B");
      // Position du message (point orange).
      // Dans le cerveau, le point passe au-dessus du mot « cerveau » (A -> B) pour ne jamais le masquer.
      const A = { x: 134, y: 54 }, B = { x: 206, y: 54 };
      let point;
      if (e <= 0.3) point = entre(P0, P1, e / 0.3);
      else if (e <= 0.35) point = entre(P1, A, (e - 0.3) / 0.05);
      else if (e <= 0.55) point = entre(A, B, (e - 0.35) / 0.2);
      else if (e <= 0.6) point = entre(B, P2, (e - 0.55) / 0.05);
      else if (e <= 0.9) point = entre(P2, P3, (e - 0.6) / 0.3);
      else point = P3;
      if (perturbation === 2) {
        const coupe = entre(P2, P3, (COUPURE - 0.6) / 0.3);
        croix(coupe.x, coupe.y);
        texte(coupe.x - 14, coupe.y + 30, "coupé", "#C8102E", { "text-anchor": "end", "font-weight": "bold" });
      }
      el("circle", { cx: point.x, cy: point.y, r: 9, fill: MESSAGE, stroke: "#FFFFFF", "stroke-width": 2 });
      if (e < 0.3) etape = "1. l'œil capte, le message monte";
      else if (e < 0.6) etape = "2. le cerveau élabore une commande";
      else if (e < 0.9) etape = "3. la commande descend au muscle";
      else etape = "4. le muscle se contracte";
      if (perturbation === 2 && t >= COUPURE) etape = "le message n'arrive pas au muscle";
    } else {
      // ---- Vue cellules : neurone 1 -> synapse -> neurone 2.
      const Y = 130;
      el("circle", { cx: 36, cy: Y, r: 22, fill: "#E6EEF8", stroke: "#1F4E8C", "stroke-width": 3 });
      for (const a of [-2.2, 2.4, -1.4]) { // dendrites, du bord du corps cellulaire vers l'exterieur
        el("line", { x1: 36 + 22 * Math.cos(a), y1: Y + 22 * Math.sin(a), x2: 36 + 34 * Math.cos(a),
          y2: Y + 34 * Math.sin(a), stroke: "#1F4E8C", "stroke-width": 2 });
      }
      el("line", { x1: 58, y1: Y, x2: 142, y2: Y, stroke: "#1F4E8C", "stroke-width": 5 });
      el("rect", { x: 140, y: Y - 24, width: 22, height: 48, rx: 10, fill: "#E6EEF8", stroke: "#1F4E8C", "stroke-width": 3 });
      el("rect", { x: 194, y: Y - 24, width: 14, height: 48, rx: 4, fill: "#E6EEF8", stroke: "#1F4E8C", "stroke-width": 3 });
      el("line", { x1: 208, y1: Y, x2: 242, y2: Y, stroke: "#1F4E8C", "stroke-width": 5 });
      el("circle", { cx: 262, cy: Y, r: 20, fill: "#E6EEF8", stroke: "#1F4E8C", "stroke-width": 3 });
      el("line", { x1: 282, y1: Y, x2: 330, y2: Y, stroke: "#1F4E8C", "stroke-width": 5 });
      texte(60, 88, "neurone 1", "#14243B", { "font-weight": "bold" });
      texte(268, 88, "neurone 2", "#14243B", { "font-weight": "bold" });
      // La synapse : la fente entre les deux neurones.
      el("line", { x1: 166, y1: 64, x2: 190, y2: 64, stroke: "#14243B", "stroke-width": 2 });
      texte(178, 52, "synapse", "#14243B");
      el("line", { x1: 178, y1: 66, x2: 178, y2: Y - 28, stroke: "#14243B", "stroke-width": 2, "stroke-dasharray": "3 3" });
      // Neurotransmetteur (billes vertes) : il traverse la fente entre e = 0,4 et e = 0,6.
      const nb = perturbation === 1 ? 2 : 5;
      const f = Math.max(0, Math.min(1, (e - 0.4) / 0.2));
      for (let i = 0; i < nb; i++) {
        const y = Y - 16 + i * (32 / Math.max(1, nb - 1));
        const x = e < 0.4 ? 152 : 166 + (188 - 166) * f; // la fente va de x = 162 a x = 194
        el("circle", { cx: x, cy: y, r: 4, fill: "#2E7D32" });
      }
      if (perturbation === 2) {
        croix(201, Y);
        texte(201, Y + 50, "bloqué", "#C8102E", { "font-weight": "bold" });
      }
      // Message electrique (point orange) dans les neurones, invisible pendant le passage chimique.
      if (e < 0.4) el("circle", { cx: 58 + (142 - 58) * (e / 0.4), cy: Y, r: 9, fill: MESSAGE, stroke: "#FFFFFF", "stroke-width": 2 });
      if (e > 0.6) el("circle", { cx: 208 + (326 - 208) * ((e - 0.6) / 0.4), cy: Y, r: 9, fill: MESSAGE, stroke: "#FFFFFF", "stroke-width": 2 });
      // Legende : une couleur, une idee.
      el("circle", { cx: 30, cy: 214, r: 8, fill: MESSAGE });
      texte(46, 219, "message électrique", "#14243B", { "text-anchor": "start" });
      el("circle", { cx: 30, cy: 240, r: 5, fill: "#2E7D32" });
      texte(46, 245, "neurotransmetteur (chimique)", "#14243B", { "text-anchor": "start" });
      if (e < 0.4) etape = "1. message électrique dans le neurone 1";
      else if (e <= 0.6) etape = "2. synapse : le message devient chimique";
      else etape = "3. le neurone 2 transmet le message";
      if (perturbation === 2 && t >= COUPURE) etape = "le message ne passe pas la synapse";
    }
    if (perturbation === 1) {
      texte(170, vue === 0 ? 20 : 26, "message ralenti (fatigue, alcool)", "#E07B00", { "font-weight": "bold" });
    }
    texte(170, 292, etape, perturbation === 2 && t >= COUPURE ? "#C8102E" : "#14243B", { "font-weight": "bold" });
    return { t, perturbation, vue, avancement: Math.round(e * 100) / 100 };
  },
};
