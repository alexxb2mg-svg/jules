// Jules - gabarit "empreinte-carbone-trajet" : quatre barres horizontales (plane, car, coach, train) pour le meme
// trajet ; la longueur d'une barre = le CO2 emis PAR PASSAGER. Curseurs : km (longueur du trajet, 100 a 1 000 km)
// et transport (barre mise en avant : 1 avion, 2 voiture, 3 car, 4 train).
//
// Faits (verifies) : facteurs d'emission ADEME, Base Empreinte, repris par impactco2.fr (fichier
// https://impactco2.fr/equivalents.csv, consulte le 04/10/2026), en kg CO2e par passager et par km :
//   avion trajet court (moins de 1 000 km) 0,2246 ; voiture thermique moyenne, conducteur seul 0,1423 ;
//   autocar thermique 0,0376 ; TGV 0,00293. (Pour comparaison : voiture thermique a 4 personnes 0,0356, un peu
//   MOINS que l'autocar ; c'est ce que dit la lecture « with four people ».)
// La distance s'arrete a 1 000 km : au-dela, l'ADEME change de facteur avion (trajet moyen 0,1847) et la barre de
// l'avion raccourcirait quand le trajet s'allonge, ce qui tromperait l'eleve.
// Echelle fixe (1 px = 1 kg, 0 a 230 kg) : les barres s'allongent avec la distance. Aucune valeur n'est ecrite
// sur les barres, seulement l'axe gradue en kg : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["empreinte-carbone-trajet"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686";
    const borne = (v, min, max, d) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : d;
    };
    const km = borne(valeurs.km, 100, 1000, 500);
    const transport = Math.round(borne(valeurs.transport, 1, 4, 1));
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    // [libelle anglais, kg CO2e par passager et par km]
    const MODES = [["plane", 0.2246], ["car (alone)", 0.1423], ["coach", 0.0376], ["train", 0.00293]];
    const X0 = 96, PX_PAR_KG = 1;

    svg.setAttribute("viewBox", "0 0 340 270");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS
    el("text", { x: 170, y: 24, "font-size": 16, "font-weight": "bold", "text-anchor": "middle", fill: ENCRE },
      `a ${km} km trip`);
    el("text", { x: 170, y: 44, "font-size": 13, "text-anchor": "middle", fill: GRIS }, "CO₂ for one passenger");

    MODES.forEach(([nom, facteur], i) => {
      const y = 64 + i * 44;
      const choisi = i + 1 === transport;
      const longueur = Math.max(3, km * facteur * PX_PAR_KG); // une barre minuscule reste visible
      el("text", { x: X0 - 8, y: y + 19, "font-size": 14, "text-anchor": "end", "font-weight": choisi ? "bold" : "normal",
        fill: choisi ? BLEU : ENCRE }, nom);
      el("rect", { x: X0, y, width: longueur, height: 28, rx: 3, fill: choisi ? BLEU : GRIS,
        "fill-opacity": choisi ? 1 : 0.45, stroke: choisi ? ENCRE : "none", "stroke-width": 2 });
    });

    // Axe gradue en kg (0 a 200), sous les barres.
    const yAxe = 244;
    el("line", { x1: X0, y1: yAxe, x2: X0 + 230 * PX_PAR_KG, y2: yAxe, stroke: ENCRE, "stroke-width": 2 });
    for (let kg = 0; kg <= 200; kg += 50) {
      const x = X0 + kg * PX_PAR_KG;
      el("line", { x1: x, y1: yAxe, x2: x, y2: yAxe + 6, stroke: ENCRE, "stroke-width": 2 });
      el("text", { x, y: yAxe + 21, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, String(kg));
    }
    el("text", { x: X0 - 8, y: yAxe + 21, "font-size": 13, "text-anchor": "end", fill: GRIS }, "kg CO₂");
    return { km, transport };
  },
};
