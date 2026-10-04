// Jules - gabarit "courbe-releves" : courbe de temperature d'une journee type et thermometre a cote.
// Un point suit la courbe a l'heure choisie ; un pointille horizontal le relie au haut de la colonne du thermometre,
// gradue sur la meme echelle que la courbe. La saison deplace toute la courbe vers le haut ou le bas.
// Curseurs : heure (0 a 23, heure legale), saison (1 hiver, 2 printemps, 3 ete, 4 automne).
// Journee type : minimum vers le lever du jour, maximum vers 15 h, montee puis descente en demi-cosinus.
// La temperature n'est pas ecrite en chiffres : l'eleve la lit sur le thermometre.
// Faits verifies (EX-205) :
// - Normales 1991-2020 de la station Meteo-France d'Orleans-Bricy (07249), via Infoclimat
//   (infoclimat.fr/climatologie/normales-records/1991-2020/orleans-bricy/valeurs/07249.html), moyennes des trois
//   mois de chaque saison (hiver dec-jan-fev, printemps mars-avr-mai, ete juin-juil-aout, automne sept-oct-nov) :
//   mini / maxi moyennes : hiver 1,7 / 7,7 ; printemps 5,8 / 16,1 ; ete 13,0 / 24,9 ; automne 7,7 / 16,4 (degres C).
//   La meme station compte 48,6 jours de gel par an (Meteo Centre, normales d'Orleans) : la colonne peut passer
//   sous 0 C par grand froid, meme si la journee type d'hiver reste au-dessus.
// - Programme de sciences et technologie du cycle 3 (BO n° 24 du 11/06/2026) : realiser et exploiter des mesures
//   meteorologiques.
// Heures du minimum (approchees, lever du soleil a Orleans en heure legale) : hiver 8 h, printemps 7 h, ete 6 h,
// automne 8 h ; maximum a 15 h (l'air se rechauffe encore apres midi solaire).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["courbe-releves"] = {
  dessiner(svg, valeurs) {
    const heure = Math.min(23, Math.max(0, Number(valeurs.heure ?? 8)));
    const saison = Math.min(4, Math.max(1, Math.round(Number(valeurs.saison ?? 2))));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const SAISONS = {
      1: { nom: "en hiver", mini: 1.7, maxi: 7.7, hmin: 8 },
      2: { nom: "au printemps", mini: 5.8, maxi: 16.1, hmin: 7 },
      3: { nom: "en été", mini: 13.0, maxi: 24.9, hmin: 6 },
      4: { nom: "en automne", mini: 7.7, maxi: 16.4, hmin: 8 },
    }[saison];
    const HMAX = 15;
    const temperature = (h) => {
      const { mini, maxi, hmin } = SAISONS;
      if (h >= hmin && h <= HMAX) { // montee
        const f = (h - hmin) / (HMAX - hmin);
        return mini + ((maxi - mini) * (1 - Math.cos(Math.PI * f))) / 2;
      }
      const t = h > HMAX ? h - HMAX : h + 24 - HMAX; // descente jusqu'au minimum du lendemain
      const f = t / (24 - (HMAX - hmin));
      return maxi - ((maxi - mini) * (1 - Math.cos(Math.PI * f))) / 2;
    };

    // Echelles communes : heures 0-24 sur x (courbe), -5 a 30 degres sur y (courbe ET thermometre).
    const X0 = 22, X1 = 236, Y_HAUT = 46, Y_BAS = 256, TMIN = -5, TMAX = 30;
    const X = (h) => X0 + ((X1 - X0) * h) / 24;
    const Y = (t) => Y_BAS - ((Y_BAS - Y_HAUT) * (t - TMIN)) / (TMAX - TMIN);
    const XT = 292; // axe du thermometre

    el("text", { x: X0, y: 24, "font-size": 15, "font-weight": "bold", fill: "#14243B" }, `Une journée ${SAISONS.nom}`);

    // Lignes de graduation (tous les 5 degres) prolongees jusqu'au thermometre, etiquettes a droite.
    for (let t = TMIN; t <= TMAX; t += 5) {
      el("line", { x1: X0, y1: Y(t), x2: XT - 10, y2: Y(t), stroke: t === 0 ? "#1F4E8C" : "#D5DAE1", "stroke-width": 2 });
      el("line", { x1: XT + 9, y1: Y(t), x2: XT + 17, y2: Y(t), stroke: "#14243B", "stroke-width": 2 });
      if (t % 10 === 0) el("text", { x: XT + 20, y: Y(t) + 5, "font-size": 13, fill: "#14243B" }, String(t));
    }
    el("text", { x: XT + 20, y: Y_HAUT - 16, "font-size": 13, fill: "#14243B" }, "°C");

    // Axe des heures.
    el("line", { x1: X0, y1: Y_BAS, x2: X1, y2: Y_BAS, stroke: "#14243B", "stroke-width": 2 });
    for (const h of [0, 6, 12, 18, 24]) {
      el("line", { x1: X(h), y1: Y_BAS, x2: X(h), y2: Y_BAS + 6, stroke: "#14243B", "stroke-width": 2 });
      el("text", { x: X(h), y: Y_BAS + 22, "font-size": 13, "text-anchor": "middle", fill: "#14243B" }, `${h} h`);
    }

    // Courbe de la journee type.
    const pts = [];
    for (let i = 0; i <= 96; i++) {
      const h = i / 4;
      pts.push(`${X(h).toFixed(1)},${Y(temperature(h % 24)).toFixed(1)}`);
    }
    el("polyline", { points: pts.join(" "), fill: "none", stroke: "#1F4E8C", "stroke-width": 3 });

    // Point a l'heure choisie, relie au thermometre.
    const T = temperature(heure);
    el("line", { x1: X(heure), y1: Y(T), x2: XT, y2: Y(T), stroke: "#C8102E", "stroke-width": 2, "stroke-dasharray": "4 4" });
    el("line", { x1: X(heure), y1: Y(T), x2: X(heure), y2: Y_BAS, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "3 4" });
    el("circle", { cx: X(heure), cy: Y(T), r: 7, fill: "#C8102E", stroke: "#FFFFFF", "stroke-width": 2 });

    // Thermometre : tube, reservoir, colonne rouge jusqu'a la temperature.
    el("rect", { x: XT - 8, y: Y_HAUT - 8, width: 16, height: Y_BAS - Y_HAUT + 20, rx: 8, fill: "#FFFFFF", stroke: "#14243B", "stroke-width": 2 });
    el("circle", { cx: XT, cy: Y_BAS + 22, r: 14, fill: "#C8102E", stroke: "#14243B", "stroke-width": 2 });
    el("rect", { x: XT - 4, y: Y(T), width: 8, height: Y_BAS + 14 - Y(T), fill: "#C8102E" });
    return { heure, saison, temperature: Math.round(T * 10) / 10 };
  },
};
