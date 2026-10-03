// Jules - gabarit "courbe-point-mobile" : courbe de f(x) = ax² + bx + c (a = 0 : une droite) et un point
// mobile d'abscisse x. Pointilles bleus vers x (la variable, axe horizontal), verts vers f(x) (l'image, axe
// vertical) ; ligne orange a la hauteur f(x) avec l'autre antecedent s'il existe ; petit tableau de valeurs
// (x de -3 a 3) dont la colonne de x s'allume. Curseurs x, courbure (a), pente (b, pente de la courbe en 0)
// et hauteur (c = f(0), ou la courbe coupe l'axe vertical). Noms en mots et non a, b, c : dans les fiches de
// fonctions, a et b designent deja un antecedent et son image (f(a) = b).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["courbe-point-mobile"] = {
  dessiner(svg, valeurs) {
    const borne = (v, defaut, min, max) => {
      const n = Number(v ?? defaut);
      return Math.min(max, Math.max(min, Number.isFinite(n) ? n : defaut));
    };
    const x = borne(valeurs.x, 1, -4, 4);
    const a = borne(valeurs.courbure, 0.5, -1, 1);
    const b = borne(valeurs.pente, 0, -3, 3);
    const c = borne(valeurs.hauteur, -2, -4, 4);
    const f = (t) => a * t * t + b * t + c;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const fmt = (n) => String(Math.round(n * 1000) / 1000).replace(".", ",").replace("-", "\u2212");
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";
    const halo = { stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke", "stroke-linejoin": "round" };

    // Repere : 1 unite = 30 px en x (-5,3 a 5,3), 20 px en y (-6 a 6) ; origine en (170 ; 130).
    const OX = 170, OY = 130, UX = 30, UY = 20, XMAX = 5.3, YMAX = 6;
    const X = (t) => OX + t * UX;
    const Y = (y) => OY - y * UY;
    svg.setAttribute("viewBox", "0 0 340 340");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    for (let i = -5; i <= 5; i++) el("line", { x1: X(i), y1: Y(YMAX), x2: X(i), y2: Y(-YMAX), stroke: "#EEF1F5", "stroke-width": 1 });
    for (let j = -6; j <= 6; j++) el("line", { x1: X(-XMAX), y1: Y(j), x2: X(XMAX), y2: Y(j), stroke: "#EEF1F5", "stroke-width": 1 });
    el("line", { x1: X(-XMAX), y1: OY, x2: X(XMAX), y2: OY, stroke: GRIS, "stroke-width": 2 });
    el("line", { x1: OX, y1: Y(YMAX), x2: OX, y2: Y(-YMAX), stroke: GRIS, "stroke-width": 2 });
    const y0 = f(x);
    const dedans = Math.abs(y0) <= YMAX;
    // l'autre solution de f(t) = f(x) (symetrique de x par rapport au sommet), s'il y en a une
    const autre = a !== 0 ? -b / a - x : null;
    const autreVisible = dedans && autre !== null && Math.abs(autre - x) > 1e-9 && Math.abs(autre) <= XMAX;
    // Courbe, coupee proprement aux bords haut et bas du cadre.
    let d = "", dansCadre = false, avant = null;
    const pt = (t, y) => `${X(t).toFixed(1)},${Y(y).toFixed(1)}`;
    for (let i = 0; i <= 212; i++) {
      const t = -XMAX + i * 0.05, y = f(t);
      const ici = Math.abs(y) <= YMAX;
      if (avant && ici !== dansCadre) {
        const bord = (ici ? avant.y : y) > 0 ? YMAX : -YMAX; // point de sortie ou d'entree sur le bord
        const tb = avant.t + ((bord - avant.y) / (y - avant.y)) * (t - avant.t);
        d += ici ? `M${pt(tb, bord)} L${pt(t, y)} ` : `L${pt(tb, bord)} `;
      } else if (ici) {
        d += (dansCadre && avant ? "L" : "M") + pt(t, y) + " ";
      }
      dansCadre = ici;
      avant = { t, y };
    }
    if (d) el("path", { d, fill: "none", stroke: ENCRE, "stroke-width": 3, "stroke-linejoin": "round" });
    // graduations ecrites apres la courbe (halo blanc : la courbe ne les masque pas)
    for (const g of [-4, -2, 2, 4]) {
      const cache = Math.abs(g - x) < 0.75 || (autreVisible && Math.abs(g - autre) < 0.75 && Math.abs(y0) < 1.2);
      if (!cache) el("text", { x: X(g), y: OY + 16, "font-size": 13, "text-anchor": "middle", fill: GRIS, ...halo }, fmt(g));
      if (!dedans || Math.abs(g - y0) >= 1.1) el("text", { x: OX - 6, y: Y(g) + 5, "font-size": 13, "text-anchor": "end", fill: GRIS, ...halo }, fmt(g));
    }

    if (dedans) {
      // Ligne orange a la hauteur f(x) : tous les points de la courbe qui ont cette image.
      el("line", { x1: X(-XMAX), y1: Y(y0), x2: X(XMAX), y2: Y(y0), stroke: ORANGE, "stroke-width": 2, opacity: 0.55 });
      if (autreVisible) {
        el("line", { x1: X(autre), y1: OY, x2: X(autre), y2: Y(y0), stroke: ORANGE, "stroke-width": 2, "stroke-dasharray": "5 4" });
        el("circle", { cx: X(autre), cy: Y(y0), r: 6, fill: "#FFFFFF", stroke: ORANGE, "stroke-width": 3 });
      }
      el("line", { x1: X(x), y1: OY, x2: X(x), y2: Y(y0), stroke: BLEU, "stroke-width": 2.5, "stroke-dasharray": "6 4" });
      el("line", { x1: X(x), y1: Y(y0), x2: OX, y2: Y(y0), stroke: VERT, "stroke-width": 2.5, "stroke-dasharray": "6 4" });
      el("circle", { cx: OX, cy: Y(y0), r: 5, fill: VERT });
      // valeur de f(x) sur l'axe vertical, du cote oppose au point et loin de l'axe horizontal (dessus si
      // f(x) >= 0, dessous sinon), retournee pres des bords haut et bas du cadre
      const dessus = (y0 >= 0 && y0 <= 5) || y0 < -5;
      el("text", { x: x >= 0 ? OX - 8 : OX + 8, y: Y(y0) + (dessus ? -10 : 20), "font-size": 15, "font-weight": 700,
        "text-anchor": x >= 0 ? "end" : "start", fill: VERT, ...halo }, fmt(y0));
      el("circle", { cx: X(x), cy: Y(y0), r: 7, fill: ROUGE, stroke: "#FFFFFF", "stroke-width": 2 });
    } else {
      // Le point sort du cadre : pointilles jusqu'au bord et fleche vers le haut ou le bas.
      const bord = y0 > 0 ? YMAX : -YMAX, s = y0 > 0 ? -1 : 1;
      el("line", { x1: X(x), y1: OY, x2: X(x), y2: Y(bord), stroke: BLEU, "stroke-width": 2.5, "stroke-dasharray": "6 4" });
      el("polygon", { points: `${X(x)},${Y(bord) + s * 2} ${X(x) - 8},${Y(bord) - s * 12} ${X(x) + 8},${Y(bord) - s * 12}`, fill: ROUGE });
    }
    el("circle", { cx: X(x), cy: OY, r: 5, fill: BLEU });
    el("text", { x: X(x), y: dedans && y0 < 0 ? OY - 8 : OY + 18, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: BLEU, ...halo }, fmt(x));

    // Tableau de valeurs de -3 a 3 : la colonne de x s'allume.
    const T0 = 264, H = 32, G = 4, LG = 44, LC = 41;
    const col = Math.round(x) === x && Math.abs(x) <= 3 ? x + 3 : -1;
    if (col >= 0) el("rect", { x: G + LG + col * LC, y: T0, width: LC, height: 2 * H, fill: "#DCE7F5", stroke: BLEU, "stroke-width": 2.5 });
    el("rect", { x: G, y: T0, width: LG + 7 * LC, height: 2 * H, fill: "none", stroke: GRIS, "stroke-width": 1.5 });
    el("line", { x1: G, y1: T0 + H, x2: G + LG + 7 * LC, y2: T0 + H, stroke: GRIS, "stroke-width": 1.5 });
    for (let k = 0; k <= 6; k++) el("line", { x1: G + LG + k * LC, y1: T0, x2: G + LG + k * LC, y2: T0 + 2 * H, stroke: GRIS, "stroke-width": 1.5 });
    el("text", { x: G + LG / 2, y: T0 + 21, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: BLEU }, "x");
    el("text", { x: G + LG / 2, y: T0 + H + 21, "font-size": 15, "font-weight": 700, "text-anchor": "middle", fill: VERT }, "f(x)");
    for (let k = 0; k < 7; k++) {
      const cx = G + LG + k * LC + LC / 2, fort = k === col ? 700 : 400;
      el("text", { x: cx, y: T0 + 21, "font-size": 14, "font-weight": fort, "text-anchor": "middle", fill: BLEU }, fmt(k - 3));
      el("text", { x: cx, y: T0 + H + 21, "font-size": 13, "font-weight": fort, "text-anchor": "middle", fill: VERT }, fmt(f(k - 3)));
    }
    return { x, courbure: a, pente: b, hauteur: c, image: y0 };
  },
};
