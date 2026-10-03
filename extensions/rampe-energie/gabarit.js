// Jules - gabarit "rampe-energie" : un skateur part sans vitesse du haut gauche d'une rampe en U.
// Curseur x = position (0 = haut gauche, 0,5 = en bas, 1 = haut droite) ; curseur f = frottements (0 a 0,5).
// Trois barres : energie de position (bleu), energie cinetique (orange), energie thermique (rouge) ; la barre
// « total » garde toujours la meme longueur (conservation de l'energie).
// Modele (energies rapportees a l'energie de depart = 1) :
//   hauteur h(x) = (2x - 1)^2 ; position = h ; thermique = f x x (frottements le long du trajet) ;
//   cinetique = 1 - h - f x x. Avec frottements, le skateur s'arrete quand la cinetique s'annule :
//   (2x - 1)^2 + f x = 1, soit x = 1 - f / 4 ; il ne remonte donc pas a la hauteur de depart.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["rampe-energie"] = {
  dessiner(svg, valeurs) {
    const xDemande = Math.max(0, Math.min(1, Number(valeurs.x ?? 0.25)));
    const f = Math.max(0, Math.min(0.5, Number(valeurs.f ?? 0)));
    const xMax = 1 - f / 4;
    const x = Math.min(xDemande, xMax);
    const arrete = f > 0 && xDemande >= xMax;
    const h = (2 * x - 1) ** 2;
    const thermique = f * x;
    const cinetique = Math.max(0, 1 - h - thermique);
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

    // --- rampe : x de 0 a 1 -> abscisse de 40 a 300 ; hauteur 0 a 1 -> ordonnee de 180 a 50.
    const PX = (u) => 40 + 260 * u;
    const PY = (v) => 180 - 130 * v;
    const points = [];
    for (let i = 0; i <= 40; i++) {
      const u = i / 40;
      points.push(`${i ? "L" : "M"}${PX(u).toFixed(1)},${PY((2 * u - 1) ** 2).toFixed(1)}`);
    }
    el("path", { d: `${points.join(" ")} L300,190 L40,190 Z`, fill: "#EEF1F5", stroke: "none" });
    el("path", { d: points.join(" "), fill: "none", stroke: GRIS, "stroke-width": 4, "stroke-linecap": "round" });
    el("line", { x1: 30, y1: PY(1), x2: 310, y2: PY(1), stroke: GRIS, "stroke-width": 1.5, "stroke-dasharray": "4 4" });
    el("text", { x: 170, y: PY(1) - 8, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "hauteur de départ");

    // --- skateur : disque pose sur la rampe, decale le long de la normale.
    const pente = 4 * (2 * x - 1) * (130 / 260); // derivee de la courbe dessinee (sens ecran inverse)
    const nx = -pente / Math.hypot(1, pente), ny = -1 / Math.hypot(1, pente);
    const sx = PX(x) + nx * 14, sy = PY(h) + ny * 14;
    el("circle", { cx: sx, cy: sy, r: 12, fill: ENCRE });
    if (arrete) {
      el("text", { x: sx - 18, y: sy + 5, "font-size": 14, "font-weight": "bold", "text-anchor": "end", fill: ROUGE }, "il s'arrête ici");
    }

    // --- barres d'energie (longueur 200 px = energie de depart).
    const X0 = 108, L = 200, HB = 18;
    const lignes = [
      ["position", 208, [[h, BLEU]]],
      ["cinétique", 238, [[cinetique, ORANGE]]],
      ["thermique", 268, [[thermique, ROUGE]]],
      ["total", 308, [[h, BLEU], [cinetique, ORANGE], [thermique, ROUGE]]],
    ];
    for (const [nom, y, parts] of lignes) {
      el("text", { x: X0 - 8, y: y + 14, "font-size": 15, "font-weight": nom === "total" ? "bold" : "normal", "text-anchor": "end", fill: ENCRE }, nom);
      el("rect", { x: X0, y, width: L, height: HB, rx: 3, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
      let debut = X0;
      for (const [v, couleur] of parts) {
        const largeur = Math.max(0, Math.min(1, v)) * L;
        if (largeur > 0.5) el("rect", { x: debut, y, width: largeur, height: HB, fill: couleur });
        debut += largeur;
      }
    }
    el("line", { x1: 20, y1: 296, x2: 320, y2: 296, stroke: GRIS, "stroke-width": 1.5 });
    return { x, f, position: h, cinetique, thermique, total: h + cinetique + thermique, arrete };
  },
};
