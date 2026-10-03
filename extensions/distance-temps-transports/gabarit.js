// Jules - gabarit "distance-temps-transports" : distance en km (curseur km) et distance en temps pour cinq modes de
// transport. Echelles logarithmiques (1, 10, 100, 1 000 km ; 1 min, 1 h, 1 jour, 1 semaine) : aucune duree ecrite en
// chiffres, seulement des barres. Vitesses moyennes reprises des exemples de la fiche CM1 (500 m en 8 min a pied,
// 3 km en 15 min a velo, 300 km en 2 h en train, 4 200 km en 5 h 30 en avion) ; voiture 80 km/h. Temps fixes
// (approximations, jamais ecrites) : 5 min pour garer la voiture, 20 min pour aller a la gare, 2 h 30 pour aller a
// l'aeroport et embarquer : c'est pour cela que le train puis l'avion ne gagnent que sur les longues distances.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["distance-temps-transports"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const BLEU = "#1F4E8C", GRIS = "#6B7686", ENCRE = "#14243B", VERT = "#2E7D32", ORANGE = "#E07B00";
    const km = Math.min(1000, Math.max(1, Number(valeurs.km ?? 5) || 5));
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    // [nom, vitesse en km/h, temps fixe en minutes]
    const MODES = [["à pied", 4, 0], ["vélo", 12, 0], ["voiture", 80, 5], ["train", 150, 20], ["avion", 800, 150]];
    const minutes = MODES.map(([, v, fixe]) => (km / v) * 60 + fixe);
    const plusRapide = minutes.indexOf(Math.min(...minutes));

    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // --- distance en km : une barre bleue, echelle 1 -> 1 000 km --------------------------------------------
    const XD = (d) => 24 + (Math.log10(d) / 3) * 288;
    el("text", { x: 8, y: 20, "font-size": 14, fill: BLEU, "font-weight": 700 }, "distance en km");
    el("rect", { x: 24, y: 32, width: 288, height: 14, rx: 7, fill: "#D5DAE1" });
    el("rect", { x: 24, y: 32, width: Math.max(14, XD(km) - 24), height: 14, rx: 7, fill: BLEU });
    for (const [d, nom] of [[1, "1 km"], [10, "10 km"], [100, "100 km"], [1000, "1 000 km"]]) {
      el("line", { x1: XD(d), y1: 48, x2: XD(d), y2: 56, stroke: GRIS, "stroke-width": 2 });
      const ancre = d === 1 ? "start" : d === 1000 ? "end" : "middle";
      el("text", { x: d === 1 ? 18 : d === 1000 ? 332 : XD(d), y: 72, "font-size": 13, "text-anchor": ancre, fill: GRIS }, nom);
    }

    // --- distance en temps : une barre par mode, echelle 1 min -> 1 semaine ---------------------------------
    const T0 = 96, T1 = 312, SEMAINE = 7 * 24 * 60;
    const XT = (m) => T0 + (Math.log10(Math.min(SEMAINE, Math.max(1, m))) / Math.log10(SEMAINE)) * (T1 - T0);
    el("text", { x: 8, y: 104, "font-size": 14, fill: ORANGE, "font-weight": 700 }, "distance en temps");
    for (const [m, nom] of [[60, "1 h"], [1440, "1 jour"], [SEMAINE, "1 sem."]]) {
      el("line", { x1: XT(m), y1: 114, x2: XT(m), y2: 268, stroke: "#D5DAE1", "stroke-width": 2, "stroke-dasharray": "4 4" });
      el("text", { x: m === SEMAINE ? 334 : XT(m), y: 286, "font-size": 13, "text-anchor": m === SEMAINE ? "end" : "middle", fill: GRIS }, nom);
    }
    el("text", { x: T0, y: 286, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "1 min");
    el("line", { x1: T0, y1: 268, x2: T1, y2: 268, stroke: GRIS, "stroke-width": 2 });
    MODES.forEach(([nom], i) => {
      const y = 122 + i * 29, rapide = i === plusRapide, couleur = rapide ? VERT : ORANGE;
      el("text", { x: 88, y: y + 14, "font-size": 14, "text-anchor": "end", fill: rapide ? VERT : ENCRE, "font-weight": rapide ? 700 : 400 }, nom);
      const largeur = Math.max(6, XT(minutes[i]) - T0);
      el("rect", { x: T0, y, width: largeur, height: 18, rx: 4, fill: couleur }).setAttribute("data-adresse", `graphe/mode-${i + 1}`);
      if (minutes[i] > SEMAINE) {
        // Plus d'une semaine : la barre sort du cadre, une pointe le montre.
        el("polygon", { points: `${T1},${y - 3} ${T1 + 14},${y + 9} ${T1},${y + 21}`, fill: couleur });
      }
    });
    return { km, plus_rapide: MODES[plusRapide][0] };
  },
};
