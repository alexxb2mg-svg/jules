// Jules - gabarit "matrice-risque" : grille alea x vulnerabilite, coloriee du gris (risque nul) au rouge (risque
// fort), avec un point qui se deplace. Le risque n'est fort que si les deux sont hauts ; si l'un des deux est nul,
// le risque est nul.
// Curseurs : alea (0 nul a 3 fort : intensite et probabilite du phenomene), vuln (0 rien d'expose a 3 tres expose).
// Niveau de chaque case (produit alea x vuln, ordre de grandeur et non vrai calcul, comme la formule de la fiche) :
// 0 nul (gris), 1-2 faible (vert), 3 moyen (orange), 4 et plus fort (rouge). Aucun mot de niveau n'est ecrit pres
// du point : la couleur de la case se lit dans la legende.
// Faits verifies (EX-205) : ministere de la Transition ecologique, « Prevention des risques majeurs »
// (ecologie.gouv.fr/politiques-publiques/prevention-risques-majeurs) : « Le risque majeur est donc la confrontation
// d'un alea avec des enjeux » (sans enjeu expose, pas de risque) ; la prevention vise a reduire la vulnerabilite.
// Programme de SVT cycle 4 (Eduscol, annexe 3, arrete du 17-7-2020) : alea, vulnerabilite, risque, prevention.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["matrice-risque"] = {
  dessiner(svg, valeurs) {
    const alea = Math.min(3, Math.max(0, Math.round(Number(valeurs.alea ?? 2))));
    const vuln = Math.min(3, Math.max(0, Math.round(Number(valeurs.vuln ?? 2))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 320");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const NIVEAUX = [
      { nom: "nul", couleur: "#C9CED6" },
      { nom: "faible", couleur: "#2E7D32" },
      { nom: "moyen", couleur: "#E07B00" },
      { nom: "fort", couleur: "#C8102E" },
    ];
    const niveau = (a, b) => {
      const p = a * b;
      if (p === 0) return 0;
      if (p <= 2) return 1;
      if (p === 3) return 2;
      return 3;
    };

    // Grille 4 x 4 : alea en abscisse, vulnerabilite en ordonnee (0 en bas).
    const X0 = 96, Y0 = 250, C = 56;
    for (let a = 0; a <= 3; a++) {
      for (let b = 0; b <= 3; b++) {
        const n = niveau(a, b);
        el("rect", {
          x: X0 + a * C, y: Y0 - (b + 1) * C, width: C, height: C,
          fill: NIVEAUX[n].couleur, "fill-opacity": n === 0 ? 0.5 : 0.35, stroke: "#FFFFFF", "stroke-width": 2,
        });
      }
    }
    // Axes et graduations.
    el("line", { x1: X0, y1: Y0, x2: X0 + 4 * C, y2: Y0, stroke: "#14243B", "stroke-width": 2 });
    el("line", { x1: X0, y1: Y0, x2: X0, y2: Y0 - 4 * C, stroke: "#14243B", "stroke-width": 2 });
    for (let i = 0; i <= 3; i++) {
      el("text", { x: X0 + i * C + C / 2, y: Y0 + 18, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, String(i));
      el("text", { x: X0 - 8, y: Y0 - i * C - C / 2 + 5, "font-size": 13, "text-anchor": "end", fill: "#14243B" }, String(i));
    }
    el("text", { x: X0 + 2 * C, y: Y0 + 38, "font-size": 14, "text-anchor": "middle", fill: "#E07B00", "font-weight": "bold" }, "aléa (le phénomène) →");
    // Titre de l'axe vertical sur une seule ligne, au-dessus de la grille (haut de grille : Y0 - 4C = 26).
    const titreV = el("text", { x: 8, y: 16, "font-size": 14, fill: "#1F4E8C", "font-weight": "bold" }, "↑ vulnérabilité ");
    const sousTitreV = document.createElementNS(NS, "tspan");
    sousTitreV.setAttribute("font-weight", "normal");
    sousTitreV.setAttribute("font-size", 13);
    sousTitreV.textContent = "(ce qui est exposé)";
    titreV.appendChild(sousTitreV);

    // Point de la situation choisie.
    const px = X0 + alea * C + C / 2, py = Y0 - vuln * C - C / 2;
    el("circle", { cx: px, cy: py, r: 15, fill: "#14243B", stroke: "#FFFFFF", "stroke-width": 3 });

    // Legende des couleurs (a lire, rien d'ecrit pres du point).
    el("text", { x: 8, y: 312, "font-size": 13, fill: "#14243B" }, "risque :");
    let x = 64;
    for (const n of NIVEAUX) {
      el("rect", { x, y: 300, width: 14, height: 14, fill: n.couleur, "fill-opacity": n.nom === "nul" ? 0.5 : 0.6 });
      el("text", { x: x + 18, y: 312, "font-size": 13, fill: "#14243B" }, n.nom);
      x += 18 + n.nom.length * 7.5 + 12;
    }
    return { alea, vuln, niveau: NIVEAUX[niveau(alea, vuln)].nom };
  },
};
