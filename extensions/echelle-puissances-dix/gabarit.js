// Jules - gabarit "echelle-puissances-dix" : une echelle verticale ou chaque cran vaut 10 fois le cran du dessous,
// le nombre a x 10^n y est place (point rouge) ; il SAUTE d'un cran quand n change et GLISSE dans son cran quand a
// change (position = log10(a x 10^n)). Des reperes en metres donnent l'ordre de grandeur.
// Deux echelles fixes : n <= 6 : de 10^-6 a 10^7 m (bacterie a Loire) ; n >= 7 : de 10^7 a 10^26 m (Terre a
// galaxies, unite adaptee km / ua / al ecrite sous le point). La valeur decimale n'est jamais ecrite.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
//
// Faits (EX-205), en metres, ordres de grandeur arrondis :
// - bacterie Escherichia coli : environ 2 um de long (Wikipedia « Escherichia coli », 1 a 2 um) -> 2e-6 ;
// - cheveu : diametre 50 a 100 um (Wikipedia « Cheveu ») -> 7e-5 ;
// - fourmi : quelques mm (fourmi rousse 4 a 9 mm, Wikipedia « Formica rufa ») -> 5e-3 ;
// - humain (eleve de 3e) : environ 1,6 m ;
// - tour Eiffel : 330 m (toureiffel.paris, « Les chiffres de la tour Eiffel », depuis 2022) -> 3,3e2 ;
// - mont Blanc : 4 805,59 m (mesure 2021, chambre des geometres-experts de Haute-Savoie) -> 4,8e3 ;
// - Loire : 1 006 km (Wikipedia « Loire », SANDRE) -> 1,0e6 ;
// - Terre : diametre 12 742 km (NASA, Earth Fact Sheet, rayon moyen 6 371 km) -> 1,3e7 ;
// - Terre-Lune : 384 400 km (NASA, Moon Fact Sheet, demi-grand axe) -> 3,8e8 ;
// - Terre-Soleil : 1 ua = 149 597 870 700 m (UAI 2012, resolution B2) -> 1,5e11 ;
// - Soleil-Neptune : 30,07 ua = 4 495 millions de km (NASA, Neptune Fact Sheet) -> 4,5e12 ;
// - Proxima du Centaure : 4,24 al (ESO, communique eso1629) ; 1 al = 9,4607e15 m (UAI) -> 4,0e16 ;
// - Voie lactee : environ 100 000 al de diametre (ESA, Gaia) -> 9,5e20 ;
// - galaxie d'Andromede : 2,5 millions d'al (NASA, « Andromeda Galaxy », M31) -> 2,4e22.
// Unites (programme de cycle 4, physique-chimie, « Organisation et transformations de la matiere », BO n° 31 du
// 30/07/2020) : km a l'echelle de la Terre et de la Lune, ua dans le systeme solaire, al pour les etoiles et galaxies.
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["echelle-puissances-dix"] = {
  // dessiner(svg, valeurs) : a de 1 a 9,5 (nombre devant la puissance), n de -6 a 25 (exposant de 10).
  dessiner(svg, valeurs) {
    const borne = (v, d, mini, maxi) => Math.min(maxi, Math.max(mini, Number.isFinite(Number(v ?? d)) ? Number(v ?? d) : d));
    const a = borne(valeurs.a, 3, 1, 9.5);
    const n = Math.round(borne(valeurs.n, 2, -6, 25));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (x) => x.toFixed(1);
    const EXPOSANTS = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
    const puissance = (k) => "10" + String(k).split("").map((c) => EXPOSANTS[c]).join("");
    const virgule = (x) => String(x).replace(".", ",");
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E";
    const espace = n >= 7;
    const bas = espace ? 7 : -6, haut = espace ? 26 : 7;
    const REPERES = espace
      ? [[1.3e7, "Terre (diamètre)"], [3.8e8, "Terre → Lune"], [1.5e11, "Terre → Soleil"],
        [4.5e12, "Soleil → Neptune"], [4.0e16, "Proxima du Centaure"], [9.5e20, "Voie lactée"],
        [2.4e22, "→ Andromède"]]
      : [[2e-6, "bactérie"], [7e-5, "cheveu (épaisseur)"], [5e-3, "fourmi"], [1.6, "humain"],
        [330, "tour Eiffel"], [4.8e3, "mont Blanc"], [1.0e6, "la Loire"]];

    // Axe vertical : y = 312 pour 10^bas, y = 30 pour 10^haut ; un cran = une puissance de 10.
    const X = 168, Y0 = 312, Y1 = 30;
    const cran = (Y0 - Y1) / (haut - bas);
    const Y = (log) => Y0 - (log - bas) * cran;
    el("text", { x: 170, y: 18, "font-size": 14, fill: GRIS, "text-anchor": "middle", "font-family": "sans-serif" },
      espace ? "tailles et distances en mètres" : "un cran = 10 fois plus (repères en mètres)");

    // Le cran du nombre : bande rouge pale entre 10^n et 10^(n+1).
    el("rect", { x: X - 9, y: f(Y(n + 1)), width: 18, height: f(cran), fill: "#F6D5DA", stroke: "none" });
    el("line", { x1: X, y1: Y0, x2: X, y2: Y1, stroke: ENCRE, "stroke-width": 3 });
    for (let k = bas; k <= haut; k++) {
      el("line", { x1: X - 7, y1: f(Y(k)), x2: X + 7, y2: f(Y(k)), stroke: ENCRE, "stroke-width": 2 });
      // A l'echelle de l'espace (19 crans de 15 px), une puissance sur deux est ecrite.
      if (!espace || (k - bas) % 2 === 0) {
        el("text", { x: X + 12, y: f(Y(k) + 5), "font-size": 13, fill: ENCRE, "font-family": "sans-serif" }, puissance(k));
      }
    }

    // Les reperes : un petit point bleu sur l'axe et le nom a gauche.
    for (const [valeur, nom] of REPERES) {
      const y = Y(Math.log10(valeur));
      el("circle", { cx: X, cy: f(y), r: 4, fill: BLEU });
      el("line", { x1: X - 6, y1: f(y), x2: X - 14, y2: f(y), stroke: BLEU, "stroke-width": 2 });
      el("text", { x: X - 18, y: f(y + 5), "font-size": 13, fill: BLEU, "text-anchor": "end", "font-family": "sans-serif" }, nom);
    }

    // Le nombre a x 10^n : point rouge et fleche depuis l'etiquette, a droite des puissances.
    const yp = Y(n + Math.log10(a));
    const ye = Math.min(Y0 - 4, Math.max(Y1 + 22, yp));
    el("line", { x1: 230, y1: f(ye), x2: X + 9, y2: f(yp), stroke: ROUGE, "stroke-width": 2 });
    el("circle", { cx: X, cy: f(yp), r: 7, fill: ROUGE, stroke: "#FFFFFF", "stroke-width": 2 });
    el("text", { x: 234, y: f(ye + 5), "font-size": 15, "font-weight": "bold", fill: ROUGE, "font-family": "sans-serif" },
      `${virgule(a)} × ${puissance(n)}${espace ? " m" : ""}`);
    if (espace) {
      const unite = n <= 9 ? "en km" : n <= 14 ? "en ua" : "en al";
      el("text", { x: 234, y: f(ye + 22), "font-size": 13, fill: GRIS, "font-family": "sans-serif" }, "on compte " + unite);
    }
    return { a, n, espace, position: n + Math.log10(a) };
  },
};
