// Jules - gabarit "action-enzyme" : une enzyme (amylase) decoupe une chaine d'amidon en petits sucres ;
// la vitesse de decoupe depend de la temperature.
// Curseurs : temps (minutes), temp (degres C), enzyme (0 = tube temoin avec de l'eau, 1 = avec amylase).
// Modele (illustration, ordres de grandeur d'une experience de classe) : activite a(T) = exp(-((T - 37) / 15)^2)
// pour T < 60, nulle a partir de 60 degres (enzyme detruite, denaturee) ; nombre de liaisons coupees sur 11 :
// arrondi(11 x min(1, a x temps / 20)), soit tout l'amidon decoupe en 20 min a 37 degres.
// Faits verifies :
// - programme de SVT du cycle 4 (annexe 3, arrete du 17-7-2020, eduscol.education.fr/document/621/download) :
//   transformations des aliments par les enzymes digestives ;
// - Vikidia « Enzyme » : une enzyme accelere une reaction a la temperature du corps (37 degres C chez les
//   mammiferes), elle ressort intacte ; trop chaude elle est denaturee (detruite), trop froide elle est
//   seulement ralentie et reprend son activite au chaud ;
// - fiches 3e svt mecanismes-moleculaires-digestion et devenir-aliments-tube-digestif : l'eau iodee devient
//   bleu-noir en presence d'amidon ; le tube temoin sans salive reste bleu-noir.
// L'amylase donne surtout du maltose (deux glucoses) : la figure dit « petits sucres », pas « glucose ».
// Aucune valeur de reponse ecrite : revele false.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["action-enzyme"] = {
  dessiner(svg, valeurs) {
    const temps = Math.min(30, Math.max(0, Number(valeurs.temps ?? 10)));
    const temp = Math.min(80, Math.max(0, Number(valeurs.temp ?? 40)));
    const enzyme = Number(valeurs.enzyme ?? 1) >= 1 ? 1 : 0;
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
    svg.setAttribute("viewBox", "0 0 340 270");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    const AMIDON = "#E07B00", SUCRE = "#2E7D32", ENZYME = "#1F4E8C";
    const detruite = temp >= 60;
    const activite = enzyme === 0 || detruite ? 0 : Math.exp(-(((temp - 37) / 15) ** 2));
    const N = 12, LIAISONS = N - 1;
    const coupes = Math.round(LIAISONS * Math.min(1, (activite * temps) / 20));
    // Ordre fixe des coupures (l'enzyme attaque la chaine a plusieurs endroits).
    const ORDRE = [5, 2, 8, 0, 10, 3, 7, 1, 9, 4, 6];
    const coupee = new Array(LIAISONS).fill(false);
    ORDRE.slice(0, coupes).forEach((i) => { coupee[i] = true; });

    texte(170, 22, `tube à ${temp} °C, après ${temps} min`, "#14243B", { "font-weight": "bold" });
    // Chaine : perles reliees ; une liaison coupee laisse un ecart. Morceau de 3 perles ou plus = amidon (orange),
    // morceau de 1 ou 2 perles = petit sucre (vert).
    const PAS = 20, ECART = 6, Y = 92;
    const xs = [];
    let x = 170 - (PAS * LIAISONS + ECART * coupes) / 2;
    for (let i = 0; i < N; i++) {
      xs.push(x);
      if (i < LIAISONS) x += PAS + (coupee[i] ? ECART : 0);
    }
    const morceau = new Array(N).fill(0);
    let debut = 0;
    for (let i = 0; i <= LIAISONS; i++) {
      if (i === LIAISONS || coupee[i]) {
        for (let j = debut; j <= i; j++) morceau[j] = i - debut + 1;
        debut = i + 1;
      }
    }
    for (let i = 0; i < LIAISONS; i++) {
      if (!coupee[i]) el("line", { x1: xs[i], y1: Y, x2: xs[i + 1], y2: Y, stroke: AMIDON, "stroke-width": 4 });
    }
    for (let i = 0; i < N; i++) {
      el("circle", { cx: xs[i], cy: Y, r: 8, fill: morceau[i] >= 3 ? AMIDON : SUCRE, stroke: "#FFFFFF", "stroke-width": 2 });
    }
    texte(52, 124, "amidon", AMIDON, { "font-weight": "bold" });
    texte(268, 124, "petits sucres", SUCRE, { "font-weight": "bold" });

    // L'enzyme : une forme en ciseaux bleue au-dessus de la chaine ; grise et croisee si elle est detruite.
    if (enzyme === 1) {
      const cible = coupes < LIAISONS ? ORDRE[coupes] : ORDRE[LIAISONS - 1];
      const ex = (xs[cible] + xs[cible + 1]) / 2, ey = 56;
      const couleur = detruite ? "#6B7686" : ENZYME;
      el("path", { d: `M ${ex - 14} ${ey - 12} L ${ex} ${ey + 8} L ${ex + 14} ${ey - 12}`, fill: "none", stroke: couleur,
        "stroke-width": 4, "stroke-linecap": "round", "stroke-linejoin": "round" });
      el("circle", { cx: ex - 16, cy: ey - 16, r: 5, fill: "none", stroke: couleur, "stroke-width": 3 });
      el("circle", { cx: ex + 16, cy: ey - 16, r: 5, fill: "none", stroke: couleur, "stroke-width": 3 });
      if (detruite) {
        el("line", { x1: ex - 12, y1: ey - 14, x2: ex + 12, y2: ey + 6, stroke: "#C8102E", "stroke-width": 3 });
        el("line", { x1: ex - 12, y1: ey + 6, x2: ex + 12, y2: ey - 14, stroke: "#C8102E", "stroke-width": 3 });
      }
      texte(ex < 170 ? ex + 30 : ex - 30, ey - 6, detruite ? "enzyme détruite" : "enzyme",
        detruite ? "#C8102E" : ENZYME, { "text-anchor": ex < 170 ? "start" : "end", "font-weight": "bold" });
    } else {
      texte(170, 52, "pas d'enzyme : de l'eau seulement", "#6B7686");
    }

    // Vitesse de decoupe : une jauge qui depend de la temperature.
    const JX = 40, JL = 260, JY = 150;
    texte(JX, JY - 6, "vitesse de découpe", "#14243B", { "text-anchor": "start" });
    el("rect", { x: JX, y: JY, width: JL, height: 16, fill: "#FFFFFF", stroke: "#C9D1DC", "stroke-width": 2 });
    if (activite > 0) el("rect", { x: JX, y: JY, width: Math.max(2, JL * activite), height: 16, fill: ENZYME });
    texte(JX, JY + 34, "nulle", "#6B7686", { "text-anchor": "start", "font-size": 13 });
    texte(JX + JL, JY + 34, "maximale (37 °C)", "#6B7686", { "text-anchor": "end", "font-size": 13 });

    // Test a l'eau iodee : bleu-noir tant qu'il reste de l'amidon. La couleur est montree, jamais ecrite :
    // l'interpreter est la reponse de l'exercice type des tubes (EX-204).
    const amidonReste = morceau.some((m) => m >= 3);
    el("rect", { x: 40, y: 206, width: 24, height: 44, rx: 8, fill: amidonReste ? "#14243B" : "#E07B00",
      "fill-opacity": amidonReste ? 1 : 0.35, stroke: "#6B7686", "stroke-width": 2 });
    texte(76, 234, "test à l'eau iodée", "#14243B", { "text-anchor": "start" });
    return { temps, temp, enzyme, coupes, amidonReste };
  },
};
