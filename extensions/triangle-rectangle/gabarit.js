// Jules - gabarit "triangle-rectangle" : triangle ABC rectangle en C, cotes ac = AC et bc = BC reglables,
// avec un carre construit sur chaque cote et son aire ecrite (AC², BC², et AC² + BC² sur l'hypotenuse).
// La longueur AB n'est jamais ecrite : la figure montre le theoreme de Pythagore sans donner la longueur.
// reponse (0 ou 1, defaut 0) : a 0, le carre orange porte « ? » au lieu de AC² + BC² ; aucune valeur de AB ni de
// AB² n'est ecrite (aide aux devoirs, cours). A 1, son aire est ecrite (mode reexplique seulement).
// Echelle adaptee a la taille de la figure (carres compris) : meme 1 et 1 remplissent le cadre.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["triangle-rectangle"] = {
  dessiner(svg, valeurs) {
    const ac = Number(valeurs.ac ?? 6);
    const bc = Number(valeurs.bc ?? 8);
    const reponse = Number(valeurs.reponse ?? 0) >= 1;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Repere mathematique (y vers le haut), en unites : C a l'origine, A sur l'axe vertical, B sur l'horizontal.
    // Carre sur [AC] a gauche, sur [BC] en dessous, sur [AB] vers l'exterieur (decale de (ac ; bc)).
    // Boite englobante : x de -ac a ac + bc, y de -bc a ac + bc.
    const largeur = 2 * ac + bc, hauteur = ac + 2 * bc;
    const MARGE = 24; // place des lettres A, B, C et d'une aire ecrite hors d'un petit carre
    const U = Math.min((340 - 2 * MARGE) / largeur, (340 - 2 * MARGE) / hauteur);
    const ox = (340 - largeur * U) / 2 + ac * U; // abscisse de C dans le cadre
    const oy = (340 - hauteur * U) / 2 + (ac + bc) * U; // ordonnee de C dans le cadre
    const P = (x, y) => ({ x: ox + x * U, y: oy - y * U });
    const C = P(0, 0), A = P(0, ac), B = P(bc, 0);
    const pts = (liste) => liste.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");

    const carres = [
      { coins: [P(0, 0), P(0, ac), P(-ac, ac), P(-ac, 0)], aire: ac * ac, trait: "#2E7D32", fond: "#E3F1E4", cote: ac * U },
      { coins: [P(0, 0), P(bc, 0), P(bc, -bc), P(0, -bc)], aire: bc * bc, trait: "#1F4E8C", fond: "#E4ECF7", cote: bc * U },
      {
        coins: [P(0, ac), P(bc, 0), P(bc + ac, bc), P(ac, ac + bc)],
        aire: ac * ac + bc * bc, trait: "#E07B00", fond: "#FCEBD6", cote: Math.hypot(ac, bc) * U,
      },
    ];
    for (const c of carres) el("polygon", { points: pts(c.coins), fill: c.fond, stroke: c.trait, "stroke-width": 2 });

    // Le triangle par-dessus : cotes de l'angle droit en vert et bleu, hypotenuse en orange (comme leurs carres).
    el("polygon", { points: pts([A, B, C]), fill: "#FFFFFF", stroke: "none" });
    el("line", { x1: C.x, y1: C.y, x2: A.x, y2: A.y, stroke: "#2E7D32", "stroke-width": 3 });
    el("line", { x1: C.x, y1: C.y, x2: B.x, y2: B.y, stroke: "#1F4E8C", "stroke-width": 3 });
    el("line", { x1: A.x, y1: A.y, x2: B.x, y2: B.y, stroke: "#E07B00", "stroke-width": 3 });
    const q = Math.min(14, 0.35 * Math.min(ac, bc) * U); // codage de l'angle droit, plus petit que les cotes
    el("path", { d: `M${C.x + q},${C.y} L${C.x + q},${C.y - q} L${C.x},${C.y - q}`, fill: "none", stroke: "#14243B", "stroke-width": 2 });

    // Aire de chaque carre en son centre ; carre trop petit pour le nombre : ecrite juste a cote, dehors.
    const TAILLE = 16;
    carres.forEach((c, i) => {
      const centre = { x: c.coins.reduce((s, p) => s + p.x, 0) / 4, y: c.coins.reduce((s, p) => s + p.y, 0) / 4 };
      const texte = i === 2 && !reponse ? "?" : String(c.aire);
      const assez = c.cote >= texte.length * 10 + 10;
      let x = centre.x, y = centre.y + TAILLE * 0.35, ancre = "middle";
      if (!assez && i === 0) { x = c.coins[2].x - 4; y = c.coins[2].y + TAILLE * 0.35; ancre = "end"; }
      if (!assez && i === 1) { y = c.coins[2].y + TAILLE + 2; }
      el("text", { x: x.toFixed(1), y: y.toFixed(1), "font-size": TAILLE, "font-weight": 700, "text-anchor": ancre, fill: c.trait }, texte);
    });

    // Lettres des sommets, dans les angles laisses libres par les carres.
    el("text", { x: A.x.toFixed(1), y: (A.y - 8).toFixed(1), "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, "A");
    el("text", { x: (B.x + 8).toFixed(1), y: (B.y + 5).toFixed(1), "font-size": 15, "font-weight": 700, fill: "#14243B" }, "B");
    el("text", { x: (C.x - 5).toFixed(1), y: (C.y + 16).toFixed(1), "font-size": 15, "font-weight": 700, "text-anchor": "end", fill: "#14243B" }, "C");
    return { ac, bc, reponse: reponse ? 1 : 0 };
  },
};
