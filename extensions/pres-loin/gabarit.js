// Jules - gabarit "pres-loin" : un enfant montre du doigt une, deux ou trois balles, pres de lui ou loin de lui.
// Valeurs : d (distance, 1 a 6 pas ; 1 a 3 = pres, 4 a 6 = loin) et q (nombre de balles, 1 a 3). Le sol est
// partage en deux zones, « près » et « loin », separees par un trait gris en pointilles.
// La figure n'ecrit pas le demonstratif (this, these, that, those) : l'eleve le trouve, les lectures de la fiche
// le confirment.
// Faits : this / these pour ce qui est pres de celui qui parle, that / those pour ce qui est loin ; these et those
// au pluriel (Cambridge Grammar, « This, that, these, those »,
// dictionary.cambridge.org/grammar/british-grammar/this-that-these-those, consulte le 04/10/2026).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["pres-loin"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00";
    const entier = (v, defaut, min, max) => {
      const x = Number(v);
      return Math.min(max, Math.max(min, Math.round(Number.isFinite(x) ? x : defaut)));
    };
    const d = entier(valeurs.d, 2, 1, 6);
    const q = entier(valeurs.q, 1, 1, 3);
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 250");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const SOL = 200, LIMITE = 200; // la limite pres / loin passe entre d = 3 (centre x 175) et d = 4 (centre x 225)
    // Zone « près » legerement teintee, sol, limite et mots des zones.
    el("rect", { x: 60, y: 60, width: LIMITE - 60, height: SOL - 60, fill: "#EAF3EA" });
    el("line", { x1: 10, y1: SOL, x2: 330, y2: SOL, stroke: GRIS, "stroke-width": 3, "stroke-linecap": "round" });
    el("line", { x1: LIMITE, y1: 60, x2: LIMITE, y2: SOL, stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "6 5" });
    el("text", { x: 130, y: 226, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: "#2E7D32" }, "près");
    el("text", { x: 265, y: 226, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: GRIS }, "loin");

    // L'enfant (bleu) qui montre les balles du doigt.
    el("circle", { cx: 36, cy: 98, r: 15, fill: "#C9D6EA", stroke: BLEU, "stroke-width": 3 });
    el("line", { x1: 36, y1: 113, x2: 36, y2: 162, stroke: BLEU, "stroke-width": 4, "stroke-linecap": "round" });
    el("polyline", { points: "22,199 36,162 50,199", fill: "none", stroke: BLEU, "stroke-width": 4, "stroke-linecap": "round", "stroke-linejoin": "round" });
    el("line", { x1: 36, y1: 128, x2: 22, y2: 150, stroke: BLEU, "stroke-width": 4, "stroke-linecap": "round" });
    el("line", { x1: 36, y1: 126, x2: 70, y2: 140, stroke: BLEU, "stroke-width": 4, "stroke-linecap": "round" });

    // Les balles (orange), posees au sol a la distance d ; deux cote a cote, trois en petite pyramide.
    // Demi-largeur du groupe : 12 d'ecart + rayon 11 + demi-trait 1 = 24. Centres 95/135/175 (pres) et
    // 225/265/305 (loin) : toutes les balles restent entierement du bon cote du trait (175 + 24 < 200 < 225 - 24).
    const cx = d <= 3 ? 55 + d * 40 : 65 + d * 40, R = 11;
    const places = q === 1 ? [[0, 0]] : q === 2 ? [[-12, 0], [12, 0]] : [[-12, 0], [12, 0], [0, -21]];
    for (const [dx, dy] of places) {
      el("circle", { cx: cx + dx, cy: SOL - R - 1 + dy, r: R, fill: ORANGE, stroke: ENCRE, "stroke-width": 2 });
    }
    // Ligne du regard : du doigt aux balles, en pointilles.
    el("line", { x1: 74, y1: 142, x2: cx - 14 * (q > 1 ? 2 : 1), y2: SOL - 14, stroke: BLEU, "stroke-width": 2, "stroke-dasharray": "3 6", "stroke-linecap": "round" });
    return { d, q };
  },
};
