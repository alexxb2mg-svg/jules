// Jules - gabarit "barre-evolution" : deux evolutions successives en pourcentage, a partir d'une valeur 100.
// Trois barres a la meme echelle : depart (100), apres une evolution de p %, puis apres une evolution de q %.
// Sur chaque fleche, le coefficient multiplicateur CM = 1 + t / 100 ; au bout de chaque barre, sa valeur. Un trait
// pointille marque 100 sur les trois lignes : +20 % puis -20 % finit a 96, plus court que le depart.
// Barre verte = la valeur a augmente, rouge = elle a baisse, bleue = depart ou valeur inchangee.
// La figure ECRIT les coefficients et les valeurs (revele: true) : c'est la lecture la plus claire pour le piege
// « +20 % puis -20 % », une version sans nombres serait illisible (4 % = 5 px).
// Faits : hausse de t % : CM = 1 + t/100 ; baisse de t % : CM = 1 - t/100 ; evolutions successives : on multiplie
// les CM (1,2 × 0,8 = 0,96). Programme de mathematiques du cycle 4, BO n° 31 du 30/07/2020 (« proportionnalite :
// pourcentages d'evolution ») ; attendus de fin de 3e, eduscol 2019.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["barre-evolution"] = {
  dessiner(svg, valeurs) {
    const borne = (v, defaut) => {
      const n = Number(v ?? defaut);
      return Math.min(50, Math.max(-50, Math.round(Number.isFinite(n) ? n : defaut)));
    };
    const p = borne(valeurs.p, 20);
    const q = borne(valeurs.q, 0);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    // Nombre a la francaise : au plus 4 decimales, zeros inutiles retires, virgule ; pas de -0.
    const fr = (x) => {
      const r = Math.round(x * 10000) / 10000;
      return String(r === 0 ? 0 : r).replace(".", ",").replace("-", "−");
    };
    const X0 = 20, ECHELLE = 300 / 225; // 225 = 100 × 1,5 × 1,5, la plus grande valeur possible
    const cm1 = 1 + p / 100, cm2 = 1 + q / 100;
    const v0 = 100, v1 = v0 * cm1, v2 = v1 * cm2;
    svg.setAttribute("viewBox", "0 0 340 250");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const couleur = (avant, apres) => (Math.abs(apres - avant) < 1e-9 ? BLEU : apres > avant ? VERT : ROUGE);
    const ligne = (y, titre, valeur, teinte) => {
      el("text", { x: X0, y: y - 8, "font-size": 14, "text-anchor": "start", fill: GRIS }, titre);
      const w = valeur * ECHELLE;
      el("rect", { x: X0, y, width: w, height: 34, fill: teinte });
      const texte = fr(valeur);
      if (w >= 70) {
        el("text", { x: X0 + w - 8, y: y + 23, "font-size": 17, "font-weight": 700, "text-anchor": "end", fill: "#FFFFFF" }, texte);
      } else {
        el("text", { x: X0 + w + 6, y: y + 23, "font-size": 17, "font-weight": 700, "text-anchor": "start", fill: teinte }, texte);
      }
    };
    const fleche = (y1, y2, cm, t) => {
      const x = 300;
      el("line", { x1: x, y1, x2: x, y2: y2 - 8, stroke: ORANGE, "stroke-width": 3 });
      el("polygon", { points: `${x - 6},${y2 - 10} ${x + 6},${y2 - 10} ${x},${y2}`, fill: ORANGE });
      const signe = t > 0 ? "+" : t < 0 ? "−" : "";
      el("text", { x: x - 10, y: (y1 + y2) / 2 + 1, "font-size": 15, "font-weight": 700, "text-anchor": "end", fill: ORANGE }, `${signe}${Math.abs(t)} %  :  × ${fr(cm)}`);
    };

    // Repere 100 : trois segments pointilles, un par barre, limites a la hauteur de la barre (y a y + 34), dessines
    // AVANT les barres (caches dans une barre plus longue, visibles au bout d'une barre plus courte). Ils ne
    // traversent ni les titres au-dessus des barres ni les valeurs ecrites.
    const x100 = X0 + 100 * ECHELLE;
    for (const y of [30, 122, 214]) {
      el("line", { x1: x100, y1: y, x2: x100, y2: y + 34, stroke: ENCRE, "stroke-width": 2, "stroke-dasharray": "5 4" });
    }
    ligne(30, "départ", v0, BLEU);
    fleche(70, 112, cm1, p);
    ligne(122, "après la 1re évolution", v1, couleur(v0, v1));
    fleche(160, 204, cm2, q);
    ligne(214, "après la 2e évolution", v2, couleur(v1, v2));
    return { p, q, cm1, cm2, v1, v2 };
  },
};
