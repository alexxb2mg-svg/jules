// Jules - gabarit "reponse-immunitaire" : quantite de microbes et d'anticorps dans le sang au fil des jours, au
// premier contact avec un microbe (vaccin 0) ou chez une personne deja vaccinee (vaccin 1, memoire immunitaire).
// Curseurs : jour (0 a 30, jours apres l'entree du microbe), vaccin (0 ou 1).
// Modele (formes de courbes, pas de mesures) :
// - premier contact : microbes en cloche, pic vers le jour 8, au-dessus du seuil ou l'on est malade ; anticorps
//   absents jusqu'au jour 5, pic vers le jour 14, puis baisse lente ;
// - deja vaccine : microbes vite elimines (pic vers le jour 2-3, sous le seuil) ; anticorps des le jour 1, pic vers
//   le jour 5, bien plus haut et durable.
// Faits verifies :
// - programme de SVT du cycle 4 (annexe 3, arrete du 17-7-2020, eduscol.education.fr/document/621/download) :
//   « expliquer les reactions qui permettent a l'organisme de se preserver des micro-organismes pathogenes » ;
//   reactions immunitaires, vaccination ;
// - reussir-svt.com, « Memoire immunitaire, reponse secondaire » : delai d'apparition des anticorps 7 a 14 jours
//   au premier contact, 1 a 3 jours au second ; taux maximal 10 a 100 fois plus eleve au second contact ;
// - Manuel Merck (grand public), « Immunite acquise » : la reponse primaire est lente (plusieurs jours), la
//   reponse secondaire, due aux lymphocytes B memoire, est rapide et tres efficace ;
// - Vikidia « Vaccin » : sans rendre malade, le vaccin provoque la fabrication d'anticorps.
// Echelle verticale non respectee (pic secondaire dessine environ 3 fois plus haut, pas 10 a 100 fois, pour que
// la courbe du premier contact reste visible) ; aucun nombre sur l'axe vertical : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["reponse-immunitaire"] = {
  dessiner(svg, valeurs) {
    const jour = Math.min(30, Math.max(0, Number(valeurs.jour ?? 10)));
    const vaccin = Number(valeurs.vaccin ?? 0) >= 1 ? 1 : 0;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const texte = (x, y, contenu, couleur, attrs = {}) =>
      el("text", Object.assign({ x, y, "font-size": 14, "text-anchor": "middle", fill: couleur }, attrs), contenu);
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const MICROBE = "#C8102E", ANTICORPS = "#1F4E8C";
    const X0 = 40, X1 = 320, Y0 = 236, HAUT = 170, SEUIL = 0.5; // hauteurs en part de HAUT
    const px = (d) => X0 + ((X1 - X0) * d) / 30;
    const py = (v) => Y0 - HAUT * v;
    const cloche = (d, centre, largeur) => Math.exp(-(((d - centre) / largeur) ** 2));
    // Montee en x.e^(1-x) jusqu'au pic, puis baisse lente vers un palier (les anticorps restent un temps).
    const montee = (d, debut, pic, palier, duree) => {
      if (d <= debut) return 0;
      const x = (d - debut) / (pic - debut);
      return x <= 1 ? x * Math.exp(1 - x) : palier + (1 - palier) * Math.exp(-(d - pic) / duree);
    };
    const microbes = (d) => (vaccin ? 0.3 * cloche(d, 2.5, 1.6) : 0.85 * cloche(d, 8, 4));
    const anticorps = (d) => (vaccin ? 0.04 + 0.92 * montee(d, 1, 5, 0.6, 6) : 0.3 * montee(d, 5, 14, 0.5, 6));

    texte(170, 22, vaccin ? "déjà vacciné : mémoire immunitaire" : "premier contact avec le microbe", "#14243B",
      { "font-weight": "bold" });
    // Axes.
    el("line", { x1: X0, y1: Y0, x2: X1, y2: Y0, stroke: "#6B7686", "stroke-width": 2 });
    el("line", { x1: X0, y1: Y0, x2: X0, y2: Y0 - HAUT - 10, stroke: "#6B7686", "stroke-width": 2 });
    for (const d of [0, 10, 20, 30]) {
      el("line", { x1: px(d), y1: Y0, x2: px(d), y2: Y0 + 5, stroke: "#6B7686", "stroke-width": 2 });
      texte(px(d), Y0 + 20, String(d), "#6B7686", { "font-size": 13 });
    }
    texte(X1, Y0 + 38, "jours", "#6B7686", { "font-size": 13, "text-anchor": "end" });
    texte(X0 - 6, Y0 - HAUT - 16, "quantité", "#6B7686", { "font-size": 13, "text-anchor": "start" });
    // Seuil au-dessus duquel les microbes rendent malade.
    el("line", { x1: X0, y1: py(SEUIL), x2: X1, y2: py(SEUIL), stroke: MICROBE, "stroke-width": 2, "stroke-dasharray": "5 4",
      "stroke-opacity": 0.6 });
    texte(X1, py(SEUIL) + 18, "microbes : on est malade", MICROBE, { "font-size": 13, "text-anchor": "end" });
    // Courbes : trait plein jusqu'au jour choisi, pointille pale apres.
    const courbe = (f, couleur) => {
      const avant = [], apres = [];
      for (let d = 0; d <= 30.001; d += 0.25) {
        const p = `${px(d).toFixed(1)},${py(f(d)).toFixed(1)}`;
        if (d <= jour) avant.push(p);
        if (d >= jour - 0.25) apres.push(p);
      }
      if (apres.length > 1) {
        el("polyline", { points: apres.join(" "), fill: "none", stroke: couleur, "stroke-width": 2,
          "stroke-dasharray": "3 4", "stroke-opacity": 0.45 });
      }
      if (avant.length > 1) el("polyline", { points: avant.join(" "), fill: "none", stroke: couleur, "stroke-width": 4 });
      el("circle", { cx: px(jour), cy: py(f(jour)), r: 6, fill: couleur, stroke: "#FFFFFF", "stroke-width": 2 });
    };
    el("line", { x1: px(jour), y1: Y0, x2: px(jour), y2: Y0 - HAUT - 4, stroke: "#14243B", "stroke-width": 2,
      "stroke-dasharray": "2 3" });
    courbe(microbes, MICROBE);
    courbe(anticorps, ANTICORPS);
    // Legende.
    el("line", { x1: 196, y1: 48, x2: 216, y2: 48, stroke: MICROBE, "stroke-width": 4 });
    texte(222, 53, "microbes", MICROBE, { "text-anchor": "start", "font-weight": "bold" });
    el("line", { x1: 196, y1: 68, x2: 216, y2: 68, stroke: ANTICORPS, "stroke-width": 4 });
    texte(222, 73, "anticorps", ANTICORPS, { "text-anchor": "start", "font-weight": "bold" });
    const malade = microbes(jour) > SEUIL;
    texte(170, 292, malade ? "jour " + jour + " : les microbes rendent malade" : "jour " + jour + " : pas malade",
      malade ? MICROBE : "#2E7D32", { "font-weight": "bold" });
    return { jour, vaccin, malade };
  },
};
