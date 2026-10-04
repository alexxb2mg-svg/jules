// Jules - gabarit "homothetie-rotation" : un drapeau quadrille (bleu), le centre O (rouge) et son image (verte)
// par l'homothetie de centre O et de rapport k suivie de la rotation de centre O et d'angle `angle` (sens inverse
// des aiguilles d'une montre). L'image est quadrillee avec des carreaux de la taille de ceux du drapeau : on compte
// que l'aire est multipliee par k² (4 carreaux pour 1 quand k = 2), les longueurs par |k|. Aucune valeur ecrite.
// Faits (programme de mathematiques du cycle 4, BO n° 31 du 30/07/2020, « Espace et geometrie », et Eduscol,
// ressources cycle 4 « Transformations ») : une homothetie de rapport k multiplie les longueurs par |k| et les aires
// par k² ; k < 0 place l'image de l'autre cote de O ; une rotation conserve longueurs, angles et aires ;
// l'homothetie de rapport -1 est la symetrie centrale de centre O (rotation de 180°). Homothetie et rotation de
// meme centre commutent : l'ordre n'importe pas.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["homothetie-rotation"] = {
  // dessiner(svg, valeurs) : k = rapport d'homothetie (-2 a 3), angle = rotation en degres (0 a 360).
  dessiner(svg, valeurs) {
    const borne = (v, defaut, mini, maxi) => {
      const x = Number(v ?? defaut);
      return Math.min(maxi, Math.max(mini, Number.isFinite(x) ? x : defaut));
    };
    const k = borne(valeurs.k, 2, -2, 3);
    const angle = borne(valeurs.angle, 0, 0, 360);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const cle in attrs) e.setAttribute(cle, attrs[cle]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const t = (angle * Math.PI) / 180;
    const image = ([x, y]) => [k * (x * Math.cos(t) - y * Math.sin(t)), k * (x * Math.sin(t) + y * Math.cos(t))];

    // Le drapeau : rectangle 3 x 2 carreaux, hampe a gauche qui descend d'un carreau ; A = coin haut droit.
    const coins = [[1, 0], [4, 0], [4, 2], [1, 2]];
    const hampe = [[1, -1], [1, 0]];
    const A = [4, 2];

    // Repere (y vers le haut) cadre sur O, le drapeau et son image : un carreau = c px (30 au plus), le tout
    // centre dans le cadre ; les deux drapeaux gardent leurs tailles relatives.
    // (l'arc de rotation, 34 px autour de O, doit tenir aussi : deux passes, c ne fait que diminuer)
    const figures = [[0, 0], ...coins, ...hampe, ...coins.map(image), ...hampe.map(image)];
    let c = 30, x0 = 0, x1 = 0, y0 = 0, y1 = 0;
    for (let passe = 0; passe < 3; passe++) {
      const m = 44 / c;
      const tous = [...figures, [-m, -m], [m, m]];
      const xs = tous.map((p) => p[0]), ys = tous.map((p) => p[1]);
      [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
      c = Math.min(30, 300 / Math.max(x1 - x0, 1e-9), 300 / Math.max(y1 - y0, 1e-9));
    }
    const O = { x: 170 - c * (x0 + x1) / 2, y: 170 + c * (y0 + y1) / 2 };
    const ecran = ([x, y]) => [O.x + c * x, O.y - c * y];
    const pts = (liste) => liste.map((p) => ecran(p).map((v) => v.toFixed(1)).join(",")).join(" ");

    const segment = (p, q, attrs) => {
      const [x1, y1] = ecran(p), [x2, y2] = ecran(q);
      el("line", { x1, y1, x2, y2, ...attrs });
    };
    // Carreaux de la taille d'ORIGINE, traces dans un rectangle (image ou non) donne par ses 4 coins.
    const quadriller = (q, largeur, hauteur, couleur) => {
      const mix = (u, v) => [
        q[0][0] + u * (q[1][0] - q[0][0]) + v * (q[3][0] - q[0][0]),
        q[0][1] + u * (q[1][1] - q[0][1]) + v * (q[3][1] - q[0][1]),
      ];
      for (let i = 1; i < largeur - 1e-9; i++) segment(mix(i / largeur, 0), mix(i / largeur, 1), { stroke: couleur, "stroke-width": 2, "stroke-opacity": 0.55 });
      for (let j = 1; j < hauteur - 1e-9; j++) segment(mix(0, j / hauteur), mix(1, j / hauteur), { stroke: couleur, "stroke-width": 2, "stroke-opacity": 0.55 });
    };
    const drapeau = (q, h, largeur, hauteur, couleur) => {
      el("polygon", { points: pts(q), fill: couleur, "fill-opacity": 0.16, stroke: "none" });
      quadriller(q, largeur, hauteur, couleur);
      el("polygon", { points: pts(q), fill: "none", stroke: couleur, "stroke-width": 3, "stroke-linejoin": "round" });
      segment(h[0], h[1], { stroke: couleur, "stroke-width": 3, "stroke-linecap": "round" });
    };

    // Les demi-droites issues de O vers A et vers A' (pointilles gris).
    const Ai = image(A);
    const rayon = (p) => segment([0, 0], p, { stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "6 5" });
    rayon(A);
    if (Math.abs(k) > 1e-9) rayon(Ai);

    // L'arc du tour effectif (rotation, plus un demi-tour si k < 0), du cote de A vers A'.
    const tour = (((angle + (k < 0 ? 180 : 0)) % 360) + 360) % 360;
    if (Math.abs(k) > 1e-9 && tour > 1e-9) {
      const r = 34, a0 = Math.atan2(A[1], A[0]), a1 = a0 + (tour * Math.PI) / 180;
      const p = (a) => [O.x + r * Math.cos(a), O.y - r * Math.sin(a)];
      const [x0, y0] = p(a0), [x1, y1] = p(a1);
      el("path", {
        d: `M ${x0.toFixed(1)} ${y0.toFixed(1)} A ${r} ${r} 0 ${tour > 180 ? 1 : 0} 0 ${x1.toFixed(1)} ${y1.toFixed(1)}`,
        fill: "none", stroke: "#E07B00", "stroke-width": 3,
      });
      // pointe de fleche tangente a l'arc, au bout (sens inverse des aiguilles)
      const tx = -Math.sin(a1), ty = Math.cos(a1); // tangente (repere y vers le haut)
      const nx = Math.cos(a1), ny = Math.sin(a1);
      const sommet = [x1 + 8 * tx, y1 - 8 * ty];
      const g = [x1 - 2 * tx + 6 * nx, y1 + 2 * ty - 6 * ny];
      const d = [x1 - 2 * tx - 6 * nx, y1 + 2 * ty + 6 * ny];
      el("polygon", { points: [sommet, g, d].map((q) => q.map((v) => v.toFixed(1)).join(",")).join(" "), fill: "#E07B00" });
    }

    // Le drapeau d'origine (bleu) puis son image (verte), quadrillee en carreaux d'origine.
    drapeau(coins, hampe, 3, 2, "#1F4E8C");
    if (Math.abs(k) > 1e-9) {
      drapeau(coins.map(image), hampe.map(image), 3 * Math.abs(k), 2 * Math.abs(k), "#2E7D32");
    }

    // Les points O, A, A' et leurs noms : O a l'oppose des deux drapeaux ; halo blanc pour rester lisible sur un trait.
    const centre = [2.5, 1];
    const nommer = (p, dir, nom, couleur) => {
      const [x, y] = ecran(p);
      el("circle", { cx: x, cy: y, r: 5, fill: couleur });
      const n = Math.hypot(dir[0], dir[1]);
      const ux = n > 1e-9 ? dir[0] / n : -0.7, uy = n > 1e-9 ? dir[1] / n : -0.7;
      el("text", {
        x: Math.min(326, Math.max(14, x + 17 * ux)), y: Math.min(332, Math.max(18, y - 17 * uy + 6)),
        "font-size": 16, "font-weight": 700, fill: couleur, "text-anchor": "middle", "font-family": "sans-serif",
        stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke", "stroke-linejoin": "round",
      }, nom);
    };
    // A et A' : perpendiculaire a la demi-droite [OA) (pas de pointilles sous le nom), du cote oppose au drapeau.
    const cote = (p, c) => {
      const perp = [p[1], -p[0]];
      return perp[0] * (p[0] - c[0]) + perp[1] * (p[1] - c[1]) >= 0 ? perp : [-perp[0], -perp[1]];
    };
    nommer(A, cote(A, centre), "A", "#1F4E8C");
    if (Math.abs(k) > 1e-9) nommer(Ai, cote(Ai, image(centre)), "A'", "#2E7D32");
    const ci = Math.abs(k) > 1e-9 ? image(centre) : [0, 0];
    nommer([0, 0], [-(centre[0] + ci[0]), -(centre[1] + ci[1])], "O", "#C8102E");
    return { k, angle };
  },
};
