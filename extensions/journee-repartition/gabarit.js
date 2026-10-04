// Jules - gabarit "journee-repartition" : la journee d'un enfant en 24 cases (1 case = 1 heure, demi-case = une
// demi-heure). Quand le point d'eau s'eloigne (« distance », en km) ou que les allers-retours se multiplient
// (« trajets »), la corvee d'eau (orange) grandit : elle mange d'abord le temps libre (vert), puis l'ecole (bleu).
// La figure n'ecrit aucune duree : l'eleve compte les cases (revele: false).
// Hypotheses (modele, pas une mesure) :
//   - marche a 4 km/h (vitesse courante a pied ; plus lent en portant l'eau, non compte) : un aller-retour de
//     d km dure 2 d / 4 = d / 2 heures ; duree arrondie a la demi-heure ; distance 0 = robinet a la maison ;
//   - sommeil 10 h (recommandation de 9 a 12 h pour un enfant de 6 a 12 ans, consensus de l'American Academy of
//     Sleep Medicine, 2016), repas et toilette 2 h, ecole 6 h (journee d'ecole primaire en France) :
//     reste 6 h de temps libre quand l'eau est au robinet.
// Reperes (OMS-UNICEF, programme commun JMP) : un point d'eau a plus de 30 minutes aller-retour = service
// « limite » ; 292 millions de personnes dans ce cas en 2022 ; dans 7 foyers sur 10 sans eau courante, ce sont les
// femmes et les filles qui vont chercher l'eau (UNICEF-OMS, 2023).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["journee-repartition"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const BLEU = "#1F4E8C", GRIS = "#6B7686", ENCRE = "#14243B", VERT = "#2E7D32", ORANGE = "#E07B00";
    const CLAIR = "#D5DAE1";
    const nombre = (v, d) => (Number.isFinite(Number(v)) ? Number(v) : d);
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };

    const distance = Math.min(5, Math.max(0, nombre(valeurs.distance, 0)));
    const trajets = Math.round(Math.min(3, Math.max(1, nombre(valeurs.trajets, 1))));
    // En demi-heures : eau = trajets x (d / 2 h) = trajets x d demi-heures.
    const eau = Math.round(trajets * distance);
    const libre = Math.max(0, 12 - eau);
    const ecole = 12 - Math.max(0, eau - 12);
    const PARTS = [
      ["sommeil", GRIS, 20],
      ["repas, toilette", CLAIR, 4],
      ["école", BLEU, ecole],
      ["chercher l'eau", ORANGE, eau],
      ["temps libre", VERT, libre],
    ];

    // --- mise en page : 4 rangees de 6 heures ---------------------------------------------------------------
    const H = 330;
    svg.setAttribute("viewBox", `0 0 340 ${H}`);
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const COTE = 44, PAS = 50, X0 = 20, Y0 = 46;
    el("text", { x: 170, y: 22, "font-size": 15, "text-anchor": "middle", fill: ENCRE, "font-weight": 700 }, "Une journée : 1 case = 1 heure");

    // Remplissage demi-heure par demi-heure, dans l'ordre des parts.
    const demi = [];
    for (const [nom, couleur, n] of PARTS) for (let k = 0; k < n; k++) demi.push([nom, couleur]);
    for (let h = 0; h < 24; h++) {
      const col = h % 6, lig = Math.floor(h / 6);
      const x = X0 + col * PAS, y = Y0 + lig * PAS;
      const [, c1] = demi[2 * h], [, c2] = demi[2 * h + 1];
      el("rect", { x, y, width: COTE / 2, height: COTE, fill: c1 });
      el("rect", { x: x + COTE / 2, y, width: COTE / 2, height: COTE, fill: c2 });
      el("rect", { x, y, width: COTE, height: COTE, rx: 3, fill: "none", stroke: ENCRE, "stroke-width": 2 });
    }

    // Legende : couleur et nom (sans nombre) ; une part a zero est barree.
    const YL = Y0 + 4 * PAS + 14;
    PARTS.forEach(([nom, couleur, n], i) => {
      const col = i % 2, lig = Math.floor(i / 2);
      const x = 12 + col * 166, y = YL + lig * 24;
      el("rect", { x, y, width: 18, height: 18, rx: 3, fill: couleur, stroke: ENCRE, "stroke-width": 1 });
      const t = el("text", { x: x + 25, y: y + 14, "font-size": 14, fill: n === 0 ? GRIS : ENCRE, "font-weight": nom === "chercher l'eau" ? 700 : 400 }, nom);
      if (n === 0) t.setAttribute("text-decoration", "line-through");
    });
    return { distance, trajets, eau_demi_heures: eau, libre_demi_heures: libre, ecole_demi_heures: ecole };
  },
};
