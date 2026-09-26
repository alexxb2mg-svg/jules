// Jules - gabarit "probabilites-frequences" : frequence observee (simulation deterministe par
// graine fixe) qui se stabilise avec n, comparee a la probabilite theorique 0,5.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

// Suite pseudo-aleatoire deterministe (meme figure a chaque affichage : pas de Math.random()).
function _suitePile(n) {
  let graine = 42;
  const suite = [];
  for (let i = 0; i < n; i++) {
    graine = (graine * 1103515245 + 12345) % 2147483648;
    suite.push(graine / 2147483648 < 0.5 ? 1 : 0);
  }
  return suite;
}

window.GABARITS["probabilites-frequences"] = {
  dessiner(svg, valeurs) {
    const n = Math.max(1, Math.round(Number(valeurs.n ?? 50)));
    const suite = _suitePile(n);
    const points = [];
    let cumul = 0;
    for (let i = 0; i < n; i++) {
      cumul += suite[i];
      points.push(cumul / (i + 1));
    }
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      svg.appendChild(e);
      return e;
    };
    const largeur = 320, hauteur = 200, marge = 30;
    const X = (i) => marge + (i / (n - 1 || 1)) * (largeur - 2 * marge);
    const Y = (p) => hauteur - marge - p * (hauteur - 2 * marge);
    svg.setAttribute("viewBox", `0 0 ${largeur} ${hauteur}`);
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS
    el("line", { x1: marge, y1: Y(0.5), x2: largeur - marge, y2: Y(0.5), stroke: "#2B8A3E", "stroke-width": 1.5, "stroke-dasharray": "4 4" });
    el("text", { x: largeur - marge, y: Y(0.5) - 6, "font-size": 11, "text-anchor": "end", fill: "#2B8A3E" }).textContent = "0,5 (théorique)";
    el("line", { x1: marge, y1: hauteur - marge, x2: largeur - marge, y2: hauteur - marge, stroke: "#6B7686" });
    el("line", { x1: marge, y1: marge, x2: marge, y2: hauteur - marge, stroke: "#6B7686" });
    const chemin = points.map((p, i) => `${i === 0 ? "M" : "L"}${X(i)},${Y(p)}`).join(" ");
    el("path", { d: chemin, fill: "none", stroke: "#1F4E8C", "stroke-width": 2 });
    return { n, derniere: points[points.length - 1] };
  },
};
