// Jules - gabarit "spectre-ondes" : la famille des rayonnements (ondes electromagnetiques), des ondes radio aux
// rayons X, sur une bande ; un repere mobile choisit un domaine, une onde dessinee au-dessus se resserre quand on
// avance (longueur d'onde plus courte, energie transportee plus grande). Valeur :
//   k 1..6 (pas 0.25) : position sur le spectre. Domaines (memes bornes que les lectures des fiches) :
//     k < 2 radio ; 2 <= k < 3 micro-ondes ; 3 <= k < 3.75 infrarouge ; 3.75 <= k <= 4.25 visible ;
//     4.25 < k < 5.25 ultraviolet ; k >= 5.25 rayons X. Le visible est la bande la plus etroite : une petite
//     fenetre (dessin qualitatif, l'echelle reelle couvre plus de dix puissances de dix).
// Faits (verifies) :
//   - Ordre radio, micro-ondes, infrarouge, visible, ultraviolet, X (puis gamma) par longueur d'onde decroissante
//     et energie croissante ; meme nature que la lumiere, meme vitesse dans le vide (environ 300 000 km/s).
//     Sources : programme de physique-chimie du cycle 4 (BO n° 31 du 30/07/2020, theme « Des signaux pour
//     observer et communiquer ») ; norme ISO 21348 (definitions des domaines du rayonnement solaire) ;
//     NASA Science, « Tour of the Electromagnetic Spectrum » (science.nasa.gov/ems).
//   - Visible : environ 400 nm (violet) a 800 nm (rouge), seul domaine que l'oeil percoit (programme cycle 4).
//   - Usages : radio et television (ondes radio ; le telephone portable est aussi range cote radio, comme dans la
//     fiche 3e « types-rayonnements », les micro-ondes etant les ondes radio les plus courtes) ; four a
//     micro-ondes et radar ; telecommande et camera thermique (infrarouge) ; bronzage et coups de soleil (UV) ;
//     radiographie (rayons X). Sources : NASA Science (ci-dessus) ; fiche 3e « types-rayonnements ».
// Palette : celle des consignes, plus le jaune #C9A400 et le violet #6A3D9A dans la seule bande du visible
// (arc-en-ciel du rouge au violet, sans lequel le visible ne se reconnait pas).
// La figure ECRIT le nom du domaine et un usage : c'est la reponse d'un exercice « quel rayonnement pour cet
// usage ? » -> revele: true (extension.yaml).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["spectre-ondes"] = {
  dessiner(svg, valeurs) {
    const brut = Number(valeurs.k ?? 4);
    const k = Number.isFinite(brut) ? Math.min(6, Math.max(1, brut)) : 4;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const c in attrs) e.setAttribute(c, attrs[c]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", GRIS = "#6B7686", ROUGE = "#C8102E", ORANGE = "#E07B00";

    // Domaines : [debut, fin) en k, nom court sur la bande, nom long, usage, couleur de la bande.
    const DOMAINES = [
      { de: 0.875, a: 2, court: "radio", nom: "ondes radio", usage: "radio, télévision", couleur: "#DCE6F2" },
      { de: 2, a: 3, court: "micro", nom: "micro-ondes", usage: "four, radar", couleur: "#C9D8EC" },
      { de: 3, a: 3.75, court: "IR", nom: "infrarouge", usage: "télécommande, chaleur", couleur: "#F3D3D3" },
      { de: 3.75, a: 4.375, court: "", nom: "lumière visible", usage: "nos yeux la voient", couleur: "" },
      { de: 4.375, a: 5.25, court: "UV", nom: "ultraviolet", usage: "bronzage, coup de soleil", couleur: "#E3D9F0" },
      { de: 5.25, a: 6.125, court: "X", nom: "rayons X", usage: "radiographie", couleur: "#D9D9DE" },
    ];
    // Bornes des lectures : le visible va de 3.75 a 4.25 compris (pas de 0.25).
    const indice = k < 2 ? 0 : k < 3 ? 1 : k < 3.75 ? 2 : k <= 4.25 ? 3 : k < 5.25 ? 4 : 5;
    const d = DOMAINES[indice];
    const X0 = 14, X1 = 326;
    const xk = (v) => X0 + ((v - 0.875) / (6.125 - 0.875)) * (X1 - X0);

    svg.setAttribute("viewBox", "0 0 340 300");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    // Titre : le domaine et un usage.
    el("text", { x: 170, y: 28, "font-size": 20, "font-weight": "bold", "text-anchor": "middle", fill: ENCRE }, d.nom);
    el("text", { x: 170, y: 52, "font-size": 15, "text-anchor": "middle", fill: GRIS }, d.usage);

    // Onde : longueur d'onde de 110 px (k = 1) a 10 px (k = 6), decroissance geometrique.
    const lambda = 110 * Math.pow(10 / 110, (k - 1) / 5);
    const yo = 105, amp = 22;
    const couleurVisible = ["#C8102E", "#E07B00", "#C9A400", "#2E7D32", "#1F4E8C", "#6A3D9A"];
    const couleurOnde = indice === 3
      ? couleurVisible[Math.min(5, Math.max(0, Math.round(((k - 3.75) / 0.5) * 5)))]
      : "#1F4E8C"; // bleu = onde invisible ; couleurs de l'arc-en-ciel seulement dans le visible
    let chemin = `M${X0},${yo}`;
    for (let x = 1; x <= X1 - X0; x++) {
      chemin += ` L${X0 + x},${(yo - amp * Math.sin((2 * Math.PI * x) / lambda)).toFixed(1)}`;
    }
    el("path", { d: chemin, fill: "none", stroke: couleurOnde, "stroke-width": 2, "stroke-linejoin": "round" });
    // Une longueur d'onde reperee (accolade grise) quand elle est assez grande pour etre vue.
    if (lambda >= 18) {
      const xa = X0 + lambda / 4, xb = xa + lambda;
      el("line", { x1: xa, y1: yo - amp - 10, x2: xb, y2: yo - amp - 10, stroke: GRIS, "stroke-width": 2 });
      el("line", { x1: xa, y1: yo - amp - 15, x2: xa, y2: yo - amp - 5, stroke: GRIS, "stroke-width": 2 });
      el("line", { x1: xb, y1: yo - amp - 15, x2: xb, y2: yo - amp - 5, stroke: GRIS, "stroke-width": 2 });
    }

    // Bande du spectre.
    const B = { y: 150, h: 46 };
    for (const dom of DOMAINES) {
      const xa = xk(dom.de), xb = xk(dom.a);
      if (dom.couleur) {
        el("rect", { x: xa, y: B.y, width: xb - xa, height: B.h, fill: dom.couleur });
      } else {
        const n = couleurVisible.length;
        couleurVisible.forEach((c, i) => {
          el("rect", { x: xa + ((xb - xa) * i) / n, y: B.y, width: (xb - xa) / n + 0.3, height: B.h, fill: c });
        });
      }
      if (dom.court) {
        el("text", { x: (xa + xb) / 2, y: B.y + B.h / 2 + 5, "font-size": 14, "text-anchor": "middle", fill: ENCRE }, dom.court);
      }
      el("line", { x1: xa, y1: B.y, x2: xa, y2: B.y + B.h, stroke: "#FFFFFF", "stroke-width": 2 });
    }
    el("rect", { x: X0, y: B.y, width: X1 - X0, height: B.h, fill: "none", stroke: GRIS, "stroke-width": 2 });
    // « visible » sous sa bande etroite.
    el("text", { x: (xk(3.75) + xk(4.375)) / 2, y: B.y + B.h + 18, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "visible");

    // Repere mobile : triangle rouge au-dessus de la bande et trait a travers.
    const xm = xk(k);
    el("line", { x1: xm, y1: B.y - 6, x2: xm, y2: B.y + B.h + 4, stroke: ROUGE, "stroke-width": 3 });
    el("path", { d: `M${xm - 8},${B.y - 16} L${xm + 8},${B.y - 16} L${xm},${B.y - 4} z`, fill: ROUGE });

    // Energie transportee : fleche orange, faible a gauche, forte a droite.
    const yE = 250;
    el("line", { x1: X0 + 4, y1: yE, x2: X1 - 12, y2: yE, stroke: ORANGE, "stroke-width": 3 });
    el("path", { d: `M${X1},${yE} L${X1 - 14},${yE - 7} L${X1 - 14},${yE + 7} z`, fill: ORANGE });
    el("text", { x: 170, y: yE - 10, "font-size": 14, "text-anchor": "middle", fill: ORANGE }, "énergie transportée");
    el("text", { x: X0, y: yE + 22, "font-size": 13, fill: GRIS }, "faible");
    el("text", { x: X1, y: yE + 22, "font-size": 13, "text-anchor": "end", fill: GRIS }, "forte");
    return { k, domaine: d.nom };
  },
};
