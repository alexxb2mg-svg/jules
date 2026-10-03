// Jules - gabarit "quadrilatere-deformable" : un quadrilatere dont on penche les cotes (angle en A) et dont on
// allonge deux cotes opposes ; il devient carre, rectangle, losange ou aucun des trois, et ses codages suivent :
// petit carre rouge = angle droit, memes petits traits orange = meme longueur. Aucun degre ni nom de figure ecrit.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["quadrilatere-deformable"] = {
  // dessiner(svg, valeurs) : angle en A de 60 a 120 (90 = droit), allonge de 0 a 3 (0 = quatre cotes egaux).
  dessiner(svg, valeurs) {
    const angle = Math.min(120, Math.max(60, Number(valeurs.angle ?? 90)));
    const allonge = Math.min(3, Math.max(0, Number(valeurs.allonge ?? 0)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const s = 120;                       // [AD] et [BC]
    const h = s + allonge * 35;          // [AB] et [DC] : 120 a 225 px
    const rad = (angle * Math.PI) / 180;
    const dx = s * Math.cos(rad), dy = s * Math.sin(rad);
    // Boite englobante centree sur (170, 165).
    const xmin = Math.min(0, dx), xmax = Math.max(h, h + dx);
    const ox = 170 - (xmin + xmax) / 2, oy = 165 + dy / 2;
    const A = { x: ox, y: oy }, B = { x: ox + h, y: oy };
    const C = { x: ox + h + dx, y: oy - dy }, D = { x: ox + dx, y: oy - dy };
    const P = [A, B, C, D];
    const centre = { x: (A.x + C.x) / 2, y: (A.y + C.y) / 2 };
    const f = (n) => n.toFixed(1);

    el("polygon", { points: P.map((p) => `${f(p.x)},${f(p.y)}`).join(" "), fill: "#EAF1FA", stroke: "#1F4E8C", "stroke-width": 4, "stroke-linejoin": "round" });

    // Angles droits : un petit carre rouge dans chaque coin (seulement si l'angle est droit).
    if (angle === 90) {
      const c = 16;
      P.forEach((p, i) => {
        const suiv = P[(i + 1) % 4], prec = P[(i + 3) % 4];
        const u = { x: (suiv.x - p.x) / Math.hypot(suiv.x - p.x, suiv.y - p.y), y: (suiv.y - p.y) / Math.hypot(suiv.x - p.x, suiv.y - p.y) };
        const v = { x: (prec.x - p.x) / Math.hypot(prec.x - p.x, prec.y - p.y), y: (prec.y - p.y) / Math.hypot(prec.x - p.x, prec.y - p.y) };
        el("path", {
          d: `M${f(p.x + c * u.x)},${f(p.y + c * u.y)} L${f(p.x + c * (u.x + v.x))},${f(p.y + c * (u.y + v.y))} L${f(p.x + c * v.x)},${f(p.y + c * v.y)}`,
          fill: "none", stroke: "#C8102E", "stroke-width": 3,
        });
      });
    }

    // Longueurs egales : memes petits traits orange. [AB] et [DC] : 1 trait ; [AD] et [BC] : 1 trait si les
    // quatre cotes sont egaux, sinon 2 traits.
    const traits = (p, q, n) => {
      const m = { x: (p.x + q.x) / 2, y: (p.y + q.y) / 2 };
      const l = Math.hypot(q.x - p.x, q.y - p.y);
      const u = { x: (q.x - p.x) / l, y: (q.y - p.y) / l };   // le long du cote
      const nn = { x: -u.y, y: u.x };                          // perpendiculaire
      for (let k = 0; k < n; k++) {
        const d = (k - (n - 1) / 2) * 9;
        const c = { x: m.x + d * u.x, y: m.y + d * u.y };
        el("line", { x1: f(c.x - 10 * nn.x), y1: f(c.y - 10 * nn.y), x2: f(c.x + 10 * nn.x), y2: f(c.y + 10 * nn.y), stroke: "#E07B00", "stroke-width": 3.5, "stroke-linecap": "round" });
      }
    };
    const nCotes = allonge === 0 ? 1 : 2;
    traits(A, B, 1); traits(D, C, 1);
    traits(A, D, nCotes); traits(B, C, nCotes);

    // Les sommets, nommes vers l'exterieur.
    ["A", "B", "C", "D"].forEach((t, i) => {
      const p = P[i];
      const l = Math.hypot(p.x - centre.x, p.y - centre.y);
      el("text", {
        x: f(Math.min(326, Math.max(14, p.x + 22 * (p.x - centre.x) / l))), y: f(p.y + 22 * (p.y - centre.y) / l + 6),
        "font-size": 18, "font-weight": 700, fill: "#14243B", "text-anchor": "middle", "font-family": "sans-serif",
      }, t);
    });
    return { angle, allonge };
  },
};
