// Jules - gabarit "atome-constructeur" : un atome dessine avec son noyau (protons rouges, neutrons gris) et ses
// electrons (bleus) autour. Curseurs :
// - protons : nombre de protons (1 a 12) ; c'est lui qui fixe l'element, dont le nom est ecrit ;
// - neutrons : nombre de neutrons (0 a 14) ; seul le noyau grossit, l'element ne change pas (isotopes) ;
// - electrons : electrons GAGNES (positif) ou PERDUS (negatif) par rapport a l'atome neutre, de -2 a 2 ;
//   0 = atome neutre (autant d'electrons que de protons), negatif = ion positif, positif = ion negatif.
// Dessin schematique : les electrons sont places sur deux cercles (2 au plus sur le premier) pour etre comptes ;
// en realite le noyau est environ 100 000 fois plus petit que l'atome (10^-15 m contre 10^-10 m).
// Faits : constitution de l'atome (protons, neutrons, electrons), numero atomique Z = nombre de protons qui
// caracterise l'element, ions = atomes ayant gagne ou perdu des electrons : programme de physique-chimie du
// cycle 4 (BO n° 31 du 30 juillet 2020), https://eduscol.education.fr/document/621/download ; noms et symboles
// des elements 1 a 12 : tableau periodique de l'IUPAC (https://iupac.org/what-we-do/periodic-table-of-elements/),
// noms francais usuels (hydrogene ... magnesium).
// revele true : la figure ecrit le nom de l'element correspondant au nombre de protons (reponse d'un exercice
// « quel element a 8 protons ? ») ; les nombres d'electrons et la charge ne sont pas ecrits (a compter).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["atome-constructeur"] = {
  dessiner(svg, valeurs) {
    const entier = (v, d, min, max) => Math.min(max, Math.max(min, Math.round(Number(v ?? d))));
    const protons = entier(valeurs.protons, 6, 1, 12);
    const neutrons = entier(valeurs.neutrons, 6, 0, 14);
    const ecart = entier(valeurs.electrons, 0, -2, 2);
    const nbElectrons = Math.max(0, protons + ecart);
    const ELEMENTS = [
      ["hydrogène", "H"], ["hélium", "He"], ["lithium", "Li"], ["béryllium", "Be"], ["bore", "B"], ["carbone", "C"],
      ["azote", "N"], ["oxygène", "O"], ["fluor", "F"], ["néon", "Ne"], ["sodium", "Na"], ["magnésium", "Mg"],
    ];
    const [nom, symbole] = ELEMENTS[protons - 1];
    const NS = "http://www.w3.org/2000/svg";
    const el = (n, attrs, texte) => {
      const e = document.createElementNS(NS, n);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 320");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Nom de l'element (fixe par les protons).
    el("text", { x: 14, y: 28, "font-size": 18, fill: "#14243B", "font-weight": "bold" }, `${nom} (${symbole})`);

    // Cercles des electrons.
    const C = { x: 170, y: 168 }, R1 = 52, R2 = 100;
    el("circle", { cx: C.x, cy: C.y, r: R1, fill: "none", stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "5 5" });
    el("circle", { cx: C.x, cy: C.y, r: R2, fill: "none", stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "5 5" });

    // Noyau : nucleons en spirale (tournesol), protons et neutrons melanges regulierement.
    const total = protons + neutrons;
    const nucleons = [];
    let p = 0, n = 0;
    for (let i = 0; i < total; i++) {
      // place un proton quand la part de protons deja placee est en retard sur la proportion voulue
      if (n >= neutrons || (p < protons && p * total <= i * protons)) { nucleons.push("p"); p++; }
      else { nucleons.push("n"); n++; }
    }
    const ANGLE = (137.5 * Math.PI) / 180;
    nucleons.forEach((type, k) => {
      const r = 6.2 * Math.sqrt(k + 0.5);
      el("circle", {
        cx: C.x + r * Math.cos(k * ANGLE), cy: C.y + r * Math.sin(k * ANGLE), r: 6,
        fill: type === "p" ? "#C8102E" : "#6B7686", stroke: "#FFFFFF", "stroke-width": 1.5,
      });
    });

    // Electrons : 2 au plus sur le premier cercle, les autres repartis sur le second.
    const surR1 = Math.min(2, nbElectrons), surR2 = nbElectrons - surR1;
    const poser = (nb, R, depart) => {
      for (let i = 0; i < nb; i++) {
        const a = depart + (2 * Math.PI * i) / nb;
        el("circle", { cx: C.x + R * Math.cos(a), cy: C.y + R * Math.sin(a), r: 7, fill: "#1F4E8C" });
      }
    };
    poser(surR1, R1, -Math.PI / 2);
    poser(surR2, R2, -Math.PI / 2 + 0.3);
    if (protons + ecart < 0) {
      el("text", { x: 14, y: 50, "font-size": 13, fill: "#6B7686" }, "impossible : pas assez d'électrons à perdre");
    }

    // Legende sur une ligne sous l'atome (a droite, « electron (-) » sortait du cadre avec la police de l'appli).
    const leg = [["#C8102E", "proton (+)", 14], ["#6B7686", "neutron", 128], ["#1F4E8C", "électron (−)", 224]];
    leg.forEach(([c, t, x]) => {
      el("circle", { cx: x + 7, cy: 302, r: 7, fill: c });
      el("text", { x: x + 19, y: 307, "font-size": 13, fill: "#14243B" }, t);
    });
    return { protons, neutrons, electrons: nbElectrons, element: symbole };
  },
};
