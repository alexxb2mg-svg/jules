// Jules - gabarit "diagramme-gantt" : le planning (diagramme de Gantt) d'un projet technique de 5 taches sur
// 10 semaines prevues. Curseur semaine : la ligne « aujourd'hui » avance, chaque tache est terminee (vert),
// en cours (orange) ou a venir (gris). Curseur retard (0 a 3 semaines) : la conception dure plus longtemps
// (semaines en rouge), et les taches qui l'attendent (fabrication, puis tests) glissent d'autant ; leur place
// prevue reste en pointilles. La programmation, qui n'attend que le cahier des charges, ne bouge pas.
// La fin prevue (semaine 10) est un trait en pointilles ; la date de fin reelle n'est pas ecrite, elle se lit
// sur l'axe (revele false).
// Planning (taches fictives, dependances fin -> debut) : cahier des charges S1-S2 ; conception S3-S5 (+ retard) ;
// fabrication 3 semaines apres la conception ; programmation S3-S6, en parallele ; tests et presentation
// 2 semaines apres la fabrication et la programmation. Fin = semaine 10 + retard.
// Faits (EX-205) : vocabulaire du programme (tache, duree, dependance, taches en parallele, jalon, revue de
// projet) : programme de technologie du cycle 4 (BO n° 31 du 30/07/2020, « Projet : organisation, planification,
// diagramme de Gantt ») et fiche gestion-projet-technique ; Wikipedia, « Diagramme de Gantt ».
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["diagramme-gantt"] = {
  // dessiner(svg, valeurs) : semaine de 1 a 13, retard de 0 a 3 (entiers).
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => {
      const n = Number(v ?? d);
      return Math.min(maxi, Math.max(mini, Math.round(Number.isFinite(n) ? n : d)));
    };
    const semaine = ent(valeurs.semaine, 3, 1, 13);
    const retard = ent(valeurs.retard, 0, 0, 3);
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (n) => n.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 330");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    // Les taches : debut et fin (semaines incluses), et debut prevu (sans retard).
    const cahier = { nom: "Cahier des charges", debut: 1, fin: 2 };
    const conception = { nom: "Conception", debut: 3, fin: 5 + retard, finPrevue: 5 };
    const fabrication = { nom: "Fabrication", debut: conception.fin + 1, fin: conception.fin + 3, prevu: 6 };
    const programmation = { nom: "Programmation", debut: 3, fin: 6 };
    const debutTests = Math.max(fabrication.fin, programmation.fin) + 1;
    const tests = { nom: "Tests et présentation", debut: debutTests, fin: debutTests + 1, prevu: 9 };
    const taches = [cahier, conception, fabrication, programmation, tests];

    // Axe : 13 semaines, 23 px chacune, de x = 18 a x = 317.
    const X0 = 18, W = 23, NB = 13;
    const X = (s) => X0 + (s - 1) * W; // bord gauche de la semaine s
    const HAUT = 46, RANG = 40;
    const yBarre = (i) => HAUT + i * RANG + 20;

    // Numeros de semaine ; la semaine actuelle dans une pastille bleue.
    el("text", { x: X0, y: 14, "font-size": 13, fill: GRIS, "font-family": "sans-serif" }, "semaines");
    for (let s = 1; s <= NB; s++) {
      const cx = X(s) + W / 2;
      if (s === semaine) el("circle", { cx: f(cx), cy: 31, r: 11, fill: BLEU });
      el("text", { x: f(cx), y: 36, "font-size": 13, "font-weight": s === semaine ? "bold" : "normal", fill: s === semaine ? "#FFFFFF" : ENCRE, "text-anchor": "middle", "font-family": "sans-serif" }, String(s));
    }
    // Quadrillage leger des semaines.
    for (let s = 1; s <= NB + 1; s++) {
      el("line", { x1: X(s), y1: HAUT, x2: X(s), y2: HAUT + 5 * RANG, stroke: "#EDF0F4", "stroke-width": 2 });
    }

    // Place prevue des taches decalees par le retard (pointilles gris).
    if (retard > 0) {
      for (const [i, t] of [[2, fabrication], [4, tests]]) {
        const duree = t.fin - t.debut + 1;
        el("rect", { x: f(X(t.prevu) + 1), y: yBarre(i), width: f(duree * W - 2), height: 14, rx: 3, fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "4 3" });
      }
    }

    // Les barres : couleur selon l'etat a la semaine choisie ; les semaines de retard de la conception en rouge.
    const etat = (t) => (t.fin < semaine ? "terminee" : t.debut <= semaine ? "encours" : "avenir");
    const COUL = { terminee: [VERT, "#BFE0C1"], encours: [ORANGE, "#F6C58C"], avenir: [GRIS, "#E1E5EB"] };
    taches.forEach((t, i) => {
      const [trait, fond] = COUL[etat(t)];
      el("rect", { x: f(X(t.debut) + 1), y: yBarre(i), width: f((t.fin - t.debut + 1) * W - 2), height: 14, rx: 3, fill: fond, stroke: trait, "stroke-width": 2 });
      if (t === conception && retard > 0) {
        el("rect", { x: f(X(t.finPrevue + 1) + 1), y: yBarre(i) + 2, width: f(retard * W - 3), height: 10, fill: ROUGE });
      }
    });

    // Dependances (fin -> debut) : petites fleches grises (cahier -> conception, voisines, sans fleche : elle
    // couperait le nom « Conception »).
    const fleche = (x, y1, y2) => {
      el("line", { x1: f(x), y1: f(y1), x2: f(x), y2: f(y2 - 4), stroke: GRIS, "stroke-width": 2 });
      el("path", { d: `M ${f(x - 4)} ${f(y2 - 6)} L ${f(x + 4)} ${f(y2 - 6)} L ${f(x)} ${f(y2)} Z`, fill: GRIS });
    };
    fleche(X(fabrication.debut) + 4, yBarre(1) + 14, yBarre(2));
    fleche(X(tests.debut) + 4, yBarre(2) + 14, yBarre(4));
    // programmation -> tests : trait horizontal depuis la fin de la programmation, puis fleche.
    el("line", { x1: f(X(programmation.fin + 1)), y1: yBarre(3) + 7, x2: f(X(tests.debut) + 12), y2: yBarre(3) + 7, stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "4 3" });
    fleche(X(tests.debut) + 12, yBarre(3) + 7, yBarre(4));

    // Fin prevue (fin de la semaine 10) et ligne « aujourd'hui » (milieu de la semaine choisie).
    el("line", { x1: X(11), y1: HAUT - 2, x2: X(11), y2: HAUT + 5 * RANG + 6, stroke: ENCRE, "stroke-width": 2, "stroke-dasharray": "6 4" });
    const xJour = X(semaine) + W / 2;
    el("line", { x1: f(xJour), y1: 42, x2: f(xJour), y2: HAUT + 5 * RANG + 6, stroke: BLEU, "stroke-width": 3 });

    // Les noms des taches, au-dessus de leur barre, dessines apres les traits verticaux, avec un lisere blanc pour
    // rester lisibles quand la ligne « aujourd'hui » les traverse.
    taches.forEach((t, i) => {
      el("text", { x: X0, y: yBarre(i) - 5, "font-size": 13, fill: ENCRE, stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke", "stroke-linejoin": "round", "font-family": "sans-serif" }, t.nom);
    });

    // Legende.
    const yL = HAUT + 5 * RANG + 30;
    [[VERT, "#BFE0C1", "terminée", 18], [ORANGE, "#F6C58C", "en cours", 118], [GRIS, "#E1E5EB", "à venir", 218]].forEach(([t, fd, nom, x]) => {
      el("rect", { x, y: yL - 11, width: 22, height: 12, rx: 3, fill: fd, stroke: t, "stroke-width": 2 });
      el("text", { x: x + 28, y: yL, "font-size": 13, fill: ENCRE, "font-family": "sans-serif" }, nom);
    });
    const yL2 = yL + 24;
    el("rect", { x: 18, y: yL2 - 10, width: 22, height: 10, fill: ROUGE });
    el("text", { x: 46, y: yL2, "font-size": 13, fill: ENCRE, "font-family": "sans-serif" }, "retard");
    el("line", { x1: 129, y1: yL2 - 12, x2: 129, y2: yL2 + 2, stroke: ENCRE, "stroke-width": 2, "stroke-dasharray": "4 3" });
    el("text", { x: 136, y: yL2, "font-size": 13, fill: ENCRE, "font-family": "sans-serif" }, "fin prévue");
    el("line", { x1: 229, y1: yL2 - 12, x2: 229, y2: yL2 + 2, stroke: BLEU, "stroke-width": 3 });
    el("text", { x: 236, y: yL2, "font-size": 13, fill: ENCRE, "font-family": "sans-serif" }, "aujourd'hui");
    return { semaine, retard, fin: tests.fin };
  },
};
