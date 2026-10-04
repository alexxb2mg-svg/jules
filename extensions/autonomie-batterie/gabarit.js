// Jules - gabarit "autonomie-batterie" : la batterie se vide au fil des heures. Graphique « energie restante
// (Wh) en fonction du temps (h) » : la droite part de l'energie stockee et descend d'autant de Wh par heure que
// l'objet consomme de W ; elle touche l'axe du temps a l'autonomie. Un trait pointille vertical marque
// l'exigence du cahier des charges ; la droite et le verdict sont verts si la batterie tient jusqu'a
// l'exigence, rouges sinon. Petite pile a gauche : sa jauge montre l'energie stockee (0 a 100 Wh).
// Curseurs : energie (5 a 100 Wh), puissance (1 a 50 W), exigence (1 a 20 h).
// Faits (EX-205) : E = P x t, energie en wattheures (Wh) = puissance en watts (W) x duree en heures (h)
// (programme de physique-chimie du cycle 4, « energie et ses conversions », BO n° 31 du 30 juillet 2020 ;
// le Wh est l'unite d'energie des batteries d'appareils portables). D'ou l'autonomie t = E / P :
// 40 Wh a 10 W -> 4 h. Modele ideal : puissance constante, batterie entierement utilisable.
// revele : la figure dit si l'exigence est respectee et l'axe gradue (une graduation par heure) donne
// l'autonomie, reponses d'un exercice de validation ; l'autonomie n'est pas ecrite en chiffres.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["autonomie-batterie"] = {
  dessiner(svg, valeurs) {
    const borne = (v, d, mini, maxi) => {
      const n = Number(v ?? d);
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const energie = borne(valeurs.energie, 40, 5, 100);
    const puissance = borne(valeurs.puissance, 10, 1, 50);
    const exigence = borne(valeurs.exigence, 5, 1, 20);
    const autonomie = energie / puissance; // en heures
    const valide = autonomie >= exigence;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const COULEUR = valide ? VERT : ROUGE;

    // --- Repere : temps 0 a 24 h en abscisse, energie 0 a 100 Wh en ordonnee ---
    const X0 = 84, X1 = 324, Y0 = 250, Y1 = 46, TMAX = 24, EMAX = 100;
    const X = (t) => X0 + ((X1 - X0) * t) / TMAX;
    const Y = (e) => Y0 - ((Y0 - Y1) * e) / EMAX;
    el("text", { x: X0 - 6, y: 30, "font-size": 13, "text-anchor": "middle", fill: BLEU, "font-weight": "bold" }, "énergie (Wh)");
    el("line", { x1: X0, y1: Y0, x2: X0, y2: Y1 - 6, stroke: ENCRE, "stroke-width": 2 });
    el("line", { x1: X0, y1: Y0, x2: X1 + 6, y2: Y0, stroke: ENCRE, "stroke-width": 2 });
    for (const e of [0, 50, 100]) {
      el("line", { x1: X0 - 5, y1: Y(e), x2: X0, y2: Y(e), stroke: ENCRE, "stroke-width": 2 });
      el("text", { x: X0 - 8, y: Y(e) + 5, "font-size": 13, "text-anchor": "end", fill: GRIS }, String(e));
    }
    // une graduation par heure (plus haute toutes les 6 h), chiffres toutes les 6 h
    for (let t = 0; t <= TMAX; t += 1) {
      const grand = t % 6 === 0;
      el("line", { x1: X(t), y1: Y0, x2: X(t), y2: Y0 + (grand ? 9 : 5), stroke: ENCRE, "stroke-width": 2 });
      if (grand) el("text", { x: X(t), y: Y0 + 24, "font-size": 13, "text-anchor": "middle", fill: GRIS }, String(t));
    }
    el("text", { x: X1, y: Y0 + 42, "font-size": 13, "text-anchor": "end", fill: ENCRE, "font-weight": "bold" }, "temps (h)");

    // --- Decharge : droite de (0, energie) a (autonomie, 0), coupee a 24 h ---
    const tFin = Math.min(autonomie, TMAX);
    const eFin = energie - puissance * tFin;
    el("polygon", {
      points: `${X(0)},${Y0} ${X(0)},${Y(energie)} ${X(tFin)},${Y(eFin)} ${X(tFin)},${Y0}`,
      fill: valide ? "#E3F1E4" : "#FBE3E6",
    });
    // --- Exigence : trait pointille vertical, entre la zone coloree et la droite ---
    el("line", { x1: X(exigence), y1: Y0, x2: X(exigence), y2: Y1, stroke: ORANGE, "stroke-width": 3, "stroke-dasharray": "7 5" });
    el("text", { x: Math.min(X(exigence) + 4, X1 - 64), y: Y1 - 2, "font-size": 13, fill: ORANGE, "font-weight": "bold" }, "exigence");

    el("line", { x1: X(0), y1: Y(energie), x2: X(tFin), y2: Y(eFin), stroke: COULEUR, "stroke-width": 4, "stroke-linecap": "round" });
    if (autonomie <= TMAX) {
      el("circle", { cx: X(autonomie), cy: Y0, r: 6, fill: COULEUR });
      // etiquette a droite du point (la droite arrive par la gauche), ramenee dans le repere pres du bord
      const aDroite = X(autonomie) + 40 <= X1;
      el("text", {
        x: aDroite ? X(autonomie) + 9 : X(autonomie) - 9, y: Y0 - 9, "font-size": 13,
        "text-anchor": aDroite ? "start" : "end", fill: COULEUR, "font-weight": "bold",
        stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke",
      }, "vide");
    } else {
      // tient plus de 24 h : fleche au bord du repere
      el("path", { d: `M${X1 + 2},${Y(eFin)} l-10,-7 v14 z`, fill: COULEUR });
    }

    // --- Pile a gauche : jauge de l'energie stockee ---
    el("rect", { x: 14, y: 70, width: 34, height: 150, rx: 6, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 2 });
    el("rect", { x: 23, y: 62, width: 16, height: 8, rx: 2, fill: ENCRE });
    const hJauge = (146 * energie) / EMAX;
    el("rect", { x: 16, y: 218 - hJauge, width: 30, height: hJauge, rx: 4, fill: BLEU });
    el("text", { x: 31, y: 240, "font-size": 13, "text-anchor": "middle", fill: BLEU, "font-weight": "bold" }, "pile");

    // --- Verdict ---
    el("text", { x: 14, y: 320, "font-size": 15, fill: COULEUR, "font-weight": "bold" }, valide ? "exigence respectée" : "exigence non respectée");
    return { autonomie, valide: valide ? 1 : 0 };
  },
};
