// Jules - gabarit "decomposition-mouvement" : une balle qui rebondit, decomposee en images (comme une pellicule).
// Curseurs : images (nombre d'images prises pendant l'action, ou images par seconde), vitesse (vitesse de
// defilement a l'ecran : 1 = normale, < 1 ralenti, > 1 accelere), ellipse (images retirees au milieu de l'action).
// En haut : une position de la balle par image (peu d'images = mouvement saccade, beaucoup = fluide ; les images
// retirees laissent un trou marque « ellipse »). Au milieu : la pellicule, 1 case = 1 image. En bas : la duree de
// l'action en vrai et a l'ecran, a la meme echelle : duree a l'ecran = duree vraie x (images gardees / images) /
// vitesse (ralenti : plus longue ; accelere : plus courte ; ellipse : raccourcie). Aucune valeur n'est ecrite.
// Faits utilises (lectures des fiches) : 24 images par seconde = cadence du cinema sonore (norme adoptee a la fin
// des annees 1920) ; le cinema muet tournait autour de 16 a 18 images par seconde ; Eadweard Muybridge decompose le
// galop d'un cheval en photographies successives (The Horse in Motion, 1878).
// Sources : programme d'arts plastiques cycle 4 (« la narration visuelle » : temps, duree, rythme, ellipse) et
// cycle 3, BO n° 31 du 30 juillet 2020 ; CNC / Cinematheque francaise, « La cadence de prise de vues » ;
// Library of Congress, notice « The Horse in Motion » (Muybridge, 1878).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["decomposition-mouvement"] = {
  dessiner(svg, valeurs) {
    const borne = (v, min, max) => Math.min(max, Math.max(min, v));
    const images = borne(Math.round(Number(valeurs.images ?? 12)), 3, 24);
    const vitesse = borne(Number(valeurs.vitesse ?? 1), 0.25, 4);
    // On garde toujours la premiere et la derniere image : au plus images - 2 images retirees.
    const ellipse = borne(Math.round(Number(valeurs.ellipse ?? 0)), 0, images - 2);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E";

    svg.setAttribute("viewBox", "0 0 340 300");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    // Images retirees : un bloc au milieu de l'action.
    const debut = Math.floor((images - ellipse) / 2);
    const retiree = (k) => ellipse > 0 && k >= debut && k < debut + ellipse;

    // 1. Trajectoire : la balle tombe, rebondit, remonte moins haut, retombe (sol a y = 160).
    const SOL = 160, R = 9;
    const position = (k) => {
      const t = images === 1 ? 0 : k / (images - 1);
      const h = 112 * Math.abs(Math.cos(1.5 * Math.PI * t)) * (1 - 0.3 * t);
      return [30 + 280 * t, SOL - R - h];
    };
    el("line", { x1: 12, y1: SOL, x2: 328, y2: SOL, stroke: GRIS, "stroke-width": 3 });
    for (let k = 0; k < images; k += 1) {
      if (retiree(k)) continue;
      const [x, y] = position(k);
      el("circle", { cx: x, cy: y, r: R, fill: k === 0 ? "#FFFFFF" : BLEU, stroke: BLEU, "stroke-width": 2,
        opacity: k === 0 || k === images - 1 ? 1 : 0.75 });
    }
    if (ellipse > 0) {
      const xa = position(debut)[0] - 6, xb = position(debut + ellipse - 1)[0] + 6;
      el("path", { d: `M${xa},34 L${xa},26 L${xb},26 L${xb},34`, fill: "none", stroke: ROUGE, "stroke-width": 3 });
      el("text", { x: (xa + xb) / 2, y: 19, "font-size": 14, "font-weight": "bold", "text-anchor": "middle", fill: ROUGE },
        "ellipse");
    }

    // 2. Pellicule : une case par image, les cases retirees barrees en rouge.
    const Y = 180, H = 30, largeur = Math.min(26, 300 / images), X0 = 170 - (largeur * images) / 2;
    el("rect", { x: X0 - 4, y: Y - 7, width: largeur * images + 8, height: H + 14, rx: 3, fill: ENCRE });
    for (let k = 0; k < images; k += 1) {
      const x = X0 + k * largeur;
      if (retiree(k)) {
        el("rect", { x: x + 1.5, y: Y, width: largeur - 3, height: H, fill: ENCRE, stroke: ROUGE, "stroke-width": 2 });
        el("line", { x1: x + 2, y1: Y + 2, x2: x + largeur - 2, y2: Y + H - 2, stroke: ROUGE, "stroke-width": 2 });
      } else {
        el("rect", { x: x + 1.5, y: Y, width: largeur - 3, height: H, fill: "#FFFFFF" });
      }
    }
    el("text", { x: 170, y: 236, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "pellicule : 1 case = 1 image");

    // 3. Duree de l'action : en vrai (gris, fixe) et a l'ecran (bleu), meme echelle.
    const UNITE = 55; // 55 px = duree vraie de l'action ; a vitesse 0,25 l'ecran dure 4 fois plus : 220 px
    const ecran = (UNITE * (images - ellipse)) / images / vitesse;
    el("text", { x: 12, y: 262, "font-size": 13, fill: GRIS }, "en vrai");
    el("rect", { x: 92, y: 251, width: UNITE, height: 14, fill: GRIS });
    el("text", { x: 12, y: 286, "font-size": 13, fill: BLEU }, "à l'écran");
    el("rect", { x: 92, y: 275, width: Math.max(4, ecran), height: 14, fill: BLEU });
    return { images, vitesse, ellipse, duree_ecran: Math.round((ecran / UNITE) * 100) / 100 };
  },
};
