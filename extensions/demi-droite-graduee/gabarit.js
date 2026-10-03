// Jules - gabarit "demi-droite-graduee" : le nombre n milliers (n = 245 place 245 000) sur une demi-droite
// graduee de 0 a 1 000 000, puis deux loupes : le curseur zoom fait apparaitre, sous le bond de 100 000 ou se
// trouve le point, une ligne graduee de 10 000 en 10 000, puis sous celle-ci une ligne de 1 000 en 1 000.
// Le point n'est pas etiquete ; seuls les deux bouts de chaque ligne de loupe sont ecrits : l'eleve compte les bonds.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["demi-droite-graduee"] = {
  dessiner(svg, valeurs) {
    const entier = (v, defaut, min, max) => {
      const x = Math.round(Number(v ?? defaut));
      return Math.min(max, Math.max(min, Number.isFinite(x) ? x : defaut));
    };
    const n = entier(valeurs.n, 245, 0, 999);
    const zoom = entier(valeurs.zoom, 1, 1, 3);
    const nombre = n * 1000;
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const noeud = document.createElementNS(NS, nom);
      for (const cle in attrs) noeud.setAttribute(cle, attrs[cle]);
      if (texte !== undefined) noeud.textContent = texte;
      svg.appendChild(noeud);
      return noeud;
    };
    svg.setAttribute("viewBox", "0 0 340 300");
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const espaces = (x) => String(x).replace(/\B(?=(\d{3})+(?!\d))/g, " "); // 245000 -> 245 000
    const X0 = 20, BOND = 30; // 10 bonds de 30 px par ligne
    // une ligne : 10 bonds de `taille`, a partir de `debut` ; renvoie la position du point en bonds
    const ligne = (y, debut, taille, legende, fleche) => {
      // ligne du haut : legende au-dessus ; lignes de loupe : au milieu, sous la ligne (les pointilles de la loupe
      // passent au-dessus, les deux bouts ecrits sont aux extremites)
      el("text", { x: 170, y: fleche ? y - 22 : y + 28, "font-size": 14, "text-anchor": "middle", fill: "#6B7686" }, legende);
      el("line", { x1: X0, y1: y, x2: X0 + 10 * BOND + (fleche ? 12 : 0), y2: y, stroke: "#14243B", "stroke-width": 2.5 });
      if (fleche) {
        el("polygon", { points: `${X0 + 10 * BOND + 18},${y} ${X0 + 10 * BOND + 8},${y - 6} ${X0 + 10 * BOND + 8},${y + 6}`, fill: "#14243B" });
      }
      for (let i = 0; i <= 10; i++) {
        const grand = i === 0 || i === 5 || i === 10;
        el("line", { x1: X0 + i * BOND, y1: y - (grand ? 11 : 7), x2: X0 + i * BOND, y2: y + (grand ? 11 : 7), stroke: "#14243B", "stroke-width": 2 });
      }
      return (nombre - debut) / taille;
    };
    const bouts = (y, gauche, droite) => {
      el("text", { x: X0 - 4, y: y + 28, "font-size": 14, "text-anchor": "start", fill: "#14243B" }, gauche);
      el("text", { x: X0 + 10 * BOND + 4, y: y + 28, "font-size": 14, "text-anchor": "end", fill: "#14243B" }, droite);
    };
    const point = (y, position) => {
      el("circle", { cx: X0 + position * BOND, cy: y, r: 7, fill: "#C8102E", stroke: "#FFFFFF", "stroke-width": 2 });
    };
    // loupe : le bond ou se trouve le point est surligne, et deux traits le relient a la ligne du dessous
    const loupe = (yHaut, position, yBas) => { // les pointilles partent sous la rangee de nombres
      const i = Math.min(9, Math.floor(position));
      el("line", { x1: X0 + i * BOND, y1: yHaut, x2: X0 + (i + 1) * BOND, y2: yHaut, stroke: "#1F4E8C", "stroke-width": 7, "stroke-opacity": 0.85 });
      el("line", { x1: X0 + i * BOND, y1: yHaut + 38, x2: X0, y2: yBas - 12, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "5 4" });
      el("line", { x1: X0 + (i + 1) * BOND, y1: yHaut + 38, x2: X0 + 10 * BOND, y2: yBas - 12, stroke: "#6B7686", "stroke-width": 2, "stroke-dasharray": "5 4" });
    };

    const Y1 = 46, Y2 = 154, Y3 = 262;
    const p1 = ligne(Y1, 0, 100000, "bonds de 100 000", true);
    for (const [i, texte, ancre] of [[0, "0", "start"], [5, "500 000", "middle"], [10, "1 000 000", "end"]]) {
      el("text", { x: X0 + i * BOND + (i === 0 ? -4 : 0), y: Y1 + 28, "font-size": 14, "text-anchor": ancre, fill: "#14243B" }, texte);
    }
    if (zoom >= 2) {
      loupe(Y1, p1, Y2);
      const debut2 = Math.floor(nombre / 100000) * 100000;
      const p2 = ligne(Y2, debut2, 10000, "bonds de 10 000", false);
      bouts(Y2, espaces(debut2), espaces(debut2 + 100000));
      if (zoom >= 3) {
        loupe(Y2, p2, Y3);
        const debut3 = Math.floor(nombre / 10000) * 10000;
        const p3 = ligne(Y3, debut3, 1000, "bonds de 1 000", false);
        bouts(Y3, espaces(debut3), espaces(debut3 + 10000));
        point(Y3, p3);
      }
      point(Y2, p2);
    }
    point(Y1, p1);
    return { n, zoom, nombre };
  },
};
