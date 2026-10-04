// Jules - gabarit "illusion-optique" : l'illusion de Muller-Lyer. Deux traits A et B de MEME longueur, termines
// par des pointes (chevrons) ; selon l'ouverture des pointes, un trait parait plus long que l'autre. Une regle
// peut apparaitre : deux pointilles verts tombent des extremites de A sur celles de B et une regle graduee est posee
// sous chaque trait, ce qui MONTRE l'egalite sans ecrire de longueur. Valeurs :
//   angle -60..60 (degres) : inclinaison des pointes par rapport a la verticale. angle > 0 : pointes de A ouvertes
//                vers l'exterieur (>---<, A parait plus long), pointes de B refermees (<--->, B parait plus court) ;
//                angle < 0 : l'inverse ; angle = 0 : barres droites |---| aux deux bouts, pas d'illusion ;
//   regle  0..1 : 1 = afficher la verification (pointilles et regles).
// Fait : illusion decrite par F. C. Muller-Lyer, « Optische Urteilstauschungen », Archiv fur Anatomie und
// Physiologie (Physiologische Abteilung), 1889, 2 (suppl.), p. 263-270 (reference : The Illusions Index,
// illusionsindex.org/i/mueller-lyer) : le trait aux pointes ouvertes vers l'exterieur parait plus long que
// celui aux pointes en fleches, a longueur egale. Lien avec la notion : programme de sciences et technologie du
// cycle 3 (BO n° 24 du 11/06/2026, p. 14, cite par la fiche CM1 « cm1-cerveau-grandes-fonctions », dont le bloc
// schema-illusion montre deja cette illusion) : le cerveau interprete les messages des organes des sens.
// Aucune longueur n'est ecrite : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["illusion-optique"] = {
  dessiner(svg, valeurs) {
    const lire = (x, a, b, d) => {
      const n = Number(x ?? d);
      return Number.isFinite(n) ? Math.min(b, Math.max(a, n)) : d;
    };
    const angle = lire(valeurs.angle, -60, 60, 45);
    const regle = Math.round(lire(valeurs.regle, 0, 1, 0)) === 1;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const c in attrs) e.setAttribute(c, attrs[c]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", VERT = "#2E7D32", GRIS = "#6B7686";

    svg.setAttribute("viewBox", "0 0 340 250");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    const XA = 95, XB = 255; // memes extremites pour les deux traits : meme longueur (160)
    const L = 30; // longueur d'une pointe
    // Un trait et ses quatre pointes ; t = inclinaison en degres (> 0 : pointes vers l'exterieur).
    const trait = (y, t, lettre) => {
      const r = (t * Math.PI) / 180;
      const dx = L * Math.sin(r), dy = L * Math.cos(r);
      el("line", { x1: XA, y1: y, x2: XB, y2: y, stroke: BLEU, "stroke-width": 4, "stroke-linecap": "round" });
      for (const s of [-1, 1]) {
        // extremite droite : la pointe part vers +x si t > 0 ; extremite gauche : miroir.
        el("line", { x1: XB, y1: y, x2: XB + dx, y2: y + s * dy, stroke: BLEU, "stroke-width": 4, "stroke-linecap": "round" });
        el("line", { x1: XA, y1: y, x2: XA - dx, y2: y + s * dy, stroke: BLEU, "stroke-width": 4, "stroke-linecap": "round" });
      }
      el("text", { x: 22, y: y + 7, "font-size": 20, "font-weight": "bold", fill: ENCRE }, lettre);
    };
    const yA = 70, yB = 175;
    trait(yA, angle, "A");
    trait(yB, -angle, "B");

    if (regle) {
      // Pointilles verts : les extremites de A tombent exactement sur celles de B.
      for (const x of [XA, XB]) {
        el("line", { x1: x, y1: yA - 36, x2: x, y2: yB + 36, stroke: VERT, "stroke-width": 2, "stroke-dasharray": "6 5" });
      }
      // Une regle graduee sous chaque trait, de la meme longueur que lui.
      for (const y of [yA + 40, yB + 40]) {
        el("rect", { x: XA, y, width: XB - XA, height: 14, fill: "#E8F3E9", stroke: VERT, "stroke-width": 2 });
        for (let i = 0; i <= 8; i++) {
          const x = XA + (i * (XB - XA)) / 8;
          el("line", { x1: x, y1: y, x2: x, y2: y + (i % 2 === 0 ? 10 : 6), stroke: VERT, "stroke-width": 2 });
        }
      }
    } else {
      el("text", { x: 170, y: 244, "font-size": 14, "text-anchor": "middle", fill: GRIS }, "Lequel est le plus long ?");
    }
    return { angle, regle };
  },
};
