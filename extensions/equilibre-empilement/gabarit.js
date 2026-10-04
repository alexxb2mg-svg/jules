// Jules - gabarit "equilibre-empilement" : deux blocs empiles vus de face, sur un quadrillage.
// Curseur : decalage (deplacement du bloc du haut, en carreaux, - vers la gauche, + vers la droite).
// La base fait 4 carreaux de large ; le bloc du haut aussi, son centre de gravite (point rouge) est en son milieu.
// Regle dessinee : un objet pose tient tant que la verticale de son centre de gravite tombe sur sa surface
// d'appui ; si elle sort de la surface d'appui, il bascule autour du bord. Ici la surface d'appui du bloc du haut
// est le dessus de la base (de -2 a +2 carreaux) : il tient pour |decalage| <= 2 (a 2 tout juste, limite), il
// bascule au-dela. Pas de nombre ecrit : revele false.
// Sources : programme d'arts plastiques du cycle 3 (« l'espace en trois dimensions » : equilibre, empilement,
// assemblage, la question de la stabilite), BO n° 31 du 30 juillet 2020 ; programme de sciences et technologie
// cycle 3 (objets techniques, stabilite) ; notion de polygone de sustentation (mecanique, manuels de physique de
// lycee : un solide pose est en equilibre si la verticale de son centre de gravite passe dans sa base d'appui).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["equilibre-empilement"] = {
  dessiner(svg, valeurs) {
    const borne = (v, min, max) => Math.min(max, Math.max(min, v));
    const decalage = borne(Number(valeurs.decalage ?? 0), -4, 4);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32",
      ORANGE = "#E07B00", QUADRILLE = "#E3E7EC";

    svg.setAttribute("viewBox", "0 0 340 300");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    const C = 24, XC = 170, SOL = 250; // carreau, centre, sol
    const X = (carreaux) => XC + carreaux * C;
    // Quadrillage (carreaux a compter), sol.
    for (let k = -6; k <= 6; k += 1) el("line", { x1: X(k), y1: 58, x2: X(k), y2: SOL, stroke: QUADRILLE, "stroke-width": 2 });
    for (let y = SOL; y >= 58; y -= C) el("line", { x1: X(-6), y1: y, x2: X(6), y2: y, stroke: QUADRILLE, "stroke-width": 2 });
    el("line", { x1: 14, y1: SOL, x2: 326, y2: SOL, stroke: GRIS, "stroke-width": 3 });

    // Base : 4 carreaux de large, 2 de haut ; son dessus (surface d'appui) en vert.
    const HB = 2 * C, HH = 2 * C, YB = SOL - HB;
    el("rect", { x: X(-2), y: YB, width: 4 * C, height: HB, fill: "#C9D8EE", stroke: BLEU, "stroke-width": 3 });
    el("line", { x1: X(-2), y1: YB, x2: X(2), y2: YB, stroke: VERT, "stroke-width": 6 });

    const tient = Math.abs(decalage) <= 2;
    const sens = decalage > 0 ? 1 : -1;
    // Bloc du haut : coins avant rotation, centre de gravite au milieu.
    const coins = [[decalage - 2, 0], [decalage + 2, 0], [decalage + 2, 2], [decalage - 2, 2]]; // en carreaux
    let angle = 0; // en radians, rotation autour du bord de la base
    if (!tient) angle = sens * (Math.PI / 7);
    const pivot = [2 * sens, 0];
    const tourne = ([x, y]) => {
      const dx = x - pivot[0], dy = y - pivot[1];
      // y vers le haut ; basculer vers la droite = rotation dans le sens horaire vu a l'ecran
      const c = Math.cos(-angle), s = Math.sin(-angle);
      return [pivot[0] + dx * c - dy * s, pivot[1] + dx * s + dy * c];
    };
    const ecran = ([x, y]) => [X(x), YB - y * C];
    if (!tient) {
      // Position de depart en pointilles (ou le bloc etait pose).
      const p0 = coins.map(ecran).map(([x, y]) => `${x},${y}`).join(" ");
      el("polygon", { points: p0, fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "5 5" });
    }
    const pts = coins.map(tient ? (p) => p : tourne).map(ecran);
    el("polygon", { points: pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" "),
      fill: tient ? "#FCE3C2" : "#F6C9CF", stroke: tient ? ORANGE : ROUGE, "stroke-width": 3 });

    // Centre de gravite et sa verticale (jusqu'au niveau du dessus de la base).
    const [gx, gy] = ecran((tient ? (p) => p : tourne)([decalage, 1]));
    const couleur = tient ? VERT : ROUGE;
    el("line", { x1: gx, y1: gy, x2: gx, y2: YB + 2, stroke: couleur, "stroke-width": 2, "stroke-dasharray": "4 4" });
    el("path", { d: `M${gx},${YB + 4} l-6,-10 l12,0 z`, fill: couleur });
    el("circle", { cx: gx, cy: gy, r: 7, fill: ROUGE, stroke: "#FFFFFF", "stroke-width": 2 });

    // Fleche de bascule.
    if (!tient) {
      const ax = X(2 * sens + sens * 2.6), ay = YB - 3.2 * C;
      el("path", { d: `M${X(2 * sens + sens * 0.6)},${YB - 3.6 * C} Q${ax},${ay - 10} ${ax + sens * 4},${YB - 1.2 * C}`,
        fill: "none", stroke: ROUGE, "stroke-width": 3 });
      el("path", { d: `M${ax + sens * 4},${YB - 1.2 * C + 2} l${-sens * 9},-11 l${sens * 12},-2 z`, fill: ROUGE });
    }

    // Legende courte.
    el("line", { x1: 14, y1: 18, x2: 34, y2: 18, stroke: VERT, "stroke-width": 6 });
    el("text", { x: 42, y: 23, "font-size": 14, fill: VERT }, "surface d'appui");
    el("circle", { cx: 24, cy: 40, r: 6, fill: ROUGE });
    el("text", { x: 42, y: 45, "font-size": 14, fill: ENCRE }, "centre de gravité");
    el("text", { x: XC, y: 284, "font-size": 16, "font-weight": "bold", "text-anchor": "middle", fill: couleur },
      tient ? (Math.abs(decalage) === 2 ? "ça tient tout juste" : "ça tient") : "ça bascule");
    return { decalage, tient };
  },
};
