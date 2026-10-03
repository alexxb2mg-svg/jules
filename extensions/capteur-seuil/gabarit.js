// Jules - gabarit "capteur-seuil" : chaine d'information d'une veilleuse. Le capteur de lumiere donne une
// valeur (0 a 1023) lue par le microcontroleur ; le programme la compare au seuil (losange de
// l'algorigramme « mesure < seuil ? ») : branche « oui » = allumer la LED, branche « non » = l'eteindre.
// Curseurs : mesure, seuil (0 a 1023). Au cas limite mesure = seuil, le test « < » est faux : LED eteinte.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["capteur-seuil"] = {
  dessiner(svg, valeurs) {
    const mesure = Math.min(1023, Math.max(0, Math.round(Number(valeurs.mesure ?? 600))));
    const seuil = Math.min(1023, Math.max(0, Math.round(Number(valeurs.seuil ?? 300))));
    const oui = mesure < seuil;
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
    const VERT = "#2E7D32", GRIS = "#6B7686", BLEU = "#1F4E8C", ROUGE = "#C8102E";

    // --- Capteur : barre de la valeur lue (0 en bas, 1023 en haut) et trait du seuil ---
    const BAS = 300, HAUT = 52;
    const Y = (v) => BAS - ((BAS - HAUT) * v) / 1023;
    el("text", { x: 60, y: 22, "font-size": 13, "text-anchor": "middle", fill: "#14243B", "font-weight": "bold" }, "capteur");
    el("text", { x: 60, y: 40, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "0 à 1023");
    el("rect", { x: 46, y: HAUT, width: 28, height: BAS - HAUT, fill: "none", stroke: GRIS, "stroke-width": 2 });
    el("rect", { x: 46, y: Y(mesure), width: 28, height: BAS - Y(mesure), fill: BLEU });
    el("line", { x1: 38, y1: Y(seuil), x2: 82, y2: Y(seuil), stroke: ROUGE, "stroke-width": 3 });
    el("text", { x: 40, y: Y(mesure) + 5, "font-size": 14, "text-anchor": "end", fill: BLEU, "font-weight": "bold" }, String(mesure));
    el("text", { x: 86, y: Y(seuil) + 5, "font-size": 14, fill: ROUGE, "font-weight": "bold" }, String(seuil));
    el("text", { x: 4, y: 326, "font-size": 13, fill: BLEU, "font-weight": "bold" }, "mesure");
    el("text", { x: 62, y: 326, "font-size": 13, fill: ROUGE, "font-weight": "bold" }, "seuil");

    // --- Algorigramme : lire, tester, agir ---
    const fleche = (x1, y1, x2, y2, couleur, actif) => {
      el("line", {
        x1, y1, x2, y2: y2 - 7, stroke: couleur, "stroke-width": actif ? 3 : 2,
        "stroke-dasharray": actif ? "none" : "5 4",
      });
      el("path", { d: `M${x2},${y2} l-6,-9 h12 z`, fill: couleur });
    };
    el("rect", { x: 160, y: 10, width: 140, height: 32, rx: 8, fill: "#FFFFFF", stroke: "#14243B", "stroke-width": 2 });
    el("text", { x: 230, y: 31, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, "lire la mesure");
    fleche(230, 42, 230, 64, "#14243B", true);
    const L = { x: 230, y: 108, dx: 82, dy: 44 };
    el("polygon", {
      points: `${L.x},${L.y - L.dy} ${L.x + L.dx},${L.y} ${L.x},${L.y + L.dy} ${L.x - L.dx},${L.y}`,
      fill: "#FFFFFF", stroke: "#14243B", "stroke-width": 2,
    });
    el("text", { x: L.x, y: L.y - 3, "font-size": 14, "text-anchor": "middle", fill: BLEU, "font-weight": "bold" }, "mesure");
    el("text", { x: L.x, y: L.y + 15, "font-size": 14, "text-anchor": "middle", fill: "#14243B" }, "< seuil ?");

    // Branches : « oui » a gauche, « non » a droite ; la branche suivie est verte et pleine.
    const branche = (cote, actif, mot, action) => {
      const couleur = actif ? VERT : GRIS;
      const xs = L.x + cote * L.dx, xb = cote < 0 ? 150 : 310;
      el("line", { x1: xs, y1: L.y, x2: xb, y2: L.y, stroke: couleur, "stroke-width": actif ? 3 : 2, "stroke-dasharray": actif ? "none" : "5 4" });
      fleche(xb, L.y, xb, 176, couleur, actif);
      el("text", { x: xb + (cote < 0 ? 8 : -8), y: L.y + 40, "font-size": 14, "text-anchor": cote < 0 ? "start" : "end", fill: couleur, "font-weight": "bold" }, mot);
      const xc = cote < 0 ? 175 : 285;
      el("rect", {
        x: xc - 52, y: 176, width: 104, height: 42, rx: 8, fill: actif ? "#E3F1E4" : "#FFFFFF",
        stroke: couleur, "stroke-width": actif ? 3 : 2,
      });
      el("text", { x: xc, y: 193, "font-size": 13, "text-anchor": "middle", fill: actif ? "#14243B" : GRIS }, action);
      el("text", { x: xc, y: 210, "font-size": 13, "text-anchor": "middle", fill: actif ? "#14243B" : GRIS }, "la LED");
      fleche(xc, 218, cote < 0 ? 220 : 240, 252, couleur, actif);
    };
    branche(-1, oui, "oui", "allumer");
    branche(1, !oui, "non", "éteindre");

    // --- LED ---
    const C = { x: 230, y: 282 };
    if (oui) {
      for (let i = 0; i < 8; i++) {
        const a = (i * Math.PI) / 4;
        el("line", {
          x1: C.x + 27 * Math.cos(a), y1: C.y + 27 * Math.sin(a), x2: C.x + 39 * Math.cos(a), y2: C.y + 39 * Math.sin(a),
          stroke: "#E07B00", "stroke-width": 3, "stroke-linecap": "round",
        });
      }
    }
    el("circle", { cx: C.x, cy: C.y, r: 20, fill: oui ? "#FFC94D" : "#EEF1F5", stroke: oui ? "#E07B00" : GRIS, "stroke-width": 3 });
    el("text", { x: C.x + 46, y: C.y + 5, "font-size": 14, fill: "#14243B", "font-weight": "bold" }, "LED");
    el("text", { x: C.x, y: 336, "font-size": 13, "text-anchor": "middle", fill: oui ? "#E07B00" : GRIS }, oui ? "allumée" : "éteinte");
    return { mesure, seuil, led: oui ? 1 : 0 };
  },
};
