// Jules - gabarit "engrenages" : deux roues dentees A et B qui s'engrenent (ou deux poulies et une courroie).
// Valeurs : dents_a et dents_b (nombre de dents, la taille de la roue suit), avance (nombre de dents passees au
// point de contact, le meme pour les deux roues), courroie (0 = roues en prise, 1 = poulies et courroie).
// Chaque roue porte un repere rouge qui part du haut ; il devient vert quand la roue a fait un nombre entier de
// tours (repere revenu au depart). Les deux reperes verts ensemble = multiple commun de dents_a et dents_b.
// Aucun nombre de tours ni aucune vitesse n'est ecrit : on les voit en faisant tourner.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["engrenages"] = {
  dessiner(svg, valeurs) {
    const za = Math.max(3, Math.round(Number(valeurs.dents_a ?? 12)));
    const zb = Math.max(3, Math.round(Number(valeurs.dents_b ?? 18)));
    const avance = Number(valeurs.avance ?? 0);
    const courroie = Number(valeurs.courroie ?? 0) >= 1;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte, parent) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined && texte !== null) e.textContent = texte; // texte brut, jamais interprete
      (parent || svg).appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Taille : rayon primitif proportionnel au nombre de dents (s px par dent), le tout tient dans le cadre.
    const ECART = courroie ? 34 : 0; // vide entre deux poulies
    const HAUT = 230; // diametre maximal d'une roue (laisse la place des fleches en bas)
    let s = Math.min((314 - ECART) / (2 * (za + zb)), HAUT / (2 * Math.max(za, zb)));
    const pasDent = 2 * Math.PI * s; // longueur d'une dent sur le cercle primitif
    const h = courroie ? 0 : Math.max(4, Math.min(16, 0.5 * pasDent)); // hauteur des dents (dents larges : plus hautes)
    s = Math.min(s, (314 - ECART - 2 * h) / (2 * (za + zb)));
    const ra = s * za, rb = s * zb;
    const cy = 166;
    const xa = (340 - (2 * ra + 2 * rb + ECART)) / 2 + ra;
    const xb = xa + ra + rb + ECART;

    // Angles (degres, sens des aiguilles d'une montre a l'ecran) : A tourne de avance/dents_a tours ;
    // B du meme nombre de dents, en sens inverse si les roues sont en prise, dans le meme sens avec la courroie.
    const tourA = avance / za, tourB = avance / zb;
    const angA = 360 * tourA, angB = (courroie ? 1 : -1) * 360 * tourB;
    const entier = (t) => Math.abs(t - Math.round(t)) < 1e-9;

    // Courroie : les deux brins exterieurs, tangents aux deux poulies.
    if (courroie) {
      const D = xb - xa, nx = (ra - rb) / D, ny = Math.sqrt(1 - nx * nx);
      for (const sy of [-1, 1]) {
        el("line", {
          x1: f(xa + ra * nx), y1: f(cy + sy * ra * ny), x2: f(xb + rb * nx), y2: f(cy + sy * rb * ny),
          stroke: "#6B7686", "stroke-width": 5, "stroke-linecap": "round",
        });
      }
    }

    // Une roue : groupe tourne autour de son centre ; contour dente (ou cercle de poulie), moyeu, repere.
    const roue = (x, r, z, angle, decalage, trait, fond, revenu) => {
      const g = el("g", { transform: `rotate(${f(angle)} ${f(x)} ${cy})` });
      if (courroie) {
        el("circle", { cx: f(x), cy, r: f(r), fill: fond, stroke: trait, "stroke-width": 3 }, null, g);
      } else {
        const points = [];
        for (let k = 0; k < z; k++) {
          const c = ((k + decalage) / z) * 2 * Math.PI; // centre de la dent k
          const d = Math.PI / z; // demi-pas angulaire
          // Sommet de la dent (+-0,3 demi-pas), flanc, creux (0,7 a 1,3 demi-pas) : dent et creux de meme largeur.
          for (const [a, rr] of [[c - d * 0.3, r + h / 2], [c + d * 0.3, r + h / 2], [c + d * 0.7, r - h / 2], [c + d * 1.3, r - h / 2]]) {
            points.push(`${f(x + rr * Math.cos(a))},${f(cy + rr * Math.sin(a))}`);
          }
        }
        el("polygon", { points: points.join(" "), fill: fond, stroke: trait, "stroke-width": 2, "stroke-linejoin": "round" }, null, g);
      }
      el("circle", { cx: f(x), cy, r: f(Math.max(3, Math.min(8, r * 0.12))), fill: trait }, null, g);
      // Repere : rayon du centre vers le haut (position de depart), rouge en route, vert quand la roue est revenue.
      const couleur = revenu ? "#2E7D32" : "#C8102E";
      el("line", { x1: f(x), y1: cy, x2: f(x), y2: f(cy - r * 0.92), stroke: couleur, "stroke-width": 4, "stroke-linecap": "round" }, null, g);
      el("circle", { cx: f(x), cy: f(cy - r * 0.92), r: f(Math.max(3.5, Math.min(7, r * 0.1))), fill: couleur }, null, g);
    };
    // Trait gris pointille au-dessus de chaque roue : la position de depart du repere.
    for (const [x, r] of [[xa, ra], [xb, rb]]) {
      el("line", { x1: f(x), y1: f(cy - r - h / 2 - 4), x2: f(x), y2: f(cy - r - h / 2 - 16), stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "3 3" });
    }
    // A : une dent a droite (angle 0, vers B). B : un creux a gauche (angle 180), pour que les dents s'emboitent.
    roue(xa, ra, za, angA, 0, "#1F4E8C", "#E4ECF7", entier(tourA));
    roue(xb, rb, zb, angB, zb / 2 + 0.5, "#E07B00", "#FCEBD6", entier(tourB));

    // Fleches courbes sous chaque roue : le sens de rotation (A toujours dans le sens des aiguilles d'une montre).
    const fleche = (x, horaire, couleur) => {
      const y = 322, r = 15;
      const sens = horaire ? 1 : 0;
      const x0 = x - r * (horaire ? 1 : -1), x1 = x + r * (horaire ? 1 : -1);
      // Arc par le haut, de gauche a droite (horaire) ou de droite a gauche ; pointe vers le bas au bout.
      el("path", { d: `M${f(x0)},${y} A${r},${r} 0 0 ${sens} ${f(x1)},${y}`, fill: "none", stroke: couleur, "stroke-width": 3 });
      el("polygon", { points: `${f(x1 - 7)},${y - 2} ${f(x1 + 7)},${y - 2} ${f(x1)},${y + 9}`, fill: couleur });
    };
    fleche(xa, true, "#1F4E8C");
    fleche(xb, courroie, "#E07B00");

    // Etiquettes : la roue et son nombre de dents (donnees de l'enonce, jamais un resultat).
    const nomA = courroie ? "poulie A" : `A : ${za} dents`;
    const nomB = courroie ? "poulie B" : `B : ${zb} dents`;
    el("text", { x: 12, y: 24, "font-size": 16, "font-weight": 700, fill: "#1F4E8C" }, nomA);
    el("text", { x: 328, y: 24, "font-size": 16, "font-weight": 700, "text-anchor": "end", fill: "#E07B00" }, nomB);
    return { dents_a: za, dents_b: zb, avance, courroie: courroie ? 1 : 0 };
  },
};
