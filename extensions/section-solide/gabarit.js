// Jules - gabarit "section-solide" : un solide en perspective cavaliere (pave droit, cylindre, cone ou pyramide a
// base carree) coupe par un plan parallele a sa base a la hauteur choisie ; la section est coloriee (orange) dans le
// solide et redessinee a droite en vraie grandeur, posee sur le contour de la base (gris, pointilles) pour comparer.
// Aucune longueur ni aire n'est ecrite.
// Faits (programme de mathematiques du cycle 4, BO n° 31 du 30/07/2020 : « sections planes de solides » en 3e ;
// Eduscol, ressource « Sections de solides ») : la section d'un pave droit ou d'un cylindre par un plan parallele
// a la base est un rectangle ou un disque identique a la base ; celle d'un cone ou d'une pyramide est une reduction
// de la base, de rapport (hauteur restante / hauteur totale), image de la base par l'homothetie de centre le sommet.
// Perspective cavaliere pour le pave et la pyramide (fuyantes a 45°, coefficient 0,5) ; cylindre et cone avec la
// base en ellipse, dessin d'usage au college ; les aretes cachees en pointilles.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["section-solide"] = {
  // dessiner(svg, valeurs) : solide = 1 pave droit, 2 cylindre, 3 cone, 4 pyramide ; hauteur = position du plan de
  // coupe, en fraction de la hauteur du solide (0 = base, 1 = haut).
  dessiner(svg, valeurs) {
    const borne = (v, defaut, mini, maxi) => {
      const x = Number(v ?? defaut);
      return Math.min(maxi, Math.max(mini, Number.isFinite(x) ? x : defaut));
    };
    const solide = Math.round(borne(valeurs.solide, 3, 1, 4));
    const h = borne(valeurs.hauteur, 0.5, 0, 1);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 250");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const f = (v) => v.toFixed(1);
    const pts = (l) => l.map((p) => `${f(p[0])},${f(p[1])}`).join(" ");
    const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
    const vers = (a, b, t) => [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])];
    const fuite = (prof) => [prof * 0.5 * Math.SQRT1_2, -prof * 0.5 * Math.SQRT1_2]; // cavaliere 45°, 0,5
    const ORANGE = "#E07B00", BLEU = "#1F4E8C", GRIS = "#6B7686";
    const arete = (a, b, cachee) => el("line", {
      x1: f(a[0]), y1: f(a[1]), x2: f(b[0]), y2: f(b[1]), stroke: BLEU, "stroke-width": cachee ? 2 : 3,
      "stroke-linecap": "round", ...(cachee ? { "stroke-dasharray": "6 5" } : {}),
    });
    const section = (forme) => el(forme.nom, { ...forme.attrs, fill: ORANGE, "fill-opacity": 0.5, stroke: ORANGE, "stroke-width": 3 });
    const demiEllipse = (c, rx, ry, haut, cachee) => {
      // moitie haute (balayage vers le haut) ou basse d'une ellipse horizontale
      el("path", {
        d: `M ${f(c[0] - rx)} ${f(c[1])} A ${f(rx)} ${f(ry)} 0 0 ${haut ? 1 : 0} ${f(c[0] + rx)} ${f(c[1])}`,
        fill: "none", stroke: BLEU, "stroke-width": cachee ? 2 : 3, ...(cachee ? { "stroke-dasharray": "6 5" } : {}),
      });
    };

    const noms = { 1: "pavé droit", 2: "cylindre", 3: "cône", 4: "pyramide" };
    // vraie grandeur, a droite : contour de la base en gris pointille, section en orange
    const VG = { x: 272, y: 132 };
    let base, coupe;

    if (solide === 1) {
      const W = 110, D = 70, H = 120, F = [25, 215], dv = fuite(D);
      const bas = [F, add(F, [W, 0]), add(add(F, [W, 0]), dv), add(F, dv)];
      const haut = bas.map((p) => add(p, [0, -H]));
      section({ nom: "polygon", attrs: { points: pts(bas.map((p) => add(p, [0, -H * h]))) } });
      arete(bas[3], bas[0], true); arete(bas[3], bas[2], true); arete(bas[3], haut[3], true);
      arete(bas[0], bas[1]); arete(bas[1], bas[2]);
      for (let i = 0; i < 3; i++) arete(bas[i], haut[i]);
      for (let i = 0; i < 4; i++) arete(haut[i], haut[(i + 1) % 4]);
      base = { nom: "rect", attrs: { x: VG.x - W / 2, y: VG.y - D / 2, width: W, height: D } };
      coupe = base;
    } else if (solide === 2 || solide === 3) {
      const R = 55, ry = 18, H = solide === 2 ? 120 : 130, C0 = [80, 205], S = [80, 205 - H];
      if (solide === 2) {
        const c = [80, 205 - H * h];
        section({ nom: "ellipse", attrs: { cx: f(c[0]), cy: f(c[1]), rx: R, ry } });
        demiEllipse(C0, R, ry, true, true); demiEllipse(C0, R, ry, false, false);
        arete([C0[0] - R, C0[1]], [S[0] - R, S[1]]); arete([C0[0] + R, C0[1]], [S[0] + R, S[1]]);
        el("ellipse", { cx: S[0], cy: S[1], rx: R, ry, fill: "none", stroke: BLEU, "stroke-width": 3 });
        coupe = { nom: "circle", attrs: { cx: VG.x, cy: VG.y, r: R } };
      } else {
        const t = 1 - h, c = vers(S, C0, t);
        if (t > 1e-9) section({ nom: "ellipse", attrs: { cx: f(c[0]), cy: f(c[1]), rx: f(R * t), ry: f(ry * t) } });
        else el("circle", { cx: f(S[0]), cy: f(S[1]), r: 5, fill: ORANGE });
        demiEllipse(C0, R, ry, true, true); demiEllipse(C0, R, ry, false, false);
        arete([C0[0] - R, C0[1]], S); arete([C0[0] + R, C0[1]], S);
        coupe = t > 1e-9 ? { nom: "circle", attrs: { cx: VG.x, cy: VG.y, r: f(R * t) } } : null;
      }
      base = { nom: "circle", attrs: { cx: VG.x, cy: VG.y, r: R } };
    } else {
      const C = 90, H = 130, F = [25, 215], dv = fuite(C);
      const bas = [F, add(F, [C, 0]), add(add(F, [C, 0]), dv), add(F, dv)];
      const centre = add(add(F, [C / 2, 0]), [dv[0] / 2, dv[1] / 2]);
      const S = add(centre, [0, -H]);
      const t = 1 - h;
      if (t > 1e-9) section({ nom: "polygon", attrs: { points: pts(bas.map((p) => vers(S, p, t))) } });
      else el("circle", { cx: f(S[0]), cy: f(S[1]), r: 5, fill: ORANGE });
      arete(bas[3], bas[0], true); arete(bas[3], bas[2], true); arete(bas[3], S, true);
      arete(bas[0], bas[1]); arete(bas[1], bas[2]);
      for (let i = 0; i < 3; i++) arete(bas[i], S);
      base = { nom: "rect", attrs: { x: VG.x - C / 2, y: VG.y - C / 2, width: C, height: C } };
      coupe = t > 1e-9 ? { nom: "rect", attrs: { x: f(VG.x - (C * t) / 2), y: f(VG.y - (C * t) / 2), width: f(C * t), height: f(C * t) } } : null;
    }

    // Vraie grandeur : la base (contour gris) puis la section (orange) ; un point si la coupe passe par le sommet.
    el("text", { x: VG.x, y: 30, "font-size": 14, "font-weight": 700, fill: "#14243B", "text-anchor": "middle", "font-family": "sans-serif" }, "vraie grandeur");
    if (coupe) el(coupe.nom, { ...coupe.attrs, fill: ORANGE, "fill-opacity": 0.5, stroke: ORANGE, "stroke-width": 3 });
    else el("circle", { cx: VG.x, cy: VG.y, r: 5, fill: ORANGE });
    el(base.nom, { ...base.attrs, fill: "none", stroke: GRIS, "stroke-width": 2, "stroke-dasharray": "6 5" });
    el("text", { x: 240, y: 232, "font-size": 14, "font-weight": 700, fill: ORANGE, "text-anchor": "middle", "font-family": "sans-serif" }, "section");
    el("text", { x: 310, y: 232, "font-size": 14, fill: GRIS, "text-anchor": "middle", "font-family": "sans-serif" }, "base");
    el("text", { x: 95, y: 242, "font-size": 14, "font-weight": 700, fill: BLEU, "text-anchor": "middle", "font-family": "sans-serif" }, noms[solide]);
    return { solide, hauteur: h };
  },
};
