// Jules - gabarit "echelles-paralleles" : deux (ou trois) graduations cote a cote pour lire la meme chose dans
// deux codes culturels. Curseur echelle : 1 = thermometre degres Celsius / degres Fahrenheit (curseur celsius),
// 2 = reglettes des classes France / Angleterre / Etats-Unis alignees sur l'age (curseur age).
//
// Faits (verifies) :
// - Conversion : F = 1,8 x C + 32 (NIST, SP 811 « Guide for the Use of the SI », annexe B.8 ; l'eau gele a 0 °C =
//   32 °F). Graduations : °C tous les 5 (chiffres tous les 10), °F tous les 10 (chiffres tous les 20). La valeur
//   convertie n'est jamais ecrite : on la lit sur la graduation, comme une regle (la plupart des valeurs ne tombent pas
//   sur un chiffre ; ex. 20 °C = 68 °F se lit entre 60 et 80).
// - Temperature normale du corps humain ≈ 37 °C (Ameli, « Fièvre de l'adulte »).
// - Classes : France 6e (11 ans) a terminale (17 ans) (education.gouv.fr, « Le collège », « Le lycée ») ;
//   Angleterre Year 7 (11-12 ans) a Year 11 (15-16 ans, GCSE), puis Year 12-13 = sixth form (gov.uk, « The national
//   curriculum » : key stages, et « A levels ») ; Etats-Unis 6th grade (11-12 ans) a 12th grade (17-18 ans),
//   middle school = grades 6-8, high school = grades 9-12 (U.S. Department of Education, « Structure of U.S.
//   Education »). Correspondance usuelle : 6e = Year 7 = 6th grade, 3e = Year 10 = 9th grade.
//   L'age est celui de la rentree (approximation : un enfant ne fete pas son anniversaire le meme mois partout).
// Revele : la reglette des classes ECRIT l'equivalence (3e = Year 10), c'est la reponse d'un exercice -> revele true.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["echelles-paralleles"] = {
  dessiner(svg, valeurs) {
    const NS = "http://www.w3.org/2000/svg";
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const borne = (v, min, max, d) => {
      const n = Number(v);
      return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : d;
    };
    const echelle = Math.round(borne(valeurs.echelle, 1, 2, 1));
    const celsius = Math.round(borne(valeurs.celsius, -10, 40, 20) / 5) * 5;
    const age = Math.round(borne(valeurs.age, 11, 17, 14));
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    if (echelle === 1) {
      const HALO = { stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke" };
      // Thermometre : -10 °C en bas (y = 260), 40 °C en haut (y = 60), 4 px par degre Celsius.
      svg.setAttribute("viewBox", "0 0 340 320");
      const Y = (c) => 260 - 4 * (c + 10);
      const YF = (f) => Y((f - 32) / 1.8);
      const couleur = celsius <= 0 ? BLEU : celsius <= 20 ? VERT : celsius <= 30 ? ORANGE : ROUGE;
      el("text", { x: 120, y: 30, "font-size": 16, "font-weight": "bold", "text-anchor": "end", fill: ENCRE }, "°C");
      el("text", { x: 120, y: 47, "font-size": 13, "text-anchor": "end", fill: GRIS }, "France");
      el("text", { x: 220, y: 30, "font-size": 16, "font-weight": "bold", fill: ENCRE }, "°F");
      el("text", { x: 220, y: 47, "font-size": 13, fill: GRIS }, "USA");
      // Tube et reservoir, remplis jusqu'a la temperature choisie.
      el("rect", { x: 155, y: 52, width: 30, height: 222, rx: 15, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 2 });
      el("circle", { cx: 170, cy: 288, r: 20, fill: couleur, stroke: ENCRE, "stroke-width": 2 });
      el("rect", { x: 161, y: Y(celsius), width: 18, height: 290 - Y(celsius), fill: couleur });
      // Ligne de lecture : la meme hauteur sur les deux graduations, dessinee sous les nombres :
      // un liseré blanc autour de chaque nombre le garde lisible quand la ligne le traverse.
      el("line", { x1: 92, y1: Y(celsius), x2: 250, y2: Y(celsius), stroke: couleur, "stroke-width": 3, "stroke-dasharray": "7 4" });
      el("path", { d: `M92,${Y(celsius)} l-10,-7 l0,14 z`, fill: couleur });
      el("path", { d: `M250,${Y(celsius)} l10,-7 l0,14 z`, fill: couleur });
      // Graduation Celsius a gauche du tube.
      for (let c = -10; c <= 40; c += 5) {
        const long = c % 10 === 0;
        el("line", { x1: long ? 135 : 143, y1: Y(c), x2: 155, y2: Y(c), stroke: ENCRE, "stroke-width": 2 });
        if (long) el("text", { x: 130, y: Y(c) + 5, "font-size": 14, "text-anchor": "end", fill: ENCRE, ...HALO }, String(c));
      }
      // Graduation Fahrenheit a droite du tube (20 a 100 °F, soit -6,7 a 37,8 °C).
      for (let f = 20; f <= 100; f += 10) {
        const long = f % 20 === 0;
        el("line", { x1: 185, y1: YF(f), x2: long ? 205 : 197, y2: YF(f), stroke: ENCRE, "stroke-width": 2 });
        if (long) el("text", { x: 210, y: YF(f) + 5, "font-size": 14, fill: ENCRE, ...HALO }, String(f));
      }
      // Deux reperes fixes, sans nombre.
      el("text", { x: 262, y: Y(0) + 5, "font-size": 13, fill: GRIS }, "l'eau gèle");
      el("text", { x: 262, y: Y(37) + 5, "font-size": 13, fill: GRIS }, "notre corps");
      return { echelle, celsius };
    }

    // Reglettes des classes : 7 colonnes d'age (11 a 17 ans).
    svg.setAttribute("viewBox", "0 0 340 270");
    const X0 = 70, L = 37;
    const colonne = (a) => X0 + (a - 11) * L;
    const LIGNES = [
      { pays: "France", code: "classe", y: 62, noms: ["6e", "5e", "4e", "3e", "2de", "1re", "Tle"],
        etapes: [["collège", 11, 14], ["lycée", 15, 17]] },
      { pays: "England", code: "Year", y: 132, noms: ["7", "8", "9", "10", "11", "12", "13"],
        etapes: [["secondary", 11, 15], ["sixth form", 16, 17]] },
      { pays: "USA", code: "grade", y: 202, noms: ["6th", "7th", "8th", "9th", "10th", "11th", "12th"],
        etapes: [["middle school", 11, 13], ["high school", 14, 17]] },
    ];
    // Ligne des ages, colonne choisie en bleu.
    el("text", { x: 4, y: 36, "font-size": 14, fill: ENCRE }, "âge");
    el("rect", { x: colonne(age), y: 14, width: L, height: 240, fill: BLEU, "fill-opacity": 0.12 });
    for (let a = 11; a <= 17; a++) {
      el("text", { x: colonne(a) + L / 2, y: 36, "font-size": 14, "text-anchor": "middle", "font-weight": a === age ? "bold" : "normal",
        fill: a === age ? BLEU : GRIS }, String(a));
    }
    for (const ligne of LIGNES) {
      el("text", { x: 4, y: ligne.y + 13, "font-size": 14, "font-weight": "bold", fill: ENCRE }, ligne.pays);
      el("text", { x: 4, y: ligne.y + 29, "font-size": 13, fill: GRIS }, ligne.code);
      ligne.noms.forEach((nom, i) => {
        const choisi = 11 + i === age;
        el("rect", { x: colonne(11 + i), y: ligne.y, width: L, height: 30, fill: choisi ? BLEU : "#FFFFFF",
          stroke: choisi ? BLEU : GRIS, "stroke-width": 2 });
        el("text", { x: colonne(11 + i) + L / 2, y: ligne.y + 20, "font-size": 14, "text-anchor": "middle",
          "font-weight": choisi ? "bold" : "normal", fill: choisi ? "#FFFFFF" : ENCRE }, nom);
      });
      // Etapes de la scolarite sous chaque reglette (collège / lycée...).
      for (const [nom, de, a] of ligne.etapes) {
        const x1 = colonne(de) + 3, x2 = colonne(a) + L - 3;
        el("line", { x1, y1: ligne.y + 36, x2, y2: ligne.y + 36, stroke: GRIS, "stroke-width": 2 });
        el("text", { x: (x1 + x2) / 2, y: ligne.y + 52, "font-size": 13, "text-anchor": "middle", fill: GRIS }, nom);
      }
    }
    return { echelle, age };
  },
};
