// Jules - gabarit "chaine-energetique" : bilan d'energie d'un convertisseur. Une fleche d'energie recue (bleu)
// entre dans le convertisseur et se partage en energie utile (vert) et energie perdue, surtout sous forme de
// chaleur (orange). Curseurs : energie (energie recue, J) et u (part utile, en %).
// L'epaisseur des fleches est proportionnelle a l'energie (meme echelle pour tous les reglages) et, en bas, la
// barre « recue » a exactement la longueur des barres « utile » + « perdue » mises bout a bout : rien ne
// disparait, rien n'est cree. Aucune valeur d'energie n'est ecrite (revele: false) : l'eleve compare des
// longueurs, il ne lit pas le resultat d'un calcul.
// Source : programme de physique-chimie du cycle 4 (BO n° 31 du 30/07/2020, annexe 3, theme « L'energie et ses
// conversions ») : « Identifier les sources, les transferts et les conversions d'energie. Etablir un bilan
// energetique pour un systeme simple. Conservation de l'energie. » Aucune donnee chiffree d'appareil n'est
// ecrite dans la figure.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["chaine-energetique"] = {
  dessiner(svg, valeurs) {
    const energie = Math.min(1000, Math.max(100, Number(valeurs.energie ?? 500)));
    const u = Math.min(95, Math.max(10, Number(valeurs.u ?? 40)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const n = document.createElementNS(NS, nom);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      if (texte !== undefined) n.textContent = texte;
      svg.appendChild(n);
      return n;
    };
    const f = (x) => Math.round(x * 10) / 10;
    const ENCRE = "#14243B", BLEU = "#1F4E8C", VERT = "#2E7D32", ORANGE = "#E07B00";
    svg.setAttribute("viewBox", "0 0 340 326");
    svg.replaceChildren(); // vide le SVG ; tous les elements sont crees via createElementNS

    // Epaisseurs : 1 000 J = 64 px. Les deux sorties font ensemble l'epaisseur de l'entree.
    const K = 64 / 1000;
    // Une sortie tres fine (ex. 5 % de 100 J) garde 3 px d'epaisseur pour rester visible ; les barres du bas,
    // elles, restent exactement a l'echelle.
    const wIn = energie * K, wU = Math.max(3, ((energie * u) / 100) * K), wP = Math.max(3, wIn - ((energie * u) / 100) * K);
    // Convertisseur : boite au centre. Entree a gauche ; utile sort a droite (haut de la boite), perdue sort
    // par le bas (cote droit de la boite).
    const BX = 118, BY = 70, BW = 104, BH = 86, YM = BY + BH / 2;
    const POINTE = 14;
    // Fleche d'entree (bleu), centree sur le milieu de la boite.
    el("polygon", {
      points: `16,${f(YM - wIn / 2)} ${BX},${f(YM - wIn / 2)} ${BX},${f(YM + wIn / 2)} 16,${f(YM + wIn / 2)}`,
      fill: BLEU,
    });
    // Fleche utile (vert), sort a droite en haut de l'entree.
    const yU = YM - wIn / 2; // haut de la bande
    const xFinU = 322;
    el("polygon", {
      points: `${BX + BW},${f(yU)} ${xFinU - POINTE},${f(yU)} ${xFinU},${f(yU + wU / 2)} ${xFinU - POINTE},${f(yU + wU)} ${BX + BW},${f(yU + wU)}`,
      fill: VERT,
    });
    // Fleche perdue (orange) : descend sous la boite, largeur wP, puis pointe vers le bas.
    const xP = BX + BW - 8 - wP, yFinP = 236;
    el("polygon", {
      points: `${f(xP)},${BY + BH} ${f(xP + wP)},${BY + BH} ${f(xP + wP)},${yFinP - POINTE} ${f(xP + wP / 2)},${yFinP} ${f(xP)},${yFinP - POINTE}`,
      fill: ORANGE,
    });
    // La boite par-dessus les departs de fleches.
    el("rect", { x: BX, y: BY, width: BW, height: BH, rx: 8, fill: "#FFFFFF", stroke: ENCRE, "stroke-width": 3 });
    el("text", { x: BX + BW / 2, y: YM + 5, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "convertisseur");

    // Etiquettes des fleches.
    el("text", { x: 16, y: f(YM - wIn / 2 - 8), "font-size": 14, fill: BLEU }, "reçue");
    el("text", { x: 322, y: f(yU - 8), "font-size": 14, "text-anchor": "end", fill: VERT }, "utile");
    el("text", { x: f(xP - 8), y: 222, "font-size": 14, "text-anchor": "end", fill: ORANGE }, "perdue");
    el("text", { x: f(xP - 8), y: 238, "font-size": 13, "text-anchor": "end", fill: ORANGE }, "(chaleur)");

    // Barres de bilan, a la meme echelle : 1 000 J = 300 px.
    const L = (j) => (j / 1000) * 300, XB = 20;
    el("rect", { x: XB, y: 256, width: f(L(energie)), height: 18, fill: BLEU });
    const lU = L((energie * u) / 100);
    el("rect", { x: XB, y: 282, width: f(lU), height: 18, fill: VERT });
    el("rect", { x: f(XB + lU), y: 282, width: f(L(energie) - lU), height: 18, fill: ORANGE });
    el("line", { x1: f(XB + L(energie)), y1: 250, x2: f(XB + L(energie)), y2: 306, stroke: ENCRE, "stroke-width": 2, "stroke-dasharray": "3 3" });
    el("text", { x: 170, y: 318, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "reçue = utile + perdue");
    return { energie, u, utile: (energie * u) / 100, perdue: energie - (energie * u) / 100 };
  },
};
