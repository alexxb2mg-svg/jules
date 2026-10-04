// Jules - gabarit "reseau-routage" : le trajet d'un paquet de l'ordinateur au serveur. Reseau local (ordinateur,
// commutateur, box) puis Internet (routeurs maillés) jusqu'au serveur ; le paquet avance d'un saut par cran du curseur
// etape (0 = ordinateur, 6 = serveur). Le curseur coupure met une liaison en panne (0 = aucune ; 1 = R1-R2 ;
// 2 = box-R1 ; 3 = R2-R5) : le chemin se redessine par une autre route de meme longueur.
// Faits : dans un reseau local le commutateur relie les appareils et transmet le paquet vers la box (passerelle) ; un
// routeur lit l'adresse IP de destination et choisit le saut suivant dans sa table de routage ; s'il existe plusieurs
// chemins, une panne est contournee (Wikipedia, articles « Commutateur reseau », « Routeur » et « Routage » ; programme
// de technologie du cycle 4, theme « l'informatique et la programmation »). L'adresse ecrite, 203.0.113.10, est
// prise dans le bloc reserve a la documentation (RFC 5737, 203.0.113.0/24) : elle n'appartient a personne.
// Aucun calcul a trouver : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["reseau-routage"] = {
  dessiner(svg, valeurs) {
    const etape = Math.min(6, Math.max(0, Math.round(Number(valeurs.etape ?? 0))));
    const coupure = Math.min(3, Math.max(0, Math.round(Number(valeurs.coupure ?? 0))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 330");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const ENCRE = "#14243B", GRIS = "#6B7686", BLEU = "#1F4E8C", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";

    // --- Noeuds ---
    const N = {
      pc: { x: 46, y: 50 }, sw: { x: 162, y: 50 }, box: { x: 286, y: 50 },
      r1: { x: 236, y: 150 }, r3: { x: 296, y: 250 },
      r2: { x: 146, y: 150 }, r4: { x: 196, y: 250 },
      r5: { x: 70, y: 210 }, srv: { x: 70, y: 296 },
    };
    // Liaisons (cle = deux noeuds tries) ; coupures 1 a 3.
    const LIENS = [["pc", "sw"], ["sw", "box"], ["box", "r1"], ["box", "r3"], ["r1", "r2"], ["r3", "r4"], ["r1", "r4"],
      ["r2", "r5"], ["r4", "r5"], ["r5", "srv"]];
    const COUPEE = [null, "r1-r2", "box-r1", "r2-r5"][coupure];
    const cle = (a, b) => [a, b].sort().join("-");
    // Routes possibles, toutes de meme longueur, dans l'ordre de preference : la premiere sans liaison coupee gagne.
    const ROUTES = [["r1", "r2"], ["r1", "r4"], ["r3", "r4"]];
    const milieu = ROUTES.find((r) => ![cle("box", r[0]), cle(r[0], r[1]), cle(r[1], "r5")].includes(COUPEE));
    const chemin = ["pc", "sw", "box", milieu[0], milieu[1], "r5", "srv"];
    const surChemin = new Map();
    for (let i = 0; i + 1 < chemin.length; i++) surChemin.set(cle(chemin[i], chemin[i + 1]), i);

    // --- Deux zones : reseau local, Internet ---
    el("rect", { x: 4, y: 4, width: 332, height: 84, rx: 10, fill: "#F4F7FB", stroke: GRIS, "stroke-width": 2 });
    el("text", { x: 12, y: 84, "font-size": 13, fill: GRIS }, "réseau local");
    el("rect", { x: 4, y: 100, width: 332, height: 226, rx: 10, fill: "#FFFFFF", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "6 4" });
    el("text", { x: 12, y: 120, "font-size": 13, fill: GRIS }, "Internet"); // a gauche : la liaison box-R3 passe a droite

    // --- Liaisons : parcourue (vert), a venir sur la route (bleu), autres (gris), coupee (rouge) ---
    for (const [a, b] of LIENS) {
      const k = cle(a, b), A = N[a], B = N[b];
      const rang = surChemin.get(k);
      let couleur = GRIS, epaisseur = 2, tirets = "none";
      if (k === COUPEE) { couleur = ROUGE; epaisseur = 3; tirets = "6 5"; }
      else if (rang !== undefined && rang < etape) { couleur = VERT; epaisseur = 5; }
      else if (rang !== undefined) { couleur = BLEU; epaisseur = 4; }
      el("line", { x1: A.x, y1: A.y, x2: B.x, y2: B.y, stroke: couleur, "stroke-width": epaisseur, "stroke-dasharray": tirets });
      if (k === COUPEE) {
        const mx = (A.x + B.x) / 2, my = (A.y + B.y) / 2;
        el("circle", { cx: mx, cy: my, r: 11, fill: "#FFFFFF", stroke: ROUGE, "stroke-width": 3 });
        el("line", { x1: mx - 5, y1: my - 5, x2: mx + 5, y2: my + 5, stroke: ROUGE, "stroke-width": 3 });
        el("line", { x1: mx - 5, y1: my + 5, x2: mx + 5, y2: my - 5, stroke: ROUGE, "stroke-width": 3 });
      }
    }

    // --- Appareils (rectangles) et routeurs (ronds) ---
    const boite = (n, largeur, texte) => {
      const p = N[n];
      el("rect", { x: p.x - largeur / 2, y: p.y - 17, width: largeur, height: 34, rx: 6, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 2 });
      el("text", { x: p.x, y: p.y + 5, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, texte);
    };
    boite("pc", 80, "ordinateur");
    boite("sw", 98, "commutateur");
    boite("box", 56, "box");
    boite("srv", 70, "serveur");
    el("text", { x: 112, y: 294, "font-size": 13, fill: ENCRE }, "IP de destination :");
    el("text", { x: 112, y: 312, "font-size": 13, fill: ENCRE, "font-weight": "bold" }, "203.0.113.10");
    for (const [n, nom] of [["r1", "R1"], ["r2", "R2"], ["r3", "R3"], ["r4", "R4"], ["r5", "R5"]]) {
      const p = N[n];
      el("circle", { cx: p.x, cy: p.y, r: 17, fill: "#E6EEF8", stroke: BLEU, "stroke-width": 2 });
      el("text", { x: p.x, y: p.y + 5, "font-size": 14, "text-anchor": "middle", fill: BLEU, "font-weight": "bold" }, nom);
    }
    el("text", { x: 248, y: 205, "font-size": 13, fill: BLEU }, "routeurs");

    // --- Le paquet : une enveloppe orange posee sur le noeud atteint ---
    const P = N[chemin[etape]];
    const ex = P.x - 15, ey = P.y - 42;
    el("rect", { x: ex, y: ey, width: 30, height: 20, rx: 2, fill: "#FCEBD6", stroke: ORANGE, "stroke-width": 3 });
    el("path", { d: `M${ex},${ey} L${ex + 15},${ey + 11} L${ex + 30},${ey}`, fill: "none", stroke: ORANGE, "stroke-width": 2 });
    return { etape, coupure, route: ROUTES.indexOf(milieu) };
  },
};
