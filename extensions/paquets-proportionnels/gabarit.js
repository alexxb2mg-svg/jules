// Jules - gabarit "paquets-proportionnels" : deux rangees de paquets liees. En haut, des paquets de a (premiere
// grandeur, par exemple 4 personnes) ; en bas, autant de paquets de b (seconde grandeur, par exemple 250 g).
// La valeur fois donne le nombre de paquets (0,25 a 4) : un paquet coupe en 4 montre un quart, une moitie,
// trois quarts. Les deux rangees ont toujours le meme nombre de paquets : c'est la proportionnalite.
// Les totaux ne sont pas ecrits : l'eleve les calcule (« 3 paquets de 250 g »).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["paquets-proportionnels"] = {
  dessiner(svg, valeurs) {
    const a = Number(valeurs.a ?? 4);
    const b = Number(valeurs.b ?? 250);
    const fois = Math.min(4, Math.max(0.25, Math.round(Number(valeurs.fois ?? 1) * 4) / 4));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      if (texte !== undefined) e.textContent = texte; // texte brut, jamais interprete
      svg.appendChild(e);
      return e;
    };
    const nombre = (n) => String(n).replace(".", ",");
    svg.setAttribute("viewBox", "0 0 340 300");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // Nombre de paquets en mots (quart, demi, trois quarts), sans calcul de total.
    const entiers = Math.floor(fois), quarts = Math.round((fois - entiers) * 4);
    const titre = entiers === 0
      ? ["", "un quart de paquet", "un demi-paquet", "trois quarts de paquet"][quarts]
      : `${entiers} paquet${entiers > 1 ? "s" : ""}${["", " et un quart", " et demi", " et trois quarts"][quarts]}`;

    // Une rangee : paquets pleins, puis le paquet entame (contour pointille, seule la part prise est coloriee).
    const L = 66, H = 66, GAP = 10;
    const nbCases = Math.ceil(fois);
    const x0 = (340 - (nbCases * L + (nbCases - 1) * GAP)) / 2;
    const rangee = (y, contenu, trait, fond) => {
      for (let i = 0; i < nbCases; i++) {
        const x = x0 + i * (L + GAP);
        const part = Math.min(1, fois - i); // 1 = paquet entier
        if (part < 1) {
          el("rect", { x, y, width: L, height: H, rx: 8, fill: "#FFFFFF", stroke: trait, "stroke-width": 2, "stroke-dasharray": "5 4" });
          el("rect", { x, y, width: L * part, height: H, rx: 8, fill: fond, stroke: trait, "stroke-width": 3 });
          // Les coupes en quarts par-dessus : on voit combien de quarts sont pris.
          for (let k = 1; k < 4; k++) {
            el("line", { x1: x + (k * L) / 4, y1: y + 4, x2: x + (k * L) / 4, y2: y + H - 4, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "3 3" });
          }
        } else {
          el("rect", { x, y, width: L, height: H, rx: 8, fill: fond, stroke: trait, "stroke-width": 3 });
        }
        // Le contenu d'un paquet entier est ecrit sur chaque paquet entier (donnee, pas un resultat) ; le paquet
        // entame n'a pas de nombre : ce qu'il contient est une part a calculer.
        if (part === 1) el("text", { x: x + L / 2, y: y + H / 2 + 7, "font-size": contenu.length > 3 ? 17 : 20, "font-weight": 700, "text-anchor": "middle", fill: "#14243B" }, contenu);
      }
    };
    const yHaut = 60, yBas = 196;
    rangee(yHaut, nombre(a), "#1F4E8C", "#C9DAF0");
    rangee(yBas, nombre(b), "#E07B00", "#FBDDB7");

    // Liens : chaque paquet du haut va avec un paquet du bas.
    for (let i = 0; i < nbCases; i++) {
      const x = x0 + i * (L + GAP) + L / 2;
      el("line", { x1: x, y1: yHaut + H + 4, x2: x, y2: yBas - 4, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "4 4" });
    }
    // Le nombre de paquets, le meme en haut et en bas.
    el("rect", { x: 70, y: 144, width: 200, height: 30, rx: 15, fill: "#FFFFFF", stroke: "#2E7D32", "stroke-width": 2 });
    el("text", { x: 170, y: 165, "font-size": 16, "font-weight": 700, "text-anchor": "middle", fill: "#2E7D32" }, titre);
    // Rappel : un paquet du haut va avec un paquet du bas.
    el("text", { x: 170, y: 36, "font-size": 15, "text-anchor": "middle", fill: "#1F4E8C" }, `1 paquet du haut : ${nombre(a)}`);
    el("text", { x: 170, y: 290, "font-size": 15, "text-anchor": "middle", fill: "#E07B00" }, `1 paquet du bas : ${nombre(b)}`);
    return { a, b, fois };
  },
};
