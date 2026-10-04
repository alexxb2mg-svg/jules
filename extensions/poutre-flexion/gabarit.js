// Jules - gabarit "poutre-flexion" : une etagere (poutre) posee sur deux appuis, une charge au milieu. Elle se
// courbe d'autant plus que la charge est grande, la poutre fine et le materiau souple. Un trait pointille marque
// la fleche maximale admise par le cahier des charges : au-dela, la poutre devient rouge (non validee).
// Curseurs : charge (0 a 1000 N), epaisseur (5 a 40 mm), materiau (1 = bois, 2 = aluminium, 3 = acier).
// Modele (EX-205) : poutre sur deux appuis simples, charge ponctuelle au milieu, fleche f = F L^3 / (48 E I),
// avec I = b h^3 / 12 pour une section rectangulaire (Wikipedia, « Fleche (resistance des materiaux) » ;
// formulaires de RDM) : f est proportionnelle a la charge et divisee par 8 quand l'epaisseur double (h au cube).
// Etagere de portee L = 1 m et de largeur b = 20 cm. Modules d'Young (Wikipedia, « Module de Young », valeurs
// usuelles) : bois (pin, dans le sens des fibres) 11 GPa, aluminium 69 GPa, acier 210 GPa. Masses volumiques
// usuelles : bois ~0,5, aluminium 2,7, acier 7,8 g/cm3 (l'acier, plus rigide, est aussi le plus lourd).
// Fleche admise : 5 mm, soit L/200 (ordre de grandeur des limites courantes L/200 a L/500, choisi pour
// l'exemple). Exemples : bois 20 mm sous 200 N -> 2,8 mm (validee) ; bois 10 mm sous 200 N -> 22,7 mm.
// Dessin : la courbure est exageree (echelle non lineaire, monotone) ; aucune valeur de fleche n'est ecrite.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["poutre-flexion"] = {
  dessiner(svg, valeurs) {
    const borne = (v, d, mini, maxi) => {
      const n = Number(v ?? d);
      return Math.min(maxi, Math.max(mini, Number.isFinite(n) ? n : d));
    };
    const charge = borne(valeurs.charge, 200, 0, 1000);
    const epaisseur = borne(valeurs.epaisseur, 20, 5, 40);
    const materiau = Math.round(borne(valeurs.materiau, 1, 1, 3));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 320");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";

    // --- Calcul de la fleche (mm) ---
    const MATERIAUX = { 1: ["bois", 11e9, "#B07A3E"], 2: ["aluminium", 69e9, "#9AA5B4"], 3: ["acier", 210e9, "#4A5563"] };
    const [nomMat, E, teinte] = MATERIAUX[materiau];
    const L = 1, b = 0.2, h = epaisseur / 1000;
    const I = (b * h ** 3) / 12;
    const fleche = (charge * L ** 3) / (48 * E * I) * 1000; // en mm
    const LIMITE = 5; // mm, L/200
    const depasse = fleche > LIMITE;
    // echelle d'affichage exageree et monotone : 0 -> 0 ; 5 mm (limite) -> 32 px ; tend vers 80 px
    const dessinee = (f) => (80 * f) / (f + 7.5);

    // --- Appuis et poutre ---
    const XA = 40, XB = 300, YP = 120;
    const ep = 4 + epaisseur * 0.55; // epaisseur dessinee (px) : 6,75 a 26
    for (const xa of [XA, XB]) {
      el("polygon", { points: `${xa},${YP + ep / 2} ${xa - 16},${YP + ep / 2 + 26} ${xa + 16},${YP + ep / 2 + 26}`, fill: GRIS });
      el("line", { x1: xa - 24, y1: YP + ep / 2 + 28, x2: xa + 24, y2: YP + ep / 2 + 28, stroke: GRIS, "stroke-width": 3 });
    }
    // poutre courbee : parabole de fleche d au milieu (forme tracee, pas la deformee exacte)
    const d = dessinee(fleche);
    const XM = (XA + XB) / 2;
    const debord = 0; // la poutre s'arrete sur les appuis (pas de porte-a-faux)
    const haut = `M${XA - debord},${YP - ep / 2} Q${XM},${YP - ep / 2 + 2 * d} ${XB + debord},${YP - ep / 2}`;
    const bas = `L${XB + debord},${YP + ep / 2} Q${XM},${YP + ep / 2 + 2 * d} ${XA - debord},${YP + ep / 2} Z`;
    el("path", { d: `${haut} ${bas}`, fill: depasse ? ROUGE : teinte, stroke: depasse ? ROUGE : ENCRE, "stroke-width": 2 });
    // position droite d'origine, en pointilles gris (pour voir la flexion)
    if (charge > 0) el("line", { x1: XA - debord, y1: YP, x2: XB + debord, y2: YP, stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "4 4" });
    // fleche maximale admise : pointilles orange sous le milieu, dessines par-dessus la poutre pour rester visibles
    const yLim = YP + ep / 2 + dessinee(LIMITE);
    el("line", { x1: XM - 40, y1: yLim, x2: XM + 40, y2: yLim, stroke: ORANGE, "stroke-width": 3, "stroke-dasharray": "6 4" });

    // --- Charge : fleche vers le bas dont la longueur suit la charge ---
    if (charge > 0) {
      const lg = 14 + (charge / 1000) * 50;
      const ySommet = YP - ep / 2 + d - 6;
      el("line", { x1: XM, y1: ySommet - lg, x2: XM, y2: ySommet - 10, stroke: BLEU, "stroke-width": 5 });
      el("path", { d: `M${XM},${ySommet} l-10,-14 h20 z`, fill: BLEU });
      el("text", { x: XM + 14, y: ySommet - lg + 12, "font-size": 14, fill: BLEU, "font-weight": "bold" }, "charge");
    }

    // --- Legende ---
    el("text", { x: 20, y: 236, "font-size": 14, fill: ENCRE }, "matériau :");
    el("rect", { x: 96, y: 224, width: 18, height: 16, rx: 3, fill: teinte, stroke: ENCRE, "stroke-width": 2 });
    el("text", { x: 122, y: 236, "font-size": 14, fill: ENCRE, "font-weight": "bold" }, nomMat);
    el("line", { x1: 20, y1: 256, x2: 50, y2: 256, stroke: ORANGE, "stroke-width": 3, "stroke-dasharray": "6 4" });
    el("text", { x: 58, y: 261, "font-size": 13, fill: ORANGE, "font-weight": "bold" }, "flèche maximale admise");
    el("text", { x: 20, y: 312, "font-size": 13, fill: GRIS }, "courbure exagérée pour être vue");
    el("text", { x: 20, y: 288, "font-size": 15, fill: depasse ? ROUGE : VERT, "font-weight": "bold" },
      charge === 0 ? "sans charge : poutre droite" : depasse ? "trop de flexion : non validée" : "flexion admise : validée");
    return { fleche, depasse: depasse ? 1 : 0 };
  },
};
