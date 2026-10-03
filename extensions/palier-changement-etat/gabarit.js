// Jules - gabarit "palier-changement-etat" : on chauffe de la glace pure (eau) a puissance constante.
// En haut, la courbe temperature-temps avec ses deux paliers (0 °C : fusion, 100 °C : ebullition) et le point
// au temps t ; en bas, une boite de particules dont le rangement suit l'etat. Curseur t = duree (min, 0 a 30).
// Courbe schematique (memes reperes que le schema de la fiche : depart a -10 °C) :
//   0-5 min solide de -10 a 0 °C ; 5-12 min fusion a 0 °C ; 12-20 min liquide de 0 a 100 °C ;
//   20-30 min ebullition a 100 °C (a 30 min, tout est vapeur).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

// Temperature (°C) au temps t (min) et part de la matiere deja passee a l'etat suivant pendant un palier.
function _palierTemperature(t) {
  if (t <= 5) return -10 + 2 * t;
  if (t <= 12) return 0;
  if (t <= 20) return 12.5 * (t - 12);
  return 100;
}

window.GABARITS["palier-changement-etat"] = {
  dessiner(svg, valeurs) {
    const t = Math.max(0, Math.min(30, Number(valeurs.t ?? 8)));
    const T = _palierTemperature(t);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", ORANGE = "#E07B00";
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // --- courbe : t de 0 a 30 min -> x de 62 a 322 ; T de -20 a 115 °C -> y de 190 a 22.
    const X = (m) => 62 + (m / 30) * 260;
    const Y = (c) => 190 - ((c + 20) / 135) * 168;
    el("line", { x1: X(0), y1: Y(-20), x2: X(30) + 6, y2: Y(-20), stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: X(0), y1: Y(-20), x2: X(0), y2: Y(115), stroke: GRIS, "stroke-width": 2 });
    for (const c of [0, 100]) {
      el("line", { x1: X(0), y1: Y(c), x2: X(30), y2: Y(c), stroke: GRIS, "stroke-width": 1.5, "stroke-dasharray": "4 4" });
      el("text", { x: X(0) - 6, y: Y(c) + 5, "font-size": 14, "text-anchor": "end", fill: ENCRE }, `${c} °C`);
    }
    el("text", { x: X(30), y: 208, "font-size": 14, "text-anchor": "end", fill: GRIS }, "temps");
    const sommets = [0, 5, 12, 20, 30];
    const tout = sommets.map((m, i) => `${i ? "L" : "M"}${X(m)},${Y(_palierTemperature(m))}`).join(" ");
    el("path", { d: tout, fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "2 5", "stroke-linecap": "round" });
    const parcours = sommets.filter((m) => m < t).concat([t]);
    const deja = parcours.map((m, i) => `${i ? "L" : "M"}${X(m)},${Y(_palierTemperature(m))}`).join(" ");
    el("path", { d: deja, fill: "none", stroke: BLEU, "stroke-width": 4, "stroke-linejoin": "round", "stroke-linecap": "round" });
    // Paliers soulignes en orange (le moment ou la temperature ne bouge plus).
    for (const [a, b, c] of [[5, 12, 0], [20, 30, 100]]) {
      if (t > a) el("line", { x1: X(a), y1: Y(c), x2: X(Math.min(t, b)), y2: Y(c), stroke: ORANGE, "stroke-width": 6, "stroke-linecap": "round" });
    }
    el("circle", { cx: X(t), cy: Y(T), r: 7, fill: ROUGE, stroke: "#FFFFFF", "stroke-width": 2 });

    // --- etat et part deja transformee pendant un palier.
    let etat, partLiquide = 0, partGaz = 0;
    if (t < 5) etat = "solide";
    else if (t < 12) { etat = "solide + liquide"; partLiquide = (t - 5) / 7; }
    else if (t < 20) { etat = "liquide"; partLiquide = 1; }
    else if (t < 30) { etat = "liquide + gaz"; partLiquide = 1; partGaz = (t - 20) / 10; }
    else { etat = "gaz"; partLiquide = 1; partGaz = 1; }

    // --- boite de particules : 12 particules, meme nombre dans tous les etats (la masse se conserve).
    const BX = 30, BY = 222, BL = 150, BH = 110;
    el("rect", { x: BX, y: BY, width: BL, height: BH, rx: 6, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
    const N = 12;
    const nLiquide = Math.round(partLiquide * N), nGaz = Math.round(partGaz * N);
    // Emplacements choisis pour que deux particules ne se chevauchent jamais, a toutes les etapes :
    // - solide : reseau range (3 rangees de 4) ; la rangee du bas fond la premiere (particules 0 a 3) ;
    // - liquide : particules serrees mais en desordre, au fond de la boite (fondent dans l'ordre 0 a 11) ;
    // - gaz : particules ecartees dans toute la boite (s'evaporent dans l'ordre 11 a 0, celles du dessus d'abord).
    const liquide = [[46, 322], [70, 321], [94, 323], [118, 322], [142, 321], [166, 323],
      [58, 301], [82, 303], [106, 300], [130, 302], [154, 301], [100, 280]];
    const gaz = [[168, 302], [124, 300], [76, 302], [148, 292], [100, 288], [54, 284],
      [168, 268], [128, 264], [80, 262], [152, 242], [104, 238], [56, 240]];
    for (let i = 0; i < N; i++) {
      const col = i % 4, lig = 2 - Math.floor(i / 4);
      let x = 69 + col * 24, y = 258 + lig * 22; // reseau serre et range
      const r = 9;
      const agite = 11 - i < nGaz;
      if (agite) [x, y] = gaz[i];
      else if (i < nLiquide) [x, y] = liquide[i];
      el("circle", { cx: x, cy: y, r, fill: BLEU, stroke: "#FFFFFF", "stroke-width": 1.5 });
      if (agite) {
        // traits d'agitation : la particule de gaz bouge vite
        el("line", { x1: x - 18, y1: y + 2, x2: x - 12, y2: y + 1, stroke: GRIS, "stroke-width": 2, "stroke-linecap": "round" });
        el("line", { x1: x - 17, y1: y - 4, x2: x - 12, y2: y - 4, stroke: GRIS, "stroke-width": 2, "stroke-linecap": "round" });
      }
    }

    // --- legende : etat et temperature lue sur la courbe.
    el("text", { x: 196, y: 248, "font-size": 14, fill: GRIS }, "état :");
    el("text", { x: 196, y: 270, "font-size": 15, "font-weight": "bold", fill: ENCRE }, etat);
    const tAffiche = String(Math.round(T * 10) / 10).replace(".", ",").replace("-", "−");
    el("text", { x: 196, y: 300, "font-size": 14, fill: GRIS }, "température :");
    el("text", { x: 196, y: 322, "font-size": 16, "font-weight": "bold", fill: ROUGE }, `${tAffiche} °C`);
    return { t, T, etat };
  },
};
