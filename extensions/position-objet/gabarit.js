// Jules - gabarit "position-objet" : un chat et une boite ; deux curseurs deplacent le chat (place : a gauche,
// au niveau de la boite, a droite ; hauteur, quand il est au niveau de la boite :
// dessous, dedans, dessus). La figure n'ecrit pas le mot de lieu
// (in, on, under, next to) : c'est l'eleve qui le trouve, les lectures de la fiche le confirment.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["position-objet"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", ORANGE = "#E07B00";
    const n = (cle, defaut) => {
      const v = Number(valeurs[cle]);
      return Math.min(1, Math.max(-1, Math.round(Number.isFinite(v) ? v : defaut)));
    };
    const cote = n("place", valeurs.place ?? 0), hauteur = n("hauteur", valeurs.hauteur ?? 1);
    const el = (nom, attrs, parent) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      (parent || svg).appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // la boite : de x 115 a 225, de y 140 a 212 ; le fond (interieur) d'abord, la face avant ensuite
    const boiteFond = () => {
      el("polygon", { points: "115,140 135,122 245,122 225,140", fill: "#C9D6EA", stroke: BLEU, "stroke-width": 3, "stroke-linejoin": "round" });
      el("polygon", { points: "225,140 245,122 245,194 225,212", fill: "#D7E1F0", stroke: BLEU, "stroke-width": 3, "stroke-linejoin": "round" });
    };
    const boiteFace = () => {
      el("rect", { x: 115, y: 140, width: 110, height: 72, fill: "#E8EEF7", stroke: BLEU, "stroke-width": 3 });
      const t = el("text", { x: 170, y: 201, "font-size": 15, fill: BLEU, "text-anchor": "middle", "font-weight": 700,
        "font-family": "system-ui, Arial, sans-serif" });
      t.textContent = "the box";
    };
    // le chat, pose sur ses pattes au point (x, y)
    const chat = (x, y) => {
      const g = el("g", { transform: `translate(${x},${y})` });
      el("path", { d: "M22,-14 C44,-16 46,-44 34,-56", fill: "none", stroke: ORANGE, "stroke-width": 6, "stroke-linecap": "round" }, g);
      el("ellipse", { cx: 0, cy: -18, rx: 25, ry: 18, fill: ORANGE, stroke: ENCRE, "stroke-width": 2 }, g);
      el("polygon", { points: "-15,-54 -12,-74 -2,-60", fill: ORANGE, stroke: ENCRE, "stroke-width": 2, "stroke-linejoin": "round" }, g);
      el("polygon", { points: "15,-54 12,-74 2,-60", fill: ORANGE, stroke: ENCRE, "stroke-width": 2, "stroke-linejoin": "round" }, g);
      el("circle", { cx: 0, cy: -46, r: 16, fill: ORANGE, stroke: ENCRE, "stroke-width": 2 }, g);
      el("circle", { cx: -6, cy: -49, r: 2.5, fill: ENCRE }, g);
      el("circle", { cx: 6, cy: -49, r: 2.5, fill: ENCRE }, g);
      el("path", { d: "M-4,-41 Q0,-38 4,-41", fill: "none", stroke: ENCRE, "stroke-width": 2, "stroke-linecap": "round" }, g);
    };

    boiteFond();
    if (cote !== 0) {
      // a cote de la boite, a gauche ou a droite, au niveau du bas de la boite (la hauteur ne compte plus : « next to »)
      boiteFace();
      chat(cote < 0 ? 62 : 284, 212);
    } else if (hauteur === 0) {
      chat(170, 170); // dedans : la face avant cache le corps, la tete depasse
      boiteFace();
    } else if (hauteur > 0) {
      boiteFace();
      chat(170, 132); // dessus : pose sur le couvercle
    } else {
      boiteFace();
      chat(170, 294); // dessous
    }
    return { place: cote, hauteur };
  },
};
