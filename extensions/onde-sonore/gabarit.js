// Jules - gabarit "onde-sonore" : un haut-parleur, le milieu traverse par le son, une oreille, et l'ecran
// d'un oscilloscope. Valeurs :
//   hauteur   1..13 : cran de frequence sur une echelle adaptee (10, 20, 50, 100, 200, 440, 1 000, 2 000,
//                     5 000, 10 000, 20 000, 30 000, 40 000 Hz) ; plus le cran est haut, plus les vagues
//                     sont serrees (dessin qualitatif : on ne peut pas dessiner 40 000 oscillations) ;
//   intensite 1..5  : hauteur des vagues (doux -> fort) ;
//   duree     1..4  : longueur du son, en temps (le train de vagues occupe duree/4 de l'ecran) ;
//   milieu    0..2  : 0 vide (rien ne vibre, aucun son), 1 air (340 m/s), 2 eau (environ 1 500 m/s).
// Une fiche peut n'en utiliser que quelques-unes (3e : hauteur et milieu ; CM1 : hauteur, intensite, duree) :
// les autres prennent leur valeur par defaut, et ce qui les montre n'est pas dessine (sans milieu : ni
// frequence en Hz ni vitesse, la figure dit seulement grave, medium ou aigu ; sans intensite : pas de
// fleche orange ; sans duree : pas d'accolade verte). Peu d'elements a l'ecran, chacun relie a un curseur.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["onde-sonore"] = {
  dessiner(svg, valeurs) {
    const borne = (x, a, b, d) => {
      const n = Math.round(Number(x ?? d));
      return Number.isFinite(n) ? Math.min(b, Math.max(a, n)) : d;
    };
    const cran = borne(valeurs.hauteur, 1, 13, 6);
    const intensite = borne(valeurs.intensite, 1, 5, 3);
    const duree = borne(valeurs.duree, 1, 4, 4);
    const milieu = borne(valeurs.milieu, 0, 2, 1);
    const avecMilieu = valeurs.milieu !== undefined;
    const avecIntensite = valeurs.intensite !== undefined;
    const avecDuree = valeurs.duree !== undefined;
    const FREQUENCES = [10, 20, 50, 100, 200, 440, 1000, 2000, 5000, 10000, 20000, 30000, 40000];
    const PERIODES = [2, 3, 4, 5, 6, 7.5, 9, 11, 13, 15, 17, 20, 23]; // vagues sur toute la largeur de l'ecran
    const f = FREQUENCES[cran - 1];
    const audible = f >= 20 && f <= 20000;
    const domaine = f < 20 ? "infrason" : f > 20000 ? "ultrason" : f <= 200 ? "son grave" : f <= 1000 ? "son médium" : "son aigu";
    const entendu = audible && milieu > 0;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const milliers = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0");
    const BLEU = "#1F4E8C", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00", GRIS = "#6B7686", ENCRE = "#14243B";

    svg.setAttribute("viewBox", "0 0 340 340");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 26, "font-size": 18, "font-weight": "bold", "text-anchor": "middle", fill: ENCRE },
      avecMilieu ? `${milliers(f)} Hz : ${domaine}` : domaine);

    // Haut-parleur.
    el("rect", { x: 10, y: 76, width: 14, height: 28, fill: GRIS });
    el("polygon", { points: "24,76 44,58 44,122 24,104", fill: GRIS });
    // Milieu traverse par le son.
    const M = { x: 50, y: 50, l: 230, h: 80 };
    if (milieu === 0) {
      el("rect", { x: M.x, y: M.y, width: M.l, height: M.h, fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "6 5" });
      el("text", { x: M.x + M.l / 2, y: M.y + M.h / 2 + 5, "font-size": 15, "text-anchor": "middle", fill: ROUGE }, "vide : rien ne vibre");
    } else {
      el("rect", { x: M.x, y: M.y, width: M.l, height: M.h, fill: BLEU, "fill-opacity": milieu === 2 ? 0.2 : 0.06, stroke: GRIS, "stroke-width": 2 });
      // Fronts de compression : aussi serres que les vagues de l'ecran, aussi epais que le son est fort,
      // et seulement sur la longueur du son.
      const lambda = M.l / PERIODES[cran - 1];
      const fin = M.x + 4 + (M.l - 8) * duree / 4;
      for (let x = M.x + 4; x <= fin; x += lambda) {
        el("path", {
          d: `M${x.toFixed(1)},${M.y + 8} Q${(x + 12).toFixed(1)},${M.y + M.h / 2} ${x.toFixed(1)},${M.y + M.h - 8}`,
          fill: "none", stroke: BLEU, "stroke-width": 1.5 + 0.7 * intensite,
        });
      }
    }
    if (avecMilieu) el("text", { x: M.x, y: 150, "font-size": 14, fill: ENCRE },
      milieu === 0 ? "vide : pas de son" : milieu === 1 ? "air : 340 m/s" : "eau : ≈ 1\u00a0500 m/s");

    // Oreille : entend ou n'entend pas.
    el("path", { d: "M296,64 C326,58 334,104 304,114 C298,116 296,110 300,106 C316,98 314,74 300,76", fill: "none", stroke: ENCRE, "stroke-width": 3, "stroke-linecap": "round" });
    if (entendu) {
      el("path", { d: "M298,128 l7,7 l13,-14", fill: "none", stroke: VERT, "stroke-width": 4, "stroke-linecap": "round" });
    } else {
      el("path", { d: "M299,122 l14,14 M313,122 l-14,14", stroke: ROUGE, "stroke-width": 4, "stroke-linecap": "round" });
    }
    el("text", { x: 330, y: 158, "font-size": 14, "text-anchor": "end", fill: entendu ? VERT : ROUGE }, entendu ? "entend" : "n'entend pas");

    // Ecran de l'oscilloscope : ce qui arrive a l'oreille.
    const E = { x: 20, y: 180, l: 300, h: 120 };
    const mi = E.y + E.h / 2;
    el("text", { x: E.x, y: E.y - 8, "font-size": 13, fill: GRIS }, "écran : le son reçu");
    el("rect", { x: E.x, y: E.y, width: E.l, height: E.h, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2 });
    for (let i = 1; i < 10; i++) el("line", { x1: E.x + i * 30, y1: E.y, x2: E.x + i * 30, y2: E.y + E.h, stroke: "#E3E7ED", "stroke-width": 1 });
    for (let j = 1; j < 4; j++) el("line", { x1: E.x, y1: E.y + j * 30, x2: E.x + E.l, y2: E.y + j * 30, stroke: "#E3E7ED", "stroke-width": 1 });
    const A = milieu === 0 ? 0 : 10 * intensite;
    // Le son s'arrete au bout d'une demi-vague entiere (la courbe revient sur l'axe, sans saut).
    const demi = E.l / (2 * PERIODES[cran - 1]);
    const longueur = duree === 4 ? E.l : Math.max(demi, Math.round((E.l * duree) / 4 / demi) * demi);
    const w = (2 * Math.PI * PERIODES[cran - 1]) / E.l;
    let d = `M${E.x},${mi}`;
    for (let x = 1; x < longueur; x++) d += ` L${E.x + x},${(mi - A * Math.sin(w * x)).toFixed(1)}`;
    d += ` L${(E.x + longueur).toFixed(1)},${mi}`;
    if (longueur < E.l) d += ` L${E.x + E.l},${mi}`; // apres le son : ligne plate
    el("path", { d, fill: "none", stroke: BLEU, "stroke-width": 2.5, "stroke-linejoin": "round" });
    if (A > 0 && avecIntensite) {
      // Hauteur des vagues (intensite) : fleche orange ; duree : accolade verte.
      // (a droite de l'ecran, hors des vagues, pour rester visible meme quand elles sont serrees)
      const xc = E.x + E.l + 10;
      el("line", { x1: xc, y1: mi, x2: xc, y2: mi - A + 6, stroke: ORANGE, "stroke-width": 3 });
      el("path", { d: `M${xc},${mi - A} l-5,8 l10,0 z`, fill: ORANGE });
      el("line", { x1: E.x + E.l, y1: mi - A, x2: xc + 5, y2: mi - A, stroke: ORANGE, "stroke-width": 2, "stroke-dasharray": "3 3" });
    }
    if (avecDuree) {
      el("line", { x1: E.x, y1: E.y + E.h + 14, x2: E.x + longueur, y2: E.y + E.h + 14, stroke: VERT, "stroke-width": 3 });
      el("line", { x1: E.x, y1: E.y + E.h + 8, x2: E.x, y2: E.y + E.h + 20, stroke: VERT, "stroke-width": 3 });
      el("line", { x1: E.x + longueur, y1: E.y + E.h + 8, x2: E.x + longueur, y2: E.y + E.h + 20, stroke: VERT, "stroke-width": 3 });
      el("text", { x: E.x + longueur / 2, y: E.y + E.h + 34, "font-size": 13, "text-anchor": "middle", fill: VERT }, "durée du son");
    }
    return { f, audible, entendu, milieu };
  },
};
