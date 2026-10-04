// Jules - gabarit "nombre-binaire" : une rangee de 8 ampoules (les bits) avec leur poids 128, 64, 32, 16, 8, 4, 2, 1.
// Curseurs : valeur (entier de 0 a 255 a ecrire en binaire), bits (nombre de bits disponibles, de 1 a 8).
// Les cases a gauche des bits disponibles sont grisees (« pas de place ») ; si le nombre a besoin d'un bit qui manque,
// l'ampoule correspondante est dessinee en rouge et la figure dit qu'il faut plus de bits.
// Faits : ecriture en base 2, poids 2^k ; avec n bits on code N = 2^n valeurs, de 0 a 2^n - 1 ; 8 bits = 1 octet,
// 256 valeurs de 0 a 255 (programme de technologie du cycle 4, theme « l'informatique et la programmation » ;
// formule N = 2ⁿ de la fiche « structurer et traiter des donnees »). Tous les nombres ecrits sont recalcules.
// La figure ECRIT l'ecriture binaire et la somme des poids : c'est la reponse d'un exercice de conversion, revele true.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["nombre-binaire"] = {
  dessiner(svg, valeurs) {
    const valeur = Math.min(255, Math.max(0, Math.round(Number(valeurs.valeur ?? 5))));
    const bits = Math.min(8, Math.max(1, Math.round(Number(valeurs.bits ?? 8))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 290");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const ENCRE = "#14243B", GRIS = "#6B7686", BLEU = "#1F4E8C", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";

    const capacite = 2 ** bits; // nombre de valeurs codables
    const tient = valeur < capacite;
    const PAS = 40, X0 = 30; // ampoule i (0 = poids 128) en X0 + i * PAS
    const YA = 100;

    // Zone des bits disponibles (a droite) : cadre bleu ; a gauche, cases grisees.
    const debut = 8 - bits;
    el("rect", {
      x: X0 + debut * PAS - 18, y: 30, width: bits * PAS - 4, height: 128, rx: 8,
      fill: "#E6EEF8", stroke: BLEU, "stroke-width": 2,
    });
    if (debut > 0) {
      el("rect", {
        x: X0 - 18, y: 30, width: debut * PAS - 4, height: 128, rx: 8,
        fill: "#F1F2F4", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "5 4",
      });
    }
    el("text", { x: 10, y: 20, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, "poids");
    el("text", { x: 330, y: 20, "font-size": 14, "text-anchor": "end", fill: BLEU, "font-weight": "bold" },
      `${bits} bit${bits > 1 ? "s" : ""} disponible${bits > 1 ? "s" : ""}`);

    const allumes = [];
    for (let i = 0; i < 8; i++) {
      const poids = 2 ** (7 - i);
      const x = X0 + i * PAS;
      const dispo = i >= debut;
      const un = (valeur & poids) !== 0;
      if (un) allumes.push(poids);
      el("text", { x, y: 55, "font-size": 14, "text-anchor": "middle", fill: dispo ? ENCRE : GRIS }, String(poids));
      // ampoule : allumee (jaune) si le bit vaut 1 ; rouge si le bit vaut 1 mais n'est pas disponible
      const manque = un && !dispo;
      if (un && dispo) {
        for (let k = 0; k < 6; k++) {
          const a = (k * Math.PI) / 3 + Math.PI / 6;
          el("line", {
            x1: x + 17 * Math.cos(a), y1: YA + 17 * Math.sin(a), x2: x + 22 * Math.cos(a), y2: YA + 22 * Math.sin(a),
            stroke: ORANGE, "stroke-width": 2, "stroke-linecap": "round",
          });
        }
      }
      el("circle", {
        cx: x, cy: YA, r: 13,
        fill: manque ? "#F8E1E4" : un ? "#FFC94D" : "#FFFFFF",
        stroke: manque ? ROUGE : un ? ORANGE : GRIS, "stroke-width": manque || un ? 3 : 2,
        "stroke-dasharray": dispo || manque ? "none" : "4 3",
      });
      el("text", {
        x, y: 145, "font-size": 18, "text-anchor": "middle", "font-weight": "bold",
        fill: manque ? ROUGE : !dispo ? GRIS : un ? ORANGE : ENCRE,
      }, dispo || un ? (un ? "1" : "0") : "·");
    }

    // Somme des poids allumes : le nombre se relit en additionnant.
    const somme = allumes.length ? allumes.join(" + ") : "0";
    el("text", { x: 170, y: 190, "font-size": somme.length > 26 ? 14 : 16, "text-anchor": "middle", fill: ENCRE },
      `${somme} = ${valeur}`);

    // Capacite : N = 2^n valeurs, de 0 a 2^n - 1.
    el("text", { x: 170, y: 222, "font-size": 14, "text-anchor": "middle", fill: BLEU },
      `${bits} bit${bits > 1 ? "s" : ""} : ${capacite} valeurs, de 0 à ${capacite - 1}`);
    if (tient) {
      el("text", { x: 170, y: 256, "font-size": 15, "text-anchor": "middle", fill: VERT, "font-weight": "bold" },
        `${valeur} tient sur ${bits} bit${bits > 1 ? "s" : ""}`);
    } else {
      const besoin = Math.floor(Math.log2(valeur)) + 1;
      el("text", { x: 170, y: 256, "font-size": 15, "text-anchor": "middle", fill: ROUGE, "font-weight": "bold" },
        `trop grand : il faut ${besoin} bits`);
    }
    if (bits === 8) {
      el("text", { x: 170, y: 280, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "8 bits = 1 octet");
    }
    return { valeur, bits, tient: tient ? 1 : 0 };
  },
};
