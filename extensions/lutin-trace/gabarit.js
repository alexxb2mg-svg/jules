// Jules - gabarit "lutin-trace" : le chemin trace par un lutin (Scratch) ou un robot qui execute
//   longueur = L ; repeter `repetitions` fois : [motif ; tourner a droite ; ajouter `ajout` a longueur]
// ou le motif est « repeter `cotes` fois [avancer de longueur ; tourner a droite de 360 / cotes] » (cotes = 1 : un
// seul trait, c'est la boucle simple ; cotes >= 2 : un polygone regulier (2 = aller-retour), et la boucle exterieure
// tourne alors de 360 / repetitions : une rosace).
// Le programme est ecrit au-dessus du dessin ; aucune valeur calculee n'est ecrite (ni angle interieur, ni nom de
// figure). cases = 1 : longueur comptee en cases d'un quadrillage (robot, CM1) ; cases = 0 : en pas (Scratch, 3e).
// Faits : Scratch 3 (scratch.mit.edu) : le lutin part tourne vers la droite (direction 90), « tourner de ↻ n
// degres » tourne dans le sens des aiguilles d'une montre ; un polygone regulier a n cotes se ferme avec n
// rotations de 360 / n degres (angle exterieur), programme de mathematiques du cycle 4 (BO n° 31 du 30/07/2020,
// « Algorithmique et programmation ») et de sciences et technologie du cycle 3.
// Contrat : extension.yaml de ce dossier (fournit.figures), voir docs/EXTENSIONS.md. Rendu SVG pur, aucun eval().
"use strict";

window.GABARITS = window.GABARITS || {};

window.GABARITS["lutin-trace"] = {
  // dessiner(svg, valeurs) : repetitions (1-20), angle (0-180, degres, a droite), longueur (1-100), ajout (0-20),
  // cotes (1-8, cotes du motif), cases (0 = pas de Scratch, 1 = cases du quadrillage).
  dessiner(svg, valeurs) {
    const borne = (v, defaut, mini, maxi) => {
      const x = Number(v ?? defaut);
      return Math.min(maxi, Math.max(mini, Number.isFinite(x) ? x : defaut));
    };
    const repetitions = Math.round(borne(valeurs.repetitions, 4, 1, 20));
    const angle = borne(valeurs.angle, 90, 0, 180);
    const longueur = borne(valeurs.longueur, 60, 1, 100);
    const ajout = borne(valeurs.ajout, 0, 0, 20);
    const cotes = Math.round(borne(valeurs.cotes, 1, 1, 8));
    const cases = Number(valeurs.cases ?? 0) === 1;

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

    // Avec un motif (cotes >= 2), la boucle exterieure tourne de 360 / repetitions : la rosace se referme toujours
    // (bloc personnalise + boucle imbriquee, niveau 3) ; angle ne sert qu'a la boucle simple (cotes = 1).
    const tour = cotes > 1 ? 360 / repetitions : angle;

    // 1. Le programme, execute pas a pas : liste des points (unites du programme : pas ou cases).
    const points = [[0, 0]];
    let x = 0, y = 0, cap = 0; // cap en degres, 0 = vers la droite, croissant dans le sens des aiguilles
    for (let i = 0; i < repetitions; i++) {
      const L = longueur + i * ajout;
      for (let j = 0; j < cotes; j++) {
        x += L * Math.cos((cap * Math.PI) / 180);
        y += L * Math.sin((cap * Math.PI) / 180);
        points.push([x, y]);
        if (cotes > 1) cap += 360 / cotes;
      }
      cap += tour;
    }

    // 2. Echelle : fixe (2 px par pas, 32 px par case) tant que le dessin tient, reduite sinon (jamais de debord).
    const zone = { x: 14, y: 82, l: 312, h: 246 };
    const xs = points.map((p) => p[0]), ys = points.map((p) => p[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
    const base = cases ? 32 : 2;
    const marge = 16; // place pour le lutin en bout de chemin
    const echelle = Math.min(
      base,
      (zone.l - 2 * marge) / Math.max(maxX - minX, 1e-9),
      (zone.h - 2 * marge) / Math.max(maxY - minY, 1e-9),
    );
    const reduite = echelle < base - 1e-9;
    const ox = zone.x + zone.l / 2 - ((minX + maxX) / 2) * echelle;
    const oy = zone.y + zone.h / 2 - ((minY + maxY) / 2) * echelle;
    const px = (p) => [ox + p[0] * echelle, oy + p[1] * echelle];

    // 3. Le quadrillage, cale sur le point de depart : une case (robot) ou 20 pas (lutin).
    const pasGrille = (cases ? 1 : 20) * echelle;
    if (pasGrille >= 9) {
      const premier = (o, debut) => o - Math.floor((o - debut) / pasGrille) * pasGrille;
      for (let gx = premier(ox, zone.x); gx <= zone.x + zone.l + 0.01; gx += pasGrille) {
        el("line", { x1: gx, y1: zone.y, x2: gx, y2: zone.y + zone.h, stroke: "#E1E6ED", "stroke-width": 2 });
      }
      for (let gy = premier(oy, zone.y); gy <= zone.y + zone.h + 0.01; gy += pasGrille) {
        el("line", { x1: zone.x, y1: gy, x2: zone.x + zone.l, y2: gy, stroke: "#E1E6ED", "stroke-width": 2 });
      }
    }
    el("rect", { x: zone.x, y: zone.y, width: zone.l, height: zone.h, fill: "none", stroke: "#6B7686", "stroke-width": 2, rx: 6 });

    // 4. Le chemin (bleu), le depart (point vert), le lutin a l'arrivee (fleche orange tournee vers son cap).
    el("polyline", {
      points: points.map((p) => px(p).map((v) => v.toFixed(1)).join(",")).join(" "),
      fill: "none", stroke: "#1F4E8C", "stroke-width": 3, "stroke-linejoin": "round", "stroke-linecap": "round",
    });
    const [dx, dy] = px(points[0]);
    el("circle", { cx: dx, cy: dy, r: 8, fill: "#FFFFFF", stroke: "#2E7D32", "stroke-width": 4 });
    const [fx, fy] = px(points[points.length - 1]);
    const c = (cap * Math.PI) / 180;
    const pointe = (r, a) => `${(fx + r * Math.cos(c + a)).toFixed(1)},${(fy + r * Math.sin(c + a)).toFixed(1)}`;
    el("polygon", {
      points: `${pointe(14, 0)} ${pointe(9, 2.5)} ${pointe(9, -2.5)}`,
      fill: "#E07B00", stroke: "#14243B", "stroke-width": 2, "stroke-linejoin": "round",
    });

    // 5. Le programme en francais, au-dessus (c'est la donnee, pas la reponse).
    const unite = cases ? (longueur > 1 ? " cases" : " case") : "";
    const nombre = (v) => String(Math.round(v * 100) / 100).replace(".", ",");
    const lignes = []; // [retrait, texte] : le corps de la boucle est decale vers la droite
    if (ajout > 0) {
      lignes.push([0, `longueur = ${nombre(longueur)}${unite} ; répéter ${repetitions} fois :`]);
      lignes.push([1, cotes > 1 ? `motif à ${cotes} côtés de longueur` : "avancer de longueur"]);
      lignes.push([1, cotes > 1 ? `tourner ↻ de 360° ÷ ${repetitions} ; ajouter ${nombre(ajout)} à longueur` : `tourner ↻ de ${nombre(angle)}° ; ajouter ${nombre(ajout)} à longueur`]);
    } else {
      lignes.push([0, `répéter ${repetitions} fois :`]);
      if (cotes > 1) {
        lignes.push([1, `motif à ${cotes} côtés de ${nombre(longueur)}${unite}`]);
        lignes.push([1, `puis tourner ↻ de 360° ÷ ${repetitions}`]);
      } else {
        lignes.push([1, `avancer de ${nombre(longueur)}${unite} ; tourner ↻ de ${nombre(angle)}°`]);
      }
    }
    lignes.forEach(([retrait, t], i) => {
      el("text", { x: 14 + retrait * 16, y: 20 + i * 21, "font-size": 14, fill: "#14243B", "font-family": "sans-serif" }, t);
    });
    if (reduite) {
      el("text", { x: 320, y: zone.y + zone.h - 8, "font-size": 13, fill: "#6B7686", "text-anchor": "end", "font-family": "sans-serif", stroke: "#FFFFFF", "stroke-width": 4, "paint-order": "stroke" }, "dessin réduit");
    }
    return { repetitions, angle: tour, longueur, ajout, cotes, cases: cases ? 1 : 0, reduite };
  },
};
