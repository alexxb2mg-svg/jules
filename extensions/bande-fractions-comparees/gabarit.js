// Jules - gabarit "bande-fractions-comparees" : deux fractions de meme denominateur d, l'une sous l'autre,
// sur des bandes de meme longueur (1 bande = 1 unite) : n parts pour la premiere, n + ecart pour la seconde ;
// une troisieme ligne les met bout a bout (la somme). Les parts gardent leur taille : seul leur nombre change.
// La figure n'ecrit aucune fraction : l'eleve compare et compte les parts lui-meme.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["bande-fractions-comparees"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const x = Math.round(Number(v ?? defaut));
      return Math.min(max, Math.max(min, Number.isFinite(x) ? x : defaut));
    };
    const d = entier(valeurs.d, 8, 1, 12);
    const n = entier(valeurs.n, 5, 0, 24);
    const ecart = entier(valeurs.ecart, -3, -24, 24);
    const m = Math.max(0, n + ecart); // jamais moins de 0 part
    const somme = n + m;
    const unites = Math.max(1, Math.ceil(somme / d));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const noeud = document.createElementNS(NS, nom);
      for (const cle in attrs) noeud.setAttribute(cle, attrs[cle]);
      if (texte !== undefined) noeud.textContent = texte;
      svg.appendChild(noeud);
      return noeud;
    };
    svg.setAttribute("viewBox", "0 0 340 270");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const X0 = 20, L = 300, H = 40;
    const part = L / (unites * d);
    const ligne = (y, titre, morceaux) => {
      // pastilles de couleur devant le titre : une couleur = une fraction
      morceaux.forEach(([, couleur], i) => {
        el("rect", { x: X0 + i * 18, y: y - 21, width: 14, height: 14, fill: couleur, "fill-opacity": 0.85 });
      });
      el("text", { x: X0 + morceaux.length * 18 + 2, y: y - 9, "font-size": 14, fill: "#14243B", "font-weight": "bold" }, titre);
      let debut = 0;
      for (const [nombre, couleur] of morceaux) {
        if (nombre > 0) {
          el("rect", { x: X0 + debut * part, y, width: nombre * part, height: H, fill: couleur, "fill-opacity": 0.85 });
        }
        debut += nombre;
      }
      for (let j = 1; j < unites * d; j++) {
        const bord = j % d === 0;
        el("line", {
          x1: X0 + j * part, y1: bord ? y - 4 : y, x2: X0 + j * part, y2: bord ? y + H + 4 : y + H,
          stroke: bord ? "#14243B" : "#6B7686", "stroke-width": bord ? 4 : 2,
        });
      }
      el("rect", { x: X0, y, width: L, height: H, fill: "none", stroke: "#14243B", "stroke-width": 2.5 });
    };
    ligne(34, "1re fraction", [[n, "#1F4E8C"]]);
    ligne(110, "2e fraction", [[m, "#E07B00"]]);
    ligne(186, "Les deux bout à bout", [[n, "#1F4E8C"], [m, "#E07B00"]]);
    // graduation des unites sous la derniere ligne : 0, 1, 2...
    const pas = unites > 6 ? 2 : 1;
    for (let u = 0; u <= unites; u += pas) {
      el("text", {
        x: X0 + u * d * part, y: 248, "font-size": 14, fill: "#14243B",
        "text-anchor": u === 0 ? "start" : u === unites ? "end" : "middle",
      }, String(u));
    }
    if (n + ecart < 0) {
      el("text", { x: 320, y: 102, "font-size": 13, "text-anchor": "end", fill: "#6B7686" }, "pas moins de 0 part");
    }
    return { d, n, ecart, m, somme, unites };
  },
};
