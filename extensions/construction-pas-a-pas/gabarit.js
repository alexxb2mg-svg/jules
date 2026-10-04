// Jules - gabarit "construction-pas-a-pas" : un programme de construction trace une etape a la fois (CM1).
// Programme (celui de la fiche, d'apres l'exemple Eduscol) : 1. trace le segment [AB] ; 2. trace le rectangle
// ABCD (angles droits a l'equerre en A et en B, puis on reporte la largeur) ; 3. place le milieu I de [AB] ;
// 4. trace le cercle de centre A qui passe par I. A chaque etape, le nouveau trace est en orange, ce qui etait
// deja trace passe en gris. Sur papier quadrille en cm (1 carreau = 1 cm) ; les longueurs AB et BC sont
// ecrites (ce sont les donnees du programme), le rayon AI ne l'est pas.
// Source : Eduscol, « Exemples pour la mise en oeuvre du programme de mathematiques en CM1 - Exemples de
// reussite » (2025), p. 21 ; programme de mathematiques du cycle 3 (BO n° 16 du 17/04/2025) : regle, equerre,
// compas ; le milieu d'un segment est a egale distance de ses extremites.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["construction-pas-a-pas"] = {
  // dessiner(svg, valeurs) : etape 0 (feuille vide) a 4 (figure finie), longueur AB 3 a 8 cm, largeur BC 1 a 6 cm.
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => {
      const n = Math.round(Number(v ?? d));
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const etape = ent(valeurs.etape, 1, 0, 4);
    const L = ent(valeurs.longueur, 5, 3, 8); // 3 cm au moins : sous 3 cm, codages du milieu et angles droits se touchent
    const l = ent(valeurs.largeur, 3, 1, 6);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", GRIS = "#6B7686", ORANGE = "#E07B00";
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // 1 cm = 25 px, echelle fixe. A est fixe : le rectangle pousse vers la droite et vers le haut, le cercle
    // (rayon L/2 <= 4 cm) tient a gauche et en dessous de A.
    const u = 25, A = { x: 120, y: 215 };
    const B = { x: A.x + L * u, y: A.y }, C = { x: B.x, y: A.y - l * u }, D = { x: A.x, y: A.y - l * u };
    const I = { x: A.x + (L * u) / 2, y: A.y };

    // Papier quadrille.
    for (let x = 20; x <= 320; x += u) el("line", { x1: x, y1: 15, x2: x, y2: 315, stroke: "#E3E8EF", "stroke-width": 1 });
    for (let y = 15; y <= 315; y += u) el("line", { x1: 20, y1: y, x2: 320, y2: y, stroke: "#E3E8EF", "stroke-width": 1 });

    const couleur = (n) => (n === etape ? ORANGE : GRIS);
    const epaisseur = (n) => (n === etape ? 4 : 2.5);
    const seg = (P, Q, n) => el("line", { x1: P.x, y1: P.y, x2: Q.x, y2: Q.y, stroke: couleur(n), "stroke-width": epaisseur(n), "stroke-linecap": "round" });
    // Halo blanc sous les lettres et les longueurs : lisibles meme quand le cercle passe dessous (selon AB et BC).
    const HALO = { stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke", "stroke-linejoin": "round" };
    const lettre = (x, y, t, n) => el("text", { x, y, "font-size": 16, "font-weight": 700, fill: n === etape ? ORANGE : ENCRE, "text-anchor": "middle", "font-family": "sans-serif", ...HALO }, t);
    const cote = (x, y, t, n, ancre) => el("text", { x, y, "font-size": 14, fill: couleur(n), "text-anchor": ancre, "font-family": "sans-serif", ...HALO }, t);
    const cm = (n) => `${n} cm`;

    // Etape 4 en premier : le cercle passe sous les traits du rectangle.
    if (etape >= 4) {
      el("circle", { cx: A.x, cy: A.y, r: (L * u) / 2, fill: "none", stroke: couleur(4), "stroke-width": epaisseur(4) });
    }
    if (etape >= 2) {
      seg(A, D, 2); seg(D, C, 2); seg(B, C, 2);
      // Codage des angles droits en A et en B (les deux poses de l'equerre).
      const q = 12;
      el("path", { d: `M${A.x + q},${A.y} L${A.x + q},${A.y - q} L${A.x},${A.y - q}`, fill: "none", stroke: couleur(2), "stroke-width": 2 });
      el("path", { d: `M${B.x - q},${B.y} L${B.x - q},${B.y - q} L${B.x},${B.y - q}`, fill: "none", stroke: couleur(2), "stroke-width": 2 });
      // La largeur BC : a droite de [BC] quand il y a la place, sinon dedans, a gauche du codage d angle droit.
      if (L <= 6) cote(C.x + 8, (B.y + C.y) / 2 + 5, cm(l), 2, "start");
      else cote(C.x - 16, (B.y + C.y) / 2 + 5, cm(l), 2, "end");
      lettre(C.x + 10, C.y - 6, "C", 2);
      lettre(D.x - 10, D.y - 6, "D", 2);
    }
    if (etape >= 1) {
      seg(A, B, 1);
      el("circle", { cx: A.x, cy: A.y, r: 4, fill: couleur(1) });
      el("circle", { cx: B.x, cy: B.y, r: 4, fill: couleur(1) });
      lettre(A.x - 10, A.y + 20, "A", 1);
      lettre(B.x + 8, B.y + 20, "B", 1);
      // La longueur AB : au-dessus du segment avant l'etape 2 ; ensuite sous [AB], aux trois quarts vers B,
      // pour rester hors du cercle (rayon AB / 2) et loin du point I.
      if (etape >= 2) cote(A.x + (3 * L * u) / 4, A.y + 38, cm(L), 1, "middle");
      else cote((A.x + B.x) / 2, A.y - 10, cm(L), 1, "middle");
    }
    if (etape >= 3) {
      // Le milieu I et le codage des deux moities egales.
      el("circle", { cx: I.x, cy: I.y, r: 5, fill: couleur(3) });
      lettre(I.x + 11, I.y + 20, "I", 3); // decale a droite : le cercle passe par I a la verticale
      for (const xm of [(A.x + I.x) / 2, (I.x + B.x) / 2]) {
        el("line", { x1: xm - 3, y1: A.y - 7, x2: xm + 3, y2: A.y + 7, stroke: couleur(3), "stroke-width": 2.5 });
      }
    }
    if (etape === 4) {
      // La pointe du compas : un anneau orange sur le centre A.
      el("circle", { cx: A.x, cy: A.y, r: 8, fill: "none", stroke: ORANGE, "stroke-width": 3 });
    }
    return { etape, longueur: L, largeur: l };
  },
};
