// Jules - gabarit "reseau-populations" (CM1) : un reseau alimentaire du jardin, rosier -> pucerons -> coccinelles
// et mesanges, avec une barre de quantite sous chaque etre vivant. Couper la lumiere ou l'eau de la plante, ou
// pulveriser un insecticide sur les pucerons, fait baisser les barres de proche en proche.
// Curseurs : lumiere (0 non, 1 oui), eau (0 non, 1 oui), insecticide (part des pucerons tues, en %, 0 a 100).
// Modele qualitatif, sans nombre ecrit : rosier = 1 si lumiere et eau, 0,4 s'il en manque une, 0,15 s'il manque
// les deux ; pucerons = rosier x (1 - insecticide) ; coccinelles = pucerons (elles mangent les pucerons) ;
// mesanges = moitie pucerons + moitie rosier (elles mangent aussi des chenilles, qui mangent les feuilles : voir
// la fiche « reseaux alimentaires », exemple insecticide).
// Faits (programme de sciences et technologie du cycle 3, arrete du 5-6-2026, BO n° 24 du 11/06/2026 : besoins des
// vegetaux en lumiere et en eau, reseaux alimentaires, influence de l'action humaine) : la fleche se lit « est mange
// par » et va du mange vers le mangeur ; les pucerons sont manges par les coccinelles et par les mesanges.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun code
// evalue.
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["reseau-populations"] = {
  dessiner(svg, valeurs) {
    const lumiere = Number(valeurs.lumiere ?? 1) >= 1 ? 1 : 0;
    const eau = Number(valeurs.eau ?? 1) >= 1 ? 1 : 0;
    const insecticide = Math.min(100, Math.max(0, Number(valeurs.insecticide ?? 0) || 0));
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

    const VERT = "#2E7D32", ROUGE = "#C8102E", BLEU = "#1F4E8C", GRIS = "#6B7686", TEXTE = "#14243B", ORANGE = "#E07B00";
    const rosier = lumiere && eau ? 1 : lumiere || eau ? 0.4 : 0.15;
    const pucerons = rosier * (1 - insecticide / 100);
    const coccinelles = pucerons;
    const mesanges = 0.5 * pucerons + 0.5 * rosier;
    const fleche = (x1, y1, x2, y2) => {
      el("line", { x1, y1, x2: x2 - 10, y2, stroke: TEXTE, "stroke-width": 2 });
      el("path", { d: `M ${x2} ${y2} L ${x2 - 11} ${y2 - 6} L ${x2 - 11} ${y2 + 6} Z`, fill: TEXTE });
    };

    // --- Conditions en haut : lumiere, eau, insecticide.
    el("circle", { cx: 34, cy: 28, r: 14, fill: lumiere ? ORANGE : "none", stroke: lumiere ? ORANGE : GRIS, "stroke-width": 2 });
    if (!lumiere) el("line", { x1: 18, y1: 44, x2: 50, y2: 12, stroke: ROUGE, "stroke-width": 3 });
    el("text", { x: 54, y: 33, "font-size": 13, fill: lumiere ? ORANGE : ROUGE, "font-weight": "bold" }, lumiere ? "lumière" : "pas de lumière");
    el("path", { d: "M 176 12 C 168 24 164 30 164 35 A 12 12 0 0 0 188 35 C 188 30 184 24 176 12 Z", fill: eau ? BLEU : "none", stroke: eau ? BLEU : GRIS, "stroke-width": 2 });
    if (!eau) el("line", { x1: 160, y1: 46, x2: 192, y2: 14, stroke: ROUGE, "stroke-width": 3 });
    el("text", { x: 194, y: 33, "font-size": 13, fill: eau ? BLEU : ROUGE, "font-weight": "bold" }, eau ? "eau" : "pas d'eau");
    el("text", { x: 330, y: 60, "font-size": 13, "text-anchor": "end", fill: insecticide > 0 ? ROUGE : GRIS, "font-weight": "bold" },
      insecticide > 0 ? `insecticide : ${insecticide} %` : "pas d'insecticide");
    if (insecticide > 0) { // pulverisateur au-dessus des pucerons
      el("rect", { x: 300, y: 14, width: 20, height: 28, rx: 3, fill: GRIS });
      for (let i = 0; i < 3; i++) el("circle", { cx: 290 - i * 9, cy: 22 + i * 4, r: 2.5, fill: ROUGE });
    }

    // --- Les quatre etres vivants (plus pales quand leur quantite baisse) et les fleches « est mange par ».
    const X = [44, 128, 212, 296], Y = 120;
    const visible = (q) => 0.25 + 0.75 * q;
    const g = (q) => el("g", { opacity: visible(q).toFixed(2) });
    const dans = (groupe, nom, attrs) => { const e = el(nom, attrs); groupe.appendChild(e); return e; };
    let groupe = g(rosier); // rosier : tige, feuilles, fleur
    dans(groupe, "line", { x1: X[0], y1: Y + 26, x2: X[0], y2: Y - 10, stroke: VERT, "stroke-width": 3 });
    dans(groupe, "ellipse", { cx: X[0] - 11, cy: Y + 8, rx: 11, ry: 6, fill: VERT });
    dans(groupe, "ellipse", { cx: X[0] + 11, cy: Y - 2, rx: 11, ry: 6, fill: VERT });
    dans(groupe, "circle", { cx: X[0], cy: Y - 18, r: 9, fill: VERT, stroke: TEXTE, "stroke-width": 2 });
    groupe = g(pucerons); // pucerons : petits ovales
    for (const [dx, dy] of [[-12, -8], [4, -12], [12, 4], [-6, 8], [0, -1]]) {
      dans(groupe, "ellipse", { cx: X[1] + dx, cy: Y + dy, rx: 5, ry: 3.5, fill: ORANGE });
    }
    groupe = g(coccinelles); // coccinelle : dos rouge a points noirs
    dans(groupe, "circle", { cx: X[2], cy: Y + 2, r: 15, fill: ROUGE });
    dans(groupe, "circle", { cx: X[2], cy: Y - 15, r: 6, fill: TEXTE });
    dans(groupe, "line", { x1: X[2], y1: Y - 12, x2: X[2], y2: Y + 17, stroke: TEXTE, "stroke-width": 2 });
    for (const [dx, dy] of [[-7, -3], [7, -3], [-6, 8], [6, 8]]) dans(groupe, "circle", { cx: X[2] + dx, cy: Y + dy, r: 2.5, fill: TEXTE });
    groupe = g(mesanges); // mesange : corps, tete, bec
    dans(groupe, "ellipse", { cx: X[3], cy: Y + 4, rx: 18, ry: 13, fill: BLEU });
    dans(groupe, "circle", { cx: X[3] + 15, cy: Y - 10, r: 9, fill: BLEU });
    dans(groupe, "circle", { cx: X[3] + 17, cy: Y - 12, r: 2, fill: TEXTE });
    dans(groupe, "path", { d: `M ${X[3] + 23} ${Y - 12} L ${X[3] + 32} ${Y - 8} L ${X[3] + 23} ${Y - 5} Z`, fill: ORANGE });

    fleche(X[0] + 16, Y, X[1] - 18, Y);
    fleche(X[1] + 18, Y, X[2] - 20, Y);
    el("path", { d: `M ${X[1]} ${Y - 20} C ${X[1] + 30} ${Y - 56}, ${X[3] - 40} ${Y - 56}, ${X[3] - 8} ${Y - 26}`, fill: "none", stroke: TEXTE, "stroke-width": 2 });
    el("path", { d: `M ${X[3] - 4} ${Y - 21} L ${X[3] - 7} ${Y - 34} L ${X[3] - 16} ${Y - 25} Z`, fill: TEXTE });

    const noms = ["rosier", "pucerons", "coccinelles", "mésanges"];
    const couleurs = [VERT, ORANGE, ROUGE, BLEU];
    const quantites = [rosier, pucerons, coccinelles, mesanges];
    const BH = 196, BB = 296; // haut et bas des barres
    noms.forEach((nom, i) => {
      el("text", { x: X[i], y: 172, "font-size": 13, "text-anchor": "middle", fill: couleurs[i], "font-weight": "bold" }, nom);
      el("rect", { x: X[i] - 20, y: BH, width: 40, height: BB - BH, fill: "none", stroke: "#C9D1DC", "stroke-width": 2 });
      const h = (BB - BH) * quantites[i];
      if (h > 0) el("rect", { x: X[i] - 20, y: BB - h, width: 40, height: h, fill: couleurs[i] });
    });
    el("line", { x1: 8, y1: BB, x2: 332, y2: BB, stroke: GRIS, "stroke-width": 2 });
    fleche(12, 322, 44, 322);
    el("text", { x: 50, y: 327, "font-size": 13, fill: TEXTE }, "« est mangé par »");
    el("text", { x: 330, y: 327, "font-size": 13, "text-anchor": "end", fill: TEXTE }, "barre = quantité");
    return { lumiere, eau, insecticide, rosier, pucerons, coccinelles, mesanges };
  },
};
