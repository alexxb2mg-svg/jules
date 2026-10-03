// Jules - gabarit "glisse-nombre" : tableau de numeration (dizaines de mille a centiemes), virgule fixe en rouge.
// Ligne du haut : le nombre de depart ; ligne du bas : le resultat de × 10, × 100, × 1 000 ou ÷ 10. Chaque
// chiffre garde sa couleur et une fleche montre de combien de rangs il glisse ; les zeros qui apparaissent
// sont gris. Curseurs : nombre (0,1 a 99,9) et rangs (-1 = ÷ 10, 0 = rien, 1 = × 10, 2 = × 100, 3 = × 1 000).
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["glisse-nombre"] = {
  dessiner(svg, valeurs) {
    const brut = Number(valeurs.nombre ?? 4.7);
    const dixiemes = Math.min(999, Math.max(1, Math.round((Number.isFinite(brut) ? brut : 4.7) * 10)));
    const brutK = Number(valeurs.rangs ?? 1);
    const k = Math.min(3, Math.max(-1, Math.round(Number.isFinite(brutK) ? brutK : 1)));
    const NS = "http://www.w3.org/2000/svg";
    const el = (nom, attrs, texte) => {
      const e = document.createElementNS(NS, nom);
      for (const cle in attrs) e.setAttribute(cle, attrs[cle]);
      if (texte !== undefined) e.textContent = texte;
      svg.appendChild(e);
      return e;
    };
    const ENCRE = "#14243B", BLEU = "#1F4E8C", GRIS = "#6B7686", ROUGE = "#C8102E", VERT = "#2E7D32", ORANGE = "#E07B00";

    // Un nombre = ses chiffres en centiemes entiers (aucune erreur d'arrondi) ; rang e : 4 = dizaines de mille,
    // 0 = unites, -1 = dixiemes, -2 = centiemes.
    const chiffre = (centiemes, e) => Math.floor(centiemes / 10 ** (e + 2)) % 10;
    const rangsEcrits = (centiemes) => {
      const non0 = [];
      for (let e = 4; e >= -2; e--) if (chiffre(centiemes, e) !== 0) non0.push(e);
      const haut = Math.max(non0[0] ?? 0, 0), bas = Math.min(non0[non0.length - 1] ?? 0, 0);
      const liste = [];
      for (let e = haut; e >= bas; e--) liste.push(e);
      return liste;
    };
    const ecrire = (centiemes) => {
      const entier = String(Math.floor(centiemes / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0");
      const dec = String(centiemes % 100).padStart(2, "0").replace(/0+$/, "");
      return dec ? `${entier},${dec}` : entier;
    };
    const depart = dixiemes * 10;
    const resultat = k >= 0 ? depart * 10 ** k : depart / 10;
    const rangsD = rangsEcrits(depart), rangsR = rangsEcrits(resultat);

    // Colonnes : 5 colonnes entieres de 36 px, puis dixiemes et centiemes de 69 px ; virgule a x = 191.
    const VIRGULE = 191;
    const gaucheCol = (e) => (e >= 0 ? 11 + (4 - e) * 36 : VIRGULE + (-1 - e) * 69);
    const largeurCol = (e) => (e >= 0 ? 36 : 69);
    const centre = (e) => gaucheCol(e) + largeurCol(e) / 2;
    svg.setAttribute("viewBox", "0 0 340 260");
    svg.innerHTML = ""; // vide le SVG (aucune donnee inseree ici) ; tous les elements sont crees via createElementNS

    // En-tetes : classe des mille, classe des unites, dixiemes, centiemes.
    el("rect", { x: 11, y: 6, width: 318, height: 44, fill: "#EEF1F5" });
    el("text", { x: 47, y: 23, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "mille");
    el("text", { x: 137, y: 23, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "unités");
    el("line", { x1: 15, y1: 28, x2: VIRGULE - 4, y2: 28, stroke: GRIS, "stroke-width": 1 });
    ["d", "u", "c", "d", "u"].forEach((lettre, i) =>
      el("text", { x: centre(4 - i), y: 45, "font-size": 14, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, lettre));
    el("text", { x: centre(-1), y: 33, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "dixièmes");
    el("text", { x: centre(-2), y: 33, "font-size": 13, "text-anchor": "middle", fill: ENCRE }, "centièmes");
    for (let e = 4; e >= -2; e--) {
      el("line", { x1: gaucheCol(e), y1: 6, x2: gaucheCol(e), y2: 212, stroke: "#C9D0DA", "stroke-width": 1 });
    }
    el("line", { x1: 329, y1: 6, x2: 329, y2: 212, stroke: "#C9D0DA", "stroke-width": 1 });
    el("line", { x1: 83, y1: 6, x2: 83, y2: 212, stroke: GRIS, "stroke-width": 2 }); // separation des classes
    for (const y of [74, 114, 168, 208]) el("line", { x1: 11, y1: y, x2: 329, y2: y, stroke: GRIS, "stroke-width": 1.5 });

    // La virgule ne bouge pas : trait rouge sur toute la hauteur et virgule dans chaque ligne.
    el("line", { x1: VIRGULE, y1: 6, x2: VIRGULE, y2: 214, stroke: ROUGE, "stroke-width": 2.5, "stroke-dasharray": "6 4" });

    // Ligne du haut : chiffres du nombre de depart, chacun sa couleur (de gauche a droite).
    const couleurs = [BLEU, VERT, ORANGE];
    const couleurDe = {};
    rangsD.forEach((e, i) => {
      couleurDe[e] = couleurs[i % couleurs.length];
      el("text", { x: centre(e), y: 104, "font-size": 26, "font-weight": 700, "text-anchor": "middle", fill: couleurDe[e] }, String(chiffre(depart, e)));
    });
    if (rangsD.includes(-1)) el("text", { x: VIRGULE, y: 108, "font-size": 30, "font-weight": 700, "text-anchor": "middle", fill: ROUGE }, ",");

    // Fleches : chaque chiffre qui reste ecrit glisse de k rangs (vers la gauche si k > 0).
    const fleche = (x1, x2, couleur, opacite = 1) => {
      const y1 = 119, y2 = 162, ang = Math.atan2(y2 - y1, x2 - x1);
      const bx = x2 - 11 * Math.cos(ang), by = y2 - 11 * Math.sin(ang);
      el("line", { x1, y1, x2: bx, y2: by, stroke: couleur, "stroke-width": 2.5, "stroke-linecap": "round", opacity: opacite });
      const px = 6 * Math.sin(ang), py = -6 * Math.cos(ang);
      el("polygon", { points: `${x2},${y2} ${bx + px},${by + py} ${bx - px},${by - py}`, fill: couleur, opacity: opacite });
    };
    for (const e of rangsD) {
      if (rangsR.includes(e + k)) fleche(centre(e), centre(e + k), couleurDe[e]);
      else if (e + k <= 4 && e + k >= -2) {
        // zero devenu inutile (0,3 × 10 = 03 ; 20 ÷ 10 = 2,0) : il glisse aussi mais ne s'ecrit plus, trace en pale
        fleche(centre(e), centre(e + k), GRIS, 0.3);
        el("text", { x: centre(e + k), y: 198, "font-size": 26, "font-weight": 700, "text-anchor": "middle", fill: GRIS, opacity: 0.3 }, "0");
      }
    }

    // Ligne du bas : le resultat ; les chiffres venus d'en haut gardent leur couleur, les zeros ajoutes sont gris.
    for (const e of rangsR) {
      const venu = rangsD.includes(e - k);
      if (!venu) el("rect", { x: gaucheCol(e) + 3, y: 171, width: largeurCol(e) - 6, height: 34, rx: 4, fill: "#EEF1F5" });
      el("text", { x: centre(e), y: 198, "font-size": 26, "font-weight": 700, "text-anchor": "middle", fill: venu ? couleurDe[e - k] : GRIS },
        String(chiffre(resultat, e)));
    }
    if (rangsR.includes(-1)) el("text", { x: VIRGULE, y: 202, "font-size": 30, "font-weight": 700, "text-anchor": "middle", fill: ROUGE }, ",");

    // Le calcul ecrit en entier (la figure donne le resultat).
    const operation = { "-1": "\u00f7 10", 1: "\u00d7 10", 2: "\u00d7 100", 3: "\u00d7 1\u00a0000" }[k];
    const phrase = operation ? `${ecrire(depart)} ${operation} = ${ecrire(resultat)}` : `${ecrire(depart)} : choisis une opération`;
    el("text", { x: 170, y: 244, "font-size": 20, "font-weight": 700, "text-anchor": "middle", fill: ENCRE }, phrase);
    return { nombre: dixiemes / 10, rangs: k };
  },
};
