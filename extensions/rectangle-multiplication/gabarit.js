// Jules - gabarit "rectangle-multiplication" : le produit (a + b) x (c + d) vu comme un rectangle quadrille de
// (a + b) lignes et (c + d) colonnes, decoupe en quatre morceaux colores : a x c (bleu), a x d (orange), b x c (vert),
// b x d (rouge). Avec b = 0 et d = 0 : un seul rectangle a x c (tables, CM1) ; avec d > 0 seulement : a x (c + d)
// coupe en deux (calcul mental 7 x 12 = 7 x 10 + 7 x 2, simple distributivite) ; avec b > 0 et d > 0 : double
// distributivite (3e). Les carreaux se comptent ; chaque morceau porte son calcul (« 7 x 10 ») mais aucun produit
// (aucun resultat) n'est ecrit.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["rectangle-multiplication"] = {
  // dessiner(svg, valeurs) : lignes a (1 a 10) + b (0 a 6), colonnes c (1 a 20) + d (0 a 10). Absentes : b = d = 0.
  dessiner(svg, valeurs) {
    const ent = (v, d, mini, maxi) => {
      const x = Number(v ?? d);
      return Math.min(maxi, Math.max(mini, Math.round(Number.isFinite(x) ? x : d)));
    };
    const a = ent(valeurs.a, 3, 1, 10);
    const b = ent(valeurs.b, 0, 0, 6);
    const c = ent(valeurs.c, 7, 1, 20);
    const d = ent(valeurs.d, 0, 0, 10);
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const f = (x) => x.toFixed(1);
    svg.setAttribute("viewBox", "0 0 340 340");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const ENCRE = "#14243B";
    const lignes = a + b, colonnes = c + d;
    // Une seule echelle, carreaux de 28 px au plus ; le rectangle tient dans 280 x 250 px.
    const u = Math.min(28, 280 / colonnes, 250 / lignes);
    const X0 = 44, Y0 = 62;
    const facteur = (p, q) => (q > 0 ? `(${p} + ${q})` : `${p}`);
    el("text", { x: 170, y: 22, "font-size": 16, "font-weight": "bold", fill: ENCRE, "text-anchor": "middle", "font-family": "sans-serif" },
      `${facteur(a, b)} × ${facteur(c, d)}`);

    // Les quatre morceaux : [premiere colonne, nb colonnes, premiere ligne, nb lignes, fond, trait].
    const morceaux = [
      [0, c, 0, a, "#D6E4F5", "#1F4E8C"],
      [c, d, 0, a, "#FBE3C7", "#E07B00"],
      [0, c, a, b, "#D8EDD9", "#2E7D32"],
      [c, d, a, b, "#F6D5DA", "#C8102E"],
    ];
    for (const [col, nc, lig, nl, fond, trait] of morceaux) {
      if (nc === 0 || nl === 0) continue;
      const x = X0 + col * u, y = Y0 + lig * u, w = nc * u, h = nl * u;
      el("rect", { x: f(x), y: f(y), width: f(w), height: f(h), fill: fond, stroke: "none" });
      for (let i = 1; i < nc; i++) el("line", { x1: f(x + i * u), y1: f(y), x2: f(x + i * u), y2: f(y + h), stroke: trait, "stroke-opacity": 0.35, "stroke-width": 1 });
      for (let j = 1; j < nl; j++) el("line", { x1: f(x), y1: f(y + j * u), x2: f(x + w), y2: f(y + j * u), stroke: trait, "stroke-opacity": 0.35, "stroke-width": 1 });
      el("rect", { x: f(x), y: f(y), width: f(w), height: f(h), fill: "none", stroke: trait, "stroke-width": 3 });
      // Le calcul du morceau, s'il y a la place (fond blanc pour rester lisible sur le quadrillage).
      const texte = `${nl} × ${nc}`;
      const lt = texte.length * 8.5 + 8;
      if (w >= lt + 4 && h >= 24) {
        el("rect", { x: f(x + w / 2 - lt / 2), y: f(y + h / 2 - 11), width: f(lt), height: 22, rx: 4, fill: "#FFFFFF", "fill-opacity": 0.9 });
        el("text", { x: f(x + w / 2), y: f(y + h / 2 + 5), "font-size": 15, "font-weight": "bold", fill: trait, "text-anchor": "middle", "font-family": "sans-serif" }, texte);
      }
    }

    // Les cotes : colonnes c puis d au-dessus, lignes a puis b a gauche (accolades simples).
    const cote = (x1, y1, x2, y2, texte, tx, ty, ancre) => {
      el("line", { x1: f(x1), y1: f(y1), x2: f(x2), y2: f(y2), stroke: ENCRE, "stroke-width": 2 });
      const dx = y1 === y2 ? 0 : 5, dy = y1 === y2 ? 5 : 0;
      el("line", { x1: f(x1 - dx), y1: f(y1 - dy), x2: f(x1 + dx), y2: f(y1 + dy), stroke: ENCRE, "stroke-width": 2 });
      el("line", { x1: f(x2 - dx), y1: f(y2 - dy), x2: f(x2 + dx), y2: f(y2 + dy), stroke: ENCRE, "stroke-width": 2 });
      el("text", { x: f(tx), y: f(ty), "font-size": 14, fill: ENCRE, "text-anchor": ancre, "font-family": "sans-serif" }, texte);
    };
    const yh = Y0 - 10;
    cote(X0 + 2, yh, X0 + c * u - 2, yh, String(c), X0 + (c * u) / 2, yh - 7, "middle");
    if (d > 0) cote(X0 + c * u + 2, yh, X0 + colonnes * u - 2, yh, String(d), X0 + c * u + (d * u) / 2, yh - 7, "middle");
    const xg = X0 - 10;
    cote(xg, Y0 + 2, xg, Y0 + a * u - 2, String(a), xg - 6, Y0 + (a * u) / 2 + 5, "end");
    if (b > 0) cote(xg, Y0 + a * u + 2, xg, Y0 + lignes * u - 2, String(b), xg - 6, Y0 + a * u + (b * u) / 2 + 5, "end");
    return { a, b, c, d, u };
  },
};
