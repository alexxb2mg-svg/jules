// Jules - gabarit "barre-ratio" : partage selon un ratio a : b (ou a : b : c).
// La quantite a partager est une barre decoupee en a + b (+ c) parts EGALES : a parts bleues, b parts vertes,
// c parts orange (c = 0 : partage en deux). Au-dessus de chaque groupe, son nombre de parts ; sous la barre,
// « 1 part » sous la premiere part. Aucune quantite ni aucun montant n'est ecrit : la figure montre le decoupage
// (une part = total / (a + b + c)), l'eleve fait le calcul.
// Definition : ratio a : b, partage en a + b parts egales ; programme de mathematiques du cycle 4 modifie (BO n° 31
// du 30/07/2020, theme « proportionnalite » : « utiliser la notion de ratio ») ; attendus de fin de 3e, eduscol.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["barre-ratio"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const n = Number(v ?? defaut);
      return Math.min(max, Math.max(min, Math.round(Number.isFinite(n) ? n : defaut)));
    };
    const a = entier(valeurs.a, 3, 1, 9);
    const b = entier(valeurs.b, 4, 1, 9);
    const c = entier(valeurs.c, 0, 0, 9);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", VERT = "#2E7D32", ORANGE = "#E07B00";
    const X0 = 20, L = 300, Y = 64, H = 50, parts = a + b + c, w = L / parts;
    svg.setAttribute("viewBox", "0 0 340 190");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Accolade du tout, au-dessus : « la quantité à partager ».
    el("text", { x: 170, y: 18, "font-size": 14, "text-anchor": "middle", fill: GRIS }, "la quantité à partager");
    el("path", { d: `M${X0},${Y - 22} L${X0},${Y - 30} L${X0 + L},${Y - 30} L${X0 + L},${Y - 22}`, fill: "none", stroke: GRIS, "stroke-width": 2 });

    // Groupes de parts egales, chacun avec son nombre de parts au-dessus.
    let debut = 0;
    for (const [n, couleur] of [[a, BLEU], [b, VERT], [c, ORANGE]]) {
      if (n === 0) continue;
      for (let i = 0; i < n; i++) {
        el("rect", { x: X0 + (debut + i) * w, y: Y, width: w, height: H, fill: couleur, stroke: "#FFFFFF", "stroke-width": 2 });
      }
      el("text", { x: X0 + (debut + n / 2) * w, y: Y - 6, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: couleur }, String(n));
      debut += n;
    }
    el("rect", { x: X0, y: Y, width: L, height: H, fill: "none", stroke: ENCRE, "stroke-width": 2 });

    // « 1 part » sous la premiere part, avec une petite accolade.
    el("path", { d: `M${X0},${Y + H + 6} L${X0},${Y + H + 14} L${X0 + w},${Y + H + 14} L${X0 + w},${Y + H + 6}`, fill: "none", stroke: ENCRE, "stroke-width": 2 });
    el("text", { x: X0, y: Y + H + 34, "font-size": 14, "text-anchor": "start", fill: ENCRE }, "1 part");

    // Rappel du ratio sous la barre, dans les couleurs des groupes.
    const ratio = el("text", { x: 170, y: Y + H + 66, "font-size": 17, "font-weight": 700, "text-anchor": "middle", fill: ENCRE });
    const morceaux = c > 0 ? [[a, BLEU], [" : ", ENCRE], [b, VERT], [" : ", ENCRE], [c, ORANGE]] : [[a, BLEU], [" : ", ENCRE], [b, VERT]];
    ratio.appendChild(document.createTextNode("ratio "));
    for (const [t, couleur] of morceaux) {
      const span = document.createElementNS(NS, "tspan");
      span.setAttribute("fill", couleur);
      span.textContent = String(t);
      ratio.appendChild(span);
    }
    return { a, b, c, parts };
  },
};
