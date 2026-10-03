// Jules - gabarit "circuit-serie-derivation" : un generateur et deux lampes, en serie (montage = 0) ou en
// derivation (montage = 1). Fleches bleues = intensite (epaisseur proportionnelle), barres orange = tensions.
// Curseurs : montage, tension = U du generateur (V), r2 = resistance de la lampe 2 comparee a la lampe 1.
// Modele : lampes traitees comme des resistances, R1 = 1, R2 = r2.
//   serie      : I = U / (1 + R2), U1 = U / (1 + R2), U2 = U x R2 / (1 + R2) (U1 + U2 = U)
//   derivation : U1 = U2 = U, I1 = U, I2 = U / R2, I = I1 + I2
// Aucune valeur de U1, U2 ou I n'est ecrite (seule la tension U du generateur, choisie par l'eleve) :
// la figure montre les lois sans donner la reponse d'un exercice.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["circuit-serie-derivation"] = {
  dessiner(svg, valeurs) {
    const derivation = Number(valeurs.montage ?? 0) >= 0.5;
    const U = Math.max(0, Math.min(12, Number(valeurs.tension ?? 6)));
    const R2 = Math.max(0.5, Math.min(3, Number(valeurs.r2 ?? 1)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ORANGE = "#E07B00";
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Grandeurs (R1 = 1).
    let U1, U2, I, I1, I2;
    if (derivation) {
      U1 = U; U2 = U; I1 = U; I2 = U / R2; I = I1 + I2;
    } else {
      I = U / (1 + R2); I1 = I; I2 = I; U1 = I; U2 = I * R2;
    }
    const P1 = U1 * I1, P2 = U2 * I2; // puissance recue : eclat des lampes
    const IMAX = 36; // derivation, U = 12, R2 = 0,5
    const epaisseur = (i) => 2 + 8 * (i / IMAX);

    el("text", { x: 170, y: 24, "font-size": 16, "font-weight": "bold", "text-anchor": "middle", fill: ENCRE },
      derivation ? "en dérivation : 2 boucles" : "en série : 1 boucle");

    // Fils. Generateur sur le fil de gauche (x = 40), entre y = C - 10 (+) et y = C + 10 (-).
    const G = 40, D = 300, H = 60, B = 190, M = 190, C = 125; // C : hauteur des lampes et du generateur
    const fil = (x1, y1, x2, y2) =>
      el("line", { x1, y1, x2, y2, stroke: ENCRE, "stroke-width": 2, "stroke-linecap": "round" });
    fil(G, H, G, C - 10); fil(G, C + 10, G, B);
    el("line", { x1: 24, y1: C - 10, x2: 56, y2: C - 10, stroke: ENCRE, "stroke-width": 2 });
    el("line", { x1: 32, y1: C + 10, x2: 48, y2: C + 10, stroke: ENCRE, "stroke-width": 6 });
    el("text", { x: 62, y: C - 9, "font-size": 15, fill: ENCRE }, "+");
    el("text", { x: 62, y: C + 19, "font-size": 15, fill: ENCRE }, "−");

    const lampe = (cx, cy, nom, P, vertical) => {
      const k = Math.sqrt(Math.min(1, P / 144)); // 0 = eteinte, 1 = tres brillante
      if (k > 0) el("circle", { cx, cy, r: 14 + 10 * k, fill: "#F5C518", opacity: 0.25 + 0.45 * k });
      el("circle", { cx, cy, r: 14, fill: k > 0 ? "#FFF3B0" : "#FFFFFF", stroke: ENCRE, "stroke-width": 2 });
      const d = 9.9;
      el("line", { x1: cx - d, y1: cy - d, x2: cx + d, y2: cy + d, stroke: ENCRE, "stroke-width": 2 });
      el("line", { x1: cx - d, y1: cy + d, x2: cx + d, y2: cy - d, stroke: ENCRE, "stroke-width": 2 });
      if (vertical) el("text", { x: cx - 36, y: cy + 5, "font-size": 15, "font-weight": "bold", "text-anchor": "middle", fill: ENCRE }, nom);
      else el("text", { x: cx, y: cy + 34, "font-size": 15, "font-weight": "bold", "text-anchor": "middle", fill: ENCRE }, nom);
    };

    // Fleche de courant (sens conventionnel : sort par la borne +) le long d'un fil.
    const fleche = (x1, y1, x2, y2, i, nom, dxT, dyT) => {
      if (i <= 0) return;
      const w = epaisseur(i);
      const L = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / L, uy = (y2 - y1) / L;
      const t = Math.max(9, w * 1.6); // taille de la pointe
      const bx = x2 - ux * t, by = y2 - uy * t;
      el("line", { x1, y1, x2: bx, y2: by, stroke: BLEU, "stroke-width": w, opacity: 0.85 });
      el("polygon", {
        points: `${x2},${y2} ${bx - uy * (t * 0.75)},${by + ux * (t * 0.75)} ${bx + uy * (t * 0.75)},${by - ux * (t * 0.75)}`,
        fill: BLEU,
      });
      el("text", { x: (x1 + x2) / 2 + dxT, y: (y1 + y2) / 2 + dyT, "font-size": 15, "font-weight": "bold", "text-anchor": "middle", fill: BLEU }, nom);
    };

    if (!derivation) {
      fil(G, H, 156, H); fil(184, H, D, H); fil(D, H, D, C - 14); fil(D, C + 14, D, B); fil(D, B, G, B);
      lampe(170, H, "L1", P1, false);
      lampe(D, C, "L2", P2, true);
      fleche(70, H, 135, H, I, "I", 0, 26);
      fleche(250, B, 185, B, I, "I", 0, -14);
    } else {
      fil(G, H, D, H); fil(G, B, D, B);
      fil(M, H, M, C - 14); fil(M, C + 14, M, B);
      fil(D, H, D, C - 14); fil(D, C + 14, D, B);
      for (const y of [H, B]) el("circle", { cx: M, cy: y, r: 5, fill: ENCRE });
      lampe(M, C, "L1", P1, true);
      lampe(D, C, "L2", P2, true);
      fleche(70, H, 150, H, I, "I", 0, 28);
      fleche(M, C + 21, M, B - 8, I1, "I1", 24, 5);
      fleche(212, H, 272, H, I2, "I2", 0, 28);
      fleche(150, B, 80, B, I, "I", 0, -14);
    }

    // Barres de tension : U (generateur), U1 (lampe 1), U2 (lampe 2). Echelle : 12 V = 200 px.
    const X0 = 80, K = 200 / 12, HB = 18;
    const lignes = [["U", 228], ["U1", 266], ["U2", 304]];
    for (const [nom, y] of lignes) {
      el("text", { x: X0 - 10, y: y + 14, "font-size": 15, "font-weight": "bold", "text-anchor": "end", fill: ENCRE }, nom);
      el("line", { x1: X0, y1: y - 3, x2: X0, y2: y + HB + 3, stroke: GRIS, "stroke-width": 2 });
    }
    const barre = (x, y, v, plein) => {
      if (v <= 0) return;
      el("rect", {
        x, y, width: v * K, height: HB, rx: 3,
        fill: plein ? ORANGE : "#FBE3C4", stroke: ORANGE, "stroke-width": 2,
      });
    };
    barre(X0, 228, U, true);
    el("text", { x: X0 + U * K + 6, y: 242, "font-size": 15, fill: ENCRE }, `${String(U).replace(".", ",")} V`);
    barre(X0, 266, U1, false);
    // En serie, U2 commence la ou U1 s'arrete : les deux bouts mis ensemble font U.
    barre(derivation ? X0 : X0 + U1 * K, 304, U2, false);
    if (U > 0) {
      el("line", {
        x1: X0 + U * K, y1: 222, x2: X0 + U * K, y2: 330,
        stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "4 4",
      });
    }
    return { montage: derivation ? 1 : 0, tension: U, r2: R2, U1, U2, I, I1, I2 };
  },
};
