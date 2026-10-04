// Jules - gabarit "spatialisation-stereo" : un auditeur vu de dessus (en bas, nez vers le haut), deux enceintes
// (gauche, droite) et la source sonore telle qu'on l'entend (une note de musique) devant lui. pan (-5 a 5) place
// la source de la gauche vers la droite ; distance (1 a 5) l'eloigne. Deux barres montrent le volume envoye a
// chaque enceinte : c'est ce dosage qui fait entendre la source a gauche ou a droite (image stereo), et une
// source lointaine est plus faible dans les deux. On parle d'enceintes et non d'oreilles : en vrai, un son
// venu de la gauche arrive aussi a l'oreille droite ; c'est la voie d'une enceinte qui peut tomber a zero.
// Faits (EX-205) : repartition gauche/droite par la loi de panoramique a puissance constante (gauche = cos t,
// droite = sin t, t de 0 a 90 degres ; au centre les deux voies sont egales, a -3 dB chacune) ; en champ libre,
// la pression acoustique d'une source varie comme 1/distance (-6 dB quand la distance double).
// Sources : Wikipedia « Panoramique (audio) » (pan law) et « Loi en carre inverse » ; Eduscol, programme
// d'education musicale cycle 4 (timbre et espace : spatialisation, plans sonores).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["spatialisation-stereo"] = {
  dessiner(svg, valeurs) {
    const borne = (v, mini, maxi, defaut) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(maxi, Math.max(mini, Math.round(n))) : defaut;
    };
    const pan = borne(valeurs.pan, -5, 5, 0);
    const distance = borne(valeurs.distance, 1, 5, 2);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Volume de chaque voie : loi de panoramique a puissance constante, puis 1/distance.
    const t = ((pan + 5) / 10) * (Math.PI / 2);
    const gauche = Math.cos(t) / distance;
    const droite = Math.sin(t) / distance;

    // L'auditeur, vu de dessus : tete, nez vers le haut, deux oreilles.
    const HX = 170, HY = 272;
    el("ellipse", { cx: HX - 27, cy: HY, rx: 7, ry: 12, fill: "#E07B00", stroke: "#14243B", "stroke-width": 2 });
    el("ellipse", { cx: HX + 27, cy: HY, rx: 7, ry: 12, fill: "#E07B00", stroke: "#14243B", "stroke-width": 2 });
    el("circle", { cx: HX, cy: HY, r: 25, fill: "#F4EFE6", stroke: "#14243B", "stroke-width": 2 });
    el("polygon", { points: `${HX - 6},${HY - 23} ${HX + 6},${HY - 23} ${HX},${HY - 34}`, fill: "#14243B" });
    el("text", { x: HX - 27, y: HY + 34, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, "G");
    el("text", { x: HX + 27, y: HY + 34, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, "D");

    // Barres « enceinte gauche » et « enceinte droite » : hauteur proportionnelle au volume de chaque voie.
    const BH = 110, BB = 318;
    for (const [x, niveau, mot] of [[34, gauche, "gauche"], [306, droite, "droite"]]) {
      el("rect", { x: x - 14, y: BB - BH, width: 28, height: BH, fill: "#FFFFFF", stroke: "#6B7686", "stroke-width": 2 });
      const h = Math.max(2, niveau * (BH - 4));
      el("rect", { x: x - 12, y: BB - 2 - h, width: 24, height: h, fill: "#E07B00" });
      el("text", { x, y: BB - BH - 24, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, "enceinte");
      el("text", { x, y: BB - BH - 8, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, mot);
    }

    // La source : de x = 70 (pan -5) a x = 270 (pan 5), de y = 190 (proche) a y = 38 (loin).
    const SX = HX + pan * 20, SY = 228 - distance * 38;
    // Ondes : trois arcs tournes vers l'auditeur, de plus en plus pales quand la source s'eloigne.
    const versX = HX - SX, versY = HY - SY, n = Math.hypot(versX, versY);
    const ux = versX / n, uy = versY / n;
    const force = (1 / distance).toFixed(2);
    for (let k = 1; k <= 3; k++) {
      const r = 14 + k * 12;
      const a = 0.75; // demi-ouverture de l'arc, en radians
      const p1 = [SX + r * (ux * Math.cos(a) - uy * Math.sin(a)), SY + r * (uy * Math.cos(a) + ux * Math.sin(a))];
      const p2 = [SX + r * (ux * Math.cos(a) + uy * Math.sin(a)), SY + r * (uy * Math.cos(a) - ux * Math.sin(a))];
      el("path", {
        d: `M${p1[0].toFixed(1)},${p1[1].toFixed(1)} A${r},${r} 0 0 0 ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`,
        fill: "none", stroke: "#1F4E8C", "stroke-width": 3, "stroke-opacity": force, "stroke-linecap": "round",
      });
    }
    el("circle", { cx: SX, cy: SY, r: 14, fill: "#1F4E8C" });
    el("text", { x: SX, y: SY + 6, "font-size": 18, "text-anchor": "middle", fill: "#FFFFFF" }, "♪");
    return { pan, distance };
  },
};
